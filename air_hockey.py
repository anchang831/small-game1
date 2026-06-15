"""
Air Hockey 冰球大战
==================
一款双人对战的冰球游戏。
- 玩家1 (左侧): W/A/S/D 移动球拍
- 玩家2 (右侧): 方向键 ↑/↓/←/→ 移动球拍
- 先得7分者获胜！
"""

import pygame
import math
import random

# 初始化 Pygame
pygame.init()

# 常量定义
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600
FPS = 60

# 颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (30, 100, 200)
RED = (200, 50, 50)
ICE_BLUE = (200, 220, 240)
DARK_BLUE = (20, 40, 80)
GOAL_COLOR = (50, 50, 50)
YELLOW = (255, 255, 100)
GREEN = (50, 200, 50)
GRAY = (128, 128, 128)

# 游戏参数
PADDLE_RADIUS = 30
PUCK_RADIUS = 15
PADDLE_SPEED = 6
PUCK_MAX_SPEED = 12
FRICTION = 0.985
GOAL_WIDTH = 30
GOAL_HEIGHT = 160
WIN_SCORE = 7
RINK_MARGIN = 40  # 冰场边距


class Paddle:
    """球拍类"""

    def __init__(self, x, y, color, controls):
        self.x = x
        self.y = y
        self.radius = PADDLE_RADIUS
        self.color = color
        self.speed = PADDLE_SPEED
        self.vx = 0
        self.vy = 0
        self.controls = controls  # 控制键位字典
        self.score = 0
        self.rect = pygame.Rect(
            self.x - self.radius, self.y - self.radius,
            self.radius * 2, self.radius * 2
        )

    def handle_input(self, keys):
        """处理键盘输入"""
        self.vx, self.vy = 0, 0
        if keys[self.controls['up']]:
            self.vy = -self.speed
        if keys[self.controls['down']]:
            self.vy = self.speed
        if keys[self.controls['left']]:
            self.vx = -self.speed
        if keys[self.controls['right']]:
            self.vx = self.speed

        # 归一化对角线移动
        if self.vx != 0 and self.vy != 0:
            norm = math.sqrt(self.vx**2 + self.vy**2)
            self.vx = self.vx / norm * self.speed
            self.vy = self.vy / norm * self.speed

    def update(self, rink_rect, goal_rect_left, goal_rect_right):
        """更新球拍位置，限制在冰场内，不能进入球门区域"""
        new_x = self.x + self.vx
        new_y = self.y + self.vy

        # 限制在冰场边界内
        new_x = max(rink_rect.left + self.radius, min(rink_rect.right - self.radius, new_x))
        new_y = max(rink_rect.top + self.radius, min(rink_rect.bottom - self.radius, new_y))

        # 限制球拍不能进入球门区域
        # 左侧球门：禁止进入
        if goal_rect_left.collidepoint(new_x, new_y):
            if new_x < goal_rect_left.centerx:
                new_x = goal_rect_left.right + self.radius
        # 右侧球门
        if goal_rect_right.collidepoint(new_x, new_y):
            if new_x > goal_rect_right.centerx:
                new_x = goal_rect_right.left - self.radius

        self.x, self.y = new_x, new_y
        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        """绘制球拍"""
        # 阴影
        pygame.draw.circle(surface, (0, 0, 0, 60),
                           (int(self.x) + 3, int(self.y) + 3), self.radius)
        # 主体
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        # 高光
        highlight = (min(self.color[0] + 60, 255),
                     min(self.color[1] + 60, 255),
                     min(self.color[2] + 60, 255))
        pygame.draw.circle(surface, highlight,
                           (int(self.x - 8), int(self.y - 8)), self.radius // 3)

    def reset_position(self, x, y):
        """重置位置"""
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.rect.center = (self.x, self.y)


class Puck:
    """冰球类"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = PUCK_RADIUS
        self.vx = random.choice([-4, 4]) * random.uniform(0.8, 1.2)
        self.vy = random.uniform(-2, 2)
        self.color = (255, 100, 50)
        self.rect = pygame.Rect(
            self.x - self.radius, self.y - self.radius,
            self.radius * 2, self.radius * 2
        )

    def update(self, rink_rect, goal_rect_left, goal_rect_right):
        """更新冰球位置"""
        # 应用摩擦力
        self.vx *= FRICTION
        self.vy *= FRICTION

        # 限制最大速度
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > PUCK_MAX_SPEED:
            self.vx = self.vx / speed * PUCK_MAX_SPEED
            self.vy = self.vy / speed * PUCK_MAX_SPEED

        # 如果速度太小，完全停止
        if speed < 0.3:
            self.vx = 0
            self.vy = 0

        new_x = self.x + self.vx
        new_y = self.y + self.vy

        # 上下边界反弹
        if new_y - self.radius < rink_rect.top:
            new_y = rink_rect.top + self.radius
            self.vy = -self.vy
        elif new_y + self.radius > rink_rect.bottom:
            new_y = rink_rect.bottom - self.radius
            self.vy = -self.vy

        # 冰球在球门区域，允许进入
        # 左侧球门检查
        if goal_rect_left.collidepoint(new_x, new_y):
            # 检查是否进门（球完全进入球门内）
            if new_x <= goal_rect_left.left + self.radius:
                return 'right_score'  # 球进左门，右方得分
        # 右侧球门检查
        elif goal_rect_right.collidepoint(new_x, new_y):
            if new_x >= goal_rect_right.right - self.radius:
                return 'left_score'  # 球进右门，左方得分
        else:
            # 左右边界反弹（非球门区域）
            # 左边界
            if new_x - self.radius < rink_rect.left:
                if not (rink_rect.centery - GOAL_HEIGHT // 2 <= new_y <=
                        rink_rect.centery + GOAL_HEIGHT // 2):
                    new_x = rink_rect.left + self.radius
                    self.vx = -self.vx
            # 右边界
            elif new_x + self.radius > rink_rect.right:
                if not (rink_rect.centery - GOAL_HEIGHT // 2 <= new_y <=
                        rink_rect.centery + GOAL_HEIGHT // 2):
                    new_x = rink_rect.right - self.radius
                    self.vx = -self.vx

        self.x, self.y = new_x, new_y
        self.rect.center = (self.x, self.y)
        return None

    def draw(self, surface):
        """绘制冰球"""
        # 阴影
        pygame.draw.circle(surface, (0, 0, 0, 60),
                           (int(self.x) + 3, int(self.y) + 3), self.radius)
        # 主体
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        # 高光
        pygame.draw.circle(surface, (255, 180, 100),
                           (int(self.x - 4), int(self.y - 4)), self.radius // 2)
        # 冰球上的条纹装饰
        pygame.draw.line(surface, (200, 80, 30),
                         (int(self.x - 8), int(self.y)),
                         (int(self.x + 8), int(self.y)), 3)

    def reset(self, x, y, direction=1):
        """重置冰球到中心"""
        self.x = x
        self.y = y
        self.vx = direction * random.uniform(3, 5)
        self.vy = random.uniform(-2, 2)
        self.rect.center = (self.x, self.y)


def check_paddle_puck_collision(paddle, puck):
    """检测球拍与冰球的碰撞并处理"""
    dx = puck.x - paddle.x
    dy = puck.y - paddle.y
    distance = math.sqrt(dx**2 + dy**2)
    min_dist = paddle.radius + puck.radius

    if distance < min_dist and distance > 0:
        # 计算碰撞法线方向
        nx = dx / distance
        ny = dy / distance

        # 将冰球移出球拍（防止卡住）
        overlap = min_dist - distance
        puck.x += nx * overlap
        puck.y += ny * overlap

        # 球拍的速度传递
        relative_vx = puck.vx - paddle.vx
        relative_vy = puck.vy - paddle.vy

        # 计算相对速度在法线方向的分量
        relative_speed = relative_vx * nx + relative_vy * ny

        # 只在球拍和冰球相互靠近时处理碰撞
        if relative_speed < 0:
            # 弹性系数
            restitution = 1.2
            impulse = -(1 + restitution) * relative_speed

            # 更新冰球速度
            puck.vx += impulse * nx
            puck.vy += impulse * ny

            # 加入球拍速度影响
            puck.vx += paddle.vx * 0.3
            puck.vy += paddle.vy * 0.3

            # 确保冰球不会粘在球拍上
            return True
    return False


def draw_rink(surface, rink_rect, goal_rect_left, goal_rect_right):
    """绘制冰场"""
    # 冰面背景
    pygame.draw.rect(surface, ICE_BLUE, rink_rect, border_radius=20)

    # 冰面纹理线（水平）
    for y in range(rink_rect.top + 30, rink_rect.bottom, 40):
        alpha = 30
        line_color = (180, 200, 230)
        pygame.draw.line(surface, line_color,
                         (rink_rect.left + 20, y),
                         (rink_rect.right - 20, y), 1)

    # 冰场边框
    pygame.draw.rect(surface, DARK_BLUE, rink_rect, 4, border_radius=20)

    # 中线
    center_x = rink_rect.centerx
    pygame.draw.line(surface, DARK_BLUE,
                     (center_x, rink_rect.top + 10),
                     (center_x, rink_rect.bottom - 10), 3)

    # 中圈
    pygame.draw.circle(surface, DARK_BLUE,
                       (rink_rect.centerx, rink_rect.centery),
                       60, 3)

    # 中圈开球点
    pygame.draw.circle(surface, DARK_BLUE,
                       (rink_rect.centerx, rink_rect.centery), 5)

    # 左球门
    pygame.draw.rect(surface, GOAL_COLOR, goal_rect_left, border_radius=8)
    pygame.draw.rect(surface, DARK_BLUE, goal_rect_left, 3, border_radius=8)
    # 球门网效果
    for y in range(goal_rect_left.top + 10, goal_rect_left.bottom - 10, 12):
        pygame.draw.line(surface, (80, 80, 80),
                         (goal_rect_left.left + 5, y),
                         (goal_rect_left.right - 5, y), 1)
    for x in range(goal_rect_left.left + 10, goal_rect_left.right - 10, 12):
        pygame.draw.line(surface, (80, 80, 80),
                         (x, goal_rect_left.top + 5),
                         (x, goal_rect_left.bottom - 5), 1)

    # 右球门
    pygame.draw.rect(surface, GOAL_COLOR, goal_rect_right, border_radius=8)
    pygame.draw.rect(surface, DARK_BLUE, goal_rect_right, 3, border_radius=8)
    for y in range(goal_rect_right.top + 10, goal_rect_right.bottom - 10, 12):
        pygame.draw.line(surface, (80, 80, 80),
                         (goal_rect_right.left + 5, y),
                         (goal_rect_right.right - 5, y), 1)
    for x in range(goal_rect_right.left + 10, goal_rect_right.right - 10, 12):
        pygame.draw.line(surface, (80, 80, 80),
                         (x, goal_rect_right.top + 5),
                         (x, goal_rect_right.bottom - 5), 1)


def draw_score(surface, font, left_score, right_score):
    """显示比分"""
    score_text = font.render(f"{left_score}  -  {right_score}", True, WHITE)
    score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, 20))
    surface.blit(score_text, score_rect)


def show_winner(surface, font, winner_text):
    """显示获胜者"""
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    overlay.set_alpha(180)
    overlay.fill(BLACK)
    surface.blit(overlay, (0, 0))

    # 获胜文字
    win_font = pygame.font.SysFont("simhei", 72, bold=True)
    win_surf = win_font.render(winner_text, True, YELLOW)
    win_rect = win_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40))
    surface.blit(win_surf, win_rect)

    # 提示重新开始
    tip_font = pygame.font.SysFont("simhei", 30)
    tip_surf = tip_font.render("按 R 键重新开始 | 按 ESC 退出", True, WHITE)
    tip_rect = tip_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40))
    surface.blit(tip_surf, tip_rect)


def show_start_screen(surface, font):
    """显示开始画面"""
    surface.fill(BLACK)

    title_font = pygame.font.SysFont("simhei", 64, bold=True)
    title = title_font.render("冰球大战", True, ICE_BLUE)
    title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100))
    surface.blit(title, title_rect)

    sub_font = pygame.font.SysFont("simhei", 28)
    lines = [
        "玩家1 (蓝色): W/A/S/D  移动",
        "玩家2 (红色): 方向键  移动",
        "",
        "先得 7 分者获胜！",
        "",
        "按 空格键 开始游戏"
    ]

    y_start = WINDOW_HEIGHT // 2 - 20
    for i, line in enumerate(lines):
        if line == "":
            continue
        text = sub_font.render(line, True, WHITE)
        rect = text.get_rect(center=(WINDOW_WIDTH // 2, y_start + i * 38))
        surface.blit(text, rect)

    # 画两个球拍装饰
    pygame.draw.circle(surface, BLUE,
                       (WINDOW_WIDTH // 2 - 80, WINDOW_HEIGHT // 2 + 180), 35)
    pygame.draw.circle(surface, RED,
                       (WINDOW_WIDTH // 2 + 80, WINDOW_HEIGHT // 2 + 180), 35)
    pygame.draw.circle(surface, (255, 100, 50),
                       (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 180), 15)

    pygame.display.flip()


def main():
    """主函数"""
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("冰球大战 - Air Hockey")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("simhei", 48)
    small_font = pygame.font.SysFont("simhei", 24)

    # 冰场区域
    rink_rect = pygame.Rect(
        RINK_MARGIN + GOAL_WIDTH,
        RINK_MARGIN,
        WINDOW_WIDTH - 2 * (RINK_MARGIN + GOAL_WIDTH),
        WINDOW_HEIGHT - 2 * RINK_MARGIN
    )

    # 球门区域
    goal_rect_left = pygame.Rect(
        RINK_MARGIN - 5,
        rink_rect.centery - GOAL_HEIGHT // 2,
        GOAL_WIDTH + 5,
        GOAL_HEIGHT
    )
    goal_rect_right = pygame.Rect(
        WINDOW_WIDTH - RINK_MARGIN - GOAL_WIDTH,
        rink_rect.centery - GOAL_HEIGHT // 2,
        GOAL_WIDTH + 5,
        GOAL_HEIGHT
    )

    # 创建球拍
    paddle1 = Paddle(
        rink_rect.left + 80, rink_rect.centery,
        BLUE,
        {'up': pygame.K_w, 'down': pygame.K_s,
         'left': pygame.K_a, 'right': pygame.K_d}
    )
    paddle2 = Paddle(
        rink_rect.right - 80, rink_rect.centery,
        RED,
        {'up': pygame.K_UP, 'down': pygame.K_DOWN,
         'left': pygame.K_LEFT, 'right': pygame.K_RIGHT}
    )

    # 创建冰球
    puck = Puck(rink_rect.centerx, rink_rect.centery)

    # 游戏状态
    START = 0
    PLAYING = 1
    GOAL_SCORED = 2
    GAME_OVER = 3
    state = START

    goal_timer = 0
    last_scorer = 1  # 1=左方(player1), -1=右方(player2)
    goal_message = ""

    running = True

    while running:
        dt = clock.tick(FPS)
        keys = pygame.key.get_pressed()

        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE and state == START:
                    state = PLAYING
                if event.key == pygame.K_r and state == GAME_OVER:
                    # 重新开始
                    paddle1.score = 0
                    paddle2.score = 0
                    paddle1.reset_position(rink_rect.left + 80, rink_rect.centery)
                    paddle2.reset_position(rink_rect.right - 80, rink_rect.centery)
                    puck.reset(rink_rect.centerx, rink_rect.centery, 1)
                    state = PLAYING

        if state == START:
            show_start_screen(screen, font)
            continue

        if state == PLAYING or state == GOAL_SCORED:
            # 处理输入
            paddle1.handle_input(keys)
            paddle2.handle_input(keys)

            # 更新球拍
            paddle1.update(rink_rect, goal_rect_left, goal_rect_right)
            paddle2.update(rink_rect, goal_rect_left, goal_rect_right)

            if state == PLAYING:
                # 更新冰球
                result = puck.update(rink_rect, goal_rect_left, goal_rect_right)

                # 碰撞检测
                check_paddle_puck_collision(paddle1, puck)
                check_paddle_puck_collision(paddle2, puck)

                # 检查进球
                if result == 'left_score':
                    paddle2.score += 1
                    last_scorer = 1
                    goal_message = "🔵 蓝方进球！" if paddle1.score < WIN_SCORE and paddle2.score < WIN_SCORE else ""
                    state = GOAL_SCORED
                    goal_timer = 90  # 约1.5秒
                elif result == 'right_score':
                    paddle1.score += 1
                    last_scorer = -1
                    goal_message = "🔴 红方进球！" if paddle1.score < WIN_SCORE and paddle2.score < WIN_SCORE else ""
                    state = GOAL_SCORED
                    goal_timer = 90

                # 检查是否获胜
                if paddle1.score >= WIN_SCORE or paddle2.score >= WIN_SCORE:
                    state = GAME_OVER

            elif state == GOAL_SCORED:
                goal_timer -= 1
                if goal_timer <= 0:
                    # 重置冰球位置
                    puck.reset(rink_rect.centerx, rink_rect.centery, -last_scorer)
                    paddle1.reset_position(rink_rect.left + 80, rink_rect.centery)
                    paddle2.reset_position(rink_rect.right - 80, rink_rect.centery)
                    state = PLAYING

        # ---- 绘制 ----
        screen.fill(BLACK)

        # 绘制冰场
        draw_rink(screen, rink_rect, goal_rect_left, goal_rect_right)

        # 绘制球拍
        paddle1.draw(screen)
        paddle2.draw(screen)

        # 绘制冰球
        if state != START and state != GOAL_SCORED:
            puck.draw(screen)
        elif state == GOAL_SCORED:
            # 进球后也显示冰球
            puck.draw(screen)

        # 绘制比分
        draw_score(screen, font, paddle1.score, paddle2.score)

        # 显示进球消息
        if state == GOAL_SCORED and goal_message:
            msg_font = pygame.font.SysFont("simhei", 36)
            msg_surf = msg_font.render(goal_message, True, YELLOW)
            msg_rect = msg_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 80))
            screen.blit(msg_surf, msg_rect)

        # 获胜画面
        if state == GAME_OVER:
            if paddle1.score >= WIN_SCORE:
                show_winner(screen, font, "🔵 蓝方获胜！")
            else:
                show_winner(screen, font, "🔴 红方获胜！")

        # 提示信息
        if state == PLAYING:
            tip = small_font.render("ESC退出", True, GRAY)
            screen.blit(tip, (10, WINDOW_HEIGHT - 30))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()