"""
Helix Jump (螺旋跳) - 小球在旋转平台间弹跳下落
================================================
控制: 鼠标点击 / 空格键 切换旋转方向
目标: 让球通过每层平台的缺口逐层下落
"""

import pygame
import math
import random
import sys

# ====================== 常量配置 ======================
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 720
FPS = 60
BG_COLOR = (15, 15, 35)
BALL_COLOR = (255, 200, 50)
BALL_GLOW = (255, 220, 100)

# 平台层数
NUM_LEVELS = 10
# 每层平台半径（从外到内）
OUTER_RADIUS = 200
INNER_RADIUS = 40
# 球属性
BALL_RADIUS = 10
GRAVITY = 0.15          # 向边缘的"重力"
MAX_R_SPEED = 1.5       # 最大径向速度
FALL_SPEED = 6          # 下落速度


# ====================== 平台类 ======================
class Platform:
    """单个圆形平台，有缺口，可旋转"""

    # 预定义颜色方案（从外到内渐变）
    COLORS = [
        (255, 80, 80),    # 红
        (255, 140, 60),   # 橙
        (255, 200, 50),   # 黄
        (80, 220, 80),    # 绿
        (60, 180, 255),   # 蓝
        (140, 80, 255),   # 紫
        (255, 60, 180),   # 粉
        (60, 255, 220),   # 青
        (255, 180, 60),   # 金
        (200, 100, 255),  # 紫罗兰
    ]

    def __init__(self, level, total_levels):
        # 从外到内计算半径
        radius_range = OUTER_RADIUS - INNER_RADIUS
        t = level / max(total_levels - 1, 1)
        self.radius = OUTER_RADIUS - t * radius_range
        self.level = level
        self.thickness = 18  # 平台厚度

        # 缺口：中心角度（弧度）和大小
        self.gap_center = random.uniform(0, 2 * math.pi)
        self.gap_size = math.radians(random.uniform(50, 75))

        # 旋转
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(1.2, 2.2)
        self.direction = 1  # 1=顺时针, -1=逆时针

        # 颜色
        self.color = self.COLORS[level % len(self.COLORS)]
        self.dark_color = tuple(max(0, c - 60) for c in self.color)
        self.light_color = tuple(min(255, c + 40) for c in self.color)

    def update(self):
        """更新旋转"""
        self.angle += self.speed * self.direction * 0.02

    def toggle_direction(self):
        """切换旋转方向"""
        self.direction *= -1

    def is_in_gap(self, ball_angle):
        """判断球的角度是否在缺口范围内"""
        # 计算球相对于平台的角度
        rel_angle = (ball_angle - self.angle) % (2 * math.pi)
        gap_start = (self.gap_center - self.gap_size / 2) % (2 * math.pi)
        gap_end = (self.gap_center + self.gap_size / 2) % (2 * math.pi)

        if gap_start < gap_end:
            return gap_start <= rel_angle <= gap_end
        else:
            return rel_angle >= gap_start or rel_angle <= gap_end

    def draw(self, screen, cx, cy):
        """绘制平台（带立体感）"""
        # 绘制平台阴影
        pygame.draw.circle(screen, (10, 10, 25), (cx + 3, cy + 3),
                           int(self.radius + 2), int(self.thickness + 2))

        # 绘制平台主体（圆弧）
        # 缺口起始和结束角度
        gap_start = self.angle + self.gap_center - self.gap_size / 2
        gap_end = self.angle + self.gap_center + self.gap_size / 2

        # 绘制圆弧 - 用多个线段模拟
        num_segments = 64
        points = []
        for i in range(num_segments + 1):
            theta = self.angle + (i / num_segments) * 2 * math.pi
            # 跳过缺口范围内的角度
            rel = (theta - self.angle) % (2 * math.pi)
            gap_s = (self.gap_center - self.gap_size / 2) % (2 * math.pi)
            gap_e = (self.gap_center + self.gap_size / 2) % (2 * math.pi)
            in_gap = False
            if gap_s < gap_e:
                in_gap = gap_s <= rel <= gap_e
            else:
                in_gap = rel >= gap_s or rel <= gap_e
            if in_gap:
                continue

            x = cx + self.radius * math.cos(theta)
            y = cy + self.radius * math.sin(theta)
            points.append((x, y))

        if len(points) > 2:
            # 绘制外圈
            if len(points) > 2:
                pygame.draw.lines(screen, self.light_color, True, points, self.thickness + 2)
                pygame.draw.lines(screen, self.color, True, points, self.thickness)
                pygame.draw.lines(screen, self.dark_color, True, points, 2)

        # 绘制缺口标记（发光边缘）
        for sign in [-1, 1]:
            edge_angle = self.angle + self.gap_center + sign * self.gap_size / 2
            ex = cx + self.radius * math.cos(edge_angle)
            ey = cy + self.radius * math.sin(edge_angle)
            pygame.draw.circle(screen, (255, 255, 255, 100), (int(ex), int(ey)), 3)

    def get_center_distance(self):
        """返回平台中心到球心距离的参考值"""
        return self.radius


# ====================== 球类 ======================
class Ball:
    """小球，在平台上移动"""

    def __init__(self, start_radius):
        self.angle = random.uniform(0, 2 * math.pi)  # 角度位置
        self.r = 0  # 径向位置（0=中心，1=边缘）
        self.r_speed = 0  # 径向速度
        self.level = 0  # 当前所在层级
        self.falling = False  # 是否正在下落
        self.fall_timer = 0
        self.alive = True
        self.score = 0
        self.trail = []  # 轨迹

    def update(self, platform, dt):
        """更新球的位置"""
        if not self.alive:
            return

        if self.falling:
            self.fall_timer += 1
            self.r += FALL_SPEED * 0.02 * 5
            if self.fall_timer > 20:
                self.falling = False
                self.fall_timer = 0
                self.level += 1
                self.score += 1
                self.r = 0
                self.r_speed = 0
                # 随机选择新角度
                self.angle = random.uniform(0, 2 * math.pi)
            return

        # 平台旋转带动球移动
        self.angle += platform.speed * platform.direction * 0.02

        # 径向"重力" - 向边缘加速
        self.r_speed += GRAVITY * dt
        self.r_speed = min(self.r_speed, MAX_R_SPEED)
        self.r += self.r_speed * dt

        # 检查是否到达边缘
        if self.r >= 1.0:
            self.r = 1.0
            # 检查是否在缺口
            if platform.is_in_gap(self.angle):
                # 在缺口处，下落
                self.falling = True
                self.fall_timer = 0
            else:
                # 撞到边缘，游戏结束
                self.alive = False

        # 更新轨迹
        self.trail.append((self.angle, self.r, self.level))
        if len(self.trail) > 15:
            self.trail.pop(0)

    def get_screen_pos(self, cx, cy, platform_radius):
        """获取球在屏幕上的位置"""
        dist = self.r * platform_radius
        x = cx + dist * math.cos(self.angle)
        y = cy + dist * math.sin(self.angle)
        return x, y

    def draw(self, screen, cx, cy, platform_radius):
        """绘制球"""
        if not self.alive:
            return

        x, y = self.get_screen_pos(cx, cy, platform_radius)

        # 绘制轨迹
        for i, (ta, tr, tl) in enumerate(self.trail):
            alpha = i / len(self.trail) * 0.4
            td = tr * platform_radius
            tx = cx + td * math.cos(ta)
            ty = cy + td * math.sin(ta)
            size = int(BALL_RADIUS * (0.3 + 0.7 * i / len(self.trail)))
            pygame.draw.circle(screen, (255, 220, 100, int(alpha * 255)),
                               (int(tx), int(ty)), max(1, size))

        # 绘制球体（带发光效果）
        if self.falling:
            # 下落时闪烁
            glow_size = BALL_RADIUS + 8 * math.sin(self.fall_timer * 0.5)
            pygame.draw.circle(screen, BALL_GLOW, (int(x), int(y)), int(glow_size))
        else:
            # 外发光
            pygame.draw.circle(screen, BALL_GLOW, (int(x), int(y)), BALL_RADIUS + 6)
            pygame.draw.circle(screen, BALL_GLOW, (int(x), int(y)), BALL_RADIUS + 3)

        # 球体
        pygame.draw.circle(screen, BALL_COLOR, (int(x), int(y)), BALL_RADIUS)
        # 高光
        highlight_x = x - BALL_RADIUS * 0.3
        highlight_y = y - BALL_RADIUS * 0.3
        pygame.draw.circle(screen, (255, 255, 255),
                           (int(highlight_x), int(highlight_y)), BALL_RADIUS // 3)


# ====================== 粒子系统 ======================
class Particle:
    """下落时的粒子效果"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.life = 1.0
        self.color = random.choice([
            (255, 80, 80), (255, 200, 50), (80, 220, 80),
            (60, 180, 255), (255, 60, 180)
        ])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1
        self.life -= 0.02
        return self.life > 0

    def draw(self, screen):
        alpha = int(self.life * 255)
        size = int(4 * self.life)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), max(1, size))


# ====================== 游戏主类 ======================
class HelixJump:
    """游戏主控"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Helix Jump - 螺旋跳")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simhei", 36, bold=True)
        self.small_font = pygame.font.SysFont("simhei", 22)
        self.big_font = pygame.font.SysFont("simhei", 64, bold=True)

        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2 + 30

        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        # 创建平台
        self.platforms = []
        for i in range(NUM_LEVELS):
            p = Platform(i, NUM_LEVELS)
            self.platforms.append(p)

        # 创建球
        self.ball = Ball(self.platforms[0].radius)

        # 粒子列表
        self.particles = []

        # 游戏状态
        self.game_over = False
        self.won = False
        self.paused = False
        self.combo = 0
        self.high_score = 0

        # 闪烁效果
        self.flash_timer = 0

    def toggle_direction(self):
        """切换当前平台的旋转方向"""
        if not self.game_over and not self.won and not self.ball.falling:
            level = min(self.ball.level, len(self.platforms) - 1)
            self.platforms[level].toggle_direction()

    def spawn_particles(self, x, y, count=15):
        """生成粒子效果"""
        for _ in range(count):
            self.particles.append(Particle(x, y))

    def update(self, dt):
        """更新游戏状态"""
        if self.game_over or self.won or self.paused:
            return

        # 更新粒子
        self.particles = [p for p in self.particles if p.update()]

        # 更新当前平台
        level = min(self.ball.level, len(self.platforms) - 1)
        current_platform = self.platforms[level]
        current_platform.update()

        # 更新球
        old_level = self.ball.level
        self.ball.update(current_platform, dt)

        # 检测球下落时的粒子效果
        if self.ball.falling and self.ball.fall_timer == 1:
            x, y = self.ball.get_screen_pos(
                self.center_x, self.center_y,
                current_platform.radius
            )
            self.spawn_particles(x, y)

        # 检测过关
        if self.ball.level >= NUM_LEVELS:
            self.won = True
            self.ball.alive = True

        # 检测游戏结束
        if not self.ball.alive:
            self.game_over = True
            x, y = self.ball.get_screen_pos(
                self.center_x, self.center_y,
                current_platform.radius
            )
            self.spawn_particles(x, y, 30)

    def draw(self):
        """绘制所有内容"""
        self.screen.fill(BG_COLOR)

        # 绘制背景装饰
        self._draw_background()

        if self.game_over:
            self._draw_game_over()
        elif self.won:
            self._draw_win()
        else:
            # 绘制平台
            level = min(self.ball.level, len(self.platforms) - 1)
            # 从当前层到最内层绘制
            for i in range(level, len(self.platforms)):
                self.platforms[i].draw(self.screen, self.center_x, self.center_y)

            # 绘制粒子
            for p in self.particles:
                p.draw(self.screen)

            # 绘制球
            self.ball.draw(self.screen, self.center_x, self.center_y,
                           self.platforms[level].radius)

            # 绘制UI
            self._draw_ui()

        pygame.display.flip()

    def _draw_background(self):
        """绘制背景装饰"""
        # 绘制网格线
        for r in range(50, 250, 50):
            alpha = max(0, 30 - r // 10)
            pygame.draw.circle(self.screen, (30, 30, 60),
                               (self.center_x, self.center_y), r, 1)

        # 绘制中心装饰
        pygame.draw.circle(self.screen, (30, 30, 60),
                           (self.center_x, self.center_y), 3)

    def _draw_ui(self):
        """绘制UI信息"""
        # 分数
        score_text = self.font.render(f"得分: {self.ball.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, 20))

        # 层级
        level_text = self.small_font.render(
            f"层级: {self.ball.level + 1}/{NUM_LEVELS}", True, (180, 180, 200))
        self.screen.blit(level_text, (20, 65))

        # 操作提示
        hint_text = self.small_font.render("点击/空格切换方向", True, (120, 120, 150))
        self.screen.blit(hint_text, (20, SCREEN_HEIGHT - 40))

        # 当前平台旋转方向指示
        level = min(self.ball.level, len(self.platforms) - 1)
        p = self.platforms[level]
        dir_text = "▶" if p.direction == 1 else "◀"
        dir_color = (100, 255, 100) if p.direction == 1 else (255, 100, 100)
        dir_surf = self.font.render(dir_text, True, dir_color)
        self.screen.blit(dir_surf, (SCREEN_WIDTH - 60, 20))

    def _draw_game_over(self):
        """绘制游戏结束画面"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title = self.big_font.render("游戏结束", True, (255, 80, 80))
        score = self.font.render(f"得分: {self.ball.score}", True, (255, 255, 255))
        restart = self.small_font.render("按 R 重新开始", True, (180, 180, 200))

        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 250))
        self.screen.blit(score, (SCREEN_WIDTH // 2 - score.get_width() // 2, 330))
        self.screen.blit(restart, (SCREEN_WIDTH // 2 - restart.get_width() // 2, 400))

        # 粒子
        for p in self.particles:
            p.draw(self.screen)

    def _draw_win(self):
        """绘制胜利画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title = self.big_font.render("恭喜通关!", True, (80, 255, 80))
        score = self.font.render(f"最终得分: {self.ball.score}", True, (255, 255, 255))
        restart = self.small_font.render("按 R 重新开始", True, (180, 180, 200))

        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 250))
        self.screen.blit(score, (SCREEN_WIDTH // 2 - score.get_width() // 2, 330))
        self.screen.blit(restart, (SCREEN_WIDTH // 2 - restart.get_width() // 2, 400))

    def handle_event(self, event):
        """处理输入事件"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.reset_game()
                return
            if event.key == pygame.K_SPACE:
                if self.game_over or self.won:
                    self.reset_game()
                else:
                    self.toggle_direction()
                return
            if event.key == pygame.K_p:
                self.paused = not self.paused
                return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.game_over or self.won:
                self.reset_game()
            else:
                self.toggle_direction()

    def run(self):
        """游戏主循环"""
        running = True
        dt = 1.0

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.handle_event(event)

            self.update(dt)
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ====================== 入口 ======================
if __name__ == "__main__":
    game = HelixJump()
    game.run()