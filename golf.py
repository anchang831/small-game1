"""
高尔夫 (Golf) - 2D 物理高尔夫游戏
===============================
操作说明：
- 鼠标移动调整击球方向（瞄准线）
- 按住鼠标左键蓄力（力量条上升）
- 松开鼠标左键击球
- 球进洞后自动进入下一洞
- 共9洞，目标是用最少杆数完成

游戏特性：
- 真实物理：摩擦力、空气阻力、弹跳
- 风力系统（随机变化）
- 多种地形：球道、长草、沙坑、水域
- 树木障碍物
- 标准杆计分
"""

import pygame
import math
import random
import sys

# ==================== 初始化 ====================
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("高尔夫 Golf")
clock = pygame.time.Clock()
font_large = pygame.font.SysFont("simhei", 36, bold=True)
font_mid = pygame.font.SysFont("simhei", 24)
font_small = pygame.font.SysFont("simhei", 18)
FPS = 60

# ==================== 颜色 ====================
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
FAIRWAY = (80, 180, 60)
ROUGH = (60, 140, 40)
SAND = (220, 200, 150)
WATER = (30, 100, 200)
SKY = (135, 206, 235)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (180, 0, 180)
HOLE_COLOR = (0, 0, 0)
FLAG_COLOR = (255, 0, 0)

# ==================== 物理常量 ====================
GRAVITY = 0  # 俯视图，无重力
FRICTION_FAIRWAY = 0.985
FRICTION_ROUGH = 0.97
FRICTION_SAND = 0.94
FRICTION_WATER = 0.90
AIR_RESISTANCE = 0.998
BOUNCE_FACTOR = 0.5
HOLE_RADIUS = 15
BALL_RADIUS = 6

# ==================== 关卡定义 ====================
# 每个关卡: (起点x, 起点y, 球洞x, 球洞y, 标准杆, 障碍物列表, 风)
# 障碍物: (type, x, y, w, h) type: 'tree', 'sand', 'water', 'rough'
HOLES = [
    {
        "start": (150, 350),
        "hole": (850, 300),
        "par": 4,
        "wind": (-2, 1),
        "obstacles": [
            ("tree", 350, 280, 30, 30),
            ("tree", 400, 380, 30, 30),
            ("sand", 500, 250, 100, 60),
            ("rough", 550, 380, 120, 50),
            ("tree", 650, 330, 30, 30),
        ],
    },
    {
        "start": (100, 100),
        "hole": (800, 500),
        "par": 5,
        "wind": (3, 0),
        "obstacles": [
            ("water", 300, 150, 200, 80),
            ("tree", 320, 300, 30, 30),
            ("tree", 280, 400, 30, 30),
            ("sand", 500, 350, 80, 80),
            ("tree", 600, 200, 30, 30),
            ("rough", 650, 400, 100, 50),
            ("tree", 720, 300, 30, 30),
        ],
    },
    {
        "start": (200, 500),
        "hole": (850, 150),
        "par": 3,
        "wind": (-1, -2),
        "obstacles": [
            ("water", 350, 300, 250, 100),
            ("tree", 400, 200, 30, 30),
            ("tree", 500, 450, 30, 30),
            ("sand", 600, 250, 60, 60),
            ("tree", 700, 380, 30, 30),
        ],
    },
    {
        "start": (100, 350),
        "hole": (900, 350),
        "par": 4,
        "wind": (0, 2),
        "obstacles": [
            ("rough", 250, 200, 50, 300),
            ("tree", 350, 280, 30, 30),
            ("tree", 400, 420, 30, 30),
            ("sand", 500, 300, 80, 100),
            ("tree", 550, 200, 30, 30),
            ("tree", 600, 450, 30, 30),
            ("water", 680, 280, 80, 140),
            ("tree", 780, 350, 30, 30),
        ],
    },
    {
        "start": (150, 150),
        "hole": (850, 550),
        "par": 5,
        "wind": (2, -1),
        "obstacles": [
            ("tree", 250, 300, 30, 30),
            ("tree", 300, 450, 30, 30),
            ("sand", 350, 200, 70, 70),
            ("water", 450, 350, 150, 60),
            ("tree", 500, 250, 30, 30),
            ("rough", 550, 450, 100, 60),
            ("tree", 650, 300, 30, 30),
            ("sand", 700, 400, 60, 60),
            ("tree", 750, 200, 30, 30),
        ],
    },
    {
        "start": (100, 500),
        "hole": (850, 200),
        "par": 3,
        "wind": (-3, 0),
        "obstacles": [
            ("water", 300, 250, 400, 100),
            ("tree", 350, 180, 30, 30),
            ("tree", 400, 420, 30, 30),
            ("tree", 550, 180, 30, 30),
            ("sand", 600, 350, 60, 60),
            ("tree", 700, 250, 30, 30),
        ],
    },
    {
        "start": (200, 300),
        "hole": (850, 400),
        "par": 4,
        "wind": (1, 1),
        "obstacles": [
            ("rough", 300, 150, 60, 400),
            ("tree", 350, 250, 30, 30),
            ("tree", 400, 400, 30, 30),
            ("sand", 500, 280, 80, 80),
            ("tree", 550, 200, 30, 30),
            ("water", 600, 350, 100, 60),
            ("tree", 680, 280, 30, 30),
            ("tree", 720, 450, 30, 30),
        ],
    },
    {
        "start": (150, 400),
        "hole": (850, 300),
        "par": 4,
        "wind": (-1, -1),
        "obstacles": [
            ("tree", 280, 250, 30, 30),
            ("sand", 320, 380, 80, 60),
            ("tree", 400, 320, 30, 30),
            ("water", 480, 200, 80, 200),
            ("tree", 500, 450, 30, 30),
            ("rough", 550, 280, 100, 60),
            ("tree", 650, 350, 30, 30),
            ("sand", 700, 200, 60, 60),
            ("tree", 750, 400, 30, 30),
        ],
    },
    {
        "start": (100, 350),
        "hole": (900, 350),
        "par": 5,
        "wind": (2, 2),
        "obstacles": [
            ("water", 250, 150, 60, 400),
            ("tree", 300, 280, 30, 30),
            ("tree", 350, 420, 30, 30),
            ("sand", 400, 200, 80, 60),
            ("tree", 450, 450, 30, 30),
            ("water", 500, 280, 60, 140),
            ("tree", 550, 200, 30, 30),
            ("rough", 600, 400, 100, 60),
            ("tree", 650, 300, 30, 30),
            ("sand", 700, 350, 80, 80),
            ("tree", 750, 250, 30, 30),
            ("tree", 800, 450, 30, 30),
        ],
    },
]


# ==================== 游戏状态 ====================
class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = BALL_RADIUS
        self.moving = False
        self.stuck = False  # 陷在沙坑/水里
        self.terrain = "fairway"  # fairway, rough, sand, water

    def update(self, wind):
        if not self.moving:
            return

        # 空气阻力
        self.vx *= AIR_RESISTANCE
        self.vy *= AIR_RESISTANCE

        # 风力影响
        self.vx += wind[0] * 0.02
        self.vy += wind[1] * 0.02

        # 地形摩擦力
        friction = FRICTION_FAIRWAY
        if self.terrain == "rough":
            friction = FRICTION_ROUGH
        elif self.terrain == "sand":
            friction = FRICTION_SAND
        elif self.terrain == "water":
            friction = FRICTION_WATER

        self.vx *= friction
        self.vy *= friction

        # 移动
        self.x += self.vx
        self.y += self.vy

        # 边界检测
        if self.x < 10:
            self.x = 10
            self.vx = -self.vx * BOUNCE_FACTOR
        elif self.x > SCREEN_WIDTH - 10:
            self.x = SCREEN_WIDTH - 10
            self.vx = -self.vx * BOUNCE_FACTOR
        if self.y < 10:
            self.y = 10
            self.vy = -self.vy * BOUNCE_FACTOR
        elif self.y > SCREEN_HEIGHT - 10:
            self.y = SCREEN_HEIGHT - 10
            self.vy = -self.vy * BOUNCE_FACTOR

        # 停止条件
        speed = math.hypot(self.vx, self.vy)
        if speed < 0.3:
            self.vx = 0
            self.vy = 0
            self.moving = False

    def check_obstacles(self, obstacles):
        """检测与障碍物的碰撞，设置地形类型"""
        self.terrain = "fairway"
        for obs in obstacles:
            typ, ox, oy, w, h = obs
            # 树 - 圆形碰撞
            if typ == "tree":
                cx, cy = ox + w // 2, oy + h // 2
                dist = math.hypot(self.x - cx, self.y - cy)
                r = max(w, h) // 2 + self.radius
                if dist < r:
                    # 弹开
                    angle = math.atan2(self.y - cy, self.x - cx)
                    overlap = r - dist
                    self.x += math.cos(angle) * overlap
                    self.y += math.sin(angle) * overlap
                    if self.moving:
                        speed = math.hypot(self.vx, self.vy)
                        if speed > 0.5:
                            self.vx = math.cos(angle) * speed * BOUNCE_FACTOR
                            self.vy = math.sin(angle) * speed * BOUNCE_FACTOR

            # 沙坑
            elif typ == "sand":
                if ox - 10 < self.x < ox + w + 10 and oy - 10 < self.y < oy + h + 10:
                    self.terrain = "sand"

            # 长草区
            elif typ == "rough":
                if ox - 5 < self.x < ox + w + 5 and oy - 5 < self.y < oy + h + 5:
                    self.terrain = "rough"

            # 水域
            elif typ == "water":
                if ox - 5 < self.x < ox + w + 5 and oy - 5 < self.y < oy + h + 5:
                    self.terrain = "water"
                    if self.moving:
                        # 水阻力大
                        self.vx *= 0.92
                        self.vy *= 0.92

    def draw(self, surf):
        # 阴影
        pygame.draw.circle(surf, (50, 50, 50, 100), (int(self.x) + 2, int(self.y) + 2), self.radius)
        # 球体
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, (200, 200, 200), (int(self.x), int(self.y)), self.radius - 1)


class Game:
    def __init__(self):
        self.current_hole = 0
        self.strokes = 0
        self.total_strokes = 0
        self.hole_scores = []
        self.ball = None
        self.aim_angle = 0
        self.power = 0
        self.charging = False
        self.aiming = True
        self.game_over = False
        self.message = ""
        self.message_timer = 0
        self.hole_finished = False
        self.wind_change_timer = 0
        self.reset_hole()

    def reset_hole(self):
        hole_data = HOLES[self.current_hole]
        self.ball = Ball(hole_data["start"][0], hole_data["start"][1])
        self.strokes = 0
        self.aim_angle = 0
        self.power = 0
        self.charging = False
        self.aiming = True
        self.hole_finished = False
        self.message = f"第 {self.current_hole + 1} 洞  标准杆 {hole_data['par']}"
        self.message_timer = 120
        self.wind_change_timer = 0

    def get_current_wind(self):
        hole_data = HOLES[self.current_hole]
        base_wind = hole_data["wind"]
        # 风有小幅随机波动
        t = self.wind_change_timer
        variation_x = math.sin(t * 0.01) * 0.5
        variation_y = math.cos(t * 0.013) * 0.5
        return (base_wind[0] + variation_x, base_wind[1] + variation_y)

    def shoot(self, power):
        """击球"""
        angle = self.aim_angle
        speed = power * 0.12
        self.ball.vx = math.cos(angle) * speed
        self.ball.vy = math.sin(angle) * speed
        self.ball.moving = True
        self.strokes += 1
        self.total_strokes += 1
        self.aiming = False
        self.charging = False

    def update(self):
        hole_data = HOLES[self.current_hole]
        self.wind_change_timer += 1
        wind = self.get_current_wind()

        # 消息计时
        if self.message_timer > 0:
            self.message_timer -= 1

        # 球运动更新
        self.ball.check_obstacles(hole_data["obstacles"])
        self.ball.update(wind)

        # 检测是否进洞
        hx, hy = hole_data["hole"]
        dist_to_hole = math.hypot(self.ball.x - hx, self.ball.y - hy)
        if not self.ball.moving and dist_to_hole < HOLE_RADIUS:
            if not self.hole_finished:
                self.hole_finished = True
                self.hole_scores.append(self.strokes)
                par = hole_data["par"]
                diff = self.strokes - par
                if diff == 0:
                    msg = "小鸟球 (Par)！"
                elif diff == -1:
                    msg = "小鸟球 (Birdie)！"
                elif diff == -2:
                    msg = "老鹰球 (Eagle)！"
                elif diff == 1:
                    msg = "柏忌 (Bogey)"
                elif diff >= 2:
                    msg = f"双柏忌 (+{diff})"
                elif diff <= -3:
                    msg = "信天翁 (Albatross)!!"
                else:
                    msg = f"完成！"
                self.message = f"进洞！{msg}  杆数: {self.strokes}"
                self.message_timer = 180
                # 自动进入下一洞
                if self.current_hole < len(HOLES) - 1:
                    self.current_hole += 1
                    self.reset_hole()
                else:
                    self.game_over = True

        # 球停止后可以重新瞄准
        if not self.ball.moving and not self.hole_finished and not self.game_over:
            # 检查球是否在水里（罚杆重置）
            if self.ball.terrain == "water":
                self.message = "球落水！罚一杆，重置位置"
                self.message_timer = 120
                # 罚杆并重置到上一位置
                self.total_strokes += 1
                self.strokes += 1
                self.ball.x = hole_data["start"][0]
                self.ball.y = hole_data["start"][1]
                self.ball.vx = 0
                self.ball.vy = 0
                self.ball.terrain = "fairway"
                self.aiming = True

            self.aiming = True

    def draw(self, surf):
        hole_data = HOLES[self.current_hole]
        wind = self.get_current_wind()

        # 绘制背景（草地）
        surf.fill(SKY)
        # 草地
        grass_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(surf, GREEN, grass_rect)
        # 球道纹理
        for i in range(0, SCREEN_WIDTH, 40):
            for j in range(0, SCREEN_HEIGHT, 40):
                shade = random.randint(-10, 10)
                c = (FAIRWAY[0] + shade, FAIRWAY[1] + shade, FAIRWAY[2] + shade)
                pygame.draw.rect(surf, c, (i, j, 40, 40), 1)

        # 绘制障碍物
        for obs in hole_data["obstacles"]:
            typ, ox, oy, w, h = obs
            if typ == "tree":
                # 树冠
                pygame.draw.circle(surf, DARK_GREEN, (ox + w // 2, oy + h // 2), max(w, h) // 2 + 5)
                pygame.draw.circle(surf, (0, 120, 0), (ox + w // 2, oy + h // 2), max(w, h) // 2)
                # 树干
                trunk_w = 6
                trunk_h = 12
                pygame.draw.rect(
                    surf,
                    BROWN,
                    (ox + w // 2 - trunk_w // 2, oy + h // 2 + max(w, h) // 4, trunk_w, trunk_h),
                )
            elif typ == "sand":
                pygame.draw.ellipse(surf, SAND, (ox, oy, w, h))
                # 沙坑纹理
                for _ in range(20):
                    sx = ox + random.randint(5, w - 5)
                    sy = oy + random.randint(5, h - 5)
                    pygame.draw.circle(surf, (200, 180, 140), (sx, sy), 2)
            elif typ == "rough":
                pygame.draw.rect(surf, ROUGH, (ox, oy, w, h))
                for _ in range(30):
                    rx = ox + random.randint(2, w - 2)
                    ry = oy + random.randint(2, h - 2)
                    pygame.draw.line(surf, (50, 120, 30), (rx, ry), (rx, ry + 6), 2)
            elif typ == "water":
                pygame.draw.ellipse(surf, WATER, (ox, oy, w, h))
                # 水波纹
                for i in range(3):
                    wy = oy + h // 4 + i * h // 4
                    for wx in range(ox + 10, ox + w - 10, 20):
                        offset = math.sin((wx + self.wind_change_timer * 2) * 0.05) * 3
                        pygame.draw.arc(
                            surf, (60, 140, 230), (wx - 10, wy + offset - 5, 20, 10), 0, math.pi, 2
                        )

        # 绘制球洞
        hx, hy = hole_data["hole"]
        # 洞周围标记
        pygame.draw.circle(surf, (200, 200, 200), (int(hx), int(hy)), HOLE_RADIUS + 5)
        pygame.draw.circle(surf, HOLE_COLOR, (int(hx), int(hy)), HOLE_RADIUS)
        # 旗杆
        pygame.draw.line(surf, BLACK, (int(hx), int(hy) - 40), (int(hx), int(hy)), 3)
        # 旗子
        flag_points = [(int(hx), int(hy) - 40), (int(hx) + 20, int(hy) - 33), (int(hx), int(hy) - 26)]
        pygame.draw.polygon(surf, FLAG_COLOR, flag_points)
        # 旗杆上的数字
        flag_num = font_small.render(str(self.current_hole + 1), True, WHITE)
        surf.blit(flag_num, (int(hx) + 5, int(hy) - 38))

        # 绘制球
        self.ball.draw(surf)

        # 瞄准线
        if self.aiming and not self.charging:
            mx, my = pygame.mouse.get_pos()
            dx = mx - self.ball.x
            dy = my - self.ball.y
            if math.hypot(dx, dy) > 5:
                angle = math.atan2(dy, dx)
                self.aim_angle = angle
                # 瞄准线
                line_len = 80
                end_x = self.ball.x + math.cos(angle) * line_len
                end_y = self.ball.y + math.sin(angle) * line_len
                pygame.draw.line(surf, WHITE, (self.ball.x, self.ball.y), (end_x, end_y), 2)
                # 虚线延伸
                for i in range(1, 5):
                    t = i * 20
                    alpha = 200 - i * 40
                    ex = self.ball.x + math.cos(angle) * (line_len + t)
                    ey = self.ball.y + math.sin(angle) * (line_len + t)
                    pygame.draw.circle(surf, (255, 255, 255, alpha), (int(ex), int(ey)), 2)

        # 蓄力条
        if self.charging:
            # 蓄力条背景
            bar_x, bar_y = 50, SCREEN_HEIGHT - 150
            bar_w, bar_h = 30, 100
            pygame.draw.rect(surf, (50, 50, 50), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4))
            pygame.draw.rect(surf, (100, 100, 100), (bar_x, bar_y, bar_w, bar_h))
            # 蓄力填充
            fill_h = int(bar_h * self.power / 100)
            fill_color = (
                min(255, int(self.power * 2.55)),
                min(255, int(255 - self.power * 2.55)),
                0,
            )
            pygame.draw.rect(surf, fill_color, (bar_x, bar_y + bar_h - fill_h, bar_w, fill_h))
            # 力量百分比
            power_text = font_small.render(f"{int(self.power)}%", True, WHITE)
            surf.blit(power_text, (bar_x - 5, bar_y - 25))

            # 瞄准线（蓄力时显示）
            angle = self.aim_angle
            line_len = 30 + self.power * 0.8
            end_x = self.ball.x + math.cos(angle) * line_len
            end_y = self.ball.y + math.sin(angle) * line_len
            pygame.draw.line(surf, YELLOW, (self.ball.x, self.ball.y), (end_x, end_y), 3)

        # 风向指示
        wind_speed = math.hypot(wind[0], wind[1])
        wind_angle = math.atan2(wind[1], wind[0])
        wind_center_x = SCREEN_WIDTH - 80
        wind_center_y = 60
        pygame.draw.circle(surf, (200, 200, 200, 100), (wind_center_x, wind_center_y), 30, 2)
        arrow_len = 20 + wind_speed * 5
        arrow_end_x = wind_center_x + math.cos(wind_angle) * arrow_len
        arrow_end_y = wind_center_y + math.sin(wind_angle) * arrow_len
        pygame.draw.line(surf, WHITE, (wind_center_x, wind_center_y), (arrow_end_x, arrow_end_y), 3)
        # 箭头
        a_angle = 0.4
        a_len = 8
        pygame.draw.line(
            surf,
            WHITE,
            (arrow_end_x, arrow_end_y),
            (
                arrow_end_x - math.cos(wind_angle - a_angle) * a_len,
                arrow_end_y - math.sin(wind_angle - a_angle) * a_len,
            ),
            2,
        )
        pygame.draw.line(
            surf,
            WHITE,
            (arrow_end_x, arrow_end_y),
            (
                arrow_end_x - math.cos(wind_angle + a_angle) * a_len,
                arrow_end_y - math.sin(wind_angle + a_angle) * a_len,
            ),
            2,
        )
        wind_text = font_small.render(f"风力: {wind_speed:.1f}", True, WHITE)
        surf.blit(wind_text, (wind_center_x - 30, wind_center_y + 35))

        # HUD 信息
        # 当前洞信息
        hole_info = f"第 {self.current_hole + 1}/{len(HOLES)} 洞  标准杆 {hole_data['par']}"
        info_surf = font_mid.render(hole_info, True, WHITE)
        surf.blit(info_surf, (20, 20))

        # 杆数
        stroke_text = font_mid.render(f"本洞杆数: {self.strokes}", True, WHITE)
        surf.blit(stroke_text, (20, 55))

        total_text = font_mid.render(f"总杆数: {self.total_strokes}", True, WHITE)
        surf.blit(total_text, (20, 85))

        # 地形指示
        terrain_names = {
            "fairway": "球道",
            "rough": "长草区",
            "sand": "沙坑",
            "water": "水域",
        }
        terrain_label = font_small.render(f"地形: {terrain_names.get(self.ball.terrain, '未知')}", True, WHITE)
        surf.blit(terrain_label, (20, 115))

        # 操作提示
        if self.aiming and not self.charging:
            hint = font_small.render("按住鼠标左键蓄力，松开击球", True, WHITE)
            surf.blit(hint, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT - 30))

        # 消息显示
        if self.message_timer > 0 and self.message:
            msg_surf = font_large.render(self.message, True, WHITE)
            msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
            # 背景框
            bg_rect = msg_rect.inflate(40, 20)
            bg_surf = pygame.Surface(bg_rect.size)
            bg_surf.set_alpha(180)
            bg_surf.fill((0, 0, 0))
            surf.blit(bg_surf, bg_rect)
            surf.blit(msg_surf, msg_rect)

        # 游戏结束画面
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            surf.blit(overlay, (0, 0))

            title = font_large.render("🏆 游戏结束！", True, YELLOW)
            surf.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80)))

            total = font_large.render(f"总杆数: {self.total_strokes}", True, WHITE)
            surf.blit(total, total.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)))

            total_par = sum(h["par"] for h in HOLES)
            diff = self.total_strokes - total_par
            diff_text = f"标准杆 {total_par}，{'低于' if diff < 0 else '高于'}标准杆 {abs(diff)} 杆"
            diff_color = GREEN if diff <= 0 else RED
            diff_surf = font_mid.render(diff_text, True, diff_color)
            surf.blit(diff_surf, diff_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30)))

            # 每洞明细
            y_offset = SCREEN_HEIGHT // 2 + 70
            for i, (score, hole) in enumerate(zip(self.hole_scores, HOLES)):
                par = hole["par"]
                d = score - par
                if d == 0:
                    mark = "E"
                elif d > 0:
                    mark = f"+{d}"
                else:
                    mark = str(d)
                score_text = font_small.render(
                    f"第{i+1}洞: {score}杆 (标准杆{par}) [{mark}]", True, WHITE
                )
                surf.blit(score_text, (SCREEN_WIDTH // 2 - 100, y_offset))
                y_offset += 25

            restart = font_mid.render("按 R 键重新开始 / ESC 退出", True, WHITE)
            surf.blit(restart, restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)))


def main():
    game = Game()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r and game.game_over:
                    # 重新开始
                    game.__init__()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    if game.aiming and not game.ball.moving:
                        game.charging = True
                        game.power = 0

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and game.charging:
                    if game.power > 5:  # 最小力量阈值
                        game.shoot(game.power)
                    game.charging = False
                    game.power = 0

        # 蓄力递增
        if game.charging:
            game.power += 1.5
            if game.power > 100:
                game.power = 100

        # 更新游戏状态
        if not game.game_over:
            game.update()

        # 绘制
        game.draw(screen)

        # 准星（鼠标光标隐藏）
        mx, my = pygame.mouse.get_pos()
        pygame.draw.circle(screen, WHITE, (mx, my), 4, 1)
        pygame.draw.line(screen, WHITE, (mx - 8, my), (mx + 8, my), 1)
        pygame.draw.line(screen, WHITE, (mx, my - 8), (mx, my + 8), 1)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()