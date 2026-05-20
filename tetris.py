
import pygame
import random

# 初始化pygame
pygame.init()

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# 游戏区域大小
GRID_WIDTH = 10
GRID_HEIGHT = 20
CELL_SIZE = 30

# 窗口大小
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE + 200
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE

# 方块形状定义
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 0, 0], [1, 1, 1]],  # J
    [[0, 0, 1], [1, 1, 1]],  # L
    [[1, 1], [1, 1]],  # O
    [[0, 1, 1], [1, 1, 0]],  # S
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 1, 0], [0, 1, 1]]   # Z
]

# 方块颜色
SHAPE_COLORS = [CYAN, BLUE, ORANGE, YELLOW, GREEN, MAGENTA, RED]

class Tetris:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("俄罗斯方块")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.grid = [[BLACK for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = None
        self.current_x = 0
        self.current_y = 0
        self.current_color = None
        self.score = 0
        self.game_over = False
        self.fall_time = 0
        self.fall_speed = 500
        self.spawn_piece()

    def spawn_piece(self):
        shape_index = random.randint(0, len(SHAPES) - 1)
        self.current_piece = SHAPES[shape_index]
        self.current_color = SHAPE_COLORS[shape_index]
        self.current_x = GRID_WIDTH // 2 - len(self.current_piece[0]) // 2
        self.current_y = 0
        if self.check_collision(self.current_x, self.current_y):
            self.game_over = True

    def check_collision(self, x, y, piece=None):
        if piece is None:
            piece = self.current_piece
        for i, row in enumerate(piece):
            for j, cell in enumerate(row):
                if cell:
                    new_x = x + j
                    new_y = y + i
                    if new_x < 0 or new_x >= GRID_WIDTH or new_y >= GRID_HEIGHT:
                        return True
                    if new_y >= 0 and self.grid[new_y][new_x] != BLACK:
                        return True
        return False

    def rotate_piece(self):
        rotated = list(zip(*self.current_piece[::-1]))
        rotated = [list(row) for row in rotated]
        if not self.check_collision(self.current_x, self.current_y, rotated):
            self.current_piece = rotated

    def move_piece(self, dx, dy):
        new_x = self.current_x + dx
        new_y = self.current_y + dy
        if not self.check_collision(new_x, new_y):
            self.current_x = new_x
            self.current_y = new_y
            return True
        return False

    def lock_piece(self):
        for i, row in enumerate(self.current_piece):
            for j, cell in enumerate(row):
                if cell:
                    if self.current_y + i >= 0:
                        self.grid[self.current_y + i][self.current_x + j] = self.current_color
        self.clear_lines()
        self.spawn_piece()

    def clear_lines(self):
        lines_cleared = 0
        y = GRID_HEIGHT - 1
        while y >= 0:
            if all(cell != BLACK for cell in self.grid[y]):
                del self.grid[y]
                self.grid.insert(0, [BLACK for _ in range(GRID_WIDTH)])
                lines_cleared += 1
            else:
                y -= 1
        if lines_cleared > 0:
            self.score += lines_cleared * 100

    def draw_grid(self):
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                pygame.draw.rect(
                    self.screen,
                    self.grid[y][x],
                    (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE - 1, CELL_SIZE - 1)
                )

    def draw_piece(self):
        for i, row in enumerate(self.current_piece):
            for j, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        self.screen,
                        self.current_color,
                        (
                            (self.current_x + j) * CELL_SIZE,
                            (self.current_y + i) * CELL_SIZE,
                            CELL_SIZE - 1,
                            CELL_SIZE - 1
                        )
                    )

    def draw_info(self):
        score_text = self.font.render(f"分数: {self.score}", True, WHITE)
        self.screen.blit(score_text, (GRID_WIDTH * CELL_SIZE + 20, 50))
        
        if self.game_over:
            game_over_text = self.font.render("游戏结束!", True, RED)
            self.screen.blit(game_over_text, (GRID_WIDTH * CELL_SIZE + 20, 150))
            restart_text = self.font.render("按 R 重新开始", True, WHITE)
            self.screen.blit(restart_text, (GRID_WIDTH * CELL_SIZE + 20, 200))

    def reset_game(self):
        self.grid = [[BLACK for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.score = 0
        self.game_over = False
        self.spawn_piece()

    def run(self):
        running = True
        while running:
            current_time = pygame.time.get_ticks()
            delta_time = current_time - self.fall_time

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if not self.game_over:
                        if event.key == pygame.K_LEFT:
                            self.move_piece(-1, 0)
                        elif event.key == pygame.K_RIGHT:
                            self.move_piece(1, 0)
                        elif event.key == pygame.K_DOWN:
                            self.move_piece(0, 1)
                        elif event.key == pygame.K_UP:
                            self.rotate_piece()
                        elif event.key == pygame.K_SPACE:
                            while self.move_piece(0, 1):
                                pass
                            self.lock_piece()
                    else:
                        if event.key == pygame.K_r:
                            self.reset_game()

            if not self.game_over:
                if delta_time > self.fall_speed:
                    if not self.move_piece(0, 1):
                        self.lock_piece()
                    self.fall_time = current_time

            self.screen.fill(BLACK)
            self.draw_grid()
            self.draw_piece()
            self.draw_info()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = Tetris()
    game.run()
