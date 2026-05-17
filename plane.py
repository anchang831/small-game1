
"""
飞机大战游戏 - Plane Fight Game
日期: 2026-05-17
作者: AI Game Developer
"""

import pygame
import sys
import random
import math

# 初始化 Pygame
pygame.init()

# 游戏窗口设置
WINDOW_WIDTH = 480
WINDOW_HEIGHT = 700
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)

# 创建窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("飞机大战 - Plane Fight")
clock = pygame.time.Clock()

# 加载字体
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 36)
font_tiny = pygame.font.Font(None, 24)


class Player:
    """玩家飞机类"""

    def __init__(self):
        self.width = 60
        self.height = 80
        self.x = WINDOW_WIDTH // 2 - self.width // 2
        self.y = WINDOW_HEIGHT - 150
        self.speed = 5
        self.health = 3
        self.max_health = 3
        self.invincible = False
        self.invincible_time = 0

    def move(self, keys):
        """移动玩家飞机"""
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed

        # 边界检测
        if self.x < 0:
            self.x = 0
        if self.x > WINDOW_WIDTH - self.width:
            self.x = WINDOW_WIDTH - self.width
        if self.y < 0:
            self.y = 0
        if self.y > WINDOW_HEIGHT - self.height:
            self.y = WINDOW_HEIGHT - self.height

    def draw(self):
        """绘制玩家飞机"""
        if self.invincible:
            # 闪烁效果
            if pygame.time.get_ticks() % 200 < 100:
                return

        # 飞机主体
        pygame.draw.rect(screen, BLUE, (self.x + 20, self.y + 20, 20, 40), border_radius=5)
        # 机翼
        pygame.draw.polygon(screen, BLUE, [
            (self.x, self.y + 35),
            (self.x + 20, self.y + 20),
            (self.x + 20, self.y + 50)
        ])
        pygame.draw.polygon(screen, BLUE, [
            (self.x + 60, self.y + 35),
            (self.x + 40, self.y + 20),
            (self.x + 40, self.y + 50)
        ])
        # 机头
        pygame.draw.polygon(screen, CYAN, [
            (self.x + 30, self.y),
            (self.x + 20, self.y + 20),
            (self.x + 40, self.y + 20)
        ])
        # 机尾引擎
        pygame.draw.rect(screen, YELLOW, (self.x + 25, self.y + 60, 10, 20), border_radius=3)
        pygame.draw.rect(screen, ORANGE, (self.x + 27, self.y + 65, 6, 10), border_radius=2)

    def get_hitbox(self):
        """获取碰撞箱"""
        return pygame.Rect(self.x + 10, self.y + 10, self.width - 20, self.height - 20)


class Bullet:
    """子弹类"""

    def __init__(self, x, y, speed=10):
        self.x = x
        self.y = y
        self.width = 6
        self.height = 16
        self.speed = speed

    def move(self):
        """移动子弹"""
        self.y -= self.speed

    def draw(self):
        """绘制子弹"""
        pygame.draw.rect(screen, YELLOW, (self.x - self.width // 2, self.y - self.height, self.width, self.height), border_radius=3)
        pygame.draw.rect(screen, (255, 165, 0), (self.x - 2, self.y - 10, 4, 8), border_radius=2)

    def get_hitbox(self):
        """获取碰撞箱"""
        return pygame.Rect(self.x - self.width // 2, self.y - self.height, self.width, self.height)


class Enemy:
    """敌机类"""

    def __init__(self):
        self.width = random.randint(30, 50)
        self.height = self.width
        self.x = random.randint(0, WINDOW_WIDTH - self.width)
        self.y = -self.height
        self.speed = random.randint(2, 5)
        self.health = random.randint(1, 3)
        self.max_health = self.health
        self.points = self.health * 10

        # 随机颜色
        if self.health == 1:
            self.color = RED
        elif self.health == 2:
            self.color = ORANGE
        else:
            self.color = (200, 0, 200)

    def move(self):
        """移动敌机"""
        self.y += self.speed

    def draw(self):
        """绘制敌机"""
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height), border_radius=5)
        # 绘制生命值条
        if self.health < self.max_health:
            bar_width = self.width
            bar_height = 5
            health_ratio = self.health / self.max_health
            pygame.draw.rect(screen, GRAY, (self.x, self.y - 10, bar_width, bar_height), border_radius=2)
            pygame.draw.rect(screen, GREEN, (self.x, self.y - 10, bar_width * health_ratio, bar_height), border_radius=2)

    def get_hitbox(self):
        """获取碰撞箱"""
        return pygame.Rect(self.x, self.y, self.width, self.height)


class EnemyBullet:
    """敌机子弹类"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 8
        self.height = 12
        self.speed = 6

    def move(self):
        """移动敌机子弹"""
        self.y += self.speed

    def draw(self):
        """绘制敌机子弹"""
        pygame.draw.rect(screen, RED, (self.x - self.width // 2, self.y, self.width, self.height), border_radius=3)

    def get_hitbox(self):
        """获取碰撞箱"""
        return pygame.Rect(self.x - self.width // 2, self.y, self.width, self.height)


class Particle:
    """粒子类"""

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.size = random.randint(3, 8)
        self.color = color
        self.life = 30
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)

    def update(self):
        """更新粒子"""
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self):
        """绘制粒子"""
        alpha = int(255 * (self.life / 30))
        color = (*self.color, alpha)
        surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surface, color, (self.size, self.size), self.size)
        screen.blit(surface, (self.x - self.size, self.y - self.size))


class Game:
    """游戏主类"""

    def __init__(self):
        self.player = Player()
        self.bullets = []
        self.enemies = []
        self.enemy_bullets = []
        self.particles = []
        self.score = 0
        self.level = 1
        self.state = "start"  # start, playing, paused, game_over
        self.enemy_spawn_timer = 0
        self.enemy_shoot_timer = 0

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == "playing":
                        self.state = "paused"
                    elif self.state == "paused":
                        self.state = "playing"
                elif event.key == pygame.K_SPACE:
                    if self.state == "start":
                        self.state = "playing"
                    elif self.state == "game_over":
                        self.reset_game()
                elif event.key == pygame.K_p:
                    if self.state == "playing":
                        self.state = "paused"
                    elif self.state == "paused":
                        self.state = "playing"

        return True

    def update(self):
        """更新游戏状态"""
        if self.state != "playing":
            return

        # 玩家移动
        keys = pygame.key.get_pressed()
        self.player.move(keys)

        # 玩家射击
        if keys[pygame.K_SPACE] or keys[pygame.K_RETURN]:
            if len(self.bullets) < 10:  # 限制子弹数量
                bullet_x = self.player.x + self.player.width // 2
                bullet_y = self.player.y
                self.bullets.append(Bullet(bullet_x, bullet_y))

        # 更新玩家无敌状态
        if self.player.invincible and pygame.time.get_ticks() - self.player.invincible_time > 2000:
            self.player.invincible = False

        # 更新子弹
        for bullet in self.bullets[:]:
            bullet.move()
            if bullet.y < -20:
                self.bullets.remove(bullet)

        # 生成敌机
        self.enemy_spawn_timer += clock.get_time()
        if self.enemy_spawn_timer > max(500, 2000 - self.level * 100):
            self.enemies.append(Enemy())
            self.enemy_spawn_timer = 0

        # 更新敌机
        for enemy in self.enemies[:]:
            enemy.move()
            if enemy.y > WINDOW_HEIGHT + 50:
                self.enemies.remove(enemy)

        # 敌机射击
        self.enemy_shoot_timer += clock.get_time()
        if self.enemy_shoot_timer > 1500:
            for enemy in self.enemies:
                if random.random() < 0.3:
                    self.enemy_bullets.append(EnemyBullet(enemy.x + enemy.width // 2, enemy.y + enemy.height))
            self.enemy_shoot_timer = 0

        # 更新敌机子弹
        for bullet in self.enemy_bullets[:]:
            bullet.move()
            if bullet.y > WINDOW_HEIGHT + 20:
                self.enemy_bullets.remove(bullet)

        # 检测子弹与敌机碰撞
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if bullet.get_hitbox().colliderect(enemy.get_hitbox()):
                    self.bullets.remove(bullet)
                    enemy.health -= 1
                    # 添加粒子效果
                    for _ in range(5):
                        self.particles.append(Particle(bullet.x, bullet.y, YELLOW))
                    if enemy.health <= 0:
                        self.score += enemy.points
                        self.enemies.remove(enemy)
                        # 添加爆炸粒子效果
                        for _ in range(15):
                            self.particles.append(Particle(enemy.x + enemy.width // 2, enemy.y + enemy.height // 2, RED))
                    break

        # 检测敌机与玩家碰撞
        if not self.player.invincible:
            for enemy in self.enemies[:]:
                if self.player.get_hitbox().colliderect(enemy.get_hitbox()):
                    self.player.health -= 1
                    self.player.invincible = True
                    self.player.invincible_time = pygame.time.get_ticks()
                    self.enemies.remove(enemy)
                    # 添加爆炸粒子效果
                    for _ in range(15):
                        self.particles.append(Particle(self.player.x + self.player.width // 2, self.player.y + self.player.height // 2, RED))
                    if self.player.health <= 0:
                        self.state = "game_over"
                    break

        # 检测敌机子弹与玩家碰撞
        if not self.player.invincible:
            for bullet in self.enemy_bullets[:]:
                if self.player.get_hitbox().colliderect(bullet.get_hitbox()):
                    self.player.health -= 1
                    self.player.invincible = True
                    self.player.invincible_time = pygame.time.get_ticks()
                    self.enemy_bullets.remove(bullet)
                    # 添加粒子效果
                    for _ in range(10):
                        self.particles.append(Particle(bullet.x, bullet.y, RED))
                    if self.player.health <= 0:
                        self.state = "game_over"
                    break

        # 更新粒子
        for particle in self.particles[:]:
            particle.update()
            if particle.life <= 0:
                self.particles.remove(particle)

        # 升级
        if self.score > self.level * 500:
            self.level += 1

    def draw_background(self):
        """绘制背景"""
        screen.fill(BLACK)
        # 绘制星星
        for i in range(50):
            x = (i * 73) % WINDOW_WIDTH
            y = (i * 137) % WINDOW_HEIGHT
            pygame.draw.circle(screen, WHITE, (x, y), 1)

    def draw_hud(self):
        """绘制游戏界面信息"""
        # 分数
        score_text = font_small.render(f"分数: {self.score}", True, WHITE)
        screen.blit(score_text, (20, 20))

        # 等级
        level_text = font_small.render(f"等级: {self.level}", True, WHITE)
        screen.blit(level_text, (20, 60))

        # 生命值
        health_text = font_small.render(f"生命: {self.player.health}", True, WHITE)
        screen.blit(health_text, (WINDOW_WIDTH - 150, 20))
        # 绘制生命条
        bar_width = 120
        bar_height = 15
        health_ratio = self.player.health / self.player.max_health
        pygame.draw.rect(screen, GRAY, (WINDOW_WIDTH - 150, 50, bar_width, bar_height), border_radius=5)
        pygame.draw.rect(screen, GREEN, (WINDOW_WIDTH - 150, 50, bar_width * health_ratio, bar_height), border_radius=5)

    def draw_start_screen(self):
        """绘制开始界面"""
        self.draw_background()
        title = font_large.render("飞机大战", True, CYAN)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 200))
        screen.blit(title, title_rect)

        instructions = [
            "W A S D 或 方向键: 移动",
            "空格 或 回车: 射击",
            "ESC 或 P: 暂停",
            "",
            "目标: 消灭敌机, 获得高分!",
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
        game_over_text = font_large.render("游戏结束", True, RED)
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, 200))
        screen.blit(game_over_text, game_over_rect)

        score_text = font_medium.render(f"最终分数: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, 280))
        screen.blit(score_text, score_rect)

        level_text = font_small.render(f"最终等级: {self.level}", True, WHITE)
        level_rect = level_text.get_rect(center=(WINDOW_WIDTH // 2, 330))
        screen.blit(level_text, level_rect)

        restart_text = font_small.render("按 空格 重新开始", True, YELLOW)
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, 400))
        screen.blit(restart_text, restart_rect)

    def draw(self):
        """绘制游戏画面"""
        if self.state == "start":
            self.draw_start_screen()
        elif self.state == "game_over":
            self.draw_game_over_screen()
        else:
            self.draw_background()

            # 绘制子弹
            for bullet in self.bullets:
                bullet.draw()

            # 绘制敌机
            for enemy in self.enemies:
                enemy.draw()

            # 绘制敌机子弹
            for bullet in self.enemy_bullets:
                bullet.draw()

            # 绘制玩家
            self.player.draw()

            # 绘制粒子
            for particle in self.particles:
                particle.draw()

            self.draw_hud()

            if self.state == "paused":
                pause_text = font_large.render("暂停", True, YELLOW)
                text_rect = pause_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
                pygame.draw.rect(screen, BLACK, text_rect.inflate(30, 20))
                screen.blit(pause_text, text_rect)

        pygame.display.flip()

    def reset_game(self):
        """重置游戏"""
        self.player = Player()
        self.bullets = []
        self.enemies = []
        self.enemy_bullets = []
        self.particles = []
        self.score = 0
        self.level = 1
        self.state = "playing"
        self.enemy_spawn_timer = 0
        self.enemy_shoot_timer = 0

    def run(self):
        """游戏主循环"""
        running = True

        while running:
            running = self.handle_events()

            if self.state == "playing":
                self.update()

            self.draw()
            clock.tick(FPS)

        pygame.quit()
        sys.exit()


# 定义一些缺失的颜色
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)

# 主程序入口
if __name__ == "__main__":
    game = Game()
    game.run()
