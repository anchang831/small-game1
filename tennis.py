"""
网球对战 (Tennis) - 经典网球模拟游戏
====================================
操作说明:
  - 双人模式: 玩家1 (WASD) vs 玩家2 (方向键↑↓)
  - 单人模式: 玩家1 (WASD) vs AI
  - SPACE: 发球 | P: 暂停 | M: 切换模式 | ESC: 返回菜单

游戏规则:
  - 标准网球计分: 0 → 15 → 30 → 40 → 赢一局
  - 40-40 时进入 Deuce, 需连赢2分
  - 先赢3局者获胜 (短盘制)
"""

import pygame
import math
import random
import sys

# ==================== 初始化 ====================
pygame.init()
pygame.mixer.init()

# ==================== 常量 ====================
WIDTH, HEIGHT = 900, 600
FPS = 60
FONT_NAME = None  # 使用默认字体

# 颜色
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
COURT_GREEN = (46, 139, 87)
LINE_WHITE = (255, 255, 255)
BALL_COLOR = (255, 255, 0)
NET_COLOR = (200, 200, 200)
SHADOW_COLOR = (0, 0, 0, 60)
P1_COLOR = (65, 105, 225)   # 皇家蓝
P2_COLOR = (220, 20, 60)    # 大红
BG_COLOR = (20, 20, 30)
TEXT_COLOR = (255, 255, 255)
ACCENT_COLOR = (255, 215, 0)  # 金色
DEUCE_COLOR = (255, 100, 100)
MENU_BG = (30, 30, 50)

# 游戏物理
PADDLE_WIDTH, PADDLE_HEIGHT = 15, 80
PADDLE_SPEED = 6
BALL_SIZE = 12
BALL_MAX_SPEED = 12
BALL_MIN_SPEED = 5
NET_WIDTH = 4
NET_HEIGHT = 20  # 每个小段的高度
NET_GAP = 8      # 小段间距

# 网球计分
SCORE_MAP = {0: "0", 1: "15", 2: "30", 3: "40"}
WIN_GAMES = 3  # 短盘制，先赢3局获胜

# 模式
MODE_1P = 1  # 单人 vs AI
MODE_2P = 2  # 双人对战


# ==================== 工具函数 ====================
def draw_text(surf, text, size, x, y, color=TEXT_COLOR, center=True, bold=False):
    """绘制文字"""
    font = pygame.font.Font(FONT_NAME, size)
    if bold:
        font.set_bold(True)
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surf.blit(img, rect)


def draw_rounded_rect(surf, color, rect, radius=8):
    """绘制圆角矩形"""
    x, y, w, h = rect
    pygame.draw.rect(surf, color, (x + radius, y, w - 2 * radius, h))
    pygame.draw.rect(surf, color, (x, y + radius, w, h - 2 * radius))
    pygame.draw.circle(surf, color, (x + radius, y + radius), radius)
    pygame.draw.circle(surf, color, (x + w - radius - 1, y + radius), radius)
    pygame.draw.circle(surf, color, (x + radius, y + h - radius - 1), radius)
    pygame.draw.circle(surf, color, (x + w - radius - 1, y + h - radius - 1), radius)


# ==================== 球拍类 ====================
class Paddle:
    def __init__(self, x, y, color, player_id):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.color = color
        self.player_id = player_id
        self.speed = PADDLE_SPEED
        self.score = 0       # 当前局小分
        self.games = 0       # 赢的局数
        self.target_y = y    # AI 目标位置

    def move(self, dy):
        """移动球拍"""
        self.rect.y += dy
        # 限制在球场范围内
        if self.rect.top < 40:
            self.rect.top = 40
        if self.rect.bottom > HEIGHT - 40:
            self.rect.bottom = HEIGHT - 40

    def reset_position(self, is_left=True):
        """重置位置"""
        court_left = 60
        court_right = WIDTH - 60
        cx = court_left + 30 if is_left else court_right - 30 - PADDLE_WIDTH
        self.rect.x = cx
        self.rect.centery = HEIGHT // 2

    def draw(self, surf):
        """绘制球拍"""
        # 阴影
        shadow_rect = self.rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        draw_rounded_rect(surf, (0, 0, 0, 40), shadow_rect, 4)
        # 主体
        draw_rounded_rect(surf, self.color, self.rect, 6)
        # 高光
        highlight = self.rect.copy()
        highlight.width = 5
        highlight.x += 3
        highlight.y += 5
        highlight.height -= 10
        lighter = tuple(min(c + 60, 255) for c in self.color)
        draw_rounded_rect(surf, lighter, highlight, 2)


# ==================== 球类 ====================
class Ball:
    def __init__(self):
        self.reset()

    def reset(self, direction=1):
        """重置球到场地中央"""
        self.rect = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        angle = random.uniform(-0.5, 0.5)  # 随机角度
        self.speed = BALL_MIN_SPEED
        self.vx = self.speed * math.cos(angle) * direction
        self.vy = self.speed * math.sin(angle)
        self.last_hit = 0  # 0: 未击, 1: 玩家1, 2: 玩家2
        self.trail = []     # 轨迹

    def update_trail(self):
        """更新球轨迹"""
        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 12:
            self.trail.pop(0)

    def draw(self, surf):
        """绘制球和轨迹"""
        # 轨迹
        for i, pos in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)) * 0.3)
            size = int(BALL_SIZE * (0.3 + 0.7 * i / len(self.trail)))
            pygame.draw.circle(surf, (255, 255, 0, alpha), pos, size // 2)
        # 球体阴影
        pygame.draw.circle(surf, (0, 0, 0, 60),
                           (self.rect.centerx + 2, self.rect.centery + 2), BALL_SIZE // 2)
        # 球体
        pygame.draw.circle(surf, BALL_COLOR, self.rect.center, BALL_SIZE // 2)
        # 高光
        pygame.draw.circle(surf, (255, 255, 200),
                           (self.rect.centerx - 2, self.rect.centery - 2), BALL_SIZE // 4)


# ==================== 游戏类 ====================
class TennisGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("🎾 网球对战 Tennis")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "menu"  # menu, playing, paused, game_over
        self.mode = MODE_1P
        self.paused = False

        # 创建玩家
        self.player1 = Paddle(80, HEIGHT // 2 - PADDLE_HEIGHT // 2, P1_COLOR, 1)
        self.player2 = Paddle(WIDTH - 80 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2, P2_COLOR, 2)
        self.ball = Ball()

        # 游戏状态
        self.serving = True          # 等待发球
        self.server = 1              # 1: 玩家1发球, 2: 玩家2发球
        self.point_winner = 0
        self.point_timer = 0
        self.rally_count = 0
        self.game_over = False
        self.winner = 0

        # 粒子效果
        self.particles = []

        # 按键
        self.keys = {
            'w': False, 's': False,
            'up': False, 'down': False,
        }

        # 菜单动画
        self.menu_ball_angle = 0

    def add_particles(self, x, y, color, count=15):
        """添加粒子效果"""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.randint(20, 40),
                'max_life': 40,
                'color': color,
                'size': random.randint(2, 5),
            })

    def update_particles(self):
        """更新粒子效果"""
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.1  # 重力
            p['life'] -= 1
            if p['life'] <= 0:
                self.particles.remove(p)

    def draw_particles(self, surf):
        """绘制粒子效果"""
        for p in self.particles:
            alpha = p['life'] / p['max_life']
            size = int(p['size'] * alpha)
            if size > 0:
                pygame.draw.circle(surf, p['color'], (int(p['x']), int(p['y'])), size)

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN:
                if self.state == "menu":
                    if event.key == pygame.K_1:
                        self.mode = MODE_1P
                        self.state = "playing"
                        self.reset_game()
                    elif event.key == pygame.K_2:
                        self.mode = MODE_2P
                        self.state = "playing"
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False

                elif self.state == "playing":
                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                    if event.key == pygame.K_ESCAPE:
                        self.state = "menu"
                    if event.key == pygame.K_m:
                        self.state = "menu"

                    if not self.paused:
                        # 玩家1 控制
                        if event.key == pygame.K_w:
                            self.keys['w'] = True
                        if event.key == pygame.K_s:
                            self.keys['s'] = True
                        # 玩家2 控制 (双人)
                        if self.mode == MODE_2P:
                            if event.key == pygame.K_UP:
                                self.keys['up'] = True
                            if event.key == pygame.K_DOWN:
                                self.keys['down'] = True

                        # 发球
                        if event.key == pygame.K_SPACE and self.serving:
                            self.serve_ball()

                elif self.state == "game_over":
                    if event.key == pygame.K_r:
                        self.state = "playing"
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "menu"
                    elif event.key == pygame.K_m:
                        self.state = "menu"

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_w:
                    self.keys['w'] = False
                if event.key == pygame.K_s:
                    self.keys['s'] = False
                if self.mode == MODE_2P:
                    if event.key == pygame.K_UP:
                        self.keys['up'] = False
                    if event.key == pygame.K_DOWN:
                        self.keys['down'] = False

    def reset_game(self):
        """重置整场比赛"""
        self.player1.score = 0
        self.player2.score = 0
        self.player1.games = 0
        self.player2.games = 0
        self.player1.reset_position(True)
        self.player2.reset_position(False)
        self.server = 1
        self.serving = True
        self.game_over = False
        self.winner = 0
        self.point_winner = 0
        self.point_timer = 0
        self.rally_count = 0
        self.particles = []
        self.ball.reset(1)
        self.paused = False

    def reset_point(self):
        """重置这一分"""
        self.player1.reset_position(True)
        self.player2.reset_position(False)
        self.serving = True
        self.ball.reset(1 if self.server == 1 else -1)

    def serve_ball(self):
        """发球"""
        self.serving = False
        direction = 1 if self.server == 1 else -1
        angle = random.uniform(-0.4, 0.4)
        self.ball.vx = BALL_MIN_SPEED * math.cos(angle) * direction
        self.ball.vy = BALL_MIN_SPEED * math.sin(angle)
        self.ball.speed = BALL_MIN_SPEED
        self.rally_count = 0

    def score_point(self, player):
        """得分"""
        self.point_winner = player
        self.point_timer = 90  # 1.5秒展示

        # 粒子特效
        cx, cy = WIDTH // 2, HEIGHT // 2
        color = P1_COLOR if player == 1 else P2_COLOR
        self.add_particles(cx, cy, color, 30)

        if player == 1:
            self.player1.score += 1
        else:
            self.player2.score += 1

        # 检查是否赢了一局
        self.check_game_win()

    def check_game_win(self):
        """检查是否赢了一局"""
        s1, s2 = self.player1.score, self.player2.score

        # 标准网球局计分: 先到4分且领先2分
        if s1 >= 4 or s2 >= 4:
            if abs(s1 - s2) >= 2:
                if s1 > s2:
                    self.player1.games += 1
                else:
                    self.player2.games += 1
                # 重置小分
                self.player1.score = 0
                self.player2.score = 0
                # 交换发球权
                self.server = 3 - self.server

                # 检查是否赢得比赛
                if self.player1.games >= WIN_GAMES or self.player2.games >= WIN_GAMES:
                    if abs(self.player1.games - self.player2.games) >= 1:
                        self.winner = 1 if self.player1.games > self.player2.games else 2
                        self.state = "game_over"
                        self.game_over = True
                        # 胜利粒子特效
                        cx, cy = WIDTH // 2, HEIGHT // 2
                        self.add_particles(cx, cy, ACCENT_COLOR, 50)

    def get_point_display(self, score):
        """获取分数显示"""
        if score <= 3:
            return SCORE_MAP[score]
        return str(score - 3) + "AD"  # 超出40的显示

    def update_ai(self):
        """AI 控制"""
        if self.mode == MODE_2P:
            return

        # 预测球的最终位置
        target_y = self.player2.rect.centery

        if not self.serving and not self.paused:
            # 球朝AI方向移动时才追踪
            if self.ball.vx > 0:
                # 预测球到达AI球拍时的Y位置
                dx = self.player2.rect.left - self.ball.rect.right
                if dx > 0:
                    travel_time = dx / abs(self.ball.vx) if self.ball.vx != 0 else 0
                    predicted_y = self.ball.rect.centery + self.ball.vy * travel_time

                    # 考虑反弹
                    while predicted_y < 40 or predicted_y > HEIGHT - 40:
                        if predicted_y < 40:
                            predicted_y = 40 + (40 - predicted_y)
                        if predicted_y > HEIGHT - 40:
                            predicted_y = (HEIGHT - 40) - (predicted_y - (HEIGHT - 40))

                    target_y = predicted_y
            else:
                # 球远离时回到中间
                target_y = HEIGHT // 2

        # 移动AI
        diff = target_y - self.player2.rect.centery
        move_speed = min(abs(diff), self.player2.speed * 0.85)
        if abs(diff) > 10:
            self.player2.move(move_speed if diff > 0 else -move_speed)

    def update(self):
        """更新游戏状态"""
        if self.state != "playing" or self.paused:
            return

        # 更新粒子
        self.update_particles()

        # 点球结束后的等待
        if self.point_timer > 0:
            self.point_timer -= 1
            if self.point_timer == 0:
                self.reset_point()
            return

        # ---- 玩家移动 ----
        if self.keys['w']:
            self.player1.move(-self.player1.speed)
        if self.keys['s']:
            self.player1.move(self.player1.speed)

        if self.mode == MODE_2P:
            if self.keys['up']:
                self.player2.move(-self.player2.speed)
            if self.keys['down']:
                self.player2.move(self.player2.speed)
        else:
            self.update_ai()

        # ---- 发球状态 ----
        if self.serving:
            # 球跟随发球方
            server = self.player1 if self.server == 1 else self.player2
            self.ball.rect.center = (server.rect.right + 20 if self.server == 1
                                     else server.rect.left - 20, server.rect.centery)
            return

        # ---- 球移动 ----
        self.ball.rect.x += self.ball.vx
        self.ball.rect.y += self.ball.vy
        self.ball.update_trail()

        # ---- 上下边界反弹 ----
        if self.ball.rect.top <= 40:
            self.ball.rect.top = 40
            self.ball.vy = abs(self.ball.vy)
        if self.ball.rect.bottom >= HEIGHT - 40:
            self.ball.rect.bottom = HEIGHT - 40
            self.ball.vy = -abs(self.ball.vy)

        # ---- 球拍碰撞 ----
        # 玩家1 球拍
        if (self.ball.vx < 0 and
                self.ball.rect.colliderect(self.player1.rect) and
                self.ball.last_hit != 1):
            self.hit_ball(self.player1, 1)

        # 玩家2 球拍
        if (self.ball.vx > 0 and
                self.ball.rect.colliderect(self.player2.rect) and
                self.ball.last_hit != 2):
            self.hit_ball(self.player2, 2)

        # ---- 得分检测 ----
        if self.ball.rect.left <= 40:
            self.score_point(2)  # 玩家2得分
        if self.ball.rect.right >= WIDTH - 40:
            self.score_point(1)  # 玩家1得分

    def hit_ball(self, paddle, player_id):
        """击球"""
        self.ball.last_hit = player_id
        self.rally_count += 1

        # 计算击球角度 (基于球拍击中位置)
        hit_pos = (self.ball.rect.centery - paddle.rect.centery) / (PADDLE_HEIGHT / 2)
        hit_pos = max(-1, min(1, hit_pos))  # -1 ~ 1

        # 角度范围 -60° ~ 60°
        max_angle = math.radians(60)
        angle = hit_pos * max_angle

        # 增加球速 (但不超过最大值)
        self.ball.speed = min(BALL_MAX_SPEED, self.ball.speed + 0.15)
        direction = -1 if player_id == 1 else 1

        self.ball.vx = self.ball.speed * math.cos(angle) * direction
        self.ball.vy = self.ball.speed * math.sin(angle)

        # 击球粒子特效
        self.add_particles(self.ball.rect.centerx, self.ball.rect.centery,
                           paddle.color, 8)

        # 防止球卡在球拍里
        if player_id == 1:
            self.ball.rect.left = paddle.rect.right + 1
        else:
            self.ball.rect.right = paddle.rect.left - 1

    def draw_court(self, surf):
        """绘制球场"""
        # 背景
        surf.fill(BG_COLOR)

        # 球场区域
        court_rect = pygame.Rect(50, 30, WIDTH - 100, HEIGHT - 60)
        draw_rounded_rect(surf, COURT_GREEN, court_rect, 10)

        # 球场边框（白线）
        pygame.draw.rect(surf, LINE_WHITE, court_rect, 3, border_radius=10)

        # 中场线 (虚线)
        mid_x = WIDTH // 2
        for y in range(50, HEIGHT - 50, 20):
            alpha = 0.5 if (y // 20) % 2 == 0 else 1.0
            color = tuple(int(c * alpha) for c in LINE_WHITE)
            pygame.draw.line(surf, color, (mid_x, y), (mid_x, min(y + 10, HEIGHT - 50)), 2)

        # 发球线
        service_line_left = WIDTH // 4
        service_line_right = WIDTH * 3 // 4
        pygame.draw.line(surf, LINE_WHITE, (service_line_left, 50),
                         (service_line_left, HEIGHT - 50), 1)
        pygame.draw.line(surf, LINE_WHITE, (service_line_right, 50),
                         (service_line_right, HEIGHT - 50), 1)

        # 球网
        net_x = WIDTH // 2 - NET_WIDTH // 2
        for y in range(40, HEIGHT - 40, NET_HEIGHT + NET_GAP):
            rect = pygame.Rect(net_x, y, NET_WIDTH, NET_HEIGHT)
            pygame.draw.rect(surf, NET_COLOR, rect)
            # 网的高光
            pygame.draw.rect(surf, (255, 255, 255, 100), (net_x, y, NET_WIDTH, 2))

        # 网柱
        pygame.draw.circle(surf, (180, 180, 180), (mid_x, 35), 6)
        pygame.draw.circle(surf, (180, 180, 180), (mid_x, HEIGHT - 35), 6)

    def draw_scoreboard(self, surf):
        """绘制计分板"""
        # 计分板背景
        sb_width, sb_height = 400, 80
        sb_x = WIDTH // 2 - sb_width // 2
        sb_y = 5
        draw_rounded_rect(surf, (0, 0, 0, 150), (sb_x, sb_y, sb_width, sb_height), 8)

        # 玩家1 信息
        p1_color = P1_COLOR
        p2_color = P2_COLOR

        # 名字
        name1 = "玩家1" if self.mode == MODE_2P else "你"
        name2 = "玩家2" if self.mode == MODE_2P else "AI"
        draw_text(surf, name1, 20, WIDTH // 2 - 130, 30, p1_color, center=True, bold=True)
        draw_text(surf, name2, 20, WIDTH // 2 + 130, 30, p2_color, center=True, bold=True)

        # 局分
        draw_text(surf, f"第 {self.player1.games} 局", 16, WIDTH // 2 - 130, 55, TEXT_COLOR)
        draw_text(surf, f"第 {self.player2.games} 局", 16, WIDTH // 2 + 130, 55, TEXT_COLOR)

        # 当前小分
        s1 = self.player1.score
        s2 = self.player2.score

        # 判断是否 Deuce
        is_deuce = s1 >= 3 and s2 >= 3 and s1 == s2
        if is_deuce:
            draw_text(surf, "DEUCE", 28, WIDTH // 2, 42, DEUCE_COLOR, bold=True)
        elif s1 >= 4 or s2 >= 4:
            # 占先 (Advantage)
            if s1 > s2:
                draw_text(surf, "占先", 22, WIDTH // 2 - 130, 78, ACCENT_COLOR)
                draw_text(surf, self.get_point_display(s2), 22, WIDTH // 2 + 130, 78, TEXT_COLOR)
            else:
                draw_text(surf, self.get_point_display(s1), 22, WIDTH // 2 - 130, 78, TEXT_COLOR)
                draw_text(surf, "占先", 22, WIDTH // 2 + 130, 78, ACCENT_COLOR)
        else:
            draw_text(surf, self.get_point_display(s1), 22, WIDTH // 2 - 130, 78, TEXT_COLOR)
            draw_text(surf, self.get_point_display(s2), 22, WIDTH // 2 + 130, 78, TEXT_COLOR)

        # 发球指示器
        if self.server == 1:
            pygame.draw.circle(surf, ACCENT_COLOR, (WIDTH // 2 - 170, 30), 5)
        else:
            pygame.draw.circle(surf, ACCENT_COLOR, (WIDTH // 2 + 170, 30), 5)

    def draw_hud(self, surf):
        """绘制HUD信息"""
        # 按键提示
        hint_y = HEIGHT - 15
        if self.serving:
            draw_text(surf, "按 SPACE 发球", 18, WIDTH // 2, HEIGHT // 2 + 60, ACCENT_COLOR, bold=True)
            # 闪烁指示
            if pygame.time.get_ticks() % 1000 < 500:
                draw_text(surf, "● 发球", 14, WIDTH // 2, HEIGHT // 2 + 90, ACCENT_COLOR)

        # 底部提示
        if self.paused:
            draw_text(surf, "游戏暂停", 40, WIDTH // 2, HEIGHT // 2, ACCENT_COLOR, bold=True)
            draw_text(surf, "按 P 继续  |  M 返回菜单  |  ESC 退出", 18, WIDTH // 2, HEIGHT // 2 + 50, TEXT_COLOR)
        else:
            mode_text = "单人模式" if self.mode == MODE_1P else "双人模式"
            hint = f"P:暂停 | M:菜单 | ESC:退出 | {mode_text}"
            if self.mode == MODE_2P:
                hint += " | 玩家1:W/S | 玩家2:↑/↓"
            else:
                hint += " | 你:W/S | AI:自动"
            draw_text(surf, hint, 14, WIDTH // 2, hint_y, (200, 200, 200))

        # 回合数
        if not self.serving:
            draw_text(surf, f"回合: {self.rally_count}", 14, WIDTH - 80, HEIGHT - 15, (200, 200, 200))

    def draw_game_over(self, surf):
        """绘制游戏结束画面"""
        # 半透明遮罩
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        surf.blit(overlay, (0, 0))

        # 奖杯
        winner_name = "玩家1" if self.winner == 1 else ("玩家2" if self.mode == MODE_2P else "AI")
        winner_color = P1_COLOR if self.winner == 1 else P2_COLOR

        draw_text(surf, "🏆", 80, WIDTH // 2, HEIGHT // 2 - 120, ACCENT_COLOR)
        draw_text(surf, f"{winner_name} 获胜!", 52, WIDTH // 2, HEIGHT // 2 - 30, winner_color, bold=True)
        draw_text(surf, f"最终比分 {self.player1.games} - {self.player2.games}", 28,
                  WIDTH // 2, HEIGHT // 2 + 30, TEXT_COLOR)

        # 比赛统计
        draw_text(surf, f"按 R 重新开始  |  M 返回菜单  |  ESC 退出", 18,
                  WIDTH // 2, HEIGHT // 2 + 90, (200, 200, 200))

    def draw_menu(self, surf):
        """绘制主菜单"""
        # 背景
        surf.fill(MENU_BG)

        # 装饰线条
        for i in range(0, WIDTH, 40):
            y = int(HEIGHT // 2 + 60 + 30 * math.sin(self.menu_ball_angle + i * 0.02))
            pygame.draw.circle(surf, (50, 60, 80), (i, y), 2)

        # 标题
        draw_text(surf, "🎾 网 球 对 战", 64, WIDTH // 2, HEIGHT // 2 - 120, ACCENT_COLOR, bold=True)
        draw_text(surf, "TENNIS", 36, WIDTH // 2, HEIGHT // 2 - 60, TEXT_COLOR)

        # 菜单选项
        menu_y = HEIGHT // 2 + 30
        draw_rounded_rect(surf, (50, 60, 100, 200), (WIDTH // 2 - 120, menu_y - 10, 240, 100), 12)

        draw_text(surf, "按 1 - 单人模式 (vs AI)", 24, WIDTH // 2, menu_y + 15, TEXT_COLOR)
        draw_text(surf, "按 2 - 双人模式", 24, WIDTH // 2, menu_y + 55, TEXT_COLOR)

        # 操作说明
        inst_y = menu_y + 140
        draw_text(surf, "─" * 30, 14, WIDTH // 2, inst_y, (150, 150, 150))
        draw_text(surf, "操作说明", 20, WIDTH // 2, inst_y + 25, ACCENT_COLOR, bold=True)
        draw_text(surf, "玩家1: W / S 移动    玩家2: ↑ / ↓ 移动", 16, WIDTH // 2, inst_y + 55, TEXT_COLOR)
        draw_text(surf, "SPACE: 发球    P: 暂停    ESC: 退出", 16, WIDTH // 2, inst_y + 80, TEXT_COLOR)
        draw_text(surf, "先赢 3 局者获胜!", 16, WIDTH // 2, inst_y + 105, ACCENT_COLOR)

        # 底部版本
        draw_text(surf, "v1.0 | Pygame Tennis", 12, WIDTH // 2, HEIGHT - 20, (100, 100, 100))

        # 菜单动画球
        self.menu_ball_angle += 0.02
        bx = WIDTH // 2 + 80 * math.cos(self.menu_ball_angle)
        by = HEIGHT // 2 - 120 + 20 * math.sin(self.menu_ball_angle * 2)
        pygame.draw.circle(surf, BALL_COLOR, (int(bx), int(by)), BALL_SIZE // 2)
        pygame.draw.circle(surf, (255, 255, 200), (int(bx) - 2, int(by) - 2), BALL_SIZE // 4)

    def draw(self):
        """绘制画面"""
        self.screen.fill(BG_COLOR)

        if self.state == "menu":
            self.draw_menu(self.screen)
        elif self.state == "playing":
            self.draw_court(self.screen)
            self.player1.draw(self.screen)
            self.player2.draw(self.screen)
            if not (self.serving and self.point_timer > 0):
                self.ball.draw(self.screen)
            self.draw_scoreboard(self.screen)
            self.draw_particles(self.screen)
            self.draw_hud(self.screen)

            if self.game_over:
                self.draw_game_over(self.screen)
        elif self.state == "game_over":
            self.draw_court(self.screen)
            self.player1.draw(self.screen)
            self.player2.draw(self.screen)
            self.draw_scoreboard(self.screen)
            self.draw_particles(self.screen)
            self.draw_game_over(self.screen)

        pygame.display.flip()

    def run(self):
        """主循环"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ==================== 入口 ====================
if __name__ == "__main__":
    game = TennisGame()
    game.run()