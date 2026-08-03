"""
Slither.io - 蛇蛇大作战 (Slither.io Snake Battle Royale)
======================================================
经典 .io 风格蛇蛇对战游戏：
- 鼠标控制方向，自由移动
- 多只 AI 蛇 AI 对手
- 吃食物长大，碰撞其他蛇身体即死亡
- 加速冲刺（按住空格/左键）
- 实时排行榜

Date: 2026-08-03
"""

import pygame
import pygame._freetype  # 直接使用底层 FreeType 模块，避免 font 循环导入
import random
import math
import sys
from collections import deque

# ======================== 常量配置 ========================
WIDTH, HEIGHT = 1000, 700
FPS = 60
BG_COLOR = (15, 15, 30)
GRID_COLOR = (25, 25, 45)

# 蛇常量
SEGMENT_RADIUS = 7
SEGMENT_DIST = 6          # 相邻段间距
NORMAL_SPEED = 3.5
BOOST_SPEED = 6.0
BOOST_DRAIN = 0.3         # 加速时每帧消耗的长度
INITIAL_LENGTH = 30
GROWTH_PER_FOOD = 5       # 吃一个食物增加的长度

# 食物
FOOD_COUNT = 120
FOOD_RADIUS = 4

# 蛇颜色方案
SNAKE_COLORS = [
    (255, 80, 80),    # 红 - 玩家
    (80, 200, 255),   # 蓝
    (80, 255, 120),   # 绿
    (255, 200, 50),   # 橙
    (200, 100, 255),  # 紫
]

# 食物颜色池
FOOD_COLORS = [
    (255, 255, 100),
    (255, 150, 50),
    (100, 255, 150),
    (255, 100, 200),
    (100, 200, 255),
    (255, 255, 255),
]


# ======================== 工具函数 ========================
def distance(a, b):
    """计算两点距离"""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def lerp_color(c1, c2, t):
    """颜色插值"""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def wrap_position(pos):
    """环绕屏幕边界"""
    return (pos[0] % WIDTH, pos[1] % HEIGHT)


# ======================== 食物类 ========================
class Food:
    """食物粒子"""

    def __init__(self):
        self.position = (random.randint(30, WIDTH - 30),
                         random.randint(30, HEIGHT - 30))
        self.color = random.choice(FOOD_COLORS)
        self.radius = FOOD_RADIUS
        self.pulse = random.uniform(0, math.pi * 2)

    def update(self):
        self.pulse += 0.05

    def draw(self, screen):
        r = self.radius + math.sin(self.pulse) * 1
        # 发光效果
        for i in range(3, 0, -1):
            alpha = 30 // i
            surf = pygame.Surface((int(r * 4 * i), int(r * 4 * i)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, alpha),
                               (surf.get_width() // 2, surf.get_height() // 2), r * i)
            screen.blit(surf, (self.position[0] - surf.get_width() // 2,
                               self.position[1] - surf.get_height() // 2))
        pygame.draw.circle(screen, self.color,
                           (int(self.position[0]), int(self.position[1])), int(r))


# ======================== 蛇类 ========================
class Snake:
    """蛇实体"""

    def __init__(self, color, start_pos, name, is_player=False):
        self.color = color
        self.name = name
        self.is_player = is_player
        self.alive = True
        self.score = 0

        # 身体：列表 of (x, y)，段0为头部
        self.segments = [pygame.Vector2(start_pos) for _ in range(INITIAL_LENGTH)]
        self.angle = random.uniform(0, math.pi * 2)  # 移动方向（弧度）
        self.speed = NORMAL_SPEED
        self.boosting = False
        self.target_length = INITIAL_LENGTH  # 目标长度（用于增长动画）

        # 死亡动画
        self.death_timer = 0
        self.death_particles = []

    @property
    def head(self):
        return self.segments[0]

    def update(self, target_pos=None):
        """更新蛇的位置"""
        if not self.alive:
            self.death_timer += 1
            for p in self.death_particles[:]:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                p["vy"] += 0.1
                p["life"] -= 1
                if p["life"] <= 0:
                    self.death_particles.remove(p)
            return

        # 更新角度
        if target_pos:
            dx = target_pos[0] - self.head.x
            dy = target_pos[1] - self.head.y
            target_angle = math.atan2(dy, dx)
            # 平滑转向
            diff = target_angle - self.angle
            while diff > math.pi:
                diff -= 2 * math.pi
            while diff < -math.pi:
                diff += 2 * math.pi
            self.angle += diff * 0.15

        # 速度与加速
        self.boosting = False
        if self.is_player:
            keys = pygame.key.get_pressed()
            mouse_buttons = pygame.mouse.get_pressed()
            if keys[pygame.K_SPACE] or mouse_buttons[0]:
                self.boosting = True
        else:
            # AI 偶尔加速
            if random.random() < 0.008:
                self.boosting = not self.boosting

        self.speed = BOOST_SPEED if self.boosting else NORMAL_SPEED

        # 移动头部
        self.head.x += math.cos(self.angle) * self.speed
        self.head.y += math.sin(self.angle) * self.speed

        # 环绕边界
        self.head.x %= WIDTH
        self.head.y %= HEIGHT

        # 身体跟随（蛇形运动）
        for i in range(1, len(self.segments)):
            target = self.segments[i - 1]
            current = self.segments[i]
            dx = target.x - current.x
            dy = target.y - current.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                move = dist - SEGMENT_DIST
                current.x += (dx / dist) * move
                current.y += (dy / dist) * move

        # 处理长度变化
        current_len = len(self.segments)
        if self.boosting and current_len > 10:
            # 加速消耗长度
            self.target_length = max(10, self.target_length - BOOST_DRAIN)

        # 增长/收缩
        if current_len < self.target_length:
            self.segments.append(self.segments[-1].copy())
        elif current_len > self.target_length:
            self.segments.pop()

        # 更新分数
        self.score = max(0, len(self.segments) - INITIAL_LENGTH)

    def grow(self, amount=GROWTH_PER_FOOD):
        """蛇变长"""
        self.target_length += amount

    def check_self_collision(self):
        """检测自己撞自己"""
        if not self.alive:
            return False
        head = self.head
        # 从第5段开始检查（忽略头颈）
        for i in range(5, len(self.segments)):
            if head.distance_to(self.segments[i]) < SEGMENT_RADIUS * 1.2:
                return True
        return False

    def check_head_collision(self, other):
        """检测头部是否撞到 other 的身体"""
        if not self.alive or not other.alive:
            return False
        head = self.head
        # 跳过对方的头 3 段
        start = 3 if other is self else 0
        for i in range(start, len(other.segments)):
            if head.distance_to(other.segments[i]) < SEGMENT_RADIUS * 1.5:
                return True
        return False

    def die(self):
        """蛇死亡"""
        self.alive = False
        # 生成死亡粒子效果
        color = self.color
        for seg in self.segments:
            self.death_particles.append({
                "x": seg.x, "y": seg.y,
                "vx": random.uniform(-3, 3),
                "vy": random.uniform(-5, 2),
                "color": color,
                "life": random.randint(20, 50),
            })

    def draw(self, screen):
        """绘制蛇"""
        if not self.alive:
            # 绘制死亡粒子
            for p in self.death_particles:
                alpha = max(0, int(255 * p["life"] / 50))
                if alpha > 0:
                    surf = pygame.Surface((SEGMENT_RADIUS * 2, SEGMENT_RADIUS * 2), pygame.SRCALPHA)
                    pygame.draw.circle(surf, (*p["color"], alpha),
                                       (SEGMENT_RADIUS, SEGMENT_RADIUS), SEGMENT_RADIUS)
                    screen.blit(surf, (int(p["x"] - SEGMENT_RADIUS), int(p["y"] - SEGMENT_RADIUS)))
            return

        # 绘制身体（从尾部到头部）
        segments = self.segments
        n = len(segments)

        # 身体阴影
        for i, seg in enumerate(segments):
            t = i / max(n - 1, 1)
            r = SEGMENT_RADIUS * (0.6 + 0.4 * (1 - t))
            alpha = 40
            pygame.draw.circle(screen, (0, 0, 0, alpha),
                               (int(seg.x + 2), int(seg.y + 2)), int(r))

        # 身体主体
        for i, seg in enumerate(segments):
            t = i / max(n - 1, 1)  # 0=头, 1=尾
            # 颜色渐变：头部亮，尾部暗
            r = SEGMENT_RADIUS * (0.6 + 0.4 * (1 - t))
            segment_color = lerp_color(
                (min(255, self.color[0] + 60), min(255, self.color[1] + 60), min(255, self.color[2] + 60)),
                (max(0, self.color[0] - 40), max(0, self.color[1] - 40), max(0, self.color[2] - 40)),
                t
            )
            pygame.draw.circle(screen, segment_color,
                               (int(seg.x), int(seg.y)), int(r))

        # 身体轮廓线
        if n > 1:
            points = [(int(s.x), int(s.y)) for s in segments]
            if len(points) > 2:
                pygame.draw.lines(screen, (255, 255, 255, 30), False, points, 1)

        # 头部绘制
        head = segments[0]
        head_r = SEGMENT_RADIUS + 2

        # 眼睛
        eye_offset = head_r * 0.4
        eye_angle1 = self.angle - 0.5
        eye_angle2 = self.angle + 0.5
        for ea in [eye_angle1, eye_angle2]:
            ex = head.x + math.cos(ea) * eye_offset
            ey = head.y + math.sin(ea) * eye_offset
            pygame.draw.circle(screen, (255, 255, 255), (int(ex), int(ey)), 3)
            pygame.draw.circle(screen, (0, 0, 0), (int(ex), int(ey)), 1.5)

        # 加速特效
        if self.boosting:
            for i in range(3):
                offset = (i + 1) * 3
                bx = head.x - math.cos(self.angle) * offset
                by = head.y - math.sin(self.angle) * offset
                alpha = 100 - i * 30
                if alpha > 0:
                    surf = pygame.Surface((SEGMENT_RADIUS * 2, SEGMENT_RADIUS * 2), pygame.SRCALPHA)
                    pygame.draw.circle(surf, (*self.color, alpha),
                                       (SEGMENT_RADIUS, SEGMENT_RADIUS), SEGMENT_RADIUS - i)
                    screen.blit(surf, (int(bx - SEGMENT_RADIUS), int(by - SEGMENT_RADIUS)))


# ======================== AI 控制器 ========================
class AIController:
    """AI 蛇控制逻辑"""

    def __init__(self, snake):
        self.snake = snake
        self.target = None
        self.state_timer = 0
        self.personality = {
            "aggression": random.uniform(0.2, 0.8),  # 攻击性
            "caution": random.uniform(0.3, 0.9),     # 谨慎度
        }

    def update(self, foods, all_snakes):
        """计算 AI 蛇的目标方向"""
        snake = self.snake
        if not snake.alive:
            return

        head = snake.head
        self.state_timer -= 1

        # 1. 寻找最近的食物
        nearest_food = None
        nearest_dist = float("inf")
        for food in foods:
            d = head.distance_to(food.position)
            if d < nearest_dist:
                nearest_dist = d
                nearest_food = food

        # 2. 检测附近威胁（其他蛇的身体）
        threat_vec = pygame.Vector2(0, 0)
        for other in all_snakes:
            if other is snake or not other.alive:
                continue
            for seg in other.segments:
                d = head.distance_to(seg)
                if d < 120:
                    # 远离威胁
                    away = pygame.Vector2(head.x - seg.x, head.y - seg.y)
                    if d > 0:
                        away /= d
                        away *= (120 - d) / 120
                    threat_vec += away

        # 3. 检测边界（倾向往中心）
        center_vec = pygame.Vector2(0, 0)
        margin = 80
        if head.x < margin:
            center_vec.x += 1
        elif head.x > WIDTH - margin:
            center_vec.x -= 1
        if head.y < margin:
            center_vec.y += 1
        elif head.y > HEIGHT - margin:
            center_vec.y -= 1

        # 4. 合并目标方向
        target_dir = pygame.Vector2(0, 0)

        if nearest_food:
            food_dir = pygame.Vector2(
                nearest_food.position[0] - head.x,
                nearest_food.position[1] - head.y
            )
            if food_dir.length() > 0:
                food_dir /= food_dir.length()
            # 根据个性和威胁调整食物权重
            food_weight = 1.0 - self.personality["caution"] * 0.5
            target_dir += food_dir * food_weight

        # 避让威胁（高优先级）
        if threat_vec.length() > 0:
            if threat_vec.length() > 1:
                threat_vec.scale_to_length(1)
            target_dir += threat_vec * (self.personality["caution"] * 2.0)

        # 边界回避
        if center_vec.length() > 0:
            if center_vec.length() > 1:
                center_vec.scale_to_length(1)
            target_dir += center_vec * 1.5

        # 如果目标方向为零向量，随机移动
        if target_dir.length() < 0.01:
            target_dir = pygame.Vector2(math.cos(snake.angle), math.sin(snake.angle))
        else:
            target_dir.scale_to_length(1)

        # 转换为角度
        target_angle = math.atan2(target_dir.y, target_dir.x)

        # 平滑转向
        diff = target_angle - snake.angle
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        snake.angle += diff * 0.08

        # AI 决定是否加速
        if nearest_dist < 200 and random.random() < 0.01:
            snake.boosting = True
        elif nearest_dist > 400 or random.random() < 0.02:
            snake.boosting = False


# ======================== 游戏主类 ========================
class Game:
    """Slither.io 游戏主控"""

    def __init__(self):
        pygame.init()
        pygame._freetype.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Slither.io - 蛇蛇大作战")
        self.clock = pygame.time.Clock()
        self.font = self._get_font(18)
        self.font_small = self._get_font(14)
        self.font_big = self._get_font(48)
        self.font_medium = self._get_font(28)

        self.running = True
        self.paused = False
        self.game_over = False
        self.winner_message = ""
        self.reset_game()

    def _get_font(self, size):
        """获取字体，使用 FreeType 直接渲染，绕过 pygame.font 循环导入问题"""
        return pygame._freetype.Font(None, size=size)

    def reset_game(self):
        """重置游戏状态"""
        self.game_over = False
        self.winner_message = ""

        # 生成食物
        self.foods = [Food() for _ in range(FOOD_COUNT)]

        # 创建蛇
        self.snakes = []
        self.player = None

        # 玩家蛇 - 从中心附近开始
        names = ["你", "AI-蓝灵", "AI-翠影", "AI-金焰", "AI-紫晶"]
        start_positions = [
            (WIDTH // 2 + random.randint(-50, 50), HEIGHT // 2 + random.randint(-50, 50)),
            (WIDTH * 0.2, HEIGHT * 0.2),
            (WIDTH * 0.8, HEIGHT * 0.2),
            (WIDTH * 0.2, HEIGHT * 0.8),
            (WIDTH * 0.8, HEIGHT * 0.8),
        ]

        for i in range(5):
            color = SNAKE_COLORS[i]
            pos = start_positions[i]
            name = names[i]
            is_player = (i == 0)
            snake = Snake(color, pos, name, is_player)
            self.snakes.append(snake)
            if is_player:
                self.player = snake

        # AI 控制器
        self.ai_controllers = [AIController(s) for s in self.snakes[1:]]

        # 食物刷新计时器
        self.food_timer = 0

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r and self.game_over:
                    self.reset_game()
                elif event.key == pygame.K_p:
                    self.paused = not self.paused

    def update(self):
        """更新游戏状态"""
        if self.paused or self.game_over:
            return

        # 更新食物
        for food in self.foods:
            food.update()

        # 保持食物数量
        self.food_timer += 1
        if self.food_timer > 30 and len(self.foods) < FOOD_COUNT:
            self.foods.append(Food())
            self.food_timer = 0

        # 获取鼠标位置（玩家目标）
        mouse_pos = pygame.mouse.get_pos()

        # 更新玩家蛇
        if self.player and self.player.alive:
            self.player.update(mouse_pos)

        # 更新 AI 蛇
        for i, controller in enumerate(self.ai_controllers):
            snake = controller.snake
            if snake.alive:
                controller.update(self.foods, self.snakes)
                snake.update()

        # 碰撞检测
        alive_snakes = [s for s in self.snakes if s.alive]

        # 蛇吃食物
        for snake in alive_snakes:
            head = snake.head
            eaten = []
            for i, food in enumerate(self.foods):
                if head.distance_to(food.position) < SEGMENT_RADIUS + FOOD_RADIUS + 2:
                    snake.grow()
                    eaten.append(i)
            for i in reversed(eaten):
                self.foods.pop(i)
                self.foods.append(Food())  # 补充新食物

        # 蛇碰撞（头部 vs 身体）
        dead_snakes = set()
        for snake in alive_snakes:
            # 自撞
            if snake.check_self_collision():
                dead_snakes.add(snake)
                continue
            # 撞其他蛇
            for other in alive_snakes:
                if snake is other:
                    continue
                if snake.check_head_collision(other):
                    dead_snakes.add(snake)
                    break

        # 处理死亡
        for snake in dead_snakes:
            if snake.alive:
                snake.die()

        # 检查游戏结束条件
        alive_snakes = [s for s in self.snakes if s.alive]
        if self.player and not self.player.alive:
            self.game_over = True
            # 找赢家
            alive_count = len(alive_snakes)
            if alive_count == 0:
                self.winner_message = "游戏结束！全部蛇都阵亡了！"
            elif alive_count == 1:
                self.winner_message = f"{alive_snakes[0].name} 获胜！"
            else:
                self.winner_message = "你被淘汰了！按 R 重新开始"

    def draw(self):
        """绘制场景"""
        self.screen.fill(BG_COLOR)

        # 绘制网格
        grid_size = 40
        for x in range(0, WIDTH, grid_size):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, grid_size):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (WIDTH, y))

        # 绘制食物
        for food in self.foods:
            food.draw(self.screen)

        # 绘制蛇（先绘制 AI，再绘制玩家，使玩家在最上层）
        for snake in self.snakes:
            if snake != self.player:
                snake.draw(self.screen)
        if self.player:
            self.player.draw(self.screen)

        # 绘制 HUD
        self.draw_hud()

        # 暂停/结束界面
        if self.paused:
            self.draw_overlay("游戏暂停", "按 P 继续", (255, 255, 255))
        if self.game_over:
            self.draw_game_over()

        pygame.display.flip()

    def draw_hud(self):
        """绘制 HUD 信息"""
        # 排行榜
        rankings = sorted(
            [s for s in self.snakes if s.alive or s.death_timer < 120],
            key=lambda s: s.score, reverse=True
        )

        # 排行榜背景
        panel_x = WIDTH - 170
        panel_y = 10
        panel_w = 155
        panel_h = 30 + len(rankings) * 26

        s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 160))
        self.screen.blit(s, (panel_x, panel_y))

        # 标题
        title = self.font_small.render("🏆 排行榜", (255, 255, 200))[0]
        self.screen.blit(title, (panel_x + 10, panel_y + 8))

        for i, snake in enumerate(rankings):
            y = panel_y + 30 + i * 26
            alive_mark = "●" if snake.alive else "✕"
            mark_color = snake.color if snake.alive else (100, 100, 100)
            name_text = f"{alive_mark} {snake.name}"
            name_surf = self.font_small.render(name_text, mark_color)[0]
            score_surf = self.font_small.render(str(snake.score), (255, 255, 255))[0]
            self.screen.blit(name_surf, (panel_x + 10, y))
            self.screen.blit(score_surf, (panel_x + panel_w - 40, y))

        # 玩家分数
        if self.player and self.player.alive:
            score_text = self.font.render(f"长度: {len(self.player.segments)}  分数: {self.player.score}", (255, 255, 255))[0]
            self.screen.blit(score_text, (15, 15))

        # 操作提示
        if not self.game_over:
            hint = self.font_small.render("鼠标移动 · 空格/左键加速 · P暂停 · ESC退出", (150, 150, 150))[0]
            self.screen.blit(hint, (15, HEIGHT - 30))

    def draw_overlay(self, title, subtitle, color):
        """绘制半透明覆盖层"""
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 120))
        self.screen.blit(s, (0, 0))

        t = self.font_big.render(title, color)[0]
        st = self.font_medium.render(subtitle, (200, 200, 200))[0]
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 60))
        self.screen.blit(st, (WIDTH // 2 - st.get_width() // 2, HEIGHT // 2 + 10))

    def draw_game_over(self):
        """绘制游戏结束画面"""
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 160))
        self.screen.blit(s, (0, 0))

        title = self.font_big.render("游戏结束", (255, 100, 100))[0]
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 80))

        if self.winner_message:
            msg = self.font_medium.render(self.winner_message, (255, 255, 200))[0]
            self.screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - 20))

        # 最终排名
        rankings = sorted(self.snakes, key=lambda s: s.score, reverse=True)
        rank_y = HEIGHT // 2 + 30
        for i, snake in enumerate(rankings):
            rank_text = f"#{i+1} {snake.name} - 分数: {snake.score}  {'✓' if snake.alive else '✕'}"
            color = snake.color if snake.alive else (100, 100, 100)
            rs = self.font.render(rank_text, color)[0]
            self.screen.blit(rs, (WIDTH // 2 - rs.get_width() // 2, rank_y + i * 28))

        restart = self.font_medium.render("按 R 重新开始", (200, 200, 200))[0]
        self.screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, rank_y + len(rankings) * 28 + 20))

    def run(self):
        """主游戏循环"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ======================== 入口 ========================
if __name__ == "__main__":
    game = Game()
    game.run()