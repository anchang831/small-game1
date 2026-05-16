"""
打砖块游戏 - Breakout Game
日期: 2026-05-16
作者: AI Game Developer
"""

import pygame
import sys
import random
import math

# 初始化 Pygame
pygame.init()

# 游戏窗口设置
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
PINK = (255, 192, 203)

# 球的颜色
BALL_COLORS = [RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE, CYAN, PINK]

# 砖块颜色 (按行)
BRICK_COLORS = [
    RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, CYAN, PINK
]

# 游戏设置
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 15
BALL_RADIUS = 8
BRICK_ROWS = 8
BRICK_COLS = 10
BRICK_WIDTH = 70
BRICK_HEIGHT = 25
BRICK_PADDING = 5
BRICK_TOP_OFFSET = 60
BRICK_LEFT_OFFSET = 35

# 速度设置
BALL_SPEED = 6
PADDLE_SPEED = 8
BALL_SPEED_INCREASE = 0.5

# 创建窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("打砖块游戏 - Breakout Game")
clock = pygame.time.Clock()

# 加载字体
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 36)

class Paddle:
    """挡板类"""
    def __init__(self):
        self.width = PADDLE_WIDTH
        self.height = PADDLE_HEIGHT
        self.x = (WINDOW_WIDTH - self.width) // 2
        self.y = WINDOW_HEIGHT - 40
        self.speed = PADDLE_SPEED
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.color = CYAN

    def move(self, direction):
        """移动挡板"""
        self.x += direction * self.speed
        # 边界检测
        if self.x < 0:
            self.x = 0
        if self.x > WINDOW_WIDTH - self.width:
            self.x = WINDOW_WIDTH - self.width
        self.rect.x = self.x

    def draw(self):
        """绘制挡板"""
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
        # 添加高光效果
        highlight_rect = pygame.Rect(self.x, self.y, self.width, 5)
        pygame.draw.rect(screen, WHITE, highlight_rect, border_radius=5)

    def reset(self):
        """重置挡板位置"""
        self.x = (WINDOW_WIDTH - self.width) // 2
        self.y = WINDOW_HEIGHT - 40
        self.rect.x = self.x
        self.rect.y = self.y

class Ball:
    """球类"""
    def __init__(self):
        self.radius = BALL_RADIUS
        self.reset()

    def reset(self):
        """重置球的位置和速度"""
        self.x = WINDOW_WIDTH // 2
        self.y = WINDOW_HEIGHT - 100
        # 随机初始角度 (60-120度)
        angle = random.uniform(60, 120) * math.pi / 180
        speed = BALL_SPEED
        self.dx = speed * math.cos(angle) * random.choice([-1, 1])
        self.dy = -speed * math.sin(angle)
        self.color = random.choice(BALL_COLORS)

    def move(self):
        """移动球"""
        self.x += self.dx
        self.y += self.dy

        # 左右边界碰撞
        if self.x - self.radius <= 0 or self.x + self.radius >= WINDOW_WIDTH:
            self.dx = -self.dx
            self.x = max(self.radius, min(self.x, WINDOW_WIDTH - self.radius))

        # 顶部边界碰撞
        if self.y - self.radius <= 0:
            self.dy = -self.dy
            self.y = self.radius

    def draw(self):
        """绘制球"""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        # 添加高光效果
        highlight_pos = (int(self.x - 2), int(self.y - 2))
        pygame.draw.circle(screen, WHITE, highlight_pos, max(1, self.radius // 3))

    def check_paddle_collision(self, paddle):
        """检测与挡板的碰撞"""
        if pygame.Rect.colliderect(
            pygame.Rect(self.x - self.radius, self.y - self.radius,
                       self.radius * 2, self.radius * 2),
            paddle.rect
        ):
            # 计算碰撞位置相对于挡板中心的偏移
            paddle_center = paddle.x + paddle.width // 2
            offset = (self.x - paddle_center) / (paddle.width // 2)

            # 根据偏移调整反弹角度
            angle = offset * (math.pi / 3)  # 最大偏转60度
            speed = math.sqrt(self.dx ** 2 + self.dy ** 2)

            self.dx = speed * math.sin(angle)
            self.dy = -speed * math.cos(angle)
            self.color = random.choice(BALL_COLORS)

            # 确保球在挡板上方
            self.y = paddle.rect.top - self.radius
            return True
        return False

    def check_bottom_collision(self):
        """检测是否触底"""
        return self.y + self.radius >= WINDOW_HEIGHT

class Brick:
    """砖块类"""
    def __init__(self, x, y, color, points):
        self.rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
        self.color = color
        self.points = points
        self.alive = True

    def draw(self):
        """绘制砖块"""
        if self.alive:
            pygame.draw.rect(screen, self.color, self.rect, border_radius=3)
            # 添加高光
            highlight = pygame.Rect(self.rect.x, self.rect.y, BRICK_WIDTH, 8)
            highlight_color = (
                min(255, self.color[0] + 50),
                min(255, self.color[1] + 50),
                min(255, self.color[2] + 50)
            )
            pygame.draw.rect(screen, highlight_color, highlight, border_radius=3)

    def check_ball_collision(self, ball):
        """检测与球的碰撞"""
        if self.alive and pygame.Rect.colliderect(
            pygame.Rect(ball.x - ball.radius, ball.y - ball.radius,
                       ball.radius * 2, ball.radius * 2),
            self.rect
        ):
            self.alive = False
            return True
        return False

class BrickManager:
    """砖块管理器"""
    def __init__(self):
        self.bricks = []
        self.create_bricks()

    def create_bricks(self):
        """创建砖块矩阵"""
        self.bricks = []
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                x = BRICK_LEFT_OFFSET + col * (BRICK_WIDTH + BRICK_PADDING)
                y = BRICK_TOP_OFFSET + row * (BRICK_HEIGHT + BRICK_PADDING)
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                # 每行分数不同，顶部分数更高
                points = (BRICK_ROWS - row) * 10
                brick = Brick(x, y, color, points)
                self.bricks.append(brick)

    def check_collision(self, ball):
        """检测球与所有砖块的碰撞"""
        for brick in self.bricks:
            if brick.check_ball_collision(ball):
                # 反转球的垂直速度
                ball.dy = -ball.dy
                ball.color = random.choice(BALL_COLORS)
                return brick.points
        return 0

    def draw(self):
        """绘制所有砖块"""
        for brick in self.bricks:
            brick.draw()

    def get_remaining(self):
        """获取剩余砖块数量"""
        return sum(1 for brick in self.bricks if brick.alive)

    def reset(self):
        """重置所有砖块"""
        self.create_bricks()

class Game:
    """游戏主类"""
    def __init__(self):
        self.paddle = Paddle()
        self.ball = Ball()
        self.brick_manager = BrickManager()
        self.score = 0
        self.lives = 3
        self.level = 1
        self.game_over = False
        self.game_won = False
        self.paused = False
        self.state = "start"  # start, playing, paused, game_over, game_won

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
                    elif self.state == "game_over" or self.state == "game_won":
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

        # 处理挡板移动
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.paddle.move(-1)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.paddle.move(1)

        # 移动球
        self.ball.move()

        # 检测与挡板的碰撞
        self.ball.check_paddle_collision(self.paddle)

        # 检测与砖块的碰撞
        points = self.brick_manager.check_collision(self.ball)
        self.score += points

        # 检测球是否触底
        if self.ball.check_bottom_collision():
            self.lives -= 1
            if self.lives <= 0:
                self.state = "game_over"
                self.game_over = True
            else:
                self.ball.reset()

        # 检测是否胜利
        if self.brick_manager.get_remaining() == 0:
            self.level += 1
            if self.level > 3:  # 3个难度等级
                self.state = "game_won"
                self.game_won = True
            else:
                # 进入下一关
                self.ball.reset()
                self.ball.dx *= (1 + BALL_SPEED_INCREASE)
                self.ball.dy *= (1 + BALL_SPEED_INCREASE)
                self.brick_manager.reset()

    def draw_background(self):
        """绘制背景"""
        screen.fill(BLACK)
        # 绘制网格线
        for i in range(0, WINDOW_WIDTH, 50):
            pygame.draw.line(screen, (20, 20, 20), (i, 0), (i, WINDOW_HEIGHT))
        for i in range(0, WINDOW_HEIGHT, 50):
            pygame.draw.line(screen, (20, 20, 20), (0, i), (WINDOW_WIDTH, i))

    def draw_hud(self):
        """绘制游戏界面信息"""
        # 分数
        score_text = font_small.render(f"分数: {self.score}", True, WHITE)
        screen.blit(score_text, (20, 20))

        # 生命
        lives_text = font_small.render(f"生命: {self.lives}", True, WHITE)
        screen.blit(lives_text, (WINDOW_WIDTH - 150, 20))

        # 关卡
        level_text = font_small.render(f"关卡: {self.level}", True, WHITE)
        screen.blit(level_text, (WINDOW_WIDTH // 2 - 50, 20))

        # 提示信息
        if self.state == "paused":
            pause_text = font_large.render("暂停", True, YELLOW)
            text_rect = pause_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            pygame.draw.rect(screen, BLACK, text_rect.inflate(20, 20))
            screen.blit(pause_text, text_rect)

    def draw_start_screen(self):
        """绘制开始界面"""
        self.draw_background()
        title = font_large.render("打砖块游戏", True, CYAN)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 150))
        screen.blit(title, title_rect)

        instructions = [
            "← → 或 A D: 移动挡板",
            "空格: 开始游戏",
            "ESC 或 P: 暂停",
            "",
            f"目标: 消除所有砖块",
            f"生命: {self.lives}",
            "",
            "按 空格 开始游戏"
        ]

        y = 250
        for line in instructions:
            text = font_small.render(line, True, WHITE)
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, y))
            screen.blit(text, text_rect)
            y += 40

    def draw_game_over_screen(self):
        """绘制游戏结束界面"""
        self.draw_background()
        self.brick_manager.draw()
        self.paddle.draw()

        game_over_text = font_large.render("游戏结束", True, RED)
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, 200))
        screen.blit(game_over_text, game_over_rect)

        score_text = font_medium.render(f"最终分数: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, 280))
        screen.blit(score_text, score_rect)

        restart_text = font_small.render("按 空格 重新开始", True, YELLOW)
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
        elif self.state == "game_over":
            self.draw_game_over_screen()
        elif self.state == "game_won":
            self.draw_win_screen()
        else:
            self.draw_background()
            self.brick_manager.draw()
            self.paddle.draw()
            self.ball.draw()
            self.draw_hud()

            if self.state == "paused":
                pause_text = font_large.render("暂停", True, YELLOW)
                text_rect = pause_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
                pygame.draw.rect(screen, BLACK, text_rect.inflate(20, 20))
                screen.blit(pause_text, text_rect)

        pygame.display.flip()

    def reset_game(self):
        """重置游戏"""
        self.paddle.reset()
        self.ball.reset()
        self.brick_manager.reset()
        self.score = 0
        self.lives = 3
        self.level = 1
        self.game_over = False
        self.game_won = False
        self.paused = False
        self.state = "playing"

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

# 主程序入口
if __name__ == "__main__":
    game = Game()
    game.run()
