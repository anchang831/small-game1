"""
Nonogram (数织/像素拼图) - 逻辑推理填色游戏
通过行列数字提示，推理出正确格子，拼出隐藏图案
操作：左键涂色 | 右键打叉 | 滚轮切换关卡
"""

import pygame
import sys
import math
from enum import Enum

# ------------------------------ 常量 ------------------------------
SCREEN_W, SCREEN_H = 800, 720
FPS = 60
COLORS = {
    'bg':        (30, 30, 40),
    'panel':     (45, 45, 55),
    'grid_line': (80, 80, 100),
    'filled':    (100, 180, 255),
    'filled_ok': (80, 220, 140),
    'cross':     (220, 80, 80),
    'hint':      (255, 255, 255),
    'hint_dim':  (140, 140, 160),
    'text':      (220, 220, 230),
    'title':     (255, 200, 80),
    'btn':       (70, 130, 200),
    'btn_hover': (90, 160, 240),
    'btn_ok':    (60, 180, 100),
    'btn_ok_h':  (80, 210, 130),
    'complete':  (255, 215, 0),
}

# ------------------------------ 关卡数据 ------------------------------
# 每个关卡: (名称, 网格数据, 行列提示)
# 网格: 0=空, 1=填充
LEVELS = [
    ("❤️ 爱心", [
        [0,0,0,0,0,0,0,0,0,0],
        [0,1,1,0,0,0,0,1,1,0],
        [1,1,1,1,0,0,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1],
        [0,1,1,1,1,1,1,1,1,0],
        [0,0,1,1,1,1,1,1,0,0],
        [0,0,0,1,1,1,1,0,0,0],
        [0,0,0,0,1,1,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0],
    ]),
    ("⭐ 星星", [
        [0,0,0,0,0,1,0,0,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,1,0,1,1,1,1,1,0,1,0],
        [1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1],
        [0,1,1,1,1,1,1,1,1,1,0],
        [0,0,1,1,1,1,1,1,1,0,0],
        [0,0,0,1,1,1,1,1,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,0,0,1,0,0,0,0,0],
    ]),
    ("🎄 圣诞树", [
        [0,0,0,0,0,1,0,0,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,1,1,1,1,1,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,0,1,1,1,1,1,1,1,0,0],
        [0,0,0,1,1,1,1,1,0,0,0],
        [0,1,1,1,1,1,1,1,1,1,0],
        [0,0,1,1,1,1,1,1,1,0,0],
        [1,1,1,1,1,1,1,1,1,1,1],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
    ]),
    ("🐱 小猫", [
        [0,0,0,0,0,0,0,0,0,0],
        [0,1,1,0,0,0,0,1,1,0],
        [0,1,1,0,0,0,0,1,1,0],
        [0,0,0,0,0,0,0,0,0,0],
        [1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1],
        [0,1,0,1,1,1,1,0,1,0],
        [0,0,1,0,0,0,0,1,0,0],
        [0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0],
    ]),
    ("🚀 火箭", [
        [0,0,0,0,0,1,0,0,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,1,1,1,1,1,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,0,0,1,0,0,0,0,0],
        [0,0,0,0,0,1,0,0,0,0,0],
    ]),
    ("🌸 花朵", [
        [0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,1,0,1,0,1,0,0,0],
        [0,0,1,1,1,1,1,1,1,0,0],
        [0,1,1,1,1,1,1,1,1,1,0],
        [0,0,1,1,1,1,1,1,1,0,0],
        [0,1,1,1,1,1,1,1,1,1,0],
        [0,1,1,1,1,1,1,1,1,1,0],
        [0,0,1,1,1,1,1,1,1,0,0],
        [0,0,0,1,1,1,1,1,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0],
    ]),
    ("🐟 小鱼", [
        [0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,0,1,1,1,1,1,0,0,0],
        [0,1,1,1,1,1,1,1,1,1,0,0],
        [1,1,1,1,1,1,1,1,1,1,1,1],
        [1,1,1,1,1,1,1,1,1,1,1,1],
        [0,1,1,1,1,1,1,1,1,1,1,0],
        [0,0,0,0,1,1,1,1,1,0,0,0],
        [0,0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0,0,0],
    ]),
    ("🏠 小房子", [
        [0,0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,1,1,1,0,0,0,0],
        [0,0,0,1,1,1,1,1,0,0,0],
        [0,0,1,1,1,1,1,1,1,0,0],
        [0,1,1,1,1,1,1,1,1,1,0],
        [1,1,1,1,1,1,1,1,1,1,1],
        [1,0,1,1,1,1,1,1,1,0,1],
        [1,0,1,1,1,1,1,1,1,0,1],
        [1,0,1,1,1,1,1,1,1,0,1],
        [1,0,1,1,1,1,1,1,1,0,1],
        [1,1,1,1,1,1,1,1,1,1,1],
    ]),
]

# ------------------------------ 工具函数 ------------------------------
def compute_hints(grid):
    """从网格数据计算行列提示"""
    rows, cols = len(grid), len(grid[0])
    row_hints, col_hints = [], []
    for r in range(rows):
        hints = []
        count = 0
        for c in range(cols):
            if grid[r][c]:
                count += 1
            else:
                if count > 0:
                    hints.append(count)
                    count = 0
        if count > 0:
            hints.append(count)
        row_hints.append(hints if hints else [0])
    for c in range(cols):
        hints = []
        count = 0
        for r in range(rows):
            if grid[r][c]:
                count += 1
            else:
                if count > 0:
                    hints.append(count)
                    count = 0
        if count > 0:
            hints.append(count)
        col_hints.append(hints if hints else [0])
    return row_hints, col_hints

# 预处理所有关卡的提示
LEVEL_DATA = []
for name, grid in LEVELS:
    row_hints, col_hints = compute_hints(grid)
    LEVEL_DATA.append((name, grid, row_hints, col_hints))

# ------------------------------ 游戏类 ------------------------------
class Nonogram:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Nonogram 数织 - 像素拼图")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simhei", 16)
        self.font_small = pygame.font.SysFont("simhei", 13)
        self.font_big = pygame.font.SysFont("simhei", 28)
        self.font_title = pygame.font.SysFont("simhei", 22)
        self.reset()

    def reset(self):
        self.level_idx = 0
        self.load_level(self.level_idx)
        self.completed = False
        self.complete_timer = 0
        self.mistakes = 0
        self.max_mistakes = 5

    def load_level(self, idx):
        idx = idx % len(LEVEL_DATA)
        self.level_idx = idx
        name, grid, row_hints, col_hints = LEVEL_DATA[idx]
        self.name = name
        self.solution = grid
        self.row_hints = row_hints
        self.col_hints = col_hints
        self.rows = len(grid)
        self.cols = len(grid[0])
        self.grid = [[0] * self.cols for _ in range(self.rows)]
        self.marks = [[0] * self.cols for _ in range(self.rows)]
        self.completed = False
        self.complete_timer = 0
        self.mistakes = 0
        self._layout()

    def _layout(self):
        max_hint_rows = max(len(h) for h in self.row_hints)
        max_hint_cols = max(len(h) for h in self.col_hints)
        hint_w = max_hint_rows * 22 + 10
        hint_h = max_hint_cols * 22 + 10
        grid_w = 600
        grid_h = 600
        self.cell_size = min(
            (grid_w - hint_w) // self.cols,
            (grid_h - hint_h) // self.rows
        )
        self.cell_size = max(24, min(self.cell_size, 48))
        self.grid_pixel_w = self.cell_size * self.cols
        self.grid_pixel_h = self.cell_size * self.rows
        self.hint_w = max_hint_rows * (self.cell_size // 2 + 10) + 10
        self.hint_h = max_hint_cols * (self.cell_size // 2 + 10) + 10
        self.grid_x = (SCREEN_W - self.grid_pixel_w - self.hint_w) // 2 + self.hint_w
        self.grid_y = (SCREEN_H - self.grid_pixel_h - self.hint_h) // 2 + self.hint_h + 30

    def check_complete(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] != self.solution[r][c]:
                    return False
        return True

    def handle_click(self, pos, button):
        if self.completed:
            return
        mx, my = pos
        gx = (mx - self.grid_x) // self.cell_size
        gy = (my - self.grid_y) // self.cell_size
        if 0 <= gx < self.cols and 0 <= gy < self.rows:
            if button == 1:  # 左键涂色
                if self.marks[gy][gx]:
                    self.marks[gy][gx] = 0
                if self.grid[gy][gx] == 1:
                    self.grid[gy][gx] = 0
                else:
                    self.grid[gy][gx] = 1
                    # 检查是否正确
                    if self.solution[gy][gx] != 1:
                        self.mistakes += 1
                        self.grid[gy][gx] = 0
                        self.marks[gy][gx] = 1  # 标记错误
                    else:
                        # 自动检查是否完成
                        if self.check_complete():
                            self.completed = True
                            self.complete_timer = pygame.time.get_ticks()
            elif button == 3:  # 右键打叉
                if self.grid[gy][gx] == 1:
                    self.grid[gy][gx] = 0
                self.marks[gy][gx] = 1 - self.marks[gy][gx]

    def draw(self):
        self.screen.fill(COLORS['bg'])

        # 标题
        title = self.font_title.render(f"Nonogram 数织 — {self.name}", True, COLORS['title'])
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 12))

        # 关卡信息
        lvl_text = self.font.render(f"关卡 {self.level_idx + 1}/{len(LEVEL_DATA)}  |  错误: {self.mistakes}/{self.max_mistakes}", True, COLORS['text'])
        self.screen.blit(lvl_text, (SCREEN_W // 2 - lvl_text.get_width() // 2, 48))

        # 绘制网格背景
        grid_bg_rect = (self.grid_x - 2, self.grid_y - 2,
                        self.grid_pixel_w + 4, self.grid_pixel_h + 4)
        pygame.draw.rect(self.screen, COLORS['panel'], grid_bg_rect, border_radius=4)

        # 绘制格子
        for r in range(self.rows):
            for c in range(self.cols):
                x = self.grid_x + c * self.cell_size
                y = self.grid_y + r * self.cell_size
                rect = (x, y, self.cell_size, self.cell_size)
                if self.grid[r][c] == 1:
                    color = COLORS['filled_ok'] if self.completed else COLORS['filled']
                    pygame.draw.rect(self.screen, color, rect)
                elif self.marks[r][c] == 1:
                    # 画叉
                    pygame.draw.rect(self.screen, COLORS['bg'], rect)
                    pad = 4
                    pygame.draw.line(self.screen, COLORS['cross'],
                                     (x + pad, y + pad),
                                     (x + self.cell_size - pad, y + self.cell_size - pad), 2)
                    pygame.draw.line(self.screen, COLORS['cross'],
                                     (x + self.cell_size - pad, y + pad),
                                     (x + pad, y + self.cell_size - pad), 2)
                # 网格线
                pygame.draw.rect(self.screen, COLORS['grid_line'], rect, 1)

        # 绘制行提示
        for r in range(self.rows):
            hints = self.row_hints[r]
            y = self.grid_y + r * self.cell_size + self.cell_size // 2
            # 检查行是否完成
            row_done = all(self.grid[r][c] == self.solution[r][c] for c in range(self.cols))
            color = COLORS['hint'] if not row_done else COLORS['filled_ok']
            x = self.grid_x - 8
            for i, h in enumerate(reversed(hints)):
                txt = self.font_small.render(str(h), True, color)
                x -= txt.get_width() + 2
                self.screen.blit(txt, (x, y - txt.get_height() // 2))

        # 绘制列提示
        for c in range(self.cols):
            hints = self.col_hints[c]
            x = self.grid_x + c * self.cell_size + self.cell_size // 2
            col_done = all(self.grid[r][c] == self.solution[r][c] for r in range(self.rows))
            color = COLORS['hint'] if not col_done else COLORS['filled_ok']
            y = self.grid_y - 8
            for i, h in enumerate(reversed(hints)):
                txt = self.font_small.render(str(h), True, color)
                y -= txt.get_height() + 2
                self.screen.blit(txt, (x - txt.get_width() // 2, y))

        # 操作提示
        hint_y = SCREEN_H - 40
        hint = self.font.render("左键涂色  |  右键标记 ✗  |  滚轮切换关卡  |  R 键重置", True, COLORS['hint_dim'])
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, hint_y))

        # 完成动画效果
        if self.completed:
            now = pygame.time.get_ticks()
            elapsed = now - self.complete_timer
            alpha = min(255, int(elapsed * 0.5))
            if alpha > 0:
                overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, min(180, alpha // 2)))
                self.screen.blit(overlay, (0, 0))
                complete_text = self.font_big.render("🎉 完成！🎉", True, COLORS['complete'])
                sub_text = self.font.render("滚轮切换到下一关", True, COLORS['text'])
                self.screen.blit(complete_text,
                                 (SCREEN_W // 2 - complete_text.get_width() // 2,
                                  SCREEN_H // 2 - 60))
                self.screen.blit(sub_text,
                                 (SCREEN_W // 2 - sub_text.get_width() // 2,
                                  SCREEN_H // 2 + 20))

        # 错误过多提示
        if self.mistakes >= self.max_mistakes:
            warn = self.font.render("❌ 错误过多！按 R 重置本关", True, COLORS['cross'])
            self.screen.blit(warn, (SCREEN_W // 2 - warn.get_width() // 2, SCREEN_H // 2 + 60))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 or event.button == 3:
                        self.handle_click(event.pos, event.button)
                    elif event.button == 4:  # 滚轮上 - 上一关
                        self.load_level(self.level_idx - 1)
                    elif event.button == 5:  # 滚轮下 - 下一关
                        self.load_level(self.level_idx + 1)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.load_level(self.level_idx)
                    elif event.key == pygame.K_RIGHT:
                        self.load_level(self.level_idx + 1)
                    elif event.key == pygame.K_LEFT:
                        self.load_level(self.level_idx - 1)
            self.draw()
        pygame.quit()
        sys.exit()

# ------------------------------ 入口 ------------------------------
if __name__ == "__main__":
    game = Nonogram()
    game.run()