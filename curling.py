"""
冰壶 (Curling) - 双人策略物理对战游戏
====================================
玩家轮流在冰面上投掷冰壶，目标是让冰壶停在靶心(house)附近。
每位玩家每局有4个冰壶，共进行8局。
最终得分高者获胜。

控制方式：
- 鼠标拖拽瞄准方向（从冰壶位置拖出）
- 拖拽距离控制力度
- 松开鼠标投掷冰壶
- 空格键跳过等待
"""

import pygame
import math
import random

# ========== 初始化 ==========
pygame.init()
pygame.display.set_caption("冰壶 Curling")
W, H = 1000, 680
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()
font_large = pygame.font.SysFont("simhei", 48, bold=True)
font_mid = pygame.font.SysFont("simhei", 32, bold=True)
font_small = pygame.font.SysFont("simhei", 22)
font_tiny = pygame.font.SysFont("simhei", 16)

# ========== 颜色 ==========
COLOR_ICE = (220, 235, 248)       # 冰面
COLOR_ICE_LINE = (180, 200, 220)  # 冰线
COLOR_HOUSE_BLUE = (50, 80, 180)  # 靶心蓝色环
COLOR_HOUSE_WHITE = (240, 240, 250)  # 靶心白色环
COLOR_HOUSE_RED = (200, 40, 40)  # 靶心红色环
COLOR_HOUSE_CENTER = (220, 220, 220)  # 靶心中心
COLOR_STONE_RED = (210, 50, 50)   # 红队冰壶
COLOR_STONE_DARK_RED = (160, 30, 30)
COLOR_STONE_YELLOW = (230, 200, 30)  # 黄队冰壶
COLOR_STONE_DARK_YELLOW = (180, 150, 20)
COLOR_STONE_HANDLE = (200, 200, 200)
COLOR_BG = (30, 30, 50)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_DIM = (180, 180, 180)

# ========== 游戏常量 ==========
STONE_RADIUS = 14
HOUSE_CENTER_X = 800       # 靶心x坐标
HOUSE_CENTER_Y = 340       # 靶心y坐标
HOUSE_RADII = [96, 72, 48, 20]  # 从外到内各圈半径
STONES_PER_END = 4         # 每局每队冰壶数
TOTAL_ENDS = 8             # 总局数
FRICTION = 0.985           # 冰面摩擦力系数
MIN_SPEED = 0.5            # 停止阈值
MAX_POWER = 22             # 最大投掷力度
SHOOT_FROM_X = 120         # 投掷起始x

# 冰面边界
ICE_LEFT, ICE_RIGHT = 40, 960
ICE_TOP, ICE_BOTTOM = 40, 640


class Stone:
    """冰壶类"""
    def __init__(self, x, y, player):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.player = player  # 0=红队(先手), 1=黄队(后手)
        self.radius = STONE_RADIUS
        self.moving = False
        self.landed = False  # 是否已投掷

    def update(self):
        """物理更新"""
        if not self.moving:
            return
        self.vx *= FRICTION
        self.vy *= FRICTION
        self.x += self.vx
        self.y += self.vy

        # 边界碰撞
        r = self.radius
        if self.x - r < ICE_LEFT:
            self.x = ICE_LEFT + r
            self.vx = -self.vx * 0.5
        if self.x + r > ICE_RIGHT:
            self.x = ICE_RIGHT - r
            self.vx = -self.vx * 0.5
        if self.y - r < ICE_TOP:
            self.y = ICE_TOP + r
            self.vy = -self.vy * 0.5
        if self.y + r > ICE_BOTTOM:
            self.y = ICE_BOTTOM - r
            self.vy = -self.vy * 0.5

        if abs(self.vx) < MIN_SPEED and abs(self.vy) < MIN_SPEED:
            self.vx = 0
            self.vy = 0
            self.moving = False

    def is_stopped(self):
        return not self.moving

    def distance_to(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)

    def distance_to_center(self):
        return math.hypot(self.x - HOUSE_CENTER_X, self.y - HOUSE_CENTER_Y)


def resolve_collision(a, b):
    """两冰壶弹性碰撞"""
    dx = b.x - a.x
    dy = b.y - a.y
    dist = math.hypot(dx, dy)
    if dist == 0 or dist > a.radius + b.radius:
        return
    nx = dx / dist
    ny = dy / dist

    # 重叠修正
    overlap = (a.radius + b.radius - dist) / 2
    a.x -= nx * overlap
    a.y -= ny * overlap
    b.x += nx * overlap
    b.y += ny * overlap

    # 速度交换（质量相等）
    dvx = a.vx - b.vx
    dvy = a.vy - b.vy
    dot = dvx * nx + dvy * ny
    if dot > 0:
        a.vx -= dot * nx
        a.vy -= dot * ny
        b.vx += dot * nx
        b.vy += dot * ny


def draw_ice():
    """绘制冰场"""
    screen.fill(COLOR_BG)
    # 冰面
    pygame.draw.rect(screen, COLOR_ICE, (ICE_LEFT, ICE_TOP,
                     ICE_RIGHT - ICE_LEFT, ICE_BOTTOM - ICE_TOP))

    # 冰面纹理线（细白线）
    for yy in range(ICE_TOP + 20, ICE_BOTTOM, 40):
        pygame.draw.line(screen, COLOR_ICE_LINE,
                         (ICE_LEFT, yy), (ICE_RIGHT, yy), 1)

    # 中心线
    cx = (ICE_LEFT + ICE_RIGHT) // 2
    pygame.draw.line(screen, COLOR_ICE_LINE, (cx, ICE_TOP), (cx, ICE_BOTTOM), 2)

    # 前掷线
    pygame.draw.line(screen, COLOR_ICE_LINE,
                     (300, ICE_TOP), (300, ICE_BOTTOM), 2)

    # 画靶心 (house)
    colors = [COLOR_HOUSE_BLUE, COLOR_HOUSE_WHITE,
              COLOR_HOUSE_RED, COLOR_HOUSE_CENTER]
    for i, radius in enumerate(HOUSE_RADII):
        pygame.draw.circle(screen, colors[i],
                           (HOUSE_CENTER_X, HOUSE_CENTER_Y), radius, 0)
        pygame.draw.circle(screen, (100, 100, 100),
                           (HOUSE_CENTER_X, HOUSE_CENTER_Y), radius, 1)

    # 靶心十字线
    for angle in [0, 90]:
        rad = math.radians(angle)
        ex = HOUSE_CENTER_X + HOUSE_RADII[0] * math.cos(rad)
        ey = HOUSE_CENTER_Y + HOUSE_RADII[0] * math.sin(rad)
        pygame.draw.line(screen, (100, 100, 100),
                         (HOUSE_CENTER_X, HOUSE_CENTER_Y), (ex, ey), 1)


def draw_stone(stone):
    """绘制一个冰壶"""
    x, y = int(stone.x), int(stone.y)
    r = stone.radius

    if stone.player == 0:
        body_color = COLOR_STONE_RED
        dark_color = COLOR_STONE_DARK_RED
    else:
        body_color = COLOR_STONE_YELLOW
        dark_color = COLOR_STONE_DARK_YELLOW

    # 冰壶本体（圆形）
    pygame.draw.circle(screen, dark_color, (x, y), r)
    pygame.draw.circle(screen, body_color, (x, y), r - 2)
    # 高光
    pygame.draw.circle(screen, (255, 255, 255, 80), (x - 3, y - 3), r // 3)
    # 把手
    handle_r = r // 3
    pygame.draw.circle(screen, COLOR_STONE_HANDLE, (x, y), handle_r)
    pygame.draw.circle(screen, (150, 150, 150), (x, y), handle_r, 1)

    # 玩家标记
    if stone.player == 0:
        pygame.draw.circle(screen, (255, 100, 100), (x, y), handle_r - 2)
    else:
        pygame.draw.circle(screen, (255, 255, 100), (x, y), handle_r - 2)


def draw_aim_line(stone, mouse_pos):
    """绘制瞄准线"""
    dx = stone.x - mouse_pos[0]
    dy = stone.y - mouse_pos[1]
    dist = math.hypot(dx, dy)
    if dist < 5:
        return
    power = min(dist / 8, MAX_POWER)
    # 方向线（从冰壶向鼠标反方向延伸）
    nx = dx / dist
    ny = dy / dist
    end_x = stone.x + nx * 60
    end_y = stone.y + ny * 60

    # 瞄准线
    pygame.draw.line(screen, (255, 255, 100, 180),
                     (int(stone.x), int(stone.y)),
                     (int(end_x), int(end_y)), 3)
    # 力度指示 - 用圆圈
    for i in range(int(power)):
        alpha = max(50, 255 - i * 12)
        c = (255, max(200 - i * 10, 50), 50)
        pygame.draw.circle(screen, c,
                           (int(stone.x + nx * (i * 4 + 10)),
                            int(stone.y + ny * (i * 4 + 10))),
                           3, 0)

    # 显示力度
    power_text = font_tiny.render(f"力度: {int(power * 100 / MAX_POWER)}%",
                                  True, (255, 255, 200))
    screen.blit(power_text, (mouse_pos[0] + 15, mouse_pos[1] - 10))


def score_end(stones):
    """计算一局得分"""
    red_stones = [s for s in stones if s.player == 0 and s.landed]
    yellow_stones = [s for s in stones if s.player == 1 and s.landed]

    if not red_stones and not yellow_stones:
        return 0, 0

    # 找最近距离
    red_min = min((s.distance_to_center() for s in red_stones), default=999)
    yellow_min = min((s.distance_to_center() for s in yellow_stones), default=999)

    # 如果某队没有冰壶
    if not red_stones:
        count = sum(1 for s in yellow_stones if s.distance_to_center() < 999)
        return 0, count
    if not yellow_stones:
        count = sum(1 for s in red_stones if s.distance_to_center() < 999)
        return count, 0

    # 距离靶心最近的在house半径内的冰壶得分
    if red_min < yellow_min and red_min < HOUSE_RADII[0]:
        count = 0
        for s in red_stones:
            if s.distance_to_center() < HOUSE_RADII[0] and \
               s.distance_to_center() < yellow_min:
                count += 1
        return count, 0
    elif yellow_min < red_min and yellow_min < HOUSE_RADII[0]:
        count = 0
        for s in yellow_stones:
            if s.distance_to_center() < HOUSE_RADII[0] and \
               s.distance_to_center() < red_min:
                count += 1
        return 0, count
    return 0, 0


def show_result(text, sub_text="", wait_key=True):
    """显示结果弹窗"""
    overlay = pygame.Surface((W, H))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # 主文字
    txt = font_large.render(text, True, (255, 255, 100))
    tw = txt.get_width()
    screen.blit(txt, ((W - tw) // 2, H // 2 - 60))

    if sub_text:
        st = font_mid.render(sub_text, True, (200, 200, 200))
        sw = st.get_width()
        screen.blit(st, ((W - sw) // 2, H // 2 + 10))

    hint = font_small.render("按任意键继续", True, (180, 180, 180))
    hw = hint.get_width()
    screen.blit(hint, ((W - hw) // 2, H // 2 + 70))

    pygame.display.flip()
    if wait_key:
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = True
                    return True
            clock.tick(30)
    return True


def main():
    """主游戏循环"""
    stones = []
    end_num = 1
    scores = [0, 0]  # 红队, 黄队
    current_player = 0  # 0=红, 1=黄
    stones_this_end = 0
    turn = 0  # 第几次投掷 (0-based)

    # 状态: 'aiming', 'simulating', 'scoring', 'game_over'
    state = 'aiming'
    dragging = False
    drag_start = None
    selected_stone = None
    aim_mouse = None
    skip_anim = False
    running = True

    def init_end():
        nonlocal stones, stones_this_end, turn, current_player, state, dragging
        stones = []
        stones_this_end = 0
        turn = 0
        current_player = 0
        state = 'aiming'
        dragging = False

    def shoot_stone():
        nonlocal stones_this_end, turn, current_player, state, dragging, selected_stone
        if selected_stone is None:
            return
        dx = selected_stone.x - aim_mouse[0]
        dy = selected_stone.y - aim_mouse[1]
        dist = math.hypot(dx, dy)
        if dist < 5:
            return
        power = min(dist / 8, MAX_POWER)
        nx = dx / dist
        ny = dy / dist
        selected_stone.vx = nx * power
        selected_stone.vy = ny * power
        selected_stone.moving = True
        selected_stone.landed = True
        selected_stone = None
        dragging = False
        state = 'simulating'

    init_end()

    while running:
        # === 事件处理 ===
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and state == 'simulating':
                    skip_anim = True
                if event.key == pygame.K_r and state == 'game_over':
                    # 重新开始
                    scores = [0, 0]
                    end_num = 1
                    init_end()
                    state = 'aiming'

            if state == 'aiming':
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    # 找到当前玩家未投掷的冰壶
                    if stones_this_end < STONES_PER_END * 2:
                        # 已经没有待投掷的冰壶时创建一个新的
                        waiting = [s for s in stones
                                   if s.player == current_player and not s.landed]
                        if not waiting:
                            # 在投掷区创建新冰壶，随机y偏移
                            yy = random.randint(ICE_TOP + 30, ICE_BOTTOM - 30)
                            new_stone = Stone(SHOOT_FROM_X, yy, current_player)
                            stones.append(new_stone)
                            waiting = [new_stone]

                        for s in waiting:
                            dist = math.hypot(mx - s.x, my - s.y)
                            if dist < STONE_RADIUS + 20:
                                dragging = True
                                drag_start = (mx, my)
                                selected_stone = s
                                aim_mouse = (mx, my)
                                break

                if event.type == pygame.MOUSEMOTION and dragging:
                    aim_mouse = event.pos

                if event.type == pygame.MOUSEBUTTONUP and dragging:
                    shoot_stone()

        # === 物理模拟 ===
        if state == 'simulating':
            all_stopped = True
            for s in stones:
                if s.moving:
                    s.update()
                    if s.moving:
                        all_stopped = False
            # 碰撞检测
            for i in range(len(stones)):
                for j in range(i + 1, len(stones)):
                    if stones[i].distance_to(stones[j]) < stones[i].radius + stones[j].radius:
                        resolve_collision(stones[i], stones[j])

            if skip_anim:
                # 快速跳过：直接让所有冰壶停住
                for s in stones:
                    s.moving = False
                    s.vx = 0
                    s.vy = 0
                skip_anim = False
                all_stopped = True

            if all_stopped:
                stones_this_end += 1
                turn += 1
                current_player = 1 - current_player

                if stones_this_end >= STONES_PER_END * 2:
                    # 一局结束，计分
                    state = 'scoring'
                else:
                    state = 'aiming'

        # === 计分 ===
        if state == 'scoring':
            rs, ys = score_end(stones)
            scores[0] += rs
            scores[1] += ys
            score_text = f"红队 +{rs}  黄队 +{ys}"

            # 显示得分
            draw_ice()
            for s in stones:
                draw_stone(s)
            # 显示计分板
            _draw_scoreboard(scores, end_num, current_player, state)
            pygame.display.flip()

            pygame.time.wait(1500)

            if end_num >= TOTAL_ENDS:
                state = 'game_over'
            else:
                end_num += 1
                init_end()

        # === 游戏结束 ===
        if state == 'game_over':
            # 绘制最终状态
            draw_ice()
            for s in stones:
                draw_stone(s)
            _draw_scoreboard(scores, end_num - 1, current_player, state)

            if scores[0] > scores[1]:
                winner = "🏆 红队获胜！"
                sub = f"最终比分: 红队 {scores[0]} - {scores[1]} 黄队"
            elif scores[1] > scores[0]:
                winner = "🏆 黄队获胜！"
                sub = f"最终比分: 红队 {scores[0]} - {scores[1]} 黄队"
            else:
                winner = "🤝 平局！"
                sub = f"双方得分: {scores[0]}"

            show_result(winner, sub)
            continue

        # === 绘制 ===
        draw_ice()

        # 绘制冰壶
        for s in stones:
            if s != selected_stone:
                draw_stone(s)
        if selected_stone:
            draw_stone(selected_stone)

        # 瞄准线
        if dragging and selected_stone and aim_mouse:
            draw_aim_line(selected_stone, aim_mouse)

        # 计分板
        _draw_scoreboard(scores, end_num, current_player, state)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def _draw_scoreboard(scores, end_num, current_player, game_state):
    """绘制计分板"""
    # 顶部信息栏背景
    pygame.draw.rect(screen, (20, 20, 40, 200), (0, 0, W, 55))
    pygame.draw.rect(screen, (60, 60, 80), (0, 0, W, 55), 2)

    # 局数
    end_text = font_mid.render(f"第 {end_num}/{TOTAL_ENDS} 局", True, (255, 255, 255))
    screen.blit(end_text, (20, 10))

    # 得分
    red_text = font_mid.render(f"🔴 红队: {scores[0]}", True, (255, 120, 120))
    yellow_text = font_mid.render(f"🟡 黄队: {scores[1]}", True, (255, 255, 120))
    screen.blit(red_text, (280, 10))
    screen.blit(yellow_text, (480, 10))

    # 当前玩家指示
    if game_state == 'aiming':
        p_name = "红队" if current_player == 0 else "黄队"
        p_color = (255, 150, 150) if current_player == 0 else (255, 255, 150)
        turn_text = font_mid.render(f"当前: {p_name} 投掷", True, p_color)
        screen.blit(turn_text, (700, 10))
    elif game_state == 'simulating':
        sim_text = font_mid.render("模拟中... (空格跳过)", True, (180, 180, 180))
        screen.blit(sim_text, (700, 10))

    # 右下角操作提示
    hint = font_tiny.render("鼠标拖拽瞄准 → 松开投掷 | R=重新开始", True, (150, 150, 150))
    screen.blit(hint, (W - hint.get_width() - 10, H - 25))


if __name__ == "__main__":
    main()