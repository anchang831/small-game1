"""
愤怒的小鸟 (Angry Birds) - 经典弹弓物理射击游戏
================================================
使用 Pygame 实现，单文件运行，无外部依赖。
- 弹弓拖拽发射小鸟
- 抛物线物理轨迹
- 可破坏的木块/石堆结构
- 绿猪目标
- 计分系统
- 关卡重置

操作方式：
- 鼠标拖拽小鸟，瞄准后松开发射
- 按 R 键重置当前关卡
- 按 ESC 退出游戏

作者: AI Game Developer
日期: 2026-07-15
"""

import pygame
import math
import random

# ============================================================
# 常量配置
# ============================================================
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
FPS = 60

# 颜色
COLOR_SKY = (135, 206, 235)        # 天空蓝
COLOR_GROUND = (34, 139, 34)       # 草地绿
COLOR_BIRD_RED = (220, 40, 40)     # 小鸟红
COLOR_BIRD_BEAK = (255, 180, 30)   # 鸟喙黄
COLOR_PIG = (60, 180, 60)          # 猪绿
COLOR_PIG_NOSE = (40, 140, 40)     # 猪鼻子
COLOR_WOOD = (160, 120, 60)        # 木头色
COLOR_STONE = (140, 140, 140)      # 石灰色
COLOR_GLASS = (180, 220, 240)      # 玻璃色
COLOR_SLING = (80, 40, 20)         # 弹弓色
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_SHADOW = (0, 0, 0, 60)
COLOR_TRAJECTORY = (255, 255, 255, 100)

# 物理
GRAVITY = 980        # 重力加速度 (px/s²)
LAUNCH_POWER = 600   # 最大发射力度
SLING_X = 200        # 弹弓 X 位置
SLING_Y = 420        # 弹弓 Y 位置（弹弓叉中心）
GROUND_Y = 500       # 地面 Y 位置
DAMPING = 0.98       # 碰撞能量衰减

# 游戏状态
STATE_AIMING = 0     # 瞄准中
STATE_FLYING = 1     # 飞行中
STATE_SLOWING = 2    # 慢动作/碰撞中
STATE_WAITING = 3    # 等待下一只鸟
STATE_WIN = 4        # 过关
STATE_LOSE = 5       # 失败


# ============================================================
# 物理工具
# ============================================================
def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def point_in_rect(px, py, rect):
    """检测点是否在矩形内"""
    x, y, w, h = rect
    return x <= px <= x + w and y <= py <= y + h


def rect_overlap(r1, r2):
    """检测两个矩形是否重叠"""
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)


# ============================================================
# 游戏对象
# ============================================================
class Bird:
    """小鸟类"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = 18
        self.active = False
        self.alive = True
        self.trail = []  # 轨迹点

    def launch(self, vx, vy):
        self.vx = vx
        self.vy = vy
        self.active = True
        self.trail = []

    def update(self, dt):
        if not self.active or not self.alive:
            return
        # 重力
        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        # 记录轨迹
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 40:
            self.trail.pop(0)
        # 边界检测
        if self.x > SCREEN_WIDTH + 50 or self.y > GROUND_Y + 50:
            self.alive = False

    def draw(self, screen):
        if not self.alive:
            return
        # 轨迹点
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(120 * (i / len(self.trail)))
            if alpha > 0:
                pygame.draw.circle(screen, (255, 255, 200, alpha), (tx, ty), 3)
        # 身体
        x, y = int(self.x), int(self.y)
        pygame.draw.circle(screen, COLOR_BIRD_RED, (x, y), self.radius)
        # 肚子 (浅色)
        pygame.draw.circle(screen, (240, 160, 140), (x + 2, y + 4), self.radius - 6)
        # 眼睛
        eye_off = 6
        pygame.draw.circle(screen, COLOR_WHITE, (x - eye_off, y - 5), 6)
        pygame.draw.circle(screen, COLOR_WHITE, (x + eye_off, y - 5), 6)
        pygame.draw.circle(screen, COLOR_BLACK, (x - eye_off + 2, y - 5), 3)
        pygame.draw.circle(screen, COLOR_BLACK, (x + eye_off + 2, y - 5), 3)
        # 眉毛 (愤怒)
        pygame.draw.line(screen, COLOR_BLACK,
                         (x - eye_off - 6, y - 12), (x - eye_off + 2, y - 8), 2)
        pygame.draw.line(screen, COLOR_BLACK,
                         (x + eye_off + 6, y - 12), (x + eye_off - 2, y - 8), 2)
        # 嘴
        beak = [(x + 8, y + 2), (x + 18, y + 4), (x + 8, y + 8)]
        pygame.draw.polygon(screen, COLOR_BIRD_BEAK, beak)
        # 尾巴
        tail = [(x - 16, y - 4), (x - 22, y - 10), (x - 22, y + 2)]
        pygame.draw.polygon(screen, COLOR_BIRD_RED, tail)

    def get_rect(self):
        return (int(self.x - self.radius), int(self.y - self.radius),
                self.radius * 2, self.radius * 2)

    def check_collision(self, rect):
        """检测与矩形的碰撞 (圆形 vs 矩形)"""
        rx, ry, rw, rh = rect
        # 找矩形上离圆心最近的点
        cx = clamp(self.x, rx, rx + rw)
        cy = clamp(self.y, ry, ry + rh)
        dx = self.x - cx
        dy = self.y - cy
        return dx * dx + dy * dy < self.radius * self.radius


class Block:
    """可破坏的方块"""
    def __init__(self, x, y, w, h, color, hp=1.0):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.max_hp = hp
        self.hp = hp
        self.vx = 0
        self.vy = 0
        self.alive = True
        self.rotation = 0
        self.rot_speed = 0

    @property
    def rect(self):
        return (int(self.x), int(self.y), int(self.w), int(self.h))

    def update(self, dt):
        if not self.alive:
            return
        # 物理
        self.vy += GRAVITY * 0.5 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.rot_speed * dt
        self.rot_speed *= 0.98
        # 地面碰撞
        if self.y + self.h > GROUND_Y:
            self.y = GROUND_Y - self.h
            self.vy *= -0.3
            self.vx *= 0.9
            if abs(self.vy) < 20:
                self.vy = 0
        # 边界
        if self.x < 0:
            self.x = 0
            self.vx *= -0.3
        if self.x + self.w > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.w
            self.vx *= -0.3
        # 速度过小则停止
        if abs(self.vx) < 5:
            self.vx = 0
        if abs(self.vy) < 5:
            self.vy = 0

    def draw(self, screen):
        if not self.alive:
            return
        # 根据血量显示裂痕
        hp_ratio = self.hp / self.max_hp
        if hp_ratio <= 0:
            return
        color = tuple(int(c * (0.5 + 0.5 * hp_ratio)) for c in self.color)
        rect = (int(self.x), int(self.y), int(self.w), int(self.h))
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, COLOR_BLACK, rect, 2)
        # 血条
        bar_w = self.w * 0.8
        bar_h = 4
        bar_x = self.x + self.w * 0.1
        bar_y = self.y - 8
        pygame.draw.rect(screen, (60, 60, 60),
                         (int(bar_x), int(bar_y), int(bar_w), bar_h))
        pygame.draw.rect(screen, (0, 200, 0),
                         (int(bar_x), int(bar_y), int(bar_w * hp_ratio), bar_h))

    def take_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def apply_force(self, fx, fy):
        self.vx += fx
        self.vy += fy
        self.rot_speed += fx * 0.5


class Pig:
    """绿猪"""
    def __init__(self, x, y, size=1.0):
        self.x = x
        self.y = y
        self.radius = int(18 * size)
        self.size = size
        self.hp = 2.0 * size
        self.max_hp = self.hp
        self.alive = True
        self.vx = 0
        self.vy = 0
        self.rotation = 0

    def update(self, dt):
        if not self.alive:
            return
        self.vy += GRAVITY * 0.5 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        # 地面碰撞
        if self.y + self.radius > GROUND_Y:
            self.y = GROUND_Y - self.radius
            self.vy *= -0.3
            self.vx *= 0.9
            if abs(self.vy) < 10:
                self.vy = 0
        if self.x < self.radius:
            self.x = self.radius
            self.vx *= -0.3
        if self.x + self.radius > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.vx *= -0.3
        if abs(self.vx) < 3:
            self.vx = 0

    def draw(self, screen):
        if not self.alive:
            return
        x, y = int(self.x), int(self.y)
        r = self.radius
        # 身体
        pygame.draw.circle(screen, COLOR_PIG, (x, y), r)
        pygame.draw.circle(screen, COLOR_BLACK, (x, y), r, 2)
        # 肚子
        pygame.draw.circle(screen, (80, 200, 80), (x, y + 3), r - 5)
        # 眼睛
        eye_off = r // 3
        pygame.draw.circle(screen, COLOR_WHITE, (x - eye_off, y - 4), r // 3)
        pygame.draw.circle(screen, COLOR_WHITE, (x + eye_off, y - 4), r // 3)
        pygame.draw.circle(screen, COLOR_BLACK, (x - eye_off + 2, y - 4), r // 6)
        pygame.draw.circle(screen, COLOR_BLACK, (x + eye_off + 2, y - 4), r // 6)
        # 鼻子
        nose = pygame.Rect(0, 0, r // 2, r // 3)
        nose.center = (x, y + 3)
        pygame.draw.ellipse(screen, COLOR_PIG_NOSE, nose)
        pygame.draw.ellipse(screen, (30, 100, 30), nose, 1)
        # 鼻孔
        pygame.draw.circle(screen, (30, 80, 30), (x - 3, y + 3), 2)
        pygame.draw.circle(screen, (30, 80, 30), (x + 3, y + 3), 2)
        # 耳朵
        pygame.draw.circle(screen, COLOR_PIG, (x - r + 4, y - r + 4), 6)
        pygame.draw.circle(screen, COLOR_PIG, (x + r - 4, y - r + 4), 6)
        # 血条
        bar_w = r * 2
        bar_h = 4
        bar_x = x - r
        bar_y = y - r - 12
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, (60, 60, 60),
                         (int(bar_x), int(bar_y), int(bar_w), bar_h))
        pygame.draw.rect(screen, (0, 200, 0),
                         (int(bar_x), int(bar_y), int(bar_w * hp_ratio), bar_h))

    def get_rect(self):
        r = self.radius
        return (int(self.x - r), int(self.y - r), r * 2, r * 2)

    def take_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def apply_force(self, fx, fy):
        self.vx += fx
        self.vy += fy


# ============================================================
# 关卡数据
# ============================================================
def create_level(level_num):
    """创建关卡"""
    blocks = []
    pigs = []
    birds = []

    # 基础结构 - 在不同关卡有不同的布局
    base_x = 700
    base_y = GROUND_Y

    if level_num == 1:
        # 第一关：简单 - 一个木架 + 一只猪
        # 两个木柱 + 一个木顶
        blocks.append(Block(base_x, base_y - 50, 25, 50, COLOR_WOOD, 1.0))
        blocks.append(Block(base_x + 60, base_y - 50, 25, 50, COLOR_WOOD, 1.0))
        blocks.append(Block(base_x, base_y - 75, 85, 25, COLOR_WOOD, 1.0))
        pigs.append(Pig(base_x + 42, base_y - 60, 0.8))
        birds.append(Bird(SLING_X, SLING_Y))
        birds.append(Bird(SLING_X - 30, SLING_Y + 10))
        birds.append(Bird(SLING_X - 60, SLING_Y + 20))

    elif level_num == 2:
        # 第二关：一个两层结构 + 两只猪
        # 底层
        blocks.append(Block(base_x, base_y - 50, 25, 50, COLOR_WOOD, 1.5))
        blocks.append(Block(base_x + 80, base_y - 50, 25, 50, COLOR_WOOD, 1.5))
        blocks.append(Block(base_x, base_y - 75, 105, 25, COLOR_WOOD, 1.0))
        # 二层
        blocks.append(Block(base_x + 20, base_y - 105, 25, 30, COLOR_WOOD, 1.0))
        blocks.append(Block(base_x + 60, base_y - 105, 25, 30, COLOR_WOOD, 1.0))
        blocks.append(Block(base_x + 20, base_y - 125, 65, 20, COLOR_WOOD, 0.8))
        # 猪
        pigs.append(Pig(base_x + 40, base_y - 60, 0.8))
        pigs.append(Pig(base_x + 42, base_y - 110, 0.7))
        birds.append(Bird(SLING_X, SLING_Y))
        birds.append(Bird(SLING_X - 30, SLING_Y + 10))
        birds.append(Bird(SLING_X - 60, SLING_Y + 20))
        birds.append(Bird(SLING_X - 90, SLING_Y + 30))

    elif level_num == 3:
        # 第三关：复杂结构 + 石头 + 三只猪
        # 左木架
        blocks.append(Block(base_x, base_y - 50, 25, 50, COLOR_WOOD, 2.0))
        blocks.append(Block(base_x + 40, base_y - 50, 25, 50, COLOR_WOOD, 2.0))
        blocks.append(Block(base_x, base_y - 75, 65, 25, COLOR_WOOD, 1.5))
        # 右石架
        blocks.append(Block(base_x + 120, base_y - 55, 30, 55, COLOR_STONE, 3.0))
        # 顶
        blocks.append(Block(base_x + 80, base_y - 80, 80, 20, COLOR_WOOD, 1.0))
        # 玻璃点缀
        blocks.append(Block(base_x + 60, base_y - 120, 20, 40, COLOR_GLASS, 0.5))
        # 猪
        pigs.append(Pig(base_x + 20, base_y - 60, 0.7))
        pigs.append(Pig(base_x + 60, base_y - 65, 0.8))
        pigs.append(Pig(base_x + 105, base_y - 40, 1.0))
        birds.append(Bird(SLING_X, SLING_Y))
        birds.append(Bird(SLING_X - 30, SLING_Y + 10))
        birds.append(Bird(SLING_X - 60, SLING_Y + 20))
        birds.append(Bird(SLING_X - 90, SLING_Y + 30))
        birds.append(Bird(SLING_X - 120, SLING_Y + 40))

    elif level_num == 4:
        # 第四关：全石头堡垒
        # 石墙
        for i in range(4):
            blocks.append(Block(base_x + i * 35, base_y - 35, 35, 35, COLOR_STONE, 3.0))
        for i in range(4):
            blocks.append(Block(base_x + i * 35, base_y - 70, 35, 35, COLOR_STONE, 3.0))
        # 顶
        blocks.append(Block(base_x, base_y - 90, 140, 20, COLOR_STONE, 4.0))
        # 猪
        pigs.append(Pig(base_x + 70, base_y - 50, 1.2))
        pigs.append(Pig(base_x + 40, base_y - 50, 0.7))
        pigs.append(Pig(base_x + 100, base_y - 50, 0.7))
        birds.append(Bird(SLING_X, SLING_Y))
        birds.append(Bird(SLING_X - 30, SLING_Y + 10))
        birds.append(Bird(SLING_X - 60, SLING_Y + 20))
        birds.append(Bird(SLING_X - 90, SLING_Y + 30))
        birds.append(Bird(SLING_X - 120, SLING_Y + 40))

    else:
        # 第五关及以后：随机生成
        random.seed(level_num * 777)
        num_pigs = random.randint(3, 5)
        used_positions = []
        for _ in range(num_pigs):
            attempts = 0
            while attempts < 20:
                px = base_x + random.randint(0, 200)
                py = base_y - 30 - random.randint(0, 80)
                # 避免重叠
                ok = True
                for ux, uy in used_positions:
                    if abs(px - ux) < 50 and abs(py - uy) < 50:
                        ok = False
                        break
                if ok:
                    used_positions.append((px, py))
                    break
                attempts += 1
        for px, py in used_positions:
            size = random.uniform(0.6, 1.2)
            pigs.append(Pig(px, py, size))
        # 随机方块
        for _ in range(num_pigs * 3):
            bx = base_x + random.randint(0, 220)
            by = base_y - 20 - random.randint(0, 100)
            bw = random.randint(15, 35)
            bh = random.randint(15, 35)
            color = random.choice([COLOR_WOOD, COLOR_STONE, COLOR_GLASS])
            hp = {COLOR_WOOD: 1.5, COLOR_STONE: 3.0, COLOR_GLASS: 0.5}[color]
            blocks.append(Block(bx, by, bw, bh, color, hp))
        # 鸟
        for i in range(num_pigs + 2):
            birds.append(Bird(SLING_X - i * 30, SLING_Y + i * 10))

    return birds, blocks, pigs


# ============================================================
# 碰撞处理
# ============================================================
def handle_collisions(bird, blocks, pigs):
    """处理小鸟与方块、猪的碰撞"""
    score = 0
    hit_list = []

    # 小鸟 vs 方块
    for block in blocks[:]:
        if not block.alive:
            continue
        if bird.check_collision(block.rect):
            # 冲击力
            speed = math.sqrt(bird.vx ** 2 + bird.vy ** 2)
            damage = speed / 300
            block.take_damage(damage)
            block.apply_force(bird.vx * 0.3, bird.vy * 0.3)
            # 反弹小鸟
            overlap_x = (bird.x - clamp(bird.x, block.x, block.x + block.w))
            overlap_y = (bird.y - clamp(bird.y, block.y, block.y + block.h))
            if abs(overlap_x) > abs(overlap_y):
                bird.vx *= -0.4
            else:
                bird.vy *= -0.4
            bird.vx *= DAMPING
            bird.vy *= DAMPING
            hit_list.append(block)
            if not block.alive:
                score += 100

    # 小鸟 vs 猪
    for pig in pigs[:]:
        if not pig.alive:
            continue
        dx = bird.x - pig.x
        dy = bird.y - pig.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < bird.radius + pig.radius:
            speed = math.sqrt(bird.vx ** 2 + bird.vy ** 2)
            damage = speed / 200
            pig.take_damage(damage)
            pig.apply_force(bird.vx * 0.5, bird.vy * 0.5)
            # 反弹
            if dist > 0:
                bird.vx = (dx / dist) * 100
                bird.vy = (dy / dist) * 100
            hit_list.append(pig)
            if not pig.alive:
                score += 500

    # 方块 vs 猪（碎块伤害）
    for block in blocks[:]:
        if not block.alive:
            continue
        for pig in pigs[:]:
            if not pig.alive:
                continue
            dx = (block.x + block.w / 2) - pig.x
            dy = (block.y + block.h / 2) - pig.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < block.w * 0.5 + pig.radius:
                speed = math.sqrt(block.vx ** 2 + block.vy ** 2)
                if speed > 50:
                    damage = speed / 400
                    pig.take_damage(damage)
                    pig.apply_force(block.vx * 0.3, block.vy * 0.3)
                    if not pig.alive:
                        score += 500

    # 方块 vs 方块（连锁碰撞）
    for i, b1 in enumerate(blocks[:]):
        if not b1.alive:
            continue
        for j, b2 in enumerate(blocks[:]):
            if i >= j or not b2.alive:
                continue
            if rect_overlap(b1.rect, b2.rect):
                # 推离
                overlap_x = min(b1.x + b1.w, b2.x + b2.w) - max(b1.x, b2.x)
                overlap_y = min(b1.y + b1.h, b2.y + b2.h) - max(b1.y, b2.y)
                if overlap_x < overlap_y:
                    if b1.x < b2.x:
                        b1.x -= overlap_x / 2
                        b2.x += overlap_x / 2
                    else:
                        b1.x += overlap_x / 2
                        b2.x -= overlap_x / 2
                    b1.vx *= -0.3
                    b2.vx *= -0.3
                else:
                    if b1.y < b2.y:
                        b1.y -= overlap_y / 2
                        b2.y += overlap_y / 2
                    else:
                        b1.y += overlap_y / 2
                        b2.y -= overlap_y / 2
                    b1.vy *= -0.3
                    b2.vy *= -0.3

    return score, hit_list


# ============================================================
# 主游戏类
# ============================================================
class AngryBirds:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("愤怒的小鸟 | Angry Birds")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 24)
        self.running = True

        self.level = 1
        self.score = 0
        self.total_score = 0
        self.state = STATE_AIMING
        self.state_timer = 0

        # 拖拽
        self.dragging = False
        self.drag_start = (0, 0)
        self.drag_current = (0, 0)
        self.current_bird_idx = 0

        # 粒子效果
        self.particles = []

        self.reset_level()

    def reset_level(self):
        self.birds, self.blocks, self.pigs = create_level(self.level)
        self.current_bird_idx = 0
        self.bird = self.birds[0] if self.birds else None
        self.state = STATE_AIMING
        self.state_timer = 0
        self.particles = []

    def add_particles(self, x, y, color, count=10):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 200)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(0.5, 1.5),
                'max_life': 1.5,
                'color': color,
                'size': random.randint(2, 5)
            })

    def update(self, dt):
        # 更新粒子
        for p in self.particles[:]:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += 200 * dt
            p['life'] -= dt
            if p['life'] <= 0:
                self.particles.remove(p)

        # 更新方块
        for block in self.blocks:
            block.update(dt)
            # 方块碎裂粒子
            if not block.alive:
                self.add_particles(block.x + block.w / 2,
                                   block.y + block.h / 2,
                                   block.color, 8)

        # 更新猪
        for pig in self.pigs:
            pig.update(dt)
            if not pig.alive:
                self.add_particles(pig.x, pig.y, COLOR_PIG, 15)

        # 移除死亡的方块和猪（已做）

        if self.state == STATE_AIMING:
            pass  # 等待用户操作

        elif self.state == STATE_FLYING:
            if self.bird and self.bird.alive:
                self.bird.update(dt)
                # 碰撞检测
                score_gain, _ = handle_collisions(self.bird, self.blocks, self.pigs)
                self.score += score_gain
                self.total_score += score_gain
                # 如果小鸟速度很小，进入慢动作
                if self.bird.active:
                    speed = math.sqrt(self.bird.vx ** 2 + self.bird.vy ** 2)
                    if speed < 30 and self.bird.y > GROUND_Y - 20:
                        self.state = STATE_SLOWING
                        self.state_timer = 0.5
            else:
                self.state = STATE_SLOWING
                self.state_timer = 0.3

        elif self.state == STATE_SLOWING:
            # 继续更新物理一小段时间，让场景稳定
            self.state_timer -= dt
            # 更新仍活跃的方块和猪
            for block in self.blocks:
                block.update(dt)
            for pig in self.pigs:
                pig.update(dt)
            # 碰撞连锁
            for block in self.blocks:
                if not block.alive:
                    continue
                for pig in self.pigs:
                    if not pig.alive:
                        continue
                    dx = (block.x + block.w / 2) - pig.x
                    dy = (block.y + block.h / 2) - pig.y
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < block.w * 0.5 + pig.radius:
                        speed = math.sqrt(block.vx ** 2 + block.vy ** 2)
                        if speed > 50:
                            damage = speed / 400
                            if pig.take_damage(damage):
                                self.score += 500
                                self.total_score += 500
                                self.add_particles(pig.x, pig.y, COLOR_PIG, 15)

            if self.state_timer <= 0:
                self.state = STATE_WAITING

        elif self.state == STATE_WAITING:
            # 检查是否所有猪都死了
            pigs_alive = sum(1 for p in self.pigs if p.alive)
            if pigs_alive == 0:
                self.state = STATE_WIN
                self.state_timer = 3.0
            else:
                # 下一只鸟
                self.current_bird_idx += 1
                if self.current_bird_idx < len(self.birds):
                    self.bird = self.birds[self.current_bird_idx]
                    self.bird.x = SLING_X
                    self.bird.y = SLING_Y
                    self.state = STATE_AIMING
                else:
                    # 没有鸟了
                    self.state = STATE_LOSE
                    self.state_timer = 3.0

        elif self.state == STATE_WIN:
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.level += 1
                self.score = 0
                self.reset_level()

        elif self.state == STATE_LOSE:
            self.state_timer -= dt
            if self.state_timer <= 0:
                # 重试当前关卡
                self.score = 0
                self.reset_level()

    def draw_background(self):
        # 天空
        self.screen.fill(COLOR_SKY)
        # 云朵（装饰）
        for i in range(5):
            cx = 100 + i * 250 + (pygame.time.get_ticks() * 0.01 % 800)
            cy = 60 + (i * 30) % 120
            pygame.draw.circle(self.screen, (255, 255, 255, 180),
                               (int(cx % 1300), cy), 30)
            pygame.draw.circle(self.screen, (255, 255, 255, 180),
                               (int((cx + 40) % 1300), cy - 10), 25)
            pygame.draw.circle(self.screen, (255, 255, 255, 180),
                               (int((cx + 20) % 1300), cy + 10), 20)
        # 草地
        pygame.draw.rect(self.screen, COLOR_GROUND,
                         (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))
        # 草地纹理线
        for i in range(0, SCREEN_WIDTH, 20):
            h = random.randint(3, 8)
            pygame.draw.line(self.screen, (20, 120, 20),
                             (i, GROUND_Y), (i, GROUND_Y + h), 1)

    def draw_slingshot(self):
        # 弹弓支柱
        sx, sy = SLING_X, SLING_Y
        # 左支柱
        pygame.draw.line(self.screen, COLOR_SLING, (sx - 8, sy),
                         (sx - 8, sy + 80), 5)
        # 右支柱
        pygame.draw.line(self.screen, COLOR_SLING, (sx + 8, sy),
                         (sx + 8, sy + 80), 5)
        # 弹弓叉 (Y形)
        pygame.draw.line(self.screen, COLOR_SLING, (sx - 8, sy),
                         (sx - 20, sy - 20), 4)
        pygame.draw.line(self.screen, COLOR_SLING, (sx + 8, sy),
                         (sx + 20, sy - 20), 4)

        # 皮筋
        if self.dragging and self.bird and self.state == STATE_AIMING:
            bx, by = int(self.drag_current[0]), int(self.drag_current[1])
            # 后皮筋（从叉到鸟）
            pygame.draw.line(self.screen, (40, 20, 10),
                             (sx - 20, sy - 20), (bx, by), 3)
            pygame.draw.line(self.screen, (40, 20, 10),
                             (sx + 20, sy - 20), (bx, by), 3)
            # 前皮筋（从叉到叉下）
            pygame.draw.line(self.screen, (60, 30, 15),
                             (sx - 20, sy - 20), (sx, sy + 25), 3)
            pygame.draw.line(self.screen, (60, 30, 15),
                             (sx + 20, sy - 20), (sx, sy + 25), 3)
        elif self.bird and self.state == STATE_AIMING:
            # 皮筋在叉上
            pygame.draw.line(self.screen, COLOR_SLING,
                             (sx - 20, sy - 20), (sx, sy + 25), 3)
            pygame.draw.line(self.screen, COLOR_SLING,
                             (sx + 20, sy - 20), (sx, sy + 25), 3)

    def draw_trajectory_preview(self):
        """绘制瞄准时的轨迹预览"""
        if not self.dragging or not self.bird:
            return
        sx, sy = SLING_X, SLING_Y
        ex, ey = self.drag_current
        # 计算发射方向
        dx = sx - ex
        dy = sy - ey
        # 限制最大距离
        dist = math.sqrt(dx * dx + dy * dy)
        max_dist = 200
        if dist > max_dist:
            dx = dx / dist * max_dist
            dy = dy / dist * max_dist
        # 速度
        power = min(dist / max_dist, 1.0)
        vx = dx * power * 1.5
        vy = dy * power * 1.5

        # 模拟轨迹
        px, py = sx, sy
        lvx, lvy = vx, vy
        points = [(int(px), int(py))]
        for _ in range(30):
            lvy += GRAVITY * 0.03
            px += lvx * 0.03
            py += lvy * 0.03
            if py > GROUND_Y:
                break
            points.append((int(px), int(py)))

        # 绘制轨迹点
        for i, (ptx, pty) in enumerate(points):
            alpha = 200 - i * 6
            if alpha < 30:
                alpha = 30
            r = 4 - i * 0.1
            if r < 1:
                r = 1
            pygame.draw.circle(self.screen, (255, 255, 255, alpha),
                               (ptx, pty), int(r))

    def draw_hud(self):
        # 分数
        score_text = self.font.render(f"分数: {self.total_score}", True, COLOR_BLACK)
        self.screen.blit(score_text, (20, 20))

        # 关卡
        level_text = self.font.render(f"关卡 {self.level}", True, COLOR_BLACK)
        self.screen.blit(level_text, (20, 60))

        # 剩余小鸟
        remaining = len(self.birds) - self.current_bird_idx
        bird_text = self.font.render(f"小鸟: {remaining}", True, COLOR_BLACK)
        self.screen.blit(bird_text, (20, 100))

        # 当前关分数
        if self.score > 0:
            score_earned = self.font.render(f"本关 +{self.score}", True, (220, 100, 0))
            self.screen.blit(score_earned, (20, 140))

        # 提示
        if self.state == STATE_AIMING:
            hint = "拖拽小鸟发射！"
            hint_surf = self.small_font.render(hint, True, COLOR_BLACK)
            self.screen.blit(hint_surf, (SLING_X - 60, SLING_Y + 50))

    def draw_overlay(self):
        if self.state == STATE_WIN:
            # 过关
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 120))
            self.screen.blit(s, (0, 0))
            text = self.big_font.render("过关！", True, COLOR_WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
            self.screen.blit(text, text_rect)
            sub = self.font.render(f"本关得分: {self.score}", True, COLOR_WHITE)
            sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            self.screen.blit(sub, sub_rect)
        elif self.state == STATE_LOSE:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 120))
            self.screen.blit(s, (0, 0))
            text = self.big_font.render("失败！", True, (255, 100, 100))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
            self.screen.blit(text, text_rect)
            sub = self.font.render("按 R 重试", True, COLOR_WHITE)
            sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            self.screen.blit(sub, sub_rect)

    def draw(self):
        self.draw_background()

        # 绘制方块
        for block in self.blocks:
            block.draw(self.screen)

        # 绘制猪
        for pig in self.pigs:
            pig.draw(self.screen)

        # 绘制弹弓
        self.draw_slingshot()

        # 绘制轨迹预览
        self.draw_trajectory_preview()

        # 绘制小鸟（在弹弓上的鸟在皮筋前绘制）
        # 等待队列中的鸟
        for i in range(self.current_bird_idx + 1, len(self.birds)):
            b = self.birds[i]
            if b is not self.bird:
                # 在左侧排列显示
                bx = 60 + (i - self.current_bird_idx - 1) * 40
                by = GROUND_Y - 20
                # 只画一个圆圈代表
                pygame.draw.circle(self.screen, COLOR_BIRD_RED, (bx, by), 12)
                pygame.draw.circle(self.screen, COLOR_BLACK, (bx, by), 12, 1)

        # 绘制当前鸟
        if self.bird and self.bird.alive:
            if self.dragging and self.state == STATE_AIMING:
                # 拖拽时在鼠标位置画鸟
                old_x, old_y = self.bird.x, self.bird.y
                self.bird.x, self.bird.y = self.drag_current
                self.bird.draw(self.screen)
                self.bird.x, self.bird.y = old_x, old_y
            else:
                self.bird.draw(self.screen)

        # 粒子
        for p in self.particles:
            alpha = int(255 * (p['life'] / p['max_life']))
            color = tuple(min(255, c) for c in p['color'])
            pygame.draw.circle(self.screen, color,
                               (int(p['x']), int(p['y'])), p['size'])

        # HUD
        self.draw_hud()
        self.draw_overlay()

        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    if self.state in (STATE_WIN, STATE_LOSE, STATE_WAITING):
                        self.score = 0
                        self.reset_level()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == STATE_AIMING and self.bird:
                    mx, my = event.pos
                    # 检测是否点击到鸟（在弹弓位置）
                    dx = mx - SLING_X
                    dy = my - SLING_Y
                    if dx * dx + dy * dy < 50 * 50:
                        self.dragging = True
                        self.drag_start = (SLING_X, SLING_Y)
                        self.drag_current = (mx, my)
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    mx, my = event.pos
                    # 限制拖拽距离
                    dx = mx - SLING_X
                    dy = my - SLING_Y
                    dist = math.sqrt(dx * dx + dy * dy)
                    max_dist = 200
                    if dist > max_dist:
                        dx = dx / dist * max_dist
                        dy = dy / dist * max_dist
                        mx = SLING_X + dx
                        my = SLING_Y + dy
                    self.drag_current = (mx, my)
            elif event.type == pygame.MOUSEBUTTONUP:
                if self.dragging and self.state == STATE_AIMING and self.bird:
                    self.dragging = False
                    # 计算发射方向和力度
                    dx = SLING_X - self.drag_current[0]
                    dy = SLING_Y - self.drag_current[1]
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist > 15:  # 最小拖拽距离
                        power = min(dist / 200, 1.0)
                        vx = dx * power * 3.5
                        vy = dy * power * 3.5
                        self.bird.launch(vx, vy)
                        self.state = STATE_FLYING
                    else:
                        # 拖拽距离太小，不发射
                        pass

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            if dt > 0.05:
                dt = 0.05  # 防止大跳帧
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    game = AngryBirds()
    game.run()