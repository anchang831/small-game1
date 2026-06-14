"""
Frogger（青蛙过河） —— 经典街机游戏
===================================
操作：方向键 ↑↓←→ 移动青蛙
目标：从底部起点穿越马路和河流，抵达顶部安全区
玩法：
  - 马路区域：躲避来往车辆
  - 河流区域：站在浮木上顺流漂移，落水则失败
  - 顶部 5 个安全窝，全部填满即通关
  - 每成功到达一次 +100 分，奖励时间分
  - 初始 3 条命，超时或被撞/落水扣命

依赖：pygame
运行：python frogger.py
"""

import pygame
import random
import sys

# ==================== 常量 ====================
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 780
CELL_SIZE = 60          # 每格大小
COLS = SCREEN_WIDTH // CELL_SIZE  # 10 列
ROWS = SCREEN_HEIGHT // CELL_SIZE  # 13 行

# 颜色 (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 120, 0)
YELLOW = (255, 255, 0)
RED = (255, 50, 50)
BLUE = (50, 100, 255)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
ORANGE = (255, 165, 0)
PURPLE = (180, 0, 255)
CYAN = (0, 255, 255)
HOME_COLORS = [(255, 50, 50), (255, 150, 50), (255, 255, 50),
               (50, 255, 50), (50, 150, 255)]

# 方向
UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3

# 游戏状态
STATE_PLAYING = 0
STATE_WIN = 1
STATE_GAME_OVER = 2

# 时间限制（秒）
TIME_LIMIT = 30

FPS = 60


class Frog:
    """玩家控制的青蛙"""

    def __init__(self, x, y):
        self.start_x = x
        self.start_y = y
        self.reset()
        self.lives = 3
        self.score = 0

    def reset(self):
        """重置到起点"""
        self.x = self.start_x
        self.y = self.start_y
        self.target_x = self.x
        self.target_y = self.y
        self.moving = False
        self.on_log = None  # 当前所在的浮木
        self.alive = True

    def move(self, direction, obstacles):
        """尝试向指定方向移动，返回是否成功"""
        if self.moving or not self.alive:
            return False

        dx, dy = 0, 0
        if direction == UP:
            dy = -1
        elif direction == DOWN:
            dy = 1
        elif direction == LEFT:
            dx = -1
        elif direction == RIGHT:
            dx = 1

        new_x = self.x + dx
        new_y = self.y + dy

        # 边界检查
        if new_x < 0 or new_x >= COLS:
            return False
        if new_y < 0 or new_y >= ROWS:
            return False

        self.target_x = new_x
        self.target_y = new_y
        self.moving = True
        return True

    def update(self, logs, cars):
        """更新青蛙状态"""
        # 平滑移动动画
        if self.moving:
            diff_x = (self.target_x - self.x) * CELL_SIZE
            diff_y = (self.target_y - self.y) * CELL_SIZE
            # 直接完成移动（基于网格的简单实现）
            self.x = self.target_x
            self.y = self.target_y
            self.moving = False

        # 如果在河流区域，跟随浮木
        row = int(self.y)
        if 1 <= row <= 5:  # 河流区域
            self.on_log = None
            for log in logs:
                # 检查青蛙是否在浮木上
                if log.row == row and log.col <= self.x < log.col + log.length:
                    self.on_log = log
                    break
            if self.on_log is None:
                # 不在浮木上 → 落水
                self.alive = False
        else:
            self.on_log = None

        # 碰撞检测（马路区域车辆）
        if 7 <= row <= 11:
            for car in cars:
                if car.row == row:
                    # 检查是否与车辆重叠（简化：按格子碰撞）
                    if abs(self.x - car.col) < 1.0:
                        self.alive = False
                        break

    def check_reach_goal(self, goals):
        """检查是否到达安全窝"""
        for i, (gx, gy, occupied) in enumerate(goals):
            if not occupied and int(self.x) == gx and int(self.y) == gy:
                return i
        return -1

    def draw(self, screen):
        """绘制青蛙"""
        if not self.alive:
            return
        cx = int(self.x * CELL_SIZE + CELL_SIZE // 2)
        cy = int(self.y * CELL_SIZE + CELL_SIZE // 2)
        r = CELL_SIZE // 2 - 4

        # 身体（绿色圆形）
        pygame.draw.circle(screen, GREEN, (cx, cy), r)
        pygame.draw.circle(screen, DARK_GREEN, (cx, cy), r, 2)

        # 眼睛
        eye_offset = 8
        eye_r = 6
        pygame.draw.circle(screen, WHITE, (cx - eye_offset, cy - eye_offset - 2), eye_r)
        pygame.draw.circle(screen, WHITE, (cx + eye_offset, cy - eye_offset - 2), eye_r)
        pygame.draw.circle(screen, BLACK, (cx - eye_offset, cy - eye_offset - 2), 3)
        pygame.draw.circle(screen, BLACK, (cx + eye_offset, cy - eye_offset - 2), 3)

        # 嘴巴
        pygame.draw.arc(screen, BLACK, (cx - 10, cy - 2, 20, 10), 0, 3.14, 2)


class Car:
    """马路上的车辆"""

    def __init__(self, row, col, direction, speed, color, width):
        self.row = row          # 所在行
        self.col = col          # 当前列（浮点数）
        self.direction = direction  # 1=右, -1=左
        self.speed = speed
        self.color = color
        self.width = width      # 占几格

    def update(self):
        self.col += self.speed * self.direction
        # 循环：超出边界从另一侧出现
        if self.direction > 0 and self.col > COLS + 1:
            self.col = -self.width
        elif self.direction < 0 and self.col < -self.width:
            self.col = COLS + 1

    def draw(self, screen):
        x = int(self.col * CELL_SIZE)
        y = int(self.row * CELL_SIZE + 4)
        w = int(self.width * CELL_SIZE - 2)
        h = CELL_SIZE - 8
        pygame.draw.rect(screen, self.color, (x, y, w, h))
        pygame.draw.rect(screen, BLACK, (x, y, w, h), 2)
        # 车窗
        if self.width >= 2:
            win_w = 12
            win_h = h - 10
            win_y = y + 5
            for i in range(self.width - 1):
                wx = x + 10 + i * (CELL_SIZE + 6)
                pygame.draw.rect(screen, LIGHT_GRAY, (wx, win_y, win_w, win_h))
                pygame.draw.rect(screen, BLACK, (wx, win_y, win_w, win_h), 1)


class Log:
    """河流中的浮木"""

    def __init__(self, row, col, direction, speed, length, color):
        self.row = row
        self.col = col
        self.direction = direction
        self.speed = speed
        self.length = length    # 占几格
        self.color = color

    def update(self):
        self.col += self.speed * self.direction
        if self.direction > 0 and self.col > COLS + 2:
            self.col = -self.length
        elif self.direction < 0 and self.col < -self.length:
            self.col = COLS + 2

    def draw(self, screen):
        x = int(self.col * CELL_SIZE)
        y = int(self.row * CELL_SIZE + 6)
        w = int(self.length * CELL_SIZE - 2)
        h = CELL_SIZE - 12
        pygame.draw.rect(screen, self.color, (x, y, w, h))
        pygame.draw.rect(screen, BROWN, (x, y, w, h), 2)
        # 木纹线
        for i in range(self.length):
            lx = int((self.col + i) * CELL_SIZE + 10)
            pygame.draw.line(screen, BROWN, (lx, y + 4), (lx, y + h - 4), 1)


class Game:
    """游戏主控类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("青蛙过河 Frogger")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("simhei", 48)
        self.font_small = pygame.font.SysFont("simhei", 22)
        self.font_info = pygame.font.SysFont("simhei", 26)

        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        # 青蛙起点：底部中间
        start_x = COLS // 2
        start_y = ROWS - 1
        self.frog = Frog(start_x, start_y)

        self.goals = []
        for i in range(5):
            self.goals.append([2 * i + 1, 0, False])  # x, y, occupied

        self.state = STATE_PLAYING
        self.time_left = TIME_LIMIT
        self.timer_event = pygame.USEREVENT + 1
        pygame.time.set_timer(self.timer_event, 1000)

        self._init_cars()
        self._init_logs()

    def _init_cars(self):
        """初始化所有车辆"""
        self.cars = []
        # (row, start_col, direction, speed, color, width)
        car_configs = [
            (7, 0, 1, 0.08, RED, 2),
            (7, 5, 1, 0.08, RED, 2),
            (8, 8, -1, 0.12, BLUE, 2),
            (8, 3, -1, 0.12, BLUE, 2),
            (9, 1, 1, 0.06, ORANGE, 3),
            (9, 7, 1, 0.06, ORANGE, 3),
            (10, 9, -1, 0.10, PURPLE, 2),
            (10, 4, -1, 0.10, PURPLE, 2),
            (11, 0, 1, 0.15, GRAY, 2),
            (11, 6, 1, 0.15, GRAY, 2),
        ]
        for row, col, direction, speed, color, width in car_configs:
            self.cars.append(Car(row, col, direction, speed, color, width))

    def _init_logs(self):
        """初始化所有浮木"""
        self.logs = []
        log_configs = [
            (1, 0, 1, 0.04, 3, BROWN),
            (1, 6, 1, 0.04, 2, BROWN),
            (2, 8, -1, 0.05, 2, (160, 82, 45)),
            (2, 3, -1, 0.05, 3, (160, 82, 45)),
            (3, 1, 1, 0.06, 2, BROWN),
            (3, 7, 1, 0.06, 3, BROWN),
            (4, 9, -1, 0.04, 2, (160, 82, 45)),
            (4, 4, -1, 0.04, 2, (160, 82, 45)),
            (5, 0, 1, 0.07, 3, BROWN),
            (5, 5, 1, 0.07, 2, BROWN),
        ]
        for row, col, direction, speed, length, color in log_configs:
            self.logs.append(Log(row, col, direction, speed, length, color))

    def handle_events(self):
        """处理用户输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == self.timer_event and self.state == STATE_PLAYING:
                self.time_left -= 1
                if self.time_left <= 0:
                    self.frog_die()

            if event.type == pygame.KEYDOWN:
                if self.state == STATE_PLAYING:
                    if event.key == pygame.K_UP:
                        self.frog.move(UP, self.cars)
                    elif event.key == pygame.K_DOWN:
                        self.frog.move(DOWN, self.cars)
                    elif event.key == pygame.K_LEFT:
                        self.frog.move(LEFT, self.cars)
                    elif event.key == pygame.K_RIGHT:
                        self.frog.move(RIGHT, self.cars)
                elif event.key == pygame.K_r:
                    self.reset_game()
                elif event.key == pygame.K_q:
                    return False

        return True

    def frog_die(self):
        """青蛙死亡处理"""
        self.frog.alive = False
        self.frog.lives -= 1
        self.time_left = TIME_LIMIT
        if self.frog.lives <= 0:
            self.state = STATE_GAME_OVER
        else:
            # 重置青蛙位置
            self.frog.reset()

    def update(self):
        """更新所有游戏对象"""
        if self.state != STATE_PLAYING:
            return

        # 先保存青蛙当前位置信息再更新车和木头
        frog_row = int(self.frog.y)

        # 更新车辆
        for car in self.cars:
            car.update()

        # 更新浮木
        for log in self.logs:
            log.update()

        # 如果青蛙在浮木上，随着浮木移动
        if self.frog.on_log is not None:
            log = self.frog.on_log
            self.frog.x += log.speed * log.direction

            # 边界检查：漂出屏幕则死亡
            if self.frog.x < -0.5 or self.frog.x > COLS - 0.5:
                self.frog_die()
                return

        # 更新青蛙碰撞等状态
        self.frog.update(self.logs, self.cars)

        # 检查是否死亡
        if not self.frog.alive:
            self.frog_die()
            return

        # 检查是否到达安全窝
        goal_idx = self.frog.check_reach_goal(self.goals)
        if goal_idx >= 0:
            self.goals[goal_idx][2] = True  # 标记已占用
            # 加分数（时间奖励）
            self.frog.score += 100 + int(self.time_left)
            self.time_left = TIME_LIMIT
            # 检查是否全部填满
            if all(g[2] for g in self.goals):
                self.state = STATE_WIN
            else:
                self.frog.reset()

    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(BLACK)

        # 绘制背景区域
        self._draw_background()

        # 绘制浮木
        for log in self.logs:
            log.draw(self.screen)

        # 绘制车辆
        for car in self.cars:
            car.draw(self.screen)

        # 绘制安全窝
        self._draw_goals()

        # 绘制青蛙
        self.frog.draw(self.screen)

        # 绘制信息栏
        self._draw_info()

        # 绘制状态画面
        if self.state == STATE_GAME_OVER:
            self._draw_overlay("游戏结束 Game Over", RED)
        elif self.state == STATE_WIN:
            self._draw_overlay("恭喜通关 You Win!", YELLOW)

        pygame.display.flip()

    def _draw_background(self):
        """绘制背景区域"""
        for row in range(ROWS):
            y = row * CELL_SIZE
            if row == 0:  # 安全区
                color = DARK_GREEN
            elif 1 <= row <= 5:  # 河流
                color = (0, 100, 180)  # 深蓝
                # 水波纹
                for c in range(COLS):
                    wave_offset = int(8 * (row + c) + pygame.time.get_ticks() * 0.002)
                    wave_offset = (wave_offset % 16) - 8
                    wx = c * CELL_SIZE
                    wy = y + CELL_SIZE // 2
                    pygame.draw.arc(self.screen, (100, 180, 255),
                                    (wx, wy - 4 + wave_offset, CELL_SIZE, 8),
                                    0, 3.14, 2)
            elif row == 6:  # 中间安全岛
                color = (50, 50, 50)
            elif 7 <= row <= 11:  # 马路
                color = (60, 60, 60) if row % 2 == 0 else (70, 70, 70)
                # 车道线
                for c in range(COLS):
                    if (c + row) % 2 == 0:
                        lx = c * CELL_SIZE
                        pygame.draw.rect(self.screen, (80, 80, 80),
                                         (lx, y + CELL_SIZE - 4, CELL_SIZE, 4))
            else:  # 起点区
                color = (30, 80, 30)

            if row != 0 and not (1 <= row <= 5):
                pygame.draw.rect(self.screen, color, (0, y, SCREEN_WIDTH, CELL_SIZE))

        # 河流水波背景
        for row in range(1, 6):
            y = row * CELL_SIZE
            pygame.draw.rect(self.screen, (0, 80, 160), (0, y, SCREEN_WIDTH, CELL_SIZE))

    def _draw_goals(self):
        """绘制顶部安全窝"""
        for i, (gx, gy, occupied) in enumerate(self.goals):
            x = gx * CELL_SIZE
            y = gy * CELL_SIZE
            if occupied:
                pygame.draw.rect(self.screen, HOME_COLORS[i], (x + 4, y + 4,
                                                               CELL_SIZE - 8, CELL_SIZE - 8))
                # 画一个旗子标记
                fx = x + CELL_SIZE // 2
                fy = y + 8
                pygame.draw.line(self.screen, WHITE, (fx, fy), (fx, fy + 40), 3)
                pygame.draw.polygon(self.screen, YELLOW,
                                    [(fx, fy), (fx + 18, fy + 10), (fx, fy + 20)])
            else:
                pygame.draw.rect(self.screen, (0, 150, 0), (x + 4, y + 4,
                                                            CELL_SIZE - 8, CELL_SIZE - 8), 3)
                # 画一个空心窝标记
                pygame.draw.circle(self.screen, (0, 180, 0),
                                   (x + CELL_SIZE // 2, y + CELL_SIZE // 2), 15, 3)

    def _draw_info(self):
        """绘制顶部/底部信息栏"""
        # 顶部：分数、时间、生命
        score_text = self.font_info.render(f"得分: {self.frog.score}", True, WHITE)
        self.screen.blit(score_text, (10, SCREEN_HEIGHT - 35))

        time_color = RED if self.time_left <= 10 else WHITE
        time_text = self.font_info.render(f"时间: {self.time_left}s", True, time_color)
        self.screen.blit(time_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 35))

        lives_text = self.font_info.render(f"生命: {'❤️' * self.frog.lives}", True, WHITE)
        self.screen.blit(lives_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 35))

        # 操作提示（底部）
        hint = self.font_small.render("↑↓←→ 移动 | R 重开 | Q 退出", True, GRAY)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT - 8))

    def _draw_overlay(self, message, color):
        """绘制结束覆盖层"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        text = self.font_large.render(message, True, color)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(text, text_rect)

        score_msg = f"最终得分: {self.frog.score}"
        score_surf = self.font_small.render(score_msg, True, WHITE)
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(score_surf, score_rect)

        restart_msg = "按 R 重新开始 | Q 退出"
        restart_surf = self.font_small.render(restart_msg, True, GRAY)
        restart_rect = restart_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(restart_surf, restart_rect)

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
    game = Game()
    game.run()