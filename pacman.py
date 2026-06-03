"""
Pacman 吃豆人 - 经典街机游戏
============================
操作: 方向键控制吃豆人移动
目标: 吃掉所有豆子并躲避幽灵
玩法: 吃到大能量豆可反吃幽灵

Date: 2026-06-03
"""

import pygame
import random
import sys
import math

# ==================== 初始化 ====================
pygame.init()

# ==================== 常量定义 ====================
TILE_SIZE = 20
COLS = 28
ROWS = 31
SCREEN_WIDTH = COLS * TILE_SIZE   # 560
SCREEN_HEIGHT = ROWS * TILE_SIZE  # 620
SCORE_HEIGHT = 40  # 顶部分数区域高度

# 颜色 (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
PINK = (255, 182, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 182, 85)
DARK_BLUE = (0, 0, 139)
GHOST_COLOR = (255, 0, 0)
GREY = (100, 100, 100)

# 方向常量
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
STOP = (0, 0)

# 游戏状态
READY = "ready"
PLAYING = "playing"
GAME_OVER = "game_over"
WIN = "win"

# 幽灵状态
SCATTER = "scatter"
CHASE = "chase"
FRIGHTENED = "frightened"
EATEN = "eaten"

# 帧率
FPS = 60

# ==================== 迷宫地图 ====================
# 图例: W=墙, .=豆子, P=大力豆, -=门, G=幽灵出生点, H=幽灵之家, E=空
# 吃豆人出生点为 14x23 位置 (23行14列)
MAZE_TEMPLATE = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "W............WW............W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "WoW  W.W   W.WW.W   W.W  WoW",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W..........................W",
    "W.WWWW.WW.WWWWWWWW.WW.WWWW.W",
    "W.WWWW.WW.WWWWWWWW.WW.WWWW.W",
    "W......WW....WW....WW......W",
    "WWWWWW.WWWWW WW WWWWW.WWWWWW",
    "EEEEEW.WWWWW WW WWWWW.WEEEEE",
    "EEEEEW.WW          WW.WEEEEE",
    "EEEEEW.WW WWWWWWWW WW.WEEEEE",
    "WWWWWW.WW WEEEEEEW WW.WWWWWW",
    "EEEEEE.EE WEEEEEEW EE.EEEEEE",
    "WWWWWW.WW WEEEEEEW WW.WWWWWW",
    "EEEEEW.WW WWWWWWWW WW.WEEEEE",
    "EEEEEW.WW          WW.WEEEEE",
    "EEEEEW.WW WWWWWWWW WW.WEEEEE",
    "WWWWWW.WW WWWWWWWW WW.WWWWWW",
    "W............WW............W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "WoW..W................W..WoW",
    "WWW.WW.WW.WWWWWWWW.WW.WW.WWW",
    "WWW.WW.WW.WWWWWWWW.WW.WW.WWW",
    "W......WW....WW....WW......W",
    "W.WWWWWWWWWW.WW.WWWWWWWWWW.W",
    "W.WWWWWWWWWW.WW.WWWWWWWWWW.W",
    "W..........................W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWW",
]

# 解析地图
def parse_maze():
    """将地图模板解析为可用的数据结构"""
    wall_cells = []
    dot_cells = []
    power_cells = []
    ghost_home = []
    ghost_door = []
    pacman_start = None
    ghost_start_positions = []

    for y, row in enumerate(MAZE_TEMPLATE):
        for x, char in enumerate(row):
            if char == 'W':
                wall_cells.append((x, y))
            elif char == '.':
                dot_cells.append((x, y))
            elif char == 'o':
                power_cells.append((x, y))
            elif char == '-':
                ghost_door.append((x, y))
            elif char == 'G':
                ghost_home.append((x, y))
                ghost_start_positions.append((x, y))
            elif char == 'H':
                ghost_start_positions.append((x, y))

    # 吃豆人起始位置
    pacman_start = (14, 23)

    # 如果没有正确设置，使用默认位置
    if not ghost_start_positions:
        ghost_start_positions = [(14, 11), (13, 11), (15, 11), (14, 14)]

    return wall_cells, dot_cells, power_cells, ghost_home, ghost_door, pacman_start, ghost_start_positions

WALL_CELLS, DOT_CELLS, POWER_CELLS, GHOST_HOME, GHOST_DOOR, PACMAN_START, GHOST_STARTS = parse_maze()

# 计算总豆子数
TOTAL_DOTS = len(DOT_CELLS) + len(POWER_CELLS)

# ==================== 辅助函数 ====================
def cell_to_pixel(cell_pos):
    """网格坐标转像素坐标（中心点）"""
    x, y = cell_pos
    return x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2 + SCORE_HEIGHT

def pixel_to_cell(pixel_pos):
    """像素坐标转网格坐标"""
    px, py = pixel_pos
    py -= SCORE_HEIGHT
    return int(px // TILE_SIZE), int(py // TILE_SIZE)

def get_cell_center(cell_pos):
    """获取网格中心像素坐标"""
    px, py = cell_to_pixel(cell_pos)
    return px, py

# ==================== 玩家（吃豆人）类 ====================
class Pacman:
    def __init__(self, start_pos):
        self.start_pos = start_pos
        self.reset()

    def reset(self):
        self.grid_pos = list(self.start_pos)
        self.pixel_pos = list(cell_to_pixel(self.start_pos))
        self.direction = STOP
        self.next_direction = STOP
        self.speed = 2  # 像素/帧
        self.mouth_angle = 0  # 嘴巴动画
        self.mouth_dir = 1
        self.alive = True
        self.anim_frame = 0

    def set_direction(self, direction):
        """设置下一个移动方向"""
        self.next_direction = direction

    def can_move(self, direction, walls):
        """检查是否能朝指定方向移动"""
        test_pos = (self.grid_pos[0] + direction[0], self.grid_pos[1] + direction[1])
        return test_pos not in walls

    def can_move_pixel(self, pixel_pos, direction, walls):
        """基于像素位置检查是否能移动（处理拐弯对齐）"""
        cx = pixel_pos[0] - TILE_SIZE // 2
        cy = pixel_pos[1] - TILE_SIZE // 2 - SCORE_HEIGHT

        # 计算当前覆盖的网格
        grid_x = cx / TILE_SIZE
        grid_y = cy / TILE_SIZE

        # 检查移动方向是否有墙
        if direction == LEFT:
            test_x = int(math.floor(grid_x)) - 1
            test_y = int(grid_y)
            if test_y < 0 or test_y >= ROWS:
                return False
            return (test_x, test_y) not in walls
        elif direction == RIGHT:
            test_x = int(math.ceil(grid_x)) + 1
            test_y = int(grid_y)
            if test_y < 0 or test_y >= ROWS:
                return False
            return (test_x, test_y) not in walls
        elif direction == UP:
            test_x = int(grid_x)
            test_y = int(math.floor(grid_y)) - 1
            if test_x < 0 or test_x >= COLS:
                return False
            return (test_x, test_y) not in walls
        elif direction == DOWN:
            test_x = int(grid_x)
            test_y = int(math.ceil(grid_y)) + 1
            if test_x < 0 or test_x >= COLS:
                return False
            return (test_x, test_y) not in walls
        return True

    def is_aligned_to_grid(self):
        """检查是否对齐到网格（用于决定何时可以转弯）"""
        x_offset = (self.pixel_pos[0] - TILE_SIZE // 2) % TILE_SIZE
        y_offset = (self.pixel_pos[1] - TILE_SIZE // 2 - SCORE_HEIGHT) % TILE_SIZE
        return x_offset == 0 and y_offset == 0

    def update(self, walls):
        """更新吃豆人位置"""
        if not self.alive:
            return

        # 处理角落传送
        self._handle_wrapping()

        # 对齐到网格时尝试转弯
        if self.is_aligned_to_grid():
            # 更新网格位置
            cx = self.pixel_pos[0] - TILE_SIZE // 2
            cy = self.pixel_pos[1] - TILE_SIZE // 2 - SCORE_HEIGHT
            self.grid_pos = [round(cx / TILE_SIZE), round(cy / TILE_SIZE)]

            # 尝试使用下一个方向
            if self.next_direction != STOP:
                nx = self.grid_pos[0] + self.next_direction[0]
                ny = self.grid_pos[1] + self.next_direction[1]
                if (nx, ny) not in walls:
                    self.direction = self.next_direction

            # 检查当前方向是否可行
            nx = self.grid_pos[0] + self.direction[0]
            ny = self.grid_pos[1] + self.direction[1]
            if (nx, ny) in walls:
                self.direction = STOP

        # 移动
        if self.direction != STOP:
            self.pixel_pos[0] += self.direction[0] * self.speed
            self.pixel_pos[1] += self.direction[1] * self.speed

        # 嘴巴动画
        self.mouth_angle += 0.15 * self.mouth_dir
        if self.mouth_angle > 0.5 or self.mouth_angle < -0.5:
            self.mouth_dir *= -1

    def _handle_wrapping(self):
        """处理左右边缘传送"""
        if self.pixel_pos[0] < -TILE_SIZE:
            self.pixel_pos[0] = SCREEN_WIDTH + TILE_SIZE // 2
        elif self.pixel_pos[0] > SCREEN_WIDTH + TILE_SIZE:
            self.pixel_pos[0] = -TILE_SIZE // 2

    def draw(self, screen):
        """绘制吃豆人"""
        if not self.alive:
            return

        x, y = self.pixel_pos

        # 确定嘴巴张开角度（基于方向）
        if self.direction == RIGHT or (self.direction == STOP and self.direction != LEFT):
            start_angle = 0.15 + self.mouth_angle
            end_angle = 2 * math.pi - 0.15 - self.mouth_angle
        elif self.direction == LEFT:
            start_angle = math.pi + 0.15 + self.mouth_angle
            end_angle = math.pi - 0.15 - self.mouth_angle
        elif self.direction == UP:
            start_angle = -math.pi / 2 + 0.15 + self.mouth_angle
            end_angle = -math.pi / 2 - 0.15 - self.mouth_angle
        elif self.direction == DOWN:
            start_angle = math.pi / 2 + 0.15 + self.mouth_angle
            end_angle = math.pi / 2 - 0.15 - self.mouth_angle
        else:
            # 静止状态，面向右
            start_angle = 0.15 + self.mouth_angle
            end_angle = 2 * math.pi - 0.15 - self.mouth_angle

        # 如果方向改变了，嘴巴方向也要变
        start_angle = start_angle % (2 * math.pi)
        end_angle = end_angle % (2 * math.pi)

        # 用圆弧画吃豆人
        radius = TILE_SIZE // 2 - 2
        try:
            if abs(end_angle - start_angle) < 0.1:
                pygame.draw.circle(screen, YELLOW, (int(x), int(y)), radius)
            else:
                pygame.draw.arc(screen, YELLOW, (int(x) - radius, int(y) - radius,
                                                  radius * 2, radius * 2),
                                start_angle, end_angle, radius)
                # 画一个三角形填充切口
                mouth_mid = (start_angle + end_angle) / 2
                tip_x = x + math.cos(mouth_mid) * radius * 0.3
                tip_y = y + math.sin(mouth_mid) * radius * 0.3
                points = [
                    (x, y),
                    (x + math.cos(start_angle) * radius, y + math.sin(start_angle) * radius),
                    (tip_x, tip_y),
                    (x + math.cos(end_angle) * radius, y + math.sin(end_angle) * radius),
                ]
                pygame.draw.polygon(screen, YELLOW, points)
        except (ValueError, pygame.error):
            pygame.draw.circle(screen, YELLOW, (int(x), int(y)), radius)

    def get_grid_pos(self):
        return (int(round(self.grid_pos[0])), int(round(self.grid_pos[1])))

    def get_pixel_rect(self):
        r = TILE_SIZE // 2 - 2
        return pygame.Rect(self.pixel_pos[0] - r, self.pixel_pos[1] - r, r * 2, r * 2)


# ==================== 幽灵类 ====================
class Ghost:
    def __init__(self, start_pos, color, name, ghost_door, scatter_target):
        self.start_pos = list(start_pos)
        self.color = color
        self.name = name
        self.ghost_door = ghost_door
        self.ghost_door_pos = ghost_door[2] if len(ghost_door) > 2 else (ghost_door[0] if ghost_door else (14, 11))
        self.scatter_target = scatter_target
        self.reset()

    def reset(self):
        self.grid_pos = list(self.start_pos)
        self.pixel_pos = list(cell_to_pixel(self.start_pos))
        self.direction = UP
        self.state = SCATTER
        self.speed = 1.5
        self.frightened_speed = 1.0
        self.eaten_speed = 3.0
        self.in_house = True
        self.release_timer = random.randint(60, 180)  # 释放计时器
        self.frightened_timer = 0
        self.mode_timer = 0
        self.mode_switches = 0
        self.eye_frame = 0
        self.is_eaten = False

    def set_mode(self, mode):
        """设置幽灵模式"""
        if self.state != EATEN and self.state != FRIGHTENED:
            self.state = mode

    def set_frightened(self, duration):
        """设置恐惧模式"""
        if self.state != EATEN:
            self.state = FRIGHTENED
            self.frightened_timer = duration * FPS
            # 反转方向
            if self.direction == UP:
                self.direction = DOWN
            elif self.direction == DOWN:
                self.direction = UP
            elif self.direction == LEFT:
                self.direction = RIGHT
            elif self.direction == RIGHT:
                self.direction = LEFT

    def set_eaten(self):
        """幽灵被吃"""
        self.state = EATEN
        self.is_eaten = True

    def reset_after_eaten(self):
        """幽灵重生"""
        self.grid_pos = list(self.start_pos)
        self.pixel_pos = list(cell_to_pixel(self.start_pos))
        self.in_house = True
        self.is_eaten = False
        self.state = CHASE
        self.release_timer = random.randint(60, 180)

    def is_aligned_to_grid(self):
        """检查是否对齐到网格"""
        x_offset = (self.pixel_pos[0] - TILE_SIZE // 2) % TILE_SIZE
        y_offset = (self.pixel_pos[1] - TILE_SIZE // 2 - SCORE_HEIGHT) % TILE_SIZE
        return x_offset == 0 and y_offset == 0

    def _handle_wrapping(self):
        """处理左右边缘传送"""
        if self.pixel_pos[0] < -TILE_SIZE:
            self.pixel_pos[0] = SCREEN_WIDTH + TILE_SIZE // 2
        elif self.pixel_pos[0] > SCREEN_WIDTH + TILE_SIZE:
            self.pixel_pos[0] = -TILE_SIZE // 2

    def get_available_directions(self, walls, ghost_door):
        """获取幽灵可以移动的方向（不包括反方向）"""
        directions = []
        for d in [UP, DOWN, LEFT, RIGHT]:
            # 不能掉头
            if d[0] == -self.direction[0] and d[1] == -self.direction[1]:
                continue
            # 如果幽灵在屋内，只能通过门出去
            if self.in_house:
                if self.ghost_door:
                    nx = self.grid_pos[0] + d[0]
                    ny = self.grid_pos[1] + d[1]
                    if (nx, ny) not in walls or (nx, ny) in self.ghost_door:
                        directions.append(d)
                else:
                    # 没有门，任何方向都可以
                    directions.append(d)
                continue
            nx = self.grid_pos[0] + d[0]
            ny = self.grid_pos[1] + d[1]
            # 幽灵可以通过门（从内部出来）
            if (nx, ny) not in walls or (nx, ny) in ghost_door:
                directions.append(d)
        return directions

    def choose_target(self, pacman_pos, pacman_direction, blinky_pos):
        """根据幽灵类型和状态选择目标"""
        px, py = pacman_pos

        if self.state == SCATTER:
            return self.scatter_target
        elif self.state == FRIGHTENED:
            # 恐惧模式随机移动
            return None
        elif self.state == EATEN:
            # 被吃后返回幽灵之家
            return (14, 14)
        elif self.state == CHASE:
            if self.name == "blinky":
                # 直接追吃豆人
                return (px, py)
            elif self.name == "pinky":
                # 瞄准吃豆人前方4格
                target = (px + pacman_direction[0] * 4, py + pacman_direction[1] * 4)
                return target
            elif self.name == "inky":
                # 需要Blinky位置
                if blinky_pos:
                    # 取吃豆人位置与Blinky位置的向量，翻倍
                    vec = (px - blinky_pos[0], py - blinky_pos[1])
                    target = (px + vec[0], py + vec[1])
                    return target
                return (px, py)
            elif self.name == "clyde":
                # 距离吃豆人远时追击，近时散开
                dist = math.sqrt((self.grid_pos[0] - px) ** 2 +
                                 (self.grid_pos[1] - py) ** 2)
                if dist > 8:
                    return (px, py)
                else:
                    return self.scatter_target
        return self.scatter_target

    def update(self, walls, ghost_door, pacman_pos, pacman_direction, blinky_pos):
        """更新幽灵"""
        # 处理传送
        self._handle_wrapping()

        # 屋内释放计时
        if self.in_house:
            self.release_timer -= 1
            if self.release_timer <= 0:
                self.in_house = False
                # 出生后直接移动到门前
                if ghost_door:
                    door_pos = ghost_door[2] if len(ghost_door) > 2 else ghost_door[0]
                else:
                    door_pos = (13, 11)
                self.grid_pos = list(door_pos)
                self.pixel_pos = list(cell_to_pixel(door_pos))
                self.direction = LEFT if ghost_door else UP
            else:
                # 在屋内上下移动
                self.pixel_pos[1] += math.sin(pygame.time.get_ticks() * 0.005) * 0.5
                return

        # 恐惧计时
        if self.state == FRIGHTENED:
            self.frightened_timer -= 1
            if self.frightened_timer <= 0:
                self.state = CHASE

        # 如果被吃且回到幽灵之家
        if self.state == EATEN:
            if self.grid_pos == (14, 14) or self.grid_pos in GHOST_HOME:
                self.reset_after_eaten()
                return

        # 对齐网格时选择方向
        if self.is_aligned_to_grid():
            # 更新网格位置
            cx = self.pixel_pos[0] - TILE_SIZE // 2
            cy = self.pixel_pos[1] - TILE_SIZE // 2 - SCORE_HEIGHT
            self.grid_pos = [int(round(cx / TILE_SIZE)), int(round(cy / TILE_SIZE))]

            # 选择目标
            target = self.choose_target(pacman_pos, pacman_direction, blinky_pos)
            directions = self.get_available_directions(walls, ghost_door)

            if not directions:
                self.direction = UP
            elif self.state == FRIGHTENED:
                # 恐惧模式随机选方向
                self.direction = random.choice(directions)
            elif target:
                # 计算到每个方向目标格的距离，选最近的
                best_dir = directions[0]
                best_dist = float('inf')
                for d in directions:
                    nx = self.grid_pos[0] + d[0]
                    ny = self.grid_pos[1] + d[1]
                    dist = (nx - target[0]) ** 2 + (ny - target[1]) ** 2
                    if dist < best_dist:
                        best_dist = dist
                        best_dir = d
                self.direction = best_dir

        # 移动
        current_speed = self.speed
        if self.state == FRIGHTENED:
            current_speed = self.frightened_speed
        elif self.state == EATEN:
            current_speed = self.eaten_speed

        self.pixel_pos[0] += self.direction[0] * current_speed
        self.pixel_pos[1] += self.direction[1] * current_speed

    def draw(self, screen):
        """绘制幽灵"""
        x, y = int(self.pixel_pos[0]), int(self.pixel_pos[1])
        r = TILE_SIZE // 2 - 2

        if self.state == EATEN:
            # 只画眼睛
            self._draw_eyes(screen, x, y, r)
            return

        if self.state == FRIGHTENED:
            # 恐惧模式 - 蓝色
            color = (0, 0, 255)
            # 闪烁效果（快结束时）
            if self.frightened_timer < 120 and (self.frightened_timer // 10) % 2 == 0:
                color = (255, 255, 255)
            self._draw_ghost_body(screen, x, y, r, color)
            return

        self._draw_ghost_body(screen, x, y, r, self.color)

    def _draw_ghost_body(self, screen, x, y, r, color):
        """绘制幽灵身体"""
        # 主身体（半圆 + 波浪底部）
        body_rect = pygame.Rect(x - r, y - r, r * 2, r * 2)
        pygame.draw.circle(screen, color, (x, y - r // 3), r)
        pygame.draw.rect(screen, color, (x - r, y - r // 3, r * 2, r))

        # 波浪底部
        wave_pts = []
        for i in range(4):
            wx = x - r + i * (r * 2 / 3)
            wy = y + r // 2 + int(math.sin((pygame.time.get_ticks() * 0.01) + i) * 3)
            wave_pts.append((wx, wy))
        wave_pts.append((x + r, y + r // 2))
        wave_pts.append((x + r, y + r))
        wave_pts.append((x - r, y + r))
        pygame.draw.polygon(screen, color, wave_pts)

        # 眼睛
        self._draw_eyes(screen, x, y, r)

    def _draw_eyes(self, screen, x, y, r):
        """画眼睛"""
        eye_r = r // 3
        # 白眼白
        pygame.draw.circle(screen, WHITE, (x - r // 3, y - r // 4), eye_r + 1)
        pygame.draw.circle(screen, WHITE, (x + r // 3, y - r // 4), eye_r + 1)
        # 瞳孔（根据方向）
        dx, dy = self.direction
        if dx == 0 and dy == 0:
            dx = -1
        pupil_offset_x = dx * 2
        pupil_offset_y = dy * 2
        pygame.draw.circle(screen, BLACK,
                          (x - r // 3 + pupil_offset_x, y - r // 4 + pupil_offset_y), eye_r - 1)
        pygame.draw.circle(screen, BLACK,
                          (x + r // 3 + pupil_offset_x, y - r // 4 + pupil_offset_y), eye_r - 1)

    def get_pixel_rect(self):
        r = TILE_SIZE // 2
        return pygame.Rect(self.pixel_pos[0] - r, self.pixel_pos[1] - r, r * 2, r * 2)

    def get_grid_pos(self):
        return (int(round(self.grid_pos[0])), int(round(self.grid_pos[1])))


# ==================== 游戏主类 ====================
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT + SCORE_HEIGHT))
        pygame.display.set_caption("Pacman 吃豆人")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 22, bold=True)
        self.big_font = pygame.font.SysFont("arial", 36, bold=True)
        self.reset_game()

    def reset_game(self):
        """重置游戏"""
        self.score = 0
        self.lives = 3
        self.state = READY
        self.level = 1
        self.ghost_mode_timer = 0
        self.ghost_mode_index = 0
        self.combo = 0  # 连续吃幽灵得分倍率

        # 重新解析地图（确保豆子重置）
        self.walls = WALL_CELLS.copy()
        self.dots = DOT_CELLS.copy()
        self.power_dots = POWER_CELLS.copy()
        self.ghost_door = GHOST_DOOR.copy()
        self.ghost_home = GHOST_HOME.copy()

        # 创建吃豆人
        self.pacman = Pacman(PACMAN_START)

        # 创建幽灵
        ghost_data = [
            ("blinky", RED, (16, 11), (25, 0)),
            ("pinky", PINK, (14, 14), (2, 0)),
            ("inky", CYAN, (12, 14), (0, 30)),
            ("clyde", ORANGE, (16, 14), (27, 30)),
        ]

        self.ghosts = []
        for name, color, start, scatter in ghost_data:
            g = Ghost(start, color, name, self.ghost_door, scatter)
            if name == "blinky":
                g.in_house = False
                g.release_timer = 0
                g.grid_pos = [14, 11]
                g.pixel_pos = list(cell_to_pixel((14, 11)))
            elif name == "pinky":
                g.release_timer = 30
            elif name == "inky":
                g.release_timer = 90
            elif name == "clyde":
                g.release_timer = 150
            self.ghosts.append(g)

        self.blinky = self.ghosts[0]
        self.mode_switch_event = pygame.event.Event(pygame.USEREVENT, {"mode": CHASE})
        self.mode_timers = [7, 20, 7, 20, 5, 20, 5]  # 散射/追击切换时间（秒）
        self.mode_index = 0
        self.mode_timer = 0
        self.mode_is_scatter = True

        self.ready_timer = 120  # "READY!" 显示时间
        self.death_animation_timer = 0
        self.death_animating = False
        self.win_timer = 0

    def handle_events(self):
        """处理输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_r and self.state in [GAME_OVER, WIN]:
                    self.reset_game()
                    return True

                if self.state == READY and event.key in [pygame.K_UP, pygame.K_DOWN,
                                                          pygame.K_LEFT, pygame.K_RIGHT]:
                    self.state = PLAYING

                if self.state == PLAYING:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.pacman.set_direction(LEFT)
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.pacman.set_direction(RIGHT)
                    elif event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.pacman.set_direction(UP)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.pacman.set_direction(DOWN)
        return True

    def update_mode_timer(self):
        """更新幽灵模式（散射/追击）"""
        self.mode_timer += 1 / FPS
        if self.mode_index < len(self.mode_timers):
            if self.mode_timer >= self.mode_timers[self.mode_index]:
                self.mode_timer = 0
                self.mode_index += 1
                self.mode_is_scatter = not self.mode_is_scatter
                new_mode = SCATTER if self.mode_is_scatter else CHASE
                for ghost in self.ghosts:
                    ghost.set_mode(new_mode)

    def check_dot_collision(self):
        """检查吃豆人是否吃到豆子"""
        px, py = self.pacman.get_grid_pos()

        # 检查普通豆子
        if (px, py) in self.dots:
            self.dots.remove((px, py))
            self.score += 10
            return True

        # 检查大力豆
        if (px, py) in self.power_dots:
            self.power_dots.remove((px, py))
            self.score += 50
            self.combo = 0
            for ghost in self.ghosts:
                if ghost.state != EATEN and not ghost.in_house:
                    ghost.set_frightened(8)
            return True

        return False

    def check_ghost_collision(self):
        """检查与幽灵的碰撞"""
        pac_rect = self.pacman.get_pixel_rect()
        pac_grid = self.pacman.get_grid_pos()

        for ghost in self.ghosts:
            if ghost.in_house:
                continue
            ghost_grid = ghost.get_grid_pos()
            ghost_rect = ghost.get_pixel_rect()

            # 网格碰撞检测
            if abs(pac_grid[0] - ghost_grid[0]) <= 1 and abs(pac_grid[1] - ghost_grid[1]) <= 1:
                if ghost.state == FRIGHTENED:
                    # 吃幽灵
                    ghost.set_eaten()
                    self.combo += 1
                    self.score += 200 * (2 ** (self.combo - 1))
                elif ghost.state != EATEN:
                    # 被幽灵抓到
                    return True
        return False

    def check_win(self):
        """检查是否胜利"""
        return len(self.dots) == 0 and len(self.power_dots) == 0

    def death_animation(self):
        """死亡动画"""
        self.death_animating = True
        self.death_animation_timer += 1
        if self.death_animation_timer > 60:
            self.death_animating = False
            self.death_animation_timer = 0
            if self.lives <= 0:
                self.state = GAME_OVER
            else:
                self.state = READY
                self.pacman.reset()
                for ghost in self.ghosts:
                    ghost.reset()
                # 重新设置初始释放时间
                for i, ghost in enumerate(self.ghosts):
                    if ghost.name == "blinky":
                        ghost.in_house = False
                        ghost.release_timer = 0
                    elif ghost.name == "pinky":
                        ghost.release_timer = 30
                    elif ghost.name == "inky":
                        ghost.release_timer = 90
                    elif ghost.name == "clyde":
                        ghost.release_timer = 150
                self.ready_timer = 120

    def update(self):
        """更新游戏状态"""
        if self.state == READY:
            self.ready_timer -= 1
            if self.ready_timer <= 0:
                self.state = PLAYING
            return

        if self.state == GAME_OVER or self.state == WIN:
            return

        if self.death_animating:
            self.death_animation()
            return

        # 更新吃豆人
        self.pacman.update(self.walls)

        # 更新幽灵模式
        self.update_mode_timer()

        # 更新幽灵
        blinky_pos = self.blinky.get_grid_pos() if self.blinky else None
        pac_pos = self.pacman.get_grid_pos()
        pac_dir = self.pacman.direction
        for ghost in self.ghosts:
            ghost.update(self.walls, self.ghost_door, pac_pos, pac_dir, blinky_pos)

        # 检查豆子碰撞
        self.check_dot_collision()

        # 检查幽灵碰撞
        if self.check_ghost_collision():
            self.lives -= 1
            self.death_animation()

        # 检查胜利
        if self.check_win():
            self.state = WIN
            self.win_timer = 180

    def draw_maze(self, screen):
        """绘制迷宫"""
        # 画墙
        for wx, wy in self.walls:
            rect = pygame.Rect(wx * TILE_SIZE, wy * TILE_SIZE + SCORE_HEIGHT,
                              TILE_SIZE, TILE_SIZE)
            # 粗边框风格墙壁
            pygame.draw.rect(screen, BLUE, rect, 2)
            # 内部填充
            inner_rect = rect.inflate(-4, -4)
            pygame.draw.rect(screen, DARK_BLUE, inner_rect)

        # 画门（幽灵门）
        for dx, dy in self.ghost_door:
            rect = pygame.Rect(dx * TILE_SIZE, dy * TILE_SIZE + SCORE_HEIGHT,
                              TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, PINK, rect)

        # 画豆子
        for dx, dy in self.dots:
            cx = dx * TILE_SIZE + TILE_SIZE // 2
            cy = dy * TILE_SIZE + SCORE_HEIGHT + TILE_SIZE // 2
            pygame.draw.circle(screen, WHITE, (cx, cy), 2)

        # 画大力豆
        for dx, dy in self.power_dots:
            cx = dx * TILE_SIZE + TILE_SIZE // 2
            cy = dy * TILE_SIZE + SCORE_HEIGHT + TILE_SIZE // 2
            pulse = 2 + int(math.sin(pygame.time.get_ticks() * 0.005) * 2)
            pygame.draw.circle(screen, WHITE, (cx, cy), 4 + pulse // 2)

    def draw_ui(self, screen):
        """绘制UI"""
        # 分数
        score_text = self.font.render(f"SCORE: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        # 生命数
        lives_text = self.font.render(f"LIVES: {self.lives}", True, YELLOW)
        screen.blit(lives_text, (SCREEN_WIDTH - 120, 10))

        # 关卡
        level_text = self.font.render(f"LEVEL {self.level}", True, WHITE)
        screen.blit(level_text, (SCREEN_WIDTH // 2 - 40, 10))

        # READY / GAME OVER / WIN
        if self.state == READY and self.ready_timer > 30:
            text = self.font.render("READY!", True, YELLOW)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + SCORE_HEIGHT))
            screen.blit(text, text_rect)
        elif self.state == GAME_OVER:
            text = self.big_font.render("GAME OVER", True, RED)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + SCORE_HEIGHT - 20))
            screen.blit(text, text_rect)
            restart = self.font.render("Press R to Restart", True, WHITE)
            restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + SCORE_HEIGHT + 20))
            screen.blit(restart, restart_rect)
        elif self.state == WIN:
            text = self.big_font.render("YOU WIN!", True, YELLOW)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + SCORE_HEIGHT - 20))
            screen.blit(text, text_rect)
            score = self.font.render(f"FINAL SCORE: {self.score}", True, WHITE)
            score_rect = score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + SCORE_HEIGHT + 10))
            screen.blit(score, score_rect)
            restart = self.font.render("Press R to Restart", True, WHITE)
            restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + SCORE_HEIGHT + 40))
            screen.blit(restart, restart_rect)

    def draw(self):
        """绘制所有内容"""
        self.screen.fill(BLACK)

        # 画迷宫
        self.draw_maze(self.screen)

        # 画豆子计数
        remaining = len(self.dots) + len(self.power_dots)
        if remaining > 0:
            progress = 1 - remaining / TOTAL_DOTS
            bar_width = 100
            bar_x = SCREEN_WIDTH // 2 - bar_width // 2
            bar_y = SCREEN_HEIGHT + SCORE_HEIGHT + 5
            pygame.draw.rect(self.screen, GREY, (bar_x, bar_y, bar_width, 5))
            pygame.draw.rect(self.screen, YELLOW,
                            (bar_x, bar_y, int(bar_width * progress), 5))

        # 画吃豆人
        if not self.death_animating:
            self.pacman.draw(self.screen)
        else:
            # 死亡动画 - 缩小吃豆人
            alpha = max(0, 1 - self.death_animation_timer / 60)
            if alpha > 0:
                pygame.draw.circle(self.screen, YELLOW,
                                  (int(self.pacman.pixel_pos[0]),
                                   int(self.pacman.pixel_pos[1])),
                                  int((TILE_SIZE // 2 - 2) * alpha))

        # 画幽灵
        for ghost in self.ghosts:
            ghost.draw(self.screen)

        # 画UI
        self.draw_ui(self.screen)

        pygame.display.flip()

    def run(self):
        """主循环"""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ==================== 程序入口 ====================
if __name__ == "__main__":
    print("Pacman 吃豆人 - 按方向键开始游戏")
    print("方向键移动 | R键重新开始 | ESC退出")
    game = Game()
    game.run()