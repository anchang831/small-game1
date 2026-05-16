
"""
2048 数字拼图游戏 - 2048 Game
日期: 2026-05-16
作者: AI Game Developer
"""

import pygame
import random
import sys

# 初始化 Pygame
pygame.init()

# 游戏窗口设置
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 650
FPS = 60

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (187, 173, 160)
LIGHT_GRAY = (238, 228, 218)
EMPTY_CELL_COLOR = (204, 192, 179)

# 数字方块颜色
CELL_COLORS = {
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
    4096: (60, 58, 50),
    8192: (60, 58, 50),
}

# 数字颜色
TEXT_COLORS = {
    2: (119, 110, 101),
    4: (119, 110, 101),
    8: (249, 246, 242),
    16: (249, 246, 242),
    32: (249, 246, 242),
    64: (249, 246, 242),
    128: (249, 246, 242),
    256: (249, 246, 242),
    512: (249, 246, 242),
    1024: (249, 246, 242),
    2048: (249, 246, 242),
    4096: (249, 246, 242),
    8192: (249, 246, 242),
}

# 游戏网格设置
GRID_SIZE = 4
CELL_SIZE = 100
CELL_PADDING = 15
GRID_TOP_OFFSET = 150

# 创建窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("2048 数字拼图")
clock = pygame.time.Clock()

# 加载字体
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 36)
font_tiny = pygame.font.Font(None, 24)


class Grid:
    """游戏网格类"""

    def __init__(self):
        self.reset()

    def reset(self):
        """重置网格"""
        self.cells = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.score = 0
        self.add_random_tile()
        self.add_random_tile()
        self.game_over = False
        self.won = False
        self.moved = False

    def add_random_tile(self):
        """添加随机数字方块"""
        empty_cells = []
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if self.cells[i][j] == 0:
                    empty_cells.append((i, j))
        if empty_cells:
            i, j = random.choice(empty_cells)
            self.cells[i][j] = 2 if random.random() < 0.9 else 4

    def compress(self, row):
        """压缩一行，将非零元素移到左边"""
        new_row = [num for num in row if num != 0]
        new_row += [0] * (GRID_SIZE - len(new_row))
        return new_row

    def merge(self, row):
        """合并相邻相同的数字"""
        for i in range(GRID_SIZE - 1):
            if row[i] != 0 and row[i] == row[i + 1]:
                row[i] *= 2
                self.score += row[i]
                row[i + 1] = 0
                if row[i] == 2048:
                    self.won = True
        return row

    def reverse(self, row):
        """反转一行"""
        return row[::-1]

    def transpose(self):
        """矩阵转置"""
        self.cells = [list(row) for row in zip(*self.cells)]

    def move_left(self):
        """向左移动"""
        self.moved = False
        for i in range(GRID_SIZE):
            original_row = self.cells[i].copy()
            compressed = self.compress(self.cells[i])
            merged = self.merge(compressed)
            final = self.compress(merged)
            self.cells[i] = final
            if original_row != final:
                self.moved = True
        if self.moved:
            self.add_random_tile()

    def move_right(self):
        """向右移动"""
        self.moved = False
        for i in range(GRID_SIZE):
            original_row = self.cells[i].copy()
            reversed_row = self.reverse(self.cells[i])
            compressed = self.compress(reversed_row)
            merged = self.merge(compressed)
            final = self.compress(merged)
            self.cells[i] = self.reverse(final)
            if original_row != self.cells[i]:
                self.moved = True
        if self.moved:
            self.add_random_tile()

    def move_up(self):
        """向上移动"""
        self.transpose()
        self.move_left()
        self.transpose()

    def move_down(self):
        """向下移动"""
        self.transpose()
        self.move_right()
        self.transpose()

    def can_move(self):
        """检查是否还能移动"""
        # 检查是否有空格
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if self.cells[i][j] == 0:
                    return True
        # 检查相邻格子是否有相同数字
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if j < GRID_SIZE - 1 and self.cells[i][j] == self.cells[i][j + 1]:
                    return True
                if i < GRID_SIZE - 1 and self.cells[i][j] == self.cells[i + 1][j]:
                    return True
        return False

    def draw(self):
        """绘制网格"""
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                x = j * (CELL_SIZE + CELL_PADDING) + CELL_PADDING
                y = GRID_TOP_OFFSET + i * (CELL_SIZE + CELL_PADDING) + CELL_PADDING

                # 绘制方块背景
                value = self.cells[i][j]
                if value == 0:
                    color = EMPTY_CELL_COLOR
                else:
                    color = CELL_COLORS.get(value, CELL_COLORS[8192])

                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, color, rect, border_radius=5)

                # 绘制数字
                if value != 0:
                    if value < 100:
                        font = font_large
                    elif value < 1000:
                        font = font_medium
                    else:
                        font = font_small

                    text_color = TEXT_COLORS.get(value, TEXT_COLORS[8192])
                    text = font.render(str(value), True, text_color)
                    text_rect = text.get_rect(center=(x + CELL_SIZE // 2, y + CELL_SIZE // 2))
                    screen.blit(text, text_rect)


class Game:
    """游戏主类"""

    def __init__(self):
        self.grid = Grid()
        self.state = "start"  # start, playing, game_over, won

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if self.state == "start":
                    if event.key == pygame.K_SPACE:
                        self.state = "playing"
                elif self.state == "playing":
                    if event.key == pygame.K_LEFT:
                        self.grid.move_left()
                    elif event.key == pygame.K_RIGHT:
                        self.grid.move_right()
                    elif event.key == pygame.K_UP:
                        self.grid.move_up()
                    elif event.key == pygame.K_DOWN:
                        self.grid.move_down()
                    elif event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "start"

                    # 检查游戏状态
                    if self.grid.won:
                        self.state = "won"
                    elif not self.grid.can_move():
                        self.grid.game_over = True
                        self.state = "game_over"
                elif self.state == "game_over" or self.state == "won":
                    if event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "start"
        return True

    def draw_background(self):
        """绘制背景"""
        screen.fill(GRAY)

    def draw_header(self):
        """绘制顶部信息栏"""
        # 游戏标题
        title = font_large.render("2048", True, WHITE)
        screen.blit(title, (20, 30))

        # 分数框
        score_rect = pygame.Rect(280, 30, 100, 80)
        pygame.draw.rect(screen, LIGHT_GRAY, score_rect, border_radius=5)
        score_label = font_tiny.render("分数", True, BLACK)
        score_label_rect = score_label.get_rect(center=(330, 50))
        screen.blit(score_label, score_label_rect)
        score_value = font_medium.render(str(self.grid.score), True, BLACK)
        score_value_rect = score_value.get_rect(center=(330, 85))
        screen.blit(score_value, score_value_rect)

        # 提示信息
        if self.state == "playing":
            hint = font_tiny.render("方向键移动 | R 重置 | ESC 返回", True, WHITE)
            hint_rect = hint.get_rect(center=(WINDOW_WIDTH // 2, 125))
            screen.blit(hint, hint_rect)

    def draw_start_screen(self):
        """绘制开始界面"""
        self.draw_background()
        self.draw_header()
        self.grid.draw()

        # 开始提示
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        title = font_large.render("2048", True, WHITE)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 200))
        screen.blit(title, title_rect)

        instructions = [
            "数字拼图游戏",
            "",
            "使用方向键移动方块",
            "相同数字合并",
            "目标: 得到 2048!",
            "",
            "按 空格 开始游戏"
        ]

        y = 300
        for line in instructions:
            text = font_small.render(line, True, WHITE)
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, y))
            screen.blit(text, text_rect)
            y += 40

    def draw_game_over_screen(self):
        """绘制游戏结束界面"""
        self.draw_background()
        self.draw_header()
        self.grid.draw()

        # 游戏结束提示
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        game_over_text = font_large.render("游戏结束", True, (255, 100, 100))
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, 300))
        screen.blit(game_over_text, game_over_rect)

        final_score = font_medium.render(f"最终分数: {self.grid.score}", True, WHITE)
        final_score_rect = final_score.get_rect(center=(WINDOW_WIDTH // 2, 360))
        screen.blit(final_score, final_score_rect)

        restart_text = font_small.render("按 R 重新开始 | ESC 返回", True, WHITE)
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, 420))
        screen.blit(restart_text, restart_rect)

    def draw_won_screen(self):
        """绘制胜利界面"""
        self.draw_background()
        self.draw_header()
        self.grid.draw()

        # 胜利提示
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        won_text = font_large.render("恭喜获胜!", True, (100, 255, 100))
        won_rect = won_text.get_rect(center=(WINDOW_WIDTH // 2, 300))
        screen.blit(won_text, won_rect)

        final_score = font_medium.render(f"分数: {self.grid.score}", True, WHITE)
        final_score_rect = final_score.get_rect(center=(WINDOW_WIDTH // 2, 360))
        screen.blit(final_score, final_score_rect)

        continue_text = font_small.render("按 R 重新开始 | ESC 返回", True, WHITE)
        continue_rect = continue_text.get_rect(center=(WINDOW_WIDTH // 2, 420))
        screen.blit(continue_text, continue_rect)

    def draw(self):
        """绘制游戏画面"""
        if self.state == "start":
            self.draw_start_screen()
        elif self.state == "game_over":
            self.draw_game_over_screen()
        elif self.state == "won":
            self.draw_won_screen()
        else:
            self.draw_background()
            self.draw_header()
            self.grid.draw()

        pygame.display.flip()

    def reset_game(self):
        """重置游戏"""
        self.grid.reset()
        self.state = "playing"

    def run(self):
        """游戏主循环"""
        running = True

        while running:
            running = self.handle_events()
            self.draw()
            clock.tick(FPS)

        pygame.quit()
        sys.exit()


# 主程序入口
if __name__ == "__main__":
    game = Game()
    game.run()

