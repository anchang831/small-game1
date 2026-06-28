"""
连连看 (LinkUp) - Classic Tile-Matching Puzzle Game
====================================================
技术栈: Python + Pygame 2.6.1
玩法: 点击两个相同图标的方块，如果它们之间的连线路径最多拐2个弯，
      且路径上无阻挡，则消除。清空所有方块即获胜。

Controls:
  - 鼠标左键点击选择方块
  - H 键提示
  - S 键重新洗牌
  - R 键重新开始
  - ESC 退出
"""

import pygame
import random
import math
import sys
from collections import deque

# ===================== 游戏配置 =====================
COLS = 12          # 列数 (偶数, 保证每对出现)
ROWS = 10          # 行数
TILE_SIZE = 50     # 每个方块的像素大小
MARGIN = 4         # 方块间距
BORDER = 30        # 边框宽度
TOP_BAR = 80       # 顶部信息栏高度

# 窗口尺寸
WIN_WIDTH = COLS * (TILE_SIZE + MARGIN) + MARGIN + BORDER * 2
WIN_HEIGHT = ROWS * (TILE_SIZE + MARGIN) + MARGIN + BORDER * 2 + TOP_BAR

# 颜色
COLORS = {
    'bg': (30, 30, 50),
    'panel': (20, 20, 35),
    'border': (100, 100, 150),
    'tile_bg': (240, 240, 255),
    'selected': (255, 255, 0),
    'hint': (0, 255, 100),
    'path': (255, 200, 50),
    'text': (255, 255, 255),
    'text_dim': (180, 180, 200),
    'button': (60, 60, 120),
    'button_hover': (80, 80, 160),
    'win': (50, 200, 100),
}

# 方块类型 — 不同的图标形状和颜色
TILE_TYPES = [
    {'shape': 'circle',     'color': (255, 80, 80),   'label': '●'},
    {'shape': 'square',     'color': (80, 150, 255),  'label': '■'},
    {'shape': 'diamond',    'color': (255, 200, 50),  'label': '◆'},
    {'shape': 'triangle',   'color': (80, 255, 80),   'label': '▲'},
    {'shape': 'cross',      'color': (200, 100, 255), 'label': '✚'},
    {'shape': 'star',       'color': (255, 180, 50),  'label': '★'},
    {'shape': 'heart',      'color': (255, 50, 150),  'label': '♥'},
    {'shape': 'hexagon',    'color': (50, 200, 200),  'label': '⬡'},
    {'shape': 'moon',       'color': (200, 200, 80),  'label': '☽'},
    {'shape': 'clover',     'color': (100, 220, 100), 'label': '♣'},
    {'shape': 'spade',      'color': (150, 150, 255), 'label': '♠'},
    {'shape': 'diamond2',   'color': (255, 130, 200), 'label': '◇'},
]

# 需要配对的数量 = ROWS * COLS / 2
NUM_PAIRS = (ROWS * COLS) // 2

FPS = 60


class LinkGame:
    """连连看游戏主类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        pygame.display.set_caption("连连看 LinkUp")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        self.font_big = pygame.font.Font(None, 60)

        # 计算网格的起始偏移 (居中)
        grid_w = COLS * (TILE_SIZE + MARGIN) + MARGIN
        grid_h = ROWS * (TILE_SIZE + MARGIN) + MARGIN
        self.offset_x = (WIN_WIDTH - grid_w) // 2
        self.offset_y = TOP_BAR + (WIN_HEIGHT - TOP_BAR - grid_h) // 2

        # 游戏状态
        self.reset_game()

    def reset_game(self):
        """初始化/重置游戏"""
        self.grid = self._generate_grid()
        self.selected = None          # 当前选中的方块 (row, col)
        self.hint_pair = None         # 提示的方块对
        self.path_line = []           # 消除路径动画
        self.path_timer = 0           # 路径显示计时器
        self.score = 0
        self.moves = 0
        self.time = 0
        self.game_over = False
        self.won = False
        self.shuffle_count = 0
        self.message = ""
        self.message_timer = 0

        # 确保初始局面有解
        if not self._has_valid_moves():
            self._shuffle_grid()

    def _generate_grid(self):
        """生成配对排列的网格数据"""
        # 创建配对列表
        pairs = []
        tiles_per_type = max(1, NUM_PAIRS // len(TILE_TYPES)) + 1
        tile_pool = []
        for i in range(min(NUM_PAIRS, len(TILE_TYPES) * tiles_per_type)):
            tile_pool.append(i % len(TILE_TYPES))

        # 确保是偶数个
        if NUM_PAIRS > len(tile_pool):
            extra = NUM_PAIRS - len(tile_pool)
            tile_pool.extend([i % len(TILE_TYPES) for i in range(extra)])

        tile_pool = tile_pool[:NUM_PAIRS]

        # 每个类型出现两次
        tiles = []
        for t in tile_pool:
            tiles.append(t)
            tiles.append(t)

        random.shuffle(tiles)

        # 填入网格
        grid = [[-1 for _ in range(COLS)] for _ in range(ROWS)]
        idx = 0
        for r in range(ROWS):
            for c in range(COLS):
                grid[r][c] = tiles[idx]
                idx += 1
        return grid

    def _get_tile_rect(self, row, col):
        """获取某个方块在屏幕上的矩形区域"""
        x = self.offset_x + col * (TILE_SIZE + MARGIN) + MARGIN
        y = self.offset_y + row * (TILE_SIZE + MARGIN) + MARGIN
        return pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

    def _get_grid_pos(self, px, py):
        """将屏幕坐标转换为网格坐标, 不在方块内返回None"""
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] != -1:
                    rect = self._get_tile_rect(r, c)
                    if rect.collidepoint(px, py):
                        return r, c
        return None

    def _draw_tile(self, row, col, highlight=None):
        """绘制单个方块"""
        tile_type = self.grid[row][col]
        if tile_type == -1:
            return

        info = TILE_TYPES[tile_type % len(TILE_TYPES)]
        rect = self._get_tile_rect(row, col)
        color = info['color']
        shape = info['shape']

        # 背景
        bg = COLORS['tile_bg']
        if highlight == 'selected':
            bg = COLORS['selected']
        elif highlight == 'hint':
            bg = COLORS['hint']

        # 圆角矩形背景
        pygame.draw.rect(self.screen, bg, rect, border_radius=6)
        pygame.draw.rect(self.screen, color, rect, width=2, border_radius=6)

        # 绘制图形符号
        cx, cy = rect.center
        r = TILE_SIZE // 3

        # 根据形状绘制不同图标
        if shape == 'circle':
            pygame.draw.circle(self.screen, color, (cx, cy), r)
            pygame.draw.circle(self.screen, (255, 255, 255, 100), (cx - 3, cy - 3), r // 3)
        elif shape == 'square':
            sq_rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
            pygame.draw.rect(self.screen, color, sq_rect)
        elif shape == 'diamond':
            pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
            pygame.draw.polygon(self.screen, color, pts)
        elif shape == 'triangle':
            pts = [(cx, cy - r), (cx + r, cy + r), (cx - r, cy + r)]
            pygame.draw.polygon(self.screen, color, pts)
        elif shape == 'cross':
            w = r // 2
            pygame.draw.rect(self.screen, color, (cx - w, cy - r, w * 2, r * 2))
            pygame.draw.rect(self.screen, color, (cx - r, cy - w, r * 2, w * 2))
        elif shape == 'star':
            self._draw_star(self.screen, color, cx, cy, r)
        elif shape == 'heart':
            self._draw_heart(self.screen, color, cx, cy, r)
        elif shape == 'hexagon':
            pts = []
            for i in range(6):
                angle = math.pi / 3 * i - math.pi / 6
                pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
            pygame.draw.polygon(self.screen, color, pts)
        elif shape == 'moon':
            pygame.draw.circle(self.screen, color, (cx - 3, cy), r)
            pygame.draw.circle(self.screen, COLORS['tile_bg'], (cx + 3, cy), r)
            # 修复月亮背景
            pygame.draw.circle(self.screen, COLORS['tile_bg'] if highlight is None else bg,
                              (cx + 3, cy), r)
        elif shape == 'clover':
            for dx, dy in [(-r//2, -r//2), (r//2, -r//2), (-r//2, r//2), (r//2, r//2)]:
                pygame.draw.circle(self.screen, color, (cx + dx, cy + dy), r//2)
        elif shape == 'spade':
            pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r//3), (cx - r, cy)]
            pygame.draw.polygon(self.screen, color, pts)
            pygame.draw.rect(self.screen, color, (cx - r//4, cy, r//2, r//2))
        elif shape == 'diamond2':
            pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
            pygame.draw.polygon(self.screen, color, pts, width=3)

    def _draw_star(self, surface, color, cx, cy, r):
        """绘制五角星"""
        pts = []
        for i in range(10):
            angle = math.pi / 5 * i - math.pi / 2
            radius = r if i % 2 == 0 else r // 2
            pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        pygame.draw.polygon(surface, color, pts)

    def _draw_heart(self, surface, color, cx, cy, r):
        """绘制心形"""
        points = []
        for i in range(30):
            t = math.pi * 2 * i / 30
            x = 16 * math.sin(t) ** 3
            y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
            scale = r / 16
            points.append((cx + x * scale, cy - y * scale))
        pygame.draw.polygon(surface, color, points)

    def _is_empty(self, row, col):
        """判断某个位置是否为空(无方块或在边界外)"""
        if row < 0 or row >= ROWS or col < 0 or col >= COLS:
            return True  # 边界外视为空, 允许路径通过
        return self.grid[row][col] == -1

    def _check_line(self, r1, c1, r2, c2):
        """
        检查两点之间直线是否通畅 (0个拐弯)
        返回: (True, [path_points]) 或 (False, [])
        """
        if r1 == r2 and c1 == c2:
            return False, []

        if r1 == r2:
            # 水平方向检查
            step = 1 if c2 > c1 else -1
            for c in range(c1 + step, c2, step):
                if not self._is_empty(r1, c):
                    return False, []
            return True, [(r1, c1), (r1, c2)]

        if c1 == c2:
            # 垂直方向检查
            step = 1 if r2 > r1 else -1
            for r in range(r1 + step, r2, step):
                if not self._is_empty(r, c1):
                    return False, []
            return True, [(r1, c1), (r2, c1)]

        return False, []

    def _check_one_turn(self, r1, c1, r2, c2):
        """
        检查1个拐弯的连接
        拐点: (r1, c2) 或 (r2, c1)
        """
        # 拐点1: (r1, c2)
        if self._is_empty(r1, c2) or (r1 == r1 and c1 == c2) or (r2 == r1 and c2 == c2):
            valid1, _ = self._check_line(r1, c1, r1, c2)
            valid2, _ = self._check_line(r1, c2, r2, c2)
            if valid1 and valid2:
                return True, [(r1, c1), (r1, c2), (r2, c2)]

        # 拐点2: (r2, c1)
        if self._is_empty(r2, c1) or (r1 == r2 and c1 == c1) or (r2 == r2 and c1 == c2):
            valid1, _ = self._check_line(r1, c1, r2, c1)
            valid2, _ = self._check_line(r2, c1, r2, c2)
            if valid1 and valid2:
                return True, [(r1, c1), (r2, c1), (r2, c2)]

        return False, []

    def _check_two_turns(self, r1, c1, r2, c2):
        """
        检查2个拐弯的连接 (需要两个拐点)
        遍历所有可能的行和列作为中间转折
        """
        # 垂直扫描: 固定列c1和c2, 遍历行r
        for r in range(-1, ROWS + 1):
            if r == r1 or r == r2:
                continue
            # 检查 r1,c1 -> r,c1 -> r,c2 -> r2,c2
            if (self._is_empty(r, c1) or (r == r1 and c1 == c1)) and \
               (self._is_empty(r, c2) or (r == r2 and c2 == c2)):
                valid1, _ = self._check_line(r1, c1, r, c1)
                valid2, _ = self._check_line(r, c1, r, c2)
                valid3, _ = self._check_line(r, c2, r2, c2)
                if valid1 and valid2 and valid3:
                    return True, [(r1, c1), (r, c1), (r, c2), (r2, c2)]

        # 水平扫描: 固定行r1和r2, 遍历列c
        for c in range(-1, COLS + 1):
            if c == c1 or c == c2:
                continue
            # 检查 r1,c1 -> r1,c -> r2,c -> r2,c2
            if (self._is_empty(r1, c) or (r1 == r1 and c == c1)) and \
               (self._is_empty(r2, c) or (r2 == r2 and c == c2)):
                valid1, _ = self._check_line(r1, c1, r1, c)
                valid2, _ = self._check_line(r1, c, r2, c)
                valid3, _ = self._check_line(r2, c, r2, c2)
                if valid1 and valid2 and valid3:
                    return True, [(r1, c1), (r1, c), (r2, c), (r2, c2)]

        return False, []

    def _can_connect(self, r1, c1, r2, c2):
        """
        判断两个方块是否可以通过 ≤2 个拐弯连接
        返回: (True, path) 或 (False, [])
        """
        if r1 == r2 and c1 == c2:
            return False, []
        if self.grid[r1][c1] == -1 or self.grid[r2][c2] == -1:
            return False, []
        if self.grid[r1][c1] != self.grid[r2][c2]:
            return False, []

        # 0个拐弯
        ok, path = self._check_line(r1, c1, r2, c2)
        if ok:
            return True, path

        # 1个拐弯
        ok, path = self._check_one_turn(r1, c1, r2, c2)
        if ok:
            return True, path

        # 2个拐弯
        ok, path = self._check_two_turns(r1, c1, r2, c2)
        if ok:
            return True, path

        return False, []

    def _has_valid_moves(self):
        """检查当前局面是否有可消除的对"""
        tiles_pos = []
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] != -1:
                    tiles_pos.append((r, c, self.grid[r][c]))

        # 分组相同类型的方块
        from collections import defaultdict
        groups = defaultdict(list)
        for r, c, t in tiles_pos:
            groups[t].append((r, c))

        # 检查每组中是否有可连接的
        for t, positions in groups.items():
            for i in range(len(positions)):
                for j in range(i + 1, len(positions)):
                    ok, _ = self._can_connect(positions[i][0], positions[i][1],
                                              positions[j][0], positions[j][1])
                    if ok:
                        return True
        return False

    def _find_hint(self):
        """查找一对可消除的方块"""
        tiles_pos = []
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] != -1:
                    tiles_pos.append((r, c, self.grid[r][c]))

        from collections import defaultdict
        groups = defaultdict(list)
        for r, c, t in tiles_pos:
            groups[t].append((r, c))

        for t, positions in groups.items():
            for i in range(len(positions)):
                for j in range(i + 1, len(positions)):
                    ok, path = self._can_connect(positions[i][0], positions[i][1],
                                                  positions[j][0], positions[j][1])
                    if ok:
                        return (positions[i][0], positions[i][1],
                                positions[j][0], positions[j][1], path)
        return None

    def _shuffle_grid(self):
        """洗牌 — 重新排列剩余方块"""
        remaining = []
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] != -1:
                    remaining.append(self.grid[r][c])

        if len(remaining) == 0:
            return

        random.shuffle(remaining)
        idx = 0
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] != -1:
                    self.grid[r][c] = remaining[idx]
                    idx += 1

        self.shuffle_count += 1
        self.message = f"已重新洗牌! (第{self.shuffle_count}次)"
        self.message_timer = 120  # 2秒

        # 如果仍然无解, 再洗一次(递归但有深度限制)
        if not self._has_valid_moves() and self.shuffle_count < 10:
            self._shuffle_grid()

    def _remove_pair(self, r1, c1, r2, c2):
        """消除一对方块"""
        self.grid[r1][c1] = -1
        self.grid[r2][c2] = -1
        self.score += 10
        self.moves += 1

        # 检查是否获胜
        if self._count_remaining() == 0:
            self.won = True
            self.game_over = True
            self.message = "恭喜通关! 🎉"
        elif not self._has_valid_moves():
            self._shuffle_grid()

    def _count_remaining(self):
        """统计剩余方块数"""
        count = 0
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] != -1:
                    count += 1
        return count

    def _draw_path(self, path):
        """绘制连接路径"""
        if not path:
            return

        # 将网格坐标转换为屏幕坐标 (方块中心)
        points = []
        for r, c in path:
            rect = self._get_tile_rect(r, c)
            points.append(rect.center)

        if len(points) >= 2:
            for i in range(len(points) - 1):
                pygame.draw.line(self.screen, COLORS['path'],
                                 points[i], points[i + 1], 4)
                # 在拐点画小圆
                if 0 < i < len(points) - 1:
                    pygame.draw.circle(self.screen, COLORS['path'], points[i], 5)

    def _draw_ui(self):
        """绘制UI界面"""
        # 背景
        self.screen.fill(COLORS['bg'])

        # 顶部面板
        pygame.draw.rect(self.screen, COLORS['panel'],
                         (0, 0, WIN_WIDTH, TOP_BAR))
        pygame.draw.line(self.screen, COLORS['border'],
                         (0, TOP_BAR), (WIN_WIDTH, TOP_BAR), 2)

        # 游戏信息
        remaining = self._count_remaining()
        texts = [
            f"剩余: {remaining}",
            f"得分: {self.score}",
            f"步数: {self.moves}",
            f"时间: {self.time // 60}秒",
        ]
        x = 20
        for text in texts:
            surf = self.font.render(text, True, COLORS['text'])
            self.screen.blit(surf, (x, 15))
            x += surf.get_width() + 30

        # 操作提示
        tips = "[H]提示  [S]洗牌  [R]重开  [ESC]退出"
        surf = self.font_small.render(tips, True, COLORS['text_dim'])
        self.screen.blit(surf, (WIN_WIDTH - surf.get_width() - 20, 20))

        # 消息显示
        if self.message_timer > 0:
            surf = self.font_big.render(self.message, True, COLORS['win'] if self.won else COLORS['hint'])
            msg_rect = surf.get_rect(center=(WIN_WIDTH // 2, WIN_HEIGHT // 2 - 40))
            # 背景框
            bg_rect = msg_rect.inflate(40, 20)
            bg_rect.center = msg_rect.center
            pygame.draw.rect(self.screen, (0, 0, 0, 180), bg_rect, border_radius=10)
            pygame.draw.rect(self.screen, COLORS['win'] if self.won else COLORS['hint'],
                            bg_rect, width=2, border_radius=10)
            self.screen.blit(surf, msg_rect)

        # 游戏结束/获胜显示
        if self.won:
            win_surf = self.font_big.render("🎉 恭喜通关! 🎉", True, COLORS['win'])
            win_rect = win_surf.get_rect(center=(WIN_WIDTH // 2, WIN_HEIGHT // 2 - 100))
            self.screen.blit(win_surf, win_rect)

            info_surf = self.font.render(f"得分: {self.score}  步数: {self.moves}  用时: {self.time // 60}秒",
                                          True, COLORS['text'])
            info_rect = info_surf.get_rect(center=(WIN_WIDTH // 2, WIN_HEIGHT // 2 - 50))
            self.screen.blit(info_surf, info_rect)

            restart_surf = self.font.render("按 R 重新开始", True, COLORS['text_dim'])
            restart_rect = restart_surf.get_rect(center=(WIN_WIDTH // 2, WIN_HEIGHT // 2))
            self.screen.blit(restart_surf, restart_rect)

    def handle_event(self, event):
        """处理输入事件"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            if event.key == pygame.K_r:
                self.reset_game()
                return True
            if event.key == pygame.K_h:
                # 提示
                hint = self._find_hint()
                if hint:
                    r1, c1, r2, c2, path = hint
                    self.hint_pair = ((r1, c1), (r2, c2))
                    self.path_line = path
                    self.path_timer = 60
                    self.selected = None
            if event.key == pygame.K_s:
                # 洗牌
                if not self.game_over:
                    self._shuffle_grid()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.game_over:
                return True

            pos = self._get_grid_pos(event.pos[0], event.pos[1])
            if pos is None:
                return True

            r, c = pos
            if self.grid[r][c] == -1:
                return True

            if self.selected is None:
                # 第一次选择
                self.selected = (r, c)
                self.hint_pair = None
            else:
                r1, c1 = self.selected
                # 点击同一个方块 — 取消选中
                if r1 == r and c1 == c:
                    self.selected = None
                    return True

                # 检查是否可以连接
                if self.grid[r1][c1] == self.grid[r][c]:
                    ok, path = self._can_connect(r1, c1, r, c)
                    if ok:
                        self.path_line = path
                        self.path_timer = 30
                        self._remove_pair(r1, c1, r, c)
                        self.selected = None
                        self.hint_pair = None
                    else:
                        self.selected = (r, c)
                        self.hint_pair = None
                else:
                    self.selected = (r, c)
                    self.hint_pair = None

        return True

    def update(self):
        """更新游戏状态"""
        if not self.game_over:
            self.time += 1

        if self.path_timer > 0:
            self.path_timer -= 1
            if self.path_timer == 0:
                self.path_line = []

        if self.message_timer > 0:
            self.message_timer -= 1

    def render(self):
        """渲染游戏"""
        self._draw_ui()

        # 绘制网格背景
        grid_rect = pygame.Rect(
            self.offset_x, self.offset_y,
            COLS * (TILE_SIZE + MARGIN) + MARGIN,
            ROWS * (TILE_SIZE + MARGIN) + MARGIN
        )
        pygame.draw.rect(self.screen, COLORS['panel'], grid_rect, border_radius=8)

        # 绘制所有方块
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] == -1:
                    continue
                highlight = None
                if self.selected and self.selected[0] == r and self.selected[1] == c:
                    highlight = 'selected'
                if self.hint_pair:
                    if (r, c) == self.hint_pair[0] or (r, c) == self.hint_pair[1]:
                        highlight = 'hint'
                self._draw_tile(r, c, highlight)

        # 绘制连接路径
        if self.path_timer > 0 and self.path_line:
            self._draw_path(self.path_line)

        pygame.display.flip()

    def run(self):
        """主循环"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    if not self.handle_event(event):
                        running = False

            self.update()
            self.render()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = LinkGame()
    game.run()