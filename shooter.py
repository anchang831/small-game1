import pygame
import random
import sys

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("射击游戏")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

clock = pygame.time.Clock()
FPS = 60

class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 100
        self.width = 50
        self.height = 50
        self.speed = 5
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
    
    def move(self, keys):
        if keys[pygame.K_LEFT] and self.x > 0:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] and self.x < SCREEN_WIDTH - self.width:
            self.x += self.speed
        if keys[pygame.K_UP] and self.y > 0:
            self.y -= self.speed
        if keys[pygame.K_DOWN] and self.y < SCREEN_HEIGHT - self.height:
            self.y += self.speed
        self.rect.x = self.x
        self.rect.y = self.y
    
    def draw(self):
        pygame.draw.rect(screen, GREEN, self.rect)

class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 5
        self.height = 15
        self.speed = -10
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
    
    def update(self):
        self.y += self.speed
        self.rect.y = self.y
    
    def draw(self):
        pygame.draw.rect(screen, BLUE, self.rect)

class Enemy:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH - 50)
        self.y = -50
        self.width = 50
        self.height = 50
        self.speed = random.randint(2, 5)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
    
    def update(self):
        self.y += self.speed
        self.rect.y = self.y
    
    def draw(self):
        pygame.draw.rect(screen, RED, self.rect)

def main():
    player = Player()
    bullets = []
    enemies = []
    score = 0
    font = pygame.font.Font(None, 36)
    
    enemy_spawn_timer = 0
    enemy_spawn_delay = 60
    
    running = True
    while running:
        screen.fill(BLACK)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bullets.append(Bullet(player.x + player.width // 2 - 2, player.y))
        
        keys = pygame.key.get_pressed()
        player.move(keys)
        
        enemy_spawn_timer += 1
        if enemy_spawn_timer >= enemy_spawn_delay:
            enemies.append(Enemy())
            enemy_spawn_timer = 0
        
        for bullet in bullets[:]:
            bullet.update()
            if bullet.y < -bullet.height:
                bullets.remove(bullet)
        
        for enemy in enemies[:]:
            enemy.update()
            if enemy.y > SCREEN_HEIGHT:
                enemies.remove(enemy)
        
        for bullet in bullets[:]:
            for enemy in enemies[:]:
                if bullet.rect.colliderect(enemy.rect):
                    bullets.remove(bullet)
                    enemies.remove(enemy)
                    score += 10
        
        for enemy in enemies[:]:
            if enemy.rect.colliderect(player.rect):
                running = False
        
        player.draw()
        for bullet in bullets:
            bullet.draw()
        for enemy in enemies:
            enemy.draw()
        
        score_text = font.render(f"得分: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
