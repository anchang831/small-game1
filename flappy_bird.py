import pygame
import random
import sys

pygame.init()

SCREEN_WIDTH = 480
SCREEN_HEIGHT = 720
FPS = 60

GRAVITY = 0.5
FLAP_STRENGTH = -9
PIPE_SPEED = -4
PIPE_GAP = 180
PIPE_FREQ = 1500
PIPE_WIDTH = 70
BIRD_RADIUS = 18

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 80)
DARK_GREEN = (0, 150, 50)
YELLOW = (255, 220, 50)
ORANGE = (255, 160, 20)
BLUE = (135, 206, 250)
GRAY = (180, 180, 180)
RED = (255, 80, 80)
BROWN = (139, 90, 43)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Flappy Bird - 飞扬小鸟')
clock = pygame.time.Clock()
font_large = pygame.font.SysFont('arial', 60)
font_medium = pygame.font.SysFont('arial', 36)
font_small = pygame.font.SysFont('arial', 24)

class Bird:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = SCREEN_WIDTH // 4
        self.y = SCREEN_HEIGHT // 2
        self.vel_y = 0
        self.angle = 0

    def flap(self):
        self.vel_y = FLAP_STRENGTH

    def update(self):
        self.vel_y += GRAVITY
        self.vel_y = min(self.vel_y, 15)
        self.y += self.vel_y
        if self.vel_y < 0:
            self.angle = max(-30, self.angle - 3)
        else:
            self.angle = min(90, self.angle + 4)

    def draw(self, surf):
        wing_offset = 0
        if self.vel_y < 0:
            wing_offset = -5
        body = pygame.Rect(0, 0, BIRD_RADIUS * 2, BIRD_RADIUS * 2)
        body.center = (self.x, self.y)
        rotated = pygame.Surface((BIRD_RADIUS * 2, BIRD_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(rotated, YELLOW, (BIRD_RADIUS, BIRD_RADIUS), BIRD_RADIUS)
        pygame.draw.circle(rotated, ORANGE, (BIRD_RADIUS + 6, BIRD_RADIUS - 4), 5)
        pygame.draw.circle(rotated, BLACK, (BIRD_RADIUS + 8, BIRD_RADIUS - 5), 2)
        pygame.draw.ellipse(rotated, ORANGE, (BIRD_RADIUS + 10, BIRD_RADIUS - 3, 10, 6))
        pygame.draw.ellipse(rotated, (255, 200, 50), (BIRD_RADIUS - 8, BIRD_RADIUS + 2 + wing_offset, 16, 8))
        rotated = pygame.transform.rotate(rotated, self.angle)
        rect = rotated.get_rect(center=(self.x, self.y))
        surf.blit(rotated, rect.topleft)

    def get_rect(self):
        return pygame.Rect(self.x - BIRD_RADIUS, self.y - BIRD_RADIUS, BIRD_RADIUS * 2, BIRD_RADIUS * 2)


class Pipe:
    def __init__(self, x):
        self.x = x
        self.gap_y = random.randint(180, SCREEN_HEIGHT - 180)
        self.passed = False
        self.gap_height = PIPE_GAP

    def update(self):
        self.x += PIPE_SPEED

    def draw(self, surf):
        top_rect = pygame.Rect(self.x, 0, PIPE_WIDTH, self.gap_y - self.gap_height // 2)
        bottom_rect = pygame.Rect(self.x, self.gap_y + self.gap_height // 2, PIPE_WIDTH, SCREEN_HEIGHT)

        pygame.draw.rect(surf, DARK_GREEN, top_rect)
        pygame.draw.rect(surf, GREEN, (self.x - 4, self.gap_y - self.gap_height // 2 - 20, PIPE_WIDTH + 8, 20))
        pygame.draw.rect(surf, DARK_GREEN, bottom_rect)
        pygame.draw.rect(surf, GREEN, (self.x - 4, self.gap_y + self.gap_height // 2, PIPE_WIDTH + 8, 20))

    def get_rects(self):
        top = pygame.Rect(self.x, 0, PIPE_WIDTH, self.gap_y - self.gap_height // 2)
        bottom = pygame.Rect(self.x, self.gap_y + self.gap_height // 2, PIPE_WIDTH, SCREEN_HEIGHT)
        return top, bottom

    def offscreen(self):
        return self.x + PIPE_WIDTH < 0


class Ground:
    def __init__(self):
        self.y = SCREEN_HEIGHT - 80
        self.x1 = 0
        self.x2 = SCREEN_WIDTH

    def update(self):
        self.x1 -= 3
        self.x2 -= 3
        if self.x1 + SCREEN_WIDTH <= 0:
            self.x1 = SCREEN_WIDTH
        if self.x2 + SCREEN_WIDTH <= 0:
            self.x2 = SCREEN_WIDTH

    def draw(self, surf):
        for x in (self.x1, self.x2):
            rect = pygame.Rect(x, self.y, SCREEN_WIDTH, 80)
            pygame.draw.rect(surf, (210, 180, 140), rect)
            pygame.draw.line(surf, (180, 150, 100), (x, self.y), (x + SCREEN_WIDTH, self.y), 3)
            for i in range(0, SCREEN_WIDTH, 20):
                pygame.draw.rect(surf, (190, 160, 110), (x + i, self.y + 5, 10, 15))
                pygame.draw.rect(surf, (170, 140, 90), (x + i + 10, self.y + 25, 10, 15))

    def get_rect(self):
        return pygame.Rect(0, self.y, SCREEN_WIDTH, 80)


def show_start_screen():
    screen.fill(BLUE)
    render_clouds()
    title = font_large.render('Flappy Bird', True, WHITE)
    title_shadow = font_large.render('Flappy Bird', True, BLACK)
    screen.blit(title_shadow, (SCREEN_WIDTH // 2 - title.get_width() // 2 + 3, 173))
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 170))
    sub = font_medium.render('按 SPACE 或点击开始', True, WHITE)
    sub_shadow = font_medium.render('按 SPACE 或点击开始', True, BLACK)
    screen.blit(sub_shadow, (SCREEN_WIDTH // 2 - sub.get_width() // 2 + 2, 242))
    screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 240))
    hint = font_small.render('最高分: ' + str(high_score), True, WHITE)
    screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 290))
    pygame.display.flip()
    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                waiting = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False
    return True


def render_clouds():
    for cx, cy, size in clouds:
        pygame.draw.ellipse(screen, (255, 255, 255, 200), (cx, cy, size * 3, size))
        pygame.draw.ellipse(screen, (255, 255, 255, 200), (cx + size, cy - size // 2, size * 2, size))


clouds = [(60, 100, 40), (300, 150, 35), (150, 250, 30), (380, 80, 45)]


def game_loop():
    global high_score
    bird = Bird()
    pipes = []
    ground = Ground()
    score = 0
    last_pipe = pygame.time.get_ticks()
    game_over = False
    passed = False

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game_over:
                        return True
                    bird.flap()
                if event.key == pygame.K_r and game_over:
                    return True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_over:
                    return True
                bird.flap()

        if not game_over:
            bird.update()
            ground.update()
            now = pygame.time.get_ticks()
            if now - last_pipe > PIPE_FREQ:
                pipes.append(Pipe(SCREEN_WIDTH))
                last_pipe = now

            for pipe in pipes[:]:
                pipe.update()
                if pipe.offscreen():
                    pipes.remove(pipe)

            for pipe in pipes:
                if not pipe.passed and pipe.x + PIPE_WIDTH < bird.x:
                    pipe.passed = True
                    score += 1

            bird_rect = bird.get_rect()
            if bird_rect.colliderect(ground.get_rect()) or bird.y - BIRD_RADIUS <= 0:
                game_over = True

            for pipe in pipes:
                top, bottom = pipe.get_rects()
                if bird_rect.colliderect(top) or bird_rect.colliderect(bottom):
                    game_over = True

        screen.fill(BLUE)
        render_clouds()

        for pipe in pipes:
            pipe.draw(screen)
        ground.draw(screen)
        bird.draw(screen)

        score_text = font_large.render(str(score), True, WHITE)
        score_shadow = font_large.render(str(score), True, BLACK)
        screen.blit(score_shadow, (SCREEN_WIDTH // 2 - score_text.get_width() // 2 + 3, 53))
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 50))

        if game_over:
            if score > high_score:
                high_score = score
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(100)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))

            over_text = font_large.render('游戏结束', True, RED)
            screen.blit(over_text, (SCREEN_WIDTH // 2 - over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 70))
            score_text2 = font_medium.render(f'得分: {score}', True, WHITE)
            screen.blit(score_text2, (SCREEN_WIDTH // 2 - score_text2.get_width() // 2, SCREEN_HEIGHT // 2 - 10))
            best_text = font_medium.render(f'最高分: {high_score}', True, YELLOW)
            screen.blit(best_text, (SCREEN_WIDTH // 2 - best_text.get_width() // 2, SCREEN_HEIGHT // 2 + 40))
            restart_text = font_small.render('按 R 或点击重新开始', True, WHITE)
            screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 90))

        pygame.display.flip()


high_score = 0
running = True
while running:
    if not show_start_screen():
        break
    result = game_loop()
    if result is None:
        break
    if not result:
        break

pygame.quit()
sys.exit()