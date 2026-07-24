"""
钓鱼大师 (Fishing Master)
一个完整的钓鱼模拟游戏
- 蓄力抛竿，等待鱼儿上钩
- 点击收竿，享受钓鱼乐趣
- 不同鱼类有不同分值
- 60秒限时挑战

控制方式:
- 鼠标点击: 抛竿 / 收竿
- 空格键: 切换视角
"""

import pygame
import random
import math
import sys

# ==================== 初始化 ====================
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🎣 钓鱼大师 - Fishing Master")
clock = pygame.time.Clock()
font_large = pygame.font.SysFont("simhei", 36, bold=True)
font_medium = pygame.font.SysFont("simhei", 24, bold=True)
font_small = pygame.font.SysFont("simhei", 18)

# ==================== 颜色 ====================
COLORS = {
    "sky": (135, 206, 235),
    "sky_top": (100, 180, 240),
    "water": (30, 120, 180),
    "water_deep": (10, 60, 120),
    "water_surface": (50, 160, 210),
    "grass": (60, 160, 40),
    "grass_dark": (40, 130, 30),
    "dirt": (139, 90, 43),
    "wood": (160, 120, 60),
    "rod": (180, 140, 80),
    "line": (200, 200, 200),
    "bobber_top": (255, 50, 50),
    "bobber_bottom": (200, 200, 200),
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "gold": (255, 215, 0),
    "red": (255, 50, 50),
    "green": (50, 200, 50),
    "shadow": (0, 0, 0, 60),
    "ui_bg": (0, 0, 0, 160),
}

# ==================== 鱼类数据 ====================
FISH_TYPES = [
    {"name": "小鲫鱼", "color": (180, 180, 160), "size": 18, "score": 10, "speed": 1.5, "rarity": 40},
    {"name": "鲤鱼", "color": (200, 150, 80), "size": 24, "score": 25, "speed": 1.2, "rarity": 30},
    {"name": "鲈鱼", "color": (100, 160, 120), "size": 28, "score": 40, "speed": 1.8, "rarity": 20},
    {"name": "大草鱼", "color": (140, 180, 100), "size": 34, "score": 60, "speed": 1.0, "rarity": 15},
    {"name": "金鲤鱼", "color": (255, 200, 50), "size": 30, "score": 80, "speed": 2.0, "rarity": 10},
    {"name": "巨鲶鱼", "color": (80, 80, 100), "size": 42, "score": 120, "speed": 0.8, "rarity": 8},
    {"name": "彩虹鳟鱼", "color": (255, 100, 150), "size": 26, "score": 150, "speed": 2.5, "rarity": 5},
    {"name": "传说龙鱼", "color": (255, 50, 50), "size": 48, "score": 300, "speed": 3.0, "rarity": 2},
]


# ==================== 游戏状态 ====================
class GameState:
    IDLE = "idle"          # 等待抛竿
    CASTING = "casting"    # 蓄力中
    FISHING = "fishing"    # 等待鱼咬钩
    BITING = "biting"      # 鱼在试探
    HOOKED = "hooked"      # 鱼上钩了/收线中
    RESULT = "result"      # 显示结果
    GAMEOVER = "gameover"  # 游戏结束


class Fish:
    def __init__(self):
        self.reset()

    def reset(self):
        fish_data = random.choices(FISH_TYPES, weights=[f["rarity"] for f in FISH_TYPES], k=1)[0]
        self.name = fish_data["name"]
        self.color = fish_data["color"]
        self.size = fish_data["size"]
        self.score = fish_data["score"]
        self.speed = fish_data["speed"] * random.uniform(0.8, 1.2)
        self.rarity = fish_data["rarity"]

        self.x = random.randint(100, WIDTH - 100)
        self.y = random.randint(280, 520)
        self.vx = random.choice([-1, 1]) * self.speed
        self.vy = random.uniform(-0.3, 0.3)
        self.target_x = self.x
        self.target_y = self.y
        self.wobble = random.uniform(0, math.pi * 2)
        self.wobble_speed = random.uniform(0.02, 0.05)
        self.caught = False
        self.interest = 0  # 对鱼漂的兴趣 0-100
        self.bite_timer = 0
        self.escape_timer = 0

    def update(self, bobber_x, bobber_y, line_in_water):
        self.wobble += self.wobble_speed

        if line_in_water and abs(self.x - bobber_x) < 150 and abs(self.y - bobber_y) < 80:
            dist = math.hypot(self.x - bobber_x, self.y - bobber_y)
            if dist < 60:
                self.interest = min(100, self.interest + 0.5)
                # 游向鱼漂
                self.target_x = bobber_x + random.uniform(-20, 20)
                self.target_y = bobber_y + random.uniform(-10, 10)
            elif dist < 120:
                self.interest = min(100, self.interest + 0.2)
                self.target_x = bobber_x + random.uniform(-40, 40)
                self.target_y = bobber_y + random.uniform(-20, 20)
            else:
                self.interest = max(0, self.interest - 0.1)
                # 随机游动
                if random.random() < 0.01:
                    self.target_x = random.randint(80, WIDTH - 80)
                    self.target_y = random.randint(260, 540)
        else:
            self.interest = max(0, self.interest - 0.2)
            if random.random() < 0.01:
                self.target_x = random.randint(80, WIDTH - 80)
                self.target_y = random.randint(260, 540)

        # 游向目标
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 5:
            move_speed = min(self.speed, dist * 0.03)
            self.x += (dx / dist) * move_speed
            self.y += (dy / dist) * move_speed

        # 游动摆动
        self.x += math.sin(self.wobble) * 0.3
        self.y += math.cos(self.wobble * 0.7) * 0.2

        # 边界
        self.x = max(30, min(WIDTH - 30, self.x))
        self.y = max(260, min(550, self.y))

        # 咬钩逻辑
        if line_in_water and self.interest > 60 and abs(self.x - bobber_x) < 25:
            self.bite_timer += 1
            if self.bite_timer > 30 + random.randint(0, 60):
                self.bite_timer = 0
                return "bite"
        else:
            self.bite_timer = 0

        return None

    def draw(self, surface, camera_shake=0):
        # 鱼身 (椭圆)
        cx, cy = int(self.x + camera_shake), int(self.y)
        size = self.size
        # 身体
        body_rect = pygame.Rect(cx - size, cy - size // 2, size * 2, size)
        pygame.draw.ellipse(surface, self.color, body_rect)
        # 尾部
        tail_points = [
            (cx - size - 4, cy),
            (cx - size - 10, cy - size // 2),
            (cx - size - 10, cy + size // 2),
        ]
        pygame.draw.polygon(surface, self.color, tail_points)
        # 眼睛
        eye_x = cx + size // 3
        eye_y = cy - size // 6
        pygame.draw.circle(surface, COLORS["white"], (eye_x, eye_y), max(3, size // 8))
        pygame.draw.circle(surface, COLORS["black"], (eye_x + 1, eye_y), max(1, size // 14))
        # 鱼鳞纹理 (简单线条)
        for i in range(-1, 2):
            sx = cx + i * size // 3
            sy = cy - size // 4
            pygame.draw.arc(surface, (min(255, self.color[0] + 20),
                                       min(255, self.color[1] + 20),
                                       min(255, self.color[2] + 20)),
                            (sx - 4, sy, 8, size // 2), 0, math.pi, 1)
        # 鱼鳍
        fin_points = [
            (cx, cy - size // 2),
            (cx + size // 4, cy - size),
            (cx + size // 2, cy - size // 2),
        ]
        pygame.draw.polygon(surface, (min(255, self.color[0] + 30),
                                       min(255, self.color[1] + 30),
                                       min(255, self.color[2] + 30)), fin_points)

        # 稀有度特效
        if self.rarity <= 5:
            glow = int((math.sin(self.wobble * 3) + 1) * 60)
            glow_color = (255, glow, glow, 100)
            glow_surf = pygame.Surface((size * 3, size * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surf, glow_color, (0, 0, size * 3, size * 2))
            surface.blit(glow_surf, (cx - size * 1.5, cy - size))


# ==================== 游戏主类 ====================
class FishingGame:
    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.state = GameState.IDLE
        self.score = 0
        self.total_caught = 0
        self.time_left = 60
        self.game_timer = 0
        self.last_time_update = 0

        # 抛竿相关
        self.cast_power = 0
        self.cast_power_dir = 1
        self.cast_distance = 0
        self.line_angle = 0
        self.line_in_water = False
        self.bobber_x = 0
        self.bobber_y = 0
        self.bobber_float_offset = 0
        self.bobber_splash = 0
        self.bobber_ripple = 0
        self.ripple_radius = 0

        # 鱼相关
        self.fishes = [Fish() for _ in range(6)]
        self.active_fish = None
        self.bite_count = 0
        self.bite_direction = 0  # 鱼漂拉扯方向
        self.bite_strength = 0
        self.hook_struggle = 0
        self.reel_progress = 0
        self.reel_direction = 1  # 收线方向

        # 视觉效果
        self.camera_shake = 0
        self.particles = []
        self.caught_fish_display = None
        self.caught_fish_timer = 0
        self.message = ""
        self.message_timer = 0
        self.combo_count = 0
        self.combo_timer = 0

        # 水面波纹
        self.wave_offset = 0

    def add_particles(self, x, y, color, count=10, speed=3):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(1, speed)
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * spd,
                "vy": math.sin(angle) * spd - 1,
                "life": random.randint(20, 40),
                "max_life": 40,
                "color": color,
                "size": random.randint(2, 5),
            })

    def set_message(self, text, duration=90):
        self.message = text
        self.message_timer = duration

    def cast_line(self):
        if self.state == GameState.IDLE:
            self.state = GameState.CASTING
            self.cast_power = 0
            self.cast_power_dir = 1

    def release_cast(self):
        if self.state == GameState.CASTING:
            power = self.cast_power / 100.0
            self.cast_distance = 100 + power * 400
            self.line_angle = -60 - power * 30  # 角度
            self.state = GameState.FISHING

            # 计算鱼漂位置
            rad = math.radians(90 + self.line_angle)
            self.bobber_x = 150 + math.cos(rad) * self.cast_distance
            self.bobber_y = 200 + math.sin(rad) * self.cast_distance
            self.bobber_y = max(260, self.bobber_y)

            # 水花效果
            if self.bobber_y > 250:
                self.bobber_splash = 15
                self.ripple_radius = 0
                self.line_in_water = True
                self.add_particles(self.bobber_x, self.bobber_y,
                                   COLORS["water_surface"], 15, 4)
            else:
                self.line_in_water = False

            self.bite_count = 0
            self.active_fish = None

    def hook_fish(self):
        if self.state == GameState.BITING:
            self.state = GameState.HOOKED
            self.hook_struggle = 0
            self.reel_progress = 0
            self.camera_shake = 5
            self.set_message("上钩了！快速点击收线！", 120)

    def update(self):
        self.wave_offset += 0.02
        self.game_timer += 1

        # 计时器
        if self.game_timer - self.last_time_update >= 60:
            self.last_time_update = self.game_timer
            self.time_left -= 1
            if self.time_left <= 0:
                self.time_left = 0
                self.state = GameState.GAMEOVER

        # 更新粒子
        self.particles = [p for p in self.particles if p["life"] > 0]
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.05
            p["life"] -= 1
            p["size"] = max(1, p["size"] - 0.05)

        # 相机抖动衰减
        if self.camera_shake > 0:
            self.camera_shake *= 0.9
            if self.camera_shake < 0.1:
                self.camera_shake = 0

        # 消息计时
        if self.message_timer > 0:
            self.message_timer -= 1

        # 连击计时
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo_count = 0

        # 捕获展示计时
        if self.caught_fish_timer > 0:
            self.caught_fish_timer -= 1

        # 更新鱼漂波纹
        if self.bobber_splash > 0:
            self.bobber_splash -= 0.5
        if self.line_in_water:
            self.ripple_radius += 0.5
            if self.ripple_radius > 40:
                self.ripple_radius = 0
            self.bobber_float_offset = math.sin(self.wave_offset * 2 +
                                                self.bobber_x * 0.01) * 3

        # 更新鱼
        for fish in self.fishes:
            result = fish.update(self.bobber_x, self.bobber_y + self.bobber_float_offset,
                                 self.line_in_water)
            if result == "bite" and self.state == GameState.FISHING:
                self.active_fish = fish
                self.state = GameState.BITING
                self.bite_count = 0
                self.bite_direction = random.choice([-1, 1])
                self.bite_strength = random.uniform(2, 5)
                self.set_message("鱼在试探... 注意观察鱼漂！", 60)

        # 咬钩阶段
        if self.state == GameState.BITING:
            self.bite_count += 1
            self.bite_direction = -self.bite_direction if random.random() < 0.1 else self.bite_direction
            # 鱼漂上下抖动
            self.bobber_float_offset += self.bite_direction * self.bite_strength * 0.3
            self.bobber_float_offset = max(-15, min(15, self.bobber_float_offset))

            # 鱼漂下沉表示鱼真的咬钩了
            if self.bite_count > 80 and random.random() < 0.02:
                self.bobber_float_offset = 20  # 沉下去
                self.set_message("咬钩了！快收竿！", 60)

            # 鱼可能跑掉
            if self.bite_count > 200 and random.random() < 0.005:
                self.active_fish = None
                self.state = GameState.FISHING
                self.set_message("鱼跑了...", 60)

        # 收线阶段
        if self.state == GameState.HOOKED:
            self.hook_struggle += 1
            # 鱼挣扎
            struggle = math.sin(self.hook_struggle * 0.1) * 3
            self.bobber_float_offset = 15 + struggle
            self.camera_shake = max(self.camera_shake, 2)

            # 自动收线 (缓慢)
            self.reel_progress += 0.2
            # 挣扎会减少进度
            if abs(struggle) > 2:
                self.reel_progress -= 0.1

            if self.reel_progress >= 100:
                # 钓上来了！
                self.catch_fish()
            elif self.reel_progress < -20:
                # 鱼跑了
                self.active_fish = None
                self.state = GameState.FISHING
                self.camera_shake = 0
                self.set_message("鱼挣脱了！", 60)

        # 更新鱼
        for fish in self.fishes:
            if self.state == GameState.HOOKED and fish == self.active_fish:
                fish.x = self.bobber_x + math.sin(self.hook_struggle * 0.1) * 20
                fish.y = self.bobber_y + 10 + math.cos(self.hook_struggle * 0.15) * 10
            else:
                fish.update(self.bobber_x, self.bobber_y + self.bobber_float_offset,
                            self.line_in_water)

    def catch_fish(self):
        if self.active_fish:
            fish = self.active_fish
            fish.caught = True
            self.total_caught += 1
            self.combo_count += 1
            self.combo_timer = 180  # 3秒内连击

            bonus = 1.0
            if self.combo_count >= 3:
                bonus = 1.5
                self.set_message(f"连击 x{self.combo_count}! 1.5倍分数!", 90)
            elif self.combo_count >= 2:
                bonus = 1.2
                self.set_message("连击 x2!", 60)

            points = int(fish.score * bonus)
            self.score += points

            # 特效
            self.add_particles(fish.x, fish.y, (255, 215, 0), 20, 5)
            self.add_particles(fish.x, fish.y, fish.color, 15, 4)

            self.caught_fish_display = fish
            self.caught_fish_timer = 120

            self.set_message(f"钓到 {fish.name}! +{points}分", 90)

            # 鱼沉底后消失
            self.fishes.remove(fish)
            # 补充新鱼
            self.fishes.append(Fish())

            self.active_fish = None
            self.state = GameState.FISHING
            self.camera_shake = 0
            self.reel_progress = 0

    def reel_in(self):
        """玩家点击收线"""
        if self.state == GameState.HOOKED:
            self.reel_progress += 8
            self.camera_shake = 5
            self.add_particles(self.bobber_x, self.bobber_y,
                               COLORS["water_surface"], 3, 2)

    # ==================== 绘制 ====================
    def draw(self, surface):
        shake_x = random.uniform(-1, 1) * self.camera_shake
        shake_y = random.uniform(-1, 1) * self.camera_shake

        # --- 天空 ---
        for y in range(200):
            t = y / 200
            r = int(COLORS["sky_top"][0] * (1 - t) + COLORS["sky"][0] * t)
            g = int(COLORS["sky_top"][1] * (1 - t) + COLORS["sky"][1] * t)
            b = int(COLORS["sky_top"][2] * (1 - t) + COLORS["sky"][2] * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

        # 太阳
        pygame.draw.circle(surface, (255, 240, 200), (650, 60), 40)
        pygame.draw.circle(surface, (255, 220, 150), (650, 60), 35)
        # 阳光
        for i in range(8):
            angle = math.radians(i * 45 + self.game_timer * 0.5)
            x = 650 + math.cos(angle) * 55
            y = 60 + math.sin(angle) * 55
            pygame.draw.line(surface, (255, 240, 150, 80),
                             (650, 60), (x, y), 2)

        # 云朵
        cloud_offset = (self.game_timer * 0.1) % 900
        self.draw_cloud(surface, 100 - cloud_offset, 40, 1.0)
        self.draw_cloud(surface, 400 - cloud_offset * 0.7, 70, 0.8)
        self.draw_cloud(surface, 700 - cloud_offset * 1.2, 30, 1.2)

        # 远山
        for i in range(10):
            x = i * 90
            h = 60 + math.sin(i * 1.5) * 30
            pygame.draw.polygon(surface, (100, 160, 100),
                                [(x, 200), (x + 45, 200 - h), (x + 90, 200)])

        # --- 地面 ---
        pygame.draw.rect(surface, COLORS["grass"], (0, 190, WIDTH, 30))
        pygame.draw.rect(surface, COLORS["dirt"], (0, 210, WIDTH, 50))

        # 草地细节
        for i in range(0, WIDTH, 8):
            h = random.randint(3, 8) if i % 16 == 0 else 0
            pygame.draw.line(surface, COLORS["grass_dark"],
                             (i, 190), (i, 190 - h), 2)

        # --- 水面 ---
        water_rect = pygame.Rect(0, 250, WIDTH, 350)
        # 渐变水面
        for y in range(250, HEIGHT):
            t = (y - 250) / 350
            r = int(COLORS["water"][0] * (1 - t) + COLORS["water_deep"][0] * t)
            g = int(COLORS["water"][1] * (1 - t) + COLORS["water_deep"][1] * t)
            b = int(COLORS["water"][2] * (1 - t) + COLORS["water_deep"][2] * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

        # 水面波纹
        for x in range(0, WIDTH, 20):
            wave_y = 250 + math.sin((x + self.wave_offset * 20) * 0.05) * 3
            wave_y += math.sin((x * 0.02 + self.wave_offset * 10)) * 2
            alpha = 30 + math.sin(x * 0.1 + self.wave_offset * 5) * 15
            pygame.draw.line(surface, (255, 255, 255, alpha),
                             (x, wave_y), (x + 10, wave_y + 1), 2)

        # --- 钓鱼平台 ---
        # 码头
        dock_points = [(0, 220), (0, 260), (160, 260), (160, 220)]
        pygame.draw.polygon(surface, COLORS["wood"], dock_points)
        pygame.draw.polygon(surface, (120, 80, 40), dock_points, 2)
        # 木板纹理
        for i in range(5):
            x = i * 32
            pygame.draw.line(surface, (140, 100, 50),
                             (x, 220), (x, 260), 1)

        # 码头柱子
        for x in [20, 60, 100, 140]:
            pygame.draw.rect(surface, (100, 70, 30), (x, 255, 8, 20))
            pygame.draw.rect(surface, (80, 55, 20), (x, 255, 8, 20), 1)

        # --- 钓鱼竿 ---
        rod_base_x = 130
        rod_base_y = 230

        if self.state in [GameState.IDLE, GameState.CASTING]:
            # 鱼竿
            if self.state == GameState.IDLE:
                angle = -45
            else:
                power_angle = -45 - self.cast_power * 0.6
                angle = power_angle

            rad = math.radians(angle)
            rod_length = 180
            rod_tip_x = rod_base_x + math.cos(rad) * rod_length
            rod_tip_y = rod_base_y + math.sin(rad) * rod_length

            # 竿身
            pygame.draw.line(surface, COLORS["rod"],
                             (rod_base_x, rod_base_y), (rod_tip_x, rod_tip_y), 6)
            pygame.draw.line(surface, (120, 90, 50),
                             (rod_base_x, rod_base_y), (rod_tip_x, rod_tip_y), 3)

            # 鱼线 (从竿稍到水面)
            line_end_x = rod_tip_x
            line_end_y = min(rod_tip_y + 80, 255)
            pygame.draw.line(surface, COLORS["line"],
                             (rod_tip_x, rod_tip_y), (line_end_x, line_end_y), 1)

            # 鱼漂在线上
            if self.state == GameState.IDLE:
                bobber_x = line_end_x
                bobber_y = line_end_y
                pygame.draw.circle(surface, COLORS["bobber_top"],
                                   (int(bobber_x), int(bobber_y)), 6)
                pygame.draw.circle(surface, COLORS["bobber_bottom"],
                                   (int(bobber_x), int(bobber_y + 4)), 4)

        else:
            # 鱼竿抬起
            rad = math.radians(-60)
            rod_tip_x = rod_base_x + math.cos(rad) * 180
            rod_tip_y = rod_base_y + math.sin(rad) * 180
            pygame.draw.line(surface, COLORS["rod"],
                             (rod_base_x, rod_base_y), (rod_tip_x, rod_tip_y), 6)
            pygame.draw.line(surface, (120, 90, 50),
                             (rod_base_x, rod_base_y), (rod_tip_x, rod_tip_y), 3)

            # 鱼线到鱼漂
            if self.line_in_water:
                # 鱼线曲线 (用二次贝塞尔)
                mid_x = (rod_tip_x + self.bobber_x + shake_x) / 2
                mid_y = min(rod_tip_y, self.bobber_y + self.bobber_float_offset) + 40
                points = []
                for t in range(0, 11):
                    t_norm = t / 10
                    px = (1 - t_norm) ** 2 * rod_tip_x + \
                         2 * (1 - t_norm) * t_norm * mid_x + \
                         t_norm ** 2 * (self.bobber_x + shake_x)
                    py = (1 - t_norm) ** 2 * rod_tip_y + \
                         2 * (1 - t_norm) * t_norm * mid_y + \
                         t_norm ** 2 * (self.bobber_y + self.bobber_float_offset)
                    points.append((int(px), int(py)))
                if len(points) > 1:
                    pygame.draw.lines(surface, COLORS["line"], False, points, 1)

                # 鱼漂
                bbx = int(self.bobber_x + shake_x)
                bby = int(self.bobber_y + self.bobber_float_offset)

                # 水花
                if self.bobber_splash > 0:
                    for i in range(5):
                        a = random.uniform(0, math.pi * 2)
                        r = random.uniform(5, self.bobber_splash * 2)
                        sx = bbx + math.cos(a) * r
                        sy = bby + math.sin(a) * r * 0.3
                        pygame.draw.circle(surface, COLORS["water_surface"],
                                           (int(sx), int(sy)), random.randint(1, 3))

                # 波纹
                if self.ripple_radius > 0:
                    alpha = max(0, 100 - self.ripple_radius * 2)
                    ripple_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    pygame.draw.circle(ripple_surf, (255, 255, 255, alpha),
                                       (bbx, bby), int(self.ripple_radius), 1)
                    surface.blit(ripple_surf, (0, 0))

                # 鱼漂本体
                if self.state == GameState.BITING:
                    # 抖动
                    jitter = random.randint(-2, 2)
                    bbx += jitter
                pygame.draw.circle(surface, COLORS["bobber_top"], (bbx, bby - 3), 6)
                pygame.draw.circle(surface, COLORS["bobber_bottom"], (bbx, bby + 3), 5)
                # 鱼漂顶部的亮光
                pygame.draw.circle(surface, (255, 100, 100), (bbx - 1, bby - 4), 2)

                # 水下鱼线
                pygame.draw.line(surface, (150, 150, 150, 100),
                                 (bbx, bby + 8), (bbx, bby + 30), 1)
            else:
                # 鱼线没有入水
                line_end_x = rod_tip_x
                line_end_y = rod_tip_y + 100
                pygame.draw.line(surface, COLORS["line"],
                                 (rod_tip_x, rod_tip_y), (line_end_x, line_end_y), 1)
                pygame.draw.circle(surface, COLORS["bobber_top"],
                                   (int(line_end_x), int(line_end_y)), 6)

        # --- 绘制鱼 (水下) ---
        for fish in self.fishes:
            if fish != self.active_fish or self.state != GameState.HOOKED:
                fish.draw(surface, 0)

        # 上钩的鱼画在最上层
        if self.state == GameState.HOOKED and self.active_fish:
            self.active_fish.draw(surface, shake_x)

        # --- 水底装饰 ---
        # 水草
        for i in range(8):
            gx = 100 + i * 90 + math.sin(i) * 30
            gy = 580
            sway = math.sin(self.wave_offset * 2 + i) * 5
            pygame.draw.ellipse(surface, (30, 120, 30),
                                (gx + sway, gy - 40, 15, 40))
            pygame.draw.ellipse(surface, (40, 140, 40),
                                (gx + sway + 3, gy - 30, 10, 30))

        # 石头
        stone_positions = [(250, 570), (500, 575), (650, 565)]
        for sx, sy in stone_positions:
            pygame.draw.ellipse(surface, (80, 80, 80), (sx, sy, 25, 15))
            pygame.draw.ellipse(surface, (100, 100, 100), (sx + 2, sy - 2, 20, 10))

        # --- 粒子 ---
        for p in self.particles:
            alpha = int(255 * (p["life"] / p["max_life"]))
            color = (*p["color"][:3], alpha)
            p_surf = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, color, (p["size"], p["size"]), p["size"])
            surface.blit(p_surf, (int(p["x"] - p["size"]), int(p["y"] - p["size"])))

        # --- 捕获展示 ---
        if self.caught_fish_timer > 0 and self.caught_fish_display:
            fish = self.caught_fish_display
            cx, cy = WIDTH // 2, 140
            alpha = min(255, self.caught_fish_timer * 3)
            # 背景框
            bg_surf = pygame.Surface((300, 80), pygame.SRCALPHA)
            bg_surf.fill((0, 0, 0, 180))
            surface.blit(bg_surf, (cx - 150, cy - 40))

            # 鱼
            fish.draw(surface, 0)
            # 文字
            text = font_medium.render(f"+{int(fish.score * (1.5 if self.combo_count >= 3 else 1.2 if self.combo_count >= 2 else 1))} {fish.name}",
                                      True, COLORS["gold"])
            text_rect = text.get_rect(center=(cx, cy + 30))
            surface.blit(text, text_rect)

        # --- UI ---
        self.draw_ui(surface)

        # --- 消息 ---
        if self.message_timer > 0:
            msg_alpha = min(255, self.message_timer * 3)
            msg_surf = pygame.Surface((400, 40), pygame.SRCALPHA)
            msg_surf.fill((0, 0, 0, 160))
            surface.blit(msg_surf, (WIDTH // 2 - 200, 300))

            msg_text = font_small.render(self.message, True, COLORS["white"])
            msg_rect = msg_text.get_rect(center=(WIDTH // 2, 320))
            surface.blit(msg_text, msg_rect)

        # --- 蓄力条 ---
        if self.state == GameState.CASTING:
            bar_width = 200
            bar_height = 20
            bar_x = WIDTH // 2 - bar_width // 2
            bar_y = 400
            pygame.draw.rect(surface, (60, 60, 60),
                             (bar_x, bar_y, bar_width, bar_height))
            fill_width = int(bar_width * self.cast_power / 100)
            color = (50 + int(self.cast_power * 2),
                     200 - int(self.cast_power * 1.5),
                     50)
            pygame.draw.rect(surface, color,
                             (bar_x, bar_y, fill_width, bar_height))
            pygame.draw.rect(surface, COLORS["white"],
                             (bar_x, bar_y, bar_width, bar_height), 2)
            power_text = font_small.render(f"蓄力: {int(self.cast_power)}%",
                                           True, COLORS["white"])
            surface.blit(power_text, (bar_x, bar_y - 25))

        # --- 游戏结束 ---
        if self.state == GameState.GAMEOVER:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))

            title = font_large.render("🎣 钓鱼结束!", True, COLORS["gold"])
            surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 180))

            score_text = font_large.render(f"最终得分: {self.score}", True, COLORS["white"])
            surface.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 240))

            fish_text = font_medium.render(f"钓到 {self.total_caught} 条鱼", True, (200, 200, 200))
            surface.blit(fish_text, (WIDTH // 2 - fish_text.get_width() // 2, 290))

            if self.total_caught > 0:
                avg = self.score // self.total_caught
                avg_text = font_small.render(f"平均每条 {avg} 分", True, (180, 180, 180))
                surface.blit(avg_text, (WIDTH // 2 - avg_text.get_width() // 2, 330))

            restart_text = font_medium.render("按 R 重新开始, 按 ESC 退出", True, COLORS["white"])
            surface.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, 400))

    def draw_cloud(self, surface, x, y, scale):
        s = scale
        clouds = [(x, y, 40 * s), (x + 30 * s, y - 10 * s, 30 * s),
                  (x + 50 * s, y, 35 * s), (x + 20 * s, y + 5 * s, 25 * s)]
        for cx, cy, r in clouds:
            cloud_surf = pygame.Surface((int(r * 2), int(r * 2)), pygame.SRCALPHA)
            pygame.draw.circle(cloud_surf, (255, 255, 255, 180),
                               (int(r), int(r)), int(r))
            surface.blit(cloud_surf, (int(cx - r), int(cy - r)))

    def draw_ui(self, surface):
        # 左上角: 分数和计时器
        ui_bg = pygame.Surface((250, 100), pygame.SRCALPHA)
        ui_bg.fill((0, 0, 0, 120))
        surface.blit(ui_bg, (10, 10))

        score_text = font_medium.render(f"得分: {self.score}", True, COLORS["gold"])
        surface.blit(score_text, (20, 15))

        time_color = COLORS["red"] if self.time_left <= 10 else COLORS["white"]
        time_text = font_medium.render(f"时间: {self.time_left}s", True, time_color)
        surface.blit(time_text, (20, 45))

        fish_count_text = font_small.render(f"已钓: {self.total_caught} 条", True, (200, 200, 200))
        surface.blit(fish_count_text, (20, 75))

        # 连击显示
        if self.combo_count >= 2:
            combo_text = font_medium.render(f"连击 x{self.combo_count}!", True, COLORS["red"])
            surface.blit(combo_text, (150, 75))

        # 底部提示
        if self.state == GameState.IDLE:
            hint = font_small.render("点击鼠标左键蓄力抛竿", True, COLORS["white"])
            surface.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))
        elif self.state == GameState.FISHING:
            hint = font_small.render("等待鱼儿上钩...", True, (200, 200, 200))
            surface.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))
        elif self.state == GameState.BITING:
            hint = font_small.render("鱼在咬钩! 点击鼠标收竿!", True, COLORS["red"])
            surface.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))
        elif self.state == GameState.HOOKED:
            hint = font_small.render("疯狂点击鼠标收线!", True, COLORS["green"])
            surface.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))

        # 鱼类图鉴 (右上角)
        legend_bg = pygame.Surface((160, 200), pygame.SRCALPHA)
        legend_bg.fill((0, 0, 0, 100))
        surface.blit(legend_bg, (WIDTH - 170, 10))
        legend_title = font_small.render("🐟 鱼类图鉴", True, COLORS["gold"])
        surface.blit(legend_title, (WIDTH - 160, 15))
        for i, ft in enumerate(FISH_TYPES):
            rarity_stars = "★" * max(1, 5 - ft["rarity"] // 8)
            color = ft["color"]
            # 稀有度颜色
            if ft["rarity"] <= 5:
                name_color = (255, 200, 50)
            elif ft["rarity"] <= 10:
                name_color = (200, 150, 255)
            else:
                name_color = (200, 200, 200)
            text = font_small.render(f"{ft['name']} {ft['score']}分", True, name_color)
            surface.blit(text, (WIDTH - 160, 35 + i * 20))


# ==================== 主循环 ====================
def main():
    game = FishingGame()
    running = True
    show_instructions = True
    instr_timer = 180  # 3秒

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r and game.state == GameState.GAMEOVER:
                    game.reset_game()
                    show_instructions = True
                    instr_timer = 180

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game.state == GameState.GAMEOVER:
                    continue
                if game.state == GameState.IDLE:
                    game.cast_line()
                elif game.state == GameState.CASTING:
                    game.release_cast()
                elif game.state == GameState.BITING:
                    game.hook_fish()
                elif game.state == GameState.HOOKED:
                    game.reel_in()

        # 蓄力自动涨落
        if game.state == GameState.CASTING:
            game.cast_power += game.cast_power_dir * 1.5
            if game.cast_power >= 100:
                game.cast_power = 100
                game.cast_power_dir = -1
            elif game.cast_power <= 0:
                game.cast_power = 0
                game.cast_power_dir = 1
                # 自动释放
                game.release_cast()

        game.update()

        # 清屏
        screen.fill((0, 0, 0))
        game.draw(screen)

        # 操作说明 (刚启动时显示)
        if show_instructions:
            if instr_timer > 0:
                instr_timer -= 1
                instr_surf = pygame.Surface((500, 120), pygame.SRCALPHA)
                instr_surf.fill((0, 0, 0, 200))
                screen.blit(instr_surf, (WIDTH // 2 - 250, 80))

                lines = [
                    "🎣 钓鱼大师 - 操作说明",
                    "1. 点击鼠标左键 - 开始蓄力抛竿",
                    "2. 蓄力到合适位置时，再次点击释放抛竿",
                    "3. 鱼漂抖动时，快速点击收竿钓鱼",
                    "4. 鱼上钩后，疯狂点击鼠标收线",
                ]
                for i, line in enumerate(lines):
                    if i == 0:
                        text = font_medium.render(line, True, COLORS["gold"])
                    else:
                        text = font_small.render(line, True, COLORS["white"])
                    screen.blit(text, (WIDTH // 2 - 230, 90 + i * 22))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()