"""
Pipe Puzzle (接水管) - 经典管道连接益智游戏
===========================================
玩法：旋转管道碎片，连接水源到出水口，让水顺利流过所有管道！
- 点击管道碎片旋转(90度)
- 连接所有管道形成完整路径
- 水会沿着连通路径流动
- 关卡逐步升级，难度递增

Author: AI Game Developer
Date: 2026-07-31
"""

import pygame
import random
import sys
import math
from collections import deque

# ==================== 初始化 ====================
pygame.init()
pygame.display.set_caption("Pipe Puzzle - 接水管")

# ==================== 常量 ====================
# 屏幕尺寸
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 680
FPS = 60

# 颜色
COLORS = {
    'bg': (18, 18, 32),
    'panel': (25, 25, 50),
    'grid_bg': (30, 30, 55),
    'grid_line': (40, 40, 70),
    'pipe': (60, 120, 200),
    'pipe_hover': (80, 150, 230),
    'pipe_connected': (50, 200, 100),
    'pipe_water': (0, 180, 255),
    'water_flow': (0, 220, 255),
    'source': (255, 200, 50),
    'drain': (255, 100, 100),
    'text': (220, 220, 240),
    'text_dim': (140, 140, 160),
    'accent': (255, 180, 50),
    'success': (50, 255, 100),
    'fail': (255, 80, 80),
    'button': (60, 60, 100),
    'button_hover': (80, 80, 130),
    'star': (255, 215, 0),
    'shadow': (10, 10, 20),
    'level_bg': (35, 35, 65),
    'progress': (50, 200, 100),
}

# 管道类型
PIPE_EMPTY = 0
PIPE_STRAIGHT = 1  # 直线管 ─ │
PIPE_CORNER = 2    # 弯管 └ ┘ ┐ ┌
PIPE_TEE = 3       # T型管 ┴ ┬ ├ ┤
PIPE_CROSS = 4     # 十字管 ┼

# 方向
DIR_UP = 0
DIR_RIGHT = 1
DIR_DOWN = 2
DIR_LEFT = 3
DIRS = [DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT]
DIR_OFFSETS = [(0, -1), (1, 0), (0, 1), (-1, 0)]
DIR_NAMES = ['↑', '→', '↓', '←']

# 管道连接定义: 每种管道的连接方向 (相对方向)
PIPE_CONNECTIONS = {
    PIPE_EMPTY: [],
    PIPE_STRAIGHT: [
        [DIR_UP, DIR_DOWN],      # 旋转0: 上下
        [DIR_RIGHT, DIR_LEFT],   # 旋转1: 左右
        [DIR_UP, DIR_DOWN],      # 旋转2: 上下 (同0)
        [DIR_RIGHT, DIR_LEFT],   # 旋转3: 左右 (同1)
    ],
    PIPE_CORNER: [
        [DIR_UP, DIR_RIGHT],     # 旋转0: └ (上右)
        [DIR_RIGHT, DIR_DOWN],   # 旋转1: ┌ (右下)
        [DIR_DOWN, DIR_LEFT],    # 旋转2: ┐ (下左)
        [DIR_LEFT, DIR_UP],      # 旋转3: ┘ (左上)
    ],
    PIPE_TEE: [
        [DIR_UP, DIR_RIGHT, DIR_DOWN],      # 旋转0: ┴ (上右下)
        [DIR_RIGHT, DIR_DOWN, DIR_LEFT],    # 旋转1: ├ (右下左)
        [DIR_DOWN, DIR_LEFT, DIR_UP],       # 旋转2: ┤ (下左上)
        [DIR_LEFT, DIR_UP, DIR_RIGHT],      # 旋转3: ┬ (左上右)
    ],
    PIPE_CROSS: [
        [DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT],  # 旋转0: ┼
        [DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT],  # 旋转1: ┼
        [DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT],  # 旋转2: ┼
        [DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT],  # 旋转3: ┼
    ],
}

# 绘制管道用的点集 (归一化, 中心在0,0, 范围[-1,1])
# 每个管道用多个线段或曲线表示


def get_pipe_shape(pipe_type, rotation, cell_size):
    """获取管道形状的顶点列表"""
    hw = cell_size // 2  # 半宽
    gap = cell_size // 6  # 管道壁厚/2
    cx, cy = 0, 0

    # 内径和外径
    inner = gap
    outer = hw - 2

    shapes = []
    connections = PIPE_CONNECTIONS[pipe_type][rotation]

    # 十字管特殊处理 - 中心方块
    if pipe_type == PIPE_CROSS:
        shapes.append([
            (-inner, -inner), (inner, -inner),
            (inner, inner), (-inner, inner)
        ])

    # 为每个连接方向画一个矩形
    for dir_idx in connections:
        dx, dy = DIR_OFFSETS[dir_idx]
        if dx == 0:  # 上下
            y1 = -inner if dy < 0 else inner
            y2 = -outer if dy < 0 else outer
            shapes.append([
                (-inner, y1), (inner, y1),
                (inner, y2), (-inner, y2)
            ])
        else:  # 左右
            x1 = -inner if dx < 0 else inner
            x2 = -outer if dx < 0 else outer
            shapes.append([
                (x1, -inner), (x2, -inner),
                (x2, inner), (x1, inner)
            ])

    # T型管/T型管/弯管 中心填充
    if pipe_type == PIPE_TEE or pipe_type == PIPE_CORNER:
        shapes.append([
            (-inner, -inner), (inner, -inner),
            (inner, inner), (-inner, inner)
        ])

    return shapes


# ==================== 关卡配置 ====================
LEVELS = [
    # (grid_size, num_pipes, time_limit_sec)
    (4, 4, 120),   # 第1关
    (4, 5, 110),   # 第2关
    (5, 6, 120),   # 第3关
    (5, 7, 110),   # 第4关
    (6, 8, 120),   # 第5关
    (6, 9, 110),   # 第6关
    (7, 10, 120),  # 第7关
    (7, 11, 110),  # 第8关
    (8, 12, 120),  # 第9关
    (8, 14, 110),  # 第10关
]


# ==================== 游戏类 ====================
class PipePuzzle:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        self.font_tiny = pygame.font.Font(None, 24)

        self.running = True
        self.state = 'menu'  # menu, playing, won, lost, level_clear
        self.current_level = 0
        self.score = 0
        self.total_score = 0
        self.animating = False
        self.animation_timer = 0
        self.water_particles = []
        self.water_complete = False
        self.flash_timer = 0

        # 网格偏移 (居中)
        self.grid_offset_x = 0
        self.grid_offset_y = 80

        self.init_level()

    def init_level(self):
        """初始化当前关卡"""
        level_idx = min(self.current_level, len(LEVELS) - 1)
        grid_size, num_pipes, time_limit = LEVELS[level_idx]

        self.grid_size = grid_size
        self.cell_size = min(
            (SCREEN_WIDTH - 160) // grid_size,
            (SCREEN_HEIGHT - 160) // grid_size
        )
        self.cell_size = max(self.cell_size, 40)
        self.cell_size = min(self.cell_size, 80)

        self.grid_offset_x = (SCREEN_WIDTH - grid_size * self.cell_size) // 2
        self.grid_offset_y = 100

        self.time_limit = time_limit
        self.time_remaining = time_limit
        self.timer_active = False

        # 生成网格
        self.grid = [[PIPE_EMPTY for _ in range(grid_size)] for _ in range(grid_size)]
        self.rotations = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
        self.connected = [[False for _ in range(grid_size)] for _ in range(grid_size)]
        self.hover_cell = None
        self.click_cooldown = 0

        # 生成管道
        self._generate_pipes(num_pipes)

        # 水源和出水口
        self.source_pos = None
        self.drain_pos = None
        self._place_source_drain()

        # 水流动画
        self.water_path = []
        self.water_progress = 0
        self.water_flowing = False
        self.water_segments = []

        # 检查初始状态
        self.check_connections()

    def _generate_pipes(self, num_pipes):
        """在网格中随机放置管道"""
        grid_size = self.grid_size
        cells = [(r, c) for r in range(grid_size) for c in range(grid_size)]
        random.shuffle(cells)

        # 要放置的管道类型分布
        pipe_types = [PIPE_STRAIGHT] * (num_pipes // 3)
        pipe_types += [PIPE_CORNER] * (num_pipes // 3)
        pipe_types += [PIPE_TEE] * max(1, num_pipes - 2 * (num_pipes // 3))
        # 偶尔加一个十字管
        if random.random() < 0.15 and num_pipes > 6:
            pipe_types[-1] = PIPE_CROSS

        random.shuffle(pipe_types)

        for i in range(min(num_pipes, len(cells))):
            r, c = cells[i]
            if i < len(pipe_types):
                self.grid[r][c] = pipe_types[i]
            else:
                self.grid[r][c] = random.choice([PIPE_STRAIGHT, PIPE_CORNER, PIPE_TEE])
            self.rotations[r][c] = random.randint(0, 3)

    def _place_source_drain(self):
        """放置水源和出水口"""
        grid_size = self.grid_size
        # 找有管道的单元格
        pipe_cells = [(r, c) for r in range(grid_size) for c in range(grid_size) if self.grid[r][c] != PIPE_EMPTY]

        if len(pipe_cells) < 2:
            return

        # 水源在左上方区域，出水口在右下方区域
        src_candidates = [p for p in pipe_cells if p[0] + p[1] < grid_size]
        dst_candidates = [p for p in pipe_cells if p[0] + p[1] >= grid_size and p != src_candidates[0]]

        if not src_candidates or not dst_candidates:
            self.source_pos = pipe_cells[0]
            self.drain_pos = pipe_cells[-1]
        else:
            self.source_pos = random.choice(src_candidates)
            self.drain_pos = random.choice(dst_candidates)

    def check_connections(self):
        """检查所有管道的连接状态，从水源出发进行BFS"""
        grid_size = self.grid_size
        self.connected = [[False for _ in range(grid_size)] for _ in range(grid_size)]

        if not self.source_pos:
            return

        sr, sc = self.source_pos
        queue = deque()
        queue.append((sr, sc))
        self.connected[sr][sc] = True

        visited = set()
        visited.add((sr, sc))

        while queue:
            r, c = queue.popleft()
            pipe_type = self.grid[r][c]
            if pipe_type == PIPE_EMPTY:
                continue
            rotation = self.rotations[r][c]
            connections = PIPE_CONNECTIONS[pipe_type][rotation]

            for dir_idx in connections:
                dr, dc = DIR_OFFSETS[dir_idx]
                nr, nc = r + dr, c + dc
                if 0 <= nr < grid_size and 0 <= nc < grid_size and (nr, nc) not in visited:
                    if self.grid[nr][nc] != PIPE_EMPTY:
                        # 检查对面是否连接过来
                        opp_dir = (dir_idx + 2) % 4
                        n_rot = self.rotations[nr][nc]
                        n_conns = PIPE_CONNECTIONS[self.grid[nr][nc]][n_rot]
                        if opp_dir in n_conns:
                            self.connected[nr][nc] = True
                            visited.add((nr, nc))
                            queue.append((nr, nc))

    def is_solved(self):
        """检查是否所有管道都连通了"""
        if not self.source_pos or not self.drain_pos:
            return False
        if not self.connected:
            return False
        # 检查水源到出水口是否连通
        sr, sc = self.source_pos
        dr, dc = self.drain_pos
        if not self.connected[sr][sc] or not self.connected[dr][dc]:
            return False

        # 检查所有管道是否都连通
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.grid[r][c] != PIPE_EMPTY and not self.connected[r][c]:
                    return False
        return True

    def rotate_pipe(self, r, c):
        """旋转管道"""
        if self.grid[r][c] == PIPE_EMPTY:
            return
        if self.water_flowing:
            return
        self.rotations[r][c] = (self.rotations[r][c] + 1) % 4
        self.check_connections()
        self.click_cooldown = 10

        # 检查是否通关
        if self.is_solved():
            self.start_water_flow()

    def start_water_flow(self):
        """开始水流动画"""
        self.water_flowing = True
        self.water_progress = 0
        self.water_path = []
        self.water_segments = []

        # 从水源到出水口找路径
        if not self.source_pos:
            return

        sr, sc = self.source_pos
        dr, dc = self.drain_pos

        # BFS找路径
        visited = set()
        parent = {}
        queue = deque()
        queue.append((sr, sc))
        visited.add((sr, sc))

        found = False
        while queue and not found:
            r, c = queue.popleft()
            if (r, c) == (dr, dc):
                found = True
                break
            pipe_type = self.grid[r][c]
            if pipe_type == PIPE_EMPTY:
                continue
            rotation = self.rotations[r][c]
            connections = PIPE_CONNECTIONS[pipe_type][rotation]
            for dir_idx in connections:
                nr, nc = r + DIR_OFFSETS[dir_idx][0], c + DIR_OFFSETS[dir_idx][1]
                if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size and (nr, nc) not in visited:
                    if self.grid[nr][nc] != PIPE_EMPTY and self.connected[nr][nc]:
                        visited.add((nr, nc))
                        parent[(nr, nc)] = (r, c)
                        queue.append((nr, nc))

        if found:
            # 重建路径
            curr = (dr, dc)
            path = []
            while curr != (sr, sc):
                path.append(curr)
                curr = parent[curr]
            path.append((sr, sc))
            path.reverse()
            self.water_path = path

            # 生成水段
            for i in range(len(path)):
                self.water_segments.append({
                    'pos': path[i],
                    'progress': i / max(1, len(path) - 1),
                    'alpha': 0,
                })

    def update(self):
        """更新游戏状态"""
        if self.click_cooldown > 0:
            self.click_cooldown -= 1

        if self.state == 'playing':
            if self.timer_active and not self.water_flowing:
                self.time_remaining -= 1 / FPS
                if self.time_remaining <= 0:
                    self.time_remaining = 0
                    self.state = 'lost'

        # 水流动画
        if self.water_flowing:
            self.water_progress += 0.015
            if self.water_progress >= 1.0:
                self.water_flowing = False
                self.water_complete = True
                # 计算分数
                time_bonus = int(self.time_remaining * 10)
                level_bonus = (self.current_level + 1) * 100
                self.score = time_bonus + level_bonus
                self.total_score += self.score
                self.state = 'level_clear'

            # 更新水段显示
            for seg in self.water_segments:
                if seg['progress'] <= self.water_progress:
                    seg['alpha'] = min(255, seg['alpha'] + 15)

        # 闪烁效果
        if self.water_complete:
            self.flash_timer += 1

    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(COLORS['bg'])

        if self.state == 'menu':
            self._draw_menu()
        elif self.state == 'playing':
            self._draw_game()
            if self.water_flowing:
                self._draw_water_effect()
        elif self.state == 'level_clear':
            self._draw_game()
            self._draw_water_effect()
            self._draw_level_clear()
        elif self.state == 'won':
            self._draw_win()
        elif self.state == 'lost':
            self._draw_game()
            self._draw_lost()

        pygame.display.flip()

    def _draw_menu(self):
        """绘制主菜单"""
        # 标题
        title = self.font_large.render("🚰 Pipe Puzzle", True, COLORS['accent'])
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, title_rect)

        subtitle = self.font_medium.render("接水管 - 旋转管道，连通水源！", True, COLORS['text'])
        sub_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(subtitle, sub_rect)

        # 操作说明
        instructions = [
            "🖱 点击管道碎片旋转 90°",
            "💧 连通所有管道让水流过",
            "⏱ 时间越短，分数越高！",
        ]
        for i, text in enumerate(instructions):
            inst = self.font_small.render(text, True, COLORS['text_dim'])
            inst_rect = inst.get_rect(center=(SCREEN_WIDTH // 2, 300 + i * 40))
            self.screen.blit(inst, inst_rect)

        # 开始按钮
        self._draw_button(SCREEN_WIDTH // 2 - 100, 450, 200, 55,
                          "开始游戏", COLORS['button'], COLORS['button_hover'],
                          self.state == 'menu')

        # 总分数
        if self.total_score > 0:
            score_text = self.font_small.render(f"总分: {self.total_score}", True, COLORS['text_dim'])
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 550))
            self.screen.blit(score_text, score_rect)

    def _draw_game(self):
        """绘制游戏主界面"""
        # 顶部信息栏
        level_text = self.font_medium.render(f"第 {self.current_level + 1} 关", True, COLORS['accent'])
        self.screen.blit(level_text, (20, 20))

        score_text = self.font_small.render(f"总分: {self.total_score}", True, COLORS['text'])
        self.screen.blit(score_text, (20, 60))

        # 计时器
        time_color = COLORS['fail'] if self.time_remaining < 20 else COLORS['text']
        minutes = int(self.time_remaining) // 60
        seconds = int(self.time_remaining) % 60
        timer_text = self.font_small.render(f"⏱ {minutes:02d}:{seconds:02d}", True, time_color)
        timer_rect = timer_text.get_rect(topright=(SCREEN_WIDTH - 20, 30))
        self.screen.blit(timer_text, timer_rect)

        # 进度条
        progress = 1.0 - (self.time_remaining / self.time_limit)
        bar_width = 150
        bar_height = 8
        bar_x = SCREEN_WIDTH - 20 - bar_width
        bar_y = 55
        pygame.draw.rect(self.screen, COLORS['grid_bg'], (bar_x, bar_y, bar_width, bar_height), border_radius=4)
        if progress > 0:
            fill_color = COLORS['fail'] if progress > 0.7 else COLORS['progress']
            pygame.draw.rect(self.screen, fill_color,
                             (bar_x, bar_y, int(bar_width * progress), bar_height), border_radius=4)

        # 提示文字
        hint = self.font_tiny.render("点击管道旋转 ↻", True, COLORS['text_dim'])
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 80))

        # 绘制网格
        grid_px = self.grid_size * self.cell_size
        grid_x = self.grid_offset_x
        grid_y = self.grid_offset_y

        # 网格背景
        pygame.draw.rect(self.screen, COLORS['grid_bg'],
                         (grid_x - 4, grid_y - 4, grid_px + 8, grid_px + 8),
                         border_radius=8)

        for r in range(self.grid_size):
            for c in range(self.grid_size):
                x = grid_x + c * self.cell_size
                y = grid_y + r * self.cell_size
                rect = pygame.Rect(x, y, self.cell_size, self.cell_size)

                # 单元格背景
                cell_color = COLORS['grid_bg']
                if self.hover_cell == (r, c) and self.grid[r][c] != PIPE_EMPTY:
                    cell_color = (40, 40, 70)

                if self.grid[r][c] != PIPE_EMPTY:
                    pygame.draw.rect(self.screen, cell_color, rect)
                    pygame.draw.rect(self.screen, COLORS['grid_line'], rect, 1)

                    # 绘制管道
                    self._draw_pipe(r, c, x, y)

                    # 连通高亮
                    if self.connected[r][c] and not self.water_flowing:
                        glow = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                        glow.fill((50, 200, 100, 30))
                        self.screen.blit(glow, (x, y))
                else:
                    pygame.draw.rect(self.screen, (22, 22, 40), rect)
                    pygame.draw.rect(self.screen, COLORS['grid_line'], rect, 1)

        # 水源和出水口标记
        self._draw_source_drain()

    def _draw_pipe(self, r, c, x, y):
        """绘制单个管道"""
        pipe_type = self.grid[r][c]
        if pipe_type == PIPE_EMPTY:
            return

        rotation = self.rotations[r][c]
        cx, cy = x + self.cell_size // 2, y + self.cell_size // 2
        shapes = get_pipe_shape(pipe_type, rotation, self.cell_size)

        # 管道颜色
        if self.connected[r][c]:
            if self.water_flowing:
                # 根据水流进度决定颜色
                seg_progress = 0
                for seg in self.water_segments:
                    if seg['pos'] == (r, c):
                        seg_progress = seg['progress']
                        break
                if seg_progress <= self.water_progress:
                    pipe_color = COLORS['pipe_water']
                else:
                    pipe_color = COLORS['pipe_connected']
            else:
                pipe_color = COLORS['pipe_connected']
        else:
            pipe_color = COLORS['pipe']

        # 绘制管道形状
        for shape in shapes:
            points = [(cx + v[0], cy + v[1]) for v in shape]
            if len(points) >= 3:
                pygame.draw.polygon(self.screen, pipe_color, points)
                # 边框
                pygame.draw.polygon(self.screen,
                                    (min(255, pipe_color[0] + 40),
                                     min(255, pipe_color[1] + 40),
                                     min(255, pipe_color[2] + 40)),
                                    points, 1)
            else:
                pygame.draw.line(self.screen, pipe_color, points[0], points[1], max(2, self.cell_size // 8))

    def _draw_source_drain(self):
        """绘制水源和出水口标记"""
        if self.source_pos:
            r, c = self.source_pos
            x = self.grid_offset_x + c * self.cell_size + self.cell_size // 2
            y = self.grid_offset_y + r * self.cell_size + self.cell_size // 2
            # 水源标记
            pygame.draw.circle(self.screen, COLORS['source'], (x, y), self.cell_size // 4, 3)
            label = self.font_tiny.render("水源", True, COLORS['source'])
            self.screen.blit(label, (x - label.get_width() // 2, y - self.cell_size // 2 - 20))

        if self.drain_pos:
            r, c = self.drain_pos
            x = self.grid_offset_x + c * self.cell_size + self.cell_size // 2
            y = self.grid_offset_y + r * self.cell_size + self.cell_size // 2
            # 出水口标记
            pygame.draw.circle(self.screen, COLORS['drain'], (x, y), self.cell_size // 4, 3)
            label = self.font_tiny.render("出口", True, COLORS['drain'])
            self.screen.blit(label, (x - label.get_width() // 2, y - self.cell_size // 2 - 20))

    def _draw_water_effect(self):
        """绘制水流效果"""
        if not self.water_path:
            return

        cell_size = self.cell_size
        grid_x = self.grid_offset_x
        grid_y = self.grid_offset_y

        for i, (r, c) in enumerate(self.water_path):
            seg_progress = i / max(1, len(self.water_path) - 1)
            if seg_progress <= self.water_progress:
                cx = grid_x + c * cell_size + cell_size // 2
                cy = grid_y + r * cell_size + cell_size // 2

                # 流水粒子
                alpha = int(255 * (1 - abs(seg_progress - self.water_progress) * 3))
                alpha = max(0, min(255, alpha))

                # 发光效果
                glow_size = cell_size // 2 + int(5 * math.sin(self.flash_timer * 0.1 + i))
                glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                glow_color = (0, 200, 255, alpha // 3)
                pygame.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
                self.screen.blit(glow_surf, (cx - glow_size, cy - glow_size), special_flags=pygame.BLEND_ALPHA_SDL2)

                # 水滴粒子
                if alpha > 50 and random.random() < 0.3:
                    px = cx + random.randint(-cell_size // 3, cell_size // 3)
                    py = cy + random.randint(-cell_size // 3, cell_size // 3)
                    particle_size = random.randint(2, 4)
                    particle_alpha = alpha // 2
                    p_surf = pygame.Surface((particle_size * 2, particle_size * 2), pygame.SRCALPHA)
                    p_color = (0, 220, 255, particle_alpha)
                    pygame.draw.circle(p_surf, p_color, (particle_size, particle_size), particle_size)
                    self.screen.blit(p_surf, (px - particle_size, py - particle_size),
                                     special_flags=pygame.BLEND_ALPHA_SDL2)

    def _draw_level_clear(self):
        """绘制过关界面"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # 过关文字
        clear_text = self.font_large.render("🎉 关卡通过！", True, COLORS['success'])
        clear_rect = clear_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(clear_text, clear_rect)

        # 分数
        score_text = self.font_medium.render(f"本关得分: {self.score}", True, COLORS['accent'])
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 280))
        self.screen.blit(score_text, score_rect)

        total_text = self.font_small.render(f"总分: {self.total_score}", True, COLORS['text'])
        total_rect = total_text.get_rect(center=(SCREEN_WIDTH // 2, 330))
        self.screen.blit(total_text, total_rect)

        # 星级评定
        if self.score > 500:
            stars = "⭐⭐⭐"
        elif self.score > 300:
            stars = "⭐⭐"
        else:
            stars = "⭐"
        star_text = self.font_medium.render(stars, True, COLORS['star'])
        star_rect = star_text.get_rect(center=(SCREEN_WIDTH // 2, 380))
        self.screen.blit(star_text, star_rect)

        # 下一关按钮
        if self.current_level < len(LEVELS) - 1:
            self._draw_button(SCREEN_WIDTH // 2 - 100, 430, 200, 50,
                              "下一关 ▶", COLORS['button'], COLORS['button_hover'],
                              self.state == 'level_clear')
        else:
            self._draw_button(SCREEN_WIDTH // 2 - 100, 430, 200, 50,
                              "🏆 通关!", COLORS['accent'], (255, 200, 80),
                              self.state == 'level_clear')

    def _draw_win(self):
        """绘制通关画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        win_text = self.font_large.render("🏆 恭喜通关！🏆", True, COLORS['accent'])
        win_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(win_text, win_rect)

        score_text = self.font_medium.render(f"总分: {self.total_score}", True, COLORS['text'])
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 280))
        self.screen.blit(score_text, score_rect)

        self._draw_button(SCREEN_WIDTH // 2 - 100, 380, 200, 50,
                          "再来一次", COLORS['button'], COLORS['button_hover'],
                          self.state == 'won')

    def _draw_lost(self):
        """绘制失败画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        lost_text = self.font_large.render("⏰ 时间到！", True, COLORS['fail'])
        lost_rect = lost_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(lost_text, lost_rect)

        hint_text = self.font_small.render("再试一次，连通所有管道！", True, COLORS['text_dim'])
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, 270))
        self.screen.blit(hint_text, hint_rect)

        self._draw_button(SCREEN_WIDTH // 2 - 100, 340, 200, 50,
                          "重新开始", COLORS['button'], COLORS['button_hover'],
                          self.state == 'lost')

    def _draw_button(self, x, y, w, h, text, color, hover_color, active):
        """绘制按钮"""
        mouse_pos = pygame.mouse.get_pos()
        rect = pygame.Rect(x, y, w, h)
        is_hover = rect.collidepoint(mouse_pos)

        btn_color = hover_color if is_hover else color
        pygame.draw.rect(self.screen, btn_color, rect, border_radius=10)
        pygame.draw.rect(self.screen, COLORS['text_dim'], rect, 2, border_radius=10)

        btn_text = self.font_small.render(text, True, COLORS['text'])
        text_rect = btn_text.get_rect(center=rect.center)
        self.screen.blit(btn_text, text_rect)

    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.QUIT:
            self.running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()

            if self.state == 'menu':
                # 开始按钮
                btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 450, 200, 55)
                if btn_rect.collidepoint(pos):
                    self.state = 'playing'
                    self.timer_active = True
                    self.current_level = 0
                    self.total_score = 0
                    self.init_level()

            elif self.state == 'playing' and not self.water_flowing:
                # 检查点击网格
                if self.click_cooldown <= 0:
                    r, c = self._get_cell_from_pos(pos)
                    if r is not None and 0 <= r < self.grid_size and 0 <= c < self.grid_size:
                        self.rotate_pipe(r, c)

            elif self.state == 'level_clear':
                if self.current_level < len(LEVELS) - 1:
                    btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 430, 200, 50)
                    if btn_rect.collidepoint(pos):
                        self.current_level += 1
                        self.water_flowing = False
                        self.water_complete = False
                        self.water_path = []
                        self.water_segments = []
                        self.flash_timer = 0
                        self.init_level()
                        self.state = 'playing'
                        self.timer_active = True
                else:
                    btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 430, 200, 50)
                    if btn_rect.collidepoint(pos):
                        self.state = 'won'

            elif self.state == 'won':
                btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 380, 200, 50)
                if btn_rect.collidepoint(pos):
                    self.state = 'menu'

            elif self.state == 'lost':
                btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 340, 200, 50)
                if btn_rect.collidepoint(pos):
                    self.water_flowing = False
                    self.water_complete = False
                    self.water_path = []
                    self.water_segments = []
                    self.flash_timer = 0
                    self.init_level()
                    self.state = 'playing'
                    self.timer_active = True

        if event.type == pygame.MOUSEMOTION:
            if self.state == 'playing':
                self.hover_cell = self._get_cell_from_pos(event.pos)

    def _get_cell_from_pos(self, pos):
        """从屏幕坐标获取网格坐标"""
        mx, my = pos
        grid_x = self.grid_offset_x
        grid_y = self.grid_offset_y

        c = (mx - grid_x) // self.cell_size
        r = (my - grid_y) // self.cell_size

        if 0 <= r < self.grid_size and 0 <= c < self.grid_size:
            cell_x = grid_x + c * self.cell_size
            cell_y = grid_y + r * self.cell_size
            if cell_x <= mx < cell_x + self.cell_size and cell_y <= my < cell_y + self.cell_size:
                return r, c
        return None, None

    def run(self):
        """主循环"""
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)

            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ==================== 入口 ====================
if __name__ == "__main__":
    game = PipePuzzle()
    game.run()