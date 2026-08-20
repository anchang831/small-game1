"""
2D 足球对战游戏 (Soccer)
==========================
双人足球对战：玩家1 (WASD+空格键) vs 玩家2 (方向键+回车键)
先得5分者获胜！

操作说明:
  玩家1: W/A/S/D 移动, 空格键 踢球
  玩家2: ↑/↓/←/→ 移动, 回车键 踢球
  按 R 键重新开始, ESC 退出
"""

import pygame
import math
import random

# 初始化 Pygame
pygame.init()

# 游戏常量
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
FPS = 60

# 颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
LIGHT_GREEN = (50, 180, 50)
YELLOW = (255, 255, 0)
RED = (255, 50, 50)
BLUE = (50, 50, 255)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)
BROWN = (139, 69, 19)

# 物理常量
FRICTION = 0.98
BALL_FRICTION = 0.99
KICK_FORCE = 12
MAX_SPEED = 8
BALL_MAX_SPEED = 15
PLAYER_RADIUS = 18
BALL_RADIUS = 10
GOAL_WIDTH = 20
GOAL_HEIGHT = 160

# 屏幕设置
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("2D 足球对战 - 先得5分获胜!")
clock = pygame.time.Clock()
font = pygame.font.SysFont("simhei", 36, bold=True)
small_font = pygame.font.SysFont("simhei", 24)
big_font = pygame.font.SysFont("simhei", 60, bold=True)

# 游戏状态
class GameState:
    MENU = 0
    PLAYING = 1
    GOAL = 2
    WINNER = 3

class Player:
    """玩家类"""
    def __init__(self, x, y, color, keys_config):
        self.x = x
        self.y = y
        self.color = color
        self.vx = 0
        self.vy = 0
        self.radius = PLAYER_RADIUS
        self.score = 0
        self.keys = keys_config  # 按键配置
        self.kick_cooldown = 0   # 踢球冷却
        self.direction = 0       # 朝向角度

    def handle_input(self, keys):
        """处理玩家输入"""
        # 移动
        dx, dy = 0, 0
        if keys[self.keys['up']]:
            dy = -1
        if keys[self.keys['down']]:
            dy = 1
        if keys[self.keys['left']]:
            dx = -1
        if keys[self.keys['right']]:
            dx = 1

        # 归一化对角线移动
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        # 加速
        self.vx += dx * 0.8
        self.vy += dy * 0.8

        # 限制最大速度
        speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        if speed > MAX_SPEED:
            self.vx = self.vx / speed * MAX_SPEED
            self.vy = self.vy / speed * MAX_SPEED

        # 摩擦力
        self.vx *= FRICTION
        self.vy *= FRICTION

        # 如果速度很小就归零
        if abs(self.vx) < 0.1:
            self.vx = 0
        if abs(self.vy) < 0.1:
            self.vy = 0

        # 更新位置
        self.x += self.vx
        self.y += self.vy

        # 更新朝向
        if dx != 0 or dy != 0:
            self.direction = math.atan2(dy, dx)

        # 踢球冷却
        if self.kick_cooldown > 0:
            self.kick_cooldown -= 1

        # 踢球
        kick = keys[self.keys['kick']]
        return kick and self.kick_cooldown == 0

    def kick(self, kick_strength=1.0):
        """踢球动作"""
        self.kick_cooldown = 15
        return kick_strength

    def reset_position(self, side):
        """重置位置到球场一侧"""
        if side == 'left':
            self.x = SCREEN_WIDTH * 0.25
        else:
            self.x = SCREEN_WIDTH * 0.75
        self.y = SCREEN_HEIGHT / 2
        self.vx = 0
        self.vy = 0

    def draw(self, surface):
        """绘制玩家"""
        # 身体
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        # 轮廓
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 2)

        # 绘制朝向指示线
        end_x = self.x + math.cos(self.direction) * self.radius * 1.5
        end_y = self.y + math.sin(self.direction) * self.radius * 1.5
        pygame.draw.line(surface, WHITE, (self.x, self.y), (end_x, end_y), 3)

        # 球衣号码
        num_text = font.render(
            str(self.score) if hasattr(self, 'score') else "0",
            True, WHITE
        )
        # 不显示号码在球衣上，改用分数显示在别处

    def get_rect(self):
        return pygame.Rect(
            self.x - self.radius, self.y - self.radius,
            self.radius * 2, self.radius * 2
        )


class Ball:
    """足球类"""
    def __init__(self):
        self.reset()

    def reset(self):
        """重置球到中场"""
        self.x = SCREEN_WIDTH / 2
        self.y = SCREEN_HEIGHT / 2
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.radius = BALL_RADIUS

    def update(self):
        """更新球的位置"""
        self.x += self.vx
        self.y += self.vy

        # 摩擦力
        self.vx *= BALL_FRICTION
        self.vy *= BALL_FRICTION

        # 限制最大速度
        speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        if speed > BALL_MAX_SPEED:
            self.vx = self.vx / speed * BALL_MAX_SPEED
            self.vy = self.vy / speed * BALL_MAX_SPEED

        # 如果速度很小就归零
        if abs(self.vx) < 0.05:
            self.vx = 0
        if abs(self.vy) < 0.05:
            self.vy = 0

        # 上下边界碰撞
        if self.y - self.radius < 0:
            self.y = self.radius
            self.vy = -self.vy
        elif self.y + self.radius > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.radius
            self.vy = -self.vy

        # 左右边界碰撞（球门区域特殊处理）
        # 左球门
        if self.x - self.radius < 0:
            if (SCREEN_HEIGHT - GOAL_HEIGHT) / 2 < self.y < (SCREEN_HEIGHT + GOAL_HEIGHT) / 2:
                return 'right_goal'  # 右侧得分
            else:
                self.x = self.radius
                self.vx = -self.vx
        # 右球门
        elif self.x + self.radius > SCREEN_WIDTH:
            if (SCREEN_HEIGHT - GOAL_HEIGHT) / 2 < self.y < (SCREEN_HEIGHT + GOAL_HEIGHT) / 2:
                return 'left_goal'  # 左侧得分
            else:
                self.x = SCREEN_WIDTH - self.radius
                self.vx = -self.vx

        return None

    def draw(self, surface):
        """绘制球"""
        # 球体
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius, 2)

        # 足球花纹（五边形图案简化）
        pygame.draw.circle(surface, BLACK, (int(self.x) - 3, int(self.y) - 3), 3)
        pygame.draw.circle(surface, BLACK, (int(self.x) + 3, int(self.y) + 3), 3)
        pygame.draw.circle(surface, BLACK, (int(self.x) + 3, int(self.y) - 3), 3)
        pygame.draw.circle(surface, BLACK, (int(self.x) - 3, int(self.y) + 3), 3)

    def get_rect(self):
        return pygame.Rect(
            self.x - self.radius, self.y - self.radius,
            self.radius * 2, self.radius * 2
        )


def check_collision(player, ball):
    """检测玩家和球的碰撞并处理"""
    dx = ball.x - player.x
    dy = ball.y - player.y
    distance = math.sqrt(dx ** 2 + dy ** 2)

    if distance < player.radius + ball.radius:
        # 碰撞法线方向
        if distance == 0:
            nx, ny = 1, 0
        else:
            nx = dx / distance
            ny = dy / distance

        # 分离球和玩家
        overlap = player.radius + ball.radius - distance
        ball.x += nx * overlap
        ball.y += ny * overlap

        # 相对速度
        rel_vx = ball.vx - player.vx
        rel_vy = ball.vy - player.vy

        # 相对速度在法线方向的分量
        rel_vel_normal = rel_vx * nx + rel_vy * ny

        # 如果球正在远离玩家，不处理
        if rel_vel_normal > 0:
            return

        # 弹性系数
        restitution = 0.8

        # 冲量（玩家的质量更大）
        impulse = -(1 + restitution) * rel_vel_normal

        # 更新球的速度（加入玩家速度的影响）
        ball.vx += impulse * nx * 0.8 + player.vx * 0.3
        ball.vy += impulse * ny * 0.8 + player.vy * 0.3

        # 确保球不会太快
        ball_speed = math.sqrt(ball.vx ** 2 + ball.vy ** 2)
        if ball_speed > BALL_MAX_SPEED:
            ball.vx = ball.vx / ball_speed * BALL_MAX_SPEED
            ball.vy = ball.vy / ball_speed * BALL_MAX_SPEED

        # 玩家受到轻微反冲
        player.vx -= impulse * nx * 0.15
        player.vy -= impulse * ny * 0.15


def check_player_collision(p1, p2):
    """检测两个玩家之间的碰撞"""
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    distance = math.sqrt(dx ** 2 + dy ** 2)

    if distance < p1.radius + p2.radius and distance > 0:
        nx = dx / distance
        ny = dy / distance

        # 分离
        overlap = p1.radius + p2.radius - distance
        p1.x -= nx * overlap / 2
        p1.y -= ny * overlap / 2
        p2.x += nx * overlap / 2
        p2.y += ny * overlap / 2

        # 交换部分速度（碰撞）
        rel_v = (p1.vx - p2.vx) * nx + (p1.vy - p2.vy) * ny
        if rel_v > 0:
            p1.vx -= rel_v * nx * 0.5
            p1.vy -= rel_v * ny * 0.5
            p2.vx += rel_v * nx * 0.5
            p2.vy += rel_v * ny * 0.5


def keep_in_bounds(player):
    """限制玩家在球场内"""
    margin = player.radius
    if player.x < margin:
        player.x = margin
        player.vx = 0
    elif player.x > SCREEN_WIDTH - margin:
        player.x = SCREEN_WIDTH - margin
        player.vx = 0
    if player.y < margin:
        player.y = margin
        player.vy = 0
    elif player.y > SCREEN_HEIGHT - margin:
        player.y = SCREEN_HEIGHT - margin
        player.vy = 0


def draw_field(surface):
    """绘制足球场"""
    # 草地背景
    surface.fill(GREEN)

    # 外框
    pygame.draw.rect(surface, WHITE, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 4)

    # 中场线
    pygame.draw.line(surface, WHITE, (SCREEN_WIDTH // 2, 0),
                     (SCREEN_WIDTH // 2, SCREEN_HEIGHT), 3)

    # 中圈
    pygame.draw.circle(surface, WHITE, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 60, 3)

    # 中圈点
    pygame.draw.circle(surface, WHITE, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 4)

    # 左球门
    goal_top = (SCREEN_HEIGHT - GOAL_HEIGHT) // 2
    pygame.draw.rect(surface, WHITE, (0, goal_top, GOAL_WIDTH, GOAL_HEIGHT), 3)
    pygame.draw.rect(surface, (200, 200, 200),
                     (0, goal_top, GOAL_WIDTH, GOAL_HEIGHT), 1)

    # 右球门
    pygame.draw.rect(surface, WHITE,
                     (SCREEN_WIDTH - GOAL_WIDTH, goal_top, GOAL_WIDTH, GOAL_HEIGHT), 3)
    pygame.draw.rect(surface, (200, 200, 200),
                     (SCREEN_WIDTH - GOAL_WIDTH, goal_top, GOAL_WIDTH, GOAL_HEIGHT), 1)

    # 左禁区
    pygame.draw.rect(surface, WHITE,
                     (0, SCREEN_HEIGHT // 2 - 120, 80, 240), 2)
    # 右禁区
    pygame.draw.rect(surface, WHITE,
                     (SCREEN_WIDTH - 80, SCREEN_HEIGHT // 2 - 120, 80, 240), 2)

    # 球场草皮纹理（简单条纹）
    for i in range(0, SCREEN_HEIGHT, 40):
        if (i // 40) % 2 == 0:
            pygame.draw.rect(surface, LIGHT_GREEN,
                             (0, i, SCREEN_WIDTH, 20), 0)
        else:
            pygame.draw.rect(surface, DARK_GREEN,
                             (0, i, SCREEN_WIDTH, 20), 0)

    # 重新绘制边界线（在草皮条纹之上）
    # 外框
    pygame.draw.rect(surface, WHITE, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 4)
    # 中场线
    pygame.draw.line(surface, WHITE, (SCREEN_WIDTH // 2, 0),
                     (SCREEN_WIDTH // 2, SCREEN_HEIGHT), 3)
    # 中圈
    pygame.draw.circle(surface, WHITE, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 60, 3)
    # 中圈点
    pygame.draw.circle(surface, WHITE, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 4)
    # 左球门
    goal_top = (SCREEN_HEIGHT - GOAL_HEIGHT) // 2
    pygame.draw.rect(surface, WHITE, (0, goal_top, GOAL_WIDTH, GOAL_HEIGHT), 3)
    # 右球门
    pygame.draw.rect(surface, WHITE,
                     (SCREEN_WIDTH - GOAL_WIDTH, goal_top, GOAL_WIDTH, GOAL_HEIGHT), 3)
    # 禁区
    pygame.draw.rect(surface, WHITE,
                     (0, SCREEN_HEIGHT // 2 - 120, 80, 240), 2)
    pygame.draw.rect(surface, WHITE,
                     (SCREEN_WIDTH - 80, SCREEN_HEIGHT // 2 - 120, 80, 240), 2)


def draw_goal_effect(surface, scoring_side, timer):
    """进球特效"""
    alpha = min(255, timer * 10)
    color = RED if scoring_side == 'left' else BLUE
    text = "左队进球!" if scoring_side == 'left' else "右队进球!"

    # 半透明遮罩
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    s.set_alpha(alpha // 2)
    s.fill((255, 255, 255))
    surface.blit(s, (0, 0))

    # 大字
    goal_text = big_font.render("⚽ 进球! ⚽", True, color)
    goal_rect = goal_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
    surface.blit(goal_text, goal_rect)

    # 谁进球
    who_text = font.render(text, True, color)
    who_rect = who_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
    surface.blit(who_text, who_rect)


def draw_scoreboard(surface, p1_score, p2_score):
    """绘制计分板"""
    # 背景
    score_bg = pygame.Rect(SCREEN_WIDTH // 2 - 100, 10, 200, 50)
    pygame.draw.rect(surface, (0, 0, 0, 180), score_bg, border_radius=10)
    pygame.draw.rect(surface, WHITE, score_bg, 2, border_radius=10)

    # 分数
    p1_color = BLUE
    p2_color = RED
    score_text = font.render(
        f"{p1_score}  -  {p2_score}", True, WHITE
    )
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 35))
    surface.blit(score_text, score_rect)

    # 玩家标签
    p1_label = small_font.render("玩家1 (WASD)", True, p1_color)
    p2_label = small_font.render("玩家2 (方向键)", True, p2_color)
    surface.blit(p1_label, (SCREEN_WIDTH // 2 - 230, 20))
    surface.blit(p2_label, (SCREEN_WIDTH // 2 + 80, 20))


def draw_controls(surface):
    """绘制操作提示"""
    # 玩家1
    p1_controls = small_font.render("玩家1: WASD移动 | 空格踢球", True, BLUE)
    surface.blit(p1_controls, (10, SCREEN_HEIGHT - 50))

    # 玩家2
    p2_controls = small_font.render("玩家2: 方向键移动 | 回车踢球", True, RED)
    p2_rect = p2_controls.get_rect(topright=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 50))
    surface.blit(p2_controls, p2_rect)

    reset_text = small_font.render("R: 重新开始 | ESC: 退出", True, GRAY)
    reset_rect = reset_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 25))
    surface.blit(reset_text, reset_rect)


def draw_menu(surface):
    """绘制主菜单"""
    # 背景
    draw_field(surface)

    # 半透明遮罩
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    s.set_alpha(180)
    s.fill(BLACK)
    surface.blit(s, (0, 0))

    # 标题
    title = big_font.render("2D 足球对战", True, WHITE)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
    surface.blit(title, title_rect)

    # 规则
    rules = [
        "⚽ 双人足球对战游戏 ⚽",
        "",
        "先得 5 分者获胜!",
        "",
        "玩家1: W/A/S/D 移动 | 空格键 踢球",
        "玩家2: ↑/↓/←/→ 移动 | 回车键 踢球",
        "",
        "按 空格键 开始游戏",
        "按 ESC 退出"
    ]

    y_offset = 240
    for rule in rules:
        if rule.startswith("⚽"):
            r = font.render(rule, True, YELLOW)
        elif rule.startswith("按"):
            r = font.render(rule, True, ORANGE)
        else:
            r = font.render(rule, True, WHITE)
        r_rect = r.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
        surface.blit(r, r_rect)
        y_offset += 35


def draw_winner(surface, player_num, player_color):
    """绘制胜利画面"""
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    s.set_alpha(200)
    s.fill(BLACK)
    surface.blit(s, (0, 0))

    # 胜利文字
    win_text = big_font.render(f"🎉 玩家{player_num} 获胜! 🎉", True, player_color)
    win_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
    surface.blit(win_text, win_rect)

    # 最终比分
    score_text = font.render("恭喜夺冠!", True, WHITE)
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
    surface.blit(score_text, score_rect)

    # 提示
    restart_text = font.render("按 R 重新开始 | 按 ESC 退出", True, ORANGE)
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
    surface.blit(restart_text, restart_rect)


def main():
    """主游戏循环"""
    # 创建玩家
    player1 = Player(
        SCREEN_WIDTH * 0.25, SCREEN_HEIGHT / 2,
        BLUE,
        {'up': pygame.K_w, 'down': pygame.K_s,
         'left': pygame.K_a, 'right': pygame.K_d,
         'kick': pygame.K_SPACE}
    )

    player2 = Player(
        SCREEN_WIDTH * 0.75, SCREEN_HEIGHT / 2,
        RED,
        {'up': pygame.K_UP, 'down': pygame.K_DOWN,
         'left': pygame.K_LEFT, 'right': pygame.K_RIGHT,
         'kick': pygame.K_RETURN}
    )

    ball = Ball()
    game_state = GameState.MENU
    goal_timer = 0
    scoring_side = None
    running = True
    goal_score = 5  # 获胜所需分数

    while running:
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    # 重新开始游戏
                    player1.score = 0
                    player2.score = 0
                    player1.reset_position('left')
                    player2.reset_position('right')
                    ball.reset()
                    game_state = GameState.PLAYING
                    goal_timer = 0
                elif event.key == pygame.K_SPACE and game_state == GameState.MENU:
                    game_state = GameState.PLAYING

        keys = pygame.key.get_pressed()

        if game_state == GameState.MENU:
            draw_menu(screen)
            pygame.display.flip()
            clock.tick(FPS)
            continue

        elif game_state == GameState.PLAYING:
            # 玩家输入
            kick1 = player1.handle_input(keys)
            kick2 = player2.handle_input(keys)

            # 踢球检测
            if kick1:
                # 计算踢球方向和力度
                dx = ball.x - player1.x
                dy = ball.y - player1.y
                dist = math.sqrt(dx ** 2 + dy ** 2)
                if dist < 100:  # 球在可踢范围内
                    if dist > 0:
                        ball.vx += dx / dist * KICK_FORCE
                        ball.vy += dy / dist * KICK_FORCE
                    player1.kick()

            if kick2:
                dx = ball.x - player2.x
                dy = ball.y - player2.y
                dist = math.sqrt(dx ** 2 + dy ** 2)
                if dist < 100:
                    if dist > 0:
                        ball.vx += dx / dist * KICK_FORCE
                        ball.vy += dy / dist * KICK_FORCE
                    player2.kick()

            # 限制玩家在球场内
            keep_in_bounds(player1)
            keep_in_bounds(player2)

            # 玩家碰撞
            check_player_collision(player1, player2)

            # 球和玩家碰撞
            check_collision(player1, ball)
            check_collision(player2, ball)

            # 更新球
            result = ball.update()

            # 处理进球
            if result == 'left_goal':
                player2.score += 1
                scoring_side = 'right'
                game_state = GameState.GOAL
                goal_timer = 0
            elif result == 'right_goal':
                player1.score += 1
                scoring_side = 'left'
                game_state = GameState.GOAL
                goal_timer = 0

            # 检查胜利
            if player1.score >= goal_score:
                game_state = GameState.WINNER
                winner_num = 1
                winner_color = BLUE
            elif player2.score >= goal_score:
                game_state = GameState.WINNER
                winner_num = 2
                winner_color = RED

            # 绘制
            draw_field(screen)
            ball.draw(screen)
            player1.draw(screen)
            player2.draw(screen)
            draw_scoreboard(screen, player1.score, player2.score)
            draw_controls(screen)

        elif game_state == GameState.GOAL:
            goal_timer += 1
            draw_field(screen)
            ball.draw(screen)
            player1.draw(screen)
            player2.draw(screen)
            draw_scoreboard(screen, player1.score, player2.score)
            draw_goal_effect(screen, scoring_side, goal_timer)

            if goal_timer > 90:  # 1.5秒后继续
                # 重置位置
                player1.reset_position('left')
                player2.reset_position('right')
                ball.reset()
                game_state = GameState.PLAYING

        elif game_state == GameState.WINNER:
            draw_field(screen)
            ball.draw(screen)
            player1.draw(screen)
            player2.draw(screen)
            draw_scoreboard(screen, player1.score, player2.score)
            draw_winner(screen, winner_num, winner_color)

        # 更新显示
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()