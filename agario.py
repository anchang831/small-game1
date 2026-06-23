"""
球球大作战 (Agar.io)
====================
一个 Agar.io 风格的多人竞技游戏
- WASD / 方向键 移动
- 吃彩色食物颗粒长大
- AI 机器人也会成长
- 大的球可以吃掉小的球
- 按 Space 分裂（质量 > 50 时）
- 按 ESC 暂停 / 重新开始

作者: AI 游戏开发者
日期: 2026-06-23
"""

import pygame
import math
import random
import sys

# ===== 初始化 =====
pygame.init()

# ===== 常量 =====
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700
FPS = 60
WORLD_WIDTH, WORLD_HEIGHT = 3000, 3000  # 世界地图大小

# 颜色
COLORS = {
    "bg": (240, 240, 240),
    "grid": (220, 220, 220),
    "food": [
        (255, 99, 71),   # 番茄红
        (100, 149, 237), # 矢车菊蓝
        (50, 205, 50),   # 酸橙绿
        (255, 215, 0),   # 金色
        (255, 105, 180), # 热粉色
        (147, 112, 219), # 中紫
        (0, 206, 209),   # 暗宝石绿
        (255, 165, 0),   # 橙色
    ],
    "player": (70, 130, 180),       # 钢蓝
    "player_outline": (50, 100, 150),
    "bot_names": [
        (220, 50, 50), (50, 180, 50), (180, 50, 180),
        (200, 150, 30), (30, 150, 200), (200, 80, 30),
        (80, 200, 150), (150, 80, 200), (200, 130, 80),
    ],
    "white": (255, 255, 255),
    "black": (30, 30, 30),
    "gray": (100, 100, 100),
    "red": (200, 50, 50),
    "overlay": (0, 0, 0, 128),
}

# 名字列表
PLAYER_NAMES = [
    "玩家", "Bot-Alpha", "Bot-Beta", "Bot-Gamma", "Bot-Delta",
    "Bot-Epsilon", "Bot-Zeta", "Bot-Eta", "Bot-Theta", "Bot-Iota"
]

# ===== 设置屏幕 =====
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("球球大作战 - Agar.io")
clock = pygame.time.Clock()
font_small = pygame.font.SysFont("simhei", 16, bold=True)
font_medium = pygame.font.SysFont("simhei", 24, bold=True)
font_large = pygame.font.SysFont("simhei", 48, bold=True)
font_score = pygame.font.SysFont("simhei", 20, bold=True)


# ===== 工具函数 =====
def distance(a, b):
    """计算两点之间的距离"""
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return math.sqrt(dx * dx + dy * dy)


def random_color():
    """生成随机鲜艳的颜色"""
    while True:
        r = random.randint(50, 255)
        g = random.randint(50, 255)
        b = random.randint(50, 255)
        if abs(r - g) + abs(g - b) + abs(b - r) > 200:
            return (r, g, b)


def random_name(exclude=None):
    """生成随机名字"""
    names = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta",
             "Eta", "Theta", "Iota", "Kappa", "Lambda", "Mu",
             "Nu", "Xi", "Omicron", "Pi", "Rho", "Sigma"]
    name = random.choice(names)
    if exclude and name in exclude:
        return random_name(exclude)
    return name


# ===== 食物类 =====
class Food:
    """地图上的食物颗粒"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = random.randint(4, 7)
        self.color = random.choice(COLORS["food"])
        self.mass = self.radius * 0.3

    def draw(self, surface, camera_x, camera_y):
        """绘制食物"""
        sx = self.x - camera_x
        sy = self.y - camera_y
        # 屏幕裁剪
        margin = 10
        if (-margin <= sx <= SCREEN_WIDTH + margin and
                -margin <= sy <= SCREEN_HEIGHT + margin):
            pygame.draw.circle(surface, self.color, (int(sx), int(sy)), self.radius)


# ===== 细胞（玩家/AI）类 =====
class Cell:
    """细胞类 - 玩家和 AI 都使用此类"""
    def __init__(self, x, y, radius, color, name, is_player=False):
        self.x = x
        self.y = y
        self.radius = radius
        self.mass = radius * radius * 0.01  # 质量 ≈ r²
        self.color = color
        self.outline_color = tuple(max(0, c - 40) for c in color[:3])
        self.name = name
        self.is_player = is_player
        self.speed = 0
        self.target_x = x
        self.target_y = y

        # AI 属性
        self.ai_target_food = None  # 目标食物
        self.ai_target_cell = None  # 目标可吃的细胞
        self.ai_danger_cell = None  # 危险细胞（比自己大）
        self.ai_wander_angle = random.random() * math.pi * 2
        self.ai_wander_timer = 0

    def mass_to_radius(self, mass):
        """根据质量计算半径"""
        return math.sqrt(mass / 0.01)

    def add_mass(self, amount):
        """增加质量并更新半径"""
        self.mass += amount
        self.radius = self.mass_to_radius(self.mass)

    def get_speed(self):
        """根据大小计算移动速度"""
        # 越大越慢，但不会太慢
        return max(1.5, 6.0 - self.radius * 0.015)

    def can_eat(self, other):
        """判断能否吃掉另一个细胞"""
        return self.radius > other.radius * 1.25

    def update_ai(self, foods, cells, dt):
        """AI 逻辑更新"""
        if self.is_player:
            return

        self.ai_wander_timer -= dt
        if self.ai_wander_timer <= 0:
            self.ai_wander_angle += random.uniform(-1.0, 1.0)
            self.ai_wander_timer = random.uniform(0.5, 2.0)

        best_food = None
        best_food_dist = float('inf')

        # 寻找最近的食物
        for food in foods:
            d = distance((self.x, self.y), (food.x, food.y))
            if d < best_food_dist:
                best_food_dist = d
                best_food = food

        # 危险检测 - 远离比自己大的细胞
        danger_dir_x = 0
        danger_dir_y = 0
        for cell in cells:
            if cell is self:
                continue
            d = distance((self.x, self.y), (cell.x, cell.y))
            if cell.can_eat(self) and d < 400:
                # 逃离方向
                dx = self.x - cell.x
                dy = self.y - cell.y
                if d > 0:
                    danger_dir_x += dx / d * (400 - d) / 400
                    danger_dir_y += dy / d * (400 - d) / 400

        # 追踪比自己小的细胞
        chase_x, chase_y = 0, 0
        for cell in cells:
            if cell is self:
                continue
            d = distance((self.x, self.y), (cell.x, cell.y))
            if self.can_eat(cell) and d < 500:
                chase_x += (cell.x - self.x) / d * (500 - d) / 500
                chase_y += (cell.y - self.y) / d * (500 - d) / 500

        # 向食物移动
        food_dir_x, food_dir_y = 0, 0
        if best_food:
            d = best_food_dist
            if d > 0:
                food_dir_x = (best_food.x - self.x) / d
                food_dir_y = (best_food.y - self.y) / d

        # 随机漫游
        wander_x = math.cos(self.ai_wander_angle)
        wander_y = math.sin(self.ai_wander_angle)

        # 边界回避
        edge_x, edge_y = 0, 0
        margin = 100
        if self.x < margin:
            edge_x = (margin - self.x) / margin
        elif self.x > WORLD_WIDTH - margin:
            edge_x = (WORLD_WIDTH - margin - self.x) / margin
        if self.y < margin:
            edge_y = (margin - self.y) / margin
        elif self.y > WORLD_HEIGHT - margin:
            edge_y = (WORLD_HEIGHT - margin - self.y) / margin

        # 合成最终方向
        total_x = (food_dir_x * 2.0 + chase_x * 3.0 + danger_dir_x * 5.0 +
                   wander_x * 0.5 + edge_x * 3.0)
        total_y = (food_dir_y * 2.0 + chase_y * 3.0 + danger_dir_y * 5.0 +
                   wander_y * 0.5 + edge_y * 3.0)

        mag = math.sqrt(total_x * total_x + total_y * total_y)
        if mag > 0:
            total_x /= mag
            total_y /= mag

        ai_speed = self.get_speed()
        self.target_x = self.x + total_x * ai_speed * 60 * dt
        self.target_y = self.y + total_y * ai_speed * 60 * dt

        # 限制在世界边界内
        self.target_x = max(self.radius, min(WORLD_WIDTH - self.radius, self.target_x))
        self.target_y = max(self.radius, min(WORLD_HEIGHT - self.radius, self.target_y))

    def update(self, dt):
        """更新位置（向目标移动）"""
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        d = math.sqrt(dx * dx + dy * dy)
        if d > 1:
            speed = self.get_speed() * 60 * dt
            move = min(speed, d)  # 不超过剩余距离
            self.x += dx / d * move
            self.y += dy / d * move

        # 边界限制
        self.x = max(self.radius, min(WORLD_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(WORLD_HEIGHT - self.radius, self.y))

    def draw(self, surface, camera_x, camera_y):
        """绘制细胞"""
        sx = self.x - camera_x
        sy = self.y - camera_y

        # 屏幕裁剪（加边距）
        margin = self.radius + 5
        if (sx < -margin or sx > SCREEN_WIDTH + margin or
                sy < -margin or sy > SCREEN_HEIGHT + margin):
            return

        int_x, int_y = int(sx), int(sy)

        # 绘制外发光效果
        for i in range(3, 0, -1):
            alpha = 30 // i
            glow_surf = pygame.Surface((int(self.radius * 2) + i * 8,
                                        int(self.radius * 2) + i * 8),
                                       pygame.SRCALPHA)
            glow_color = (*self.color[:3], alpha)
            pygame.draw.circle(glow_surf, glow_color,
                               (glow_surf.get_width() // 2,
                                glow_surf.get_height() // 2),
                               self.radius + i * 4)
            surface.blit(glow_surf,
                         (int_x - glow_surf.get_width() // 2,
                          int_y - glow_surf.get_height() // 2))

        # 绘制主体
        pygame.draw.circle(surface, self.color, (int_x, int_y),
                           int(self.radius))
        # 边框
        pygame.draw.circle(surface, self.outline_color,
                           (int_x, int_y), int(self.radius), 3)

        # 高光效果
        highlight_offset = int(self.radius * 0.3)
        pygame.draw.circle(surface, (255, 255, 255, 80),
                           (int_x - highlight_offset,
                            int_y - highlight_offset),
                           int(self.radius * 0.4), 0)

        # 绘制名字（如果半径够大）
        if self.radius > 12:
            name_size = max(12, min(24, int(self.radius * 0.5)))
            font_name = pygame.font.SysFont("simhei", name_size, bold=True)
            text = font_name.render(self.name, True, COLORS["white"])
            text_rect = text.get_rect(center=(int_x, int_y))
            # 文字阴影
            shadow = font_name.render(self.name, True, (0, 0, 0))
            shadow_rect = shadow.get_rect(center=(int_x + 1, int_y + 1))
            surface.blit(shadow, shadow_rect)
            surface.blit(text, text_rect)

        # 质量显示
        if self.radius > 20 and self.is_player:
            mass_text = font_small.render(f"{int(self.mass)}", True,
                                          COLORS["white"])
            mass_rect = mass_text.get_rect(center=(int_x, int_y + name_size + 2))
            surface.blit(mass_text, mass_rect)


# ===== 游戏主类 =====
class AgarGame:
    """球球大作战主游戏类"""
    def __init__(self):
        self.reset()

    def reset(self):
        """重置游戏"""
        self.foods = []
        self.cells = []
        self.player = None
        self.running = True
        self.game_over = False
        self.paused = False
        self.score = 0
        self.high_score = 0

        # 生成食物
        self.spawn_foods(500)

        # 生成玩家
        start_x = random.randint(200, WORLD_WIDTH - 200)
        start_y = random.randint(200, WORLD_HEIGHT - 200)
        self.player = Cell(start_x, start_y, 25,
                           COLORS["player"], PLAYER_NAMES[0], is_player=True)
        self.cells.append(self.player)

        # 生成 AI 机器人
        for i in range(1, min(8, len(PLAYER_NAMES))):
            self.spawn_bot(PLAYER_NAMES[i])

        self.total_foods = 500
        self.spawn_timer = 0

    def spawn_foods(self, count):
        """生成指定数量的食物"""
        for _ in range(count):
            x = random.randint(10, WORLD_WIDTH - 10)
            y = random.randint(10, WORLD_HEIGHT - 10)
            self.foods.append(Food(x, y))

    def spawn_bot(self, name):
        """生成一个 AI 机器人"""
        for _ in range(50):
            x = random.randint(100, WORLD_WIDTH - 100)
            y = random.randint(100, WORLD_HEIGHT - 100)
            # 避免在玩家附近生成
            if self.player and distance((x, y), (self.player.x, self.player.y)) < 300:
                continue
            # 避免在其他AI附近生成
            too_close = False
            for cell in self.cells:
                if distance((x, y), (cell.x, cell.y)) < 200:
                    too_close = True
                    break
            if not too_close:
                break

        radius = random.randint(18, 30)
        color = random_color()
        bot = Cell(x, y, radius, color, name, is_player=False)
        self.cells.append(bot)
        return bot

    def handle_events(self):
        """处理输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_over:
                        self.reset()
                    else:
                        self.paused = not self.paused
                if event.key == pygame.K_SPACE and not self.game_over and not self.paused:
                    self.split_player()
                if event.key == pygame.K_r and self.game_over:
                    self.reset()
        return True

    def split_player(self):
        """玩家分裂"""
        if not self.player or self.player.mass < 50:
            return

        # 减半质量
        new_mass = self.player.mass / 2
        self.player.mass = new_mass
        self.player.radius = self.player.mass_to_radius(new_mass)

        # 创建分裂体
        import math
        mouse_x, mouse_y = pygame.mouse.get_pos()
        camera_x = self.player.x - SCREEN_WIDTH // 2
        camera_y = self.player.y - SCREEN_HEIGHT // 2
        world_mouse_x = mouse_x + camera_x
        world_mouse_y = mouse_y + camera_y

        dx = world_mouse_x - self.player.x
        dy = world_mouse_y - self.player.y
        d = math.sqrt(dx * dx + dy * dy)
        if d > 0:
            dx /= d
            dy /= d

        # 分裂出去的细胞
        split_cell = Cell(
            self.player.x + dx * self.player.radius * 1.5,
            self.player.y + dy * self.player.radius * 1.5,
            self.player.radius,
            self.player.color,
            self.player.name + "'",
        )
        split_cell.mass = new_mass
        split_cell.target_x = self.player.x + dx * 500
        split_cell.target_y = self.player.y + dy * 500
        split_cell.is_player = True  # 视为玩家的一部分
        self.cells.append(split_cell)

    def update(self, dt):
        """更新游戏状态"""
        if self.paused or self.game_over:
            return

        # 更新鼠标位置（玩家目标）
        if self.player:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            camera_x = self.player.x - SCREEN_WIDTH // 2
            camera_y = self.player.y - SCREEN_HEIGHT // 2
            self.player.target_x = mouse_x + camera_x
            self.player.target_y = mouse_y + camera_y

        # 更新 AI
        for cell in self.cells:
            cell.update_ai(self.foods, self.cells, dt)

        # 更新所有细胞位置
        for cell in self.cells:
            cell.update(dt)

        # 合并靠近的分裂细胞
        self.merge_cells()

        # 吃食物
        self.eat_food()

        # 细胞互相吃
        self.eat_cells()

        # 补充食物
        self.spawn_timer += dt
        if self.spawn_timer >= 0.1 and len(self.foods) < self.total_foods:
            self.spawn_foods(3)
            self.spawn_timer = 0

        # 检查游戏结束
        self.check_game_over()

    def merge_cells(self):
        """合并玩家分裂的细胞"""
        player_cells = [c for c in self.cells if c.is_player]
        if len(player_cells) <= 1:
            return

        for i, c1 in enumerate(player_cells):
            for c2 in player_cells[i + 1:]:
                d = distance((c1.x, c1.y), (c2.x, c2.y))
                if d < c1.radius + c2.radius:
                    # 合并到较大的细胞
                    if c1.mass >= c2.mass:
                        c1.mass += c2.mass
                        c1.radius = c1.mass_to_radius(c1.mass)
                        self.cells.remove(c2)
                    else:
                        c2.mass += c1.mass
                        c2.radius = c2.mass_to_radius(c2.mass)
                        self.cells.remove(c1)
                    break

    def eat_food(self):
        """细胞吃食物"""
        for cell in self.cells[:]:
            if cell not in self.cells:
                continue
            eaten = []
            for food in self.foods:
                d = distance((cell.x, cell.y), (food.x, food.y))
                if d < cell.radius:
                    cell.add_mass(food.mass * 0.5)
                    eaten.append(food)
            for food in eaten:
                self.foods.remove(food)

    def eat_cells(self):
        """细胞吃细胞"""
        # 按大小排序，大的先检查
        sorted_cells = sorted(self.cells, key=lambda c: c.mass, reverse=True)
        eaten = set()

        for predator in sorted_cells:
            if predator in eaten:
                continue
            for prey in self.cells[:]:
                if prey is predator or prey in eaten:
                    continue
                d = distance((predator.x, predator.y), (prey.x, prey.y))
                if d < predator.radius and predator.can_eat(prey):
                    predator.add_mass(prey.mass * 0.8)
                    eaten.add(prey)

        for cell in eaten:
            if cell in self.cells:
                self.cells.remove(cell)

        # 如果玩家被吃，重新生成
        if self.player and self.player not in self.cells:
            self.player = None

    def check_game_over(self):
        """检查游戏是否结束"""
        if not self.player and not self.game_over:
            self.game_over = True
            # 找到并显示分数
            for cell in self.cells:
                if cell.is_player:
                    self.player = cell
                    return
            # 真的死了
            pass

    def draw_grid(self, surface, camera_x, camera_y):
        """绘制背景网格"""
        grid_size = 40
        start_x = int(camera_x // grid_size) * grid_size
        start_y = int(camera_y // grid_size) * grid_size

        for x in range(start_x, int(camera_x + SCREEN_WIDTH), grid_size):
            pygame.draw.line(surface, COLORS["grid"],
                             (x - camera_x, 0),
                             (x - camera_x, SCREEN_HEIGHT), 1)
        for y in range(start_y, int(camera_y + SCREEN_HEIGHT), grid_size):
            pygame.draw.line(surface, COLORS["grid"],
                             (0, y - camera_y),
                             (SCREEN_WIDTH, y - camera_y), 1)

    def draw(self):
        """绘制整个画面"""
        # 计算摄像机位置（跟随玩家）
        camera_x, camera_y = 0, 0
        if self.player:
            camera_x = self.player.x - SCREEN_WIDTH // 2
            camera_y = self.player.y - SCREEN_HEIGHT // 2

        # 限制不超出世界边界
        camera_x = max(0, min(WORLD_WIDTH - SCREEN_WIDTH, camera_x))
        camera_y = max(0, min(WORLD_HEIGHT - SCREEN_HEIGHT, camera_y))

        # 绘制背景
        screen.fill(COLORS["bg"])
        self.draw_grid(screen, camera_x, camera_y)

        # 绘制食物
        for food in self.foods:
            food.draw(screen, camera_x, camera_y)

        # 绘制所有细胞（按大小排序，大的在上面）
        sorted_cells = sorted(self.cells, key=lambda c: c.mass)
        for cell in sorted_cells:
            cell.draw(screen, camera_x, camera_y)

        # ===== HUD =====
        if self.player:
            # 分数
            score_text = font_score.render(
                f"质量: {int(self.player.mass)}", True, COLORS["black"])
            screen.blit(score_text, (15, 15))

            # 排行
            rankings = sorted(self.cells, key=lambda c: c.mass, reverse=True)
            rank = 1
            for i, c in enumerate(rankings):
                if c is self.player:
                    rank = i + 1
                    break

            rank_text = font_score.render(
                f"排名: #{rank} / {len(self.cells)}", True, COLORS["black"])
            screen.blit(rank_text, (15, 40))

            # 食物数量
            food_text = font_score.render(
                f"食物: {len(self.foods)}", True, COLORS["gray"])
            screen.blit(food_text, (15, 65))

        if self.paused:
            # 暂停遮罩
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),
                                     pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            screen.blit(overlay, (0, 0))
            pause_text = font_large.render("暂停", True, COLORS["white"])
            pause_rect = pause_text.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(pause_text, pause_rect)
            hint_text = font_medium.render("按 ESC 继续", True, COLORS["white"])
            hint_rect = hint_text.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            screen.blit(hint_text, hint_rect)

        if self.game_over:
            # 游戏结束遮罩
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),
                                     pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            # "游戏结束" 标题
            title_text = font_large.render("游戏结束", True, COLORS["red"])
            title_rect = title_text.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
            screen.blit(title_text, title_rect)

            # 最终分数
            if self.player:
                score_text = font_medium.render(
                    f"最终质量: {int(self.player.mass)}", True, COLORS["white"])
                score_rect = score_text.get_rect(
                    center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
                screen.blit(score_text, score_rect)

                if self.player.mass > self.high_score:
                    self.high_score = self.player.mass
                    new_record = font_medium.render(
                        "新纪录!", True, (255, 215, 0))
                    new_record_rect = new_record.get_rect(
                        center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
                    screen.blit(new_record, new_record_rect)

            hint_text = font_medium.render(
                "按 R 重新开始 | ESC 退出", True, COLORS["white"])
            hint_rect = hint_text.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 90))
            screen.blit(hint_text, hint_rect)

        # 操作提示（左下角）
        if not self.game_over and not self.paused:
            help_lines = [
                "鼠标移动  控制方向",
                "Space     分裂",
                "ESC       暂停",
            ]
            y_offset = SCREEN_HEIGHT - 70
            for line in help_lines:
                help_text = font_small.render(line, True, COLORS["gray"])
                screen.blit(help_text, (15, y_offset))
                y_offset += 22

        # 排行榜（右上角）
        if not self.game_over and not self.paused:
            rankings = sorted(self.cells, key=lambda c: c.mass, reverse=True)
            top_n = min(5, len(rankings))
            rank_x = SCREEN_WIDTH - 180
            rank_y = 15

            title = font_small.render("--- 排行榜 ---", True, COLORS["black"])
            screen.blit(title, (rank_x, rank_y))
            rank_y += 25

            for i in range(top_n):
                cell = rankings[i]
                is_player = cell is self.player
                prefix = "🤖 " if not is_player else "🧑 "
                name = cell.name[:12]
                rank_color = COLORS["black"]
                if is_player:
                    rank_color = COLORS["player"]
                text = font_small.render(
                    f"{i + 1}. {prefix}{name} {int(cell.mass)}",
                    True, rank_color)
                screen.blit(text, (rank_x, rank_y))
                rank_y += 22

    def run(self):
        """主游戏循环"""
        while self.running:
            dt = clock.tick(FPS) / 1000.0  # 转换为秒
            dt = min(dt, 0.05)  # 防止卡顿时跳跃太大

            if not self.handle_events():
                self.running = False
                break

            self.update(dt)
            self.draw()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ===== 主入口 =====
if __name__ == "__main__":
    game = AgarGame()
    game.run()