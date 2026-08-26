"""
消灭星星 (Pop Star) - 经典点击消除益智游戏
2026-08-26
游戏规则：
  - 10x10 彩色方块网格，5种颜色
  - 点击连接在一起的同色方块组（≥2个）消除
  - 消除后上方方块落下，空列向左移动
  - 无法消除时游戏结束，全部消除获得额外奖励
"""

import pygame
import random
import sys
from collections import deque

# ==================== 常量配置 ====================
COLS = 10
ROWS = 10
COLORS = [
    (255, 80, 80),   # 红
    (80, 200, 80),   # 绿
    (80, 130, 255),  # 蓝
    (255, 200, 50),  # 黄
    (200, 80, 255),  # 紫
]
COLOR_NAMES = ["红", "绿", "蓝", "黄", "紫"]

# 尺寸
BLOCK_SIZE = 52
GRID_OFFSET_X = 60
GRID_OFFSET_Y = 120
INFO_OFFSET_Y = 20

# 窗口
WINDOW_W = GRID_OFFSET_X * 2 + COLS * BLOCK_SIZE
WINDOW_H = GRID_OFFSET_Y + ROWS * BLOCK_SIZE + 60

FPS = 60

# ==================== 游戏核心 ====================


class PopStar:
    """游戏主逻辑"""

    def __init__(self):
        self.grid = [[0] * COLS for _ in range(ROWS)]
        self.score = 0
        self.game_over = False
        self.cleared = False  # 是否全部消除
        self._init_grid()

    def _init_grid(self):
        """生成随机初始网格，确保没有初始大块"""
        for r in range(ROWS):
            for c in range(COLS):
                self.grid[r][c] = random.randint(0, len(COLORS) - 1)
        # 如果初始就没有可消除的，重新生成
        if not self._find_all_groups():
            self._init_grid()

    def _get_color(self, r, c):
        """获取格子颜色索引，越界返回 -1"""
        if 0 <= r < ROWS and 0 <= c < COLS:
            return self.grid[r][c]
        return -1

    def get_group(self, start_r, start_c):
        """BFS 查找与 (start_r, start_c) 连通的所有同色格子"""
        color = self._get_color(start_r, start_c)
        if color < 0:
            return []

        visited = set()
        queue = deque([(start_r, start_c)])
        group = []

        while queue:
            r, c = queue.popleft()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            group.append((r, c))
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if self._get_color(nr, nc) == color and (nr, nc) not in visited:
                    queue.append((nr, nc))
        return group

    def _find_all_groups(self):
        """查找所有可消除的组（≥2个同色连通块）"""
        visited = set()
        groups = []
        for r in range(ROWS):
            for c in range(COLS):
                if self.grid[r][c] >= 0 and (r, c) not in visited:
                    group = self.get_group(r, c)
                    for cell in group:
                        visited.add(cell)
                    if len(group) >= 2:
                        groups.append(group)
        return groups

    def has_valid_moves(self):
        """检查是否还有可消除的组"""
        return len(self._find_all_groups()) > 0

    def remove_group(self, group):
        """消除一组方块并更新分数"""
        if len(group) < 2:
            return False

        # 计算分数：n * (n-1) * 5
        self.score += len(group) * (len(group) - 1) * 5

        # 标记为消除
        for r, c in group:
            self.grid[r][c] = -1

        # 重力下落 & 左移
        self._apply_gravity()
        self._apply_shift_left()

        # 检查游戏状态
        if not self.has_valid_moves():
            # 检查是否全部消除
            all_cleared = all(self.grid[r][c] < 0 for r in range(ROWS) for c in range(COLS))
            if all_cleared:
                self.score += 1000  # 全部消除奖励
                self.cleared = True
            self.game_over = True

        return True

    def _apply_gravity(self):
        """让方块下落（每列内部下落）"""
        for c in range(COLS):
            # 从下往上收集非空方块
            col_blocks = []
            for r in range(ROWS - 1, -1, -1):
                if self.grid[r][c] >= 0:
                    col_blocks.append(self.grid[r][c])
            # 从底向上填充
            for r in range(ROWS):
                idx = ROWS - 1 - r
                if r < len(col_blocks):
                    self.grid[ROWS - 1 - r][c] = col_blocks[r]
                else:
                    self.grid[ROWS - 1 - r][c] = -1

    def _apply_shift_left(self):
        """空列向左移动"""
        # 收集非空列
        new_cols = []
        for c in range(COLS):
            if any(self.grid[r][c] >= 0 for r in range(ROWS)):
                col_data = [self.grid[r][c] for r in range(ROWS)]
                new_cols.append(col_data)

        # 填充新网格
        for c in range(COLS):
            for r in range(ROWS):
                if c < len(new_cols):
                    self.grid[r][c] = new_cols[c][r]
                else:
                    self.grid[r][c] = -1

    def get_grid(self):
        return self.grid


# ==================== 渲染 ====================


class GameRenderer:
    """负责绘制游戏画面"""

    def __init__(self, screen):
        self.screen = screen
        self.font_large = pygame.font.SysFont("simhei", 36, bold=True)
        self.font_medium = pygame.font.SysFont("simhei", 28)
        self.font_small = pygame.font.SysFont("simhei", 20)
        self.font_en = pygame.font.SysFont("arial", 24, bold=True)
        # 尝试加载中文字体
        self._try_chinese_font()

    def _try_chinese_font(self):
        """尝试加载中文字体"""
        candidates = [
            "simhei.ttf", "SimHei", "Microsoft YaHei",
            "WenQuanYi Micro Hei", "Noto Sans CJK SC",
            "DejaVu Sans", "Arial"
        ]
        for name in candidates:
            try:
                f = pygame.font.SysFont(name, 28)
                if f.render("测", True, (255, 255, 255)).get_width() > 0:
                    self.font_medium = pygame.font.SysFont(name, 28)
                    self.font_small = pygame.font.SysFont(name, 20)
                    self.font_large = pygame.font.SysFont(name, 36, bold=True)
                    return
            except Exception:
                continue

    def draw_grid(self, grid, highlight_group=None):
        """绘制网格"""
        for r in range(ROWS):
            for c in range(COLS):
                val = grid[r][c]
                if val < 0:
                    continue
                x = GRID_OFFSET_X + c * BLOCK_SIZE
                y = GRID_OFFSET_Y + r * BLOCK_SIZE
                color = COLORS[val]
                rect = pygame.Rect(x + 1, y + 1, BLOCK_SIZE - 2, BLOCK_SIZE - 2)

                # 高亮
                is_highlight = highlight_group and (r, c) in highlight_group
                if is_highlight:
                    # 画外发光效果
                    glow_rect = pygame.Rect(x - 2, y - 2, BLOCK_SIZE + 4, BLOCK_SIZE + 4)
                    pygame.draw.rect(self.screen, (255, 255, 255), glow_rect, border_radius=6)

                # 方块主体
                pygame.draw.rect(self.screen, color, rect, border_radius=4)

                # 高光（左上角亮色）
                light = tuple(min(255, c + 60) for c in color)
                hl_rect = pygame.Rect(x + 3, y + 3, BLOCK_SIZE - 10, BLOCK_SIZE // 3)
                pygame.draw.rect(self.screen, light, hl_rect, border_radius=2)

                # 边框
                pygame.draw.rect(self.screen, (60, 60, 60), rect, 1, border_radius=4)

    def draw_info(self, game):
        """绘制分数和提示信息"""
        # 标题
        title = self.font_large.render("消灭星星", True, (255, 255, 100))
        self.screen.blit(title, (WINDOW_W // 2 - title.get_width() // 2, INFO_OFFSET_Y))

        # 分数
        score_text = self.font_medium.render(f"分数: {game.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (WINDOW_W // 2 - score_text.get_width() // 2, 65))

        # 提示
        hint = self.font_small.render("点击 ≥2 个同色相连方块消除", True, (180, 180, 180))
        self.screen.blit(hint, (WINDOW_W // 2 - hint.get_width() // 2, GRID_OFFSET_Y - 25))

    def draw_game_over(self, game):
        """绘制游戏结束画面"""
        # 半透明遮罩
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # 结束文字
        if game.cleared:
            text = self.font_large.render("完美通关！", True, (255, 255, 100))
        else:
            text = self.font_large.render("游戏结束", True, (255, 100, 100))
        self.screen.blit(text, (WINDOW_W // 2 - text.get_width() // 2, WINDOW_H // 2 - 60))

        # 最终分数
        final = self.font_large.render(f"最终得分: {game.score}", True, (255, 255, 255))
        self.screen.blit(final, (WINDOW_W // 2 - final.get_width() // 2, WINDOW_H // 2 - 10))

        # 重新开始提示
        restart = self.font_medium.render("按 R 重新开始  |  按 ESC 退出", True, (200, 200, 200))
        self.screen.blit(restart, (WINDOW_W // 2 - restart.get_width() // 2, WINDOW_H // 2 + 40))


# ==================== 主循环 ====================


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("消灭星星 - Pop Star")
    clock = pygame.time.Clock()

    game = PopStar()
    renderer = GameRenderer(screen)
    highlight_group = []  # 当前高亮组
    running = True

    while running:
        dt = clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    # 重新开始
                    game = PopStar()
                    highlight_group = []
                elif event.key == pygame.K_q:
                    running = False

            if event.type == pygame.MOUSEBUTTONDOWN and not game.game_over:
                mx, my = event.pos
                # 计算点击的格子
                c = (mx - GRID_OFFSET_X) // BLOCK_SIZE
                r = (my - GRID_OFFSET_Y) // BLOCK_SIZE
                if 0 <= r < ROWS and 0 <= c < COLS and game.grid[r][c] >= 0:
                    group = game.get_group(r, c)
                    if len(group) >= 2:
                        game.remove_group(group)
                        highlight_group = []

        # 鼠标悬停高亮
        if not game.game_over:
            mx, my = mouse_pos
            c = (mx - GRID_OFFSET_X) // BLOCK_SIZE
            r = (my - GRID_OFFSET_Y) // BLOCK_SIZE
            if 0 <= r < ROWS and 0 <= c < COLS and game.grid[r][c] >= 0:
                group = game.get_group(r, c)
                if len(group) >= 2:
                    highlight_group = group
                else:
                    highlight_group = []
            else:
                highlight_group = []

        # === 绘制 ===
        screen.fill((30, 30, 40))

        # 网格背景
        grid_bg = pygame.Rect(
            GRID_OFFSET_X - 4, GRID_OFFSET_Y - 4,
            COLS * BLOCK_SIZE + 8, ROWS * BLOCK_SIZE + 8
        )
        pygame.draw.rect(screen, (20, 20, 28), grid_bg, border_radius=6)

        renderer.draw_grid(game.grid, highlight_group)
        renderer.draw_info(game)

        if game.game_over:
            renderer.draw_game_over(game)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()