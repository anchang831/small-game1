"""
滑雪冒险 (Skiing Adventure) - 极速滑雪躲避障碍
=============================================
操作方式：
  ← →  左右转向
  ↓    加速
  SPACE 重新开始
  ESC   退出

游戏规则：
  - 控制滑雪者从山顶滑下，速度逐渐加快
  - 躲避树木(绿色)和岩石(灰色)
  - 收集旗帜(金色)获得加分
  - 撞到障碍物游戏结束
  - 坚持越久得分越高

作者: AI Game Generator
日期: 2026-08-17
"""

import pygame
import random
import math
import sys

# ==================== 初始化 ====================
pygame.init()

# 屏幕参数
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("滑雪冒险 Skiing Adventure")
clock = pygame.time.Clock()
font_large = pygame.font.SysFont("simhei", 48, bold=True)
font_mid = pygame.font.SysFont("simhei", 28)
font_small = pygame.font.SysFont("simhei", 20)

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GREEN = (30, 160, 50)
DARK_GREEN = (10, 120, 30)
BLUE = (100, 150, 255)
GRAY = (120, 120, 120)
DARK_GRAY = (80, 80, 80)
YELLOW = (255, 215, 0)
GOLD = (255, 200, 0)
BROWN = (139, 69, 19)
SKY_BLUE = (180, 210, 255)
SNOW_WHITE = (240, 245, 255)
SKIER_COLOR = (220, 50, 50)

# ==================== 游戏常量 ====================
SNOW_PARTICLES = 80          # 下雪粒子数
TREE_COUNT = 7               # 同时存在的树木数量
ROCK_COUNT = 4               # 同时存在的岩石数量
FLAG_COUNT = 2               # 同时存在的旗帜数量
BASE_SPEED = 4.0             # 基础速度
MAX_SPEED = 12.0             # 最大速度
OBSTACLE_SPEED_FACTOR = 1.0  # 障碍物速度倍率
INITIAL_SPEED_BOOST = 0.0    # 起始速度加成

# 滑雪者尺寸
SKIER_WIDTH = 24
SKIER_HEIGHT = 32

# 地形参数
LANE_COUNT = 5               # 车道数
LANE_WIDTH = WIDTH / LANE_COUNT  # 每车道宽度

# ==================== 辅助函数 ====================
def draw_text(text, font, color, x, y, center=True):
    """绘制文字"""
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)


class Snowflake:
    """雪花粒子"""
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(-HEIGHT, 0)
        self.size = random.uniform(2, 5)
        self.speed = random.uniform(1, 3)
        self.drift = random.uniform(-0.5, 0.5)
        self.alpha = random.randint(150, 255)

    def update(self, speed):
        self.y += self.speed + speed * 0.2
        self.x += self.drift
        if self.y > HEIGHT:
            self.reset()
            self.y = -5
        if self.x < 0:
            self.x = WIDTH
        elif self.x > WIDTH:
            self.x = 0

    def draw(self):
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, self.alpha),
                           (int(self.size), int(self.size)), int(self.size))
        screen.blit(s, (int(self.x - self.size), int(self.y - self.size)))


class Skier:
    """滑雪者"""
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 150
        self.width = SKIER_WIDTH
        self.height = SKIER_HEIGHT
        self.target_x = self.x
        self.tilt = 0  # 倾斜角度

    def move_left(self):
        self.target_x = max(self.width // 2, self.target_x - LANE_WIDTH)
        self.tilt = -15

    def move_right(self):
        self.target_x = min(WIDTH - self.width // 2, self.target_x + LANE_WIDTH)
        self.tilt = 15

    def update(self):
        # 平滑移动
        dx = self.target_x - self.x
        self.x += dx * 0.15
        if abs(dx) < 0.5:
            self.x = self.target_x
            self.tilt = 0

    def draw(self):
        # 绘制滑雪者身体
        body_points = [
            (self.x, self.y - self.height // 2),  # 头
            (self.x - self.width // 2, self.y + self.height // 4),  # 左下
            (self.x + self.width // 2, self.y + self.height // 4),  # 右下
        ]
        # 身体偏移
        body_y = self.y - self.height // 4
        head = (self.x, self.y - self.height // 2)
        left_shoulder = (self.x - self.width // 3, body_y)
        right_shoulder = (self.x + self.width // 3, body_y)
        left_hip = (self.x - self.width // 4, self.y + self.height // 6)
        right_hip = (self.x + self.width // 4, self.y + self.height // 6)

        # 滑雪板
        board_offset = 14
        pygame.draw.line(screen, BROWN,
                         (self.x - board_offset, self.y + self.height // 4),
                         (self.x - board_offset - 8, self.y + self.height // 2 + 4), 4)
        pygame.draw.line(screen, BROWN,
                         (self.x + board_offset, self.y + self.height // 4),
                         (self.x + board_offset + 8, self.y + self.height // 2 + 4), 4)

        # 腿
        pygame.draw.line(screen, BLACK, left_hip,
                         (self.x - board_offset, self.y + self.height // 4), 3)
        pygame.draw.line(screen, BLACK, right_hip,
                         (self.x + board_offset, self.y + self.height // 4), 3)

        # 身体（倾斜）
        tilt_rad = math.radians(self.tilt)
        cos_t = math.cos(tilt_rad)
        sin_t = math.sin(tilt_rad)
        cx, cy = self.x, body_y

        body_w = self.width // 2
        body_h = self.height // 3
        # 身体旋转的四个点
        b1 = (cx - body_w * cos_t + body_h * sin_t,
              cy - body_w * sin_t - body_h * cos_t)
        b2 = (cx + body_w * cos_t + body_h * sin_t,
              cy + body_w * sin_t - body_h * cos_t)
        b3 = (cx + body_w * cos_t - body_h * sin_t,
              cy + body_w * sin_t + body_h * cos_t)
        b4 = (cx - body_w * cos_t - body_h * sin_t,
              cy - body_w * sin_t + body_h * cos_t)
        pygame.draw.polygon(screen, SKIER_COLOR, [b1, b2, b3, b4])

        # 头
        pygame.draw.circle(screen, (255, 200, 180), (int(self.x), int(self.y - self.height // 2 - 4)), 10)

        # 帽子
        hat_points = [
            (self.x - 10, self.y - self.height // 2 - 8),
            (self.x + 10, self.y - self.height // 2 - 8),
            (self.x + 8, self.y - self.height // 2 - 18),
            (self.x - 8, self.y - self.height // 2 - 18),
        ]
        pygame.draw.polygon(screen, RED, hat_points)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y - self.height // 2 - 4)), 10, 1)

        # 滑雪杖
        pole_len = 30
        pygame.draw.line(screen, (100, 100, 100),
                         (self.x - 18, self.y + 6),
                         (self.x - 18, self.y + 6 + pole_len), 2)
        pygame.draw.line(screen, (100, 100, 100),
                         (self.x + 18, self.y + 6),
                         (self.x + 18, self.y + 6 + pole_len), 2)

    def get_rect(self):
        """获取碰撞矩形"""
        return pygame.Rect(self.x - self.width // 2 + 4,
                           self.y - self.height // 2 + 4,
                           self.width - 8,
                           self.height - 8)

    def get_center(self):
        return (self.x, self.y)


class Obstacle:
    """障碍物 (树木/岩石)"""
    def __init__(self, obs_type, lane, speed):
        self.type = obs_type  # 'tree' or 'rock'
        self.lane = lane
        self.x = (lane + 0.5) * LANE_WIDTH
        self.y = -random.randint(30, 120)
        self.speed = speed
        self.passed = False  # 是否已越过玩家

        if obs_type == 'tree':
            self.size = random.randint(22, 32)
            self.color = random.choice([GREEN, DARK_GREEN, (50, 180, 70)])
        else:  # rock
            self.size = random.randint(18, 28)
            self.color = random.choice([GRAY, DARK_GRAY, (140, 130, 120)])

    def update(self, speed):
        self.y += speed
        return self.y > HEIGHT + 50

    def draw(self):
        if self.type == 'tree':
            # 树冠
            crown_size = self.size
            pygame.draw.polygon(screen, self.color, [
                (self.x, self.y - crown_size),
                (self.x - crown_size, self.y + crown_size // 2),
                (self.x + crown_size, self.y + crown_size // 2),
            ])
            # 树干
            trunk_w = 4
            trunk_h = crown_size // 2
            pygame.draw.rect(screen, BROWN,
                             (self.x - trunk_w // 2, self.y + crown_size // 2,
                              trunk_w, trunk_h))
            # 雪堆积
            pygame.draw.ellipse(screen, SNOW_WHITE,
                                (self.x - crown_size // 2, self.y - crown_size - 3,
                                 crown_size, crown_size // 3))
        else:  # rock
            pygame.draw.circle(screen, self.color,
                               (int(self.x), int(self.y)), self.size)
            # 高光
            highlight = (min(self.color[0] + 40, 255),
                         min(self.color[1] + 40, 255),
                         min(self.color[2] + 40, 255))
            pygame.draw.circle(screen, highlight,
                               (int(self.x - self.size // 4),
                                int(self.y - self.size // 4)),
                               self.size // 3)
            # 雪顶
            pygame.draw.ellipse(screen, SNOW_WHITE,
                                (self.x - self.size // 2, self.y - self.size - 2,
                                 self.size, self.size // 3))

    def get_rect(self):
        factor = 0.75
        s = int(self.size * factor)
        return pygame.Rect(self.x - s, self.y - s, s * 2, s * 2)


class Flag:
    """旗帜(收集品)"""
    def __init__(self, lane, speed):
        self.lane = lane
        self.x = (lane + 0.5) * LANE_WIDTH
        self.y = -random.randint(20, 80)
        self.speed = speed
        self.collected = False
        self.wave_offset = random.uniform(0, math.pi * 2)

    def update(self, speed):
        self.y += speed
        self.wave_offset += 0.05
        return self.y > HEIGHT + 50

    def draw(self):
        if self.collected:
            return
        # 旗杆
        pygame.draw.line(screen, (200, 180, 150),
                         (self.x, self.y + 15),
                         (self.x, self.y - 15), 3)
        # 旗帜（飘动效果）
        wave = math.sin(self.wave_offset) * 3
        flag_points = [
            (self.x, self.y - 12),
            (self.x + 14 + wave, self.y - 4),
            (self.x, self.y + 4),
        ]
        pygame.draw.polygon(screen, GOLD, flag_points)
        # 发光
        glow = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 215, 0, 40),
                           (20, 20), 20)
        screen.blit(glow, (int(self.x - 20), int(self.y - 20)))

    def get_rect(self):
        return pygame.Rect(self.x - 10, self.y - 15, 24, 30)


class SkiGame:
    """游戏主类"""
    def __init__(self):
        self.reset()

    def reset(self):
        self.skier = Skier()
        self.snowflakes = [Snowflake() for _ in range(SNOW_PARTICLES)]
        self.obstacles = []
        self.flags = []
        self.score = 0
        self.distance = 0
        self.speed = BASE_SPEED
        self.game_over = False
        self.start_delay = 60  # 游戏开始前准备帧数
        self.combo = 0       # 连续收集旗帜连击
        self.max_combo = 0
        self.flags_collected = 0
        self.high_score = self.load_high_score()

        # 初始生成一些障碍物和旗帜
        for _ in range(TREE_COUNT):
            lane = random.randint(0, LANE_COUNT - 1)
            obs_type = random.choice(['tree', 'tree', 'rock'])
            obs = Obstacle(obs_type, lane, self.speed * OBSTACLE_SPEED_FACTOR)
            obs.y = random.randint(-HEIGHT, -30)
            self.obstacles.append(obs)
        for _ in range(FLAG_COUNT):
            lane = random.randint(0, LANE_COUNT - 1)
            flag = Flag(lane, self.speed * OBSTACLE_SPEED_FACTOR)
            flag.y = random.randint(-HEIGHT, -50)
            self.flags.append(flag)

    def load_high_score(self):
        """加载最高分"""
        try:
            with open("skiing_highscore.txt", "r") as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return 0

    def save_high_score(self):
        """保存最高分"""
        try:
            with open("skiing_highscore.txt", "w") as f:
                f.write(str(self.high_score))
        except:
            pass

    def handle_input(self, keys):
        if self.game_over:
            if keys[pygame.K_SPACE]:
                self.reset()
            return

        if self.start_delay > 0:
            return

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.skier.move_left()
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.skier.move_right()
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.speed = min(MAX_SPEED, self.speed + 0.1)

    def update(self):
        if self.game_over:
            return

        if self.start_delay > 0:
            self.start_delay -= 1
            # 在准备阶段也更新雪花飘落
            for sf in self.snowflakes:
                sf.update(0)
            return

        # 更新滑雪者
        self.skier.update()

        # 更新距离和分数
        self.distance += 1
        if self.distance % 5 == 0:
            self.score += 1

        # 逐渐加速
        if self.speed < MAX_SPEED:
            self.speed += 0.003

        # 更新雪花
        for sf in self.snowflakes:
            sf.update(self.speed * 0.5)

        # 生成障碍物
        current_trees = sum(1 for o in self.obstacles if o.type == 'tree')
        current_rocks = sum(1 for o in self.obstacles if o.type == 'rock')

        if current_trees < TREE_COUNT and random.random() < 0.02:
            lane = random.randint(0, LANE_COUNT - 1)
            # 避免在同一车道生成
            if not any(abs(o.lane - lane) < 1 and o.y > -100 for o in self.obstacles):
                obs = Obstacle('tree', lane, self.speed * OBSTACLE_SPEED_FACTOR)
                self.obstacles.append(obs)

        if current_rocks < ROCK_COUNT and random.random() < 0.015:
            lane = random.randint(0, LANE_COUNT - 1)
            if not any(abs(o.lane - lane) < 1 and o.y > -100 for o in self.obstacles):
                obs = Obstacle('rock', lane, self.speed * OBSTACLE_SPEED_FACTOR)
                self.obstacles.append(obs)

        # 生成旗帜
        if len(self.flags) < FLAG_COUNT and random.random() < 0.01:
            lane = random.randint(0, LANE_COUNT - 1)
            if not any(abs(f.lane - lane) < 1 and f.y > -100 for f in self.flags):
                flag = Flag(lane, self.speed * OBSTACLE_SPEED_FACTOR)
                self.flags.append(flag)

        # 更新障碍物
        self.obstacles = [o for o in self.obstacles if not o.update(self.speed * OBSTACLE_SPEED_FACTOR)]
        self.flags = [f for f in self.flags if not f.update(self.speed * OBSTACLE_SPEED_FACTOR)]

        # 碰撞检测 - 障碍物
        skier_rect = self.skier.get_rect()
        for obs in self.obstacles:
            if skier_rect.colliderect(obs.get_rect()):
                self.game_over = True
                if self.score > self.high_score:
                    self.high_score = self.score
                    self.save_high_score()
                return

        # 收集旗帜
        for flag in self.flags[:]:
            if not flag.collected and skier_rect.colliderect(flag.get_rect()):
                flag.collected = True
                self.flags.remove(flag)
                self.flags_collected += 1
                self.combo += 1
                if self.combo > self.max_combo:
                    self.max_combo = self.combo
                # 收集旗帜额外加分
                bonus = 50 * self.combo
                self.score += bonus
                self.collect_effect = {
                    'x': flag.x,
                    'y': flag.y,
                    'text': f"+{bonus}",
                    'timer': 40
                }

        # 重置连击（一段时间没收集到）
        if random.random() < 0.001:
            self.combo = 0

    def draw(self):
        # 绘制背景（渐变天空到雪地）
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(180 + ratio * 60)
            g = int(210 + ratio * 40)
            b = int(255 - ratio * 60)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

        # 绘制雪地纹理（远处山脉）
        for i in range(10):
            mx = (i * 70 + self.distance // 2) % (WIDTH + 100) - 50
            my = 500 + math.sin(i * 1.5 + self.distance * 0.001) * 30
            pygame.draw.polygon(screen, (200, 220, 240), [
                (mx, my),
                (mx - 40, my + 60),
                (mx + 40, my + 60),
            ])

        # 绘制车道线（虚线）
        for lane in range(1, LANE_COUNT):
            lx = lane * LANE_WIDTH
            for y in range(0, HEIGHT, 30):
                dy = (y + int(self.distance * 2)) % (HEIGHT + 40) - 20
                if 0 <= dy <= HEIGHT:
                    pygame.draw.line(screen, (200, 210, 230, 100),
                                     (lx, dy), (lx, dy + 15), 1)

        # 绘制雪花（在障碍物后面，营造景深感）
        for sf in self.snowflakes:
            sf.draw()

        # 绘制旗帜
        for flag in self.flags:
            flag.draw()

        # 绘制障碍物
        for obs in self.obstacles:
            obs.draw()

        # 绘制滑雪者
        if not self.game_over or self.start_delay > 0:
            self.skier.draw()

        # 绘制HUD
        self.draw_hud()

        # 游戏结束
        if self.game_over:
            self.draw_game_over()

        # 准备倒计时
        if self.start_delay > 0 and not self.game_over:
            self.draw_start_countdown()

    def draw_hud(self):
        """绘制信息面板"""
        # 半透明背景
        hud_surf = pygame.Surface((WIDTH, 50), pygame.SRCALPHA)
        hud_surf.fill((0, 0, 0, 120))
        screen.blit(hud_surf, (0, 0))

        draw_text(f"得分: {self.score}", font_small, WHITE, 80, 25)
        draw_text(f"距离: {self.distance}m", font_small, WHITE, 200, 25)
        draw_text(f"旗帜: {self.flags_collected}", font_small, GOLD, 320, 25)
        draw_text(f"速度: {self.speed:.1f}", font_small, WHITE, 440, 25)
        draw_text(f"最高: {self.high_score}", font_small, (200, 200, 200), 540, 25)

        if self.combo > 1:
            draw_text(f"连击 x{self.combo}!", font_small, GOLD, WIDTH // 2, 70)

    def draw_start_countdown(self):
        """绘制开始倒计时"""
        alpha = min(255, (60 - self.start_delay) * 8)
        if self.start_delay > 30:
            text = "准备!"
        else:
            text = "出发!"
        color = (255, 255, 255, alpha)
        s = font_large.render(text, True, WHITE)
        s.set_alpha(alpha)
        screen.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2 - 40))

    def draw_game_over(self):
        """绘制游戏结束界面"""
        # 半透明遮罩
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        draw_text("游戏结束", font_large, RED, WIDTH // 2, HEIGHT // 2 - 80)
        draw_text(f"最终得分: {self.score}", font_mid, WHITE, WIDTH // 2, HEIGHT // 2 - 20)
        draw_text(f"收集旗帜: {self.flags_collected} | 最高连击: {self.max_combo}",
                  font_small, GOLD, WIDTH // 2, HEIGHT // 2 + 20)

        if self.score >= self.high_score and self.score > 0:
            draw_text("🏆 新纪录!", font_mid, YELLOW, WIDTH // 2, HEIGHT // 2 + 60)

        draw_text("按 [空格键] 重新开始", font_mid, WHITE, WIDTH // 2, HEIGHT // 2 + 110)
        draw_text("按 [ESC] 退出", font_small, (200, 200, 200), WIDTH // 2, HEIGHT // 2 + 150)


def main():
    game = SkiGame()
    running = True

    while running:
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if game.game_over and event.key == pygame.K_SPACE:
                    game.reset()

        # 按键输入
        keys = pygame.key.get_pressed()
        game.handle_input(keys)

        # 更新
        game.update()

        # 绘制
        game.draw()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()