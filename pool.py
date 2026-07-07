"""
台球 (Pool/Billiards) - 经典美式台球
- 鼠标瞄准：移动鼠标调整击球方向
- 点击拖拽蓄力，松开击球
- 15 颗彩色球按三角形排列，白球为母球
- 真实 2D 物理：碰撞、摩擦、反弹
- 进球计分，所有球停下后轮到你继续出杆

操作方式：
- 移动鼠标瞄准
- 按住鼠标左键蓄力（拖拽越远力量越大）
- 松开鼠标左键击球
- R 键重新开始
"""

import pygame
import math
import random

# 初始化
pygame.init()
WIDTH, HEIGHT = 900, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("台球 Pool - 美式台球")
clock = pygame.time.Clock()
font = pygame.font.SysFont("simhei", 22)
big_font = pygame.font.SysFont("simhei", 36)

# 颜色
GREEN = (0, 120, 40)
DARK_GREEN = (0, 90, 30)
BROWN = (120, 70, 30)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 220, 0)
BLUE = (0, 50, 255)
RED = (220, 30, 30)
PURPLE = (130, 0, 200)
ORANGE = (255, 150, 0)
DARK_BLUE = (0, 30, 120)
PINK = (255, 80, 120)
LIGHT_BLUE = (80, 180, 255)
LIGHT_GREEN = (50, 200, 50)
MAROON = (180, 50, 80)
GRAY = (180, 180, 180)
BEIGE = (220, 200, 160)

# 桌面参数
TABLE_LEFT = 100
TABLE_TOP = 50
TABLE_WIDTH = 700
TABLE_HEIGHT = 350
TABLE_RIGHT = TABLE_LEFT + TABLE_WIDTH
TABLE_BOTTOM = TABLE_TOP + TABLE_HEIGHT
POCKET_RADIUS = 22
BALL_RADIUS = 11
FRICTION = 0.985
MIN_SPEED = 0.5

# 球洞位置 (6个)
POCKETS = [
    (TABLE_LEFT, TABLE_TOP),                    # 左上
    (TABLE_LEFT + TABLE_WIDTH // 2, TABLE_TOP - 5),  # 上中
    (TABLE_RIGHT, TABLE_TOP),                   # 右上
    (TABLE_LEFT, TABLE_BOTTOM),                 # 左下
    (TABLE_LEFT + TABLE_WIDTH // 2, TABLE_BOTTOM + 5), # 下中
    (TABLE_RIGHT, TABLE_BOTTOM),                # 右下
]

# 球颜色映射 (1-15号球)
BALL_COLORS = {
    1: (YELLOW, WHITE),    # 1号 黄色 (纯色)
    2: (BLUE, WHITE),      # 2号 蓝色 (纯色)
    3: (RED, WHITE),       # 3号 红色 (纯色)
    4: (PURPLE, WHITE),    # 4号 紫色 (纯色)
    5: (ORANGE, WHITE),    # 5号 橙色 (纯色)
    6: (DARK_BLUE, WHITE), # 6号 深蓝 (纯色)
    7: (MAROON, WHITE),    # 7号 栗色 (纯色)
    8: (BLACK, WHITE),     # 8号 黑色 (纯色)
    9: (YELLOW, WHITE),    # 9号 黄色 (条纹)
    10: (BLUE, WHITE),     # 10号 蓝色 (条纹)
    11: (RED, WHITE),      # 11号 红色 (条纹)
    12: (PURPLE, WHITE),   # 12号 紫色 (条纹)
    13: (ORANGE, WHITE),   # 13号 橙色 (条纹)
    14: (DARK_BLUE, WHITE),# 14号 深蓝 (条纹)
    15: (MAROON, WHITE),   # 15号 栗色 (条纹)
}

# ============ 球类 ============
class Ball:
    def __init__(self, number, x, y):
        self.number = number
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.radius = BALL_RADIUS
        self.color = BALL_COLORS.get(number, (WHITE, WHITE))[0]
        self.mass = 1.0

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= FRICTION
        self.vy *= FRICTION
        if abs(self.vx) < MIN_SPEED:
            self.vx = 0
        if abs(self.vy) < MIN_SPEED:
            self.vy = 0

    def speed(self):
        return math.hypot(self.vx, self.vy)

    def draw(self, surface):
        # 球体阴影
        pygame.draw.circle(surface, (30, 30, 30), (int(self.x) + 2, int(self.y) + 2), self.radius)
        # 球体
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 1)
        # 球号
        if self.number == 0:
            return  # 母球不显示号码
        # 白底圆
        inner_r = self.radius - 3
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), inner_r)
        # 号码文字
        num_text = font.render(str(self.number), True, BLACK)
        text_rect = num_text.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(num_text, text_rect)
        # 条纹球标志（9-15号加条纹线）
        if 9 <= self.number <= 15:
            pygame.draw.line(surface, WHITE,
                           (int(self.x - self.radius), int(self.y)),
                           (int(self.x + self.radius), int(self.y)), 2)
            pygame.draw.line(surface, self.color,
                           (int(self.x - self.radius), int(self.y - 4)),
                           (int(self.x + self.radius), int(self.y - 4)), 2)
            pygame.draw.line(surface, self.color,
                           (int(self.x - self.radius), int(self.y + 4)),
                           (int(self.x + self.radius), int(self.y + 4)), 2)


# ============ 物理引擎 ============
def ball_ball_collision(b1, b2):
    """两球弹性碰撞"""
    dx = b2.x - b1.x
    dy = b2.y - b1.y
    dist = math.hypot(dx, dy)
    min_dist = b1.radius + b2.radius
    if dist == 0 or dist > min_dist:
        return False

    # 分离球
    overlap = min_dist - dist
    nx = dx / dist
    ny = dy / dist
    b1.x -= nx * overlap / 2
    b1.y -= ny * overlap / 2
    b2.x += nx * overlap / 2
    b2.y += ny * overlap / 2

    # 弹性碰撞
    dvx = b1.vx - b2.vx
    dvy = b1.vy - b2.vy
    dot = dvx * nx + dvy * ny
    if dot > 0:
        return True  # 正在远离

    # 质量相同，速度交换法向分量
    impulse = dot
    b1.vx -= impulse * nx
    b1.vy -= impulse * ny
    b2.vx += impulse * nx
    b2.vy += impulse * ny
    return True


def ball_wall_collision(ball):
    """球与桌壁碰撞"""
    # 左右壁
    if ball.x - ball.radius < TABLE_LEFT:
        ball.x = TABLE_LEFT + ball.radius
        ball.vx = -ball.vx * 0.8
    elif ball.x + ball.radius > TABLE_RIGHT:
        ball.x = TABLE_RIGHT - ball.radius
        ball.vx = -ball.vx * 0.8
    # 上下壁
    if ball.y - ball.radius < TABLE_TOP:
        ball.y = TABLE_TOP + ball.radius
        ball.vy = -ball.vy * 0.8
    elif ball.y + ball.radius > TABLE_BOTTOM:
        ball.y = TABLE_BOTTOM - ball.radius
        ball.vy = -ball.vy * 0.8


def check_pocket(ball):
    """检查球是否进洞"""
    for px, py in POCKETS:
        dist = math.hypot(ball.x - px, ball.y - py)
        if dist < POCKET_RADIUS * 0.7:
            return True
    return False


def all_balls_stopped(balls):
    """所有球是否都静止"""
    for b in balls:
        if b.speed() > MIN_SPEED:
            return False
    return True


# ============ 游戏主类 ============
class PoolGame:
    def __init__(self):
        self.reset()

    def reset(self):
        """重置游戏"""
        self.balls = []
        self.pocketed = []  # 已进洞的球
        self.cue_ball = Ball(0, TABLE_LEFT + 180, TABLE_TOP + TABLE_HEIGHT // 2)
        self.balls.append(self.cue_ball)

        # 三角形排列 15 颗球
        start_x = TABLE_LEFT + 500
        start_y = TABLE_TOP + TABLE_HEIGHT // 2
        numbers = list(range(1, 16))
        # 8号球在中心
        numbers[4], numbers[7] = numbers[7], numbers[4]
        idx = 0
        for row in range(5):
            for col in range(row + 1):
                x = start_x + row * (BALL_RADIUS * 2 + 2)
                y = start_y - row * BALL_RADIUS + col * (BALL_RADIUS * 2 + 2)
                ball = Ball(numbers[idx], x, y)
                self.balls.append(ball)
                idx += 1

        self.aiming = False
        self.aim_start = None
        self.aim_end = None
        self.power = 0
        self.message = ""
        self.message_timer = 0
        self.shoot_count = 0
        self.pocketed_balls = []  # 记录进球号码
        self.foul = False

    def get_ball_at(self, pos):
        """获取指定位置的球"""
        for b in self.balls:
            if b.number != 0:  # 非母球
                dx = b.x - pos[0]
                dy = b.y - pos[1]
                if math.hypot(dx, dy) < b.radius + 5:
                    return b
        return None

    def shoot(self, dx, dy, power):
        """击球"""
        if not all_balls_stopped(self.balls):
            return
        self.cue_ball.vx = dx * power * 0.03
        self.cue_ball.vy = dy * power * 0.03
        self.shoot_count += 1

    def update(self):
        """更新物理"""
        if all_balls_stopped(self.balls):
            return

        # 更新所有球
        for ball in self.balls[:]:
            ball.update()
            ball_wall_collision(ball)

            # 检查进洞
            if check_pocket(ball):
                if ball.number == 0:
                    # 母球进洞，犯规
                    self.message = "犯规！母球进洞！"
                    self.message_timer = 120
                    self.foul = True
                    # 母球回到发球区
                    ball.x = TABLE_LEFT + 180
                    ball.y = TABLE_TOP + TABLE_HEIGHT // 2
                    ball.vx = 0
                    ball.vy = 0
                else:
                    self.pocketed.append(ball.number)
                    self.balls.remove(ball)
                    self.pocketed_balls.append(ball.number)

        # 球与球碰撞
        for i in range(len(self.balls)):
            for j in range(i + 1, len(self.balls)):
                ball_ball_collision(self.balls[i], self.balls[j])

    def get_cue_angle(self):
        """获取瞄准角度"""
        if self.aim_end:
            dx = self.cue_ball.x - self.aim_end[0]
            dy = self.cue_ball.y - self.aim_end[1]
        else:
            mx, my = pygame.mouse.get_pos()
            dx = self.cue_ball.x - mx
            dy = self.cue_ball.y - my
        if dx == 0 and dy == 0:
            return 0
        return math.atan2(dy, dx)

    def draw(self, surface):
        """绘制游戏"""
        # 背景
        surface.fill(BROWN)

        # 桌面外框
        pygame.draw.rect(surface, DARK_GREEN,
                        (TABLE_LEFT - 15, TABLE_TOP - 15,
                         TABLE_WIDTH + 30, TABLE_HEIGHT + 30), 5)
        # 桌面
        pygame.draw.rect(surface, GREEN,
                        (TABLE_LEFT, TABLE_TOP, TABLE_WIDTH, TABLE_HEIGHT))
        # 桌面纹理 (细线)
        for i in range(0, TABLE_WIDTH, 20):
            pygame.draw.line(surface, DARK_GREEN,
                           (TABLE_LEFT + i, TABLE_TOP),
                           (TABLE_LEFT + i, TABLE_BOTTOM), 1)
        for i in range(0, TABLE_HEIGHT, 20):
            pygame.draw.line(surface, DARK_GREEN,
                           (TABLE_LEFT, TABLE_TOP + i),
                           (TABLE_RIGHT, TABLE_TOP + i), 1)

        # 发球线
        pygame.draw.line(surface, (0, 60, 20), (TABLE_LEFT + 250, TABLE_TOP),
                        (TABLE_LEFT + 250, TABLE_BOTTOM), 1)

        # 球洞
        for px, py in POCKETS:
            pygame.draw.circle(surface, (30, 30, 30), (px, py), POCKET_RADIUS)
            pygame.draw.circle(surface, (60, 60, 60), (px, py), POCKET_RADIUS - 3)

        # 球
        for ball in self.balls:
            ball.draw(surface)

        # 瞄准线和球杆
        if all_balls_stopped(self.balls) and not self.foul:
            angle = self.get_cue_angle()
            cue_length = 200

            if self.aim_end:
                mx, my = self.aim_end
            else:
                mx, my = pygame.mouse.get_pos()

            # 球杆方向
            dir_x = math.cos(angle)
            dir_y = math.sin(angle)

            # 球杆起始（母球后方）
            start_x = self.cue_ball.x + dir_x * self.cue_ball.radius
            start_y = self.cue_ball.y + dir_y * self.cue_ball.radius

            # 蓄力时球杆缩短
            if self.aiming and self.aim_start:
                aim_dx = mx - self.aim_start[0]
                aim_dy = my - self.aim_start[1]
                power = min(math.hypot(aim_dx, aim_dy), 200)
                cue_length = 200 - power * 0.5
                self.power = power

            end_x = start_x + dir_x * cue_length
            end_y = start_y + dir_y * cue_length

            # 球杆 (棕色杆 + 白色尖端)
            pygame.draw.line(surface, (200, 160, 100),
                           (start_x, start_y), (end_x, end_y), 6)
            # 球杆尖端(白色)
            tip_x = start_x + dir_x * 12
            tip_y = start_y + dir_y * 12
            pygame.draw.line(surface, WHITE,
                           (start_x, start_y), (tip_x, tip_y), 6)

            # 辅助瞄准线（虚线）
            aim_len = 300
            ax = self.cue_ball.x + dir_x * (self.cue_ball.radius + 5)
            ay = self.cue_ball.y + dir_y * (self.cue_ball.radius + 5)
            for step in range(5, int(aim_len), 20):
                alpha = 0.5 if (step // 20) % 2 == 0 else 0.3
                px1 = ax + dir_x * step
                py1 = ay + dir_y * step
                px2 = ax + dir_x * (step + 10)
                py2 = ay + dir_y * (step + 10)
                pygame.draw.line(surface, (255, 255, 255, int(255 * alpha)),
                               (int(px1), int(py1)), (int(px2), int(py2)), 1)

            # 力量条
            if self.aiming:
                bar_x, bar_y = TABLE_RIGHT + 30, TABLE_TOP + 50
                bar_w, bar_h = 20, 200
                pygame.draw.rect(surface, GRAY, (bar_x, bar_y, bar_w, bar_h))
                fill_h = int((self.power / 200) * bar_h)
                color = (255, 0, 0) if self.power > 150 else (255, 255, 0) if self.power > 80 else (0, 255, 0)
                pygame.draw.rect(surface, color,
                               (bar_x, bar_y + bar_h - fill_h, bar_w, fill_h))
                pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_w, bar_h), 2)

        # 已进球
        if self.pocketed:
            pocket_text = font.render("已进球: " + ", ".join(str(n) for n in sorted(self.pocketed)), True, WHITE)
            surface.blit(pocket_text, (TABLE_LEFT, TABLE_BOTTOM + 20))

        # 统计
        stats_text = font.render(f"击球次数: {self.shoot_count}  剩余球: {len(self.balls) - 1}", True, WHITE)
        surface.blit(stats_text, (TABLE_LEFT, TABLE_BOTTOM + 45))

        # 消息
        if self.message_timer > 0:
            msg_surf = big_font.render(self.message, True, RED)
            msg_rect = msg_surf.get_rect(center=(WIDTH // 2, TABLE_TOP - 30))
            surface.blit(msg_surf, msg_rect)
            self.message_timer -= 1

        # 操作提示
        tips = font.render("鼠标移动瞄准 | 按住左键蓄力 | 松开击球 | R键重开", True, BEIGE)
        surface.blit(tips, (WIDTH // 2 - tips.get_width() // 2, HEIGHT - 30))

    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.reset()
                return

        if not all_balls_stopped(self.balls):
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.aiming = True
            self.aim_start = event.pos
            self.aim_end = event.pos

        elif event.type == pygame.MOUSEMOTION and self.aiming:
            self.aim_end = event.pos

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.aiming:
            self.aiming = False
            if self.aim_start:
                dx = self.aim_start[0] - event.pos[0]
                dy = self.aim_start[1] - event.pos[1]
                power = min(math.hypot(dx, dy), 200)
                if power > 10:
                    angle = math.atan2(dy, dx)
                    self.shoot(math.cos(angle), math.sin(angle), power)
            self.aim_start = None
            self.aim_end = None
            self.power = 0
            self.foul = False


# ============ 主循环 ============
def main():
    game = PoolGame()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_event(event)

        game.update()
        game.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()