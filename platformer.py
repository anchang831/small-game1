"""
2D平台闯关游戏 - Platformer Game
日期: 2026-05-26
作者: AI Game Developer
"""

import pygame
import sys
import random

# 初始化 Pygame
pygame.init()

# 游戏窗口设置
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
GRAVITY = 0.8
JUMP_FORCE = -16

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
RED = (220, 20, 60)
YELLOW = (255, 215, 0)
ORANGE = (255, 140, 0)
BLUE = (30, 144, 255)
GRAY = (128, 128, 128)

# 创建窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("2D平台闯关 - Platformer Game")
clock = pygame.time.Clock()

# 加载字体
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 36)

class Player:
    """玩家类"""
    def __init__(self, x, y):
        self.width = 40
        self.height = 50
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.speed = 5
        self.on_ground = False
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = BLUE
        self.facing_right = True

    def move(self, left, right):
        """移动玩家"""
        if left:
            self.dx = -self.speed
            self.facing_right = False
        elif right:
            self.dx = self.speed
            self.facing_right = True
        else:
            self.dx = 0

        # 应用重力
        self.dy += GRAVITY
        self.x += self.dx
        self.y += self.dy

        # 边界检测
        if self.x < 0:
            self.x = 0
        if self.x + self.width > WINDOW_WIDTH:
            self.x = WINDOW_WIDTH - self.width

        # 更新矩形
        self.rect.x = self.x
        self.rect.y = self.y

    def jump(self):
        """跳跃"""
        if self.on_ground:
            self.dy = JUMP_FORCE
            self.on_ground = False

    def draw(self):
        """绘制玩家"""
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
        # 绘制眼睛
        eye_x = self.x + (self.width - 10) if self.facing_right else self.x + 5
        pygame.draw.circle(screen, WHITE, (int(eye_x + 5), int(self.y + 15)), 5)
        pygame.draw.circle(screen, BLACK, (int(eye_x + 7), int(self.y + 15)), 2)

    def reset(self, x, y):
        """重置玩家位置"""
        self.x = x
        self.y = y
        self.dx = 0
        self.dy = 0
        self.on_ground = False
        self.rect.x = x
        self.rect.y = y

class Platform:
    """平台类"""
    def __init__(self, x, y, width, height, color=GREEN):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

    def draw(self):
        """绘制平台"""
        pygame.draw.rect(screen, self.color, self.rect)
        # 绘制顶部装饰
        top_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, 5)
        pygame.draw.rect(screen, DARK_GREEN, top_rect)

class Coin:
    """金币类"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 15
        self.collected = False
        self.rect = pygame.Rect(x - self.radius, y - self.radius, self.radius * 2, self.radius * 2)

    def draw(self):
        """绘制金币"""
        if not self.collected:
            pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, ORANGE, (int(self.x), int(self.y)), self.radius - 5)

class Enemy:
    """敌人类"""
    def __init__(self, x, y, patrol_start, patrol_end):
        self.x = x
        self.y = y
        self.width = 35
        self.height = 35
        self.patrol_start = patrol_start
        self.patrol_end = patrol_end
        self.speed = 2
        self.direction = 1  # 1向右，-1向左
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = RED

    def update(self):
        """更新敌人位置"""
        self.x += self.speed * self.direction
        if self.x <= self.patrol_start:
            self.direction = 1
        if self.x + self.width >= self.patrol_end:
            self.direction = -1
        self.rect.x = self.x

    def draw(self):
        """绘制敌人"""
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
        # 绘制眼睛
        eye_x = self.x + (self.width - 8) if self.direction == 1 else self.x + 5
        pygame.draw.circle(screen, WHITE, (int(eye_x + 4), int(self.y + 10)), 4)
        pygame.draw.circle(screen, BLACK, (int(eye_x + 5), int(self.y + 10)), 2)

class Goal:
    """目标类"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 50
        self.height = 60
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = YELLOW

    def draw(self):
        """绘制目标"""
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
        # 绘制旗帜
        pole_x = self.x + 10
        pygame.draw.line(screen, BLACK, (pole_x, self.y), (pole_x, self.y - 40), 3)
        flag_rect = pygame.Rect(pole_x + 2, self.y - 40, 30, 20)
        pygame.draw.rect(screen, RED, flag_rect)

class Level:
    """关卡类"""
    def __init__(self, level_num):
        self.level_num = level_num
        self.platforms = []
        self.coins = []
        self.enemies = []
        self.goal = None
        self.player_start = (50, 450)
        self.create_level()

    def create_level(self):
        """创建关卡"""
        # 地面平台
        self.platforms.append(Platform(0, 550, WINDOW_WIDTH, 50, GRAY))
        
        if self.level_num == 1:
            # 第一关
            self.platforms.append(Platform(100, 450, 150, 20))
            self.platforms.append(Platform(300, 380, 150, 20))
            self.platforms.append(Platform(500, 300, 150, 20))
            self.platforms.append(Platform(650, 220, 100, 20))
            
            self.coins.append(Coin(175, 420))
            self.coins.append(Coin(375, 350))
            self.coins.append(Coin(575, 270))
            self.coins.append(Coin(700, 190))
            
            self.enemies.append(Enemy(300, 515, 300, 450))
            
            self.goal = Goal(675, 160)
            
        elif self.level_num == 2:
            # 第二关
            self.platforms.append(Platform(80, 480, 120, 20))
            self.platforms.append(Platform(250, 400, 100, 20))
            self.platforms.append(Platform(400, 320, 120, 20))
            self.platforms.append(Platform(200, 240, 100, 20))
            self.platforms.append(Platform(550, 200, 120, 20))
            self.platforms.append(Platform(700, 140, 80, 20))
            
            self.coins.append(Coin(140, 450))
            self.coins.append(Coin(300, 370))
            self.coins.append(Coin(460, 290))
            self.coins.append(Coin(250, 210))
            self.coins.append(Coin(610, 170))
            
            self.enemies.append(Enemy(80, 515, 80, 200))
            self.enemies.append(Enemy(400, 515, 400, 520))
            
            self.goal = Goal(710, 80)
            
        elif self.level_num == 3:
            # 第三关
            self.platforms.append(Platform(50, 500, 80, 20))
            self.platforms.append(Platform(180, 420, 80, 20))
            self.platforms.append(Platform(320, 340, 80, 20))
            self.platforms.append(Platform(450, 420, 80, 20))
            self.platforms.append(Platform(580, 340, 80, 20))
            self.platforms.append(Platform(400, 260, 100, 20))
            self.platforms.append(Platform(600, 180, 150, 20))
            
            self.coins.append(Coin(90, 470))
            self.coins.append(Coin(220, 390))
            self.coins.append(Coin(360, 310))
            self.coins.append(Coin(490, 390))
            self.coins.append(Coin(620, 310))
            self.coins.append(Coin(450, 230))
            
            self.enemies.append(Enemy(180, 515, 180, 320))
            self.enemies.append(Enemy(450, 515, 450, 530))
            
            self.goal = Goal(675, 120)

    def reset(self):
        """重置关卡"""
        for coin in self.coins:
            coin.collected = False
        for enemy in self.enemies:
            enemy.x = enemy.patrol_start if enemy.direction == 1 else enemy.patrol_end - enemy.width
            enemy.rect.x = enemy.x

class Game:
    """游戏主类"""
    def __init__(self):
        self.player = Player(50, 450)
        self.level = Level(1)
        self.score = 0
        self.lives = 3
        self.state = "start"  # start, playing, paused, level_complete, game_over, game_won
        self.current_level = 1
        self.max_level = 3

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.state == "start":
                        self.state = "playing"
                    elif self.state == "level_complete":
                        self.next_level()
                    elif self.state == "game_over" or self.state == "game_won":
                        self.reset_game()
                    elif self.state == "playing":
                        self.player.jump()
                elif event.key == pygame.K_ESCAPE:
                    if self.state == "playing":
                        self.state = "paused"
                    elif self.state == "paused":
                        self.state = "playing"
                elif event.key == pygame.K_p:
                    if self.state == "playing":
                        self.state = "paused"
                    elif self.state == "paused":
                        self.state = "playing"
                elif event.key == pygame.K_r:
                    if self.state == "game_over":
                        self.reset_game()

        return True

    def update(self):
        """更新游戏状态"""
        if self.state != "playing":
            return

        # 处理玩家移动
        keys = pygame.key.get_pressed()
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        self.player.move(left, right)

        # 检测平台碰撞
        self.player.on_ground = False
        for platform in self.level.platforms:
            if self.player.rect.colliderect(platform.rect):
                # 从上方碰撞
                if self.player.dy > 0 and self.player.rect.bottom - self.player.dy <= platform.rect.top:
                    self.player.y = platform.rect.top - self.player.height
                    self.player.dy = 0
                    self.player.on_ground = True
                    self.player.rect.y = self.player.y
                # 从下方碰撞
                elif self.player.dy < 0 and self.player.rect.top - self.player.dy >= platform.rect.bottom:
                    self.player.y = platform.rect.bottom
                    self.player.dy = 0
                    self.player.rect.y = self.player.y
                # 从左侧碰撞
                elif self.player.dx > 0 and self.player.rect.right - self.player.dx <= platform.rect.left:
                    self.player.x = platform.rect.left - self.player.width
                    self.player.rect.x = self.player.x
                # 从右侧碰撞
                elif self.player.dx < 0 and self.player.rect.left - self.player.dx >= platform.rect.right:
                    self.player.x = platform.rect.right
                    self.player.rect.x = self.player.x

        # 检测掉落
        if self.player.y > WINDOW_HEIGHT:
            self.lives -= 1
            if self.lives <= 0:
                self.state = "game_over"
            else:
                self.player.reset(self.level.player_start[0], self.level.player_start[1])

        # 更新敌人
        for enemy in self.level.enemies:
            enemy.update()
            # 检测与敌人碰撞
            if self.player.rect.colliderect(enemy.rect):
                # 从上方踩敌人
                if self.player.dy > 0 and self.player.rect.bottom - self.player.dy <= enemy.rect.top:
                    self.level.enemies.remove(enemy)
                    self.score += 100
                    self.player.dy = JUMP_FORCE // 2
                else:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.state = "game_over"
                    else:
                        self.player.reset(self.level.player_start[0], self.level.player_start[1])

        # 检测金币收集
        for coin in self.level.coins:
            if not coin.collected and self.player.rect.colliderect(coin.rect):
                coin.collected = True
                self.score += 50

        # 检测到达目标
        if self.level.goal and self.player.rect.colliderect(self.level.goal.rect):
            if self.current_level >= self.max_level:
                self.state = "game_won"
            else:
                self.state = "level_complete"

    def draw_background(self):
        """绘制背景"""
        screen.fill(SKY_BLUE)

    def draw_hud(self):
        """绘制游戏界面信息"""
        # 分数
        score_text = font_small.render(f"分数: {self.score}", True, WHITE)
        screen.blit(score_text, (20, 20))

        # 生命
        lives_text = font_small.render(f"生命: {self.lives}", True, WHITE)
        screen.blit(lives_text, (WINDOW_WIDTH - 150, 20))

        # 关卡
        level_text = font_small.render(f"关卡: {self.current_level}/{self.max_level}", True, WHITE)
        screen.blit(level_text, (WINDOW_WIDTH // 2 - 70, 20))

    def draw_start_screen(self):
        """绘制开始界面"""
        self.draw_background()
        title = font_large.render("2D平台闯关", True, WHITE)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 150))
        screen.blit(title, title_rect)

        instructions = [
            "← → 或 A D: 移动",
            "空格: 跳跃/开始",
            "ESC 或 P: 暂停",
            "",
            "目标: 收集金币，避开敌人，到达终点！",
            "",
            "按 空格 开始游戏"
        ]

        y = 250
        for line in instructions:
            text = font_small.render(line, True, WHITE)
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, y))
            screen.blit(text, text_rect)
            y += 40

    def draw_level_complete_screen(self):
        """绘制关卡完成界面"""
        self.draw_background()
        complete_text = font_large.render("关卡完成!", True, GREEN)
        complete_rect = complete_text.get_rect(center=(WINDOW_WIDTH // 2, 200))
        screen.blit(complete_text, complete_rect)

        score_text = font_medium.render(f"当前分数: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, 280))
        screen.blit(score_text, score_rect)

        next_text = font_small.render("按 空格 进入下一关", True, YELLOW)
        next_rect = next_text.get_rect(center=(WINDOW_WIDTH // 2, 350))
        screen.blit(next_text, next_rect)

    def draw_game_over_screen(self):
        """绘制游戏结束界面"""
        self.draw_background()
        game_over_text = font_large.render("游戏结束", True, RED)
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, 200))
        screen.blit(game_over_text, game_over_rect)

        score_text = font_medium.render(f"最终分数: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, 280))
        screen.blit(score_text, score_rect)

        restart_text = font_small.render("按 空格 或 R 重新开始", True, YELLOW)
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, 350))
        screen.blit(restart_text, restart_rect)

    def draw_win_screen(self):
        """绘制胜利界面"""
        self.draw_background()
        win_text = font_large.render("恭喜通关!", True, GREEN)
        win_rect = win_text.get_rect(center=(WINDOW_WIDTH // 2, 200))
        screen.blit(win_text, win_rect)

        score_text = font_medium.render(f"最终分数: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, 280))
        screen.blit(score_text, score_rect)

        restart_text = font_small.render("按 空格 重新开始", True, YELLOW)
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, 350))
        screen.blit(restart_text, restart_rect)

    def draw(self):
        """绘制游戏画面"""
        if self.state == "start":
            self.draw_start_screen()
        elif self.state == "level_complete":
            self.draw_level_complete_screen()
        elif self.state == "game_over":
            self.draw_game_over_screen()
        elif self.state == "game_won":
            self.draw_win_screen()
        else:
            self.draw_background()
            # 绘制平台
            for platform in self.level.platforms:
                platform.draw()
            # 绘制金币
            for coin in self.level.coins:
                coin.draw()
            # 绘制敌人
            for enemy in self.level.enemies:
                enemy.draw()
            # 绘制目标
            if self.level.goal:
                self.level.goal.draw()
            # 绘制玩家
            self.player.draw()
            # 绘制HUD
            self.draw_hud()

            if self.state == "paused":
                pause_text = font_large.render("暂停", True, YELLOW)
                text_rect = pause_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
                pygame.draw.rect(screen, BLACK, text_rect.inflate(20, 20))
                screen.blit(pause_text, text_rect)

        pygame.display.flip()

    def next_level(self):
        """进入下一关"""
        self.current_level += 1
        self.level = Level(self.current_level)
        self.player.reset(self.level.player_start[0], self.level.player_start[1])
        self.state = "playing"

    def reset_game(self):
        """重置游戏"""
        self.current_level = 1
        self.level = Level(1)
        self.player.reset(self.level.player_start[0], self.level.player_start[1])
        self.score = 0
        self.lives = 3
        self.state = "playing"

    def run(self):
        """游戏主循环"""
        running = True

        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            clock.tick(FPS)

        pygame.quit()
        sys.exit()

# 主程序入口
if __name__ == "__main__":
    game = Game()
    game.run()
