import pygame
import random
import sys

# 初始化 Pygame
pygame.init()

# 游戏常量
CELL_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 20
SCREEN_WIDTH = CELL_SIZE * GRID_WIDTH
SCREEN_HEIGHT = CELL_SIZE * GRID_HEIGHT + 60
FPS = 10

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 150, 0)
RED = (255, 50, 50)
GRAY = (50, 50, 50)
LIGHT_GRAY = (200, 200, 200)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# 方向向量
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)


class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        start_x = GRID_WIDTH // 2
        start_y = GRID_HEIGHT // 2
        self.body = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.grow_flag = False

    def change_direction(self, new_dir):
        opposite = (-self.direction[0], -self.direction[1])
        if new_dir != opposite:
            self.next_direction = new_dir

    def move(self):
        self.direction = self.next_direction
        head = self.body[0]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])
        self.body.insert(0, new_head)
        if self.grow_flag:
            self.grow_flag = False
        else:
            self.body.pop()

    def grow(self):
        self.grow_flag = True

    def check_collision(self):
        head = self.body[0]
        if head[0] < 0 or head[0] >= GRID_WIDTH or head[1] < 0 or head[1] >= GRID_HEIGHT:
            return True
        if head in self.body[1:]:
            return True
        return False

    def draw(self, screen):
        for i, segment in enumerate(self.body):
            rect = pygame.Rect(
                segment[0] * CELL_SIZE,
                segment[1] * CELL_SIZE + 60,
                CELL_SIZE - 1,
                CELL_SIZE - 1
            )
            color = GREEN if i == 0 else DARK_GREEN
            pygame.draw.rect(screen, color, rect, border_radius=3)
            if i == 0:
                eye_size = 4
                cx = segment[0] * CELL_SIZE + CELL_SIZE // 2
                cy = segment[1] * CELL_SIZE + 60 + CELL_SIZE // 2
                if self.direction == RIGHT:
                    pygame.draw.circle(screen, WHITE, (cx + 4, cy - 3), eye_size)
                    pygame.draw.circle(screen, WHITE, (cx + 4, cy + 3), eye_size)
                elif self.direction == LEFT:
                    pygame.draw.circle(screen, WHITE, (cx - 4, cy - 3), eye_size)
                    pygame.draw.circle(screen, WHITE, (cx - 4, cy + 3), eye_size)
                elif self.direction == UP:
                    pygame.draw.circle(screen, WHITE, (cx - 3, cy - 4), eye_size)
                    pygame.draw.circle(screen, WHITE, (cx + 3, cy - 4), eye_size)
                else:
                    pygame.draw.circle(screen, WHITE, (cx - 3, cy + 4), eye_size)
                    pygame.draw.circle(screen, WHITE, (cx + 3, cy + 4), eye_size)


class Food:
    def __init__(self):
        self.position = (0, 0)
        self.spawn_time = 0
        self.is_bonus = False

    def spawn(self, snake_body):
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if (x, y) not in snake_body:
                self.position = (x, y)
                break
        self.spawn_time = pygame.time.get_ticks()
        self.is_bonus = random.random() < 0.15

    def draw(self, screen):
        rect = pygame.Rect(
            self.position[0] * CELL_SIZE,
            self.position[1] * CELL_SIZE + 60,
            CELL_SIZE - 1,
            CELL_SIZE - 1
        )
        if self.is_bonus:
            pygame.draw.rect(screen, YELLOW, rect, border_radius=8)
            pygame.draw.rect(screen, ORANGE, rect, width=2, border_radius=8)
        else:
            pygame.draw.rect(screen, RED, rect, border_radius=8)


class Game:
    STATE_START = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2
    STATE_OVER = 3

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("贪吃蛇 - Snake Game")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.snake = Snake()
        self.food = Food()
        self.food.spawn(self.snake.body)
        self.score = 0
        self.high_score = 0
        self.state = self.STATE_START
        self.move_timer = 0

    def draw_top_bar(self):
        pygame.draw.rect(self.screen, GRAY, (0, 0, SCREEN_WIDTH, 60))
        score_text = self.font_medium.render(f"得分: {self.score}", True, WHITE)
        high_text = self.font_small.render(f"最高分: {self.high_score}", True, LIGHT_GRAY)
        self.screen.blit(score_text, (15, 12))
        self.screen.blit(high_text, (15, 38))
        hint_text = self.font_small.render("方向键移动 | P 暂停 | R 重新开始", True, LIGHT_GRAY)
        self.screen.blit(hint_text, (SCREEN_WIDTH - hint_text.get_width() - 15, 12))

    def draw_start_screen(self):
        self.screen.fill(BLACK)
        title = self.font_large.render("贪 吃 蛇", True, GREEN)
        subtitle = self.font_medium.render("SNAKE GAME", True, WHITE)
        prompt = self.font_small.render("按任意方向键开始游戏", True, LIGHT_GRAY)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 210))
        self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 280))

    def draw_game_over_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        over_text = self.font_large.render("游戏结束", True, RED)
        score_text = self.font_medium.render(f"最终得分: {self.score}", True, WHITE)
        prompt = self.font_small.render("按 R 重新开始 | 按 ESC 退出", True, LIGHT_GRAY)
        self.screen.blit(over_text, (SCREEN_WIDTH // 2 - over_text.get_width() // 2, 160))
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 230))
        self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 290))

    def draw_pause_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        pause_text = self.font_large.render("暂 停", True, WHITE)
        prompt = self.font_small.render("按 P 继续", True, LIGHT_GRAY)
        self.screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, 200))
        self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 270))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if self.state == self.STATE_START:
                    if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                        self.state = self.STATE_PLAYING
                        if event.key == pygame.K_UP:
                            self.snake.change_direction(UP)
                        elif event.key == pygame.K_DOWN:
                            self.snake.change_direction(DOWN)
                        elif event.key == pygame.K_LEFT:
                            self.snake.change_direction(LEFT)
                        else:
                            self.snake.change_direction(RIGHT)
                elif self.state == self.STATE_PLAYING:
                    if event.key == pygame.K_UP:
                        self.snake.change_direction(UP)
                    elif event.key == pygame.K_DOWN:
                        self.snake.change_direction(DOWN)
                    elif event.key == pygame.K_LEFT:
                        self.snake.change_direction(LEFT)
                    elif event.key == pygame.K_RIGHT:
                        self.snake.change_direction(RIGHT)
                    elif event.key == pygame.K_p:
                        self.state = self.STATE_PAUSED
                    elif event.key == pygame.K_r:
                        self.restart()
                elif self.state == self.STATE_PAUSED:
                    if event.key == pygame.K_p:
                        self.state = self.STATE_PLAYING
                elif self.state == self.STATE_OVER:
                    if event.key == pygame.K_r:
                        self.restart()
                    elif event.key == pygame.K_ESCAPE:
                        return False
        return True

    def update(self):
        if self.state != self.STATE_PLAYING:
            return
        self.move_timer += self.clock.get_time()
        if self.move_timer < 1000 // FPS:
            return
        self.move_timer = 0
        self.snake.move()
        if self.snake.check_collision():
            self.state = self.STATE_OVER
            if self.score > self.high_score:
                self.high_score = self.score
            return
        if self.snake.body[0] == self.food.position:
            if self.food.is_bonus:
                self.score += 3
            else:
                self.score += 1
            self.snake.grow()
            self.food.spawn(self.snake.body)

    def draw(self):
        self.screen.fill(BLACK)
        if self.state == self.STATE_START:
            self.draw_start_screen()
        else:
            self.draw_top_bar()
            for x in range(GRID_WIDTH):
                for y in range(GRID_HEIGHT):
                    rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE + 60, CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(self.screen, (20, 20, 20), rect, 1)
            self.food.draw(self.screen)
            self.snake.draw(self.screen)
            if self.state == self.STATE_PAUSED:
                self.draw_pause_screen()
            elif self.state == self.STATE_OVER:
                self.draw_game_over_screen()

    def restart(self):
        self.snake.reset()
        self.food.spawn(self.snake.body)
        self.score = 0
        self.state = self.STATE_PLAYING
        self.move_timer = 0

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()