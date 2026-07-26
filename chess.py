"""
国际象棋 (Chess) - 经典策略棋类游戏
使用 Pygame 实现，单文件运行
支持: 完整走法生成、将军/将杀检测、王车易位、吃过路兵、兵升变
"""

import pygame
import sys

# ==================== 常量定义 ====================
BOARD_SIZE = 8
SQUARE_SIZE = 80
WINDOW_SIZE = SQUARE_SIZE * BOARD_SIZE  # 640
INFO_PANEL_WIDTH = 220
TOTAL_WIDTH = WINDOW_SIZE + INFO_PANEL_WIDTH
WINDOW_HEIGHT = WINDOW_SIZE

# 颜色
LIGHT_BROWN = (240, 217, 181)
DARK_BROWN = (181, 136, 99)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PANEL_BG = (40, 40, 40)
GOLD = (255, 215, 0)

# 棋子类型
KING = 'K'
QUEEN = 'Q'
ROOK = 'R'
BISHOP = 'B'
KNIGHT = 'N'
PAWN = 'P'

# Unicode 棋子符号
PIECE_SYMBOLS = {
    'wK': '♔', 'wQ': '♕', 'wR': '♖', 'wB': '♗', 'wN': '♘', 'wP': '♙',
    'bK': '♚', 'bQ': '♛', 'bR': '♜', 'bB': '♝', 'bN': '♞', 'bP': '♟'
}

# 棋子中文名
PIECE_NAMES = {KING: '王', QUEEN: '后', ROOK: '车', BISHOP: '象', KNIGHT: '马', PAWN: '兵'}


class ChessGame:
    """国际象棋游戏主类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((TOTAL_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("国际象棋 Chess")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont('simsun, arial', 44)
        self.font_small = pygame.font.SysFont('simsun, arial', 20)
        self.font_big = pygame.font.SysFont('simsun, arial', 52)
        self.reset_game()

    # ==================== 初始化 ====================
    def reset_game(self):
        """重置游戏状态"""
        self.board = self._init_board()
        self.turn = 'w'          # 当前走棋方: 'w'白方 / 'b'黑方
        self.selected = None     # 选中的棋子位置 (row, col)
        self.valid_moves = []    # 选中棋子的合法走法列表
        self.move_history = []   # 走棋历史记录
        self.game_over = False
        self.winner = None
        self.en_passant_target = None  # 吃过路兵目标格
        self.castling_rights = {       # 王车易位权限
            'w': {'K': True, 'Q': True},
            'b': {'K': True, 'Q': True}
        }
        self.last_move = None  # 上一步 ((from_r, from_c), (to_r, to_c))

    def _init_board(self):
        """初始化棋盘布局"""
        board = [[None for _ in range(8)] for _ in range(8)]
        # 黑方棋子
        back_rank = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]
        for c in range(8):
            board[0][c] = ('b', back_rank[c])
            board[1][c] = ('b', PAWN)
        # 白方棋子
        for c in range(8):
            board[6][c] = ('w', PAWN)
            board[7][c] = ('w', back_rank[c])
        return board

    # ==================== 基础检测 ====================
    def in_bounds(self, r, c):
        """检查坐标是否在棋盘内"""
        return 0 <= r < 8 and 0 <= c < 8

    def get_piece(self, r, c):
        """获取指定位置的棋子，越界返回 None"""
        return self.board[r][c] if self.in_bounds(r, c) else None

    def find_king(self, color):
        """查找指定颜色的王的位置"""
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == (color, KING):
                    return (r, c)
        return None

    # ==================== 攻击检测 ====================
    def is_attacked_by(self, r, c, attacker_color):
        """判断 (r, c) 是否被 attacker_color 的棋子攻击"""
        # 马
        for dr, dc in [(2, 1), (2, -1), (-2, 1), (-2, -1),
                       (1, 2), (1, -2), (-1, 2), (-1, -2)]:
            nr, nc = r + dr, c + dc
            if self.get_piece(nr, nc) == (attacker_color, KNIGHT):
                return True

        # 王（相邻格）
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                if self.get_piece(r + dr, c + dc) == (attacker_color, KING):
                    return True

        # 兵
        pawn_dir = -1 if attacker_color == 'w' else 1
        for dc in (-1, 1):
            if self.get_piece(r + pawn_dir, c + dc) == (attacker_color, PAWN):
                return True

        # 车/后（直线）
        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nr, nc = r + dr, c + dc
            while self.in_bounds(nr, nc):
                p = self.board[nr][nc]
                if p:
                    if p[0] == attacker_color and p[1] in (ROOK, QUEEN):
                        return True
                    break
                nr += dr
                nc += dc

        # 象/后（斜线）
        for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            nr, nc = r + dr, c + dc
            while self.in_bounds(nr, nc):
                p = self.board[nr][nc]
                if p:
                    if p[0] == attacker_color and p[1] in (BISHOP, QUEEN):
                        return True
                    break
                nr += dr
                nc += dc

        return False

    def in_check(self, color):
        """判断 color 方是否被将军"""
        king_pos = self.find_king(color)
        if not king_pos:
            return False
        enemy = 'b' if color == 'w' else 'w'
        return self.is_attacked_by(king_pos[0], king_pos[1], enemy)

    # ==================== 走法生成 ====================
    def _pawn_moves(self, r, c, color):
        """生成兵的所有伪合法走法"""
        moves = []
        d = -1 if color == 'w' else 1
        start = 6 if color == 'w' else 1

        # 前进一步
        nr = r + d
        if self.in_bounds(nr, c) and not self.board[nr][c]:
            moves.append((nr, c))
            # 起始位置前进两步
            nr2 = r + 2 * d
            if r == start and not self.board[nr2][c]:
                moves.append((nr2, c))

        # 吃子
        for dc in (-1, 1):
            nc = c + dc
            if self.in_bounds(r + d, nc):
                target = self.get_piece(r + d, nc)
                if target and target[0] != color:
                    moves.append((r + d, nc))
                # 吃过路兵
                if self.en_passant_target == (r + d, nc):
                    moves.append((r + d, nc))
        return moves

    def _knight_moves(self, r, c, color):
        """生成马的所有走法"""
        moves = []
        for dr, dc in ((2, 1), (2, -1), (-2, 1), (-2, -1),
                       (1, 2), (1, -2), (-1, 2), (-1, -2)):
            nr, nc = r + dr, c + dc
            if not self.in_bounds(nr, nc):
                continue
            p = self.board[nr][nc]
            if p is None or p[0] != color:
                moves.append((nr, nc))
        return moves

    def _sliding_moves(self, r, c, color, directions):
        """生成滑动棋子的走法（车/象/后）"""
        moves = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while self.in_bounds(nr, nc):
                p = self.board[nr][nc]
                if p:
                    if p[0] != color:
                        moves.append((nr, nc))
                    break
                moves.append((nr, nc))
                nr += dr
                nc += dc
        return moves

    def _bishop_moves(self, r, c, color):
        return self._sliding_moves(r, c, color, ((1, 1), (1, -1), (-1, 1), (-1, -1)))

    def _rook_moves(self, r, c, color):
        return self._sliding_moves(r, c, color, ((0, 1), (0, -1), (1, 0), (-1, 0)))

    def _queen_moves(self, r, c, color):
        return self._bishop_moves(r, c, color) + self._rook_moves(r, c, color)

    def _king_moves(self, r, c, color):
        """生成王的所有走法（含王车易位）"""
        moves = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if not self.in_bounds(nr, nc):
                    continue
                p = self.board[nr][nc]
                if p is None or p[0] != color:
                    moves.append((nr, nc))

        # 王车易位
        enemy = 'b' if color == 'w' else 'w'
        if not self.in_check(color):
            # 王翼
            if self.castling_rights[color]['K']:
                if (not self.board[r][5] and not self.board[r][6]
                        and self.board[r][7] == (color, ROOK)):
                    if (not self.is_attacked_by(r, 5, enemy)
                            and not self.is_attacked_by(r, 6, enemy)):
                        moves.append((r, 6))
            # 后翼
            if self.castling_rights[color]['Q']:
                if (not self.board[r][1] and not self.board[r][2]
                        and not self.board[r][3]
                        and self.board[r][0] == (color, ROOK)):
                    if (not self.is_attacked_by(r, 2, enemy)
                            and not self.is_attacked_by(r, 3, enemy)):
                        moves.append((r, 2))
        return moves

    def _pseudo_moves(self, r, c):
        """获取指定位置棋子的所有伪合法走法（不考虑将军）"""
        piece = self.board[r][c]
        if not piece:
            return []
        color, ptype = piece
        if ptype == PAWN:
            return self._pawn_moves(r, c, color)
        elif ptype == KNIGHT:
            return self._knight_moves(r, c, color)
        elif ptype == BISHOP:
            return self._bishop_moves(r, c, color)
        elif ptype == ROOK:
            return self._rook_moves(r, c, color)
        elif ptype == QUEEN:
            return self._queen_moves(r, c, color)
        elif ptype == KING:
            return self._king_moves(r, c, color)
        return []

    # ==================== 合法走法 ====================
    def legal_moves(self, r, c):
        """获取指定位置棋子的所有合法走法（走完后不能让自己被将军）"""
        piece = self.board[r][c]
        if not piece:
            return []
        color = piece[0]
        legal = []
        for tr, tc in self._pseudo_moves(r, c):
            # 模拟走棋
            captured = self.board[tr][tc]
            self.board[tr][tc] = self.board[r][c]
            self.board[r][c] = None

            # 处理吃过路兵
            ep_captured = None
            if piece[1] == PAWN and (tr, tc) == self.en_passant_target:
                ep_captured = self.board[r][tc]
                self.board[r][tc] = None

            # 检查是否自将
            if not self.in_check(color):
                legal.append((tr, tc))

            # 撤销
            self.board[r][c] = self.board[tr][tc]
            self.board[tr][tc] = captured
            if ep_captured:
                self.board[r][tc] = ep_captured

        return legal

    def has_legal_moves(self, color):
        """判断某方是否还有合法走法"""
        for r in range(8):
            for c in range(8):
                if self.board[r][c] and self.board[r][c][0] == color:
                    if self.legal_moves(r, c):
                        return True
        return False

    def is_checkmate(self, color):
        """判断是否将杀"""
        return self.in_check(color) and not self.has_legal_moves(color)

    def is_stalemate(self, color):
        """判断是否逼和"""
        return not self.in_check(color) and not self.has_legal_moves(color)

    # ==================== 走棋执行 ====================
    def make_move(self, from_pos, to_pos):
        """执行一步走棋"""
        fr, fc = from_pos
        tr, tc = to_pos
        piece = self.board[fr][fc]
        color, ptype = piece

        # 保存状态（用于撤销）
        old_en_passant = self.en_passant_target
        old_castling = {k: dict(v) for k, v in self.castling_rights.items()}

        # 记录被吃子
        captured = self.board[tr][tc]
        captured_desc = ""

        # 吃过路兵
        ep_captured = None
        if ptype == PAWN and (tr, tc) == self.en_passant_target:
            ep_captured = (fr, tc)
            captured_desc = f"吃过路兵{PIECE_NAMES[PAWN]}"
            self.board[fr][tc] = None

        # 移动棋子
        self.board[tr][tc] = piece
        self.board[fr][fc] = None

        # 兵升变（自动升后）
        promotion = None
        if ptype == PAWN and (tr == 0 or tr == 7):
            self.board[tr][tc] = (color, QUEEN)
            promotion = 'Q'

        # 更新过路兵标记
        self.en_passant_target = None
        if ptype == PAWN and abs(tr - fr) == 2:
            self.en_passant_target = ((fr + tr) // 2, fc)

        # 更新王车易位权限
        if ptype == KING:
            self.castling_rights[color]['K'] = False
            self.castling_rights[color]['Q'] = False
            # 王车易位移动
            if tc - fc == 2:  # 王翼
                self.board[fr][5] = self.board[fr][7]
                self.board[fr][7] = None
            elif tc - fc == -2:  # 后翼
                self.board[fr][3] = self.board[fr][0]
                self.board[fr][0] = None

        if ptype == ROOK:
            if fc == 0:
                self.castling_rights[color]['Q'] = False
            elif fc == 7:
                self.castling_rights[color]['K'] = False

        # 如果吃掉了车，更新对方易位权限
        if captured and captured[1] == ROOK:
            if tc == 0:
                self.castling_rights[captured[0]]['Q'] = False
            elif tc == 7:
                self.castling_rights[captured[0]]['K'] = False

        # 切换走棋方
        self.turn = 'b' if color == 'w' else 'w'
        self.last_move = (from_pos, to_pos)

        # 记录走法
        if captured and not captured_desc:
            captured_desc = f"吃{PIECE_NAMES[captured[1]]}"
        move_parts = [
            f"{'白' if color == 'w' else '黑'}{PIECE_NAMES[ptype]}",
            f"{chr(ord('a') + fc)}{8 - fr}→{chr(ord('a') + tc)}{8 - tr}",
        ]
        if promotion:
            move_parts.append(f"升{PIECE_NAMES[promotion]}")
        if captured_desc:
            move_parts.append(captured_desc)
        self.move_history.append(' '.join(move_parts))

        # 检查游戏状态
        enemy = self.turn
        if self.in_check(enemy):
            if self.is_checkmate(enemy):
                self.game_over = True
                self.winner = color
                self.move_history.append(
                    f"将杀！{'白方' if color == 'w' else '黑方'}获胜！")
            else:
                self.move_history.append(f"{'黑方' if enemy == 'b' else '白方'}被将军！")
        elif self.is_stalemate(enemy):
            self.game_over = True
            self.winner = None
            self.move_history.append("和棋！逼和！")

    # ==================== 事件处理 ====================
    def handle_click(self, pos):
        """处理鼠标点击事件"""
        x, y = pos
        if x >= WINDOW_SIZE:
            return
        col = x // SQUARE_SIZE
        row = y // SQUARE_SIZE

        if self.game_over:
            self.reset_game()
            return

        if self.selected:
            if (row, col) in self.valid_moves:
                self.make_move(self.selected, (row, col))
            self.selected = None
            self.valid_moves = []
            # 点击自己的棋子重新选择
            piece = self.board[row][col]
            if piece and piece[0] == self.turn and not self.game_over:
                self.selected = (row, col)
                self.valid_moves = self.legal_moves(row, col)
        else:
            piece = self.board[row][col]
            if piece and piece[0] == self.turn:
                self.selected = (row, col)
                self.valid_moves = self.legal_moves(row, col)

    # ==================== 渲染 ====================
    def draw(self):
        """绘制画面"""
        self.screen.fill(PANEL_BG)

        # ----- 棋盘 -----
        for r in range(8):
            for c in range(8):
                color = LIGHT_BROWN if (r + c) % 2 == 0 else DARK_BROWN
                rect = (c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(self.screen, color, rect)

        # 高亮上一步
        if self.last_move:
            for r, c in self.last_move:
                surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                surf.fill((255, 255, 100, 80))
                self.screen.blit(surf, (c * SQUARE_SIZE, r * SQUARE_SIZE))

        # 高亮选中棋子
        if self.selected:
            r, c = self.selected
            surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            surf.fill((255, 255, 0, 100))
            self.screen.blit(surf, (c * SQUARE_SIZE, r * SQUARE_SIZE))

        # 标记合法走法
        for r, c in self.valid_moves:
            surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            if self.board[r][c]:
                surf.fill((255, 0, 0, 60))
                pygame.draw.circle(surf, (255, 50, 50, 200),
                                   (SQUARE_SIZE // 2, SQUARE_SIZE // 2),
                                   SQUARE_SIZE // 2 - 4, 4)
            else:
                surf.fill((0, 200, 0, 40))
                pygame.draw.circle(surf, (0, 200, 0, 160),
                                   (SQUARE_SIZE // 2, SQUARE_SIZE // 2), 10)
            self.screen.blit(surf, (c * SQUARE_SIZE, r * SQUARE_SIZE))

        # 绘制棋子
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece:
                    color, ptype = piece
                    sym = PIECE_SYMBOLS[f'{color}{ptype}']
                    text = self.font_large.render(sym, True, BLACK)
                    if color == 'w':
                        # 给白棋加描边
                        for ox, oy in ((-1, -1), (1, 1)):
                            outline = self.font_large.render(sym, True, (60, 60, 60))
                            self.screen.blit(outline, (c * SQUARE_SIZE + 20 + ox,
                                                        r * SQUARE_SIZE + 12 + oy))
                    rect = text.get_rect(center=(c * SQUARE_SIZE + SQUARE_SIZE // 2,
                                                  r * SQUARE_SIZE + SQUARE_SIZE // 2))
                    self.screen.blit(text, rect)

        # 棋盘边框
        pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, WINDOW_SIZE, WINDOW_SIZE), 3)

        # 坐标标注
        for i in range(8):
            # 行号
            lbl = self.font_small.render(str(8 - i), True, (180, 180, 180))
            self.screen.blit(lbl, (4, i * SQUARE_SIZE + 4))
            # 列号
            lbl = self.font_small.render(chr(ord('a') + i), True, (180, 180, 180))
            self.screen.blit(lbl, (i * SQUARE_SIZE + SQUARE_SIZE - 18, WINDOW_SIZE - 22))

        # ----- 信息面板 -----
        px = WINDOW_SIZE + 12
        texts = [
            ("国际象棋", self.font_small, GOLD, None),
            ("", None, None, None),
            (f"回合: {'白方' if self.turn == 'w' else '黑方'}", self.font_small, WHITE, None),
            ("", None, None, None),
            ("—— 走法记录 ——", self.font_small, (160, 160, 160), None),
        ]
        for txt, font, color, _ in texts:
            if txt:
                surf = font.render(txt, True, color)
                self.screen.blit(surf, (px, 10 + texts.index((txt, font, color, None)) * 26))

        # 走法历史
        y = 130
        for move in self.move_history[-22:]:
            surf = self.font_small.render(move, True, (200, 200, 200))
            self.screen.blit(surf, (px, y))
            y += 22

        # 操作提示
        y = WINDOW_HEIGHT - 60
        for hint in ["[R] 重新开始", "[ESC] 退出"]:
            surf = self.font_small.render(hint, True, (120, 120, 120))
            self.screen.blit(surf, (px, y))
            y += 22

        # ----- 游戏结束遮罩 -----
        if self.game_over:
            overlay = pygame.Surface((WINDOW_SIZE, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            if self.winner:
                msg = f"{'白方' if self.winner == 'w' else '黑方'}获胜！"
            else:
                msg = "和棋！"
            text = self.font_big.render(msg, True, GOLD)
            text_rect = text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_HEIGHT // 2 - 25))
            self.screen.blit(text, text_rect)
            sub = self.font_small.render("点击任意位置重新开始", True, WHITE)
            sub_rect = sub.get_rect(center=(WINDOW_SIZE // 2, WINDOW_HEIGHT // 2 + 30))
            self.screen.blit(sub, sub_rect)

        pygame.display.flip()

    # ==================== 主循环 ====================
    def run(self):
        """游戏主循环"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        running = False
            self.draw()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    game = ChessGame()
    game.run()