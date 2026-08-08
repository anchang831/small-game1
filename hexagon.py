"""
超六边形 (Hexagon Survival)
类 Super Hexagon 旋转躲避生存游戏
- 玩家围绕中心六边形旋转，躲避从四周逼近的彩色墙壁
- 每多存活一秒，难度递增
- 左右方向键 / A D 控制旋转方向
"""

import pygame
import math
import random
import sys

# ==================== 初始化 ====================
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("超六边形 - Hexagon Survival")
clock = pygame.time.Clock()

# 字体
FONT_LARGE = pygame.font.Font(None, 72)
FONT_MED = pygame.font.Font(None, 48)
FONT_SMALL = pygame.font.Font(None, 32)
FONT_TINY = pygame.font.Font(None, 20)

# ==================== 颜色 ====================
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 100, 255)
YELLOW = (255, 255, 50)
CYAN = (50, 255, 255)
ORANGE = (255, 150, 50)
PURPLE = (200, 50, 255)
GRAY = (60, 60, 60)
DARK_GRAY = (20, 20, 20)

WALL_COLORS = [
    (255, 50, 50), (255, 100, 50), (255, 50, 100),
    (200, 50, 200), (255, 150, 50), (255, 80, 80),
    (255, 200, 50), (255, 50, 200)
]

# ==================== 常量 ====================
CENTER = (WIDTH // 2, HEIGHT // 2)
PLAYER_RADIUS = 72        # 玩家距中心的固定距离
WALL_THICKNESS = 16        # 墙壁厚度
HEX_RADIUS = 80            # 装饰六边形半径
ROTATION_RATE = 0.085      # 玩家旋转速度
INITIAL_WALL_SPEED = 1.8   # 墙壁初始速度
SPAWN_INTERVAL_BASE = 55   # 基础生成间隔(帧数)

# ==================== 游戏状态 ====================
player_angle = 0.0          # 玩家当前角度(弧度)
rotation_input = 0.0        # 旋转输入: -1, 0, 1
walls = []                  # 墙壁列表
spawn_timer = 0
game_speed = 1.0
score = 0
high_score = 0
game_state = "menu"         # menu | playing | game_over
combo = 0                   # 连续躲避计数
max_combo = 0

# 粒子效果
particles = []


# ==================== 辅助函数 ====================

def draw_hexagon(surf, center, radius, color, width=2, glow=False):
    """绘制六边形"""
    points = []
    for i in range(6):
        angle = math.pi / 3 * i - math.pi / 6
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))
    if glow:
        # 发光效果
        for r in range(radius + 4, radius + 16, 4):
            pts = []
            for i in range(6):
                angle = math.pi / 3 * i - math.pi / 6
                x = center[0] + r * math.cos(angle)
                y = center[1] + r * math.sin(angle)
                pts.append((x, y))
            alpha = max(0, 80 - (r - radius) * 10)
            pygame.draw.polygon(surf, (*color, alpha), pts, 1)
    pygame.draw.polygon(surf, color, points, width)


def draw_player(surf, angle):
    """绘制玩家三角形箭头"""
    r = PLAYER_RADIUS
    cx, cy = CENTER
    x = cx + r * math.cos(angle)
    y = cy + r * math.sin(angle)

    # 发光拖尾
    for i in range(3, 0, -1):
        a = angle + rotation_input * 0.03 * i
        px = cx + r * math.cos(a)
        py = cy + r * math.sin(a)
        size = 12 - i * 3
        tip = (px + size * math.cos(angle), py + size * math.sin(angle))
        left = (px + size * 0.5 * math.cos(angle + 2.5), py + size * 0.5 * math.sin(angle + 2.5))
        right = (px + size * 0.5 * math.cos(angle - 2.5), py + size * 0.5 * math.sin(angle - 2.5))
        alpha = 60 - i * 15
        if alpha > 0:
            pygame.draw.polygon(surf, (*CYAN, alpha), [tip, left, right])

    # 主体三角形
    tip = (x + 16 * math.cos(angle), y + 16 * math.sin(angle))
    left = (x + 9 * math.cos(angle + 2.4), y + 9 * math.sin(angle + 2.4))
    right = (x + 9 * math.cos(angle - 2.4), y + 9 * math.sin(angle - 2.4))
    pygame.draw.polygon(surf, WHITE, [tip, left, right])
    pygame.draw.polygon(surf, CYAN, [tip, left, right], 2)


def spawn_wall():
    """生成一面墙壁：覆盖大部分圆周，留一个缺口"""
    gap_size = random.uniform(1.0, 2.2)  # 缺口弧度大小
    gap_start = random.uniform(0, 2 * math.pi)

    # 随难度增加，缺口变小、墙壁变快
    speed_mult = 0.8 + random.random() * 0.4
    if game_speed > 2.0:
        gap_size = random.uniform(0.8, 1.8)

    wall = {
        'distance': WIDTH * 0.8,  # 从屏幕边缘开始
        'gap_start': gap_start,
        'gap_end': gap_start + gap_size,
        'speed': INITIAL_WALL_SPEED * speed_mult,
        'color': random.choice(WALL_COLORS),
        'passed': False  # 是否已通过玩家位置
    }
    return wall


def draw_walls(surf):
    """绘制所有墙壁（使用多边形渲染厚弧段）"""
    for wall in walls:
        d = wall['distance']
        if d <= 0:
            continue

        outer_r = min(d, WIDTH * 0.8)
        inner_r = max(0, d - WALL_THICKNESS)

        if outer_r <= 0:
            continue

        color = wall['color']
        gap_start = wall['gap_start']
        gap_end = wall['gap_end']
        # 墙壁覆盖从 gap_end 到 gap_start+2π 的区域（即非缺口部分）
        start_angle = gap_end
        end_angle = gap_start + 2 * math.pi

        # 构建多边形顶点
        points = []
        num_segments = 48

        # 外弧
        for i in range(num_segments + 1):
            t = i / num_segments
            a = start_angle + (end_angle - start_angle) * t
            x = CENTER[0] + outer_r * math.cos(a)
            y = CENTER[1] + outer_r * math.sin(a)
            points.append((x, y))

        # 内弧（反向）
        for i in range(num_segments, -1, -1):
            t = i / num_segments
            a = start_angle + (end_angle - start_angle) * t
            x = CENTER[0] + inner_r * math.cos(a)
            y = CENTER[1] + inner_r * math.sin(a)
            points.append((x, y))

        if len(points) > 2:
            # 发光描边
            glow_color = (min(255, color[0] + 60), min(255, color[1] + 60), min(255, color[2] + 60))
            # 先画发光外圈
            pygame.draw.polygon(surf, glow_color, points, 3)
            # 再画填充
            pygame.draw.polygon(surf, color, points)


def check_collision():
    """检测玩家是否与墙壁碰撞"""
    for wall in walls:
        d = wall['distance']
        # 墙壁覆盖 [d - WALL_THICKNESS, d] 范围
        if not (d - WALL_THICKNESS <= PLAYER_RADIUS <= d):
            continue

        pa = player_angle % (2 * math.pi)
        gs = wall['gap_start'] % (2 * math.pi)
        ge = wall['gap_end'] % (2 * math.pi)

        # 判断玩家是否在缺口内
        in_gap = False
        if gs < ge:
            if gs < pa < ge:
                in_gap = True
        else:  # 缺口跨越0度
            if pa > gs or pa < ge:
                in_gap = True

        if not in_gap:
            return True, wall
    return False, None


def add_particles(x, y, color, count=15):
    """添加粒子效果"""
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 5)
        particles.append({
            'x': x,
            'y': y,
            'vx': math.cos(angle) * speed,
            'vy': math.sin(angle) * speed,
            'life': random.randint(20, 40),
            'max_life': 40,
            'color': color,
            'size': random.randint(2, 5)
        })


def update_particles():
    """更新粒子"""
    for p in particles[:]:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['vx'] *= 0.96
        p['vy'] *= 0.96
        p['life'] -= 1
        if p['life'] <= 0:
            particles.remove(p)


def draw_particles(surf):
    """绘制粒子"""
    for p in particles:
        alpha = int(255 * p['life'] / p['max_life'])
        size = int(p['size'] * p['life'] / p['max_life'])
        if size > 0:
            pygame.draw.circle(surf, (*p['color'], alpha), (int(p['x']), int(p['y'])), size)


def draw_background(surf):
    """绘制背景装饰"""
    # 背景网格
    for r in range(100, 500, 40):
        alpha = max(10, 30 - r // 20)
        draw_hexagon(surf, CENTER, r, (*GRAY, alpha), 1)


def reset_game():
    """重置游戏状态"""
    global player_angle, rotation_input, walls, spawn_timer, game_speed, score, particles, combo, max_combo
    player_angle = 0.0
    rotation_input = 0.0
    walls = []
    spawn_timer = 0
    game_speed = 1.0
    score = 0
    particles = []
    combo = 0
    max_combo = 0


# ==================== 主循环 ====================
running = True
while running:
    clock.tick(60)
    dt = 1.0  # 固定时间步长

    # ---- 事件处理 ----
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key in (pygame.K_LEFT, pygame.K_a):
                rotation_input = -1
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                rotation_input = 1
            if event.key == pygame.K_SPACE:
                if game_state == "menu":
                    reset_game()
                    game_state = "playing"
                elif game_state == "game_over":
                    reset_game()
                    game_state = "playing"
        if event.type == pygame.KEYUP:
            if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                rotation_input = 0

    # ---- 绘制背景 ----
    screen.fill(DARK_GRAY)
    draw_background(screen)

    # ---- 根据不同状态处理 ----
    if game_state == "menu":
        # 装饰性旋转六边形
        t = pygame.time.get_ticks() / 1000
        draw_hexagon(screen, CENTER, HEX_RADIUS, WHITE, 2, glow=True)
        # 旋转的装饰点
        for i in range(6):
            a = t * 0.5 + math.pi / 3 * i
            x = CENTER[0] + 120 * math.cos(a)
            y = CENTER[1] + 120 * math.sin(a)
            pygame.draw.circle(screen, CYAN, (int(x), int(y)), 3)

        # 标题
        title = FONT_LARGE.render("超六边形", True, WHITE)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 120)))

        subtitle = FONT_SMALL.render("HEXAGON SURVIVAL", True, CYAN)
        screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))

        # 提示
        blink = int(pygame.time.get_ticks() / 500) % 2 == 0
        if blink:
            start = FONT_SMALL.render("按 SPACE 开始游戏", True, WHITE)
            screen.blit(start, start.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)))

        controls = FONT_TINY.render("← → / A D 旋转  |  在墙壁逼近时躲入缺口", True, GRAY)
        screen.blit(controls, controls.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100)))

        if high_score > 0:
            hs = FONT_SMALL.render(f"最高分: {int(high_score)}", True, YELLOW)
            screen.blit(hs, hs.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 160)))

    elif game_state == "playing":
        # ---- 更新 ----
        # 玩家旋转
        player_angle = (player_angle + rotation_input * ROTATION_RATE) % (2 * math.pi)

        # 分数和难度
        score += 1 / 60.0
        game_speed = 1.0 + score / 25.0

        # 生成墙壁
        spawn_timer += 1
        spawn_interval = max(18, int(SPAWN_INTERVAL_BASE - score * 2))
        if spawn_timer >= spawn_interval:
            walls.append(spawn_wall())
            spawn_timer = 0

        # 移动墙壁
        for wall in walls[:]:
            wall['distance'] -= wall['speed'] * game_speed
            # 标记通过
            if not wall['passed'] and wall['distance'] < PLAYER_RADIUS - WALL_THICKNESS:
                wall['passed'] = True
                combo += 1
                if combo > max_combo:
                    max_combo = combo
            if wall['distance'] < -WALL_THICKNESS * 2:
                walls.remove(wall)

        # 碰撞检测
        collision, hit_wall = check_collision()
        if collision:
            # 碰撞粒子效果
            px = CENTER[0] + PLAYER_RADIUS * math.cos(player_angle)
            py = CENTER[1] + PLAYER_RADIUS * math.sin(player_angle)
            add_particles(px, py, RED, 30)
            # 记录最高分
            if score > high_score:
                high_score = score
            game_state = "game_over"

        # 更新粒子
        update_particles()

        # ---- 绘制 ----
        draw_hexagon(screen, CENTER, HEX_RADIUS, WHITE, 2, glow=True)
        draw_walls(screen)
        draw_particles(screen)
        draw_player(screen, player_angle)

        # 分数显示
        score_text = FONT_MED.render(f"{int(score)}", True, WHITE)
        screen.blit(score_text, score_text.get_rect(center=(WIDTH // 2, 40)))

        # 连击显示
        if combo >= 3:
            combo_text = FONT_SMALL.render(f"连击 x{combo}", True, YELLOW)
            screen.blit(combo_text, combo_text.get_rect(center=(WIDTH // 2, 80)))

        # 速度指示
        speed_text = FONT_TINY.render(f"速度 x{game_speed:.1f}", True, GRAY)
        screen.blit(speed_text, (20, 20))

    elif game_state == "game_over":
        # ---- 绘制当前场景 ----
        draw_hexagon(screen, CENTER, HEX_RADIUS, WHITE, 2, glow=True)
        draw_walls(screen)
        update_particles()
        draw_particles(screen)
        draw_player(screen, player_angle)

        # 半透明遮罩
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # 游戏结束文字
        go = FONT_LARGE.render("游戏结束", True, RED)
        screen.blit(go, go.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100)))

        fs = FONT_MED.render(f"得分: {int(score)}", True, WHITE)
        screen.blit(fs, fs.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))

        # 统计信息
        stats = FONT_TINY.render(f"最高连击: {max_combo}  |  最高纪录: {int(high_score)}", True, GRAY)
        screen.blit(stats, stats.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))

        if score >= high_score and score > 0:
            nr = FONT_SMALL.render("新纪录!", True, YELLOW)
            screen.blit(nr, nr.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))

        blink = int(pygame.time.get_ticks() / 500) % 2 == 0
        if blink:
            restart = FONT_SMALL.render("按 SPACE 重新开始", True, WHITE)
            screen.blit(restart, restart.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120)))

    # ---- 刷新 ----
    pygame.display.flip()

pygame.quit()
sys.exit()