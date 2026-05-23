import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Game constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 500
GROUND_Y = 400
FPS = 60

# Color definitions
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)
DARK_BLUE = (30, 100, 200)
RED = (255, 50, 50)
GRAY = (100, 100, 100)
LIGHT_GRAY = (180, 180, 180)
GREEN = (50, 200, 50)
BROWN = (139, 69, 19)


class Player:
    def __init__(self):
        self.width = 40
        self.height = 50
        self.x = 100
        self.y = GROUND_Y - self.height
        self.velocity_y = 0
        self.gravity = 0.8
        self.jump_strength = -18
        self.is_jumping = False
        self.on_ground = True

    def jump(self):
        if self.on_ground:
            self.velocity_y = self.jump_strength
            self.is_jumping = True
            self.on_ground = False

    def update(self):
        self.velocity_y += self.gravity
        self.y += self.velocity_y
        if self.y >= GROUND_Y - self.height:
            self.y = GROUND_Y - self.height
            self.velocity_y = 0
            self.is_jumping = False
            self.on_ground = True

    def draw(self, screen):
        pygame.draw.rect(screen, BLUE, (self.x, self.y, self.width, self.height), border_radius=5)
        pygame.draw.rect(screen, DARK_BLUE, (self.x + 5, self.y + 5, self.width - 10, self.height - 10), border_radius=3)
        pygame.draw.circle(screen, WHITE, (self.x + 12, self.y + 18), 5)
        pygame.draw.circle(screen, WHITE, (self.x + 28, self.y + 18), 5)
        pygame.draw.circle(screen, BLACK, (self.x + 14, self.y + 18), 2)
        pygame.draw.circle(screen, BLACK, (self.x + 30, self.y + 18), 2)


class Obstacle:
    def __init__(self, x):
        self.type = random.choice(["cactus", "rock"])
        if self.type == "cactus":
            self.width = 30
            self.height = 60
        else:
            self.width = 50
            self.height = 40
        self.x = x
        self.y = GROUND_Y - self.height
        self.speed = 5

    def update(self):
        self.x -= self.speed

    def draw(self, screen):
        if self.type == "cactus":
            pygame.draw.rect(screen, GREEN, (self.x, self.y, self.width, self.height), border_radius=3)
            pygame.draw.rect(screen, (30, 150, 30), (self.x + 5, self.y + 5, self.width - 10, self.height - 10), border_radius=2)
        else:
            pygame.draw.rect(screen, GRAY, (self.x, self.y, self.width, self.height), border_radius=8)
            pygame.draw.rect(screen, LIGHT_GRAY, (self.x + 10, self.y + 5, self.width - 20, self.height - 10), border_radius=5)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 12
        self.collected = False
        self.speed = 5

    def update(self):
        self.x -= self.speed

    def draw(self, screen):
        if not self.collected:
            pygame.draw.circle(screen, (255, 215, 0), (self.x, self.y), self.radius)
            pygame.draw.circle(screen, (255, 165, 0), (self.x, self.y), self.radius - 4)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)


class Game:
    STATE_START = 0
    STATE_PLAYING = 1
    STATE_PAUSED = 2
    STATE_OVER = 3

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("跑酷游戏 - Runner Game")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 60)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 28)
        self.player = Player()
        self.obstacles = []
        self.coins = []
        self.score = 0
        self.high_score = 0
        self.state = self.STATE_START
        self.obstacle_timer = 0
        self.coin_timer = 0
        self.speed_increase = 0

    def reset(self):
        self.player = Player()
        self.obstacles = []
        self.coins = []
        self.score = 0
        self.obstacle_timer = 0
        self.coin_timer = 0
        self.speed_increase = 0

    def draw_ground(self):
        pygame.draw.rect(self.screen, BROWN, (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))
        for i in range(0, SCREEN_WIDTH, 40):
            pygame.draw.rect(self.screen, (160, 82, 45), (i, GROUND_Y, 20, 10))

    def draw_background(self):
        self.screen.fill((135, 206, 235))
        pygame.draw.circle(self.screen, (255, 255, 200), (700, 80), 40)
        pygame.draw.circle(self.screen, WHITE, (200, 100), 30)
        pygame.draw.circle(self.screen, WHITE, (230, 100), 40)
        pygame.draw.circle(self.screen, WHITE, (260, 100), 30)
        pygame.draw.circle(self.screen, WHITE, (500, 150), 35)
        pygame.draw.circle(self.screen, WHITE, (540, 150), 45)
        pygame.draw.circle(self.screen, WHITE, (580, 150), 35)

    def draw_start_screen(self):
        self.draw_background()
        self.draw_ground()
        title = self.font_large.render("跑 酷 游 戏", True, BLACK)
        subtitle = self.font_medium.render("RUNNER GAME", True, DARK_BLUE)
        prompt = self.font_small.render("按 空格键 开始游戏", True, GRAY)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 190))
        self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 260))

    def draw_game_over_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        over_text = self.font_large.render("游戏结束", True, RED)
        score_text = self.font_medium.render(f"最终得分: {self.score}", True, WHITE)
        prompt = self.font_small.render("按 R 重新开始 | 按 ESC 退出", True, LIGHT_GRAY)
        self.screen.blit(over_text, (SCREEN_WIDTH // 2 - over_text.get_width() // 2, 150))
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 220))
        self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 280))

    def draw_pause_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        pause_text = self.font_large.render("暂 停", True, WHITE)
        prompt = self.font_small.render("按 P 继续", True, LIGHT_GRAY)
        self.screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, 200))
        self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 270))

    def draw_score(self):
        score_text = self.font_medium.render(f"得分: {self.score}", True, BLACK)
        high_text = self.font_small.render(f"最高分: {self.high_score}", True, GRAY)
        self.screen.blit(score_text, (20, 20))
        self.screen.blit(high_text, (20, 60))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if self.state == self.STATE_START:
                    if event.key == pygame.K_SPACE:
                        self.reset()
                        self.state = self.STATE_PLAYING
                elif self.state == self.STATE_PLAYING:
                    if event.key == pygame.K_SPACE:
                        self.player.jump()
                    elif event.key == pygame.K_p:
                        self.state = self.STATE_PAUSED
                    elif event.key == pygame.K_r:
                        self.reset()
                        self.state = self.STATE_PLAYING
                elif self.state == self.STATE_PAUSED:
                    if event.key == pygame.K_p:
                        self.state = self.STATE_PLAYING
                elif self.state == self.STATE_OVER:
                    if event.key == pygame.K_r:
                        self.reset()
                        self.state = self.STATE_PLAYING
                    elif event.key == pygame.K_ESCAPE:
                        return False
        return True

    def update(self):
        if self.state != self.STATE_PLAYING:
            return
        self.player.update()
        self.speed_increase = min(self.score // 50, 8)
        self.obstacle_timer += self.clock.get_time()
        if self.obstacle_timer > 1500 - self.speed_increase * 100:
            self.obstacle_timer = 0
            self.obstacles.append(Obstacle(SCREEN_WIDTH + 100))
        self.coin_timer += self.clock.get_time()
        if self.coin_timer > 2000:
            self.coin_timer = 0
            coin_y = random.randint(GROUND_Y - 150, GROUND_Y - 80)
            self.coins.append(Coin(SCREEN_WIDTH + 100, coin_y))
        for obstacle in self.obstacles[:]:
            obstacle.speed = 5 + self.speed_increase
            obstacle.update()
            if obstacle.x < -obstacle.width:
                self.obstacles.remove(obstacle)
        for coin in self.coins[:]:
            coin.speed = 5 + self.speed_increase
            coin.update()
            if coin.x < -coin.radius * 2:
                self.coins.remove(coin)
        player_rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.height)
        for obstacle in self.obstacles:
            if player_rect.colliderect(obstacle.get_rect()):
                self.state = self.STATE_OVER
                if self.score > self.high_score:
                    self.high_score = self.score
        for coin in self.coins:
            if not coin.collected and player_rect.colliderect(coin.get_rect()):
                coin.collected = True
                self.score += 10
        self.score += 1

    def draw(self):
        self.draw_background()
        if self.state == self.STATE_START:
            self.draw_start_screen()
        else:
            self.draw_ground()
            for obstacle in self.obstacles:
                obstacle.draw(self.screen)
            for coin in self.coins:
                coin.draw(self.screen)
            self.player.draw(self.screen)
            self.draw_score()
            if self.state == self.STATE_PAUSED:
                self.draw_pause_screen()
            elif self.state == self.STATE_OVER:
                self.draw_game_over_screen()

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
    game = Game()
    game.run()
