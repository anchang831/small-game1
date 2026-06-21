#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
塔防游戏 (Tower Defense)
======================
类型: 策略塔防
操作:
  - 按 1/2/3 选择防御塔类型
  - 点击格子(绿色高亮)放置防御塔
  - 防御塔自动攻击射程内敌人
  - 消灭敌人获得金币
  - 生存20波即可获胜

作者: AI Game Developer
日期: 2026-06-21
"""

import pygame
import math
import random
import sys

# ==================== 初始化 ====================
pygame.init()

# -------------------- 屏幕设置 --------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
HUD_HEIGHT = 40
GRID_ROWS = 14
GRID_COLS = 20
CELL_SIZE = 40
GRID_WIDTH = GRID_COLS * CELL_SIZE  # 800
GRID_HEIGHT = GRID_ROWS * CELL_SIZE  # 560
GAME_AREA_TOP = HUD_HEIGHT

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("塔防游戏 Tower Defense")
clock = pygame.time.Clock()
font_small = pygame.font.Font(None, 24)
font_medium = pygame.font.Font(None, 32)
font_large = pygame.font.Font(None, 48)

# -------------------- 颜色定义 --------------------
COLORS = {
    "bg": (30, 30, 40),
    "grid": (50, 50, 60),
    "grid_alt": (45, 45, 55),
    "path": (80, 70, 50),
    "path_border": (100, 85, 60),
    "hud_bg": (20, 20, 30),
    "hud_text": (220, 220, 220),
    "valid": (0, 180, 80, 80),
    "invalid": (180, 0, 0, 60),
    "selected": (255, 255, 100),
    "arrow_tower": (50, 180, 50),
    "cannon_tower": (200, 50, 50),
    "magic_tower": (50, 100, 220),
    "enemy_normal": (220, 180, 50),
    "enemy_fast": (50, 200, 200),
    "enemy_tank": (200, 50, 200),
    "hp_bar_bg": (60, 20, 20),
    "hp_bar_fg": (0, 220, 0),
    "projectile": (255, 255, 100),
    "button_bg": (60, 60, 80),
    "button_hover": (80, 80, 110),
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "gold": (255, 215, 0),
    "wave_info": (100, 200, 255),
}

# ==================== 路径定义 ====================
# 路径以网格坐标表示 (col, row)
# S形路径: 从左侧进入→向右→向下→向右→向上→向右从右侧出去
PATH_CELLS = set()
_path_segments = [
    ("right", (0, 5), 9),   # 行5: col 0-8 向右
    ("down", (8, 5), 6),    # 列8: row 5-10 向下
    ("right", (8, 10), 6),  # 行10: col 8-13 向右
    ("up", (13, 10), 7),    # 列13: row 10-4 向上
    ("right", (13, 4), 7),  # 行4: col 13-19 向右
]

for direction, start, length in _path_segments:
    c, r = start
    for i in range(length):
        if direction == "right":
            PATH_CELLS.add((c + i, r))
        elif direction == "down":
            PATH_CELLS.add((c, r + i))
        elif direction == "up":
            PATH_CELLS.add((c, r - i))

# 路径航点 (像素坐标, 中心点)
WAYPOINTS = [
    (-20, GAME_AREA_TOP + 5 * CELL_SIZE + CELL_SIZE // 2),        # 入口
    (8 * CELL_SIZE + CELL_SIZE // 2, GAME_AREA_TOP + 5 * CELL_SIZE + CELL_SIZE // 2),
    (8 * CELL_SIZE + CELL_SIZE // 2, GAME_AREA_TOP + 10 * CELL_SIZE + CELL_SIZE // 2),
    (13 * CELL_SIZE + CELL_SIZE // 2, GAME_AREA_TOP + 10 * CELL_SIZE + CELL_SIZE // 2),
    (13 * CELL_SIZE + CELL_SIZE // 2, GAME_AREA_TOP + 4 * CELL_SIZE + CELL_SIZE // 2),
    (SCREEN_WIDTH + 20, GAME_AREA_TOP + 4 * CELL_SIZE + CELL_SIZE // 2),  # 出口
]


def grid_to_pixel(col, row):
    """网格坐标转像素坐标 (左上角)"""
    return col * CELL_SIZE, GAME_AREA_TOP + row * CELL_SIZE


def pixel_to_grid(px, py):
    """像素坐标转网格坐标"""
    col = px // CELL_SIZE
    row = (py - GAME_AREA_TOP) // CELL_SIZE
    return col, row


def is_valid_placement(col, row):
    """检查是否为可放置位置（紧邻路径但不在路径上）"""
    if (col, row) in PATH_CELLS:
        return False
    if col < 0 or col >= GRID_COLS or row < 0 or row >= GRID_ROWS:
        return False
    # 检查是否已被占用
    for tower in towers:
        if tower.grid_pos == (col, row):
            return False
    # 必须至少与一个路径格相邻
    for dc, dr in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nc, nr = col + dc, row + dr
        if (nc, nr) in PATH_CELLS:
            return True
    return False


# ==================== 防御塔类 ====================
class Tower:
    """防御塔基类"""
    def __init__(self, col, row, tower_type):
        self.grid_pos = (col, row)
        self.px, self.py = grid_to_pixel(col, row)
        self.cx = self.px + CELL_SIZE // 2  # 中心x
        self.cy = self.py + CELL_SIZE // 2  # 中心y
        self.type = tower_type

        # 根据类型设置属性
        configs = {
            "arrow": {
                "name": "箭塔", "cost": 100, "range": 180, "damage": 20,
                "cooldown_max": 25, "color": COLORS["arrow_tower"], "splash": 0,
            },
            "cannon": {
                "name": "炮塔", "cost": 200, "range": 140, "damage": 50,
                "cooldown_max": 50, "color": COLORS["cannon_tower"], "splash": 45,
            },
            "magic": {
                "name": "魔法塔", "cost": 150, "range": 220, "damage": 12,
                "cooldown_max": 18, "color": COLORS["magic_tower"], "splash": 0,
                "slow_amount": 0.5, "slow_duration": 90,
            },
        }
        cfg = configs[tower_type]
        self.name = cfg["name"]
        self.cost = cfg["cost"]
        self.range = cfg["range"]
        self.damage = cfg["damage"]
        self.cooldown_max = cfg["cooldown_max"]
        self.color = cfg["color"]
        self.splash = cfg["splash"]
        self.cooldown = 0
        self.target = None
        self.angle = 0  # 炮塔朝向角度
        self.kills = 0
        self.slow_amount = cfg.get("slow_amount", 0)
        self.slow_duration = cfg.get("slow_duration", 0)

    def update(self, enemies):
        """更新塔状态: 寻找目标, 攻击"""
        self.cooldown = max(0, self.cooldown - 1)

        # 寻找目标
        if self.target is None or not self.target.alive:
            self.target = self._find_target(enemies)
        else:
            # 检查目标是否仍在射程内
            dx = self.target.x - self.cx
            dy = self.target.y - self.cy
            if dx * dx + dy * dy > self.range * self.range:
                self.target = self._find_target(enemies)

        # 攻击
        if self.target and self.cooldown == 0:
            self.cooldown = self.cooldown_max
            self.angle = math.degrees(math.atan2(
                self.target.y - self.cy, self.target.x - self.cx
            ))
            return Projectile(
                self.cx, self.cy, self.target, self.damage,
                self.splash, self.slow_amount, self.slow_duration,
            )
        return None

    def _find_target(self, enemies):
        """在射程内查找最近的敌人"""
        best = None
        best_dist = float("inf")
        for enemy in enemies:
            if not enemy.alive:
                continue
            dx = enemy.x - self.cx
            dy = enemy.y - self.cy
            dist = dx * dx + dy * dy
            if dist <= self.range * self.range and dist < best_dist:
                best_dist = dist
                best = enemy
        return best

    def draw(self, surf):
        """绘制塔"""
        # 塔体
        rect = pygame.Rect(self.px, self.py, CELL_SIZE - 4, CELL_SIZE - 4)
        rect.center = (self.cx, self.cy)
        pygame.draw.rect(surf, self.color, rect, border_radius=4)
        pygame.draw.rect(surf, COLORS["white"], rect, 1, border_radius=4)

        # 炮管
        end_x = self.cx + math.cos(math.radians(self.angle)) * 18
        end_y = self.cy + math.sin(math.radians(self.angle)) * 18
        pygame.draw.line(surf, COLORS["white"], (self.cx, self.cy),
                         (end_x, end_y), 3)

        # 如果是当前选中的塔类型, 绘制射程
        if self.type == selected_tower_type:
            pygame.draw.circle(surf, (*self.color, 60),
                               (self.cx, self.cy), self.range, 1)

    def draw_range(self, surf):
        """绘制射程指示器 (当塔被悬停时)"""
        s = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, 40), (self.range, self.range),
                           self.range)
        pygame.draw.circle(s, (*self.color, 100), (self.range, self.range),
                           self.range, 2)
        surf.blit(s, (self.cx - self.range, self.cy - self.range))


# ==================== 弹丸类 ====================
class Projectile:
    """攻击弹丸"""
    def __init__(self, x, y, target, damage, splash=0,
                 slow_amount=0, slow_duration=0):
        self.x = x
        self.y = y
        self.target = target
        self.damage = damage
        self.splash = splash
        self.slow_amount = slow_amount
        self.slow_duration = slow_duration
        self.speed = 8
        self.alive = True

    def update(self):
        """更新弹丸位置, 命中检测"""
        if not self.alive:
            return

        if self.target is None or not self.target.alive:
            self.alive = False
            return

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < self.speed:
            # 命中
            self._hit()
            self.alive = False
        else:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

    def _hit(self):
        """命中效果"""
        if not self.target.alive:
            return

        self.target.take_damage(self.damage)

        # 减速效果
        if self.slow_amount > 0:
            self.target.apply_slow(self.slow_amount, self.slow_duration)

        # 溅射伤害
        if self.splash > 0:
            for enemy in enemies:
                if enemy is self.target or not enemy.alive:
                    continue
                dx = enemy.x - self.target.x
                dy = enemy.y - self.target.y
                if dx * dx + dy * dy <= self.splash * self.splash:
                    enemy.take_damage(self.damage * 0.5)
                    if self.slow_amount > 0:
                        enemy.apply_slow(self.slow_amount, self.slow_duration)

        # 特效粒子
        for _ in range(8):
            particles.append(Particle(self.target.x, self.target.y,
                                       self.damage))

    def draw(self, surf):
        """绘制弹丸"""
        if self.alive:
            color = COLORS["projectile"]
            if self.splash > 0:
                color = COLORS["cannon_tower"]
            elif self.slow_amount > 0:
                color = COLORS["magic_tower"]
            pygame.draw.circle(surf, color, (int(self.x), int(self.y)), 4)
            pygame.draw.circle(surf, COLORS["white"],
                               (int(self.x), int(self.y)), 2)


# ==================== 粒子特效类 ====================
class Particle:
    """简单粒子特效"""
    def __init__(self, x, y, damage=0):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.life = random.randint(15, 30)
        self.max_life = self.life
        colors = [(255, 200, 50), (255, 150, 50), (255, 100, 50),
                  (255, 50, 50), (255, 255, 100)]
        self.color = random.choice(colors)
        self.size = random.uniform(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1  # 重力
        self.life -= 1
        return self.life > 0

    def draw(self, surf):
        alpha = int(255 * (self.life / self.max_life))
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha),
                           (self.size, self.size), self.size)
        surf.blit(s, (int(self.x - self.size), int(self.y - self.size)))


# ==================== 敌人类 ====================
class Enemy:
    """敌人基类"""
    def __init__(self, enemy_type, wave_num=1):
        self.type = enemy_type

        configs = {
            "normal": {
                "hp": 80, "speed": 1.8, "reward": 10, "color": COLORS["enemy_normal"],
                "size": 12,
            },
            "fast": {
                "hp": 50, "speed": 3.0, "reward": 15, "color": COLORS["enemy_fast"],
                "size": 10,
            },
            "tank": {
                "hp": 250, "speed": 1.0, "reward": 25, "color": COLORS["enemy_tank"],
                "size": 16,
            },
        }
        cfg = configs[enemy_type]

        # 波次加成
        hp_mult = 1 + (wave_num - 1) * 0.15
        self.max_hp = int(cfg["hp"] * hp_mult)
        self.hp = self.max_hp
        self.base_speed = cfg["speed"]
        self.speed = cfg["speed"]
        self.reward = cfg["reward"] + wave_num // 5
        self.color = cfg["color"]
        self.size = cfg["size"]

        # 路径跟随
        self.waypoint_index = 1  # 目标航点索引
        self.x, self.y = WAYPOINTS[0]
        self.alive = True
        self.reached_end = False
        self.distance_traveled = 0

        # 减速状态
        self.slow_timer = 0
        self.slow_amount = 0

    def apply_slow(self, amount, duration):
        """应用减速效果"""
        self.slow_amount = max(self.slow_amount, amount)
        self.slow_timer = max(self.slow_timer, duration)

    def take_damage(self, amount):
        """受到伤害"""
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            global gold
            gold += self.reward
            # 死亡粒子
            for _ in range(12):
                particles.append(Particle(self.x, self.y))

    def update(self):
        """更新位置"""
        if not self.alive or self.reached_end:
            return

        # 更新减速
        if self.slow_timer > 0:
            self.slow_timer -= 1
            self.speed = self.base_speed * (1 - self.slow_amount)
            if self.slow_timer <= 0:
                self.speed = self.base_speed
                self.slow_amount = 0
        else:
            self.speed = self.base_speed

        # 向目标航点移动
        if self.waypoint_index >= len(WAYPOINTS):
            self.reached_end = True
            return

        tx, ty = WAYPOINTS[self.waypoint_index]
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < self.speed:
            self.x, self.y = tx, ty
            self.waypoint_index += 1
        else:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
            self.distance_traveled += self.speed

    def draw(self, surf):
        """绘制敌人"""
        if not self.alive:
            return

        # 身体
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)),
                           self.size)
        pygame.draw.circle(surf, COLORS["white"], (int(self.x), int(self.y)),
                           self.size, 1)

        # 减速特效
        if self.slow_timer > 0:
            pygame.draw.circle(surf, (100, 200, 255, 100),
                               (int(self.x), int(self.y)), self.size + 3, 2)

        # 血条
        bar_w = self.size * 2 + 4
        bar_h = 4
        bar_x = int(self.x) - bar_w // 2
        bar_y = int(self.y) - self.size - 8
        hp_ratio = self.hp / self.max_hp

        pygame.draw.rect(surf, COLORS["hp_bar_bg"],
                         (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surf, COLORS["hp_bar_fg"],
                         (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))

        # 当前血量文本
        hp_text = font_small.render(f"{int(self.hp)}", True, COLORS["white"])
        surf.blit(hp_text, (bar_x, bar_y - 12))


# ==================== 游戏状态管理 ====================
def spawn_wave():
    """生成一波敌人"""
    global wave_num, enemies, wave_spawning, spawn_timer, enemies_in_wave
    wave_spawning = True
    spawn_timer = 0

    n_normal = 3 + wave_num * 2
    n_fast = max(0, wave_num // 2)
    n_tank = max(0, (wave_num - 1) // 3)

    enemies_in_wave = []
    for _ in range(n_normal):
        enemies_in_wave.append("normal")
    for _ in range(n_fast):
        enemies_in_wave.append("fast")
    for _ in range(n_tank):
        enemies_in_wave.append("tank")
    random.shuffle(enemies_in_wave)

    enemies_to_spawn = len(enemies_in_wave)
    wave_label = font_medium.render(f"第 {wave_num} 波! ({enemies_to_spawn} 个敌人)",
                                     True, COLORS["wave_info"])
    wave_label_ticks = 60  # 显示1秒


def start_next_wave():
    """开始下一波"""
    global wave_num, wave_cooldown, wave_started
    wave_num += 1
    wave_started = False
    wave_cooldown = 30  # 冷却后自动开始
    spawn_wave()


# ==================== 初始化游戏 ====================
towers = []
enemies = []
projectiles = []
particles = []
gold = 300
lives = 20
wave_num = 0
wave_started = False
wave_cooldown = 60
wave_spawning = False
spawn_timer = 0
spawn_index = 0
enemies_in_wave = []
game_over = False
game_won = False
selected_tower_type = "arrow"
hovered_grid = None
tower_info_target = None  # 悬停查看信息的塔

# 底部按钮区域
BUTTON_Y = SCREEN_HEIGHT - 50
button_list = [
    {"type": "arrow", "label": "1:箭塔 $100", "color": COLORS["arrow_tower"]},
    {"type": "cannon", "label": "2:炮塔 $200", "color": COLORS["cannon_tower"]},
    {"type": "magic", "label": "3:魔法塔 $150", "color": COLORS["magic_tower"]},
]


def draw_hud(surf):
    """绘制顶部信息栏"""
    pygame.draw.rect(surf, COLORS["hud_bg"], (0, 0, SCREEN_WIDTH, HUD_HEIGHT))

    wave_text = font_small.render(f"波次: {wave_num}/20", True, COLORS["hud_text"])
    lives_text = font_small.render(f"生命: {lives}", True, COLORS["hud_text"])
    gold_text = font_small.render(f"金币: {gold}", True, COLORS["gold"])
    tower_text = font_small.render(
        f"当前: {next(t['label'] for t in button_list if t['type'] == selected_tower_type)}",
        True, COLORS["selected"])

    surf.blit(wave_text, (10, 12))
    surf.blit(lives_text, (150, 12))
    surf.blit(gold_text, (290, 12))
    surf.blit(tower_text, (430, 12))

    # 下一波按钮
    btn_rect = pygame.Rect(650, 5, 140, 30)
    if not wave_spawning:
        pygame.draw.rect(surf, (0, 120, 0), btn_rect, border_radius=4)
        next_text = font_small.render("点击开始下一波", True, COLORS["white"])
        surf.blit(next_text, (655, 10))
    return btn_rect


def draw_tower_buttons(surf):
    """绘制底部塔选择按钮"""
    panel_rect = pygame.Rect(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50)
    pygame.draw.rect(surf, COLORS["hud_bg"], panel_rect)
    pygame.draw.line(surf, (80, 80, 100), (0, SCREEN_HEIGHT - 50),
                     (SCREEN_WIDTH, SCREEN_HEIGHT - 50), 2)

    buttons = []
    btn_w = 150
    btn_h = 36
    spacing = 20
    total_w = len(button_list) * btn_w + (len(button_list) - 1) * spacing
    start_x = (SCREEN_WIDTH - total_w) // 2

    for i, btn in enumerate(button_list):
        x = start_x + i * (btn_w + spacing)
        y = SCREEN_HEIGHT - 44
        rect = pygame.Rect(x, y, btn_w, btn_h)

        is_selected = (btn["type"] == selected_tower_type)
        bg = btn["color"] if is_selected else COLORS["button_bg"]
        pygame.draw.rect(surf, bg, rect, border_radius=6)
        pygame.draw.rect(surf, COLORS["white"], rect, 1, border_radius=6)

        text = font_small.render(btn["label"], True, COLORS["white"])
        text_rect = text.get_rect(center=rect.center)
        surf.blit(text, text_rect)

        buttons.append({"rect": rect, "type": btn["type"]})

    return buttons


def draw_grid(surf):
    """绘制游戏网格和路径"""
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x, y = grid_to_pixel(col, row)
            color = COLORS["grid_alt"] if (col + row) % 2 == 0 else COLORS["grid"]
            pygame.draw.rect(surf, color, (x, y, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(surf, (40, 40, 50), (x, y, CELL_SIZE, CELL_SIZE), 1)

    # 绘制路径
    for col, row in PATH_CELLS:
        x, y = grid_to_pixel(col, row)
        pygame.draw.rect(surf, COLORS["path"], (x, y, CELL_SIZE, CELL_SIZE))
        # 路径箭头指示方向
        pygame.draw.rect(surf, COLORS["path_border"],
                         (x, y, CELL_SIZE, CELL_SIZE), 1)

    # 绘制可放置位置指示
    if hovered_grid:
        col, row = hovered_grid
        valid = is_valid_placement(col, row)
        x, y = grid_to_pixel(col, row)
        s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        color = COLORS["valid"] if valid else COLORS["invalid"]
        s.fill(color)
        surf.blit(s, (x, y))

    # 绘制路径箭头(简洁指示方向)
    for i, (wp_x, wp_y) in enumerate(WAYPOINTS[1:-1], 1):
        prev_x, prev_y = WAYPOINTS[i - 1]
        if prev_x == wp_x:  # 垂直
            mid_y = (prev_y + wp_y) // 2
            arrow_size = 6
            pygame.draw.polygon(surf, (120, 100, 70), [
                (wp_x - arrow_size, mid_y),
                (wp_x + arrow_size, mid_y),
                (wp_x, mid_y + (8 if wp_y > prev_y else -8)),
            ])
        else:  # 水平
            mid_x = (prev_x + wp_x) // 2
            arrow_size = 6
            pygame.draw.polygon(surf, (120, 100, 70), [
                (mid_x, wp_y - arrow_size),
                (mid_x, wp_y + arrow_size),
                (mid_x + (8 if wp_x > prev_x else -8), wp_y),
            ])


def draw_game_over(surf):
    """绘制游戏结束界面"""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surf.blit(overlay, (0, 0))

    if game_won:
        title = font_large.render("🎉 胜利! 🎉", True, COLORS["gold"])
        sub = font_medium.render("成功抵挡了20波敌人攻击!", True, COLORS["white"])
    else:
        title = font_large.render("💀 失败 💀", True, (255, 80, 80))
        sub = font_medium.render("基地被突破... 点击 R 重新开始", True, COLORS["white"])

    restart = font_small.render("按 R 键重新开始", True, COLORS["hud_text"])

    surf.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 180))
    surf.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 250))
    surf.blit(restart, (SCREEN_WIDTH // 2 - restart.get_width() // 2, 320))

    # 统计信息
    total_kills = sum(t.kills for t in towers)
    stats = font_small.render(f"消灭敌人: {total_kills} | 防御塔: {len(towers)}座",
                                True, COLORS["hud_text"])
    surf.blit(stats, (SCREEN_WIDTH // 2 - stats.get_width() // 2, 370))


def reset_game():
    """重置游戏"""
    global towers, enemies, projectiles, particles, gold, lives
    global wave_num, wave_started, wave_cooldown, wave_spawning
    global spawn_timer, spawn_index, enemies_in_wave, game_over, game_won
    towers = []
    enemies = []
    projectiles = []
    particles = []
    gold = 300
    lives = 20
    wave_num = 0
    wave_started = False
    wave_cooldown = 60
    wave_spawning = False
    spawn_timer = 0
    spawn_index = 0
    enemies_in_wave = []
    game_over = False
    game_won = False


# ==================== 主游戏循环 ====================
running = True
next_wave_btn = pygame.Rect(650, 5, 140, 30)

while running:
    dt = clock.tick(60)

    # ========== 事件处理 ==========
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            sys.exit()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and (game_over or game_won):
                reset_game()
            if not game_over and not game_won:
                if event.key == pygame.K_1:
                    selected_tower_type = "arrow"
                elif event.key == pygame.K_2:
                    selected_tower_type = "cannon"
                elif event.key == pygame.K_3:
                    selected_tower_type = "magic"

        elif event.type == pygame.MOUSEBUTTONDOWN and not game_over and not game_won:
            mx, my = event.pos

            # 底部按钮点击
            if my >= SCREEN_HEIGHT - 50:
                for btn_info in draw_tower_buttons(screen):
                    if btn_info["rect"].collidepoint(mx, my):
                        selected_tower_type = btn_info["type"]
                        break
            # 下一波按钮点击
            elif next_wave_btn.collidepoint(mx, my) and not wave_spawning and wave_started:
                start_next_wave()
            # 网格点击 - 放置塔
            elif my >= GAME_AREA_TOP:
                col = mx // CELL_SIZE
                row = (my - GAME_AREA_TOP) // CELL_SIZE
                if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS:
                    if is_valid_placement(col, row):
                        costs = {"arrow": 100, "cannon": 200, "magic": 150}
                        cost = costs[selected_tower_type]
                        if gold >= cost:
                            gold -= cost
                            new_tower = Tower(col, row, selected_tower_type)
                            towers.append(new_tower)

    # ========== 游戏逻辑更新 ==========
    if not game_over and not game_won:
        # 波次管理
        if not wave_started:
            wave_started = True
            wave_cooldown = 30

        if not wave_spawning and wave_started:
            wave_cooldown -= 1
            if wave_cooldown <= 0 and len(enemies) == 0:
                if wave_num >= 20:
                    game_won = True
                else:
                    start_next_wave()

        # 生成敌人
        if wave_spawning:
            spawn_timer += 1
            spawn_interval = max(15, 40 - wave_num)
            if spawn_timer >= spawn_interval and spawn_index < len(enemies_in_wave):
                e_type = enemies_in_wave[spawn_index]
                enemies.append(Enemy(e_type, wave_num))
                spawn_index += 1
                spawn_timer = 0
            if spawn_index >= len(enemies_in_wave) and len(enemies) == 0:
                wave_spawning = False

        # 更新敌人
        for enemy in enemies[:]:
            enemy.update()
            if enemy.reached_end:
                lives -= 1
                enemies.remove(enemy)
                if lives <= 0:
                    game_over = True
                # 损失生命粒子
                for _ in range(10):
                    particles.append(Particle(enemy.x, enemy.y, 50))
            elif not enemy.alive:
                enemies.remove(enemy)
                # 记录击杀
                for tower in towers:
                    if tower.target and tower.target is enemy:
                        tower.kills += 1

        # 更新塔
        for tower in towers:
            proj = tower.update(enemies)
            if proj:
                projectiles.append(proj)

        # 更新弹丸
        for proj in projectiles[:]:
            proj.update()
            if not proj.alive:
                projectiles.remove(proj)

        # 更新粒子
        particles = [p for p in particles if p.update()]

    # ========== 渲染 ==========
    screen.fill(COLORS["bg"])
    draw_grid(screen)

    # 绘制塔(以及悬停时的射程)
    mouse_x, mouse_y = pygame.mouse.get_pos()
    tower_info_target = None
    for tower in towers:
        tower.draw(screen)
        rect = pygame.Rect(tower.px, tower.py, CELL_SIZE, CELL_SIZE)
        if rect.collidepoint(mouse_x, mouse_y) and mouse_y >= GAME_AREA_TOP:
            tower.draw_range(screen)
            tower_info_target = tower

    # 绘制敌人
    for enemy in enemies:
        enemy.draw(screen)

    # 绘制弹丸
    for proj in projectiles:
        proj.draw(screen)

    # 绘制粒子
    for p in particles:
        p.draw(screen)

    # 绘制UI
    next_wave_btn = draw_hud(screen)
    draw_tower_buttons(screen)

    # 塔信息提示
    if tower_info_target and mouse_y >= GAME_AREA_TOP:
        info_surf = pygame.Surface((200, 90), pygame.SRCALPHA)
        info_surf.fill((0, 0, 0, 200))
        lines = [
            f"{tower_info_target.name} (击杀: {tower_info_target.kills})",
            f"伤害: {tower_info_target.damage} | 射程: {tower_info_target.range}",
            f"冷却: {tower_info_target.cooldown_max}帧",
        ]
        if tower_info_target.splash > 0:
            lines.append(f"溅射: {tower_info_target.splash}px")
        info_x = min(mouse_x + 10, SCREEN_WIDTH - 210)
        info_y = max(mouse_y - 100, 50)
        screen.blit(info_surf, (info_x, info_y))
        for i, line in enumerate(lines):
            txt = font_small.render(line, True, COLORS["white"])
            screen.blit(txt, (info_x + 5, info_y + 5 + i * 20))

    # 波次开始提示
    if wave_spawning and spawn_index < len(enemies_in_wave) and spawn_timer < 30:
        remaining = len(enemies_in_wave) - spawn_index
        wave_info = font_small.render(f"剩余: {remaining} 个敌人待出场",
                                       True, COLORS["wave_info"])
        screen.blit(wave_info, (SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 - 60))

    # 游戏结束/胜利界面
    if game_over or game_won:
        draw_game_over(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()