"""
光轮摩托 (Tron Light Cycle) - 经典双人光轮对战游戏
===================================================
控制方式:
  - 玩家1 (蓝色): W/A/S/D
  - 玩家2 (红色): 方向键 ↑/←/↓/→
  - 游戏结束后按 R 重新开始, Q 退出

规则:
  - 每位玩家驾驶光轮摩托, 身后留下光墙
  - 撞到光墙或边界则输
  - 随着时间推移, 速度逐渐加快
"""

import pygame
import sys
import random

# ==================== 常量配置 ====================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 10                     # 网格大小(像素)
COLS = SCREEN_WIDTH // GRID_SIZE   # 列数
ROWS = SCREEN_HEIGHT // GRID_SIZE  # 行数

# 颜色 (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)
RED = (255, 50, 50)
GREEN = (0, 255, 100)
GRAY = (40, 40, 40)
LIGHT_GRAY = (100, 100, 100)

# 方向
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# 初始速度(帧间隔)
INITIAL_SPEED = 8
MIN_SPEED = 3  # 最快速度


class Player:
    """玩家光轮摩托"""

    def __init__(self, start_col, start_row, start_dir, color, trail_color):
        self.col = start_col          # 当前列
        self.row = start_row          # 当前行
        self.dir = start_dir          # 移动方向
        self.color = color            # 光轮颜色
        self.trail_color = trail_color  # 光墙颜色
        self.alive = True
        self.score = 0

    def set_direction(self, new_dir):
        """改变方向 (不能直接掉头)"""
        if new_dir != self.dir and (new_dir[0] != -self.dir[0] or new_dir[1] != -self.dir[1]):
            self.dir = new_dir

    def move(self):
        """向前移动一步"""
        self.col += self.dir[0]
        self.row += self.dir[1]

    def get_pos(self):
        return self.col, self.row


class TronGame:
    """游戏主逻辑"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("光轮摩托 Tron - 玩家1:WASD  玩家2:方向键")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("simhei", 48)
        self.font_mid = pygame.font.SysFont("simhei", 28)
        self.font_small = pygame.font.SysFont("simhei", 18)
        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        # 网格记录每个格子被谁占据 (None=空, 1=玩家1光墙, 2=玩家2光墙)
        self.grid = [[0] * COLS for _ in range(ROWS)]

        # 创建两个玩家
        mid_col = COLS // 2
        mid_row = ROWS // 2
        self.player1 = Player(10, mid_row, RIGHT, BLUE, (50, 100, 200))
        self.player2 = Player(COLS - 11, mid_row, LEFT, RED, (200, 50, 50))

        # 记录初始位置
        self.grid[mid_row][10] = 1
        self.grid[mid_row][COLS - 11] = 2

        self.speed = INITIAL_SPEED
        self.frame_count = 0
        self.game_over = False
        self.winner = None  # None=未结束, 1=玩家1赢, 2=玩家2赢, 0=平局
        self.move_counter = 0

    def handle_input(self):
        """处理键盘输入"""
        keys = pygame.key.get_pressed()

        # 玩家1: WASD
        if keys[pygame.K_w]:
            self.player1.set_direction(UP)
        elif keys[pygame.K_s]:
            self.player1.set_direction(DOWN)
        elif keys[pygame.K_a]:
            self.player1.set_direction(LEFT)
        elif keys[pygame.K_d]:
            self.player1.set_direction(RIGHT)

        # 玩家2: 方向键
        if keys[pygame.K_UP]:
            self.player2.set_direction(UP)
        elif keys[pygame.K_DOWN]:
            self.player2.set_direction(DOWN)
        elif keys[pygame.K_LEFT]:
            self.player2.set_direction(LEFT)
        elif keys[pygame.K_RIGHT]:
            self.player2.set_direction(RIGHT)

    def update(self):
        """更新游戏状态"""
        if self.game_over:
            return

        self.frame_count += 1
        # 根据速度控制移动频率
        if self.frame_count % self.speed != 0:
            return

        self.move_counter += 1
        # 每50步加速一次
        if self.move_counter % 50 == 0 and self.speed > MIN_SPEED:
            self.speed -= 1

        # 移动两个玩家
        p1_pos = self._move_player(self.player1, 1)
        p2_pos = self._move_player(self.player2, 2)

        # 检查碰撞 (移动后已标记, 这里只需检查双方是否同时死亡)
        if not self.player1.alive and not self.player2.alive:
            self.game_over = True
            self.winner = 0  # 平局
        elif not self.player1.alive:
            self.game_over = True
            self.winner = 2
        elif not self.player2.alive:
            self.game_over = True
            self.winner = 1

    def _move_player(self, player, player_id):
        """移动单个玩家, 返回新位置, 处理碰撞"""
        player.move()
        col, row = player.get_pos()

        # 检查边界碰撞
        if col < 0 or col >= COLS or row < 0 or row >= ROWS:
            player.alive = False
            return (col, row)

        # 检查光墙碰撞
        if self.grid[row][col] != 0:
            player.alive = False
            return (col, row)

        # 标记光墙
        self.grid[row][col] = player_id
        return (col, row)

    def draw(self):
        """绘制画面"""
        self.screen.fill(BLACK)

        # 绘制网格线 (淡灰色)
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, GRAY, (0, y), (SCREEN_WIDTH, y))

        # 绘制光墙
        for row in range(ROWS):
            for col in range(COLS):
                if self.grid[row][col] == 1:
                    color = self.player1.trail_color
                elif self.grid[row][col] == 2:
                    color = self.player2.trail_color
                else:
                    continue
                rect = (col * GRID_SIZE, row * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(self.screen, color, rect)
                # 给光墙加一点发光效果
                inner = (col * GRID_SIZE + 2, row * GRID_SIZE + 2, GRID_SIZE - 4, GRID_SIZE - 4)
                pygame.draw.rect(self.screen, self.grid[row][col] == 1 and BLUE or RED, inner)

        # 绘制玩家光轮 (当前位置)
        if self.player1.alive:
            self._draw_cycle(self.player1)
        if self.player2.alive:
            self._draw_cycle(self.player2)

        # 绘制UI信息
        self._draw_ui()

        # 绘制游戏结束画面
        if self.game_over:
            self._draw_game_over()

        pygame.display.flip()

    def _draw_cycle(self, player):
        """绘制光轮摩托"""
        col, row = player.get_pos()
        x = col * GRID_SIZE
        y = row * GRID_SIZE
        # 外圈发光
        pygame.draw.circle(self.screen, WHITE, (x + GRID_SIZE // 2, y + GRID_SIZE // 2), GRID_SIZE // 2)
        # 内圈颜色
        pygame.draw.circle(self.screen, player.color, (x + GRID_SIZE // 2, y + GRID_SIZE // 2), GRID_SIZE // 2 - 2)

    def _draw_ui(self):
        """绘制顶部UI (分数、速度)"""
        # 玩家1分数
        p1_text = self.font_small.render(f"玩家1: {self.player1.score}", True, BLUE)
        self.screen.blit(p1_text, (20, 10))

        # 玩家2分数
        p2_text = self.font_small.render(f"玩家2: {self.player2.score}", True, RED)
        self.screen.blit(p2_text, (SCREEN_WIDTH - 120, 10))

        # 速度显示
        speed_text = self.font_small.render(f"速度: {self.speed}", True, LIGHT_GRAY)
        self.screen.blit(speed_text, (SCREEN_WIDTH // 2 - 30, 10))

    def _draw_game_over(self):
        """绘制游戏结束画面"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # 胜负文字
        if self.winner == 0:
            title = "平局! 双方同归于尽!"
            color = WHITE
        elif self.winner == 1:
            title = "玩家1 (蓝色) 获胜!"
            color = BLUE
        else:
            title = "玩家2 (红色) 获胜!"
            color = RED

        title_surf = self.font_large.render(title, True, color)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
        self.screen.blit(title_surf, title_rect)

        # 操作提示
        hint1 = self.font_mid.render("按 R 重新开始", True, GREEN)
        hint1_rect = hint1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(hint1, hint1_rect)

        hint2 = self.font_mid.render("按 Q 退出游戏", True, LIGHT_GRAY)
        hint2_rect = hint2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(hint2, hint2_rect)

    def run(self):
        """主循环"""
        running = True
        while running:
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    if event.key == pygame.K_r and self.game_over:
                        # 给赢家加分
                        if self.winner == 1:
                            self.player1.score += 1
                        elif self.winner == 2:
                            self.player2.score += 1
                        self.__init__()  # 重新初始化
                        # 保留分数
                        old_score1 = self.player1.score
                        old_score2 = self.player2.score
                        self.reset_game()
                        self.player1.score = old_score1
                        self.player2.score = old_score2

            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(60)  # 60 FPS

        pygame.quit()
        sys.exit()


# ==================== 程序入口 ====================
if __name__ == "__main__":
    print("=== 光轮摩托 Tron ===")
    print("玩家1 (蓝色): W/A/S/D 控制方向")
    print("玩家2 (红色): 方向键 ↑/←/↓/→ 控制方向")
    print("撞墙或光墙则输, 按 R 重新开始, Q 退出\n")
    game = TronGame()
    game.run()