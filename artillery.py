"""
火炮对决 (Artillery Duel)
========================
双人回合制火炮对战游戏
- 玩家1: WASD调整角度/力度, 空格发射
- 玩家2: 方向键调整角度/力度, Enter发射
- 风力和重力影响炮弹轨迹, 地形可破坏
"""

import pygame
import math
import random
import sys

# ========== 初始化 ==========
pygame.init()
pygame.display.set_caption("火炮对决 Artillery Duel")
clock = pygame.time.Clock()

# ========== 常量 ==========
WIDTH, HEIGHT = 900, 600
FPS = 60
GRAVITY = 0.15
FONT = None

# 颜色
COLORS = {
    "sky": (135, 206, 235),
    "ground": (101, 67, 33),
    "ground_top": (76, 153, 0),
    "player1": (220, 50, 50),
    "player2": (50, 100, 220),
    "projectile": (255, 200, 50),
    "trail": (255, 255, 200),
    "explosion": (255, 100, 0),
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "gray": (100, 100, 100),
    "wind_arrow": (200, 200, 100),
    "ui_bg": (0, 0, 0, 180),
}

# ========== 地形生成 ==========
def generate_terrain():
    """生成随机地形高度图"""
    heights = []
    step = WIDTH // 60
    for x in range(0, WIDTH + step, step):
        h = HEIGHT * 0.5 + random.uniform(-0.2, 0.2) * HEIGHT * 0.3
        # 中间高两边低的山脊效果
        mid_factor = 1 - abs(x / WIDTH - 0.5) * 2
        h -= mid_factor * HEIGHT * 0.15
        heights.append(int(h))
    return heights, step


def smooth_terrain(heights, step):
    """平滑地形"""
    smoothed = [heights[0]]
    for i in range(1, len(heights)):
        avg = (heights[i - 1] + heights[i]) // 2
        smoothed.append(avg)
    # 再次平滑
    result = [smoothed[0]]
    for i in range(1, len(smoothed)):
        avg = (smoothed[i - 1] + smoothed[i]) // 2
        result.append(avg)
    return result, step


def get_ground_y(x, terrain_heights, step):
    """获取指定x坐标的地面高度"""
    idx = int(x / step)
    if idx < 0:
        idx = 0
    if idx >= len(terrain_heights) - 1:
        idx = len(terrain_heights) - 2
    x0 = idx * step
    x1 = (idx + 1) * step
    y0 = terrain_heights[idx]
    y1 = terrain_heights[idx + 1]
    # 线性插值
    if x1 == x0:
        return y0
    t = (x - x0) / (x1 - x0)
    return int(y0 + (y1 - y0) * t)


# ========== 玩家类 ==========
class Player:
    def __init__(self, x, y, color, controls, name, facing_right):
        self.x = x
        self.y = y
        self.color = color
        self.controls = controls  # {"angle_up": ..., "angle_down": ..., "power_up": ..., "power_down": ..., "fire": ...}
        self.name = name
        self.facing_right = facing_right
        self.angle = 45 if facing_right else 135
        self.power = 50
        self.health = 100
        self.score = 0
        self.tank_w = 40
        self.tank_h = 20
        self.barrel_len = 35

    def draw(self, screen):
        # 坦克车身
        body_rect = pygame.Rect(
            self.x - self.tank_w // 2,
            self.y - self.tank_h,
            self.tank_w, self.tank_h
        )
        pygame.draw.rect(screen, self.color, body_rect, border_radius=3)

        # 炮管
        angle_rad = math.radians(self.angle)
        end_x = self.x + math.cos(angle_rad) * self.barrel_len
        end_y = self.y - self.tank_h // 2 - math.sin(angle_rad) * self.barrel_len
        pygame.draw.line(screen, self.color, (self.x, self.y - self.tank_h // 2),
                         (end_x, end_y), 5)

        # 炮塔圆
        pygame.draw.circle(screen, self.color, (self.x, self.y - self.tank_h // 2), 8)

        # 血量条
        bar_w = 50
        bar_h = 6
        bar_x = self.x - bar_w // 2
        bar_y = self.y - self.tank_h - 14
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        hp_w = int(bar_w * (self.health / 100))
        hp_color = (0, 255, 0) if self.health > 50 else (255, 255, 0) if self.health > 25 else (255, 0, 0)
        pygame.draw.rect(screen, hp_color, (bar_x, bar_y, hp_w, bar_h))

        # 名字
        text = FONT.render(self.name, True, self.color)
        screen.blit(text, (self.x - text.get_width() // 2, bar_y - 16))

    def get_barrel_tip(self):
        angle_rad = math.radians(self.angle)
        return (
            self.x + math.cos(angle_rad) * self.barrel_len,
            self.y - self.tank_h // 2 - math.sin(angle_rad) * self.barrel_len
        )


# ========== 炮弹类 ==========
class Projectile:
    def __init__(self, x, y, vx, vy, owner):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.owner = owner
        self.trail = []
        self.alive = True
        self.radius = 4

    def update(self, wind):
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 30:
            self.trail.pop(0)
        self.vx += wind * 0.02
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy

        # 出界
        if self.x < -20 or self.x > WIDTH + 20 or self.y > HEIGHT + 20:
            self.alive = False

    def draw(self, screen):
        # 轨迹
        for i, (tx, ty) in enumerate(self.trail):
            alpha = i / len(self.trail) * 255
            size = max(1, int(self.radius * (i / len(self.trail))))
            pygame.draw.circle(screen, COLORS["trail"], (tx, ty), size)
        # 炮弹
        pygame.draw.circle(screen, COLORS["projectile"], (int(self.x), int(self.y)), self.radius)
        # 发光效果
        pygame.draw.circle(screen, (255, 255, 200), (int(self.x), int(self.y)), self.radius + 2, 1)


# ========== 爆炸效果 ==========
class Explosion:
    def __init__(self, x, y, radius=30):
        self.x = x
        self.y = y
        self.radius = radius
        self.max_radius = radius
        self.life = 1.0
        self.particles = []
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 2,
                "life": random.uniform(0.5, 1.0),
            })

    def update(self):
        self.life -= 0.04
        self.radius = self.max_radius * (1 - self.life * 0.5)
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.1
            p["life"] -= 0.03
        return self.life > 0

    def draw(self, screen):
        # 爆炸圈
        if self.life > 0.3:
            alpha = int(255 * self.life)
            color = (255, int(100 * self.life), 0)
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), int(self.radius), 3)

        # 粒子
        for p in self.particles:
            if p["life"] > 0:
                alpha = int(255 * p["life"])
                color = (255, int(200 * p["life"]), 0)
                pygame.draw.circle(screen, color, (int(p["x"]), int(p["y"])), max(1, int(3 * p["life"])))


# ========== 地形破坏 ==========
def destroy_terrain(terrain_heights, step, cx, cy, radius):
    """在爆炸位置破坏地形"""
    start_idx = max(0, int((cx - radius) / step))
    end_idx = min(len(terrain_heights) - 1, int((cx + radius) / step))
    for i in range(start_idx, end_idx + 1):
        x = i * step
        dist = math.sqrt((x - cx) ** 2)
        if dist < radius:
            depth = int((radius - dist) / radius * radius * 0.8)
            terrain_heights[i] = min(terrain_heights[i] + depth, HEIGHT - 20)


# ========== 碰撞检测 ==========
def check_hit(px, py, terrain_heights, step):
    """检查炮弹是否击中地形"""
    ground_y = get_ground_y(px, terrain_heights, step)
    return py >= ground_y


def check_player_hit(px, py, players, radius=30):
    """检查炮弹是否击中玩家"""
    for p in players:
        dist = math.sqrt((px - p.x) ** 2 + (py - (p.y - p.tank_h // 2)) ** 2)
        if dist < radius:
            return p
    return None


# ========== AI 玩家 ==========
class AIPlayer:
    """简单的AI对手"""
    @staticmethod
    def get_action(ai_player, enemy, wind):
        # 简单AI: 调整角度和力度朝向敌人
        dx = enemy.x - ai_player.x
        dy = (enemy.y - enemy.tank_h // 2) - (ai_player.y - ai_player.tank_h // 2)
        # 距离越远需要更大角度
        dist = math.sqrt(dx ** 2 + dy ** 2)
        target_angle = math.degrees(math.atan2(-dy, dx))
        target_angle = max(10, min(170, target_angle))

        # 风力补偿
        wind_comp = wind * 0.3
        if ai_player.facing_right:
            target_angle += wind_comp
        else:
            target_angle -= wind_comp

        target_power = min(100, max(20, dist * 0.12 + random.uniform(-5, 5)))

        action = {"angle_up": False, "angle_down": False, "power_up": False, "power_down": False, "fire": False}

        # 调整角度
        angle_diff = target_angle - ai_player.angle
        if abs(angle_diff) > 2:
            if angle_diff > 0:
                action["angle_up"] = True if ai_player.facing_right else False
                action["angle_down"] = False if ai_player.facing_right else True
            else:
                action["angle_down"] = True if ai_player.facing_right else False
                action["angle_up"] = False if ai_player.facing_right else True

        # 调整力度
        power_diff = target_power - ai_player.power
        if abs(power_diff) > 3:
            if power_diff > 0:
                action["power_up"] = True
            else:
                action["power_down"] = True

        # 瞄准好了就发射
        if abs(angle_diff) < 5 and abs(power_diff) < 5:
            action["fire"] = True

        return action


# ========== 游戏主类 ==========
class ArtilleryGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        # 生成地形
        self.terrain_heights, self.step = generate_terrain()
        self.terrain_heights, self.step = smooth_terrain(self.terrain_heights, self.step)

        # 创建玩家
        p1_x = 100
        p1_y = get_ground_y(p1_x, self.terrain_heights, self.step)
        p2_x = WIDTH - 100
        p2_y = get_ground_y(p2_x, self.terrain_heights, self.step)

        self.players = [
            Player(p1_x, p1_y, COLORS["player1"],
                   {"angle_up": pygame.K_w, "angle_down": pygame.K_s,
                    "power_up": pygame.K_d, "power_down": pygame.K_a,
                    "fire": pygame.K_SPACE},
                   "P1", True),
            Player(p2_x, p2_y, COLORS["player2"],
                   {"angle_up": pygame.K_UP, "angle_down": pygame.K_DOWN,
                    "power_up": pygame.K_RIGHT, "power_down": pygame.K_LEFT,
                    "fire": pygame.K_RETURN},
                   "P2", False),
        ]

        self.current_player = 0
        self.projectiles = []
        self.explosions = []
        self.wind = random.uniform(-15, 15)
        self.wind_timer = 0
        self.game_over = False
        self.winner = None
        self.turn_count = 0
        self.ai_mode = False
        self.ai_timer = 0
        self.ai_cooldown = 0
        self.show_menu = True
        self.menu_options = ["双人对战 (2 Players)", "人机对战 (vs AI)"]
        self.menu_selected = 0

    def reset_game(self):
        """重置游戏"""
        self.terrain_heights, self.step = generate_terrain()
        self.terrain_heights, self.step = smooth_terrain(self.terrain_heights, self.step)

        p1_x = 100
        p1_y = get_ground_y(p1_x, self.terrain_heights, self.step)
        p2_x = WIDTH - 100
        p2_y = get_ground_y(p2_x, self.terrain_heights, self.step)

        self.players[0].x = p1_x
        self.players[0].y = p1_y
        self.players[0].health = 100
        self.players[0].angle = 45
        self.players[0].power = 50

        self.players[1].x = p2_x
        self.players[1].y = p2_y
        self.players[1].health = 100
        self.players[1].angle = 135
        self.players[1].power = 50

        self.current_player = 0
        self.projectiles.clear()
        self.explosions.clear()
        self.wind = random.uniform(-15, 15)
        self.game_over = False
        self.winner = None
        self.turn_count = 0

    def draw_terrain(self):
        """绘制地形"""
        points = []
        for i, h in enumerate(self.terrain_heights):
            points.append((i * self.step, h))
        # 地面
        points.append((WIDTH, HEIGHT))
        points.append((0, HEIGHT))
        pygame.draw.polygon(self.screen, COLORS["ground"], points)
        # 地表草皮
        top_points = [(i * self.step, h) for i, h in enumerate(self.terrain_heights)]
        pygame.draw.lines(self.screen, COLORS["ground_top"], False, top_points, 4)

    def draw_wind(self):
        """绘制风力指示"""
        wind_text = f"风力: {self.wind:.1f}"
        color = COLORS["wind_arrow"]
        if self.wind > 5:
            wind_text += " →→→"
        elif self.wind < -5:
            wind_text += " ←←←"
        elif self.wind > 1:
            wind_text += " →"
        elif self.wind < -1:
            wind_text += " ←"
        else:
            wind_text += " ·"

        text = FONT.render(wind_text, True, color)
        # 背景
        bg_rect = pygame.Rect(WIDTH // 2 - text.get_width() // 2 - 10, 10, text.get_width() + 20, text.get_height() + 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 128), bg_rect, border_radius=5)
        pygame.draw.rect(self.screen, (100, 100, 100), bg_rect, 1, border_radius=5)
        self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 15))

        # 风向箭头
        center_x = WIDTH // 2
        center_y = 45
        arrow_len = min(60, max(10, abs(self.wind) * 4))
        if abs(self.wind) > 0.5:
            direction = 1 if self.wind > 0 else -1
            end_x = center_x + direction * arrow_len
            pygame.draw.line(self.screen, color, (center_x, center_y), (end_x, center_y), 3)
            # 箭头
            arrow_size = 8
            if direction > 0:
                pygame.draw.polygon(self.screen, color, [
                    (end_x, center_y),
                    (end_x - arrow_size, center_y - arrow_size),
                    (end_x - arrow_size, center_y + arrow_size)
                ])
            else:
                pygame.draw.polygon(self.screen, color, [
                    (end_x, center_y),
                    (end_x + arrow_size, center_y - arrow_size),
                    (end_x + arrow_size, center_y + arrow_size)
                ])

    def draw_ui(self):
        """绘制界面信息"""
        # 当前玩家指示
        p = self.players[self.current_player]
        info_text = f"{p.name} 回合 | 角度:{p.angle:.0f}° 力度:{p.power:.0f}%"
        text = FONT.render(info_text, True, p.color)
        bg_rect = pygame.Rect(10, 10, text.get_width() + 20, text.get_height() + 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 180), bg_rect, border_radius=5)
        pygame.draw.rect(self.screen, p.color, bg_rect, 1, border_radius=5)
        self.screen.blit(text, (20, 15))

        # 分数
        score_text = FONT.render(f"P1: {self.players[0].score}  P2: {self.players[1].score}", True, COLORS["white"])
        self.screen.blit(score_text, (WIDTH - score_text.get_width() - 20, 15))

        # 操作提示
        if self.current_player == 0:
            hint = "W/S:角度  A/D:力度  空格:发射"
        else:
            if self.ai_mode:
                hint = "AI 思考中..."
            else:
                hint = "↑/↓:角度  ←/→:力度  Enter:发射"
        hint_text = FONT.render(hint, True, COLORS["gray"])
        self.screen.blit(hint_text, (20, HEIGHT - 30))

    def draw_game_over(self):
        """绘制游戏结束界面"""
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        if self.winner:
            title = FONT.render(f"{self.winner.name} 获胜!", True, self.winner.color)
        else:
            title = FONT.render("平局!", True, COLORS["white"])

        score_text = FONT.render(f"最终比分  P1: {self.players[0].score} - P2: {self.players[1].score}", True, COLORS["white"])
        restart_text = FONT.render("按 R 重新开始  按 ESC 退出", True, COLORS["gray"])

        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 60))
        self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 20))
        self.screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 20))

    def draw_menu(self):
        """绘制主菜单"""
        self.screen.fill(COLORS["sky"])

        # 装饰地形
        menu_heights = [HEIGHT * 0.65 + random.randint(-20, 20) for _ in range(10)]
        menu_points = [(i * (WIDTH // 9), menu_heights[i]) for i in range(10)]
        menu_points.append((WIDTH, HEIGHT))
        menu_points.append((0, HEIGHT))
        pygame.draw.polygon(self.screen, COLORS["ground"], menu_points)
        pygame.draw.lines(self.screen, COLORS["ground_top"], False, [(i * (WIDTH // 9), menu_heights[i]) for i in range(10)], 4)

        # 标题
        title_font = pygame.font.Font(None, 72)
        title = title_font.render("火炮对决", True, COLORS["player1"])
        title2 = title_font.render("Artillery Duel", True, COLORS["player2"])
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))
        self.screen.blit(title2, (WIDTH // 2 - title2.get_width() // 2, 180))

        # 菜单选项
        for i, opt in enumerate(self.menu_options):
            color = COLORS["white"] if i == self.menu_selected else COLORS["gray"]
            text = FONT.render(opt, True, color)
            x = WIDTH // 2 - text.get_width() // 2
            y = 300 + i * 50
            if i == self.menu_selected:
                pygame.draw.rect(self.screen, (255, 255, 255, 30), (x - 10, y - 5, text.get_width() + 20, text.get_height() + 10), 2, border_radius=5)
            self.screen.blit(text, (x, y))

        hint = FONT.render("↑/↓ 选择   Enter 确认", True, COLORS["gray"])
        self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 450))

    def fire(self, player_idx):
        """发射炮弹"""
        p = self.players[player_idx]
        angle_rad = math.radians(p.angle)
        speed = p.power * 0.4
        tip_x, tip_y = p.get_barrel_tip()
        vx = math.cos(angle_rad) * speed
        vy = -math.sin(angle_rad) * speed

        proj = Projectile(tip_x, tip_y, vx, vy, player_idx)
        self.projectiles.append(proj)

    def update(self):
        """更新游戏状态"""
        if self.show_menu or self.game_over:
            return

        # 更新炮弹
        for proj in self.projectiles[:]:
            if not proj.alive:
                continue
            proj.update(self.wind)

            # 检查是否击中地形
            if check_hit(proj.x, proj.y, self.terrain_heights, self.step):
                self.explosions.append(Explosion(proj.x, proj.y, 35))
                destroy_terrain(self.terrain_heights, self.step, proj.x, proj.y, 35)
                proj.alive = False

                # 检查是否击中玩家
                hit_player = check_player_hit(proj.x, proj.y, self.players, 40)
                if hit_player and hit_player != self.players[proj.owner]:
                    damage = random.randint(20, 40)
                    hit_player.health -= damage
                    if hit_player.health <= 0:
                        hit_player.health = 0
                        self.players[proj.owner].score += 1
                        if self.players[proj.owner].score >= 3:
                            self.game_over = True
                            self.winner = self.players[proj.owner]
                        else:
                            self.reset_game()
                            return

            # 检查是否击中玩家（飞行中）
            hit_player = check_player_hit(proj.x, proj.y, self.players, 15)
            if hit_player and hit_player != self.players[proj.owner]:
                self.explosions.append(Explosion(proj.x, proj.y, 30))
                damage = random.randint(20, 40)
                hit_player.health -= damage
                proj.alive = False
                if hit_player.health <= 0:
                    hit_player.health = 0
                    self.players[proj.owner].score += 1
                    if self.players[proj.owner].score >= 3:
                        self.game_over = True
                        self.winner = self.players[proj.owner]
                    else:
                        self.reset_game()
                        return

        # 移除已死亡的炮弹
        self.projectiles = [p for p in self.projectiles if p.alive]

        # 更新爆炸效果
        self.explosions = [e for e in self.explosions if e.update()]

        # 切换回合（所有炮弹消失后）
        if not self.projectiles and not self.explosions:
            if self.ai_mode and self.current_player == 1:
                # AI 控制
                if self.ai_cooldown <= 0:
                    action = AIPlayer.get_action(self.players[1], self.players[0], self.wind)
                    p = self.players[1]

                    if action["angle_up"] and p.angle < 180:
                        p.angle += 1
                    if action["angle_down"] and p.angle > 0:
                        p.angle -= 1
                    if action["power_up"] and p.power < 100:
                        p.power += 1
                    if action["power_down"] and p.power > 10:
                        p.power -= 1
                    if action["fire"]:
                        self.fire(1)
                        self.current_player = 0
                        self.turn_count += 1
                        self.wind += random.uniform(-3, 3)
                        self.wind = max(-20, min(20, self.wind))
                        self.ai_cooldown = 30
                    else:
                        self.ai_cooldown = 5
                else:
                    self.ai_cooldown -= 1

        # 风力随时间变化
        self.wind_timer += 1
        if self.wind_timer > 300:
            self.wind += random.uniform(-2, 2)
            self.wind = max(-20, min(20, self.wind))
            self.wind_timer = 0

    def handle_event(self, event):
        """处理输入事件"""
        if self.show_menu:
            self._handle_menu_event(event)
            return

        if self.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.players[0].score = 0
                    self.players[1].score = 0
                    self.reset_game()
                elif event.key == pygame.K_ESCAPE:
                    self.show_menu = True
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.show_menu = True
                return

            # AI 回合不处理玩家输入
            if self.ai_mode and self.current_player == 1:
                return

            p = self.players[self.current_player]
            c = p.controls

            if event.key == c["angle_up"] and p.angle < 180:
                p.angle += 2
            elif event.key == c["angle_down"] and p.angle > 0:
                p.angle -= 2
            elif event.key == c["power_up"] and p.power < 100:
                p.power += 2
            elif event.key == c["power_down"] and p.power > 10:
                p.power -= 2
            elif event.key == c["fire"]:
                if not self.projectiles:
                    self.fire(self.current_player)
                    self.current_player = 1 - self.current_player
                    self.turn_count += 1
                    self.wind += random.uniform(-3, 3)
                    self.wind = max(-20, min(20, self.wind))

    def _handle_menu_event(self, event):
        """处理菜单事件"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.menu_selected = (self.menu_selected - 1) % len(self.menu_options)
            elif event.key == pygame.K_DOWN:
                self.menu_selected = (self.menu_selected + 1) % len(self.menu_options)
            elif event.key == pygame.K_RETURN:
                self.ai_mode = self.menu_selected == 1
                self.show_menu = False
                self.reset_game()

    def draw(self):
        """绘制所有内容"""
        if self.show_menu:
            self.draw_menu()
            pygame.display.flip()
            return

        # 背景
        self.screen.fill(COLORS["sky"])

        # 云朵装饰
        for i in range(3):
            cx = (i * 300 + pygame.time.get_ticks() * 0.01) % (WIDTH + 200) - 100
            cy = 60 + i * 30
            pygame.draw.ellipse(self.screen, (255, 255, 255, 200), (cx, cy, 80, 30))
            pygame.draw.ellipse(self.screen, (255, 255, 255, 200), (cx + 30, cy - 10, 60, 25))

        # 地形
        self.draw_terrain()

        # 玩家
        for p in self.players:
            p.draw(self.screen)

        # 炮弹
        for proj in self.projectiles:
            proj.draw(self.screen)

        # 爆炸效果
        for exp in self.explosions:
            exp.draw(self.screen)

        # 风力
        self.draw_wind()

        # UI
        self.draw_ui()

        # 游戏结束
        if self.game_over:
            self.draw_game_over()

        pygame.display.flip()

    def run(self):
        """主循环"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.handle_event(event)

            self.update()
            self.draw()
            clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ========== 入口 ==========
if __name__ == "__main__":
    FONT = pygame.font.Font(None, 28)
    game = ArtilleryGame()
    game.run()