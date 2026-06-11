"""
水果忍者 (Fruit Ninja)
=======================
使用 Pygame 实现的水果忍者游戏
- 水果从屏幕底部抛出，玩家通过鼠标滑动切割水果
- 切中水果得分，切中炸弹扣分，漏掉水果损失生命
- 难度随分数递增

操作说明:
- 鼠标拖动切割水果
- 按 R 键重新开始
- 按 ESC 或 Q 键退出

作者: AI Game Developer
日期: 2026-06-11
"""

import pygame
import random
import math
import sys

# ==================== 初始化 ====================
pygame.init()

# ==================== 常量配置 ====================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 50, 255)
YELLOW = (255, 255, 50)
ORANGE = (255, 165, 0)
PURPLE = (200, 50, 255)
PINK = (255, 100, 200)
GRAY = (100, 100, 100)
DARK_GRAY = (30, 30, 30)
BROWN = (139, 69, 19)
LIGHT_BLUE = (100, 200, 255)

# 水果类型定义: (名称, 颜色, 半径, 分数, 速度倍率)
FRUIT_TYPES = [
    ("苹果", RED, 20, 1, 1.0),
    ("橙子", ORANGE, 22, 1, 1.0),
    ("西瓜", GREEN, 35, 3, 0.8),
    ("蓝莓", PURPLE, 15, 1, 1.2),
    ("桃子", PINK, 25, 2, 0.9),
    ("柠檬", YELLOW, 18, 1, 1.1),
    ("猕猴桃", BROWN, 20, 2, 1.0),
]

# 游戏状态
STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2


# ==================== 水果类 ====================
class Fruit:
    """水果对象，具有物理抛物线运动"""

    def __init__(self):
        # 随机选择水果类型
        self.type = random.choice(FRUIT_TYPES)
        self.name, self.color, self.radius, self.score_value, self.speed_mult = self.type

        # 初始位置 - 从屏幕底部随机水平位置出现
        self.x = random.randint(self.radius, SCREEN_WIDTH - self.radius)

        # 物理参数 - 向上抛射
        self.gravity = 0.4
        self.vel_x = random.uniform(-3, 3) * self.speed_mult
        self.vel_y = random.uniform(-14, -10) * self.speed_mult

        # 保证初始向上速度
        if self.vel_y >= 0:
            self.vel_y = -12 * self.speed_mult

        self.y = SCREEN_HEIGHT + self.radius

        # 旋转角度
        self.angle = 0
        self.rot_speed = random.uniform(-5, 5)

        # 是否已被切割
        self.sliced = False
        # 切割后的两半
        self.halves = []
        # 切割后的粒子效果
        self.particles = []

        # 是否已被计分或扣分
        self.scored = False

    def update(self):
        """更新水果物理位置"""
        if self.sliced:
            # 更新两半
            for half in self.halves[:]:
                half["x"] += half["vx"]
                half["y"] += half["vy"]
                half["vy"] += 0.5
                half["life"] -= 1
                half["angle"] += half["rot_speed"]
                if half["life"] <= 0:
                    self.halves.remove(half)

            # 更新粒子
            for p in self.particles[:]:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 0.2
                p["life"] -= 1
                p["vx"] *= 0.98
                if p["life"] <= 0:
                    self.particles.remove(p)
            return True

        # 物理更新
        self.vel_y += self.gravity
        self.x += self.vel_x
        self.y += self.vel_y
        self.angle += self.rot_speed

        # 超出屏幕范围 - 移除
        if self.y > SCREEN_HEIGHT + 100:
            return False
        if self.x < -100 or self.x > SCREEN_WIDTH + 100:
            return False
        return True

    def slice(self, slice_angle):
        """切割水果，产生两半和粒子"""
        self.sliced = True
        # 创建两半
        for i in (-1, 1):
            half = {
                "x": self.x,
                "y": self.y,
                "vx": self.vel_x + i * random.uniform(1, 3),
                "vy": self.vel_y - random.uniform(0, 2),
                "angle": self.angle,
                "rot_speed": self.rot_speed + i * random.uniform(1, 4),
                "life": 40,
                "side": i,
            }
            self.halves.append(half)

        # 创建粒子 (果汁飞溅效果)
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            p = {
                "x": self.x,
                "y": self.y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 2,
                "life": random.randint(15, 30),
                "size": random.randint(3, 6),
            }
            self.particles.append(p)

    def draw(self, screen):
        """绘制水果"""
        if self.sliced:
            # 绘制两半
            for half in self.halves:
                # 半圆绘制
                rect = pygame.Rect(
                    int(half["x"] - self.radius),
                    int(half["y"] - self.radius),
                    self.radius * 2,
                    self.radius * 2,
                )
                # 绘制半圆
                start_angle = math.radians(half["angle"])
                if half["side"] > 0:
                    start_angle += math.pi / 2
                else:
                    start_angle -= math.pi / 2

                # 用圆弧近似画半圆 (画扇形)
                points = [(half["x"], half["y"])]
                for a in range(0, 190, 10):
                    ang = start_angle + math.radians(a)
                    px = half["x"] + self.radius * math.cos(ang)
                    py = half["y"] + self.radius * math.sin(ang)
                    points.append((px, py))
                if len(points) > 2:
                    pygame.draw.polygon(screen, self.color, points)
                    pygame.draw.polygon(screen, WHITE, points, 1)

            # 绘制粒子
            for p in self.particles:
                alpha = p["life"] / 30
                color = (
                    int(self.color[0] * alpha),
                    int(self.color[1] * alpha),
                    int(self.color[2] * alpha),
                )
                pygame.draw.circle(screen, color, (int(p["x"]), int(p["y"])), p["size"])
            return

        # 正常水果绘制 - 圆形水果
        # 外发光
        glow_rect = pygame.Rect(
            int(self.x - self.radius - 4),
            int(self.y - self.radius - 4),
            (self.radius + 4) * 2,
            (self.radius + 4) * 2,
        )
        pygame.draw.ellipse(screen, (*self.color, 50), glow_rect, 2)

        # 主水果
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

        # 高光效果
        highlight_x = int(self.x - self.radius * 0.3)
        highlight_y = int(self.y - self.radius * 0.3)
        highlight_r = int(self.radius * 0.35)
        pygame.draw.circle(
            screen,
            (min(self.color[0] + 100, 255), min(self.color[1] + 100, 255),
             min(self.color[2] + 100, 255)),
            (highlight_x, highlight_y),
            highlight_r,
        )

        # 亮斑
        spot_x = int(self.x - self.radius * 0.15)
        spot_y = int(self.y - self.radius * 0.15)
        pygame.draw.circle(screen, WHITE, (spot_x, spot_y), int(self.radius * 0.15))


# ==================== 炸弹类 ====================
class Bomb:
    """炸弹 - 切中会扣分"""

    def __init__(self):
        self.radius = 22
        self.x = random.randint(self.radius, SCREEN_WIDTH - self.radius)
        self.gravity = 0.4
        self.vel_x = random.uniform(-2, 2)
        self.vel_y = random.uniform(-12, -9)
        self.y = SCREEN_HEIGHT + self.radius
        self.sliced = False
        self.exploded = False
        self.explosion_particles = []
        self.angle = 0

    def update(self):
        """更新炸弹物理"""
        if self.exploded:
            for p in self.explosion_particles[:]:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 0.15
                p["life"] -= 1
                p["size"] *= 0.98
                if p["life"] <= 0:
                    self.explosion_particles.remove(p)
            return len(self.explosion_particles) > 0

        self.vel_y += self.gravity
        self.x += self.vel_x
        self.y += self.vel_y
        self.angle += 3

        if self.y > SCREEN_HEIGHT + 80:
            return False
        if self.x < -80 or self.x > SCREEN_WIDTH + 80:
            return False
        return True

    def explode(self):
        """炸弹爆炸"""
        self.exploded = True
        for _ in range(25):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            self.explosion_particles.append({
                "x": self.x,
                "y": self.y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.randint(20, 40),
                "size": random.uniform(3, 8),
            })

    def draw(self, screen):
        """绘制炸弹"""
        if self.exploded:
            for p in self.explosion_particles:
                alpha = p["life"] / 40
                r = int(255 * alpha)
                g = int(150 * alpha)
                b = int(50 * alpha)
                pygame.draw.circle(
                    screen, (r, g, b), (int(p["x"]), int(p["y"])), int(p["size"])
                )
            return

        # 炸弹主体 - 黑色圆形
        pygame.draw.circle(screen, DARK_GRAY, (int(self.x), int(self.y)), self.radius)

        # 引信
        fuse_top = (int(self.x + 10), int(self.y - self.radius - 5))
        fuse_bottom = (int(self.x + 8), int(self.y - self.radius + 5))
        pygame.draw.line(screen, BROWN, fuse_bottom, fuse_top, 3)

        # 火花
        spark_radius = 4 + random.randint(0, 3)
        pygame.draw.circle(
            screen, (255, random.randint(100, 200), 0),
            (int(self.x + 10), int(self.y - self.radius - 8)),
            spark_radius,
        )

        # X 标记
        offset = int(self.radius * 0.35)
        pygame.draw.line(
            screen, RED,
            (int(self.x - offset), int(self.y - offset)),
            (int(self.x + offset), int(self.y + offset)),
            3,
        )
        pygame.draw.line(
            screen, RED,
            (int(self.x + offset), int(self.y - offset)),
            (int(self.x - offset), int(self.y + offset)),
            3,
        )


# ==================== 刀刃轨迹 ====================
class BladeTrail:
    """鼠标滑动的刀刃轨迹效果"""

    def __init__(self):
        self.points = []
        self.max_points = 20
        self.min_distance = 5

    def add_point(self, pos):
        """添加轨迹点"""
        if self.points:
            last = self.points[-1]
            dx = pos[0] - last[0]
            dy = pos[1] - last[1]
            if math.sqrt(dx * dx + dy * dy) < self.min_distance:
                return
        self.points.append(pos)
        if len(self.points) > self.max_points:
            self.points.pop(0)

    def draw(self, screen):
        """绘制刀刃轨迹"""
        if len(self.points) < 2:
            return

        for i in range(len(self.points) - 1):
            alpha = i / len(self.points)
            width = int((alpha + 0.3) * 6)
            color = (
                int(200 + 55 * alpha),
                int(200 + 55 * alpha),
                int(255),
            )
            pygame.draw.line(
                screen, color,
                (int(self.points[i][0]), int(self.points[i][1])),
                (int(self.points[i + 1][0]), int(self.points[i + 1][1])),
                width,
            )

    def clear(self):
        """清空轨迹"""
        self.points.clear()


# ==================== 粒子特效 ====================
class ScorePopup:
    """得分/扣分弹出文字"""

    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 40
        self.vel_y = -2

    def update(self):
        self.y += self.vel_y
        self.life -= 1
        return self.life > 0

    def draw(self, screen, font):
        if self.life > 0:
            alpha = min(255, self.life * 8)
            text_surf = font.render(self.text, True, self.color)
            text_surf.set_alpha(alpha)
            screen.blit(text_surf, (int(self.x - text_surf.get_width() / 2), int(self.y)))


# ==================== 主游戏类 ====================
class FruitNinjaGame:
    """水果忍者游戏主类"""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("水果忍者 - Fruit Ninja")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 28)

        # 游戏状态
        self.state = STATE_MENU
        self.score = 0
        self.high_score = self.load_high_score()
        self.lives = 3
        self.combo = 0
        self.max_combo = 0
        self.difficulty = 1

        # 游戏对象
        self.fruits = []
        self.bombs = []
        self.blade = BladeTrail()
        self.popups = []
        self.stars = []

        # 生成控制
        self.spawn_timer = 0
        self.spawn_interval = 40
        self.bomb_chance = 0.15

        # 背景星星
        for _ in range(50):
            self.stars.append({
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(0, SCREEN_HEIGHT),
                "size": random.randint(1, 3),
                "speed": random.uniform(0.1, 0.5),
                "brightness": random.randint(100, 255),
            })

        # 当前鼠标位置
        self.mouse_pos = (0, 0)
        self.mouse_pressed = False
        self.mouse_travelled = False
        self.start_pos = None

    def load_high_score(self):
        """读取最高分"""
        try:
            with open("fruit_ninja_highscore.txt", "r") as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return 0

    def save_high_score(self):
        """保存最高分"""
        try:
            with open("fruit_ninja_highscore.txt", "w") as f:
                f.write(str(self.high_score))
        except IOError:
            pass

    def reset_game(self):
        """重置游戏"""
        self.score = 0
        self.lives = 3
        self.combo = 0
        self.max_combo = 0
        self.difficulty = 1
        self.fruits.clear()
        self.bombs.clear()
        self.blade.clear()
        self.popups.clear()
        self.spawn_timer = 0
        self.spawn_interval = 40
        self.bomb_chance = 0.15

    def spawn_fruit(self):
        """生成一个水果"""
        self.fruits.append(Fruit())

    def spawn_bomb(self):
        """生成一个炸弹"""
        self.bombs.append(Bomb())

    def spawn_random(self):
        """随机生成水果或炸弹"""
        if random.random() < self.bomb_chance:
            self.spawn_bomb()
        # 有时一次生成多个水果
        count = 1
        if self.difficulty >= 3 and random.random() < 0.3:
            count = 2
        if self.difficulty >= 5 and random.random() < 0.2:
            count = 3
        for _ in range(count):
            self.spawn_fruit()

    def check_slice(self, start, end):
        """检查鼠标滑动是否切割了水果或炸弹"""
        sliced_anything = False

        # 检查水果
        for fruit in self.fruits[:]:
            if fruit.sliced:
                continue
            if self.point_to_segment_distance(
                (fruit.x, fruit.y), start, end
            ) < fruit.radius + 10:
                # 计算切割角度
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                slice_angle = math.atan2(dy, dx)
                fruit.slice(slice_angle)
                self.score += fruit.score_value
                self.combo += 1
                if self.combo > self.max_combo:
                    self.max_combo = self.combo
                sliced_anything = True

                # 连击加分
                combo_bonus = ""
                if self.combo >= 3:
                    bonus = self.combo * 2
                    self.score += bonus
                    combo_bonus = f" 连击x{self.combo} +{bonus}!"

                # 弹出得分文字
                popup_text = f"+{fruit.score_value}{combo_bonus}"
                self.popups.append(
                    ScorePopup(fruit.x, fruit.y - 20, popup_text, GREEN)
                )

        # 检查炸弹
        for bomb in self.bombs[:]:
            if bomb.exploded:
                continue
            if self.point_to_segment_distance(
                (bomb.x, bomb.y), start, end
            ) < bomb.radius + 10:
                bomb.explode()
                self.score = max(0, self.score - 5)
                self.combo = 0
                self.popups.append(
                    ScorePopup(bomb.x, bomb.y - 20, "-5 炸弹！", RED)
                )
                sliced_anything = True

        return sliced_anything

    @staticmethod
    def point_to_segment_distance(point, seg_start, seg_end):
        """计算点到线段的最短距离"""
        px, py = point
        sx, sy = seg_start
        ex, ey = seg_end

        dx = ex - sx
        dy = ey - sy

        if dx == 0 and dy == 0:
            return math.sqrt((px - sx) ** 2 + (py - sy) ** 2)

        t = ((px - sx) * dx + (py - sy) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))

        nearest_x = sx + t * dx
        nearest_y = sy + t * dy

        return math.sqrt((px - nearest_x) ** 2 + (py - nearest_y) ** 2)

    def update_difficulty(self):
        """根据分数调整难度"""
        new_difficulty = min(10, self.score // 15 + 1)
        if new_difficulty != self.difficulty:
            self.difficulty = new_difficulty
            self.spawn_interval = max(15, 40 - self.difficulty * 2)
            self.bomb_chance = min(0.35, 0.15 + self.difficulty * 0.02)

    def handle_events(self):
        """处理输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    return False
                if event.key == pygame.K_r:
                    self.reset_game()
                    self.state = STATE_PLAYING
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    if self.state == STATE_MENU:
                        self.reset_game()
                        self.state = STATE_PLAYING
                    elif self.state == STATE_GAME_OVER:
                        self.reset_game()
                        self.state = STATE_PLAYING

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    self.mouse_pressed = True
                    self.start_pos = event.pos
                    self.mouse_travelled = False
                    self.blade.add_point(event.pos)

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if self.state == STATE_MENU:
                        self.reset_game()
                        self.state = STATE_PLAYING
                    elif self.state == STATE_GAME_OVER:
                        self.reset_game()
                        self.state = STATE_PLAYING
                    self.mouse_pressed = False
                    if self.mouse_travelled and self.state == STATE_PLAYING:
                        self.check_slice(self.start_pos, self.mouse_pos)
                    self.blade.clear()
                    self.mouse_travelled = False

            if event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos
                if self.mouse_pressed:
                    dx = event.pos[0] - self.start_pos[0]
                    dy = event.pos[1] - self.start_pos[1]
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist > 15:
                        self.mouse_travelled = True
                    self.blade.add_point(event.pos)

        return True

    def update(self):
        """更新游戏逻辑"""
        if self.state != STATE_PLAYING:
            return

        # 更新难度
        self.update_difficulty()

        # 生成水果和炸弹
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            self.spawn_random()

        # 更新水果
        for fruit in self.fruits[:]:
            alive = fruit.update()
            if not alive:
                # 如果水果未被切割且落出屏幕，扣生命
                if not fruit.sliced and not fruit.scored:
                    fruit.scored = True
                    self.lives -= 1
                    self.combo = 0
                    if self.lives <= 0:
                        self.state = STATE_GAME_OVER
                        if self.score > self.high_score:
                            self.high_score = self.score
                            self.save_high_score()
                self.fruits.remove(fruit)

        # 更新炸弹
        for bomb in self.bombs[:]:
            alive = bomb.update()
            if not alive:
                self.bombs.remove(bomb)

        # 更新弹出文字
        for popup in self.popups[:]:
            if not popup.update():
                self.popups.remove(popup)

    def draw_background(self):
        """绘制背景"""
        # 渐变背景
        for y in range(SCREEN_HEIGHT):
            r = int(20 + (y / SCREEN_HEIGHT) * 30)
            g = int(10 + (y / SCREEN_HEIGHT) * 20)
            b = int(40 + (y / SCREEN_HEIGHT) * 30)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # 星星
        for star in self.stars:
            pygame.draw.circle(
                self.screen,
                (star["brightness"], star["brightness"], star["brightness"]),
                (int(star["x"]), int(star["y"])),
                star["size"],
            )

    def draw_ui(self):
        """绘制UI界面"""
        # 分数
        score_text = self.font_medium.render(f"分数: {self.score}", True, WHITE)
        self.screen.blit(score_text, (20, 20))

        # 最高分
        hs_text = self.font_small.render(f"最高分: {self.high_score}", True, YELLOW)
        self.screen.blit(hs_text, (20, 60))

        # 生命 (用红心表示)
        heart_x = SCREEN_WIDTH - 120
        for i in range(3):
            color = RED if i < self.lives else DARK_GRAY
            cx = heart_x + i * 35
            cy = 35
            # 简易心形
            pygame.draw.circle(self.screen, color, (cx - 7, cy), 9)
            pygame.draw.circle(self.screen, color, (cx + 7, cy), 9)
            pygame.draw.polygon(
                self.screen, color,
                [(cx - 14, cy - 2), (cx + 14, cy - 2), (cx, cy + 14)],
            )

        # 连击显示
        if self.combo >= 2 and self.state == STATE_PLAYING:
            combo_text = self.font_medium.render(f"连击 x{self.combo}!", True, YELLOW)
            combo_rect = combo_text.get_rect(center=(SCREEN_WIDTH // 2, 40))
            self.screen.blit(combo_text, combo_rect)

        # 难度
        diff_text = self.font_small.render(f"难度 Lv.{self.difficulty}", True, LIGHT_BLUE)
        self.screen.blit(diff_text, (SCREEN_WIDTH - 150, 90))

    def draw_menu(self):
        """绘制主菜单"""
        self.draw_background()

        # 标题
        title = self.font_large.render("水果忍者", True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 180))
        self.screen.blit(title, title_rect)

        # 副标题
        subtitle = self.font_medium.render("Fruit Ninja", True, ORANGE)
        sub_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 230))
        self.screen.blit(subtitle, sub_rect)

        # 操作说明
        instructions = [
            "鼠标拖动 切割水果得分",
            "避开炸弹! 切中炸弹扣5分",
            "漏掉水果会损失生命",
            "",
            "点击 或 按空格键 开始游戏",
        ]
        y_offset = 310
        for line in instructions:
            text = self.font_small.render(line, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 35

        # 最高分
        if self.high_score > 0:
            hs_text = self.font_medium.render(f"最高分: {self.high_score}", True, YELLOW)
            hs_rect = hs_text.get_rect(center=(SCREEN_WIDTH // 2, 480))
            self.screen.blit(hs_text, hs_rect)

        # 装饰水果 (不可切割的展示水果)
        self._draw_decorative_fruits()

    def _draw_decorative_fruits(self):
        """绘制菜单装饰水果"""
        decorative = [
            (150, 400, RED, 25),
            (650, 380, ORANGE, 28),
            (400, 500, GREEN, 30),
            (200, 480, PURPLE, 18),
            (600, 500, PINK, 22),
        ]
        for x, y, color, r in decorative:
            pygame.draw.circle(self.screen, color, (x, y), r)
            hl = (min(color[0] + 100, 255), min(color[1] + 100, 255), min(color[2] + 100, 255))
            pygame.draw.circle(self.screen, hl, (x - r // 3, y - r // 3), r // 3)

    def draw_game_over(self):
        """绘制游戏结束画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # 游戏结束标题
        title = self.font_large.render("游戏结束", True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 170))
        self.screen.blit(title, title_rect)

        # 最终得分
        score_text = self.font_medium.render(f"最终得分: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
        self.screen.blit(score_text, score_rect)

        # 最高分
        hs_text = self.font_small.render(f"最高分: {self.high_score}", True, YELLOW)
        hs_rect = hs_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
        self.screen.blit(hs_text, hs_rect)

        # 最高连击
        combo_text = self.font_small.render(f"最高连击: {self.max_combo}", True, ORANGE)
        combo_rect = combo_text.get_rect(center=(SCREEN_WIDTH // 2, 340))
        self.screen.blit(combo_text, combo_rect)

        # 提示
        hint1 = self.font_small.render("点击 或 按 R 键重新开始", True, WHITE)
        hint1_rect = hint1.get_rect(center=(SCREEN_WIDTH // 2, 420))
        self.screen.blit(hint1, hint1_rect)

        hint2 = self.font_small.render("按 ESC 或 Q 退出", True, GRAY)
        hint2_rect = hint2.get_rect(center=(SCREEN_WIDTH // 2, 460))
        self.screen.blit(hint2, hint2_rect)

    def draw(self):
        """绘制画面"""
        self.screen.fill(BLACK)

        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_PLAYING:
            self.draw_background()

            # 绘制所有对象
            for fruit in self.fruits:
                fruit.draw(self.screen)
            for bomb in self.bombs:
                bomb.draw(self.screen)

            # 刀刃轨迹
            self.blade.draw(self.screen)

            # 弹出文字
            for popup in self.popups:
                popup.draw(self.screen, self.font_small)

            # UI
            self.draw_ui()
        elif self.state == STATE_GAME_OVER:
            # 仍在绘制游戏场景但加上蒙层
            self.draw_background()
            for fruit in self.fruits:
                fruit.draw(self.screen)
            for bomb in self.bombs:
                bomb.draw(self.screen)
            self.draw_game_over()

        pygame.display.flip()

    def run(self):
        """游戏主循环"""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ==================== 程序入口 ====================
if __name__ == "__main__":
    game = FruitNinjaGame()
    game.run()