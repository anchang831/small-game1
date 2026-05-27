import pygame
import random
import sys

pygame.init()

WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("打地鼠")

WHITE = (255, 255, 255)
BROWN = (139, 69, 19)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

FPS = 60
clock = pygame.time.Clock()

class Hole:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 50
        self.mole = None
        self.mole_timer = 0
        self.mole_duration = 1500

    def draw(self):
        pygame.draw.circle(screen, BROWN, (self.x, self.y), self.radius)
        pygame.draw.circle(screen, BLACK, (self.x, self.y), self.radius - 10)
        if self.mole:
            color = GREEN if not self.mole.hit else RED
            pygame.draw.circle(screen, color, (self.x, self.y - 20), 40)

    def update(self, dt):
        if self.mole:
            self.mole_timer += dt
            if self.mole_timer >= self.mole_duration:
                self.mole = None
                self.mole_timer = 0

    def spawn_mole(self):
        if not self.mole:
            self.mole = Mole()
            self.mole_timer = 0

    def check_hit(self, pos):
        if self.mole and not self.mole.hit:
            dx = pos[0] - self.x
            dy = pos[1] - (self.y - 20)
            if dx*dx + dy*dy <= 40*40:
                self.mole.hit = True
                return True
        return False

class Mole:
    def __init__(self):
        self.hit = False

class Game:
    def __init__(self):
        self.holes = []
        self.score = 0
        self.time_left = 60000
        self.game_over = False
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 36)
        
        positions = [
            (200, 200), (400, 200), (600, 200),
            (200, 350), (400, 350), (600, 350),
            (200, 500), (400, 500), (600, 500)
        ]
        for pos in positions:
            self.holes.append(Hole(pos[0], pos[1]))
        
        self.spawn_timer = 0
        self.spawn_interval = 800

    def reset(self):
        self.score = 0
        self.time_left = 60000
        self.game_over = False
        for hole in self.holes:
            hole.mole = None
            hole.mole_timer = 0

    def draw(self):
        screen.fill(WHITE)
        
        for hole in self.holes:
            hole.draw()
        
        score_text = self.font.render(f"分数: {self.score}", True, BLACK)
        time_text = self.font.render(f"时间: {self.time_left // 1000}", True, BLACK)
        screen.blit(score_text, (20, 20))
        screen.blit(time_text, (WIDTH - 200, 20))
        
        if self.game_over:
            game_over_text = self.font.render("游戏结束!", True, RED)
            restart_text = self.small_font.render("按 R 重新开始", True, BLACK)
            screen.blit(game_over_text, (WIDTH//2 - 100, HEIGHT//2 - 50))
            screen.blit(restart_text, (WIDTH//2 - 100, HEIGHT//2 + 20))

    def update(self, dt):
        if not self.game_over:
            self.time_left -= dt
            if self.time_left <= 0:
                self.time_left = 0
                self.game_over = True
            
            for hole in self.holes:
                hole.update(dt)
            
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_interval:
                self.spawn_timer = 0
                available_holes = [h for h in self.holes if not h.mole]
                if available_holes:
                    random.choice(available_holes).spawn_mole()

    def handle_click(self, pos):
        if not self.game_over:
            for hole in self.holes:
                if hole.check_hit(pos):
                    self.score += 10

def main():
    game = Game()
    last_time = pygame.time.get_ticks()
    
    while True:
        current_time = pygame.time.get_ticks()
        dt = current_time - last_time
        last_time = current_time
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                game.handle_click(event.pos)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game.game_over:
                    game.reset()
        
        game.update(dt)
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
