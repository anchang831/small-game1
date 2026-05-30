import pygame
import random
import sys
from datetime import datetime

pygame.init()

TILE_SIZE = 40
GRID_COLS = 10
GRID_ROWS = 10
NUM_MINES = 15

HEADER_HEIGHT = 80
WINDOW_WIDTH = GRID_COLS * TILE_SIZE
WINDOW_HEIGHT = GRID_ROWS * TILE_SIZE + HEADER_HEIGHT
FPS = 60

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("扫雷 Minesweeper")
clock = pygame.time.Clock()

font_large = pygame.font.SysFont("arial", 36, bold=True)
font_medium = pygame.font.SysFont("arial", 24, bold=True)
font_small = pygame.font.SysFont("arial", 18, bold=True)

GRAY = (192, 192, 192)
DARK_GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
DARK_RED = (200, 0, 0)
GREEN = (0, 128, 0)
BLUE = (0, 0, 255)
DARK_BLUE = (0, 0, 128)
PURPLE = (128, 0, 128)
TEAL = (0, 128, 128)
ORANGE = (255, 140, 0)
YELLOW = (255, 255, 0)
LIGHT_GRAY = (220, 220, 220)
LIGHTER_GRAY = (240, 240, 240)
BG_COLOR = (60, 63, 65)
HEADER_BG = (45, 45, 48)

NUM_COLORS = {
    1: BLUE,
    2: GREEN,
    3: RED,
    4: DARK_BLUE,
    5: DARK_RED,
    6: TEAL,
    7: BLACK,
    8: DARK_GRAY,
}

UNREVEALED_COLOR = (140, 140, 140)
REVEALED_COLOR = (200, 200, 200)
FLAG_COLOR = (220, 50, 50)
MINE_COLOR = (40, 40, 40)
EXPLODED_COLOR = (255, 50, 50)

class Minesweeper:
    def __init__(self):
        self.reset()

    def reset(self):
        self.grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.revealed = [[False for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.flagged = [[False for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.mines_placed = False
        self.game_over = False
        self.won = False
        self.first_click = True
        self.start_time = None
        self.elapsed_seconds = 0

    def place_mines(self, safe_r, safe_c):
        mine_count = 0
        while mine_count < NUM_MINES:
            r = random.randint(0, GRID_ROWS - 1)
            c = random.randint(0, GRID_COLS - 1)
            if self.grid[r][c] == 9:
                continue
            if abs(r - safe_r) <= 1 and abs(c - safe_c) <= 1:
                continue
            self.grid[r][c] = 9
            mine_count += 1

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if self.grid[r][c] == 9:
                    continue
                count = 0
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS and self.grid[nr][nc] == 9:
                            count += 1
                self.grid[r][c] = count

    def reveal(self, r, c):
        if not (0 <= r < GRID_ROWS and 0 <= c < GRID_COLS):
            return
        if self.revealed[r][c] or self.flagged[r][c]:
            return

        self.revealed[r][c] = True

        if self.grid[r][c] == 0:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    self.reveal(r + dr, c + dc)

    def reveal_all_mines(self):
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if self.grid[r][c] == 9:
                    self.revealed[r][c] = True

    def check_win(self):
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if self.grid[r][c] != 9 and not self.revealed[r][c]:
                    return False
        return True

    def handle_click(self, pos, button):
        if self.game_over:
            return

        gx = (pos[0] - 0) // TILE_SIZE
        gy = (pos[1] - HEADER_HEIGHT) // TILE_SIZE

        if not (0 <= gx < GRID_COLS and 0 <= gy < GRID_ROWS):
            return

        if self.first_click:
            self.place_mines(gy, gx)
            self.first_click = False
            self.start_time = datetime.now()

        if button == 1:
            if self.flagged[gy][gx]:
                return
            if self.grid[gy][gx] == 9:
                self.revealed[gy][gx] = True
                self.reveal_all_mines()
                self.game_over = True
                return
            self.reveal(gy, gx)

            if self.check_win():
                self.game_over = True
                self.won = True
                for r in range(GRID_ROWS):
                    for c in range(GRID_COLS):
                        if self.grid[r][c] == 9:
                            self.flagged[r][c] = True

        elif button == 3:
            if not self.revealed[gy][gx]:
                self.flagged[gy][gx] = not self.flagged[gy][gx]

    def draw(self):
        screen.fill(BG_COLOR)

        pygame.draw.rect(screen, HEADER_BG, (0, 0, WINDOW_WIDTH, HEADER_HEIGHT))
        pygame.draw.line(screen, DARK_GRAY, (0, HEADER_HEIGHT), (WINDOW_WIDTH, HEADER_HEIGHT), 2)

        mine_display = font_large.render(f"{NUM_MINES - sum(row.count(True) for row in self.flagged)}", True, RED)
        screen.blit(mine_display, (15, HEADER_HEIGHT // 2 - mine_display.get_height() // 2))

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                x = c * TILE_SIZE
                y = r * TILE_SIZE + HEADER_HEIGHT
                rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

                if self.revealed[r][c]:
                    pygame.draw.rect(screen, REVEALED_COLOR, rect)
                    pygame.draw.rect(screen, DARK_GRAY, rect, 1)

                    val = self.grid[r][c]
                    if val == 9:
                        if self.game_over and not self.won:
                            pygame.draw.circle(screen, MINE_COLOR, rect.center, TILE_SIZE // 4)
                            if self.revealed[r][c] and self.grid[r][c] == 9:
                                pass
                    elif val > 0:
                        text = font_small.render(str(val), True, NUM_COLORS.get(val, BLACK))
                        screen.blit(text, (x + (TILE_SIZE - text.get_width()) // 2,
                                           y + (TILE_SIZE - text.get_height()) // 2))
                else:
                    pygame.draw.rect(screen, UNREVEALED_COLOR, rect)
                    bevel_size = 3
                    pygame.draw.rect(screen, LIGHTER_GRAY, (x, y, TILE_SIZE, bevel_size))
                    pygame.draw.rect(screen, LIGHTER_GRAY, (x, y, bevel_size, TILE_SIZE))
                    pygame.draw.rect(screen, DARK_GRAY, (x + TILE_SIZE - bevel_size, y, bevel_size, TILE_SIZE))
                    pygame.draw.rect(screen, DARK_GRAY, (x, y + TILE_SIZE - bevel_size, TILE_SIZE, bevel_size))
                    pygame.draw.rect(screen, DARK_GRAY, rect, 1)

                    if self.flagged[r][c]:
                        pygame.draw.polygon(screen, FLAG_COLOR, [
                            (x + 8, y + TILE_SIZE - 8),
                            (x + 8, y + 8),
                            (x + TILE_SIZE - 4, y + TILE_SIZE // 2),
                        ])
                        pole_start = (x + 8, y + 8)
                        pole_end = (x + 8, y + TILE_SIZE - 8)
                        pygame.draw.line(screen, BLACK, pole_start, pole_end, 2)

        if self.game_over:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (0, 0))

            center_x = WINDOW_WIDTH // 2
            center_y = WINDOW_HEIGHT // 2

            if self.won:
                msg = "你赢了! You Win!"
                color = GREEN
            else:
                msg = "游戏结束! Game Over!"
                color = RED
            win_text = font_large.render(msg, True, color, (0, 0, 0))
            win_rect = win_text.get_rect(center=(center_x, center_y - 20))
            screen.blit(win_text, win_rect)

            restart_text = font_medium.render("点击重新开始 Click to Restart", True, WHITE, (0, 0, 0))
            restart_rect = restart_text.get_rect(center=(center_x, center_y + 30))
            screen.blit(restart_text, restart_rect)

        if not self.game_over and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self.elapsed_seconds = int(elapsed)
            time_text = font_medium.render(f"⏱ {self.elapsed_seconds}s", True, WHITE)
            time_rect = time_text.get_rect()
            time_rect.right = WINDOW_WIDTH - 15
            time_rect.centery = HEADER_HEIGHT // 2
            screen.blit(time_text, time_rect)
        elif self.game_over and self.start_time:
            time_text = font_medium.render(f"⏱ {self.elapsed_seconds}s", True, WHITE)
            time_rect = time_text.get_rect()
            time_rect.right = WINDOW_WIDTH - 15
            time_rect.centery = HEADER_HEIGHT // 2
            screen.blit(time_text, time_rect)

        pygame.display.flip()


def main():
    game = Minesweeper()
    running = True

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if game.game_over:
                    game.reset()
                elif event.button in (1, 3):
                    game.handle_click(pos, event.button)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset()

        game.draw()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()