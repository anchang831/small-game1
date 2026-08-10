"""
Knife Hit (飞刀挑战)
====================
向旋转的圆木投掷飞刀，避开已有刀刃，挑战更高关卡。
操作: 鼠标点击/空格键 投掷飞刀

author: AI Game Developer
date: 2026-08-10
"""

import pygame
import sys
import math
import random

# ==================== 常量配置 ====================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 颜色
BLACK = (10, 10, 10)
WHITE = (245, 245, 245)
WOOD_BROWN = (139, 90, 43)
WOOD_DARK = (101, 67, 33)
KNIFE_SILVER = (200, 200, 210)
KNIFE_BLADE = (180, 185, 200)
KNIFE_HANDLE = (80, 60, 40)
RED = (220, 50, 50)
GREEN = (50, 220, 80)
BLUE = (50, 130, 220)
GOLD = (255, 215, 0)
ORANGE = (255, 140, 50)
APPLE_RED = (220, 30, 30)
APPLE_GREEN = (50, 200, 50)
BG_COLOR = (20, 25, 35)
TEXT_SHADOW = (0, 0, 0, 100)

# 游戏参数
LOG_RADIUS = 80
LOG_CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
KNIFE_LENGTH = 55
KNIFE_WIDTH = 6
MAX_KNIVES_PER_LEVEL = 8
TARGET_KNIVES_BASE = 6
ROTATION_SPEED_BASE = 0.8  # 基础旋转速度 (度/帧)
ROTATION_SPEED_INCREMENT = 0.25  # 每关增加
SPEED_FLUCTUATION = 0.3  # 速度波动幅度


class Knife:
    """飞刀类"""

    def __init__(self, angle, is_stuck=True, from_player=True):
        self.angle = angle  # 在圆木上的角度 (弧度)
        self.is_stuck = is_stuck  # 是否已插在圆木上
        self.from_player = from_player  # 是否由玩家投出
        self.target_angle = None  # 投掷动画目标角度
        self.flying = False  # 是否正在飞行中
        self.fly_progress = 0.0  # 飞行进度 0~1
        self.fly_speed = 0.08  # 飞行速度
        self.start_pos = None  # 飞行起始位置
        self.end_pos = None  # 飞行终点位置
        self.hit_effect_timer = 0  # 击中特效计时
        self.is_obstacle = False  # 是否障碍物(苹果)

    def get_tip_position(self, log_center, log_radius, rotation):
        """获取刀尖位置 (刀刃朝外)"""
        total_angle = self.angle + rotation
        # 刀尖在圆木边缘向外延伸
        tip_dist = log_radius + KNIFE_LENGTH
        x = log_center[0] + math.cos(total_angle) * tip_dist
        y = log_center[1] + math.sin(total_angle) * tip_dist
        return (int(x), int(y))

    def get_base_position(self, log_center, log_radius, rotation):
        """获取刀柄底部位置 (插入点)"""
        total_angle = self.angle + rotation
        x = log_center[0] + math.cos(total_angle) * log_radius
        y = log_center[1] + math.sin(total_angle) * log_radius
        return (int(x), int(y))

    def draw(self, screen, log_center, log_radius, rotation):
        """绘制飞刀"""
        if self.is_obstacle:
            # 障碍物苹果
            total_angle = self.angle + rotation
            x = log_center[0] + math.cos(total_angle) * (log_radius + 15)
            y = log_center[1] + math.sin(total_angle) * (log_radius + 15)
            pygame.draw.circle(screen, APPLE_RED, (int(x), int(y)), 14)
            pygame.draw.circle(screen, (180, 20, 20), (int(x - 3), int(y - 3)), 5)
            # 叶子
            leaf_x = int(x + math.cos(total_angle - 0.5) * 10)
            leaf_y = int(y + math.sin(total_angle - 0.5) * 10)
            pygame.draw.ellipse(screen, APPLE_GREEN,
                                (leaf_x - 4, leaf_y - 6, 8, 12))
            return

        if not self.is_stuck and not self.flying:
            # 待投掷的刀 - 在屏幕底部显示
            self._draw_knife_at(screen, (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80), 0)
            return

        total_angle = self.angle + rotation

        if self.flying:
            # 飞行中的刀
            if self.fly_progress < 1.0:
                t = self.fly_progress
                # 平滑插值
                t = t * t * (3 - 2 * t)  # smoothstep
                cur_x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * t
                cur_y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * t
                self._draw_knife_at(screen, (int(cur_x), int(cur_y)), total_angle)
                return

        # 插在圆木上的刀
        base = (log_center[0] + math.cos(total_angle) * log_radius,
                log_center[1] + math.sin(total_angle) * log_radius)
        tip = (base[0] + math.cos(total_angle) * KNIFE_LENGTH,
               base[1] + math.sin(total_angle) * KNIFE_LENGTH)
        self._draw_knife_line(screen, base, tip, total_angle)

    def _draw_knife_at(self, screen, pos, angle):
        """在指定位置绘制刀"""
        # 刀刃
        blade_end = (pos[0] + math.cos(angle) * 30,
                     pos[1] + math.sin(angle) * 30)
        # 刀柄
        handle_end = (pos[0] - math.cos(angle) * 25,
                      pos[1] - math.sin(angle) * 25)

        # 刀刃
        pygame.draw.line(screen, KNIFE_BLADE, pos, blade_end, 5)
        # 刀柄
        pygame.draw.line(screen, KNIFE_HANDLE, pos, handle_end, 7)
        # 护手
        guard_perp = (-math.sin(angle), math.cos(angle))
        g1 = (pos[0] + guard_perp[0] * 8, pos[1] + guard_perp[1] * 8)
        g2 = (pos[0] - guard_perp[0] * 8, pos[1] - guard_perp[1] * 8)
        pygame.draw.line(screen, KNIFE_SILVER, g1, g2, 4)

    def _draw_knife_line(self, screen, base, tip, angle):
        """从刀尖到刀柄绘制刀"""
        # 刀刃 (从插入点到刀尖)
        blade_end = (base[0] + math.cos(angle) * KNIFE_LENGTH,
                     base[1] + math.sin(angle) * KNIFE_LENGTH)
        handle_end = (base[0] - math.cos(angle) * 20,
                      base[1] - math.sin(angle) * 20)

        # 刀刃
        pygame.draw.line(screen, KNIFE_BLADE, base, blade_end, 5)
        # 刀柄
        pygame.draw.line(screen, KNIFE_HANDLE, base, handle_end, 7)
        # 护手 (在插入点)
        perp = (-math.sin(angle), math.cos(angle))
        g1 = (base[0] + perp[0] * 8, base[1] + perp[1] * 8)
        g2 = (base[0] - perp[0] * 8, base[1] - perp[1] * 8)
        pygame.draw.line(screen, KNIFE_SILVER, g1, g2, 4)


class Game:
    """游戏主类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Knife Hit - 飞刀挑战")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        self.font_tiny = pygame.font.Font(None, 24)

        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        self.level = 1
        self.score = 0
        self.best_score = 0
        self.state = "menu"  # menu, playing, game_over
        self.knives = []
        self.rotation = 0.0  # 当前旋转角度
        self.rotation_speed = ROTATION_SPEED_BASE
        self.target_knives = TARGET_KNIVES_BASE
        self.knives_thrown = 0
        self.ready_knife = Knife(0, is_stuck=False)  # 待投掷的刀
        self.max_level = 1

        # 速度波动
        self.speed_oscillation = 0.0
        self.oscillation_direction = 1

        # 特效
        self.sparkles = []
        self.shake_timer = 0
        self.shake_intensity = 0
        self.combo_count = 0
        self.combo_timer = 0
        self.level_complete_timer = 0

        # 初始化关卡
        self.init_level()

    def init_level(self):
        """初始化关卡"""
        self.knives = []
        self.knives_thrown = 0
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = ROTATION_SPEED_BASE + (self.level - 1) * ROTATION_SPEED_INCREMENT
        self.target_knives = TARGET_KNIVES_BASE + self.level // 2
        self.knives_on_target = 0
        self.level_complete_timer = 0

        # 生成障碍物 (苹果)
        num_obstacles = min(self.level // 2, 4)
        obstacle_angles = set()
        for _ in range(num_obstacles):
            while True:
                angle = random.uniform(0, math.pi * 2)
                # 确保不与其他障碍物太近
                too_close = False
                for oa in obstacle_angles:
                    diff = abs(angle - oa)
                    diff = min(diff, math.pi * 2 - diff)
                    if diff < 0.5:
                        too_close = True
                        break
                if not too_close:
                    obstacle_angles.add(angle)
                    break

        for angle in obstacle_angles:
            obs = Knife(angle, is_stuck=True, from_player=False)
            obs.is_obstacle = True
            self.knives.append(obs)

        # 初始已插的刀 (让游戏有挑战)
        if self.level > 1:
            num_existing = min(self.level - 1, 3)
            existing_angles = set()
            for _ in range(num_existing):
                while True:
                    angle = random.uniform(0, math.pi * 2)
                    too_close = False
                    for ea in existing_angles:
                        diff = abs(angle - ea)
                        diff = min(diff, math.pi * 2 - diff)
                        if diff < 0.4:
                            too_close = True
                            break
                    for oa in obstacle_angles:
                        diff = abs(angle - oa)
                        diff = min(diff, math.pi * 2 - diff)
                        if diff < 0.5:
                            too_close = True
                            break
                    if not too_close:
                        existing_angles.add(angle)
                        break
            for angle in existing_angles:
                self.knives.append(Knife(angle, is_stuck=True, from_player=False))

        self.ready_knife = Knife(0, is_stuck=False)

    def handle_throw(self):
        """处理投掷"""
        if self.state != "playing":
            return
        if self.level_complete_timer > 0:
            return

        if self.ready_knife is None:
            return

        # 计算插入角度 (基于当前旋转)
        angle = 0  # 相对于圆木的角度

        # 检查是否有刀在此角度
        for k in self.knives:
            if k.is_obstacle:
                continue
            diff = abs(angle - k.angle)
            diff = min(diff, math.pi * 2 - diff)
            if diff < 0.15:  # 约8.6度
                self.game_over()
                return

        # 检查是否有苹果在此角度
        for k in self.knives:
            if k.is_obstacle:
                diff = abs(angle - k.angle)
                diff = min(diff, math.pi * 2 - diff)
                if diff < 0.2:
                    # 击中苹果 - 加组合奖励
                    self.combo_count += 1
                    self.combo_timer = 60
                    self.score += 10 * self.combo_count
                    # 移除苹果
                    k.is_obstacle = False
                    k.is_stuck = False
                    # 特效
                    total_angle = k.angle + self.rotation
                    pos = (LOG_CENTER[0] + math.cos(total_angle) * (LOG_RADIUS + 15),
                           LOG_CENTER[1] + math.sin(total_angle) * (LOG_RADIUS + 15))
                    for _ in range(15):
                        self.sparkles.append({
                            'pos': list(pos),
                            'vel': [random.uniform(-5, 5), random.uniform(-5, 5)],
                            'life': 30,
                            'color': (random.randint(200, 255), random.randint(50, 100), random.randint(50, 100)),
                            'size': random.randint(3, 6)
                        })
                    # 震动
                    self.shake_timer = 10
                    self.shake_intensity = 6
                    break

        # 投掷飞刀
        new_knife = Knife(angle, is_stuck=True, from_player=True)
        new_knife.flying = True
        new_knife.fly_progress = 0.01
        new_knife.start_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80)
        new_knife.end_pos = (LOG_CENTER[0] + math.cos(self.rotation) * (LOG_RADIUS + 30),
                             LOG_CENTER[1] + math.sin(self.rotation) * (LOG_RADIUS + 30))

        self.knives.append(new_knife)
        self.knives_thrown += 1
        self.ready_knife = None

        # 特效
        self.shake_timer = 3
        self.shake_intensity = 3

        # 检查是否已完成本关
        stuck_knives = sum(1 for k in self.knives if k.is_stuck and not k.is_obstacle and k.from_player)
        if stuck_knives >= self.target_knives:
            self.level_complete_timer = 90

    def game_over(self):
        """游戏结束"""
        self.state = "game_over"
        # 爆炸特效
        for _ in range(30):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3, 12)
            self.sparkles.append({
                'pos': [LOG_CENTER[0], LOG_CENTER[1]],
                'vel': [math.cos(angle) * speed, math.sin(angle) * speed],
                'life': 60,
                'color': (random.randint(200, 255), random.randint(100, 200), random.randint(50, 100)),
                'size': random.randint(4, 8)
            })
        self.shake_timer = 20
        self.shake_intensity = 10
        self.best_score = max(self.best_score, self.score)

    def check_collision_with_stuck(self, new_angle):
        """检查是否与已插刀碰撞"""
        for k in self.knives:
            if not k.is_stuck or k.is_obstacle:
                continue
            diff = abs(new_angle - k.angle)
            diff = min(diff, math.pi * 2 - diff)
            if diff < 0.15:
                return True
        return False

    def update(self):
        """更新游戏状态"""
        # 更新速度波动
        self.speed_oscillation += 0.02 * self.oscillation_direction
        if abs(self.speed_oscillation) > 1.0:
            self.oscillation_direction *= -1

        if self.state == "playing":
            # 更新旋转
            speed_factor = 1.0 + self.speed_oscillation * SPEED_FLUCTUATION
            self.rotation += self.rotation_speed * speed_factor
            self.rotation %= 360

            # 更新飞刀飞行
            all_landed = True
            for k in self.knives:
                if k.flying:
                    k.fly_progress += k.fly_speed
                    if k.fly_progress >= 1.0:
                        k.flying = False
                        k.fly_progress = 1.0
                        # 飞刀落地特效
                        pos = k.get_base_position(LOG_CENTER, LOG_RADIUS, math.radians(self.rotation))
                        for _ in range(8):
                            self.sparkles.append({
                                'pos': [pos[0], pos[1]],
                                'vel': [random.uniform(-3, 3), random.uniform(-3, 3)],
                                'life': 20,
                                'color': (random.randint(180, 220), random.randint(180, 220), 255),
                                'size': random.randint(2, 4)
                            })
                    else:
                        all_landed = False

            # 如果所有飞刀都已落地，生成新的待投掷刀
            if all_landed and self.ready_knife is None and self.state == "playing":
                if self.level_complete_timer <= 0:
                    self.ready_knife = Knife(0, is_stuck=False)

            # 关卡完成倒计时
            if self.level_complete_timer > 0:
                self.level_complete_timer -= 1
                if self.level_complete_timer == 0:
                    # 进入下一关
                    self.level += 1
                    self.score += 50
                    self.max_level = max(self.max_level, self.level)
                    self.init_level()

            # 更新组合计时器
            if self.combo_timer > 0:
                self.combo_timer -= 1
                if self.combo_timer == 0:
                    self.combo_count = 0

        # 更新特效
        if self.shake_timer > 0:
            self.shake_timer -= 1
            if self.shake_timer == 0:
                self.shake_intensity = 0

        # 更新火花
        new_sparkles = []
        for s in self.sparkles:
            s['pos'][0] += s['vel'][0]
            s['pos'][1] += s['vel'][1]
            s['vel'][1] += 0.2  # 重力
            s['life'] -= 1
            s['size'] *= 0.97
            if s['life'] > 0 and s['size'] > 0.5:
                new_sparkles.append(s)
        self.sparkles = new_sparkles

    def draw(self):
        """绘制画面"""
        # 屏幕震动
        shake_offset = (0, 0)
        if self.shake_timer > 0:
            shake_offset = (random.randint(-self.shake_intensity, self.shake_intensity),
                            random.randint(-self.shake_intensity, self.shake_intensity))

        # 背景
        self.screen.fill(BG_COLOR)

        # 背景装饰 - 网格
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(self.screen, (30, 35, 45), (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(self.screen, (30, 35, 45), (0, y), (SCREEN_WIDTH, y), 1)

        if self.state == "menu":
            self.draw_menu()
        elif self.state == "playing" or self.state == "game_over":
            self.draw_game(shake_offset)

        # 绘制火花特效 (在最上层)
        for s in self.sparkles:
            alpha = int(255 * (s['life'] / 60))
            color = (min(s['color'][0], 255), min(s['color'][1], 255), min(s['color'][2], 255))
            pygame.draw.circle(self.screen, color,
                               (int(s['pos'][0] + shake_offset[0]),
                                int(s['pos'][1] + shake_offset[1])),
                               max(1, int(s['size'])))

        pygame.display.flip()

    def draw_menu(self):
        """绘制主菜单"""
        # 标题
        title = self.font_large.render("KNIFE HIT", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 180))
        self.screen.blit(title, title_rect)

        # 副标题
        subtitle = self.font_small.render("飞 刀 挑 战", True, GOLD)
        sub_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 230))
        self.screen.blit(subtitle, sub_rect)

        # 操作提示
        tip1 = self.font_tiny.render("点击鼠标 或 按空格键 投掷飞刀", True, (150, 150, 170))
        tip1_rect = tip1.get_rect(center=(SCREEN_WIDTH // 2, 310))
        self.screen.blit(tip1, tip1_rect)

        tip2 = self.font_tiny.render("避开已有刀刃，击中苹果获得额外分数", True, (150, 150, 170))
        tip2_rect = tip2.get_rect(center=(SCREEN_WIDTH // 2, 340))
        self.screen.blit(tip2, tip2_rect)

        # 开始提示
        blink = int(pygame.time.get_ticks() / 500) % 2 == 0
        if blink:
            start_text = self.font_medium.render("点击任意位置开始", True, GREEN)
            start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, 430))
            self.screen.blit(start_text, start_rect)

        # 最佳记录
        if self.best_score > 0:
            best_text = self.font_small.render(f"最高分: {self.best_score}", True, GOLD)
            best_rect = best_text.get_rect(center=(SCREEN_WIDTH // 2, 500))
            self.screen.blit(best_text, best_rect)

        # 展示飞刀
        self.draw_knife_demo()

    def draw_knife_demo(self):
        """菜单中的飞刀动画"""
        angle = pygame.time.get_ticks() / 1000
        base_x = SCREEN_WIDTH // 2
        base_y = 120
        # 绘制一把旋转的刀
        demo_angle = angle * 2
        blade_end = (base_x + math.cos(demo_angle) * 35,
                     base_y + math.sin(demo_angle) * 35)
        handle_end = (base_x - math.cos(demo_angle) * 25,
                      base_y - math.sin(demo_angle) * 25)

        pygame.draw.line(self.screen, KNIFE_BLADE, (base_x, base_y), blade_end, 5)
        pygame.draw.line(self.screen, KNIFE_HANDLE, (base_x, base_y), handle_end, 7)
        perp = (-math.sin(demo_angle), math.cos(demo_angle))
        g1 = (base_x + perp[0] * 8, base_y + perp[1] * 8)
        g2 = (base_x - perp[0] * 8, base_y - perp[1] * 8)
        pygame.draw.line(self.screen, KNIFE_SILVER, g1, g2, 4)

    def draw_game(self, shake_offset):
        """绘制游戏画面"""
        # 应用震动偏移
        offset_x = shake_offset[0]
        offset_y = shake_offset[1]
        center = (LOG_CENTER[0] + offset_x, LOG_CENTER[1] + offset_y)

        # 绘制圆木
        self.draw_log(center)

        # 绘制所有飞刀
        rotation_rad = math.radians(self.rotation)
        for k in self.knives:
            k.draw(self.screen, center, LOG_RADIUS, rotation_rad)
            # 绘制撞击特效
            if k.hit_effect_timer > 0:
                pos = k.get_base_position(center, LOG_RADIUS, rotation_rad)
                pygame.draw.circle(self.screen, (255, 255, 200, 100),
                                   pos, int(10 * (k.hit_effect_timer / 20)), 2)
                k.hit_effect_timer -= 1

        # 绘制待投掷的刀
        if self.ready_knife is not None:
            self.ready_knife.draw(self.screen, center, LOG_RADIUS, rotation_rad)

        # 绘制UI
        self.draw_ui(center)

        # 绘制游戏结束
        if self.state == "game_over":
            self.draw_game_over()

    def draw_log(self, center):
        """绘制圆木"""
        # 圆木主体
        pygame.draw.circle(self.screen, WOOD_BROWN, center, LOG_RADIUS)
        pygame.draw.circle(self.screen, WOOD_DARK, center, LOG_RADIUS, 3)

        # 年轮
        for i in range(1, 5):
            r = LOG_RADIUS * i / 5
            alpha = 40 - i * 5
            color = (WOOD_DARK[0] + alpha, WOOD_DARK[1] + alpha, WOOD_DARK[2] + alpha)
            pygame.draw.circle(self.screen, color, center, int(r), 1)

        # 中心点
        pygame.draw.circle(self.screen, WOOD_DARK, center, 6)

        # 高光
        highlight = pygame.Surface((LOG_RADIUS * 2, LOG_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(highlight, (255, 255, 255, 15),
                           (LOG_RADIUS - 20, LOG_RADIUS - 20), LOG_RADIUS - 10)
        self.screen.blit(highlight,
                         (center[0] - LOG_RADIUS, center[1] - LOG_RADIUS))

    def draw_ui(self, center):
        """绘制UI信息"""
        # 关卡
        level_text = self.font_small.render(f"Level {self.level}", True, WHITE)
        level_rect = level_text.get_rect(topleft=(20, 20))
        self.screen.blit(level_text, level_rect)

        # 分数
        score_text = self.font_small.render(f"Score: {self.score}", True, GOLD)
        score_rect = score_text.get_rect(topright=(SCREEN_WIDTH - 20, 20))
        self.screen.blit(score_text, score_rect)

        # 进度条 - 已投掷/目标
        stuck_knives = sum(1 for k in self.knives if k.is_stuck and not k.is_obstacle and k.from_player)
        progress = min(stuck_knives / self.target_knives, 1.0)

        bar_width = 200
        bar_height = 20
        bar_x = SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = 25

        # 进度条背景
        pygame.draw.rect(self.screen, (50, 50, 60),
                         (bar_x, bar_y, bar_width, bar_height), border_radius=10)
        # 进度条填充
        if progress > 0:
            fill_color = (100, 200, 100) if progress < 0.7 else (200, 200, 50)
            pygame.draw.rect(self.screen, fill_color,
                             (bar_x + 2, bar_y + 2,
                              int((bar_width - 4) * progress), bar_height - 4),
                             border_radius=8)
        # 进度条文字
        progress_text = self.font_tiny.render(f"✓ {stuck_knives}/{self.target_knives}", True, WHITE)
        progress_rect = progress_text.get_rect(center=(SCREEN_WIDTH // 2, bar_y + bar_height // 2))
        self.screen.blit(progress_text, progress_rect)

        # 旋转速度指示器
        speed_text = self.font_tiny.render(f"Speed: {self.rotation_speed:.1f}", True, (150, 150, 170))
        speed_rect = speed_text.get_rect(bottomleft=(20, SCREEN_HEIGHT - 20))
        self.screen.blit(speed_text, speed_rect)

        # 组合提示
        if self.combo_count > 1 and self.combo_timer > 0:
            combo_text = self.font_medium.render(f"Combo x{self.combo_count}!", True, ORANGE)
            combo_rect = combo_text.get_rect(center=(SCREEN_WIDTH // 2, 120))
            self.screen.blit(combo_text, combo_rect)

        # 关卡完成提示
        if self.level_complete_timer > 0 and self.level_complete_timer > 30:
            complete_text = self.font_large.render("LEVEL COMPLETE!", True, GREEN)
            complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(complete_text, complete_rect)
            next_text = self.font_small.render("准备下一关...", True, WHITE)
            next_rect = next_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
            self.screen.blit(next_text, next_rect)

    def draw_game_over(self):
        """绘制游戏结束画面"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Game Over
        go_text = self.font_large.render("GAME OVER", True, RED)
        go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        self.screen.blit(go_text, go_rect)

        # 分数
        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        self.screen.blit(score_text, score_rect)

        # 最高分
        best_text = self.font_small.render(f"Best: {self.best_score}", True, GOLD)
        best_rect = best_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        self.screen.blit(best_text, best_rect)

        # 关卡
        level_text = self.font_tiny.render(f"Reached Level {self.level}", True, (150, 150, 170))
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
        self.screen.blit(level_text, level_rect)

        # 重新开始
        blink = int(pygame.time.get_ticks() / 500) % 2 == 0
        if blink:
            restart_text = self.font_small.render("点击重新开始", True, GREEN)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 140))
            self.screen.blit(restart_text, restart_rect)

    def handle_click(self, pos):
        """处理点击事件"""
        if self.state == "menu":
            self.state = "playing"
            self.reset_game()
            self.state = "playing"
            return

        if self.state == "game_over":
            self.reset_game()
            self.state = "playing"
            return

        if self.state == "playing":
            self.handle_throw()

    def run(self):
        """主循环"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.state == "playing":
                            self.handle_throw()
                        elif self.state == "menu":
                            self.state = "playing"
                            self.reset_game()
                            self.state = "playing"
                        elif self.state == "game_over":
                            self.reset_game()
                            self.state = "playing"
                    elif event.key == pygame.K_r:
                        self.reset_game()
                        self.state = "playing"

            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()