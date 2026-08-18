"""
射箭 (Archery) - 经典射箭模拟游戏
===============================
控制弓箭瞄准靶心射击，受风力影响抛物线轨迹
- 鼠标控制瞄准角度，按住蓄力，释放射击
- 风力随机变化，影响箭矢飞行
- 10轮比赛，每轮射1箭
- 环数计分：靶心10环，向外递减

操作：
- 鼠标移动：瞄准
- 按住左键：蓄力（力量条上升）
- 释放左键：射箭
- R键：重新开始
- ESC键：退出

Author: AI Game Generator
Date: 2026-08-18
"""

import pygame
import math
import random
import sys

# ==================== 初始化 ====================
pygame.init()

# ==================== 常量配置 ====================
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 650
FPS = 60
GRAVITY = 0.15
GROUND_Y = 550
ARCHER_X = 150
ARCHER_Y = GROUND_Y - 20

# 颜色
COLORS = {
    'sky_top': (135, 206, 235),
    'sky_bottom': (255, 255, 255),
    'ground': (34, 139, 34),
    'ground_dark': (25, 100, 25),
    'bow': (139, 69, 19),
    'bow_string': (100, 50, 10),
    'arrow': (80, 50, 20),
    'arrow_head': (200, 200, 200),
    'target_outer': (255, 255, 255),  # 1环白色
    'target_black': (50, 50, 50),     # 2环黑色
    'target_blue': (50, 100, 200),    # 3环蓝色
    'target_red': (200, 50, 50),      # 4环红色
    'target_yellow': (255, 215, 0),   # 5环黄金
    'bullseye': (255, 50, 50),        # 靶心
    'wind_arrow': (100, 200, 255),
    'text': (255, 255, 255),
    'text_dark': (50, 50, 50),
    'ui_bg': (0, 0, 0, 180),
    'power_bar_bg': (60, 60, 60),
    'power_bar_fill': (255, 200, 50),
    'power_bar_high': (255, 50, 50),
    'trajectory': (255, 255, 200, 100),
    'feather': (200, 50, 50),
}

# 靶子环数半径
RING_RADII = [200, 160, 120, 80, 40]  # 从外到内
RING_SCORES = [1, 2, 3, 4, 5]  # 对应环数
# 靶心额外奖励

# 风力范围
WIND_MIN = -4
WIND_MAX = 4

# 箭矢参数
MAX_POWER = 28
MIN_POWER = 5


# ==================== 游戏类 ====================
class ArcheryGame:
    """射箭游戏主类"""

    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("🎯 射箭 Archery")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 28)
        self.font_tiny = pygame.font.Font(None, 20)

        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        self.round = 1
        self.max_rounds = 10
        self.scores = []
        self.total_score = 0
        self.game_over = False

        # 射箭状态
        self.aim_angle = -45  # 瞄准角度(度)，向上为负
        self.power = 0
        self.is_charging = False
        self.arrow_flying = False
        self.arrow_showing = False  # 箭是否在飞行中或已命中

        # 箭矢飞行数据
        self.arrow_x = 0
        self.arrow_y = 0
        self.arrow_vx = 0
        self.arrow_vy = 0
        self.arrow_trail = []
        self.arrow_hit = False
        self.hit_score = 0
        self.hit_pos = None
        self.show_result_timer = 0

        # 生成靶子和风力
        self.target_x = random.randint(650, 880)
        self.target_y = random.randint(150, 380)
        self.target_size = 200  # 靶子半径
        self.wind = 0
        self.refresh_wind()

        # 记录上一轮的箭痕
        self.arrow_marks = []  # 存储 [(x, y, score), ...]

    def refresh_wind(self):
        """刷新风力"""
        self.wind = random.uniform(WIND_MIN, WIND_MAX)
        # 风力变化频率
        self.wind_change_timer = random.randint(60, 180)

    def get_ring_score(self, dx, dy):
        """根据距离靶心的距离计算环数分数"""
        distance = math.sqrt(dx * dx + dy * dy)
        if distance <= 20:
            return 10  # 靶心
        elif distance <= 40:
            return 9
        elif distance <= 60:
            return 8
        elif distance <= 80:
            return 7
        elif distance <= 100:
            return 6
        elif distance <= 120:
            return 5
        elif distance <= 140:
            return 4
        elif distance <= 160:
            return 3
        elif distance <= 180:
            return 2
        elif distance <= 200:
            return 1
        else:
            return 0  # 脱靶

    def handle_events(self):
        """处理输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_r:
                    if self.game_over or self.round > self.max_rounds:
                        self.reset_game()
                    else:
                        # 重置当前轮
                        self.arrow_flying = False
                        self.arrow_showing = False
                        self.arrow_hit = False
                        self.show_result_timer = 0
                        self.power = 0
                        self.is_charging = False
                        self.arrow_trail = []
                        self.hit_pos = None
                        self.hit_score = 0

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    if self.game_over or self.round > self.max_rounds:
                        self.reset_game()
                    elif not self.arrow_flying and not self.arrow_showing:
                        self.is_charging = True
                        self.power = 0

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # 左键释放
                    if self.is_charging and not self.arrow_flying:
                        self.shoot_arrow()
                        self.is_charging = False

        return True

    def shoot_arrow(self):
        """发射箭矢"""
        if self.power < 5:
            return

        self.arrow_flying = True
        self.arrow_showing = True
        self.arrow_hit = False
        self.arrow_trail = []

        # 计算箭矢初始位置（弓弦位置）
        angle_rad = math.radians(self.aim_angle)
        bow_length = 60
        self.arrow_x = ARCHER_X + math.cos(angle_rad) * bow_length
        self.arrow_y = ARCHER_Y + math.sin(angle_rad) * bow_length

        # 计算初始速度
        power_factor = self.power / 100.0
        speed = MIN_POWER + (MAX_POWER - MIN_POWER) * power_factor
        self.arrow_vx = math.cos(angle_rad) * speed
        self.arrow_vy = math.sin(angle_rad) * speed

    def update_arrow(self):
        """更新箭矢飞行物理"""
        if not self.arrow_flying:
            return

        # 记录轨迹
        self.arrow_trail.append((self.arrow_x, self.arrow_y))
        if len(self.arrow_trail) > 50:
            self.arrow_trail.pop(0)

        # 物理更新：重力 + 风力
        self.arrow_vx += self.wind * 0.02
        self.arrow_vy += GRAVITY
        self.arrow_x += self.arrow_vx
        self.arrow_y += self.arrow_vy

        # 检查是否碰到靶子
        dx = self.arrow_x - self.target_x
        dy = self.arrow_y - self.target_y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist <= self.target_size and self.arrow_x > self.target_x - 30:
            # 箭矢命中靶子
            self.arrow_flying = False
            self.arrow_hit = True
            self.hit_score = self.get_ring_score(dx, dy)
            self.hit_pos = (self.arrow_x, self.arrow_y)
            self.arrow_marks.append((self.arrow_x - self.target_x,
                                      self.arrow_y - self.target_y,
                                      self.hit_score))
            self.scores.append(self.hit_score)
            self.total_score += self.hit_score
            self.show_result_timer = 120  # 显示结果2秒
            return

        # 检查是否超出屏幕
        if (self.arrow_x > WINDOW_WIDTH + 50 or
                self.arrow_x < -50 or
                self.arrow_y > GROUND_Y + 50):
            self.arrow_flying = False
            self.arrow_hit = True
            self.hit_score = 0
            self.hit_pos = (self.arrow_x, self.arrow_y)
            self.scores.append(0)
            self.show_result_timer = 120
            return

        # 检查是否碰到地面
        if self.arrow_y >= GROUND_Y - 5:
            self.arrow_flying = False
            self.arrow_hit = True
            self.hit_score = 0
            self.hit_pos = (self.arrow_x, GROUND_Y - 5)
            self.scores.append(0)
            self.show_result_timer = 120
            return

    def update(self):
        """每帧更新"""
        if self.arrow_hit:
            self.show_result_timer -= 1
            if self.show_result_timer <= 0:
                # 进入下一轮
                self.arrow_hit = False
                self.arrow_showing = False
                self.arrow_trail = []
                self.hit_pos = None
                self.round += 1
                self.power = 0
                self.is_charging = False

                if self.round > self.max_rounds:
                    self.game_over = True
                    return

                # 生成新靶子和风力
                self.target_x = random.randint(650, 880)
                self.target_y = random.randint(150, 380)
                self.refresh_wind()
                return

        if self.arrow_flying:
            self.update_arrow()
            return

        # 更新瞄准角度（非射击状态）
        if not self.arrow_showing:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            dx = mouse_x - ARCHER_X
            dy = mouse_y - ARCHER_Y
            if dx != 0:
                angle = math.degrees(math.atan2(dy, dx))
                self.aim_angle = max(-80, min(-5, angle))

        # 蓄力更新
        if self.is_charging:
            self.power = min(100, self.power + 2)

        # 风力随机变化
        self.wind_change_timer -= 1
        if self.wind_change_timer <= 0:
            self.refresh_wind()

    # ==================== 绘制方法 ====================

    def draw_sky(self):
        """绘制天空渐变"""
        for y in range(GROUND_Y):
            t = y / GROUND_Y
            r = int(COLORS['sky_top'][0] + (COLORS['sky_bottom'][0] - COLORS['sky_top'][0]) * t)
            g = int(COLORS['sky_top'][1] + (COLORS['sky_bottom'][1] - COLORS['sky_top'][1]) * t)
            b = int(COLORS['sky_top'][2] + (COLORS['sky_bottom'][2] - COLORS['sky_top'][2]) * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WINDOW_WIDTH, y))

    def draw_ground(self):
        """绘制地面"""
        # 草地
        pygame.draw.rect(self.screen, COLORS['ground'],
                         (0, GROUND_Y, WINDOW_WIDTH, WINDOW_HEIGHT - GROUND_Y))
        # 草地纹理线
        for x in range(0, WINDOW_WIDTH, 20):
            h = random.randint(3, 8)
            pygame.draw.line(self.screen, COLORS['ground_dark'],
                             (x, GROUND_Y), (x + 10, GROUND_Y - h), 1)

        # 地面线
        pygame.draw.line(self.screen, (20, 80, 20),
                         (0, GROUND_Y), (WINDOW_WIDTH, GROUND_Y), 3)

    def draw_bow(self):
        """绘制弓"""
        angle_rad = math.radians(self.aim_angle)

        # 弓臂 - 从弓中心延伸的两条弧线
        bow_center_x = ARCHER_X
        bow_center_y = ARCHER_Y

        # 弓臂长度和弯曲
        bow_length = 55
        perp_angle = angle_rad + math.pi / 2

        # 弓臂两端
        tip1_x = bow_center_x + math.cos(angle_rad) * bow_length + math.cos(perp_angle) * 15
        tip1_y = bow_center_y + math.sin(angle_rad) * bow_length + math.sin(perp_angle) * 15
        tip2_x = bow_center_x + math.cos(angle_rad) * bow_length - math.cos(perp_angle) * 15
        tip2_y = bow_center_y + math.sin(angle_rad) * bow_length - math.sin(perp_angle) * 15

        # 弓臂弧线 (用贝塞尔模拟)
        points = []
        steps = 20
        for i in range(steps + 1):
            t = i / steps
            # 二次贝塞尔
            bx = (1 - t) ** 2 * tip1_x + 2 * (1 - t) * t * bow_center_x + t ** 2 * tip2_x
            by = (1 - t) ** 2 * tip1_y + 2 * (1 - t) * t * bow_center_y + t ** 2 * tip2_y
            points.append((bx, by))

        if len(points) > 1:
            pygame.draw.lines(self.screen, COLORS['bow'], False, points, 5)

        # 弓弦
        string_pull = 0
        if self.is_charging:
            string_pull = self.power / 100.0 * 30

        pull_x = bow_center_x + math.cos(angle_rad) * (bow_length - string_pull)
        pull_y = bow_center_y + math.sin(angle_rad) * (bow_length - string_pull)

        pygame.draw.line(self.screen, COLORS['bow_string'],
                         tip1_x, tip1_y, pull_x, pull_y, 2)
        pygame.draw.line(self.screen, COLORS['bow_string'],
                         tip2_x, tip2_y, pull_x, pull_y, 2)

    def draw_arrow_ready(self):
        """绘制弓上的箭（待发射状态）"""
        if self.arrow_showing:
            return

        angle_rad = math.radians(self.aim_angle)
        string_pull = 0
        if self.is_charging:
            string_pull = self.power / 100.0 * 30

        bow_length = 60
        start_x = ARCHER_X + math.cos(angle_rad) * (bow_length - string_pull)
        start_y = ARCHER_Y + math.sin(angle_rad) * (bow_length - string_pull)

        arrow_length = 80
        end_x = start_x + math.cos(angle_rad) * arrow_length
        end_y = start_y + math.sin(angle_rad) * arrow_length

        # 箭杆
        pygame.draw.line(self.screen, COLORS['arrow'],
                         start_x, start_y, end_x, end_y, 3)

        # 箭头
        head_size = 8
        head_angle = angle_rad
        head_points = [
            (end_x + math.cos(head_angle) * 10, end_y + math.sin(head_angle) * 10),
            (end_x + math.cos(head_angle + 2.5) * head_size,
             end_y + math.sin(head_angle + 2.5) * head_size),
            (end_x + math.cos(head_angle - 2.5) * head_size,
             end_y + math.sin(head_angle - 2.5) * head_size),
        ]
        pygame.draw.polygon(self.screen, COLORS['arrow_head'], head_points)
        pygame.draw.polygon(self.screen, (150, 150, 150), head_points, 1)

        # 箭羽
        feather_angle = angle_rad + math.pi
        feather_start_x = start_x + math.cos(feather_angle) * 5
        feather_start_y = start_y + math.sin(feather_angle) * 5

        for offset in [-1.2, -0.4, 0.4, 1.2]:
            fx = feather_start_x + math.cos(angle_rad + offset) * 15
            fy = feather_start_y + math.sin(angle_rad + offset) * 15
            pygame.draw.line(self.screen, COLORS['feather'],
                             start_x, start_y, fx, fy, 2)

    def draw_target(self):
        """绘制靶子"""
        cx, cy = self.target_x, self.target_y

        # 靶子阴影
        shadow_offset = 5
        pygame.draw.circle(self.screen, (0, 0, 0, 50),
                           (cx + shadow_offset, cy + shadow_offset),
                           self.target_size + 5)

        # 绘制各环
        ring_colors = [
            (255, 255, 255),   # 外圈 白色
            (50, 50, 50),      # 黑色
            (50, 100, 200),    # 蓝色
            (200, 50, 50),     # 红色
            (255, 215, 0),     # 金色
        ]

        # 从外到内画环
        for i in range(5, 0, -1):
            radius = self.target_size * i // 5
            color_idx = min(i - 1, len(ring_colors) - 1)
            pygame.draw.circle(self.screen, ring_colors[color_idx],
                               (cx, cy), radius)
            pygame.draw.circle(self.screen, (100, 100, 100),
                               (cx, cy), radius, 2)

        # 靶心
        pygame.draw.circle(self.screen, (255, 50, 50), (cx, cy), 20)
        pygame.draw.circle(self.screen, (255, 200, 50), (cx, cy), 10)
        pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), 3)

        # 绘制环数数字
        for i, radius in enumerate([20, 40, 60, 80, 100, 120, 140, 160, 180, 200]):
            if i < 10:
                score = 10 - i
                if score >= 1:
                    text = self.font_tiny.render(str(score), True, (200, 200, 200))
                    text_rect = text.get_rect(center=(cx, cy - radius - 15))
                    self.screen.blit(text, text_rect)

    def draw_arrow_flying(self):
        """绘制飞行中的箭"""
        if not self.arrow_showing or self.arrow_hit:
            return

        # 绘制轨迹（虚线）
        if len(self.arrow_trail) > 2:
            for i in range(1, len(self.arrow_trail), 2):
                alpha = int(100 * i / len(self.arrow_trail))
                pygame.draw.line(self.screen, (255, 255, 200, alpha),
                                 self.arrow_trail[i - 1], self.arrow_trail[i], 1)

        # 绘制箭矢
        angle = math.atan2(self.arrow_vy, self.arrow_vx)
        arrow_length = 30

        end_x = self.arrow_x + math.cos(angle) * arrow_length
        end_y = self.arrow_y + math.sin(angle) * arrow_length

        # 箭杆
        pygame.draw.line(self.screen, COLORS['arrow'],
                         self.arrow_x, self.arrow_y, end_x, end_y, 3)

        # 箭头
        head_size = 6
        head_points = [
            (end_x + math.cos(angle) * 8, end_y + math.sin(angle) * 8),
            (end_x + math.cos(angle + 2.5) * head_size,
             end_y + math.sin(angle + 2.5) * head_size),
            (end_x + math.cos(angle - 2.5) * head_size,
             end_y + math.sin(angle - 2.5) * head_size),
        ]
        pygame.draw.polygon(self.screen, COLORS['arrow_head'], head_points)
        pygame.draw.polygon(self.screen, (150, 150, 150), head_points, 1)

        # 箭羽
        feather_angle = angle + math.pi
        feather_start_x = self.arrow_x + math.cos(feather_angle) * 3
        feather_start_y = self.arrow_y + math.sin(feather_angle) * 3

        for offset in [-1.0, -0.3, 0.3, 1.0]:
            fx = feather_start_x + math.cos(angle + offset) * 10
            fy = feather_start_y + math.sin(angle + offset) * 10
            pygame.draw.line(self.screen, COLORS['feather'],
                             feather_start_x, feather_start_y, fx, fy, 2)

    def draw_arrow_marks(self):
        """绘制已射中的箭痕"""
        for mark_x, mark_y, score in self.arrow_marks:
            ax = self.target_x + mark_x
            ay = self.target_y + mark_y
            angle = random.uniform(0, math.pi * 2)  # 随机插入角度

            length = 25
            end_x = ax + math.cos(angle) * length
            end_y = ay + math.sin(angle) * length

            pygame.draw.line(self.screen, COLORS['arrow'], ax, ay, end_x, end_y, 3)

            # 箭羽
            feather_angle = angle + math.pi
            for offset in [-1.0, 1.0]:
                fx = ax + math.cos(feather_angle + offset) * 8
                fy = ay + math.sin(feather_angle + offset) * 8
                pygame.draw.line(self.screen, COLORS['feather'],
                                 ax, ay, fx, fy, 2)

    def draw_power_bar(self):
        """绘制力量条"""
        bar_x = 30
        bar_y = GROUND_Y + 30
        bar_width = 200
        bar_height = 25

        # 背景
        pygame.draw.rect(self.screen, COLORS['power_bar_bg'],
                         (bar_x, bar_y, bar_width, bar_height), border_radius=5)
        pygame.draw.rect(self.screen, (100, 100, 100),
                         (bar_x, bar_y, bar_width, bar_height), 2, border_radius=5)

        if self.is_charging:
            # 力量条填充
            fill_width = int(bar_width * self.power / 100.0)
            if self.power < 70:
                color = COLORS['power_bar_fill']
            else:
                color = COLORS['power_bar_high']

            pygame.draw.rect(self.screen, color,
                             (bar_x + 2, bar_y + 2, fill_width - 4, bar_height - 4),
                             border_radius=4)

            # 力量文本
            power_text = self.font_tiny.render(f"POWER: {int(self.power)}%", True, COLORS['text'])
            self.screen.blit(power_text, (bar_x + 5, bar_y + 3))

        # 标签
        label = self.font_tiny.render("Power", True, COLORS['text_dark'])
        self.screen.blit(label, (bar_x, bar_y - 20))

    def draw_wind_indicator(self):
        """绘制风力指示器"""
        wx = WINDOW_WIDTH - 150
        wy = 30

        # 背景
        pygame.draw.rect(self.screen, (0, 0, 0, 100),
                         (wx - 60, wy - 10, 180, 50), border_radius=8)

        # 风力文本
        wind_text = self.font_small.render(f"Wind: {self.wind:.1f}", True, COLORS['text'])
        self.screen.blit(wind_text, (wx - 50, wy))

        # 风向箭头
        arrow_length = int(abs(self.wind) * 15)
        arrow_length = max(10, min(80, arrow_length))

        arrow_start_x = wx + 20
        arrow_start_y = wy + 30

        if abs(self.wind) > 0.1:
            if self.wind > 0:  # 右风
                end_x = arrow_start_x + arrow_length
                color = (255, 100, 100)
            else:  # 左风
                end_x = arrow_start_x - arrow_length
                color = (100, 100, 255)

            pygame.draw.line(self.screen, color,
                             (arrow_start_x, arrow_start_y),
                             (end_x, arrow_start_y), 3)

            # 箭头头
            arrow_size = 8
            if self.wind > 0:
                pygame.draw.polygon(self.screen, color, [
                    (end_x, arrow_start_y),
                    (end_x - arrow_size, arrow_start_y - arrow_size),
                    (end_x - arrow_size, arrow_start_y + arrow_size),
                ])
            else:
                pygame.draw.polygon(self.screen, color, [
                    (end_x, arrow_start_y),
                    (end_x + arrow_size, arrow_start_y - arrow_size),
                    (end_x + arrow_size, arrow_start_y + arrow_size),
                ])
        else:
            # 无风
            pygame.draw.line(self.screen, (200, 200, 200),
                             (arrow_start_x - 10, arrow_start_y),
                             (arrow_start_x + 10, arrow_start_y), 2)

    def draw_ui(self):
        """绘制UI信息"""
        # 轮次和分数
        round_text = self.font_medium.render(f"Round: {self.round}/{self.max_rounds}", True, COLORS['text_dark'])
        self.screen.blit(round_text, (WINDOW_WIDTH // 2 - 80, 15))

        score_text = self.font_small.render(f"Total Score: {self.total_score}", True, COLORS['text_dark'])
        self.screen.blit(score_text, (WINDOW_WIDTH // 2 - 70, 60))

        # 历史得分
        if self.scores:
            history = " | ".join([str(s) for s in self.scores])
            if len(history) > 50:
                history = history[-50:] + "..."
            hist_text = self.font_tiny.render(f"Scores: {history}", True, (80, 80, 80))
            self.screen.blit(hist_text, (20, GROUND_Y + 65))

        # 当前环数得分
        if self.arrow_hit and self.show_result_timer > 0:
            if self.hit_score > 0:
                result_text = self.font_large.render(f"Score: {self.hit_score}", True, (255, 215, 0))
                # 在命中位置显示
                result_rect = result_text.get_rect(center=(self.arrow_x, self.arrow_y - 50))
                self.screen.blit(result_text, result_rect)

                if self.hit_score == 10:
                    perfect_text = self.font_medium.render("BULLSEYE!", True, (255, 50, 50))
                    perfect_rect = perfect_text.get_rect(center=(WINDOW_WIDTH // 2, 120))
                    self.screen.blit(perfect_text, perfect_rect)
            else:
                miss_text = self.font_medium.render("MISS!", True, (200, 50, 50))
                miss_rect = miss_text.get_rect(center=(WINDOW_WIDTH // 2, 120))
                self.screen.blit(miss_text, miss_rect)

        # 操作提示
        if not self.arrow_showing and not self.arrow_hit:
            if not self.is_charging:
                hint = self.font_tiny.render("Hold Left Click to charge, Release to shoot", True, (80, 80, 80))
                self.screen.blit(hint, (WINDOW_WIDTH // 2 - 140, GROUND_Y + 90))

    def draw_game_over(self):
        """绘制游戏结束界面"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title = self.font_large.render("GAME OVER", True, (255, 215, 0))
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)

        total = self.font_medium.render(f"Total Score: {self.total_score}", True, COLORS['text'])
        total_rect = total.get_rect(center=(WINDOW_WIDTH // 2, 280))
        self.screen.blit(total, total_rect)

        avg_score = self.total_score / max(1, len(self.scores))
        avg = self.font_small.render(f"Average: {avg_score:.1f} / 10", True, (200, 200, 200))
        avg_rect = avg.get_rect(center=(WINDOW_WIDTH // 2, 330))
        self.screen.blit(avg, avg_rect)

        # 星级评价
        if avg_score >= 9:
            stars = "⭐⭐⭐"
            comment = "Perfect! Legendary Archer!"
        elif avg_score >= 7:
            stars = "⭐⭐"
            comment = "Great! Skilled Archer!"
        elif avg_score >= 5:
            stars = "⭐"
            comment = "Good! Keep practicing!"
        else:
            stars = ""
            comment = "Try again! Practice makes perfect!"

        if stars:
            star_text = self.font_medium.render(stars, True, (255, 215, 0))
            star_rect = star_text.get_rect(center=(WINDOW_WIDTH // 2, 380))
            self.screen.blit(star_text, star_rect)

        comment_text = self.font_small.render(comment, True, COLORS['text'])
        comment_rect = comment_text.get_rect(center=(WINDOW_WIDTH // 2, 430))
        self.screen.blit(comment_text, comment_rect)

        restart = self.font_small.render("Press R or Click to Restart", True, COLORS['text'])
        restart_rect = restart.get_rect(center=(WINDOW_WIDTH // 2, 500))
        self.screen.blit(restart, restart_rect)

        # 得分明细
        detail_y = 480
        if len(self.scores) > 0:
            detail_text = "  ".join([f"R{i+1}:{s}" for i, s in enumerate(self.scores)])
            detail = self.font_tiny.render(detail_text, True, (150, 150, 150))
            detail_rect = detail.get_rect(center=(WINDOW_WIDTH // 2, detail_y))
            self.screen.blit(detail, detail_rect)

    def draw(self):
        """主绘制方法"""
        self.screen.fill((0, 0, 0))

        # 绘制场景
        self.draw_sky()
        self.draw_target()
        self.draw_ground()

        # 绘制箭痕
        self.draw_arrow_marks()

        # 绘制弓和箭
        if not self.arrow_showing:
            self.draw_bow()
            self.draw_arrow_ready()

        # 绘制飞行中的箭
        if self.arrow_showing and not self.arrow_hit:
            self.draw_arrow_flying()

        # 绘制UI
        self.draw_wind_indicator()
        self.draw_power_bar()
        self.draw_ui()

        # 绘制游戏结束
        if self.game_over or self.round > self.max_rounds:
            self.draw_game_over()

        pygame.display.flip()

    def run(self):
        """游戏主循环"""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ==================== 启动 ====================
if __name__ == "__main__":
    game = ArcheryGame()
    game.run()