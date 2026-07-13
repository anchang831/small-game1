"""
噗哟噗哟 (Puyo Puyo) - 连锁消除益智游戏
===============================
控制方式:
  ← →  移动
  ↑    旋转
  ↓    加速下落
  空格  直接落底
  R     重新开始

规则:
  - 双球组合从上方落下
  - 4个及以上同色球相连则消除
  - 消除后上方球落下，可能引发连锁
  - 连锁越多分数越高
  - 球堆到顶部则游戏结束
"""

import pygame
import random
import sys

# ======================== 常量定义 ========================
COLS = 6
ROWS = 12  # 可见行数
HIDDEN_ROWS = 2  # 顶部隐藏行
TOTAL_ROWS = ROWS + HIDDEN_ROWS

CELL_SIZE = 36
GRID_WIDTH = COLS * CELL_SIZE
GRID_HEIGHT = ROWS * CELL_SIZE
SIDE_PANEL = 160
WINDOW_WIDTH = GRID_WIDTH + SIDE_PANEL
WINDOW_HEIGHT = GRID_HEIGHT

FPS = 60

# 颜色定义 (RGB)
COLORS = {
    'RED':    (255, 60, 60),
    'GREEN':  (60, 255, 60),
    'BLUE':   (60, 120, 255),
    'YELLOW': (255, 240, 60),
    'GRAY':   (120, 120, 120),   # 垃圾球
    'BG':     (20, 20, 30),
    'GRID':   (40, 40, 55),
    'TEXT':   (255, 255, 255),
    'PANEL':  (30, 30, 45),
}

# 颜色名称列表
COLOR_NAMES = ['RED', 'GREEN', 'BLUE', 'YELLOW']
COLOR_COUNT = len(COLOR_NAMES)

# 方向向量
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class Puyo:
    """单个噗哟球"""
    def __init__(self, col, row, color_name):
        self.col = col
        self.row = row
        self.color = color_name

    def get_color_rgb(self):
        return COLORS[self.color]

    def draw(self, surface, offset_x=0, offset_y=0, alpha=255):
        """绘制噗哟球"""
        x = offset_x + self.col * CELL_SIZE + CELL_SIZE // 2
        y = offset_y + (self.row - HIDDEN_ROWS) * CELL_SIZE + CELL_SIZE // 2

        if y < -CELL_SIZE:
            return  # 不可见区域不绘制

        # 主球体
        radius = CELL_SIZE // 2 - 2
        color = self.get_color_rgb()

        if alpha < 255:
            # 创建带透明度的表面
            s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(s, (*color, alpha), (CELL_SIZE // 2, CELL_SIZE // 2), radius)
            pygame.draw.circle(s, (255, 255, 255, alpha // 2),
                               (CELL_SIZE // 2 - 3, CELL_SIZE // 2 - 3), radius // 2)
            surface.blit(s, (x - CELL_SIZE // 2, y - CELL_SIZE // 2))
        else:
            pygame.draw.circle(surface, color, (x, y), radius)
            # 高光
            pygame.draw.circle(surface, (255, 255, 255, 80), (x - 3, y - 3), radius // 2, 0)


class PuyoPair:
    """一对噗哟球（当前操作块）"""
    def __init__(self, grid):
        self.grid = grid
        self.reset()

    def reset(self):
        """生成新的球对"""
        self.col = COLS // 2 - 1
        self.row = HIDDEN_ROWS - 1
        self.rotation = 0  # 0-3
        # 两个球的颜色
        self.colors = [random.choice(COLOR_NAMES), random.choice(COLOR_NAMES)]
        # 两个球的相对位置（基于旋转状态）
        self.offsets = self._get_offsets()

    def _get_offsets(self):
        """根据旋转状态返回两个球的相对偏移"""
        # [主球位置, 副球相对主球的偏移]
        offsets = [
            [(0, 0), (0, 1)],   # 0: 竖排 (副球在下)
            [(0, 0), (1, 0)],   # 1: 横排 (副球在右)
            [(0, 0), (0, -1)],  # 2: 竖排 (副球在上)
            [(0, 0), (-1, 0)],  # 3: 横排 (副球在左)
        ]
        return offsets[self.rotation]

    def get_puyos(self):
        """获取当前两个球的绝对位置"""
        puyos = []
        for i, (dr, dc) in enumerate(self.offsets):
            col = self.col + (dr if i == 0 else 0)
            row = self.row + (dc if i == 0 else 0)
            # 实际上对于 i=0 是主球，i=1 是副球
            c = self.col + dr
            r = self.row + dc
            puyos.append((c, r, self.colors[i]))
        return puyos

    def get_cells(self):
        """获取绝对坐标列表"""
        cells = []
        for i, (dr, dc) in enumerate(self.offsets):
            cells.append((self.col + dr, self.row + dc))
        return cells

    def rotate(self, direction=1):
        """旋转"""
        old_rotation = self.rotation
        self.rotation = (self.rotation + direction) % 4
        self.offsets = self._get_offsets()
        cells = self.get_cells()
        # 碰墙检测 - 推墙
        if any(c < 0 for c, _ in cells):
            self.col += 1
        elif any(c >= COLS for c, _ in cells):
            self.col -= 1
        # 重新检测
        cells = self.get_cells()
        if not self.grid.can_place(cells):
            self.rotation = old_rotation
            self.offsets = self._get_offsets()
            return False
        return True

    def move(self, dx, dy):
        """移动"""
        self.col += dx
        self.row += dy
        cells = self.get_cells()
        if not self.grid.can_place(cells):
            self.col -= dx
            self.row -= dy
            return False
        return True

    def move_down(self):
        """下落一格，返回是否成功"""
        return self.move(0, 1)

    def hard_drop(self):
        """直接落到底"""
        while self.move_down():
            pass


class PuyoGrid:
    """噗哟网格 / 游戏主逻辑"""
    def __init__(self):
        self.grid = [[None] * COLS for _ in range(TOTAL_ROWS)]
        self.score = 0
        self.chain_count = 0
        self.game_over = False
        self.pair = PuyoPair(self)
        self.is_clearing = False
        self.clear_animation_timer = 0
        self.clear_cells = []
        self.falling_animations = []
        self.drop_speed = 30  # 帧数间隔
        self.drop_counter = 0
        self.level = 1
        self.total_chains = 0

    def can_place(self, cells):
        """检查指定位置是否可以放置"""
        for col, row in cells:
            if col < 0 or col >= COLS or row >= TOTAL_ROWS:
                return False
            if row >= 0 and self.grid[row][col] is not None:
                return False
        return True

    def lock_pair(self):
        """固定当前球对到网格"""
        cells = self.pair.get_cells()
        colors = self.pair.colors
        for i, (col, row) in enumerate(cells):
            if row < 0:
                self.game_over = True
                return
            if row < TOTAL_ROWS:
                self.grid[row][col] = Puyo(col, row, colors[i])

        # 检查游戏结束
        for col in range(COLS):
            if self.grid[0][col] is not None:
                self.game_over = True
                return

        # 触发消除检测
        self._start_clear_chain()

    def _start_clear_chain(self):
        """开始消除连锁"""
        to_clear = self._find_groups()
        if to_clear:
            self.is_clearing = True
            self.clear_cells = to_clear
            self.clear_animation_timer = 15
            self.chain_count += 1
        else:
            # 生成新的球对
            self.pair = PuyoPair(self)
            if not self.can_place(self.pair.get_cells()):
                self.game_over = True

    def _find_groups(self):
        """查找所有4+连接的相同颜色组"""
        visited = [[False] * COLS for _ in range(TOTAL_ROWS)]
        to_clear = []

        for row in range(TOTAL_ROWS):
            for col in range(COLS):
                if visited[row][col] or self.grid[row][col] is None:
                    continue
                color = self.grid[row][col].color
                if color == 'GRAY':
                    visited[row][col] = True
                    continue

                # BFS 查找同色连通
                group = []
                stack = [(col, row)]
                while stack:
                    c, r = stack.pop()
                    if r < 0 or r >= TOTAL_ROWS or c < 0 or c >= COLS:
                        continue
                    if visited[r][c] or self.grid[r][c] is None:
                        continue
                    if self.grid[r][c].color != color:
                        continue
                    visited[r][c] = True
                    group.append((c, r))
                    for dc, dr in DIRS:
                        stack.append((c + dc, r + dr))

                if len(group) >= 4:
                    to_clear.extend(group)

        return to_clear

    def update(self):
        """每帧更新"""
        if self.game_over:
            return

        if self.is_clearing:
            self.clear_animation_timer -= 1
            if self.clear_animation_timer <= 0:
                self._do_clear()
            return

        # 自动下落
        speed = max(3, self.drop_speed - self.level * 2)
        self.drop_counter += 1
        if self.drop_counter >= speed:
            self.drop_counter = 0
            if not self.pair.move_down():
                self.lock_pair()

    def _do_clear(self):
        """执行消除"""
        if not self.clear_cells:
            self.is_clearing = False
            self.chain_count = 0
            self.pair = PuyoPair(self)
            if not self.can_place(self.pair.get_cells()):
                self.game_over = True
            return

        # 消除
        for col, row in self.clear_cells:
            self.grid[row][col] = None

        # 计分
        points = len(self.clear_cells) * 10 * self.chain_count
        if self.chain_count > 1:
            points *= self.chain_count  # 连锁倍率
        self.score += points
        self.total_chains += 1
        self.level = min(20, self.total_chains // 5 + 1)

        # 重力下落
        self._apply_gravity()

        # 检测新的消除
        self.clear_cells = []
        to_clear = self._find_groups()
        if to_clear:
            self.clear_cells = to_clear
            self.clear_animation_timer = 15
            self.chain_count += 1
        else:
            self.is_clearing = False
            self.chain_count = 0
            self.pair = PuyoPair(self)
            if not self.can_place(self.pair.get_cells()):
                self.game_over = True

    def _apply_gravity(self):
        """让悬空的球下落"""
        for col in range(COLS):
            # 从下往上扫描
            write_row = TOTAL_ROWS - 1
            for row in range(TOTAL_ROWS - 1, -1, -1):
                if self.grid[row][col] is not None:
                    if row != write_row:
                        self.grid[write_row][col] = self.grid[row][col]
                        self.grid[write_row][col].row = write_row
                        self.grid[write_row][col].col = col
                        self.grid[row][col] = None
                    write_row -= 1

    def handle_key(self, key):
        """处理按键"""
        if self.game_over:
            return
        if self.is_clearing:
            return

        if key == pygame.K_LEFT:
            self.pair.move(-1, 0)
        elif key == pygame.K_RIGHT:
            self.pair.move(1, 0)
        elif key == pygame.K_DOWN:
            self.pair.move_down()
        elif key == pygame.K_UP:
            self.pair.rotate()
        elif key == pygame.K_SPACE:
            self.pair.hard_drop()
            self.lock_pair()

    def draw(self, surface):
        """绘制游戏"""
        # 背景
        surface.fill(COLORS['BG'])

        # 绘制网格线
        for row in range(ROWS):
            for col in range(COLS):
                x = col * CELL_SIZE
                y = row * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(surface, COLORS['GRID'], rect, 1)

        # 绘制已固定的噗哟球
        for row in range(TOTAL_ROWS):
            for col in range(COLS):
                puyo = self.grid[row][col]
                if puyo and row >= HIDDEN_ROWS:
                    # 检查是否在消除动画中
                    alpha = 255
                    if self.is_clearing and (col, row) in self.clear_cells:
                        alpha = 100 + int(155 * (self.clear_animation_timer / 15))
                    puyo.draw(surface, alpha=alpha)

        # 绘制当前操作的球对
        if not self.is_clearing and not self.game_over:
            cells = self.pair.get_cells()
            colors = self.pair.colors
            for i, (col, row) in enumerate(cells):
                if row >= HIDDEN_ROWS:
                    x = col * CELL_SIZE + CELL_SIZE // 2
                    y = (row - HIDDEN_ROWS) * CELL_SIZE + CELL_SIZE // 2
                    color = COLORS[colors[i]]
                    radius = CELL_SIZE // 2 - 2
                    pygame.draw.circle(surface, color, (x, y), radius)
                    # 高光
                    pygame.draw.circle(surface, (255, 255, 255, 80),
                                       (x - 3, y - 3), radius // 2)

            # 绘制影子（预览落点）
            shadow_row = self.pair.row
            while True:
                test_cells = [(c, shadow_row + 1) if i == 0 else (c, shadow_row + 1)
                              for i, (c, r) in enumerate(cells)]
                # 简化：计算影子位置
                temp_row = shadow_row + 1
                ok = True
                for c, _ in cells:
                    if temp_row >= TOTAL_ROWS or (temp_row >= 0 and self.grid[temp_row][c] is not None):
                        ok = False
                        break
                if not ok:
                    break
                shadow_row = temp_row

            for col, row in cells:
                srow = shadow_row
                if srow >= HIDDEN_ROWS:
                    x = col * CELL_SIZE + CELL_SIZE // 2
                    y = (srow - HIDDEN_ROWS) * CELL_SIZE + CELL_SIZE // 2
                    radius = CELL_SIZE // 2 - 2
                    pygame.draw.circle(surface, (100, 100, 100, 80), (x, y), radius, 2)

        # 绘制侧边面板
        panel_x = GRID_WIDTH
        panel_rect = pygame.Rect(panel_x, 0, SIDE_PANEL, WINDOW_HEIGHT)
        pygame.draw.rect(surface, COLORS['PANEL'], panel_rect)

        font = pygame.font.Font(None, 28)
        small_font = pygame.font.Font(None, 22)

        # 标题
        title = font.render("噗哟噗哟", True, COLORS['TEXT'])
        surface.blit(title, (panel_x + 20, 20))

        # 分数
        score_label = small_font.render("分数", True, COLORS['TEXT'])
        surface.blit(score_label, (panel_x + 20, 70))
        score_text = font.render(str(self.score), True, COLORS['YELLOW'])
        surface.blit(score_text, (panel_x + 20, 95))

        # 等级
        level_label = small_font.render("等级", True, COLORS['TEXT'])
        surface.blit(level_label, (panel_x + 20, 135))
        level_text = font.render(str(self.level), True, COLORS['GREEN'])
        surface.blit(level_text, (panel_x + 20, 160))

        # 连锁数
        chain_label = small_font.render("总连锁", True, COLORS['TEXT'])
        surface.blit(chain_label, (panel_x + 20, 200))
        chain_text = font.render(str(self.total_chains), True, COLORS['BLUE'])
        surface.blit(chain_text, (panel_x + 20, 225))

        # 当前连锁提示
        if self.chain_count > 1:
            chain_flash = font.render(f"{self.chain_count}连锁!", True, COLORS['RED'])
            surface.blit(chain_flash, (panel_x + 20, 270))

        # 操作提示
        controls = [
            "← → 移动",
            "↑ 旋转",
            "↓ 加速",
            "空格 落底",
            "",
            "R 重新开始",
        ]
        y = 330
        for line in controls:
            ctrl = small_font.render(line, True, COLORS['TEXT'])
            surface.blit(ctrl, (panel_x + 20, y))
            y += 25

        # 游戏结束
        if self.game_over:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))

            go_font = pygame.font.Font(None, 56)
            go_text = go_font.render("游戏结束", True, COLORS['RED'])
            go_rect = go_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30))
            surface.blit(go_text, go_rect)

            restart_text = font.render("按 R 重新开始", True, COLORS['TEXT'])
            restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 30))
            surface.blit(restart_text, restart_rect)


def main():
    """主函数"""
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("噗哟噗哟 - Puyo Puyo")
    clock = pygame.time.Clock()

    grid = PuyoGrid()
    running = True

    while running:
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    grid = PuyoGrid()  # 重新开始
                else:
                    grid.handle_key(event.key)

        # 更新
        grid.update()

        # 绘制
        grid.draw(screen)

        # 边框
        pygame.draw.line(screen, COLORS['GRID'],
                         (GRID_WIDTH, 0), (GRID_WIDTH, WINDOW_HEIGHT), 2)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()