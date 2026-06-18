"""
Block Puzzle (方块拼图 / 1010!)
===============================
在 10x10 网格上放置随机形状的方块，
填满整行或整列即可消除，放置所有方块后游戏结束。

操作方式：
- 点击下方三个备选形状之一选中它
- 点击网格区域放置选中的形状
- 按 R 键重新开始游戏

作者：AI 游戏开发者
日期：2026-06-18
"""

import pygame
import random
import sys

# ---------------------------- 常量定义 ----------------------------
GRID_SIZE = 10          # 10x10 网格
CELL_SIZE = 44          # 每个格子像素大小
GRID_MARGIN = 30        # 网格左边距
GRID_TOP = 60           # 网格上边距
PREVIEW_SIZE = 30       # 备选方块预览区格子大小
PREVIEW_MARGIN = 20

WINDOW_WIDTH = GRID_MARGIN * 2 + GRID_SIZE * CELL_SIZE + 100
WINDOW_HEIGHT = GRID_TOP + GRID_SIZE * CELL_SIZE + 120

# 颜色定义 (R, G, B)
BLACK = (20, 20, 30)
WHITE = (240, 240, 245)
GRAY = (100, 100, 110)
LIGHT_GRAY = (180, 180, 190)
GRID_COLOR = (50, 50, 65)
GRID_LINE = (70, 70, 85)
HIGHLIGHT = (255, 255, 100, 80)

# 方块颜色方案
SHAPE_COLORS = [
    (255, 99, 71),    # 番茄红
    (54, 215, 183),   # 青绿
    (255, 185, 15),   # 金色
    (108, 92, 231),   # 紫色
    (255, 107, 107),  # 粉红
    (46, 213, 115),   # 翠绿
    (72, 126, 176),   # 天蓝
    (255, 159, 67),   # 橙色
]

# ---------------------------- 形状库 ----------------------------
# 每个形状是一个二维列表，1 表示填充，0 表示空
SHAPES = [
    # 单格
    [[1]],
    # 2格横条
    [[1, 1]],
    # 2格竖条
    [[1], [1]],
    # 3格横条
    [[1, 1, 1]],
    # 3格竖条
    [[1], [1], [1]],
    # 4格横条
    [[1, 1, 1, 1]],
    # 4格竖条
    [[1], [1], [1], [1]],
    # 5格横条
    [[1, 1, 1, 1, 1]],
    # 5格竖条
    [[1], [1], [1], [1], [1]],
    # L形
    [[1, 0], [1, 0], [1, 1]],
    # 反L形
    [[0, 1], [0, 1], [1, 1]],
    # L形 2x3
    [[1, 0, 0], [1, 1, 1]],
    # 反L形 2x3
    [[0, 0, 1], [1, 1, 1]],
    # 2x2 方形
    [[1, 1], [1, 1]],
    # 3x3 方形
    [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
    # T形
    [[1, 1, 1], [0, 1, 0]],
    # 反T形
    [[0, 1, 0], [1, 1, 1]],
    # Z形
    [[1, 1, 0], [0, 1, 1]],
    # 反Z形
    [[0, 1, 1], [1, 1, 0]],
    # 十字形
    [[0, 1, 0], [1, 1, 1], [0, 1, 0]],
    # 小L 2x2
    [[1, 0], [1, 1]],
    # 小反L 2x2
    [[0, 1], [1, 1]],
    # 3格 L 形
    [[1, 0], [1, 0], [1, 1]],
    # 长条拐角
    [[1, 0, 0], [1, 1, 1]],
]


def rotate_shape(shape):
    """顺时针旋转形状90度"""
    rows, cols = len(shape), len(shape[0])
    return [[shape[rows - 1 - j][i] for j in range(rows)] for i in range(cols)]


def get_shape_variants(shape):
    """获取一个形状的所有旋转变体（去重）"""
    variants = []
    s = shape
    for _ in range(4):
        if s not in variants:
            variants.append(s)
        s = rotate_shape(s)
    return variants


class BlockPuzzle:
    """方块拼图游戏主类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Block Puzzle - 方块拼图 1010!")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("simhei", 36, bold=True)
        self.font_medium = pygame.font.SysFont("simhei", 24, bold=True)
        self.font_small = pygame.font.SysFont("simhei", 18)

        # 尝试加载中文字体，失败则用默认字体
        try:
            self.font_large = pygame.font.Font(None, 40)
            self.font_medium = pygame.font.Font(None, 28)
            self.font_small = pygame.font.Font(None, 20)
        except Exception:
            pass

        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        # 10x10 网格，0 表示空，其他值表示颜色索引
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.score = 0
        self.game_over = False
        self.selected_index = -1  # 当前选中的备选方块索引
        self.preview_shapes = []  # 3个备选方块
        self.preview_colors = []  # 每个备选方块的颜色
        self.generate_previews()

    def generate_previews(self):
        """生成3个随机备选方块"""
        self.preview_shapes = []
        self.preview_colors = []
        for _ in range(3):
            shape = random.choice(SHAPES)
            color = random.choice(SHAPE_COLORS)
            self.preview_shapes.append(shape)
            self.preview_colors.append(color)

    def can_place(self, shape, grid_x, grid_y):
        """检查形状能否放置在网格的指定位置"""
        for r in range(len(shape)):
            for c in range(len(shape[0])):
                if shape[r][c] == 1:
                    x, y = grid_x + c, grid_y + r
                    if x < 0 or x >= GRID_SIZE or y < 0 or y >= GRID_SIZE:
                        return False
                    if self.grid[y][x] != 0:
                        return False
        return True

    def place_shape(self, shape, grid_x, grid_y, color_idx):
        """将形状放置在网格上"""
        for r in range(len(shape)):
            for c in range(len(shape[0])):
                if shape[r][c] == 1:
                    self.grid[grid_y + r][grid_x + c] = color_idx

    def clear_lines(self):
        """清除填满的行和列，返回清除的数量"""
        cleared_rows = []
        cleared_cols = []

        # 检查行
        for r in range(GRID_SIZE):
            if all(self.grid[r][c] != 0 for c in range(GRID_SIZE)):
                cleared_rows.append(r)

        # 检查列
        for c in range(GRID_SIZE):
            if all(self.grid[r][c] != 0 for r in range(GRID_SIZE)):
                cleared_cols.append(c)

        # 清除行
        for r in cleared_rows:
            for c in range(GRID_SIZE):
                self.grid[r][c] = 0

        # 清除列
        for c in cleared_cols:
            for r in range(GRID_SIZE):
                self.grid[r][c] = 0

        return len(cleared_rows) + len(cleared_cols)

    def try_place(self, shape_index, grid_x, grid_y):
        """尝试放置选中的备选方块"""
        if shape_index < 0 or shape_index >= len(self.preview_shapes):
            return False

        shape = self.preview_shapes[shape_index]
        if not self.can_place(shape, grid_x, grid_y):
            return False

        # 计算形状中的格子数
        block_count = sum(sum(row) for row in shape)

        # 放置形状
        self.place_shape(shape, grid_x, grid_y, shape_index + 1)

        # 清除行/列
        cleared = self.clear_lines()
        self.score += block_count + cleared * 5

        # 移除已放置的备选方块
        self.preview_shapes.pop(shape_index)
        self.preview_colors.pop(shape_index)
        self.selected_index = -1

        # 生成新的备选方块
        while len(self.preview_shapes) < 3:
            self.preview_shapes.append(random.choice(SHAPES))
            self.preview_colors.append(random.choice(SHAPE_COLORS))

        # 检查是否还能继续放置
        self.check_game_over()
        return True

    def check_game_over(self):
        """检查是否有任意一个备选方块可以放置"""
        for i, shape in enumerate(self.preview_shapes):
            variants = get_shape_variants(shape)
            for variant in variants:
                for r in range(GRID_SIZE - len(variant) + 1):
                    for c in range(GRID_SIZE - len(variant[0]) + 1):
                        if self.can_place(variant, c, r):
                            return  # 至少有一个可以放置
        self.game_over = True

    def handle_click(self, pos):
        """处理鼠标点击事件"""
        if self.game_over:
            return

        mx, my = pos

        # 检查是否点击了备选方块
        preview_y = GRID_TOP + GRID_SIZE * CELL_SIZE + 15
        for i in range(len(self.preview_shapes)):
            px = GRID_MARGIN + i * (CELL_SIZE * 2 + PREVIEW_MARGIN)
            shape = self.preview_shapes[i]
            shape_w = len(shape[0]) * PREVIEW_SIZE
            shape_h = len(shape) * PREVIEW_SIZE
            rect = pygame.Rect(px, preview_y, max(shape_w, CELL_SIZE * 2 - 10), max(shape_h, CELL_SIZE))
            if rect.collidepoint(mx, my):
                self.selected_index = i
                return

        # 如果选中了备选方块，尝试放置到网格
        if self.selected_index >= 0:
            gx = (mx - GRID_MARGIN) // CELL_SIZE
            gy = (my - GRID_TOP) // CELL_SIZE
            if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
                # 尝试所有旋转变体
                shape = self.preview_shapes[self.selected_index]
                variants = get_shape_variants(shape)
                for variant in variants:
                    # 调整位置，使形状居中于点击位置
                    offset_x = gx - len(variant[0]) // 2
                    offset_y = gy - len(variant) // 2
                    if self.can_place(variant, offset_x, offset_y):
                        # 替换为匹配的变体
                        self.preview_shapes[self.selected_index] = variant
                        self.try_place(self.selected_index, offset_x, offset_y)
                        return

    def handle_key(self, key):
        """处理键盘事件"""
        if key == pygame.K_r:
            self.reset_game()

    def draw_grid(self):
        """绘制游戏网格"""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x = GRID_MARGIN + c * CELL_SIZE
                y = GRID_TOP + r * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

                if self.grid[r][c] != 0:
                    # 填充方块
                    color_idx = self.grid[r][c]
                    color = SHAPE_COLORS[(color_idx - 1) % len(SHAPE_COLORS)]
                    pygame.draw.rect(self.screen, color, rect, border_radius=4)
                    # 高光效果
                    inner = pygame.Rect(x + 3, y + 3, CELL_SIZE - 6, CELL_SIZE - 6)
                    lighter = tuple(min(255, c + 40) for c in color)
                    pygame.draw.rect(self.screen, lighter, inner, border_radius=3)
                else:
                    pygame.draw.rect(self.screen, GRID_COLOR, rect, border_radius=2)

                pygame.draw.rect(self.screen, GRID_LINE, rect, 1, border_radius=2)

        # 网格边框
        outer_rect = pygame.Rect(
            GRID_MARGIN - 2, GRID_TOP - 2,
            GRID_SIZE * CELL_SIZE + 4, GRID_SIZE * CELL_SIZE + 4
        )
        pygame.draw.rect(self.screen, LIGHT_GRAY, outer_rect, 2, border_radius=4)

    def draw_previews(self):
        """绘制备选方块区域"""
        preview_y = GRID_TOP + GRID_SIZE * CELL_SIZE + 15

        # 标题
        text = self.font_medium.render("备选方块:", True, WHITE)
        self.screen.blit(text, (GRID_MARGIN, preview_y - 25))

        for i, shape in enumerate(self.preview_shapes):
            px = GRID_MARGIN + i * (CELL_SIZE * 2 + PREVIEW_MARGIN)
            py = preview_y

            # 背景框
            bg_rect = pygame.Rect(px - 5, py - 5, CELL_SIZE * 2, CELL_SIZE + 10)
            if i == self.selected_index:
                pygame.draw.rect(self.screen, HIGHLIGHT[:3], bg_rect, border_radius=6)
                pygame.draw.rect(self.screen, WHITE, bg_rect, 2, border_radius=6)
            else:
                pygame.draw.rect(self.screen, (40, 40, 55), bg_rect, border_radius=6)
                pygame.draw.rect(self.screen, GRAY, bg_rect, 1, border_radius=6)

            # 绘制形状
            color = self.preview_colors[i]
            shape_w = len(shape[0])
            shape_h = len(shape)
            offset_x = px + (CELL_SIZE * 2 - 10 - shape_w * PREVIEW_SIZE) // 2
            offset_y = py + (CELL_SIZE - shape_h * PREVIEW_SIZE) // 2 + 5

            for r in range(shape_h):
                for c in range(shape_w):
                    if shape[r][c] == 1:
                        rect = pygame.Rect(
                            offset_x + c * PREVIEW_SIZE,
                            offset_y + r * PREVIEW_SIZE,
                            PREVIEW_SIZE - 2, PREVIEW_SIZE - 2
                        )
                        pygame.draw.rect(self.screen, color, rect, border_radius=3)

    def draw_info(self):
        """绘制得分和状态信息"""
        # 得分
        score_text = self.font_large.render(f"得分: {self.score}", True, WHITE)
        self.screen.blit(score_text, (GRID_MARGIN, 10))

        # 操作提示
        hint = self.font_small.render("R: 重新开始  |  点击选择方块  |  点击网格放置", True, LIGHT_GRAY)
        self.screen.blit(hint, (GRID_MARGIN, WINDOW_HEIGHT - 30))

        if self.game_over:
            # 游戏结束蒙层
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            game_over_text = self.font_large.render("游戏结束!", True, (255, 100, 100))
            score_text2 = self.font_large.render(f"最终得分: {self.score}", True, WHITE)
            restart_text = self.font_medium.render("按 R 重新开始", True, WHITE)

            tw = game_over_text.get_width()
            self.screen.blit(game_over_text, ((WINDOW_WIDTH - tw) // 2, WINDOW_HEIGHT // 2 - 60))
            tw2 = score_text2.get_width()
            self.screen.blit(score_text2, ((WINDOW_WIDTH - tw2) // 2, WINDOW_HEIGHT // 2))
            tw3 = restart_text.get_width()
            self.screen.blit(restart_text, ((WINDOW_WIDTH - tw3) // 2, WINDOW_HEIGHT // 2 + 50))

    def run(self):
        """游戏主循环"""
        running = True
        while running:
            self.screen.fill(BLACK)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)
                    if event.key == pygame.K_ESCAPE:
                        running = False

            self.draw_grid()
            self.draw_previews()
            self.draw_info()

            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()
        sys.exit()


# ---------------------------- 程序入口 ----------------------------
if __name__ == "__main__":
    game = BlockPuzzle()
    game.run()