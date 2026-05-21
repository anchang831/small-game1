
import pygame
import random
import sys

pygame.init()

CELL_SIZE = 30
COLS = 20
ROWS = 20
SCREEN_WIDTH = CELL_SIZE * COLS
SCREEN_HEIGHT = CELL_SIZE * ROWS + 80
FPS = 60

WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
BLUE = (50, 150, 255)
GREEN = (50, 255, 100)
RED = (255, 50, 50)
GRAY = (60, 60, 60)
LIGHT_GRAY = (200, 200, 200)
YELLOW = (255, 255, 0)
PURPLE = (180, 50, 255)

class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.walls = [True, True, True, True]
        self.visited = False

class MazeGame:
    STATE_GENERATING = 0
    STATE_PLAYING = 1
    STATE_WIN = 2

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Maze - 迷宫游戏")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.reset()

    def reset(self):
        self.grid = []
        for y in range(ROWS):
            row = []
            for x in range(COLS):
                row.append(Cell(x, y))
            self.grid.append(row)
        self.current = self.grid[0][0]
        self.stack = []
        self.player_x = 0
        self.player_y = 0
        self.goal_x = COLS - 1
        self.goal_y = ROWS - 1
        self.state = self.STATE_GENERATING
        self.moves = 0
        self.win_time = 0

    def index(self, x, y):
        if x < 0 or x >= COLS or y < 0 or y >= ROWS:
            return None
        return y * COLS + x

    def get_unvisited_neighbors(self, cell):
        neighbors = []
        x = cell.x
        y = cell.y

        if y - 1 >= 0 and not self.grid[y - 1][x].visited:
            neighbors.append(self.grid[y - 1][x])
        if x + 1 < COLS and not self.grid[y][x + 1].visited:
            neighbors.append(self.grid[y][x + 1])
        if y + 1 < ROWS and not self.grid[y + 1][x].visited:
            neighbors.append(self.grid[y + 1][x])
        if x - 1 >= 0 and not self.grid[y][x - 1].visited:
            neighbors.append(self.grid[y][x - 1])

        return neighbors

    def remove_walls(self, a, b):
        dx = a.x - b.x
        if dx == 1:
            a.walls[3] = False
            b.walls[1] = False
        elif dx == -1:
            a.walls[1] = False
            b.walls[3] = False
        dy = a.y - b.y
        if dy == 1:
            a.walls[0] = False
            b.walls[2] = False
        elif dy == -1:
            a.walls[2] = False
            b.walls[0] = False

    def generate_maze_step(self):
        self.current.visited = True
        neighbors = self.get_unvisited_neighbors(self.current)
        if neighbors:
            next_cell = random.choice(neighbors)
            self.stack.append(self.current)
            self.remove_walls(self.current, next_cell)
            self.current = next_cell
        elif self.stack:
            self.current = self.stack.pop()
        else:
            self.state = self.STATE_PLAYING

    def draw_cell(self, cell):
        x = cell.x * CELL_SIZE
        y = cell.y * CELL_SIZE + 80

        if cell.visited:
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(self.screen, BLACK, rect)

        if cell.walls[0]:
            pygame.draw.line(self.screen, WHITE, (x, y), (x + CELL_SIZE, y), 2)
        if cell.walls[1]:
            pygame.draw.line(self.screen, WHITE, (x + CELL_SIZE, y), (x + CELL_SIZE, y + CELL_SIZE), 2)
        if cell.walls[2]:
            pygame.draw.line(self.screen, WHITE, (x + CELL_SIZE, y + CELL_SIZE), (x, y + CELL_SIZE), 2)
        if cell.walls[3]:
            pygame.draw.line(self.screen, WHITE, (x, y + CELL_SIZE), (x, y), 2)

    def draw_player(self):
        px = self.player_x * CELL_SIZE + CELL_SIZE // 2
        py = self.player_y * CELL_SIZE + CELL_SIZE // 2 + 80
        pygame.draw.circle(self.screen, BLUE, (px, py), CELL_SIZE // 3)
        pygame.draw.circle(self.screen, WHITE, (px, py), CELL_SIZE // 3, 2)

    def draw_goal(self):
        gx = self.goal_x * CELL_SIZE + CELL_SIZE // 2
        gy = self.goal_y * CELL_SIZE + CELL_SIZE // 2 + 80
        pygame.draw.circle(self.screen, GREEN, (gx, gy), CELL_SIZE // 3)
        pygame.draw.circle(self.screen, WHITE, (gx, gy), CELL_SIZE // 3, 2)
        pygame.draw.circle(self.screen, YELLOW, (gx, gy), CELL_SIZE // 6)

    def draw_top_bar(self):
        pygame.draw.rect(self.screen, GRAY, (0, 0, SCREEN_WIDTH, 80))
        title = self.font_medium.render("Maze - 迷宫", True, WHITE)
        moves_text = self.font_small.render(f"Moves: {self.moves}", True, LIGHT_GRAY)
        hint_text = self.font_small.render("Arrow keys to move | R to regenerate", True, LIGHT_GRAY)
        self.screen.blit(title, (15, 15))
        self.screen.blit(moves_text, (15, 50))
        self.screen.blit(hint_text, (SCREEN_WIDTH - hint_text.get_width() - 15, 30))

    def draw_win_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        win_text = self.font_large.render("You Win!", True, GREEN)
        moves_text = self.font_medium.render(f"Total Moves: {self.moves}", True, WHITE)
        prompt = self.font_small.render("Press R to restart | ESC to exit", True, LIGHT_GRAY)
        self.screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, 200))
        self.screen.blit(moves_text, (SCREEN_WIDTH // 2 - moves_text.get_width() // 2, 260))
        self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 330))

    def check_wall(self, direction):
        current_cell = self.grid[self.player_y][self.player_x]
        if direction == "up":
            return current_cell.walls[0] or self.player_y == 0
        elif direction == "right":
            return current_cell.walls[1] or self.player_x == COLS - 1
        elif direction == "down":
            return current_cell.walls[2] or self.player_y == ROWS - 1
        elif direction == "left":
            return current_cell.walls[3] or self.player_x == 0
        return True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()
                if self.state == self.STATE_PLAYING:
                    if event.key == pygame.K_UP:
                        if not self.check_wall("up"):
                            self.player_y -= 1
                            self.moves += 1
                    elif event.key == pygame.K_DOWN:
                        if not self.check_wall("down"):
                            self.player_y += 1
                            self.moves += 1
                    elif event.key == pygame.K_LEFT:
                        if not self.check_wall("left"):
                            self.player_x -= 1
                            self.moves += 1
                    elif event.key == pygame.K_RIGHT:
                        if not self.check_wall("right"):
                            self.player_x += 1
                            self.moves += 1
                if self.state == self.STATE_WIN and event.key == pygame.K_ESCAPE:
                    return False
        return True

    def update(self):
        if self.state == self.STATE_GENERATING:
            for _ in range(20):
                self.generate_maze_step()
        elif self.state == self.STATE_PLAYING:
            if self.player_x == self.goal_x and self.player_y == self.goal_y:
                self.state = self.STATE_WIN

    def draw(self):
        self.screen.fill(BLACK)
        self.draw_top_bar()
        for row in self.grid:
            for cell in row:
                self.draw_cell(cell)
        if self.state != self.STATE_GENERATING:
            self.draw_goal()
            self.draw_player()
        if self.state == self.STATE_WIN:
            self.draw_win_screen()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = MazeGame()
    game.run()

