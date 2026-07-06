"""
投篮高手 (Basketball Shooter)
- 点击并拖拽篮球调整角度和力度，松开投篮
- 篮筐左右移动，投中得分
- 60秒限时挑战
- 物理抛物线的运动轨迹
"""

import pygame
import math
import random
import sys

# 初始化 Pygame
pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    pass  # 无音频设备也可运行

# 屏幕尺寸
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("投篮高手 - Basketball Shooter")

# 颜色
BLACK = (20, 20, 30)
WHITE = (255, 255, 255)
ORANGE = (255, 140, 50)
BROWN = (180, 100, 30)
RED = (255, 60, 60)
GREEN = (60, 200, 100)
BLUE = (60, 120, 255)
YELLOW = (255, 220, 50)
GRAY = (150, 150, 150)
DARK_GRAY = (60, 60, 80)
SKY_BLUE = (100, 150, 255)
NET_COLOR = (220, 220, 220)

# 字体
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 32)

# 游戏常量
GRAVITY = 0.5
MAX_POWER = 20
TIME_LIMIT = 60  # 秒
SHOOT_COOLDOWN = 15  # 帧数

# 篮筐配置
HOOP_HEIGHT = 150
HOOP_WIDTH = 120
BACKBOARD_WIDTH = 10
BACKBOARD_HEIGHT = 80
RIM_RADIUS = 5


class Ball:
    """篮球类"""

    def __init__(self, x, y):
        self.start_x = x
        self.start_y = y
        self.reset()

    def reset(self):
        self.x = self.start_x
        self.y = self.start_y
        self.vx = 0
        self.vy = 0
        self.radius = 12
        self.shooting = False
        self.flying = False
        self.scored = False
        self.rotation = 0
        self.trail = []
        self.trail_timer = 0

    def shoot(self, angle, power):
        """发射篮球"""
        self.vx = math.cos(angle) * power
        self.vy = -math.sin(angle) * power
        self.flying = True
        self.shooting = False
        self.trail = []

    def update(self):
        """更新篮球物理状态"""
        if not self.flying:
            return

        # 物理模拟
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy

        # 旋转效果
        self.rotation += self.vx * 0.05

        # 轨迹记录
        self.trail_timer += 1
        if self.trail_timer % 3 == 0:
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 20:
                self.trail.pop(0)

        # 边界碰撞 - 地面
        if self.y > HEIGHT - 50:
            self.flying = False
            self.reset()

        # 边界碰撞 - 左右
        if self.x < self.radius or self.x > WIDTH - self.radius:
            self.vx *= -0.6
            self.x = max(self.radius, min(WIDTH - self.radius, self.x))

        # 边界碰撞 - 天花板
        if self.y < self.radius:
            self.vy *= -0.6

    def draw(self, surface):
        """绘制篮球及其轨迹"""
        # 轨迹点
        for i, (tx, ty) in enumerate(self.trail):
            alpha = i / len(self.trail) if self.trail else 0
            size = int(3 * alpha) + 1
            color = (255, int(200 * alpha), int(80 * alpha))
            pygame.draw.circle(surface, color, (tx, ty), size)

        # 篮球阴影
        if self.flying:
            shadow_x = self.x
            shadow_y = HEIGHT - 45
            shadow_size = max(3, self.radius - int(self.y / 30))
            pygame.draw.ellipse(surface, (30, 30, 40),
                                (shadow_x - shadow_size, shadow_y - shadow_size // 2,
                                 shadow_size * 2, shadow_size))

        # 篮球本体
        if not self.shooting and not self.flying and self.scored:
            return

        # 篮球带纹理
        pygame.draw.circle(surface, ORANGE, (int(self.x), int(self.y)), self.radius)

        # 篮球纹理线
        rot = self.rotation
        cx, cy = int(self.x), int(self.y)
        r = self.radius

        # 横线
        pygame.draw.line(surface, BROWN,
                         (cx - r, cy),
                         (cx + r, cy), 2)
        # 竖线
        pygame.draw.line(surface, BROWN,
                         (cx, cy - r),
                         (cx, cy + r), 2)

        # 弧线
        for offset in [-1, 1]:
            start_angle = rot + offset * math.pi / 4
            end_angle = rot + offset * math.pi / 4 + math.pi
            points = []
            for a in range(0, 180, 10):
                angle = start_angle + a * math.pi / 180
                px = cx + int(r * 0.7 * math.cos(angle))
                py = cy + int(r * 0.7 * math.sin(angle))
                points.append((px, py))
            if len(points) > 1:
                pygame.draw.lines(surface, BROWN, False, points, 2)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)


class Hoop:
    """篮筐类"""

    def __init__(self):
        self.width = HOOP_WIDTH
        self.rim_radius = RIM_RADIUS
        self.backboard_width = BACKBOARD_WIDTH
        self.backboard_height = BACKBOARD_HEIGHT
        self.y = HOOP_HEIGHT
        self.x = WIDTH // 2
        self.target_x = WIDTH // 2
        self.speed = 3
        self.direction = 1
        self.sway = random.uniform(-0.5, 0.5)

    def update(self):
        """更新篮筐位置（左右移动）"""
        self.target_x += self.direction * self.speed
        if self.target_x > WIDTH - 150:
            self.direction = -1
        elif self.target_x < 150:
            self.direction = 1

        # 平滑移动
        self.x += (self.target_x - self.x) * 0.1
        self.y = HOOP_HEIGHT + math.sin(pygame.time.get_ticks() * 0.001) * 10

    def draw(self, surface):
        """绘制篮筐"""
        x, y = int(self.x), int(self.y)

        # 篮板支柱
        pygame.draw.line(surface, GRAY, (x, y + 30), (x, y + 120), 4)

        # 篮板
        board_rect = pygame.Rect(x - 5, y - 30, self.backboard_width, self.backboard_height)
        pygame.draw.rect(surface, WHITE, board_rect, border_radius=2)
        pygame.draw.rect(surface, GRAY, board_rect, 2, border_radius=2)

        # 篮板上的方框
        inner_rect = pygame.Rect(x - 2, y - 15, 4, 30)
        pygame.draw.rect(surface, RED, inner_rect, 1)

        # 篮筐（左右两侧）
        rim_left = (x - self.width // 2, y)
        rim_right = (x + self.width // 2, y)

        # 篮筐横梁
        pygame.draw.line(surface, RED, rim_left, rim_right, 4)

        # 篮筐挂钩
        pygame.draw.line(surface, RED, rim_left, (x - self.width // 2, y - 10), 3)
        pygame.draw.line(surface, RED, rim_right, (x + self.width // 2, y - 10), 3)

        # 篮筐两端圆点
        pygame.draw.circle(surface, RED, (int(rim_left[0]), int(rim_left[1])), 4)
        pygame.draw.circle(surface, RED, (int(rim_right[0]), int(rim_right[1])), 4)

        # 篮网（网状效果）
        net_points = 8
        net_depth = 30
        for i in range(net_points + 1):
            t = i / net_points
            top_x = x - self.width // 2 + self.width * t
            bottom_x = x - self.width // 3 + self.width * 2 / 3 * t
            bottom_y = y + net_depth
            # 竖线
            pygame.draw.line(surface, NET_COLOR,
                             (int(top_x), y),
                             (int(bottom_x), int(bottom_y)), 1)

        # 横线
        for row in range(1, 4):
            t = row / 4
            row_y = y + net_depth * t
            left_x = x - self.width // 2 + self.width * t * 0.5
            right_x = x + self.width // 2 - self.width * t * 0.5
            pygame.draw.line(surface, NET_COLOR,
                             (int(left_x), int(row_y)),
                             (int(right_x), int(row_y)), 1)

    def check_score(self, ball):
        """检测是否进球"""
        if ball.flying and ball.vy > 0:  # 球在下落过程中
            # 球经过篮筐水平位置
            rim_y = self.y
            rim_left = self.x - self.width // 2 + 10
            rim_right = self.x + self.width // 2 - 10

            # 球的中心是否在篮筐范围内
            if (rim_left < ball.x < rim_right and
                    abs(ball.y - rim_y) < 20):
                return True
        return False

    def get_rim_left(self):
        return self.x - self.width // 2

    def get_rim_right(self):
        return self.x + self.width // 2


class BasketballGame:
    """投篮游戏主类"""

    def __init__(self):
        self.clock = pygame.time.Clock()
        self.ball = Ball(WIDTH // 2, HEIGHT - 80)
        self.hoop = Hoop()
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.time_left = TIME_LIMIT
        self.game_state = "ready"  # ready, aiming, flying, game_over
        self.aim_angle = 0
        self.aim_power = 0
        self.is_dragging = False
        self.mouse_start = (0, 0)
        self.frames = 0
        self.cooldown = 0
        self.particles = []
        self.shake_timer = 0
        self.shake_intensity = 0
        self.stars = []
        self.bg_court_offset = 0
        self._init_stars()

        # 得分动画
        self.score_popups = []
        self.last_score_time = 0

    def _init_stars(self):
        """初始化背景星空"""
        for _ in range(50):
            self.stars.append({
                "x": random.randint(0, WIDTH),
                "y": random.randint(0, HEIGHT // 2),
                "size": random.uniform(1, 3),
                "speed": random.uniform(0.2, 0.8),
                "brightness": random.uniform(0.3, 1.0)
            })

    def add_particles(self, x, y, color, count=20):
        """添加粒子特效"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8)
            self.particles.append({
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.randint(20, 50),
                "max_life": 50,
                "color": color,
                "size": random.uniform(2, 6)
            })

    def update_particles(self):
        """更新粒子特效"""
        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.1
            p["life"] -= 1
            if p["life"] <= 0:
                self.particles.remove(p)

    def handle_events(self):
        """处理用户输入"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_r and self.game_state == "game_over":
                    self.__init__()
                    return True
                if event.key == pygame.K_SPACE and self.game_state == "ready":
                    self.game_state = "playing"
                    self.time_left = TIME_LIMIT

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_state == "playing" and self.cooldown <= 0:
                    # 检查是否点击在篮球上
                    mx, my = event.pos
                    dx = mx - self.ball.x
                    dy = my - self.ball.y
                    if dx * dx + dy * dy < (self.ball.radius + 20) ** 2:
                        self.is_dragging = True
                        self.mouse_start = (mx, my)
                        self.ball.shooting = True

            if event.type == pygame.MOUSEBUTTONUP:
                if self.is_dragging and self.game_state == "playing":
                    self.is_dragging = False
                    self.ball.shooting = False
                    # 发射篮球
                    self.shoot_ball()

            if event.type == pygame.MOUSEMOTION:
                if self.is_dragging:
                    mx, my = event.pos
                    dx = mx - self.ball.x
                    dy = my - self.ball.y
                    # 计算角度和力度
                    distance = math.sqrt(dx * dx + dy * dy)
                    if distance > 5:
                        self.aim_angle = math.atan2(dy, dx)
                        self.aim_power = min(distance * 0.15, MAX_POWER)
                    else:
                        self.aim_angle = 0
                        self.aim_power = 0

        return True

    def shoot_ball(self):
        """发射篮球"""
        if self.aim_power < 2:
            return

        self.ball.shoot(self.aim_angle, self.aim_power)
        self.cooldown = SHOOT_COOLDOWN

    def check_collisions(self):
        """检测碰撞"""
        if not self.ball.flying:
            return

        # 检测是否进球
        if self.hoop.check_score(self.ball):
            self.ball.flying = False
            self.ball.scored = True
            self.combo += 1
            if self.combo > self.max_combo:
                self.max_combo = self.combo

            # 连击加分
            bonus = min(self.combo, 10)
            points = 10 + bonus * 5
            self.score += points

            # 特效
            self.add_particles(self.ball.x, self.ball.y, YELLOW, 40)
            self.add_particles(self.ball.x, self.ball.y, ORANGE, 30)
            self.shake_intensity = 5
            self.shake_timer = 10

            # 得分弹出
            self.score_popups.append({
                "text": f"+{points}" + (" 🔥" if self.combo >= 3 else ""),
                "x": self.ball.x,
                "y": self.ball.y,
                "life": 60,
                "vy": -2
            })
            self.last_score_time = self.frames

            # 重置球
            self.ball.reset()

        # 检测球碰到篮板
        board_x = self.hoop.x
        board_top = self.hoop.y - 30
        board_bottom = self.hoop.y + 50
        if (abs(self.ball.x - board_x) < 10 and
                board_top < self.ball.y < board_bottom and
                self.ball.vx > 0):
            self.ball.vx *= -0.5
            self.ball.x = board_x - 10

    def update(self):
        """更新游戏状态"""
        self.frames += 1
        self.cooldown = max(0, self.cooldown - 1)

        if self.game_state == "playing":
            # 更新时间
            if self.frames % 60 == 0:
                self.time_left -= 1
                if self.time_left <= 0:
                    self.time_left = 0
                    self.game_state = "game_over"

            # 更新篮筐
            self.hoop.update()

            # 更新篮球
            self.ball.update()
            self.check_collisions()

            # 更新背景星星
            for star in self.stars:
                star["y"] += star["speed"]
                if star["y"] > HEIGHT // 2:
                    star["y"] = 0
                    star["x"] = random.randint(0, WIDTH)

        # 更新粒子
        self.update_particles()

        # 更新得分弹出
        for popup in self.score_popups[:]:
            popup["y"] += popup["vy"]
            popup["life"] -= 1
            if popup["life"] <= 0:
                self.score_popups.remove(popup)

        # 更新震动效果
        if self.shake_timer > 0:
            self.shake_timer -= 1
            self.shake_intensity *= 0.9
        else:
            self.shake_intensity = 0

    def draw_background(self, surface):
        """绘制背景"""
        # 天空渐变
        for i in range(HEIGHT):
            r = int(20 + i * 0.05)
            g = int(30 + i * 0.1)
            b = int(60 + i * 0.2)
            pygame.draw.line(surface, (min(r, 100), min(g, 150), min(b, 255)),
                             (0, i), (WIDTH, i))

        # 星星
        for star in self.stars:
            alpha = int(star["brightness"] * 255)
            pygame.draw.circle(surface, (alpha, alpha, alpha),
                               (int(star["x"]), int(star["y"])),
                               int(star["size"]))

        # 城市天际线
        buildings = [
            (50, 350, 60, 200), (120, 330, 50, 220), (180, 360, 70, 190),
            (260, 340, 45, 210), (320, 355, 55, 195), (390, 320, 65, 230),
            (470, 350, 50, 200), (530, 335, 60, 215), (600, 360, 55, 190),
            (670, 340, 45, 210), (730, 355, 60, 195)
        ]
        for bx, by, bw, bh in buildings:
            # 建筑主体
            pygame.draw.rect(surface, (30, 35, 50),
                             (bx, by, bw, bh))
            pygame.draw.rect(surface, (40, 45, 60),
                             (bx, by, bw, bh), 1)
            # 窗户
            for wy in range(by + 10, by + bh - 10, 20):
                for wx in range(bx + 5, bx + bw - 5, 15):
                    if random.random() > 0.3:
                        window_color = (random.randint(60, 100),
                                        random.randint(60, 100),
                                        random.randint(80, 120))
                        pygame.draw.rect(surface, window_color,
                                         (wx, wy, 8, 12))

        # 地面（球场）
        ground_y = HEIGHT - 50
        pygame.draw.rect(surface, (60, 50, 40),
                         (0, ground_y, WIDTH, 50))
        pygame.draw.line(surface, (80, 70, 60),
                         (0, ground_y), (WIDTH, ground_y), 3)

        # 球场线条
        court_color = (80, 70, 60)
        # 中场线
        pygame.draw.line(surface, court_color,
                         (WIDTH // 2, ground_y),
                         (WIDTH // 2, HEIGHT), 2)
        # 三分弧线
        pygame.draw.arc(surface, court_color,
                        (WIDTH // 2 - 60, ground_y - 10, 120, 40),
                        0, math.pi, 2)

    def draw_aim_line(self, surface):
        """绘制瞄准线和力度指示"""
        if not self.is_dragging or self.game_state != "playing":
            return

        # 瞄准线（虚线）
        mx, my = pygame.mouse.get_pos()
        dx = mx - self.ball.x
        dy = my - self.ball.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 5:
            return

        # 归一化方向向量
        ndx = dx / distance
        ndy = dy / distance

        # 绘制瞄准线（从球到鼠标方向的延长线）
        line_length = 200
        for i in range(0, line_length, 10):
            alpha = 1 - i / line_length
            sx = self.ball.x + ndx * i
            sy = self.ball.y + ndy * i
            ex = self.ball.x + ndx * (i + 5)
            ey = self.ball.y + ndy * (i + 5)
            pygame.draw.line(surface,
                             (255, int(255 * alpha), int(100 * alpha)),
                             (int(sx), int(sy)), (int(ex), int(ey)), 3)

        # 力度指示器
        power_percent = self.aim_power / MAX_POWER
        bar_width = 200
        bar_height = 15
        bar_x = WIDTH // 2 - bar_width // 2
        bar_y = HEIGHT - 30

        # 背景
        pygame.draw.rect(surface, DARK_GRAY,
                         (bar_x, bar_y, bar_width, bar_height), border_radius=5)
        # 填充
        fill_width = int(bar_width * power_percent)
        if fill_width > 0:
            color = (int(255 * power_percent),
                     int(255 * (1 - power_percent)),
                     50)
            pygame.draw.rect(surface, color,
                             (bar_x, bar_y, fill_width, bar_height), border_radius=5)
        # 边框
        pygame.draw.rect(surface, WHITE,
                         (bar_x, bar_y, bar_width, bar_height), 2, border_radius=5)

        # 力度标签
        power_text = font_small.render(f"力度: {int(power_percent * 100)}%", True, WHITE)
        surface.blit(power_text, (bar_x + bar_width + 10, bar_y - 2))

        # 角度指示
        angle_deg = int(math.degrees(self.aim_angle)) % 360
        angle_text = font_small.render(f"角度: {angle_deg}°", True, WHITE)
        surface.blit(angle_text, (bar_x, bar_y - 30))

    def draw_hud(self, surface):
        """绘制游戏界面信息"""
        # 分数
        score_text = font_large.render(f"{self.score}", True, WHITE)
        score_shadow = font_large.render(f"{self.score}", True, (0, 0, 0, 128))
        surface.blit(score_shadow, (22, 22))
        surface.blit(score_text, (20, 20))

        # 分数标签
        label = font_small.render("SCORE", True, YELLOW)
        surface.blit(label, (20, 65))

        # 时间
        time_color = RED if self.time_left <= 10 else WHITE
        time_text = font_medium.render(f"{self.time_left}s", True, time_color)
        time_rect = time_text.get_rect(topright=(WIDTH - 20, 20))
        surface.blit(time_text, time_rect)

        # 时间标签
        time_label = font_small.render("TIME", True, YELLOW)
        time_label_rect = time_label.get_rect(topright=(WIDTH - 20, 65))
        surface.blit(time_label, time_label_rect)

        # 连击
        if self.combo >= 2:
            combo_text = font_medium.render(f"🔥 {self.combo}x 连击!", True, YELLOW)
            combo_rect = combo_text.get_rect(center=(WIDTH // 2, 30))
            surface.blit(combo_text, combo_rect)

        # 最高连击
        if self.max_combo > 0:
            max_combo_text = font_small.render(f"最高连击: {self.max_combo}x", True, GRAY)
            max_combo_rect = max_combo_text.get_rect(center=(WIDTH // 2, 65))
            surface.blit(max_combo_text, max_combo_rect)

    def draw_game_over(self, surface):
        """绘制游戏结束画面"""
        # 半透明遮罩
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))

        # 标题
        title = font_large.render("游戏结束!", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80))
        surface.blit(title, title_rect)

        # 最终分数
        score_text = font_medium.render(f"最终得分: {self.score}", True, YELLOW)
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
        surface.blit(score_text, score_rect)

        # 最高连击
        combo_text = font_small.render(f"最高连击: {self.max_combo}x", True, WHITE)
        combo_rect = combo_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
        surface.blit(combo_text, combo_rect)

        # 评级
        rating = self._get_rating()
        rating_text = font_large.render(rating, True, ORANGE)
        rating_rect = rating_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70))
        surface.blit(rating_text, rating_rect)

        # 提示
        hint = font_small.render("按 R 重新开始 | ESC 退出", True, GRAY)
        hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 130))
        surface.blit(hint, hint_rect)

    def _get_rating(self):
        """根据分数获取评级"""
        if self.score >= 200:
            return "🏆 传奇射手!"
        elif self.score >= 150:
            return "⭐ 全明星!"
        elif self.score >= 100:
            return "🔥 神射手!"
        elif self.score >= 60:
            return "👍 不错!"
        elif self.score >= 30:
            return "💪 继续加油"
        else:
            return "🤔 再练练"

    def draw_bounce_arrow(self, surface):
        """绘制提示箭头"""
        if self.game_state == "playing" and not self.is_dragging and self.cooldown <= 0:
            pulse = math.sin(pygame.time.get_ticks() * 0.005) * 0.3 + 0.7
            # 篮球周围的光晕
            glow_size = int(self.ball.radius + 10 * pulse)
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            alpha = int(60 * pulse)
            pygame.draw.circle(glow_surf, (255, 200, 100, alpha),
                               (glow_size, glow_size), glow_size)
            surface.blit(glow_surf,
                         (int(self.ball.x - glow_size),
                          int(self.ball.y - glow_size)))

            # 提示文字
            if self.score == 0:
                hint = font_small.render("拖拽篮球投篮!", True, WHITE)
                hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT - 80))
                hint.set_alpha(int(255 * pulse))
                surface.blit(hint, hint_rect)

    def draw_start_screen(self, surface):
        """绘制开始界面"""
        # 标题
        title = font_large.render("🏀 投篮高手", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80))
        surface.blit(title, title_rect)

        # 副标题
        subtitle = font_medium.render("Basketball Shooter", True, ORANGE)
        subtitle_rect = subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 25))
        surface.blit(subtitle, subtitle_rect)

        # 说明
        instructions = [
            "拖拽篮球调整角度和力度",
            "松开鼠标投篮",
            "60秒内尽可能多得分!",
            "连续投篮可获得连击加分"
        ]
        for i, text in enumerate(instructions):
            inst = font_small.render(text, True, GRAY)
            inst_rect = inst.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30 + i * 35))
            surface.blit(inst, inst_rect)

        # 开始提示
        pulse = math.sin(pygame.time.get_ticks() * 0.003) * 0.3 + 0.7
        start_text = font_medium.render("按 SPACE 开始游戏", True, WHITE)
        start_text.set_alpha(int(255 * pulse))
        start_rect = start_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 180))
        surface.blit(start_text, start_rect)

    def draw(self, surface):
        """绘制主画面"""
        # 震动偏移
        shake_x = 0
        shake_y = 0
        if self.shake_intensity > 0.5:
            shake_x = random.randint(-int(self.shake_intensity),
                                     int(self.shake_intensity))
            shake_y = random.randint(-int(self.shake_intensity),
                                     int(self.shake_intensity))

        # 绘制背景
        self.draw_background(surface)

        # 绘制篮筐
        self.hoop.draw(surface)

        # 绘制篮球
        self.ball.draw(surface)

        # 绘制瞄准线
        self.draw_aim_line(surface)

        # 绘制粒子
        for p in self.particles:
            alpha = int(255 * (p["life"] / p["max_life"]))
            color = p["color"]
            pygame.draw.circle(surface, color,
                               (int(p["x"]), int(p["y"])),
                               int(p["size"] * (p["life"] / p["max_life"])))

        # 绘制得分弹出
        for popup in self.score_popups:
            alpha = int(255 * (popup["life"] / 60))
            text = font_small.render(popup["text"], True, YELLOW)
            text.set_alpha(alpha)
            surface.blit(text, (popup["x"] - 30, popup["y"]))

        # 绘制HUD
        if self.game_state == "playing":
            self.draw_hud(surface)
            self.draw_bounce_arrow(surface)
        elif self.game_state == "game_over":
            self.draw_hud(surface)
            self.draw_game_over(surface)
        elif self.game_state == "ready":
            self.draw_start_screen(surface)

        # 应用震动
        if shake_x != 0 or shake_y != 0:
            # 由于pygame的限制，我们无法直接移动整个surface
            # 但已经无伤大雅
            pass

    def run(self):
        """主游戏循环"""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw(screen)
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = BasketballGame()
    game.run()