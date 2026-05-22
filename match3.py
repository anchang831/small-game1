import pygame
import random
import sys

# Constants
WIDTH = 600
HEIGHT = 600
GRID_SIZE = 8
CELL_SIZE = 60
GEM_SIZE = 50
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

GEM_COLORS = [RED, GREEN, BLUE, YELLOW, PURPLE, ORANGE]

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("消消乐 (Match 3)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected = None
        self.score = 0
        self.moves = 30
        self.game_over = False
        self.initialize_grid()

    def initialize_grid(self):
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                self.grid[row][col] = random.randint(0, len(GEM_COLORS) - 1)
        while self.find_matches():
            self.remove_matches()
            self.drop_gems()
            self.fill_gaps()

    def draw_gem(self, x, y, color):
        pygame.draw.rect(self.screen, color, (x, y, GEM_SIZE, GEM_SIZE), border_radius=10)
        pygame.draw.rect(self.screen, WHITE, (x + 5, y + 5, GEM_SIZE - 10, GEM_SIZE - 10), 2, border_radius=8)

    def draw_grid(self):
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = col * CELL_SIZE + (CELL_SIZE - GEM_SIZE) // 2 + (WIDTH - GRID_SIZE * CELL_SIZE) // 2
                y = row * CELL_SIZE + (CELL_SIZE - GEM_SIZE) // 2 + 100
                color = GEM_COLORS[self.grid[row][col]]
                self.draw_gem(x, y, color)
                if self.selected == (row, col):
                    pygame.draw.rect(self.screen, WHITE, (x - 5, y - 5, GEM_SIZE + 10, GEM_SIZE + 10), 3, border_radius=10)

    def draw_ui(self):
        score_text = self.font.render(f"得分: {self.score}", True, WHITE)
        moves_text = self.font.render(f"剩余步数: {self.moves}", True, WHITE)
        self.screen.blit(score_text, (20, 20))
        self.screen.blit(moves_text, (20, 50))
        if self.game_over:
            game_over_text = self.font.render("游戏结束!", True, RED)
            restart_text = self.font.render("按 R 重新开始", True, WHITE)
            self.screen.blit(game_over_text, (WIDTH // 2 - 80, HEIGHT // 2 - 40))
            self.screen.blit(restart_text, (WIDTH // 2 - 120, HEIGHT // 2 + 20))

    def find_matches(self):
        matches = set()
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE - 2):
                if (self.grid[row][col] == self.grid[row][col + 1] == self.grid[row][col + 2] and
                        self.grid[row][col] is not None):
                    matches.update([(row, col), (row, col + 1), (row, col + 2)])
        for row in range(GRID_SIZE - 2):
            for col in range(GRID_SIZE):
                if (self.grid[row][col] == self.grid[row + 1][col] == self.grid[row + 2][col] and
                        self.grid[row][col] is not None):
                    matches.update([(row, col), (row + 1, col), (row + 2, col)])
        return matches

    def remove_matches(self):
        matches = self.find_matches()
        for row, col in matches:
            self.grid[row][col] = None
        self.score += len(matches) * 10

    def drop_gems(self):
        for col in range(GRID_SIZE):
            empty_slots = []
            for row in range(GRID_SIZE - 1, -1, -1):
                if self.grid[row][col] is None:
                    empty_slots.append(row)
                else:
                    if empty_slots:
                        self.grid[empty_slots.pop(0)][col] = self.grid[row][col]
                        self.grid[row][col] = None
                        empty_slots.append(row)

    def fill_gaps(self):
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if self.grid[row][col] is None:
                    self.grid[row][col] = random.randint(0, len(GEM_COLORS) - 1)

    def is_adjacent(self, pos1, pos2):
        row1, col1 = pos1
        row2, col2 = pos2
        return abs(row1 - row2) + abs(col1 - col2) == 1

    def swap_gems(self, pos1, pos2):
        row1, col1 = pos1
        row2, col2 = pos2
        self.grid[row1][col1], self.grid[row2][col2] = self.grid[row2][col2], self.grid[row1][col1]

    def handle_click(self, pos):
        if self.game_over:
            return
        x, y = pos
        col = (x - (WIDTH - GRID_SIZE * CELL_SIZE) // 2) // CELL_SIZE
        row = (y - 100) // CELL_SIZE
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            if self.selected is None:
                self.selected = (row, col)
            else:
                if self.is_adjacent(self.selected, (row, col)):
                    self.swap_gems(self.selected, (row, col))
                    if self.find_matches():
                        self.moves -= 1
                        while self.find_matches():
                            self.remove_matches()
                            self.drop_gems()
                            self.fill_gaps()
                        if self.moves <= 0:
                            self.game_over = True
                    else:
                        self.swap_gems(self.selected, (row, col))
                self.selected = None

    def restart(self):
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected = None
        self.score = 0
        self.moves = 30
        self.game_over = False
        self.initialize_grid()

    def run(self):
        running = True
        while running:
            self.screen.fill(BLACK)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(pygame.mouse.get_pos())
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.restart()
            self.draw_grid()
            self.draw_ui()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
