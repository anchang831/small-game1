"""
西洋跳棋 (Checkers) - 经典策略棋盘游戏
========================================
规则：
- 8x8 棋盘，红方(玩家) vs 黑方(AI)
- 棋子只能斜向前进(普通棋子)
- 跳过对方棋子即可吃掉，必须吃子时强制吃子
- 到达对方底线升级为王(King)，王可前后移动
- 吃掉所有对方棋子或对方无合法移动即获胜

操作：
- 鼠标点击选中棋子，再点击目标格子移动
- 高亮显示可选移动和吃子位置
- 按 R 键重新开始，按 ESC 退出

作者：AI Game Generator
日期：2026-08-06
"""

import pygame
import sys
import copy
import random
import time

# ======================== 常量定义 ========================
WINDOW_SIZE = 640
BOARD_SIZE = 8
CELL_SIZE = WINDOW_SIZE // BOARD_SIZE  # 80px
PIECE_RADIUS = CELL_SIZE // 2 - 8      # 32px
FPS = 60

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
DARK_RED = (160, 30, 30)
LIGHT_BROWN = (240, 217, 181)
DARK_BROWN = (181, 136, 99)
HIGHLIGHT_COLOR = (255, 255, 100, 180)
SELECTED_COLOR = (100, 255, 100)
LAST_MOVE_COLOR = (255, 255, 0, 80)
KING_SYMBOL_COLOR = (255, 215, 0)

# 棋子类型
EMPTY = 0
RED_PIECE = 1      # 玩家棋子
RED_KING = 2       # 玩家王
BLACK_PIECE = 3    # AI棋子
BLACK_KING = 4     # AI王

# 游戏状态
PLAYING = 0
PLAYER_WIN = 1
AI_WIN = 2
DRAW = 3


class CheckersGame:
    """西洋跳棋游戏主逻辑"""

    def __init__(self):
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_turn = RED_PIECE  # 红方先手(玩家)
        self.selected_pos = None
        self.valid_moves = []       # 当前选中棋子的合法移动
        self.must_jump = False      # 是否强制吃子
        self.jump_chain = []        # 连跳路径
        self.last_move = None       # 上一步移动
        self.game_state = PLAYING
        self.ai_thinking = False
        self.move_history = []
        self.init_board()

    def init_board(self):
        """初始化棋盘布局"""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if (row + col) % 2 == 1:  # 深色格子
                    if row < 3:
                        self.board[row][col] = BLACK_PIECE  # 上方黑方(AI)
                    elif row > 4:
                        self.board[row][col] = RED_PIECE    # 下方红方(玩家)

    def is_red(self, piece):
        """判断是否为红方棋子"""
        return piece in (RED_PIECE, RED_KING)

    def is_black(self, piece):
        """判断是否为黑方棋子"""
        return piece in (BLACK_PIECE, BLACK_KING)

    def is_king(self, piece):
        """判断是否为王"""
        return piece in (RED_KING, BLACK_KING)

    def get_opponent(self, piece):
        """获取对方颜色"""
        return BLACK_PIECE if self.is_red(piece) else RED_PIECE

    def on_board(self, row, col):
        """检查坐标是否在棋盘内"""
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def get_piece_color(self, piece):
        """获取棋子所属阵营"""
        if self.is_red(piece):
            return RED_PIECE
        elif self.is_black(piece):
            return BLACK_PIECE
        return EMPTY

    def get_legal_moves(self, board, row, col):
        """获取指定棋子的所有合法移动"""
        piece = board[row][col]
        if piece == EMPTY:
            return []

        moves = []
        jumps = []
        directions = []

        # 普通红子只能向上(行号减小)，黑子向下(行号增大)
        if self.is_red(piece):
            directions.append(-1)  # 向上
        if self.is_black(piece):
            directions.append(1)   # 向下
        if self.is_king(piece):
            # 王可以上下两个方向
            if self.is_red(piece):
                directions.append(1)
            if self.is_black(piece):
                directions.append(-1)

        for dr in directions:
            for dc in (-1, 1):  # 左斜和右斜
                nr, nc = row + dr, col + dc
                if not self.on_board(nr, nc):
                    continue

                # 普通移动
                if board[nr][nc] == EMPTY:
                    moves.append((nr, nc))

                # 吃子跳跃
                jr, jc = row + 2 * dr, col + 2 * dc
                if self.on_board(jr, jc) and board[jr][jc] == EMPTY:
                    mid = board[nr][nc]
                    if mid != EMPTY and self.get_piece_color(mid) != self.get_piece_color(piece):
                        jumps.append((jr, jc))

        return moves, jumps

    def get_all_legal_moves(self, board, color):
        """获取某方所有棋子的所有合法移动"""
        all_moves = []
        all_jumps = []
        has_jumps = False

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if board[row][col] != EMPTY and self.get_piece_color(board[row][col]) == color:
                    moves, jumps = self.get_legal_moves(board, row, col)
                    if jumps:
                        has_jumps = True
                        all_jumps.append((row, col, jumps))
                    all_moves.append((row, col, moves))

        if has_jumps:
            return all_jumps, True  # 强制吃子
        return all_moves, False

    def make_move(self, board, row, col, target_row, target_col):
        """执行移动，返回新棋盘和是否吃子"""
        new_board = copy.deepcopy(board)
        piece = new_board[row][col]
        new_board[row][col] = EMPTY

        # 检查是否吃子
        is_jump = abs(target_row - row) == 2
        if is_jump:
            # 移除被吃的棋子
            mid_row = (row + target_row) // 2
            mid_col = (col + target_col) // 2
            new_board[mid_row][mid_col] = EMPTY

        # 升王：到达对方底线
        if self.is_red(piece) and target_row == 0:
            new_board[target_row][target_col] = RED_KING
        elif self.is_black(piece) and target_row == BOARD_SIZE - 1:
            new_board[target_row][target_col] = BLACK_KING
        else:
            new_board[target_row][target_col] = piece

        return new_board, is_jump

    def has_any_jumps(self, board, color):
        """检查某方是否有任何吃子机会"""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if board[row][col] != EMPTY and self.get_piece_color(board[row][col]) == color:
                    _, jumps = self.get_legal_moves(board, row, col)
                    if jumps:
                        return True
        return False

    def get_all_jumps_from(self, board, row, col):
        """获取某棋子的所有吃子路径(支持连跳)"""
        _, jumps = self.get_legal_moves(board, row, col)
        paths = []
        for jr, jc in jumps:
            new_board, _ = self.make_move(board, row, col, jr, jc)
            # 递归检查连跳
            sub_paths = self.get_all_jumps_from(new_board, jr, jc)
            if sub_paths:
                for sub_path in sub_paths:
                    paths.append([(jr, jc)] + sub_path)
            else:
                paths.append([(jr, jc)])
        return paths

    def get_valid_moves_for(self, board, row, col):
        """获取棋子的合法移动(考虑强制吃子规则)"""
        piece = board[row][col]
        if piece == EMPTY:
            return [], False

        color = self.get_piece_color(piece)
        moves, jumps = self.get_legal_moves(board, row, col)

        # 检查是否有强制吃子
        if self.has_any_jumps(board, color):
            if jumps:
                return jumps, True
            else:
                return [], False

        return moves, False

    def player_click(self, row, col):
        """处理玩家点击"""
        if self.game_state != PLAYING or self.current_turn != RED_PIECE or self.ai_thinking:
            return

        piece = self.board[row][col]

        # 如果已经有选中的棋子
        if self.selected_pos is not None:
            sr, sc = self.selected_pos

            # 点击了同一个棋子 - 取消选中
            if (row, col) == self.selected_pos:
                self.selected_pos = None
                self.valid_moves = []
                return

            # 点击了己方另一个棋子 - 切换选中
            if piece != EMPTY and self.get_piece_color(piece) == RED_PIECE:
                self.selected_pos = (row, col)
                self.valid_moves, self.must_jump = self.get_valid_moves_for(self.board, row, col)
                return

            # 尝试移动到目标位置
            if (row, col) in self.valid_moves:
                self.execute_player_move(sr, sc, row, col)
                return

            # 点击无效位置
            self.selected_pos = None
            self.valid_moves = []
            return

        # 选中新棋子
        if piece != EMPTY and self.get_piece_color(piece) == RED_PIECE:
            self.selected_pos = (row, col)
            self.valid_moves, self.must_jump = self.get_valid_moves_for(self.board, row, col)
            if not self.valid_moves:
                self.selected_pos = None

    def execute_player_move(self, sr, sc, tr, tc):
        """执行玩家移动"""
        self.board, is_jump = self.make_move(self.board, sr, sc, tr, tc)
        self.last_move = ((sr, sc), (tr, tc))
        self.selected_pos = None
        self.valid_moves = []

        # 检查连跳
        if is_jump:
            piece = self.board[tr][tc]
            _, more_jumps = self.get_legal_moves(self.board, tr, tc)
            if more_jumps:
                # 必须继续连跳
                self.selected_pos = (tr, tc)
                self.valid_moves, _ = self.get_valid_moves_for(self.board, tr, tc)
                self.must_jump = True
                return

        # 切换回合
        self.current_turn = BLACK_PIECE
        self.check_game_state()

        # AI 回合
        if self.game_state == PLAYING:
            self.ai_thinking = True

    def ai_move(self):
        """AI 走棋"""
        if self.game_state != PLAYING or self.current_turn != BLACK_PIECE:
            self.ai_thinking = False
            return

        # 使用 Minimax 搜索最佳走法
        best_move = self.get_best_move(self.board, BLACK_PIECE, depth=3)
        if best_move is None:
            # 备用：随机走法
            best_move = self.get_random_move(self.board, BLACK_PIECE)

        if best_move:
            sr, sc, tr, tc = best_move
            self.board, is_jump = self.make_move(self.board, sr, sc, tr, tc)
            self.last_move = ((sr, sc), (tr, tc))

            # 检查连跳
            if is_jump:
                _, more_jumps = self.get_legal_moves(self.board, tr, tc)
                if more_jumps:
                    # AI 继续连跳(使用贪心)
                    chain_pos = (tr, tc)
                    while True:
                        _, jumps = self.get_legal_moves(self.board, chain_pos[0], chain_pos[1])
                        if not jumps:
                            break
                        # 选择吃掉最多棋子的走法
                        tr2, tc2 = jumps[0]
                        self.board, _ = self.make_move(self.board, chain_pos[0], chain_pos[1], tr2, tc2)
                        self.last_move = (chain_pos, (tr2, tc2))
                        chain_pos = (tr2, tc2)

            # 切换回合
            self.current_turn = RED_PIECE
            self.check_game_state()

        self.ai_thinking = False

    def get_random_move(self, board, color):
        """获取随机合法走法"""
        all_moves_list, has_jumps = self.get_all_legal_moves(board, color)
        if not all_moves_list:
            return None

        if has_jumps:
            row, col, jumps = random.choice(all_moves_list)
            tr, tc = random.choice(jumps)
            return (row, col, tr, tc)

        row, col, moves = random.choice(all_moves_list)
        if not moves:
            return None
        tr, tc = random.choice(moves)
        return (row, col, tr, tc)

    def evaluate_board(self, board, color):
        """评估棋盘分数"""
        score = 0
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = board[row][col]
                if piece == EMPTY:
                    continue
                val = 0
                if piece == RED_PIECE:
                    val = -10
                elif piece == RED_KING:
                    val = -15
                elif piece == BLACK_PIECE:
                    val = 10
                elif piece == BLACK_KING:
                    val = 15
                # 中心位置加成
                center_dist = abs(row - 3.5) + abs(col - 3.5)
                if self.is_black(piece):
                    val += (7 - center_dist) * 0.5
                else:
                    val -= (7 - center_dist) * 0.5
                score += val
        return score

    def minimax(self, board, depth, alpha, beta, maximizing, color):
        """Minimax 搜索 + Alpha-Beta 剪枝"""
        if depth == 0:
            return self.evaluate_board(board, color), None

        all_moves_list, has_jumps = self.get_all_legal_moves(board, color)
        if not all_moves_list:
            if maximizing:
                return -10000, None
            return 10000, None

        opponent = RED_PIECE if color == BLACK_PIECE else BLACK_PIECE
        best_move = None

        if maximizing:
            max_eval = -float('inf')
            for row, col, moves in all_moves_list:
                if has_jumps:
                    targets = moves
                else:
                    targets = moves
                for tr, tc in targets:
                    new_board, _ = self.make_move(board, row, col, tr, tc)
                    eval_score, _ = self.minimax(new_board, depth - 1, alpha, beta, False, opponent)
                    if eval_score > max_eval:
                        max_eval = eval_score
                        best_move = (row, col, tr, tc)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for row, col, moves in all_moves_list:
                if has_jumps:
                    targets = moves
                else:
                    targets = moves
                for tr, tc in targets:
                    new_board, _ = self.make_move(board, row, col, tr, tc)
                    eval_score, _ = self.minimax(new_board, depth - 1, alpha, beta, True, opponent)
                    if eval_score < min_eval:
                        min_eval = eval_score
                        best_move = (row, col, tr, tc)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
                if beta <= alpha:
                    break
            return min_eval, best_move

    def get_best_move(self, board, color, depth=3):
        """获取最佳走法"""
        # 先检查强制吃子
        all_moves_list, has_jumps = self.get_all_legal_moves(board, color)
        if not all_moves_list:
            return None

        # 如果只有吃子走法，直接按估值选择
        if has_jumps:
            best_score = -float('inf')
            best_move = None
            for row, col, jumps in all_moves_list:
                for tr, tc in jumps:
                    new_board, _ = self.make_move(board, row, col, tr, tc)
                    score = self.evaluate_board(new_board, color)
                    if score > best_score:
                        best_score = score
                        best_move = (row, col, tr, tc)
            return best_move

        # 正常搜索
        maximizing = (color == BLACK_PIECE)
        _, best_move = self.minimax(board, depth, -float('inf'), float('inf'), maximizing, color)
        return best_move

    def check_game_state(self):
        """检查游戏状态"""
        # 检查玩家是否还有棋子
        player_has_piece = any(
            self.board[row][col] in (RED_PIECE, RED_KING)
            for row in range(BOARD_SIZE)
            for col in range(BOARD_SIZE)
        )
        ai_has_piece = any(
            self.board[row][col] in (BLACK_PIECE, BLACK_KING)
            for row in range(BOARD_SIZE)
            for col in range(BOARD_SIZE)
        )

        # 检查是否有合法移动
        player_moves, _ = self.get_all_legal_moves(self.board, RED_PIECE)
        ai_moves, _ = self.get_all_legal_moves(self.board, BLACK_PIECE)

        if not player_has_piece or not player_moves:
            self.game_state = AI_WIN
        elif not ai_has_piece or not ai_moves:
            self.game_state = PLAYER_WIN

    def reset(self):
        """重置游戏"""
        self.__init__()


class CheckersRenderer:
    """西洋跳棋渲染器"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + 60))
        pygame.display.set_caption("西洋跳棋 (Checkers)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simhei", 28, bold=True)
        self.small_font = pygame.font.SysFont("simhei", 18)
        self.game = CheckersGame()
        self.running = True

    def draw_board(self):
        """绘制棋盘"""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                color = LIGHT_BROWN if (row + col) % 2 == 0 else DARK_BROWN
                pygame.draw.rect(self.screen, color, rect)

        # 绘制上一步移动高亮
        if self.game.last_move:
            for pos in self.game.last_move:
                r, c = pos
                s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                s.fill(LAST_MOVE_COLOR)
                self.screen.blit(s, (c * CELL_SIZE, r * CELL_SIZE))

        # 绘制合法移动提示
        for move in self.game.valid_moves:
            r, c = move
            s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            s.fill(HIGHLIGHT_COLOR)
            self.screen.blit(s, (c * CELL_SIZE, r * CELL_SIZE))
            # 绘制小圆点
            pygame.draw.circle(
                self.screen, (0, 200, 0, 100),
                (c * CELL_SIZE + CELL_SIZE // 2, r * CELL_SIZE + CELL_SIZE // 2),
                10
            )

        # 绘制选中高亮
        if self.game.selected_pos:
            r, c = self.game.selected_pos
            s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            s.fill(SELECTED_COLOR + (100,))
            self.screen.blit(s, (c * CELL_SIZE, r * CELL_SIZE))

    def draw_pieces(self):
        """绘制棋子"""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.game.board[row][col]
                if piece == EMPTY:
                    continue

                cx = col * CELL_SIZE + CELL_SIZE // 2
                cy = row * CELL_SIZE + CELL_SIZE // 2

                if piece in (RED_PIECE, RED_KING):
                    color = RED
                    border = DARK_RED
                else:
                    color = (50, 50, 50)
                    border = (20, 20, 20)

                # 阴影
                pygame.draw.circle(self.screen, (0, 0, 0, 60),
                                   (cx + 2, cy + 2), PIECE_RADIUS)
                # 主体
                pygame.draw.circle(self.screen, color, (cx, cy), PIECE_RADIUS)
                pygame.draw.circle(self.screen, border, (cx, cy), PIECE_RADIUS, 2)
                # 高光
                pygame.draw.circle(self.screen, (255, 255, 255, 40),
                                   (cx - 5, cy - 5), PIECE_RADIUS // 2)

                # 王冠标记
                if piece in (RED_KING, BLACK_KING):
                    king_size = PIECE_RADIUS // 2
                    points = [
                        (cx, cy - king_size + 5),
                        (cx - 6, cy + 2),
                        (cx - 3, cy - 2),
                        (cx, cy + 5),
                        (cx + 3, cy - 2),
                        (cx + 6, cy + 2),
                    ]
                    pygame.draw.polygon(self.screen, KING_SYMBOL_COLOR, points)
                    pygame.draw.circle(self.screen, KING_SYMBOL_COLOR,
                                       (cx, cy + 5), 3)

    def draw_ui(self):
        """绘制 UI 信息"""
        # 状态栏背景
        bar_rect = pygame.Rect(0, WINDOW_SIZE, WINDOW_SIZE, 60)
        pygame.draw.rect(self.screen, (40, 40, 40), bar_rect)
        pygame.draw.line(self.screen, (100, 100, 100), (0, WINDOW_SIZE),
                         (WINDOW_SIZE, WINDOW_SIZE), 2)

        # 显示当前回合
        if self.game.game_state == PLAYING:
            if self.game.current_turn == RED_PIECE:
                if self.game.ai_thinking:
                    text = "AI 思考中..."
                    color = (200, 200, 200)
                else:
                    text = "你的回合 (红方)"
                    color = RED
            else:
                text = "AI 回合 (黑方)"
                color = (200, 200, 200)
        elif self.game.game_state == PLAYER_WIN:
            text = "🎉 你赢了！按 R 重新开始"
            color = (100, 255, 100)
        elif self.game.game_state == AI_WIN:
            text = "😞 AI 赢了！按 R 重新开始"
            color = (255, 100, 100)
        else:
            text = "平局！按 R 重新开始"
            color = (255, 255, 100)

        # 绘制棋子数量
        red_count = sum(
            1 for row in range(BOARD_SIZE) for col in range(BOARD_SIZE)
            if self.game.board[row][col] in (RED_PIECE, RED_KING)
        )
        black_count = sum(
            1 for row in range(BOARD_SIZE) for col in range(BOARD_SIZE)
            if self.game.board[row][col] in (BLACK_PIECE, BLACK_KING)
        )

        text_surf = self.font.render(text, True, color)
        text_rect = text_surf.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE + 20))
        self.screen.blit(text_surf, text_rect)

        count_text = f"红方: {red_count}  黑方: {black_count}"
        count_surf = self.small_font.render(count_text, True, (200, 200, 200))
        count_rect = count_surf.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE + 45))
        self.screen.blit(count_surf, count_rect)

    def run(self):
        """主循环"""
        ai_timer = 0

        while self.running:
            dt = self.clock.tick(FPS)

            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.game.reset()
                        ai_timer = 0
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        pygame.quit()
                        sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game.game_state == PLAYING and not self.game.ai_thinking:
                        mx, my = event.pos
                        if my < WINDOW_SIZE:  # 点击在棋盘内
                            col = mx // CELL_SIZE
                            row = my // CELL_SIZE
                            self.game.player_click(row, col)

            # AI 走棋
            if self.game.ai_thinking and self.game.game_state == PLAYING:
                ai_timer += dt
                if ai_timer > 300:  # 300ms 延迟，让玩家看到思考过程
                    self.game.ai_move()
                    ai_timer = 0
            else:
                ai_timer = 0

            # 绘制
            self.screen.fill(WHITE)
            self.draw_board()
            self.draw_pieces()
            self.draw_ui()

            pygame.display.flip()

        pygame.quit()


def main():
    print("西洋跳棋 (Checkers) - 开始游戏")
    print("操作：点击棋子选中，再点击目标位置移动")
    print("红方 = 玩家，黑方 = AI")
    print("按 R 重新开始，按 ESC 退出")
    renderer = CheckersRenderer()
    renderer.run()


if __name__ == "__main__":
    main()