"""
海战棋 (Battleship) - 经典战舰对战游戏
Player vs AI 双人回合制海战
"""

import pygame
import random
import sys

# -------------------- 常量配置 --------------------
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600
GRID_SIZE = 10
CELL_SIZE = 40
GRID_OFFSET_X = 50
GRID_OFFSET_Y = 80
INFO_PANEL_X = 550
FPS = 60

# 颜色定义
COLOR_BG = (30, 30, 50)
COLOR_GRID = (100, 130, 200)
COLOR_GRID_LINE = (70, 100, 170)
COLOR_WATER = (40, 60, 120)
COLOR_SHIP = (140, 140, 140)
COLOR_SHIP_PLACING = (180, 180, 100, 180)
COLOR_HIT = (220, 60, 60)
COLOR_MISS = (200, 200, 200)
COLOR_SUNK = (120, 40, 40)
COLOR_TEXT = (240, 240, 255)
COLOR_TITLE = (255, 220, 100)
COLOR_BUTTON = (60, 120, 200)
COLOR_BUTTON_HOVER = (80, 150, 230)
COLOR_BORDER = (150, 180, 255)

# 舰船定义: (名称, 长度)
SHIPS = [
    ("航空母舰", 5),
    ("战列舰", 4),
    ("巡洋舰", 3),
    ("潜艇", 3),
    ("驱逐舰", 2),
]


class Button:
    """按钮组件"""

    def __init__(self, x, y, w, h, text, color=COLOR_BUTTON, hover_color=COLOR_BUTTON_HOVER):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, screen, font):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        pygame.draw.rect(screen, COLOR_BORDER, self.rect, 2, border_radius=6)
        text_surf = font.render(self.text, True, COLOR_TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False


class Ship:
    """舰船类"""

    def __init__(self, name, length):
        self.name = name
        self.length = length
        self.cells = []  # [(row, col), ...]
        self.hits = set()  # 被击中的位置
        self.is_placed = False
        self.horizontal = True  # 水平/垂直方向

    @property
    def is_sunk(self):
        return len(self.hits) == self.length

    def contains(self, row, col):
        return (row, col) in self.cells


class Board:
    """棋盘类"""

    def __init__(self, is_player=True):
        self.is_player = is_player
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        # 0=空, 1=船, 2=命中, 3=未命中, 4=沉没
        self.ships = []
        self.shots = set()  # 已射击的位置

    def can_place_ship(self, ship, row, col, horizontal):
        """检查是否能放置舰船"""
        cells = []
        for i in range(ship.length):
            r = row if horizontal else row + i
            c = col + i if horizontal else col
            if r < 0 or r >= GRID_SIZE or c < 0 or c >= GRID_SIZE:
                return False, []
            if self.grid[r][c] != 0:
                return False, []
            cells.append((r, c))
        return True, cells

    def place_ship(self, ship, row, col, horizontal):
        """放置舰船"""
        ok, cells = self.can_place_ship(ship, row, col, horizontal)
        if not ok:
            return False
        ship.cells = cells
        ship.horizontal = horizontal
        ship.is_placed = True
        self.ships.append(ship)
        for r, c in cells:
            self.grid[r][c] = 1
        return True

    def receive_shot(self, row, col):
        """接收射击，返回结果: 'hit', 'miss', 'sink', 'already'"""
        if (row, col) in self.shots:
            return 'already'
        self.shots.add((row, col))
        if self.grid[row][col] == 1:
            self.grid[row][col] = 2
            # 检查是否有船被击沉
            for ship in self.ships:
                if ship.contains(row, col):
                    ship.hits.add((row, col))
                    if ship.is_sunk:
                        for r, c in ship.cells:
                            self.grid[r][c] = 4
                        return 'sink'
            return 'hit'
        else:
            self.grid[row][col] = 3
            return 'miss'

    @property
    def all_sunk(self):
        return all(ship.is_sunk for ship in self.ships)

    def get_random_placement(self):
        """随机放置所有舰船"""
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.ships = []
        for name, length in SHIPS:
            ship = Ship(name, length)
            placed = False
            attempts = 0
            while not placed and attempts < 1000:
                row = random.randint(0, GRID_SIZE - 1)
                col = random.randint(0, GRID_SIZE - 1)
                horizontal = random.choice([True, False])
                placed = self.place_ship(ship, row, col, horizontal)
                attempts += 1
            if not placed:
                # 如果失败，重试整个棋盘
                return self.get_random_placement()
        return True


class BattleshipGame:
    """海战棋主游戏类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("海战棋 Battleship")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("simhei", 32)
        self.font_medium = pygame.font.SysFont("simhei", 22)
        self.font_small = pygame.font.SysFont("simhei", 16)
        self.running = True

        # 游戏状态
        self.state = 'placement'  # placement, playing, game_over
        self.player_board = Board(is_player=True)
        self.ai_board = Board(is_player=False)
        self.current_turn = 'player'  # player, ai
        self.message = "点击网格放置舰船"
        self.message_timer = 0
        self.animating = False
        self.animation_timer = 0

        # 放置阶段
        self.placing_ship_index = 0
        self.placing_horizontal = True
        self.mouse_grid_pos = None
        self.placement_valid = False

        # AI 智能射击
        self.ai_last_hit = None
        self.ai_targets = []
        self.ai_mode = 'search'  # search, target

        # 按钮
        self.random_btn = Button(GRID_OFFSET_X, GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE + 10, 160, 36, "随机放置")
        self.rotate_btn = Button(GRID_OFFSET_X + 170, GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE + 10, 120, 36, "旋转")
        self.reset_btn = Button(INFO_PANEL_X, 480, 140, 40, "重新开始")

        self._init_ai_board()

    def _init_ai_board(self):
        """初始化AI棋盘"""
        self.ai_board = Board(is_player=False)
        self.ai_board.get_random_placement()

    def _get_grid_pos(self, mouse_pos, offset_x=GRID_OFFSET_X, offset_y=GRID_OFFSET_Y):
        """获取鼠标所在的网格坐标"""
        mx, my = mouse_pos
        col = (mx - offset_x) // CELL_SIZE
        row = (my - offset_y) // CELL_SIZE
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            return row, col
        return None

    def _draw_grid(self, offset_x, offset_y, board, show_ships=True, highlight=None):
        """绘制网格"""
        # 绘制网格背景
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x = offset_x + c * CELL_SIZE
                y = offset_y + r * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

                cell = board.grid[r][c]
                if cell == 0:  # 空
                    color = COLOR_WATER
                elif cell == 1:  # 船
                    color = COLOR_SHIP if show_ships else COLOR_WATER
                elif cell == 2:  # 命中
                    color = COLOR_HIT
                elif cell == 3:  # 未命中
                    color = COLOR_MISS
                elif cell == 4:  # 沉没
                    color = COLOR_SUNK
                else:
                    color = COLOR_WATER

                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, COLOR_GRID_LINE, rect, 1)

                # 命中标记: X
                if cell == 2:
                    cx, cy = x + CELL_SIZE // 2, y + CELL_SIZE // 2
                    s = CELL_SIZE // 4
                    pygame.draw.line(self.screen, (255, 255, 255), (cx - s, cy - s), (cx + s, cy + s), 3)
                    pygame.draw.line(self.screen, (255, 255, 255), (cx + s, cy - s), (cx - s, cy + s), 3)
                # 未命中标记: 点
                elif cell == 3:
                    pygame.draw.circle(self.screen, (100, 100, 100),
                                       (x + CELL_SIZE // 2, y + CELL_SIZE // 2), 4)

        # 高亮显示
        if highlight:
            for r, c in highlight:
                x = offset_x + c * CELL_SIZE
                y = offset_y + r * CELL_SIZE
                pygame.draw.rect(self.screen, (255, 255, 100, 80),
                                 (x, y, CELL_SIZE, CELL_SIZE), 3)

        # 绘制列标签 (A-J)
        for c in range(GRID_SIZE):
            label = chr(ord('A') + c)
            surf = self.font_small.render(label, True, COLOR_TEXT)
            x = offset_x + c * CELL_SIZE + CELL_SIZE // 2 - surf.get_width() // 2
            self.screen.blit(surf, (x, offset_y - 25))

        # 绘制行标签 (1-10)
        for r in range(GRID_SIZE):
            surf = self.font_small.render(str(r + 1), True, COLOR_TEXT)
            y = offset_y + r * CELL_SIZE + CELL_SIZE // 2 - surf.get_height() // 2
            self.screen.blit(surf, (offset_x - 25, y))

        # 绘制网格边框
        pygame.draw.rect(self.screen, COLOR_GRID,
                         (offset_x - 2, offset_y - 2,
                          GRID_SIZE * CELL_SIZE + 4, GRID_SIZE * CELL_SIZE + 4), 3)

    def _draw_placement_preview(self):
        """绘制放置预览"""
        if self.mouse_grid_pos is None:
            return
        row, col = self.mouse_grid_pos
        ship = Ship(*SHIPS[self.placing_ship_index])
        ok, cells = self.player_board.can_place_ship(ship, row, col, self.placing_horizontal)
        self.placement_valid = ok

        color = (100, 255, 100, 100) if ok else (255, 100, 100, 100)
        for r, c in cells:
            if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                x = GRID_OFFSET_X + c * CELL_SIZE
                y = GRID_OFFSET_Y + r * CELL_SIZE
                s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                s.fill(color)
                self.screen.blit(s, (x, y))

    def _draw_info_panel(self):
        """绘制信息面板"""
        x = INFO_PANEL_X
        y = GRID_OFFSET_Y

        # 标题
        title = self.font_large.render("信息面板", True, COLOR_TITLE)
        self.screen.blit(title, (x, y - 30))

        if self.state == 'placement':
            # 当前放置的舰船
            text = self.font_medium.render("放置舰船阶段", True, COLOR_TITLE)
            self.screen.blit(text, (x, y))

            for i, (name, length) in enumerate(SHIPS):
                color = (100, 255, 100) if i < self.placing_ship_index else COLOR_TEXT
                if i == self.placing_ship_index:
                    color = (255, 255, 100)
                done = "✓" if i < self.placing_ship_index else ""
                text = self.font_small.render(f"{name} ({length}格) {done}", True, color)
                self.screen.blit(text, (x, y + 30 + i * 25))

            y += 30 + len(SHIPS) * 25 + 10
            text = self.font_small.render("点击玩家网格放置", True, COLOR_TEXT)
            self.screen.blit(text, (x, y))
            text = self.font_small.render("按 R 键旋转方向", True, COLOR_TEXT)
            self.screen.blit(text, (x, y + 22))

            self.random_btn.draw(self.screen, self.font_small)
            self.rotate_btn.draw(self.screen, self.font_small)

        elif self.state == 'playing':
            turn_text = "你的回合 - 点击AI网格" if self.current_turn == 'player' else "AI思考中..."
            color = (100, 255, 100) if self.current_turn == 'player' else (255, 200, 100)
            text = self.font_medium.render(turn_text, True, color)
            self.screen.blit(text, (x, y))

            y += 40

            # 统计信息
            player_sunk = sum(1 for s in self.player_board.ships if s.is_sunk)
            ai_sunk = sum(1 for s in self.ai_board.ships if s.is_sunk)
            text = self.font_small.render(f"玩家舰船击沉: {player_sunk}/5", True, COLOR_TEXT)
            self.screen.blit(text, (x, y))
            text = self.font_small.render(f"AI舰船击沉: {ai_sunk}/5", True, COLOR_TEXT)
            self.screen.blit(text, (x, y + 25))

            # 剩余舰船
            y += 60
            text = self.font_medium.render("玩家剩余舰船:", True, COLOR_TITLE)
            self.screen.blit(text, (x, y))
            for i, ship in enumerate(self.player_board.ships):
                status = "沉没" if ship.is_sunk else "存活"
                color = (200, 80, 80) if ship.is_sunk else (80, 200, 80)
                t = self.font_small.render(f"{ship.name}: {status}", True, color)
                self.screen.blit(t, (x, y + 25 + i * 20))

        elif self.state == 'game_over':
            text = self.font_large.render("游戏结束!", True, COLOR_TITLE)
            self.screen.blit(text, (x, y))
            y += 45
            if self.player_board.all_sunk:
                text = self.font_medium.render("AI 获胜!", True, (255, 100, 100))
            else:
                text = self.font_medium.render("玩家 获胜!", True, (100, 255, 100))
            self.screen.blit(text, (x, y))
            self.reset_btn.draw(self.screen, self.font_small)

        # 消息显示
        if self.message and self.message_timer > 0:
            msg = self.font_small.render(self.message, True, (255, 255, 100))
            self.screen.blit(msg, (x, y + 120))

    def _draw_labels(self):
        """绘制棋盘标签"""
        # 玩家棋盘标签
        label = self.font_medium.render("玩家海域", True, (100, 200, 255))
        self.screen.blit(label, (GRID_OFFSET_X, GRID_OFFSET_Y - 50))

        # AI棋盘标签
        label = self.font_medium.render("AI海域", True, (255, 100, 100))
        ai_offset_x = GRID_OFFSET_X + GRID_SIZE * CELL_SIZE + 80
        self.screen.blit(label, (ai_offset_x, GRID_OFFSET_Y - 50))

    def _handle_placement(self, event):
        """处理放置阶段事件"""
        self.mouse_grid_pos = self._get_grid_pos(event.pos)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.placing_horizontal = not self.placing_horizontal

        if event.type == pygame.MOUSEBUTTONDOWN:
            # 按钮事件
            if self.random_btn.handle_event(event):
                self.player_board = Board(is_player=True)
                self.player_board.get_random_placement()
                self.placing_ship_index = len(SHIPS)
                self.state = 'playing'
                self.current_turn = 'player'
                self.message = "所有舰船已放置！点击AI网格攻击"
                self.message_timer = 120
                return

            if self.rotate_btn.handle_event(event):
                self.placing_horizontal = not self.placing_horizontal
                return

            # 点击网格放置
            pos = self._get_grid_pos(event.pos)
            if pos:
                row, col = pos
                ship = Ship(*SHIPS[self.placing_ship_index])
                if self.player_board.place_ship(ship, row, col, self.placing_horizontal):
                    self.placing_ship_index += 1
                    if self.placing_ship_index >= len(SHIPS):
                        self.state = 'playing'
                        self.current_turn = 'player'
                        self.message = "所有舰船已放置！点击AI网格攻击"
                        self.message_timer = 120
                else:
                    self.message = "无法在此放置，请选择其他位置"
                    self.message_timer = 60

    def _ai_think(self):
        """AI 决策 - 智能射击"""
        if not self.ai_targets:
            # 搜索模式: 随机射击
            available = []
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if (r, c) not in self.player_board.shots:
                        available.append((r, c))
            if not available:
                return None
            return random.choice(available)
        else:
            # 目标模式: 追踪命中
            return self.ai_targets.pop(0)

    def _ai_shot(self):
        """AI 执行射击"""
        pos = self._ai_think()
        if pos is None:
            return
        row, col = pos
        result = self.player_board.receive_shot(row, col)

        if result == 'hit':
            self.ai_last_hit = (row, col)
            # 添加相邻位置作为目标（优先）
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                    if (nr, nc) not in self.player_board.shots:
                        self.ai_targets.insert(0, (nr, nc))
            self.message = f"AI 击中了你! ({row+1}, {chr(ord('A')+col)})"
        elif result == 'sink':
            self.ai_last_hit = None
            self.ai_targets = [t for t in self.ai_targets
                               if not any(s.contains(t[0], t[1])
                                          for s in self.player_board.ships if s.is_sunk)]
            self.message = f"AI 击沉了你的舰船! ({row+1}, {chr(ord('A')+col)})"
        elif result == 'miss':
            self.message = f"AI 未命中 ({row+1}, {chr(ord('A')+col)})"
        elif result == 'already':
            pass

        self.message_timer = 90

        # 检查是否游戏结束
        if self.player_board.all_sunk:
            self.state = 'game_over'
            self.message = "AI 获胜!"
            return

        self.current_turn = 'player'

    def _handle_playing(self, event):
        """处理游戏阶段事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.current_turn != 'player':
                return

            # AI棋盘位置
            ai_offset_x = GRID_OFFSET_X + GRID_SIZE * CELL_SIZE + 80
            pos = self._get_grid_pos(event.pos, offset_x=ai_offset_x)
            if pos is None:
                return

            row, col = pos
            if (row, col) in self.ai_board.shots:
                self.message = "这个位置已经攻击过了!"
                self.message_timer = 60
                return

            # 执行射击
            result = self.ai_board.receive_shot(row, col)
            if result == 'hit':
                self.message = f"命中! ({row+1}, {chr(ord('A')+col)})"
            elif result == 'sink':
                self.message = f"击沉! ({row+1}, {chr(ord('A')+col)})"
            elif result == 'miss':
                self.message = f"未命中 ({row+1}, {chr(ord('A')+col)})"
            self.message_timer = 90

            # 检查是否游戏结束
            if self.ai_board.all_sunk:
                self.state = 'game_over'
                self.message = "恭喜! 你击沉了所有AI舰船!"
                return

            # AI回合
            self.current_turn = 'ai'

    def run(self):
        """主循环"""
        while self.running:
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()

                if self.state == 'placement':
                    self._handle_placement(event)
                elif self.state == 'playing':
                    self._handle_playing(event)
                elif self.state == 'game_over':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.reset_btn.handle_event(event):
                            self.__init__()
                            self.run()
                            return

                # 通用按钮事件
                if event.type == pygame.MOUSEMOTION:
                    self.random_btn.handle_event(event)
                    self.rotate_btn.handle_event(event)
                    self.reset_btn.handle_event(event)

            # AI 自动回合
            if self.state == 'playing' and self.current_turn == 'ai':
                pygame.time.wait(600)
                self._ai_shot()

            # 绘制
            self.screen.fill(COLOR_BG)

            ai_offset_x = GRID_OFFSET_X + GRID_SIZE * CELL_SIZE + 80

            # 绘制玩家棋盘
            if self.state == 'placement':
                self._draw_grid(GRID_OFFSET_X, GRID_OFFSET_Y, self.player_board, show_ships=True)
                self._draw_placement_preview()
            else:
                self._draw_grid(GRID_OFFSET_X, GRID_OFFSET_Y, self.player_board, show_ships=True)

            # 绘制AI棋盘
            self._draw_grid(ai_offset_x, GRID_OFFSET_Y, self.ai_board, show_ships=False)

            # 绘制标签和信息
            self._draw_labels()
            self._draw_info_panel()

            # 移除消息计时
            if self.message_timer > 0:
                self.message_timer -= 1

            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    game = BattleshipGame()
    game.run()