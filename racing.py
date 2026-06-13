"""
赛车竞速 - Racing Game
俯视角赛车游戏，控制车辆躲避迎面而来的车流，坚持越久得分越高。
使用 Pygame 实现，单文件运行，无外部资源依赖。

操作说明:
  ← →  : 左右变道
  ↑    : 加速前进
  ↓    : 减速后退
  R    : 重新开始
  ESC  : 退出游戏
"""

import pygame
import random
import sys

# ========== 常量定义 ==========
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 700
FPS = 60

# 道路参数
ROAD_LEFT = 90
ROAD_RIGHT = 390
ROAD_WIDTH = ROAD_RIGHT - ROAD_LEFT
LANE_COUNT = 3
LANE_WIDTH = ROAD_WIDTH // LANE_COUNT

# 车道中心线 X 坐标 (3车道)
LANE_CENTERS = [
    ROAD_LEFT + LANE_WIDTH // 2,
    ROAD_LEFT + LANE_WIDTH + LANE_WIDTH // 2,
    ROAD_LEFT + 2 * LANE_WIDTH + LANE_WIDTH // 2,
]

# 颜色 (RGB)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREEN = (34, 139, 34)       # 草地
COLOR_GRAY = (80, 80, 80)         # 路面
COLOR_DARK_GRAY = (50, 50, 50)    # 路肩
COLOR_YELLOW = (255, 255, 0)      # 车道线
COLOR_RED = (220, 40, 40)
COLOR_BLUE = (40, 100, 220)
COLOR_ORANGE = (255, 165, 0)
COLOR_CYAN = (0, 200, 200)
COLOR_PURPLE = (180, 40, 180)
COLOR_LIME = (50, 205, 50)
COLOR_GOLD = (255, 215, 0)

# 玩家颜色
PLAYER_COLORS = [COLOR_BLUE, COLOR_CYAN, COLOR_LIME]

# 敌方车辆颜色列表
ENEMY_COLORS = [COLOR_RED, COLOR_ORANGE, COLOR_PURPLE, COLOR_GOLD,
                (255, 100, 100), (200, 100, 0), (255, 20, 147)]


class Car:
    """车辆类 - 表示游戏中的任何车辆（玩家或敌方）"""

    def __init__(self, x, y, color, width=45, height=80):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.speed = 0

    @property
    def rect(self):
        return pygame.Rect(self.x - self.width // 2,
                           self.y - self.height // 2,
                           self.width, self.height)

    def draw(self, surface):
        """绘制车辆（带车灯、车窗等细节）"""
        rect = self.rect

        # 车身主体 (圆角矩形效果)
        pygame.draw.rect(surface, self.color, rect, border_radius=8)

        # 前挡风玻璃
        windshield = pygame.Rect(rect.x + 8, rect.y + 8,
                                 rect.width - 16, rect.height // 3)
        pygame.draw.rect(surface, (180, 220, 255), windshield, border_radius=4)

        # 后挡风玻璃
        rear_window = pygame.Rect(rect.x + 8, rect.y + rect.height - rect.height // 3 - 8,
                                  rect.width - 16, rect.height // 3)
        pygame.draw.rect(surface, (180, 220, 255), rear_window, border_radius=4)

        # 车灯 (前)
        light_size = 6
        for offset in [12, rect.width - 12 - light_size]:
            pygame.draw.circle(surface, (255, 255, 200),
                               (rect.x + offset, rect.y + 3), light_size // 2)

        # 车灯 (后 - 红色)
        for offset in [12, rect.width - 12 - light_size]:
            pygame.draw.circle(surface, (255, 50, 50),
                               (rect.x + offset, rect.y + rect.height - 3), light_size // 2)

    def collides_with(self, other):
        """碰撞检测"""
        return self.rect.colliderect(other.rect)


class RoadMarking:
    """道路标线 - 模拟车辆前进的动态效果"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 4
        self.height = 30
        self.speed = 0

    def update(self):
        self.y += self.speed
        # 超出底部后回到顶部
        if self.y > SCREEN_HEIGHT:
            self.y = -self.height

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_YELLOW,
                         (self.x, self.y, self.width, self.height))


class Particle:
    """碰撞粒子特效"""

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-5, 5)
        self.color = color
        self.size = random.randint(3, 8)
        self.lifetime = 30  # 帧数
        self.age = 0

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  # 重力
        self.age += 1
        return self.age < self.lifetime

    def draw(self, surface):
        alpha = max(0, 255 * (1 - self.age / self.lifetime))
        color = tuple(max(0, min(255, c * (1 - self.age / self.lifetime)))
                      for c in self.color)
        pygame.draw.circle(surface, color,
                           (int(self.x), int(self.y)), self.size)


class RacingGame:
    """赛车游戏主类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("赛车竞速 - Racing Game")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("simhei", 48, bold=True)
        self.font_medium = pygame.font.SysFont("simhei", 32, bold=True)
        self.font_small = pygame.font.SysFont("simhei", 22, bold=True)

        # 尝试加载字体（如果没有中文字体则回退）
        if not any(self.font_large.render("测试", True, COLOR_WHITE)):
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 22)

        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        # 玩家
        player_x = LANE_CENTERS[1]
        player_y = SCREEN_HEIGHT - 120
        player_color = random.choice(PLAYER_COLORS)
        self.player = Car(player_x, player_y, player_color)
        self.player.speed = 0
        self.target_lane = 1
        self.current_lane = 1

        # 敌方车辆
        self.enemies = []

        # 道路标线
        self.markings = []
        for lane in range(LANE_COUNT):
            cx = LANE_CENTERS[lane]
            for i in range(0, SCREEN_HEIGHT, 50):
                self.markings.append(RoadMarking(cx - 2, i))

        # 粒子特效
        self.particles = []

        # 游戏状态
        self.score = 0
        self.high_score = self.load_high_score()
        self.game_over = False
        self.started = False
        self.base_speed = 5
        self.spawn_timer = 0
        self.spawn_interval = 60  # 帧
        self.frame_count = 0

        # 道路偏移（用于标线动画）
        self.road_offset = 0

        # 难度
        self.difficulty = 1

    def load_high_score(self):
        """加载最高分"""
        try:
            with open("racing_highscore.txt", "r") as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return 0

    def save_high_score(self):
        """保存最高分"""
        try:
            with open("racing_highscore.txt", "w") as f:
                f.write(str(self.high_score))
        except IOError:
            pass

    def spawn_enemy(self):
        """生成敌方车辆"""
        lane = random.randint(0, LANE_COUNT - 1)
        x = LANE_CENTERS[lane]
        y = -100  # 从顶部外开始

        # 避免在三连中在同一车道生成
        for e in self.enemies:
            if abs(e.x - x) < LANE_WIDTH * 0.5 and e.y < 150:
                lane = (lane + 1) % LANE_COUNT
                x = LANE_CENTERS[lane]
                break

        color = random.choice(ENEMY_COLORS)
        # 随机车辆大小
        width = random.randint(38, 50)
        height = random.randint(70, 90)
        car = Car(x, y, color, width, height)
        car.speed = self.base_speed + random.uniform(-0.5, 1.5)
        self.enemies.append(car)

    def handle_input(self):
        """处理用户输入"""
        keys = pygame.key.get_pressed()

        if not self.game_over and self.started:
            # 左右变道
            if keys[pygame.K_LEFT] and self.current_lane > 0:
                self.current_lane -= 1
                self.target_lane = self.current_lane
            if keys[pygame.K_RIGHT] and self.current_lane < LANE_COUNT - 1:
                self.current_lane += 1
                self.target_lane = self.current_lane

            # 加速 / 减速
            if keys[pygame.K_UP]:
                self.base_speed = min(12, self.base_speed + 0.1)
            if keys[pygame.K_DOWN]:
                self.base_speed = max(3, self.base_speed - 0.1)

    def update(self):
        """更新游戏逻辑"""
        self.frame_count += 1

        if self.game_over:
            # 更新粒子特效
            self.particles = [p for p in self.particles if p.update()]
            return

        if not self.started:
            return

        # 平滑移动到目标车道
        target_x = LANE_CENTERS[self.target_lane]
        dx = target_x - self.player.x
        self.player.x += dx * 0.15

        # 速度随时间和分数逐渐增加
        self.difficulty = 1 + self.frame_count / 3600  # 每60秒增加1
        current_speed = self.base_speed + self.difficulty - 1

        # 更新道路标线速度
        for m in self.markings:
            m.speed = current_speed
            m.update()

        # 生成敌方车辆
        self.spawn_interval = max(20, int(60 / self.difficulty))
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            self.spawn_enemy()
            # 高难度时偶尔一次生成两辆
            if self.difficulty > 3 and random.random() < 0.3:
                self.spawn_enemy()

        # 更新敌方车辆
        for car in self.enemies[:]:
            car.y += car.speed
            # 超出屏幕移除
            if car.y > SCREEN_HEIGHT + 100:
                self.enemies.remove(car)
                self.score += 10

        # 碰撞检测
        for car in self.enemies:
            if self.player.collides_with(car):
                self.on_collision(car)
                break

        # 更新分数（随时间增长）
        self.score += 0.1 * self.difficulty

        # 更新粒子特效
        self.particles = [p for p in self.particles if p.update()]

    def on_collision(self, enemy):
        """碰撞发生时的处理"""
        self.game_over = True

        # 生成碰撞粒子
        cx = (self.player.x + enemy.x) / 2
        cy = (self.player.y + enemy.y) / 2
        for _ in range(40):
            color = random.choice([self.player.color, enemy.color, COLOR_RED, COLOR_ORANGE])
            self.particles.append(Particle(cx, cy, color))

        # 更新最高分
        final_score = int(self.score)
        if final_score > self.high_score:
            self.high_score = final_score
            self.save_high_score()

    def draw_road(self):
        """绘制道路和背景"""
        # 草地背景
        self.screen.fill(COLOR_GREEN)

        # 路肩 (左右两侧)
        pygame.draw.rect(self.screen, COLOR_DARK_GRAY,
                         (ROAD_LEFT - 10, 0, 10, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, COLOR_DARK_GRAY,
                         (ROAD_RIGHT, 0, 10, SCREEN_HEIGHT))

        # 路面
        pygame.draw.rect(self.screen, COLOR_GRAY,
                         (ROAD_LEFT, 0, ROAD_WIDTH, SCREEN_HEIGHT))

        # 车道分隔线（白色虚线）- 独立于标线对象绘制
        dash_height = 30
        dash_gap = 20
        speed = self.base_speed + max(0, self.difficulty - 1)
        self.road_offset = (self.road_offset + speed) % (dash_height + dash_gap)

        for lane in range(1, LANE_COUNT):
            lx = ROAD_LEFT + lane * LANE_WIDTH
            for i in range(-dash_height, SCREEN_HEIGHT + dash_height,
                           dash_height + dash_gap):
                y = (i + self.road_offset) % (SCREEN_HEIGHT + dash_height + dash_gap) - dash_height
                pygame.draw.rect(self.screen, COLOR_WHITE,
                                 (lx - 2, y, 4, dash_height))

    def draw_ui(self):
        """绘制用户界面"""
        # 分数
        score_text = self.font_medium.render(f"得分: {int(self.score)}", True, COLOR_WHITE)
        self.screen.blit(score_text, (15, 15))

        # 最高分
        high_text = self.font_small.render(f"最高: {self.high_score}", True, COLOR_YELLOW)
        self.screen.blit(high_text, (15, 55))

        # 速度指示
        speed_val = int(self.base_speed + max(0, self.difficulty - 1))
        speed_text = self.font_small.render(f"速度: {speed_val}", True, COLOR_CYAN)
        self.screen.blit(speed_text, (15, 80))

        # 游戏结束界面
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(120)
            overlay.fill(COLOR_BLACK)
            self.screen.blit(overlay, (0, 0))

            # Game Over 标题
            go_text = self.font_large.render("游戏结束", True, COLOR_RED)
            go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
            self.screen.blit(go_text, go_rect)

            # 最终得分
            score_str = f"最终得分: {int(self.score)}"
            fs_text = self.font_medium.render(score_str, True, COLOR_WHITE)
            fs_rect = fs_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(fs_text, fs_rect)

            # 最高分
            hs_text = self.font_small.render(f"最高纪录: {self.high_score}", True, COLOR_YELLOW)
            hs_rect = hs_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 45))
            self.screen.blit(hs_text, hs_rect)

            # 重新开始提示
            restart_text = self.font_small.render("按 [R] 重新开始  |  按 [ESC] 退出", True, COLOR_WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
            self.screen.blit(restart_text, restart_rect)

        # 开始提示
        elif not self.started:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(100)
            overlay.fill(COLOR_BLACK)
            self.screen.blit(overlay, (0, 0))

            title = self.font_large.render("赛车竞速", True, COLOR_GOLD)
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
            self.screen.blit(title, title_rect)

            start_text = self.font_medium.render("按 [空格] 开始游戏", True, COLOR_WHITE)
            start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(start_text, start_rect)

            controls = [
                "← → 左右变道",
                "↑ 加速 / ↓ 减速",
                "躲避来往车辆!",
            ]
            for i, line in enumerate(controls):
                ctrl = self.font_small.render(line, True, COLOR_CYAN)
                ctrl_rect = ctrl.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 55 + i * 30))
                self.screen.blit(ctrl, ctrl_rect)

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

                if event.key == pygame.K_r and self.game_over:
                    self.reset_game()
                    self.started = True

                if event.key == pygame.K_SPACE and not self.started:
                    self.started = True

        return True

    def run(self):
        """游戏主循环"""
        running = True
        while running:
            running = self.handle_events()
            self.handle_input()
            self.update()

            # 绘制
            self.draw_road()

            # 绘制敌方车辆
            for car in self.enemies:
                car.draw(self.screen)

            # 绘制玩家
            if not self.game_over:
                self.player.draw(self.screen)

            # 绘制粒子特效
            for p in self.particles:
                p.draw(self.screen)

            # 绘制UI
            self.draw_ui()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ========== 程序入口 ==========
if __name__ == "__main__":
    game = RacingGame()
    game.run()