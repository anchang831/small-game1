"""
井字棋 (Tic Tac Toe) - 玩家 vs AI (Minimax算法)
==============================================
Date: 2026-08-30
- 3x3 棋盘，玩家执 X，AI 执 O
- AI 使用 Minimax 算法，永远不输
- 鼠标点击落子，按 R 键重新开始
- 记分牌显示玩家/AI/平局分数
"""

import pygame
import sys
import random

# -------------------- 常量 --------------------
WIDTH, HEIGHT = 600, 700
BOARD_SIZE = 3
CELL_SIZE = 180
BOARD_OFFSET = 50          # 棋盘上边距
GRID_COLOR = (60, 60, 60)
BG_COLOR = (28, 28, 38)
LINE_COLOR = (80, 80, 100)
X_COLOR = (80, 200, 255)
O_COLOR = (255, 120, 120)
TEXT_COLOR = (220, 220, 230)
HIGHLIGHT_COLOR = (50, 50, 70)
FPS = 60
WIN_LINE_WIDTH = 8

# 牌面符号
EMPTY = 0
PLAYER = 1   # X
AI_PLAYER = 2  # O


class TicTacToe:
    """井字棋游戏主类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("井字棋 Tic Tac Toe - AI对手")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simhei", 48)
        self.small_font = pygame.font.SysFont("simhei", 28)
        self.big_font = pygame.font.SysFont("simhei", 60)

        self.reset()

    def reset(self):
        """重置棋盘和状态"""
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_player = PLAYER  # 玩家先手
        self.game_over = False
        self.winner = None          # None=未结束, 0=平局, 1=玩家, 2=AI
        self.win_line = None        # 胜利连线位置
        self.scores = [0, 0, 0]     # [玩家, AI, 平局]
        self.message = "你的回合 (X) - 点击格子落子"
        self.animating = False
        self.animation_timer = 0

    # ---------- 棋盘逻辑 ----------
    def is_valid_move(self, row, col):
        return self.board[row][col] == EMPTY

    def make_move(self, row, col, player):
        self.board[row][col] = player

    def undo_move(self, row, col):
        self.board[row][col] = EMPTY

    def get_empty_cells(self):
        cells = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == EMPTY:
                    cells.append((r, c))
        return cells

    def check_winner(self):
        """检查胜负，返回 (获胜者, 连线位置)"""
        # 行
        for r in range(BOARD_SIZE):
            if self.board[r][0] != EMPTY and \
               self.board[r][0] == self.board[r][1] == self.board[r][2]:
                return self.board[r][0], [(r, 0), (r, 2)]

        # 列
        for c in range(BOARD_SIZE):
            if self.board[0][c] != EMPTY and \
               self.board[0][c] == self.board[1][c] == self.board[2][c]:
                return self.board[0][c], [(0, c), (2, c)]

        # 对角线
        if self.board[0][0] != EMPTY and \
           self.board[0][0] == self.board[1][1] == self.board[2][2]:
            return self.board[0][0], [(0, 0), (2, 2)]

        if self.board[0][2] != EMPTY and \
           self.board[0][2] == self.board[1][1] == self.board[2][0]:
            return self.board[0][2], [(0, 2), (2, 0)]

        # 平局
        if len(self.get_empty_cells()) == 0:
            return 0, None  # 平局

        return None, None  # 游戏继续

    # ---------- Minimax AI ----------
    def minimax(self, board, depth, is_maximizing, alpha, beta):
        """
        Minimax 算法 + Alpha-Beta 剪枝
        AI 是最大化玩家 (O=2)，玩家是最小化玩家 (X=1)
        """
        winner, _ = self.check_winner()
        if winner == AI_PLAYER:
            return 10 - depth  # AI 赢，越快越好
        if winner == PLAYER:
            return depth - 10  # 玩家赢，越慢越好
        if winner == 0:
            return 0  # 平局

        if is_maximizing:
            best = -float('inf')
            for r, c in self.get_empty_cells():
                self.board[r][c] = AI_PLAYER
                score = self.minimax(self.board, depth + 1, False, alpha, beta)
                self.board[r][c] = EMPTY
                best = max(best, score)
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return best
        else:
            best = float('inf')
            for r, c in self.get_empty_cells():
                self.board[r][c] = PLAYER
                score = self.minimax(self.board, depth + 1, True, alpha, beta)
                self.board[r][c] = EMPTY
                best = min(best, score)
                beta = min(beta, best)
                if beta <= alpha:
                    break
            return best

    def ai_move(self):
        """AI 选择最佳落子位置"""
        best_score = -float('inf')
        best_moves = []

        for r, c in self.get_empty_cells():
            self.board[r][c] = AI_PLAYER
            score = self.minimax(self.board, 0, False, -float('inf'), float('inf'))
            self.board[r][c] = EMPTY

            if score > best_score:
                best_score = score
                best_moves = [(r, c)]
            elif score == best_score:
                best_moves.append((r, c))

        # 在相同评分中随机选择
        return random.choice(best_moves) if best_moves else None

    # ---------- 游戏流程 ----------
    def handle_click(self, pos):
        if self.game_over or self.current_player != PLAYER:
            return

        x, y = pos
        # 计算点击的格子
        board_x = (WIDTH - CELL_SIZE * BOARD_SIZE) // 2
        board_y = BOARD_OFFSET

        col = (x - board_x) // CELL_SIZE
        row = (y - board_y) // CELL_SIZE

        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            if self.is_valid_move(row, col):
                # 玩家落子
                self.make_move(row, col, PLAYER)
                self.current_player = AI_PLAYER

                # 检查结果
                winner, win_line = self.check_winner()
                if winner is not None:
                    self._handle_game_end(winner, win_line)
                else:
                    self.message = "AI 思考中 (O) ..."
                    # AI 走棋
                    move = self.ai_move()
                    if move:
                        ai_row, ai_col = move
                        self.make_move(ai_row, ai_col, AI_PLAYER)
                        self.current_player = PLAYER

                        winner, win_line = self.check_winner()
                        if winner is not None:
                            self._handle_game_end(winner, win_line)
                        else:
                            self.message = "你的回合 (X) - 点击格子落子"
                    else:
                        # 没有空位，平局
                        self._handle_game_end(0, None)

    def _handle_game_end(self, winner, win_line):
        self.game_over = True
        self.winner = winner
        self.win_line = win_line
        self.animating = True
        self.animation_timer = pygame.time.get_ticks()

        if winner == PLAYER:
            self.scores[0] += 1
            self.message = "🎉 你赢了！按 R 重新开始"
        elif winner == AI_PLAYER:
            self.scores[1] += 1
            self.message = "🤖 AI 赢了！按 R 重新开始"
        else:
            self.scores[2] += 1
            self.message = "🤝 平局！按 R 重新开始"

    # ---------- 渲染 ----------
    def draw_board(self):
        """绘制棋盘格线和格子"""
        board_x = (WIDTH - CELL_SIZE * BOARD_SIZE) // 2
        board_y = BOARD_OFFSET

        # 绘制棋盘背景
        board_rect = pygame.Rect(board_x - 10, board_y - 10,
                                 CELL_SIZE * BOARD_SIZE + 20,
                                 CELL_SIZE * BOARD_SIZE + 20)
        pygame.draw.rect(self.screen, (35, 35, 50), board_rect, border_radius=12)
        pygame.draw.rect(self.screen, GRID_COLOR, board_rect, 2, border_radius=12)

        # 绘制网格线
        for i in range(1, BOARD_SIZE):
            # 竖线
            x = board_x + i * CELL_SIZE
            pygame.draw.line(self.screen, LINE_COLOR,
                             (x, board_y), (x, board_y + CELL_SIZE * BOARD_SIZE), 3)
            # 横线
            y = board_y + i * CELL_SIZE
            pygame.draw.line(self.screen, LINE_COLOR,
                             (board_x, y), (board_x + CELL_SIZE * BOARD_SIZE, y), 3)

        # 绘制棋子
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] == EMPTY:
                    continue
                center_x = board_x + c * CELL_SIZE + CELL_SIZE // 2
                center_y = board_y + r * CELL_SIZE + CELL_SIZE // 2
                size = CELL_SIZE // 3

                if self.board[r][c] == PLAYER:
                    # 绘制 X
                    self._draw_x(center_x, center_y, size)
                else:
                    # 绘制 O
                    self._draw_o(center_x, center_y, size)

    def _draw_x(self, cx, cy, size):
        """绘制 X 符号"""
        offset = size * 0.7
        thickness = 6
        color = X_COLOR

        # 发光效果
        for glow in range(3, 0, -1):
            glow_color = (color[0] // (glow + 2), color[1] // (glow + 2), color[2] // (glow + 2))
            go = offset + glow * 3
            pygame.draw.line(self.screen, glow_color,
                             (cx - go, cy - go), (cx + go, cy + go), thickness + glow * 2)
            pygame.draw.line(self.screen, glow_color,
                             (cx + go, cy - go), (cx - go, cy + go), thickness + glow * 2)

        pygame.draw.line(self.screen, color,
                         (cx - offset, cy - offset), (cx + offset, cy + offset), thickness)
        pygame.draw.line(self.screen, color,
                         (cx + offset, cy - offset), (cx - offset, cy + offset), thickness)

    def _draw_o(self, cx, cy, size):
        """绘制 O 符号"""
        radius = size * 0.7
        thickness = 6
        color = O_COLOR

        # 发光效果
        for glow in range(3, 0, -1):
            glow_color = (color[0] // (glow + 2), color[1] // (glow + 2), color[2] // (glow + 2))
            pygame.draw.circle(self.screen, glow_color,
                               (cx, cy), radius + glow * 3, thickness + glow * 2)

        pygame.draw.circle(self.screen, color,
                           (cx, cy), radius, thickness)

    def draw_win_line(self):
        """绘制胜利连线"""
        if not self.win_line or not self.animating:
            return

        board_x = (WIDTH - CELL_SIZE * BOARD_SIZE) // 2
        board_y = BOARD_OFFSET

        start_r, start_c = self.win_line[0]
        end_r, end_c = self.win_line[1]

        start_pos = (board_x + start_c * CELL_SIZE + CELL_SIZE // 2,
                     board_y + start_r * CELL_SIZE + CELL_SIZE // 2)
        end_pos = (board_x + end_c * CELL_SIZE + CELL_SIZE // 2,
                   board_y + end_r * CELL_SIZE + CELL_SIZE // 2)

        # 动画效果：线逐渐变长
        elapsed = (pygame.time.get_ticks() - self.animation_timer) % 1000
        progress = min(elapsed / 500, 1.0)

        current_end = (
            start_pos[0] + (end_pos[0] - start_pos[0]) * progress,
            start_pos[1] + (end_pos[1] - start_pos[1]) * progress
        )

        color = (255, 255, 100)  # 金色
        pygame.draw.line(self.screen, color, start_pos, current_end, WIN_LINE_WIDTH)

        # 闪烁效果
        if progress >= 1.0:
            blink = abs(pygame.time.get_ticks() % 800 - 400) / 400
            alpha = int(255 * (0.3 + 0.7 * blink))
            flash_color = (255, 255, 100, alpha)
            # 重新绘制完整的线来闪烁
            pygame.draw.line(self.screen, flash_color[:3], start_pos, end_pos, WIN_LINE_WIDTH)

    def draw_ui(self):
        """绘制界面文字和记分牌"""
        # 标题
        title = self.big_font.render("井字棋", True, TEXT_COLOR)
        title_rect = title.get_rect(center=(WIDTH // 2, 20))
        self.screen.blit(title, title_rect)

        # 记分牌
        score_text = f"玩家 X: {self.scores[0]}  |  AI O: {self.scores[1]}  |  平局: {self.scores[2]}"
        score_surf = self.small_font.render(score_text, True, TEXT_COLOR)
        score_rect = score_surf.get_rect(center=(WIDTH // 2, BOARD_OFFSET + CELL_SIZE * 3 + 50))
        self.screen.blit(score_surf, score_rect)

        # 状态消息
        msg_color = TEXT_COLOR
        if self.game_over:
            if self.winner == PLAYER:
                msg_color = X_COLOR
            elif self.winner == AI_PLAYER:
                msg_color = O_COLOR
            else:
                msg_color = (200, 200, 100)

        msg_surf = self.small_font.render(self.message, True, msg_color)
        msg_rect = msg_surf.get_rect(center=(WIDTH // 2, BOARD_OFFSET + CELL_SIZE * 3 + 90))
        self.screen.blit(msg_surf, msg_rect)

        # 操作提示
        hint = self.small_font.render("按 R 重新开始  |  按 ESC 退出", True, (120, 120, 140))
        hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT - 25))
        self.screen.blit(hint, hint_rect)

    def draw_hover(self):
        """鼠标悬停高亮效果"""
        if self.game_over or self.current_player != PLAYER:
            return

        pos = pygame.mouse.get_pos()
        board_x = (WIDTH - CELL_SIZE * BOARD_SIZE) // 2
        board_y = BOARD_OFFSET

        col = (pos[0] - board_x) // CELL_SIZE
        row = (pos[1] - board_y) // CELL_SIZE

        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            if self.is_valid_move(row, col):
                rect = pygame.Rect(
                    board_x + col * CELL_SIZE + 5,
                    board_y + row * CELL_SIZE + 5,
                    CELL_SIZE - 10, CELL_SIZE - 10
                )
                s = pygame.Surface((CELL_SIZE - 10, CELL_SIZE - 10), pygame.SRCALPHA)
                s.fill((80, 200, 255, 30))
                self.screen.blit(s, (board_x + col * CELL_SIZE + 5, board_y + row * CELL_SIZE + 5))

    def run(self):
        """主游戏循环"""
        running = True
        while running:
            self.screen.fill(BG_COLOR)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        self.reset()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键
                        self.handle_click(event.pos)

            # 绘制所有元素
            self.draw_board()
            self.draw_hover()
            self.draw_win_line()
            self.draw_ui()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# -------------------- 入口 --------------------
if __name__ == "__main__":
    game = TicTacToe()
    game.run()