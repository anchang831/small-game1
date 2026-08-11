"""
排球对战 (Volleyball) - 2D排球游戏
===============================
操作方式:
  玩家1 (左): W/A/S/D 移动, Q 击球/发球
  玩家2 (右): ↑/←/↓/→ 移动, / 击球/发球
  ESC: 退出游戏
  R: 重新开始

游戏规则:
  - 将球击过网落到对方场地得分
  - 先到 5 分获胜
  - 每方最多触球 3 次必须过网
"""

import pygame
import sys
import math
import random

# ==================== 初始化 ====================
pygame.init()
pygame.mixer.init()

# ==================== 常量配置 ====================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 颜色
BLACK = (20, 20, 30)
WHITE = (255, 255, 255)
RED = (255, 60, 60)
BLUE = (60, 120, 255)
GREEN = (60, 200, 100)
YELLOW = (255, 255, 100)
GRAY = (100, 100, 120)
DARK_GRAY = (40, 40, 55)
NET_COLOR = (200, 200, 200)
COURT_COLOR = (50, 60, 80)
FLOOR_COLOR = (70, 80, 100)

# 物理常量
GRAVITY = 0.35
BALL_RADIUS = 10
PLAYER_WIDTH = 28
PLAYER_HEIGHT = 40
NET_HEIGHT = 180
NET_WIDTH = 6
MAX_SCORE = 5

# 延迟时间(帧)
SPIKE_COOLDOWN = 12
MAX_TOUCHES = 3


class Ball:
    """排球对象"""

    def __init__(self):
        self.reset()

    def reset(self, direction=1):
        """重置球到场地中央"""
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2 - 80
        self.vx = random.uniform(2, 4) * direction
        self.vy = random.uniform(-6, -4)
        self.radius = BALL_RADIUS
        self.active = True
        self.last_hitter = None  # 最后触球玩家
        self.touch_count = 0  # 当前方触球次数
        self.side = None  # 当前球所在方: 'left' or 'right'
        self.trail = []  # 轨迹

    def update(self):
        """更新物理位置"""
        if not self.active:
            return

        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy

        # 轨迹记录
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 12:
            self.trail.pop(0)

        # 左右墙壁反弹
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx = abs(self.vx) * 0.8
        elif self.x + self.radius > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.vx = -abs(self.vx) * 0.8

        # 天花板反弹
        if self.y - self.radius < 0:
            self.y = self.radius
            self.vy = abs(self.vy) * 0.8

        # 判断球在哪一侧
        if self.x < SCREEN_WIDTH // 2:
            self.side = 'left'
        else:
            self.side = 'right'

    def draw(self, screen):
        """绘制球及轨迹"""
        # 轨迹
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(100 * (i + 1) / len(self.trail))
            pygame.draw.circle(screen, (255, 255, 100, alpha),
                               (tx, ty), int(self.radius * 0.5 * (i + 1) / len(self.trail)))

        # 球体阴影
        pygame.draw.circle(screen, (30, 30, 40),
                           (int(self.x) + 3, int(self.y) + 3), self.radius)

        # 球体主体
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (255, 255, 200), (int(self.x), int(self.y)), self.radius - 2)

        # 球体高光
        highlight_x = int(self.x) - 3
        highlight_y = int(self.y) - 3
        pygame.draw.circle(screen, (255, 255, 255),
                           (highlight_x, highlight_y), self.radius // 3)

    def is_on_left_side(self):
        return self.x < SCREEN_WIDTH // 2

    def is_on_right_side(self):
        return self.x >= SCREEN_WIDTH // 2


class Player:
    """玩家对象"""

    def __init__(self, x, y, side, is_ai=False):
        self.x = x
        self.y = y
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.side = side  # 'left' or 'right'
        self.is_ai = is_ai
        self.vx = 0
        self.vy = 0
        self.speed = 5.5
        self.jump_power = -10
        self.on_ground = False
        self.score = 0
        self.spike_cooldown = 0  # 击球冷却
        self.facing = 1 if side == 'right' else -1
        self.win = False

        # 颜色
        if side == 'left':
            self.color = BLUE
            self.light_color = (100, 160, 255)
            self.dark_color = (40, 80, 200)
        else:
            self.color = RED
            self.light_color = (255, 100, 100)
            self.dark_color = (200, 40, 40)

    def reset_position(self):
        """重置位置到己方半场"""
        if self.side == 'left':
            self.x = SCREEN_WIDTH // 4
        else:
            self.x = SCREEN_WIDTH * 3 // 4
        self.y = SCREEN_HEIGHT - 100
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.spike_cooldown = 0

    def move_left(self):
        if self.x - self.width // 2 > 0:
            self.vx = -self.speed
        self.facing = -1

    def move_right(self):
        max_x = SCREEN_WIDTH // 2 if self.side == 'left' else SCREEN_WIDTH
        if self.x + self.width // 2 < max_x:
            self.vx = self.speed
        self.facing = 1

    def move_left_ai(self):
        self.vx = -self.speed * 0.6
        self.facing = -1

    def move_right_ai(self):
        self.vx = self.speed * 0.6
        self.facing = 1

    def stop_x(self):
        self.vx = 0

    def jump(self):
        if self.on_ground:
            self.vy = self.jump_power
            self.on_ground = False

    def update(self):
        """更新物理"""
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy

        # 地面碰撞
        if self.y + self.height // 2 >= SCREEN_HEIGHT - 20:
            self.y = SCREEN_HEIGHT - 20 - self.height // 2
            self.vy = 0
            self.on_ground = True

        # 左右边界
        if self.side == 'left':
            if self.x - self.width // 2 < 0:
                self.x = self.width // 2
            if self.x + self.width // 2 > SCREEN_WIDTH // 2 - NET_WIDTH // 2:
                self.x = SCREEN_WIDTH // 2 - NET_WIDTH // 2 - self.width // 2
        else:
            if self.x - self.width // 2 < SCREEN_WIDTH // 2 + NET_WIDTH // 2:
                self.x = SCREEN_WIDTH // 2 + NET_WIDTH // 2 + self.width // 2
            if self.x + self.width // 2 > SCREEN_WIDTH:
                self.x = SCREEN_WIDTH - self.width // 2

        # 天花板碰撞
        if self.y - self.height // 2 < 0:
            self.y = self.height // 2
            self.vy = 0

        # 冷却递减
        if self.spike_cooldown > 0:
            self.spike_cooldown -= 1

        # 摩擦减速
        if self.on_ground:
            self.vx *= 0.85
        else:
            self.vx *= 0.95

    def draw(self, screen):
        """绘制球员"""
        # 阴影
        shadow_y = SCREEN_HEIGHT - 15
        shadow_width = self.width * 0.6
        shadow_height = 8
        pygame.draw.ellipse(screen, (10, 10, 20),
                            (self.x - shadow_width // 2, shadow_y - shadow_height // 2,
                             shadow_width, shadow_height))

        # 身体
        body_rect = pygame.Rect(self.x - self.width // 2, self.y - self.height // 2,
                                self.width, self.height)
        pygame.draw.rect(screen, self.color, body_rect, border_radius=6)

        # 身体高光
        inner_rect = pygame.Rect(self.x - self.width // 2 + 4, self.y - self.height // 2 + 4,
                                 self.width // 2, self.height - 8)
        pygame.draw.rect(screen, self.light_color, inner_rect, border_radius=4)

        # 头
        head_radius = self.width // 2 - 2
        head_x = self.x + self.facing * 2
        head_y = self.y - self.height // 2 - head_radius + 4
        pygame.draw.circle(screen, self.color, (int(head_x), int(head_y)), head_radius)
        pygame.draw.circle(screen, self.light_color, (int(head_x), int(head_y)), head_radius - 2)

        # 眼睛
        eye_x = head_x + self.facing * 4
        eye_y = head_y - 2
        pygame.draw.circle(screen, WHITE, (int(eye_x), int(eye_y)), 4)
        pygame.draw.circle(screen, BLACK, (int(eye_x + self.facing * 2), int(eye_y)), 2)

        # 手臂(击球手)
        arm_offset = 14 if self.spike_cooldown > 0 else 6
        arm_x = self.x + self.facing * arm_offset
        arm_y = self.y - 4
        pygame.draw.line(screen, self.light_color,
                         (self.x + self.facing * 6, self.y - 4),
                         (arm_x, arm_y), 5)

        # 腿
        leg_spread = 8
        if abs(self.vx) > 0.5:
            leg_offset = (pygame.time.get_ticks() // 100 % 2) * 6 - 3
        else:
            leg_offset = 0
        pygame.draw.line(screen, self.dark_color,
                         (self.x - leg_spread, self.y + self.height // 2 - 2),
                         (self.x - leg_spread + leg_offset, self.y + self.height // 2 + 8), 5)
        pygame.draw.line(screen, self.dark_color,
                         (self.x + leg_spread, self.y + self.height // 2 - 2),
                         (self.x + leg_spread + leg_offset, self.y + self.height // 2 + 8), 5)

        # 球衣号码
        font = pygame.font.Font(None, 20)
        num_text = font.render("1" if self.side == 'left' else "2", True, WHITE)
        num_rect = num_text.get_rect(center=(self.x, self.y - 2))
        screen.blit(num_text, num_rect)

    def get_rect(self):
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2,
                           self.width, self.height)

    def can_spike(self):
        return self.spike_cooldown <= 0 and self.on_ground


class Net:
    """球网"""

    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 20
        self.width = NET_WIDTH
        self.height = NET_HEIGHT

    def draw(self, screen):
        # 网柱
        pole_color = (150, 150, 150)
        # 左柱
        pygame.draw.rect(screen, pole_color,
                         (self.x - self.width // 2 - 3, self.y - self.height, 5, self.height))
        # 右柱
        pygame.draw.rect(screen, pole_color,
                         (self.x + self.width // 2 - 2, self.y - self.height, 5, self.height))

        # 网面 - 网格线
        for row in range(0, self.height, 12):
            alpha = 80 if row % 24 == 0 else 40
            color = (200, 200, 200, alpha)
            s = pygame.Surface((self.width, 2), pygame.SRCALPHA)
            s.fill(color)
            screen.blit(s, (self.x - self.width // 2, self.y - self.height + row))

        # 竖线
        for col in range(0, self.width, 3):
            color = (200, 200, 200, 30)
            s = pygame.Surface((1, self.height), pygame.SRCALPHA)
            s.fill(color)
            screen.blit(s, (self.x - self.width // 2 + col, self.y - self.height))

        # 顶部白边
        pygame.draw.rect(screen, WHITE,
                         (self.x - self.width // 2 - 4, self.y - self.height - 2,
                          self.width + 8, 4), border_radius=2)


class Game:
    """游戏主类"""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("🏐 排球对战 - Volleyball")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 28)

        # 游戏模式
        self.mode = 'menu'  # menu, playing, point, win
        self.difficulty = 'normal'  # easy, normal, hard
        self.game_mode = '1p'  # 1p or 2p

        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        self.ball = Ball()
        self.net = Net()

        self.player1 = Player(SCREEN_WIDTH // 4, SCREEN_HEIGHT - 100, 'left')
        self.player2 = Player(SCREEN_WIDTH * 3 // 4, SCREEN_HEIGHT - 100, 'right',
                              is_ai=(self.game_mode == '1p'))

        self.player1.score = 0
        self.player2.score = 0
        self.player1.win = False
        self.player2.win = False

        self.serving = 'left'  # 当前发球方
        self.serve_timer = 60  # 发球等待帧
        self.point_timer = 0
        self.point_scored = None  # 得分方
        self.ball_in_play = False
        self.bump_sound = self._create_sound(440, 0.1)
        self.score_sound = self._create_sound(880, 0.2)
        self.wall_sound = self._create_sound(220, 0.08)

    def _create_sound(self, freq, duration):
        """生成简单音效"""
        try:
            sample_rate = 22050
            n_samples = int(sample_rate * duration)
            buf = pygame.sndarray.make_sound(
                [[int(127 * math.sin(2 * math.pi * freq * t / sample_rate) *
                      max(0, 1 - t / (sample_rate * duration)))
                  for _ in range(2)]
                 for t in range(n_samples)]
            )
            return buf
        except Exception:
            return None

    def handle_menu(self, event):
        """菜单输入处理"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.game_mode = '1p'
                self.mode = 'playing'
                self.reset_game()
            elif event.key == pygame.K_2:
                self.game_mode = '2p'
                self.mode = 'playing'
                self.reset_game()
            elif event.key == pygame.K_ESCAPE:
                return False
        return True

    def handle_playing(self, event):
        """游戏输入处理"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.mode = 'menu'
                return True
            if event.key == pygame.K_r:
                self.reset_game()
                self.mode = 'playing'
                return True

        # 玩家1 控制 (WASD + Q)
        keys = pygame.key.get_pressed()
        p1 = self.player1

        if keys[pygame.K_a]:
            p1.move_left()
        elif keys[pygame.K_d]:
            p1.move_right()
        else:
            p1.vx_before = p1.vx if hasattr(p1, 'vx_before') else 0
        if keys[pygame.K_w]:
            p1.jump()

        if not keys[pygame.K_a] and not keys[pygame.K_d]:
            pass  # friction handles it

        if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
            if self.ball_in_play and p1.can_spike():
                self._hit_ball(p1)
            elif not self.ball_in_play and self.serving == 'left':
                self._serve(p1)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            p1.move_left()
        elif keys[pygame.K_d]:
            p1.move_right()
        else:
            p1.vx *= 0.85

        if keys[pygame.K_w]:
            p1.jump()

        # 玩家2 控制 (方向键 + /)
        if not self.player2.is_ai:
            p2 = self.player2
            if keys[pygame.K_LEFT]:
                p2.move_left()
            elif keys[pygame.K_RIGHT]:
                p2.move_right()
            else:
                p2.vx *= 0.85

            if keys[pygame.K_UP]:
                p2.jump()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_SLASH:
                if self.ball_in_play and p2.can_spike():
                    self._hit_ball(p2)
                elif not self.ball_in_play and self.serving == 'right':
                    self._serve(p2)

        return True

    def update_ai(self):
        """AI 控制玩家2"""
        if not self.player2.is_ai:
            return

        p2 = self.player2
        ball = self.ball

        if not ball.active:
            return

        # 预测球的目标位置
        target_x = ball.x
        target_y = ball.y

        # 如果球在对方半场，AI回到中场
        if ball.side == 'left':
            target_x = SCREEN_WIDTH * 3 // 4
            if abs(p2.x - target_x) > 20:
                if p2.x < target_x:
                    p2.move_right_ai()
                else:
                    p2.move_left_ai()
            else:
                p2.stop_x()
            return

        # 球在己方半场 - 追逐球
        # 水平移动
        dx = ball.x - p2.x
        if abs(dx) > 30:
            if dx > 0:
                p2.move_right_ai()
            else:
                p2.move_left_ai()
        else:
            p2.stop_x()

        # 垂直移动 - 跳起击球
        if ball.y < SCREEN_HEIGHT // 2 and abs(dx) < 60:
            p2.jump()

        # 击球
        if p2.can_spike() and abs(dx) < 40 and ball.y > p2.y - 60 and ball.y < p2.y + 20:
            self._hit_ball(p2)

    def _serve(self, player):
        """发球"""
        self.ball.active = True
        self.ball_in_play = True
        self.ball.x = player.x + player.facing * 20
        self.ball.y = player.y - 30
        direction = 1 if player.side == 'left' else -1
        self.ball.vx = direction * random.uniform(3, 5)
        self.ball.vy = random.uniform(-7, -5)
        self.ball.last_hitter = player
        self.ball.touch_count = 0

    def _hit_ball(self, player):
        """击球逻辑"""
        if not self.ball.active:
            return

        # 计算球的方向
        direction = 1 if player.side == 'left' else -1

        # 基础击球速度
        base_speed = random.uniform(5, 8)

        # 如果球在网附近，用力扣杀
        if abs(player.x - SCREEN_WIDTH // 2) < 100:
            self.ball.vx = direction * random.uniform(6, 10)
            self.ball.vy = random.uniform(-9, -6)
        else:
            self.ball.vx = direction * base_speed
            self.ball.vy = random.uniform(-8, -5)

        # 检查是否在球附近
        dx = self.ball.x - player.x
        dy = self.ball.y - player.y
        dist = math.sqrt(dx ** 2 + dy ** 2)

        if dist < 50:
            # 根据击球点调整球的方向
            hit_angle = math.atan2(dy, dx)
            self.ball.vx = direction * abs(math.cos(hit_angle) * 8)
            self.ball.vy = min(-3, math.sin(hit_angle) * 6 - 3)

        # 防止球水平飞过网
        if abs(self.ball.vx) < 2:
            self.ball.vx = direction * 3

        # 重置触球计数
        self.ball.touch_count = 1
        self.ball.last_hitter = player
        player.spike_cooldown = SPIKE_COOLDOWN

        if self.bump_sound:
            self.bump_sound.play()

    def check_collisions(self):
        """碰撞检测"""
        if not self.ball.active:
            return

        ball = self.ball
        p1 = self.player1
        p2 = self.player2

        # 球网碰撞
        net_rect = pygame.Rect(self.net.x - self.net.width // 2,
                               self.net.y - self.net.height,
                               self.net.width, self.net.height)
        ball_rect = pygame.Rect(ball.x - ball.radius, ball.y - ball.radius,
                                ball.radius * 2, ball.radius * 2)

        if ball_rect.colliderect(net_rect):
            # 球碰到网 - 判断落在哪一侧
            if ball.vx > 0 and ball.side == 'left':
                # 从左侧撞网，得分给右侧
                self._score_point('right')
            elif ball.vx < 0 and ball.side == 'right':
                # 从右侧撞网，得分给左侧
                self._score_point('left')
            else:
                # 球在网内，反弹回去
                ball.vx = -ball.vx * 0.5
                ball.x = self.net.x + (-1 if ball.vx < 0 else 1) * (self.net.width // 2 + ball.radius + 2)

        # 球员与球碰撞
        for player in [p1, p2]:
            if player == ball.last_hitter:
                continue  # 同一玩家不能连续触球

            if ball.touch_count >= MAX_TOUCHES:
                # 超过触球次数，球权给对方
                if ball.side != player.side:
                    continue

            # 矩形碰撞检测
            player_rect = player.get_rect()
            if ball_rect.colliderect(player_rect):
                # 球碰到球员
                if player.can_spike() or abs(ball.vy) > 2:
                    self._hit_ball(player)
                    ball.touch_count += 1
                    ball.last_hitter = player

        # 球落地检测
        if ball.y + ball.radius > SCREEN_HEIGHT - 20:
            if ball.is_on_left_side():
                # 球落在左侧 => 右侧得分
                self._score_point('right')
            else:
                self._score_point('left')

    def _score_point(self, winner_side):
        """得分处理"""
        if self.point_timer > 0:
            return

        self.ball.active = False
        self.ball_in_play = False
        self.point_timer = 120  # 2秒展示
        self.point_scored = winner_side

        if winner_side == 'left':
            self.player1.score += 1
            self.serving = 'left'
        else:
            self.player2.score += 1
            self.serving = 'right'

        if self.score_sound:
            self.score_sound.play()

        # 检查是否胜利
        if self.player1.score >= MAX_SCORE:
            self.player1.win = True
            self.mode = 'win'
        elif self.player2.score >= MAX_SCORE:
            self.player2.win = True
            self.mode = 'win'

    def draw_court(self, screen):
        """绘制球场"""
        # 背景
        screen.fill(BLACK)

        # 场地
        court_rect = pygame.Rect(0, SCREEN_HEIGHT - 250,
                                 SCREEN_WIDTH, 250)
        pygame.draw.rect(screen, COURT_COLOR, court_rect)

        # 地板
        floor_rect = pygame.Rect(0, SCREEN_HEIGHT - 20,
                                 SCREEN_WIDTH, 20)
        pygame.draw.rect(screen, FLOOR_COLOR, floor_rect)
        pygame.draw.line(screen, (90, 100, 120),
                         (0, SCREEN_HEIGHT - 20),
                         (SCREEN_WIDTH, SCREEN_HEIGHT - 20), 2)

        # 中线
        pygame.draw.line(screen, GRAY,
                         (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 250),
                         (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20), 2)

        # 边线
        pygame.draw.rect(screen, GRAY,
                         (0, SCREEN_HEIGHT - 250, SCREEN_WIDTH, 250), 2)

        # 发球区标记
        if self.serving == 'left':
            pygame.draw.rect(screen, BLUE,
                             (20, SCREEN_HEIGHT - 240, 10, 10), border_radius=2)
        else:
            pygame.draw.rect(screen, RED,
                             (SCREEN_WIDTH - 30, SCREEN_HEIGHT - 240, 10, 10), border_radius=2)

    def draw_hud(self, screen):
        """绘制界面信息"""
        # 分数显示
        score_y = 40

        # 玩家1 分数
        p1_color = BLUE if self.player1.score > 0 else GRAY
        p1_text = f"{self.player1.score}"
        p1_surf = self.font_large.render(p1_text, True, p1_color)
        p1_rect = p1_surf.get_rect(center=(SCREEN_WIDTH // 4, score_y))
        screen.blit(p1_surf, p1_rect)

        # 玩家标签
        p1_label = self.font_small.render("玩家1", True, BLUE)
        screen.blit(p1_label, (SCREEN_WIDTH // 4 - 30, 10))

        # VS
        vs_surf = self.font_medium.render("VS", True, GRAY)
        vs_rect = vs_surf.get_rect(center=(SCREEN_WIDTH // 2, score_y))
        screen.blit(vs_surf, vs_rect)

        # 玩家2 分数
        p2_color = RED if self.player2.score > 0 else GRAY
        p2_text = f"{self.player2.score}"
        p2_surf = self.font_large.render(p2_text, True, p2_color)
        p2_rect = p2_surf.get_rect(center=(SCREEN_WIDTH * 3 // 4, score_y))
        screen.blit(p2_surf, p2_rect)

        p2_label_text = "AI" if self.player2.is_ai else "玩家2"
        p2_label = self.font_small.render(p2_label_text, True, RED)
        screen.blit(p2_label, (SCREEN_WIDTH * 3 // 4 - 30, 10))

        # 触球次数提示
        if self.ball.active:
            side_name = "蓝方" if self.ball.side == 'left' else "红方"
            touch_text = f"{side_name} 触球: {self.ball.touch_count}/{MAX_TOUCHES}"
            touch_surf = self.font_small.render(touch_text, True, WHITE)
            screen.blit(touch_surf, (SCREEN_WIDTH // 2 - 60, 80))

        # 操作提示
        if self.mode == 'playing' and not self.ball_in_play:
            serve_text = "按 Q 或 / 发球"
            serve_surf = self.font_small.render(serve_text, True, YELLOW)
            serve_rect = serve_surf.get_rect(center=(SCREEN_WIDTH // 2, 120))
            screen.blit(serve_surf, serve_rect)

    def draw_win_screen(self, screen):
        """绘制胜利画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        if self.player1.win:
            winner_text = "🎉 玩家1 获胜! 🎉"
            winner_color = BLUE
        else:
            winner_text = "🎉 玩家2 获胜! 🎉"
            winner_color = RED

        win_surf = self.font_large.render(winner_text, True, winner_color)
        win_rect = win_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        screen.blit(win_surf, win_rect)

        score_text = f"{self.player1.score} - {self.player2.score}"
        score_surf = self.font_medium.render(score_text, True, WHITE)
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        screen.blit(score_surf, score_rect)

        restart_text = "按 R 重新开始  |  按 ESC 返回菜单"
        restart_surf = self.font_small.render(restart_text, True, GRAY)
        restart_rect = restart_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        screen.blit(restart_surf, restart_rect)

    def draw_menu(self, screen):
        """绘制主菜单"""
        screen.fill(BLACK)

        # 标题
        title_surf = self.font_large.render("排 球 对 战", True, WHITE)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 120))
        screen.blit(title_surf, title_rect)

        # 副标题
        sub_surf = self.font_small.render("Volleyball", True, GRAY)
        sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 170))
        screen.blit(sub_surf, sub_rect)

        # 选项
        opt1_surf = self.font_medium.render("按 [1] 单人模式 (vs AI)", True, BLUE)
        opt1_rect = opt1_surf.get_rect(center=(SCREEN_WIDTH // 2, 280))
        screen.blit(opt1_surf, opt1_rect)

        opt2_surf = self.font_medium.render("按 [2] 双人模式", True, RED)
        opt2_rect = opt2_surf.get_rect(center=(SCREEN_WIDTH // 2, 340))
        screen.blit(opt2_surf, opt2_rect)

        # 操作说明
        controls = [
            "玩家1: W/A/S/D 移动, Q 击球",
            "玩家2: ↑/←/↓/→ 移动, / 击球",
            "先到 5 分获胜!",
            "ESC 返回菜单, R 重新开始"
        ]
        for i, ctrl in enumerate(controls):
            ctrl_surf = self.font_small.render(ctrl, True, GRAY)
            ctrl_rect = ctrl_surf.get_rect(center=(SCREEN_WIDTH // 2, 430 + i * 30))
            screen.blit(ctrl_surf, ctrl_rect)

        # 装饰球
        pygame.draw.circle(screen, YELLOW,
                           (SCREEN_WIDTH // 2, 540), 15)
        pygame.draw.circle(screen, (255, 255, 200),
                           (SCREEN_WIDTH // 2, 540), 12)

    def run(self):
        """主循环"""
        running = True
        while running:
            dt = self.clock.tick(FPS)

            # 输入处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if self.mode == 'menu':
                    running = self.handle_menu(event)
                elif self.mode == 'playing':
                    running = self.handle_playing(event)
                elif self.mode == 'win':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            self.reset_game()
                            self.mode = 'playing'
                        elif event.key == pygame.K_ESCAPE:
                            self.mode = 'menu'

            # 更新逻辑
            if self.mode == 'playing':
                self.player1.update()
                self.player2.update()

                if self.ball.active:
                    self.ball.update()
                    self.check_collisions()
                elif self.point_timer > 0:
                    self.point_timer -= 1
                    if self.point_timer <= 0:
                        self.point_timer = 0
                        self.point_scored = None
                        self.serve_timer = 30

                # AI 更新
                self.update_ai()

                # 发球
                if not self.ball_in_play and self.point_timer <= 0:
                    if self.serve_timer > 0:
                        self.serve_timer -= 1
                    else:
                        # 自动重置球到发球方
                        serve_player = self.player1 if self.serving == 'left' else self.player2
                        self.ball.reset(1 if self.serving == 'left' else -1)
                        self.ball.active = False
                        self.ball.x = serve_player.x + serve_player.facing * 20
                        self.ball.y = serve_player.y - 40

            # 绘制
            if self.mode == 'menu':
                self.draw_menu(self.screen)
            elif self.mode == 'playing' or self.mode == 'win':
                self.draw_court(self.screen)
                self.net.draw(self.screen)
                self.player1.draw(self.screen)
                self.player2.draw(self.screen)
                self.ball.draw(self.screen)
                self.draw_hud(self.screen)

                if self.mode == 'win':
                    self.draw_win_screen(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ==================== 启动游戏 ====================
if __name__ == "__main__":
    game = Game()
    game.run()