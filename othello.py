"""
黑白棋 (Othello/Reversi) - 经典双人策略棋盘游戏
==============================================
规则:
  - 8x8 棋盘，双方轮流落子
  - 黑棋先手，必须夹住对方棋子才能翻转
  - 若某方无合法位置则跳过，双方均无法落子时游戏结束
  - 棋子多者获胜

操作:
  - 鼠标点击落子
  - 空格键重新开始
  - ESC 退出
"""

import pygame
import sys

# ─── 常量定义 ───────────────────────────────────────────────
BOARD_SIZE = 8           # 棋盘 8x8
CELL_SIZE = 60           # 每格像素
MARGIN = 40              # 边距
INFO_HEIGHT = 60         # 底部信息栏高度

WIDTH = BOARD_SIZE * CELL_SIZE + MARGIN * 2
HEIGHT = BOARD_SIZE * CELL_SIZE + MARGIN * 2 + INFO_HEIGHT

# 颜色 (RGB)
COLOR_BG = (34, 139, 34)          # 棋盘背景(森林绿)
COLOR_BOARD = (0, 100, 0)         # 棋盘格子(深绿)
COLOR_LINE = (0, 80, 0)           # 网格线
COLOR_BLACK = (30, 30, 30)        # 黑子
COLOR_WHITE = (240, 240, 240)     # 白子
COLOR_HINT = (255, 255, 100)      # 提示点
COLOR_INFO_BG = (50, 50, 50)      # 信息栏背景
COLOR_TEXT = (255, 255, 255)      # 文字
COLOR_TEXT_SHADOW = (200, 200, 200)

# 棋子颜色标识
EMPTY = 0
BLACK = 1
WHITE = 2

FPS = 60


class Othello:
    """黑白棋核心逻辑"""

    # 八个方向: 上、下、左、右、左上、右上、左下、右下
    DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1),
                  (-1, -1), (-1, 1), (1, -1), (1, 1)]

    def __init__(self):
        self.reset()

    def reset(self):
        """初始化棋盘到标准开局"""
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        mid = BOARD_SIZE // 2
        self.board[mid - 1][mid - 1] = WHITE
        self.board[mid][mid] = WHITE
        self.board[mid - 1][mid] = BLACK
        self.board[mid][mid - 1] = BLACK
        self.current_player = BLACK
        self.game_over = False
        self.winner = None

    def is_valid(self, row, col):
        """检查坐标是否在棋盘内"""
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def get_flippable(self, row, col):
        """
        返回在 (row, col) 落子后可以翻转的对手棋子坐标列表
        如果返回空列表，表示该位置无效
        """
        if not self.is_valid(row, col) or self.board[row][col] != EMPTY:
            return []

        opponent = WHITE if self.current_player == BLACK else BLACK
        flippable = []

        for dr, dc in self.DIRECTIONS:
            r, c = row + dr, col + dc
            temp = []
            while self.is_valid(r, c) and self.board[r][c] == opponent:
                temp.append((r, c))
                r += dr
                c += dc
            # 必须是以己方棋子收尾
            if self.is_valid(r, c) and self.board[r][c] == self.current_player and temp:
                flippable.extend(temp)

        return flippable

    def get_valid_moves(self):
        """获取当前玩家的所有合法落子位置"""
        moves = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == EMPTY and self.get_flippable(r, c):
                    moves.append((r, c))
        return moves

    def make_move(self, row, col):
        """在指定位置落子，返回是否成功"""
        flippable = self.get_flippable(row, col)
        if not flippable:
            return False

        # 落子
        self.board[row][col] = self.current_player
        # 翻转棋子
        for r, c in flippable:
            self.board[r][c] = self.current_player

        # 切换玩家
        opponent = WHITE if self.current_player == BLACK else BLACK
        self.current_player = opponent

        # 检查对手是否有合法走法
        if not self.get_valid_moves():
            # 对手无棋可走，换回当前玩家
            self.current_player = opponent
            if not self.get_valid_moves():
                # 双方都无法走，游戏结束
                self.game_over = True
                self._determine_winner()

        return True

    def _determine_winner(self):
        """计算最终胜负"""
        black_count = sum(row.count(BLACK) for row in self.board)
        white_count = sum(row.count(WHITE) for row in self.board)
        if black_count > white_count:
            self.winner = BLACK
        elif white_count > black_count:
            self.winner = WHITE
        else:
            self.winner = None  # 平局

    def get_score(self):
        """返回 (黑子数, 白子数)"""
        black = sum(row.count(BLACK) for row in self.board)
        white = sum(row.count(WHITE) for row in self.board)
        return black, white

    def has_valid_moves(self, player=None):
        """指定玩家是否有合法走法"""
        if player is None:
            player = self.current_player
        saved = self.current_player
        self.current_player = player
        moves = self.get_valid_moves()
        self.current_player = saved
        return len(moves) > 0


class Game:
    """游戏渲染与事件处理"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("黑白棋 (Othello)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simsun, arial, sans-serif", 24)
        self.font_big = pygame.font.SysFont("simsun, arial, sans-serif", 32)
        self.othello = Othello()
        self.hint_moves = self.othello.get_valid_moves()

    def board_to_screen(self, row, col):
        """将棋盘坐标转换为屏幕像素坐标"""
        x = MARGIN + col * CELL_SIZE
        y = MARGIN + row * CELL_SIZE
        return x, y

    def screen_to_board(self, pos):
        """将屏幕像素坐标转换为棋盘坐标"""
        x, y = pos
        col = (x - MARGIN) // CELL_SIZE
        row = (y - MARGIN) // CELL_SIZE
        if self.othello.is_valid(row, col):
            return row, col
        return None, None

    def draw_board(self):
        """绘制棋盘"""
        self.screen.fill(COLOR_BG)

        # 绘制网格线
        for i in range(BOARD_SIZE + 1):
            x = MARGIN + i * CELL_SIZE
            pygame.draw.line(self.screen, COLOR_LINE,
                             (x, MARGIN), (x, MARGIN + BOARD_SIZE * CELL_SIZE), 2)
            y = MARGIN + i * CELL_SIZE
            pygame.draw.line(self.screen, COLOR_LINE,
                             (MARGIN, y), (MARGIN + BOARD_SIZE * CELL_SIZE, y), 2)

        # 绘制所有棋子
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                piece = self.othello.board[r][c]
                if piece == EMPTY:
                    continue
                cx, cy = self.board_to_screen(r, c)
                center = (cx + CELL_SIZE // 2, cy + CELL_SIZE // 2)
                color = COLOR_BLACK if piece == BLACK else COLOR_WHITE
                radius = CELL_SIZE // 2 - 4
                pygame.draw.circle(self.screen, color, center, radius)
                # 白子加边框
                if piece == WHITE:
                    pygame.draw.circle(self.screen, (180, 180, 180), center, radius, 2)

        # 绘制合法落子提示
        for r, c in self.hint_moves:
            cx, cy = self.board_to_screen(r, c)
            center = (cx + CELL_SIZE // 2, cy + CELL_SIZE // 2)
            pygame.draw.circle(self.screen, COLOR_HINT, center, 6)

        # 绘制信息栏
        info_rect = pygame.Rect(0, HEIGHT - INFO_HEIGHT, WIDTH, INFO_HEIGHT)
        pygame.draw.rect(self.screen, COLOR_INFO_BG, info_rect)

        black, white = self.othello.get_score()
        turn_text = "游戏结束" if self.othello.game_over else \
            f"{'黑棋' if self.othello.current_player == BLACK else '白棋'}回合"

        # 颜色指示器
        if not self.othello.game_over:
            indicator_color = COLOR_BLACK if self.othello.current_player == BLACK else COLOR_WHITE
            pygame.draw.circle(self.screen, indicator_color, (25, HEIGHT - INFO_HEIGHT // 2), 10)
            if self.othello.current_player == WHITE:
                pygame.draw.circle(self.screen, (180, 180, 180), (25, HEIGHT - INFO_HEIGHT // 2), 10, 2)

        text1 = self.font.render(turn_text, True, COLOR_TEXT)
        text2 = self.font.render(f"● {black}  ○ {white}", True, COLOR_TEXT)
        text3 = self.font.render("空格:重开  ESC:退出", True, COLOR_TEXT_SHADOW)

        self.screen.blit(text1, (60, HEIGHT - INFO_HEIGHT + 8))
        self.screen.blit(text2, (60, HEIGHT - INFO_HEIGHT + 32))
        self.screen.blit(text3, (WIDTH - 220, HEIGHT - INFO_HEIGHT + 16))

        # 显示获胜信息
        if self.othello.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))

            if self.othello.winner is None:
                msg = f"平局!  黑 {black} : {white} 白"
            else:
                winner_name = "黑棋" if self.othello.winner == BLACK else "白棋"
                msg = f"{winner_name}获胜!  黑 {black} : {white} 白"
            text = self.font_big.render(msg, True, (255, 255, 100))
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
            self.screen.blit(text, text_rect)

            hint = self.font.render("按空格重新开始", True, COLOR_TEXT)
            hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            self.screen.blit(hint, hint_rect)

    def handle_click(self, pos):
        """处理鼠标点击落子"""
        if self.othello.game_over:
            return

        row, col = self.screen_to_board(pos)
        if row is None:
            return

        if self.othello.make_move(row, col):
            self.hint_moves = self.othello.get_valid_moves()

    def handle_key(self, key):
        """处理按键事件"""
        if key == pygame.K_SPACE:
            self.othello.reset()
            self.hint_moves = self.othello.get_valid_moves()
        elif key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()

    def run(self):
        """主循环"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)

            self.draw_board()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()