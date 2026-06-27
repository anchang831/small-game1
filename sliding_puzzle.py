"""
数字华容道 (Sliding Puzzle / 15-Puzzle)
一个经典的滑动拼图游戏，你需要将打乱的数字方块按顺序排列。
使用鼠标点击与空白格相邻的方块进行滑动。

游戏规则：
- 4x4 网格，包含 1-15 的数字方块和一个空白格
- 点击空白格相邻的方块，它会滑动到空白位置
- 目标：将所有数字按 1 到 15 的顺序从左到右、从上到下排列
- 空白格最终应在右下角

Controls:
- 鼠标点击：滑动方块
- R 键：重新洗牌
- S 键：一键求解（自动演示）
- ESC：退出游戏
"""

import pygame
import random
import sys
import time
from copy import deepcopy

# -------------------- 常量配置 --------------------
SCREEN_WIDTH = 540
SCREEN_HEIGHT = 660
GRID_SIZE = 4          # 4x4 网格
TILE_SIZE = 110        # 每个方块的像素大小
MARGIN = 40            # 网格边距
GAP = 6                # 方块之间的间距

# 计算网格实际占据的尺寸
GRID_PIXEL = GRID_SIZE * TILE_SIZE + (GRID_SIZE - 1) * GAP
GRID_OFFSET_X = (SCREEN_WIDTH - GRID_PIXEL) // 2
GRID_OFFSET_Y = MARGIN + 80  # 顶部留出标题区域

# 颜色定义
COLORS = {
    'bg': (30, 30, 40),
    'panel': (45, 45, 55),
    'tile': (70, 130, 180),
    'tile_hover': (100, 160, 210),
    'tile_text': (255, 255, 255),
    'empty': (35, 35, 45),
    'title': (200, 200, 220),
    'info': (180, 180, 200),
    'win_bg': (50, 200, 100, 180),
    'win_text': (255, 255, 255),
    'button': (100, 100, 140),
    'button_hover': (130, 130, 170),
    'move_text': (150, 150, 180),
    'timer_text': (150, 150, 180),
}

# -------------------- 滑动拼图核心逻辑 --------------------
class SlidingPuzzle:
    """管理拼图的状态逻辑，与显示无关"""

    def __init__(self, grid_size=4):
        self.grid_size = grid_size
        self.total_tiles = grid_size * grid_size
        self.reset()

    def reset(self):
        """初始化解谜状态"""
        # 创建有序状态: 1..15, 0(空白)
        self.solved_state = list(range(1, self.total_tiles)) + [0]
        self.board = self.solved_state[:]
        self.empty_pos = self.total_tiles - 1  # 空白在右下角
        self.move_count = 0
        self.shuffle()

    def shuffle(self):
        """通过大量合法移动来洗牌，确保有解"""
        self.board = self.solved_state[:]
        self.empty_pos = self.total_tiles - 1
        self.move_count = 0

        moves = 200
        last_move = -1
        for _ in range(moves):
            # 获取空白格的所有邻居位置
            neighbors = self._get_neighbors(self.empty_pos)
            # 避免撤销上一步操作
            choices = [n for n in neighbors if n != last_move]
            if not choices:
                choices = neighbors
            target = random.choice(choices)
            # 交换空白和目标位置
            self.board[self.empty_pos], self.board[target] = \
                self.board[target], self.board[self.empty_pos]
            last_move = self.empty_pos
            self.empty_pos = target

    def _get_neighbors(self, pos):
        """返回位置 pos 在网格中的邻居索引列表"""
        row, col = divmod(pos, self.grid_size)
        neighbors = []
        if row > 0:
            neighbors.append(pos - self.grid_size)  # 上
        if row < self.grid_size - 1:
            neighbors.append(pos + self.grid_size)  # 下
        if col > 0:
            neighbors.append(pos - 1)  # 左
        if col < self.grid_size - 1:
            neighbors.append(pos + 1)  # 右
        return neighbors

    def is_adjacent(self, pos):
        """判断位置 pos 是否与空白格相邻"""
        return pos in self._get_neighbors(self.empty_pos)

    def slide(self, pos):
        """尝试滑动位置 pos 的方块，返回是否成功"""
        if not self.is_adjacent(pos):
            return False
        # 交换
        self.board[self.empty_pos], self.board[pos] = \
            self.board[pos], self.board[self.empty_pos]
        self.empty_pos = pos
        self.move_count += 1
        return True

    def is_solved(self):
        """检查是否已拼好"""
        return self.board == self.solved_state

    def get_tile_at(self, pos):
        """返回位置 pos 的方块数字（0 表示空白）"""
        return self.board[pos]

    def solve_step(self):
        """
        通过 BFS 找到最优解的下一步，返回应该滑动到空白位置的方块位置。
        如果已经完成，返回 None。
        """
        if self.is_solved():
            return None

        # BFS 搜索最优解
        start_state = tuple(self.board)
        target_state = tuple(self.solved_state)

        if start_state == target_state:
            return None

        # BFS 找最短路径
        visited = {start_state: None}  # state -> (prev_state, move_pos)
        queue = [start_state]
        found = False

        while queue and not found:
            current = queue.pop(0)
            # 找到当前状态中空白的位置
            empty_idx = current.index(0)
            row, col = divmod(empty_idx, self.grid_size)

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size:
                    neighbor_idx = nr * self.grid_size + nc
                    # 生成新状态：交换空白和邻居
                    lst = list(current)
                    lst[empty_idx], lst[neighbor_idx] = lst[neighbor_idx], lst[empty_idx]
                    new_state = tuple(lst)

                    if new_state not in visited:
                        visited[new_state] = (current, neighbor_idx)
                        if new_state == target_state:
                            found = True
                            break
                        queue.append(new_state)

        if not found:
            return None

        # 回溯找到第一步
        state = target_state
        while visited[state][0] != start_state:
            state = visited[state][0]

        # visited[state] = (start_state, move_pos)
        _, move_pos = visited[state]
        return move_pos


# -------------------- 游戏主类 --------------------
class SlidingPuzzleGame:
    """管理游戏窗口、事件循环和渲染"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("数字华容道 - Sliding Puzzle")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 42)
        self.font_small = pygame.font.Font(None, 30)
        self.font_title = pygame.font.Font(None, 56)

        self.puzzle = SlidingPuzzle(GRID_SIZE)
        self.start_time = time.time()
        self.running = True
        self.won = False
        self.win_time = 0
        self.hovered_tile = -1  # 当前鼠标悬停的方块位置
        self.solving = False     # 是否处于自动求解模式
        self.solve_moves = []    # 求解路径
        self.solve_timer = 0     # 求解动画计时器
        self.solve_index = 0     # 当前求解到第几步

        # 新游戏按钮矩形
        self.btn_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT - 55, 160, 40
        )

    def handle_events(self):
        """处理用户输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    self._reset_game()
                elif event.key == pygame.K_s and not self.won and not self.solving:
                    self._start_solve()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # 检查新游戏按钮
                if self.btn_rect.collidepoint(mx, my):
                    self._reset_game()
                    continue

                if self.solving:
                    continue

                # 检查点击的是哪个方块
                pos = self._pos_from_mouse(mx, my)
                if pos is not None and pos != self.puzzle.empty_pos:
                    if self.puzzle.slide(pos):
                        if self.puzzle.is_solved():
                            self.won = True
                            self.win_time = time.time() - self.start_time

            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                pos = self._pos_from_mouse(mx, my)
                self.hovered_tile = pos if pos is not None else -1

    def _reset_game(self):
        """重置游戏"""
        self.puzzle.reset()
        self.start_time = time.time()
        self.won = False
        self.solving = False
        self.solve_moves = []
        self.solve_index = 0

    def _start_solve(self):
        """开始自动求解"""
        self.solving = True
        self.solve_moves = []
        self.solve_index = 0
        self.solve_timer = 0

        # 保存当前状态用于求解，但不在求解过程中改变 state
        self._solve_state = deepcopy(self.puzzle)

    def _pos_from_mouse(self, mx, my):
        """将鼠标坐标转换为网格位置，如果不在网格内返回 None"""
        # 计算相对网格的坐标
        rx = mx - GRID_OFFSET_X
        ry = my - GRID_OFFSET_Y
        if rx < 0 or ry < 0:
            return None

        col = rx // (TILE_SIZE + GAP)
        row = ry // (TILE_SIZE + GAP)
        if col >= GRID_SIZE or row >= GRID_SIZE:
            return None

        # 检查是否在方块区域内（排除间隙）
        tile_x = col * (TILE_SIZE + GAP)
        tile_y = row * (TILE_SIZE + GAP)
        if rx - tile_x > TILE_SIZE or ry - tile_y > TILE_SIZE:
            return None

        return row * GRID_SIZE + col

    def update(self):
        """更新游戏状态（主要用于求解动画）"""
        if self.solving and self.solve_moves:
            self.solve_timer += 1
            if self.solve_timer > 8:  # 每 8 帧执行一步
                self.solve_timer = 0
                if self.solve_index < len(self.solve_moves):
                    move_pos = self.solve_moves[self.solve_index]
                    self.puzzle.slide(move_pos)
                    self.solve_index += 1
                    if self.puzzle.is_solved():
                        self.won = True
                        self.win_time = time.time() - self.start_time
                        self.solving = False
                        self.solve_moves = []

    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(COLORS['bg'])

        # 绘制标题
        title_text = self.font_title.render("数字华容道", True, COLORS['title'])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 28))
        self.screen.blit(title_text, title_rect)

        # 绘制副标题
        sub_text = self.font_small.render("点击相邻方块滑动 · R重开 · S求解", True, COLORS['info'])
        sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH // 2, 62))
        self.screen.blit(sub_text, sub_rect)

        # 绘制信息面板（步数和时间）
        elapsed = time.time() - self.start_time
        mins, secs = divmod(int(elapsed), 60)
        time_str = f"{mins:02d}:{secs:02d}"
        info_text = self.font_small.render(
            f"步数: {self.puzzle.move_count}   时间: {time_str}",
            True, COLORS['info']
        )
        info_rect = info_text.get_rect(center=(SCREEN_WIDTH // 2, 98))
        self.screen.blit(info_text, info_rect)

        # 绘制网格背景
        panel_rect = pygame.Rect(
            GRID_OFFSET_X - 10, GRID_OFFSET_Y - 10,
            GRID_PIXEL + 20, GRID_PIXEL + 20
        )
        pygame.draw.rect(self.screen, COLORS['panel'], panel_rect, border_radius=12)

        # 绘制每个方块
        for i in range(self.puzzle.total_tiles):
            tile_value = self.puzzle.board[i]
            row, col = divmod(i, GRID_SIZE)
            x = GRID_OFFSET_X + col * (TILE_SIZE + GAP)
            y = GRID_OFFSET_Y + row * (TILE_SIZE + GAP)

            if tile_value == 0:
                # 空白格
                pygame.draw.rect(
                    self.screen, COLORS['empty'],
                    (x, y, TILE_SIZE, TILE_SIZE), border_radius=8
                )
            else:
                # 数字方块
                color = COLORS['tile_hover'] if i == self.hovered_tile and not self.solving \
                    else COLORS['tile']

                # 根据数字大小变化色调（让方块更有层次感）
                hue_factor = tile_value / (self.puzzle.total_tiles - 1)
                r = int(50 + hue_factor * 80)
                g = int(100 + hue_factor * 60)
                b = int(180 - hue_factor * 60)
                tile_color = (r, g, b)

                if i == self.hovered_tile and not self.solving:
                    tile_color = (min(r + 30, 255), min(g + 30, 255), min(b + 30, 255))

                pygame.draw.rect(
                    self.screen, tile_color,
                    (x, y, TILE_SIZE, TILE_SIZE), border_radius=8
                )

                # 方块内阴影（增加立体感）
                inner_rect = pygame.Rect(x + 4, y + 4, TILE_SIZE - 8, TILE_SIZE - 8)
                pygame.draw.rect(
                    self.screen, (tile_color[0] // 2, tile_color[1] // 2, tile_color[2] // 2),
                    inner_rect, border_radius=6, width=1
                )

                # 数字文字
                text = self.font_large.render(str(tile_value), True, COLORS['tile_text'])
                text_rect = text.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))
                self.screen.blit(text, text_rect)

        # 绘制新游戏按钮
        mouse_pos = pygame.mouse.get_pos()
        btn_hover = self.btn_rect.collidepoint(mouse_pos)
        btn_color = COLORS['button_hover'] if btn_hover else COLORS['button']
        pygame.draw.rect(self.screen, btn_color, self.btn_rect, border_radius=8)
        btn_text = self.font_small.render("新游戏 (R)", True, COLORS['tile_text'])
        btn_text_rect = btn_text.get_rect(center=self.btn_rect.center)
        self.screen.blit(btn_text, btn_text_rect)

        # 胜利画面
        if self.won:
            self._draw_win_overlay()

        pygame.display.flip()

    def _draw_win_overlay(self):
        """绘制胜利弹窗"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # 胜利面板
        panel_w, panel_h = 380, 220
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2 - 30
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(self.screen, (50, 180, 100), panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, (40, 150, 80), panel_rect, border_radius=16, width=3)

        # 庆祝文字
        texts = [
            ("🎉 恭喜通关！", self.font_title, (255, 255, 220), 40),
            (f"步数: {self.puzzle.move_count}  |  用时: {self._format_time(self.win_time)}",
             self.font_small, (255, 255, 255), 100),
            ("按 R 键开始新游戏", self.font_small, (200, 255, 220), 155),
        ]

        for text, font, color, y_offset in texts:
            rendered = font.render(text, True, color)
            rect = rendered.get_rect(center=(SCREEN_WIDTH // 2, panel_y + y_offset))
            self.screen.blit(rendered, rect)

    @staticmethod
    def _format_time(seconds):
        mins, secs = divmod(int(seconds), 60)
        return f"{mins:02d}:{secs:02d}"

    def run(self):
        """主游戏循环"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

            # 如果是求解模式，每帧计算下一步
            if self.solving and not self.solve_moves:
                # 用备份状态做 BFS
                solve_puzzle = self._solve_state
                # 获取下一步
                next_move = solve_puzzle.solve_step()
                if next_move is not None:
                    # 执行一步移动并记录
                    solve_puzzle.slide(next_move)
                    # 这个移动是反向的：记录空白应该移到的位置
                    self.solve_moves.append(
                        self.puzzle.empty_pos
                    )
                    # 更新当前拼图状态
                    self.puzzle.slide(self.puzzle.empty_pos)  # 同步移动
                    self.solve_index += 1
                    if self.puzzle.is_solved():
                        self.won = True
                        self.win_time = time.time() - self.start_time
                        self.solving = False
                        self.solve_moves = []
                else:
                    self.solving = False

        pygame.quit()
        sys.exit()


# -------------------- 程序入口 --------------------
def main():
    """游戏启动入口"""
    game = SlidingPuzzleGame()
    game.run()


if __name__ == "__main__":
    main()