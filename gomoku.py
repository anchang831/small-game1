"""
五子棋 (Gomoku) — 双人对战版
使用 tkinter 实现, 15×15 棋盘, 黑白双方轮流落子, 五子连珠即获胜
运行方式: python gomoku.py
"""

import tkinter as tk
from tkinter import messagebox

# ─── 游戏常量 ────────────────────────────────────────────────────────────────
BOARD_SIZE = 15          # 棋盘 15×15
CELL_SIZE = 36           # 每格像素
MARGIN = 28              # 边距
CANVAS_SIZE = MARGIN * 2 + CELL_SIZE * (BOARD_SIZE - 1)  # 画布总尺寸

EMPTY, BLACK, WHITE = 0, 1, 2

# ─── 主游戏类 ────────────────────────────────────────────────────────────────
class Gomoku:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("五子棋 · 双人对战")
        self.root.resizable(False, False)

        # 状态
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_player = BLACK  # 黑先
        self.game_over = False

        # 画布
        self.cv = tk.Canvas(self.root, width=CANVAS_SIZE, height=CANVAS_SIZE,
                            bg="#DEB887", highlightthickness=0)
        self.cv.pack(padx=10, pady=(10, 0))
        self.cv.bind("<Button-1>", self.on_click)

        # 信息栏
        self.info_frame = tk.Frame(self.root)
        self.info_frame.pack(fill="x", padx=10, pady=(5, 10))

        self.status_var = tk.StringVar()
        self.status_var.set("黑棋走")
        self.status_label = tk.Label(self.info_frame, textvariable=self.status_var,
                                     font=("Microsoft YaHei", 14, "bold"))
        self.status_label.pack(side="left", padx=5)

        self.restart_btn = tk.Button(self.info_frame, text="重新开始",
                                     font=("Microsoft YaHei", 12),
                                     command=self.restart)
        self.restart_btn.pack(side="right", padx=5)

        self.draw_board()

    # ─── 绘制棋盘 ──────────────────────────────────────────────────────────
    def draw_board(self):
        self.cv.delete("all")

        # 画网格线
        for i in range(BOARD_SIZE):
            x = MARGIN + i * CELL_SIZE
            self.cv.create_line(x, MARGIN, x, MARGIN + (BOARD_SIZE - 1) * CELL_SIZE,
                                fill="#333", width=1)
            y = MARGIN + i * CELL_SIZE
            self.cv.create_line(MARGIN, y, MARGIN + (BOARD_SIZE - 1) * CELL_SIZE, y,
                                fill="#333", width=1)

        # 画星位（天元 + 四角星）
        star_points = [(3, 3), (3, 7), (3, 11),
                       (7, 3), (7, 7), (7, 11),
                       (11, 3), (11, 7), (11, 11)]
        for (r, c) in star_points:
            x = MARGIN + c * CELL_SIZE
            y = MARGIN + r * CELL_SIZE
            self.cv.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#333", outline="")

        # 画已有棋子
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                stone = self.board[r][c]
                if stone != EMPTY:
                    x = MARGIN + c * CELL_SIZE
                    y = MARGIN + r * CELL_SIZE
                    color = "#111" if stone == BLACK else "#F5F5F5"
                    outline = "#666"
                    self.cv.create_oval(x - 14, y - 14, x + 14, y + 14,
                                        fill=color, outline=outline, width=1)

    # ─── 鼠标点击 ──────────────────────────────────────────────────────────
    def on_click(self, event):
        if self.game_over:
            return

        # 计算最近的交叉点
        col = round((event.x - MARGIN) / CELL_SIZE)
        row = round((event.y - MARGIN) / CELL_SIZE)

        if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
            return
        if self.board[row][col] != EMPTY:
            return

        # 落子
        self.board[row][col] = self.current_player
        self.draw_board()

        # 检查胜负
        if self.check_win(row, col, self.current_player):
            winner = "黑棋" if self.current_player == BLACK else "白棋"
            self.game_over = True
            self.status_var.set(f"{winner}获胜！")
            messagebox.showinfo("游戏结束", f"{winner}获胜！")
            return

        # 检查平局
        if all(self.board[r][c] != EMPTY for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)):
            self.game_over = True
            self.status_var.set("平局！")
            messagebox.showinfo("游戏结束", "平局！")
            return

        # 切换玩家
        self.current_player = WHITE if self.current_player == BLACK else BLACK
        self.status_var.set("黑棋走" if self.current_player == BLACK else "白棋走")

    # ─── 胜负判断（八方向扫描） ──────────────────────────────────────────────
    def check_win(self, row, col, player):
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]  # 竖 | 横 | 捺 | 撇

        for dr, dc in directions:
            count = 1
            # 正方向
            r, c = row + dr, col + dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r][c] == player:
                count += 1
                r += dr
                c += dc
            # 反方向
            r, c = row - dr, col - dc
            while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and self.board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if count >= 5:
                return True
        return False

    # ─── 重新开始 ──────────────────────────────────────────────────────────
    def restart(self):
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_player = BLACK
        self.game_over = False
        self.status_var.set("黑棋走")
        self.draw_board()

    # ─── 启动 ──────────────────────────────────────────────────────────────
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    Gomoku().run()