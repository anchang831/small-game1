#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数独 (Sudoku) - 经典数字逻辑游戏
===============================
游戏规则：在 9x9 的网格中填入数字 1-9，
使得每行、每列和每个 3x3 宫格内数字不重复。

操作说明：
- 鼠标点击选中格子
- 数字键 1-9 填入数字
- Delete/Backspace 清除数字
- Shift+数字 添加笔记（候选数字）
- R 键重新开始
- H 键提示
"""

import pygame
import random
import sys
import copy
import time

# ---------- 常量 ----------
WIDTH, HEIGHT = 600, 700
GRID_SIZE = 9
CELL_SIZE = 60
GRID_POS_X = (WIDTH - CELL_SIZE * 9) // 2
GRID_POS_Y = 100
LINE_WIDTH = 2
THICK_LINE_WIDTH = 4

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
LIGHT_BLUE = (173, 216, 230)
BLUE = (70, 130, 180)
RED = (220, 50, 50)
GREEN = (50, 180, 50)
ORANGE = (255, 165, 0)
LIGHT_GRAY = (245, 245, 245)
CELL_BG = (255, 255, 255)
SELECTED_COLOR = (173, 216, 230)  # light blue
SAME_NUMBER_COLOR = (200, 220, 240)
CONFLICT_COLOR = (255, 200, 200)
NOTE_COLOR = (130, 130, 130)

# 难度配置 (要移除的格子数)
DIFFICULTY = {
    "简单": 30,
    "中等": 45,
    "困难": 55,
}


class Sudoku:
    """数独游戏核心逻辑"""

    def __init__(self, difficulty="中等"):
        self.difficulty = difficulty
        self.reset()

    def reset(self, difficulty=None):
        if difficulty:
            self.difficulty = difficulty
        # 生成完整解
        self.solution = self._generate_solution()
        # 挖空生成谜题
        self.board = copy.deepcopy(self.solution)
        self._remove_numbers()
        # 当前玩家填入的状态
        self.player_board = copy.deepcopy(self.board)
        # 笔记模式：player_notes[r][c] = set of numbers
        self.player_notes = [[set() for _ in range(9)] for _ in range(9)]
        # 标注哪些格子是初始给定的
        self.given = [[self.board[r][c] != 0 for c in range(9)] for r in range(9)]
        self.start_time = time.time()
        self.paused = False
        self.pause_start = 0
        self.total_pause_time = 0
        self.completed = False
        self.selected = None  # (r, c)
        self.note_mode = False

    def _generate_solution(self):
        """用回溯算法生成一个完整的数独解"""
        board = [[0] * 9 for _ in range(9)]
        self._solve(board)
        return board

    def _solve(self, board):
        """回溯求解数独（可求解也可生成）"""
        empty = self._find_empty(board)
        if not empty:
            return True
        r, c = empty
        nums = list(range(1, 10))
        random.shuffle(nums)
        for num in nums:
            if self._is_valid(board, r, c, num):
                board[r][c] = num
                if self._solve(board):
                    return True
                board[r][c] = 0
        return False

    def _find_empty(self, board):
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    return (r, c)
        return None

    def _is_valid(self, board, row, col, num):
        """检查在 (row, col) 放置 num 是否合法"""
        # 检查行
        if num in board[row]:
            return False
        # 检查列
        for r in range(9):
            if board[r][col] == num:
                return False
        # 检查 3x3 宫
        box_r, box_c = (row // 3) * 3, (col // 3) * 3
        for r in range(box_r, box_r + 3):
            for c in range(box_c, box_c + 3):
                if board[r][c] == num:
                    return False
        return True

    def _remove_numbers(self):
        """根据难度挖空"""
        cells = [(r, c) for r in range(9) for c in range(9)]
        random.shuffle(cells)
        to_remove = DIFFICULTY[self.difficulty]
        removed = 0
        for r, c in cells:
            if removed >= to_remove:
                break
            self.board[r][c] = 0
            removed += 1

    def select(self, r, c):
        if 0 <= r < 9 and 0 <= c < 9:
            self.selected = (r, c)

    def input_number(self, num):
        """在选中格子填入数字"""
        if not self.selected or self.completed:
            return
        r, c = self.selected
        if self.given[r][c]:
            return  # 初始格子不可修改
        if self.note_mode:
            # 笔记模式：切换候选数字
            if num in self.player_notes[r][c]:
                self.player_notes[r][c].discard(num)
            else:
                self.player_notes[r][c].add(num)
            self.player_board[r][c] = 0
        else:
            # 普通模式：填入数字（清除笔记）
            self.player_notes[r][c].clear()
            self.player_board[r][c] = num
            # 检查是否完成
            if self._check_complete():
                self.completed = True

    def clear_cell(self):
        """清除选中格子的数字和笔记"""
        if not self.selected or self.completed:
            return
        r, c = self.selected
        if self.given[r][c]:
            return
        self.player_board[r][c] = 0
        self.player_notes[r][c].clear()

    def give_hint(self):
        """给一个提示：随机填对一个空格"""
        if self.completed:
            return
        # 收集所有未填或填错的格子
        empty_or_wrong = []
        for r in range(9):
            for c in range(9):
                if not self.given[r][c]:
                    if self.player_board[r][c] != self.solution[r][c]:
                        empty_or_wrong.append((r, c))
        if not empty_or_wrong:
            return
        r, c = random.choice(empty_or_wrong)
        self.player_board[r][c] = self.solution[r][c]
        self.player_notes[r][c].clear()
        if self._check_complete():
            self.completed = True
        # 选中提示的格子
        self.selected = (r, c)

    def _check_complete(self):
        for r in range(9):
            for c in range(9):
                if self.player_board[r][c] != self.solution[r][c]:
                    return False
        return True

    def get_elapsed_time(self):
        if self.paused:
            return int(self.pause_start - self.start_time - self.total_pause_time)
        now = time.time()
        return int(now - self.start_time - self.total_pause_time)

    def toggle_pause(self):
        if self.completed:
            return
        if self.paused:
            self.total_pause_time += time.time() - self.pause_start
            self.paused = False
        else:
            self.pause_start = time.time()
            self.paused = True

    def get_conflicts(self):
        """返回所有冲突的格子坐标列表"""
        conflicts = set()
        # 检查行
        for r in range(9):
            seen = {}
            for c in range(9):
                val = self.player_board[r][c]
                if val == 0:
                    continue
                if val in seen:
                    conflicts.add((r, c))
                    conflicts.add(seen[val])
                else:
                    seen[val] = (r, c)
        # 检查列
        for c in range(9):
            seen = {}
            for r in range(9):
                val = self.player_board[r][c]
                if val == 0:
                    continue
                if val in seen:
                    conflicts.add((r, c))
                    conflicts.add(seen[val])
                else:
                    seen[val] = (r, c)
        # 检查宫格
        for box_r in range(0, 9, 3):
            for box_c in range(0, 9, 3):
                seen = {}
                for dr in range(3):
                    for dc in range(3):
                        r, c = box_r + dr, box_c + dc
                        val = self.player_board[r][c]
                        if val == 0:
                            continue
                        if val in seen:
                            conflicts.add((r, c))
                            conflicts.add(seen[val])
                        else:
                            seen[val] = (r, c)
        return conflicts


class Game:
    """游戏渲染与主循环"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("数独 Sudoku")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("simhei, sans-serif", 36)
        self.font_mid = pygame.font.SysFont("simhei, sans-serif", 24)
        self.font_small = pygame.font.SysFont("simhei, sans-serif", 18)
        self.font_num = pygame.font.SysFont("simhei, sans-serif", 40)
        self.font_note = pygame.font.SysFont("simhei, sans-serif", 16)
        self.difficulties = ["简单", "中等", "困难"]
        self.diff_index = 1
        self.sudoku = Sudoku(self.difficulties[self.diff_index])
        self.menu_active = True
        self.show_complete = False
        self.complete_timer = 0
        self.wrong_anim = 0  # 错误提示帧数
        self.last_hint_time = 0

    def draw_menu(self):
        """绘制主菜单"""
        self.screen.fill(WHITE)
        # 标题
        title = self.font_large.render("数 独", True, BLACK)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))
        subtitle = self.font_mid.render("Sudoku", True, DARK_GRAY)
        self.screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 200))

        # 难度选择
        y_start = 300
        for i, diff in enumerate(self.difficulties):
            color = BLUE if i == self.diff_index else DARK_GRAY
            rect = pygame.Rect(WIDTH // 2 - 80, y_start + i * 60, 160, 45)
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            if i == self.diff_index:
                pygame.draw.rect(self.screen, color, rect, border_radius=8)
                text = self.font_mid.render(diff, True, WHITE)
            else:
                pygame.draw.rect(self.screen, GRAY, rect, border_radius=8)
                text = self.font_mid.render(diff, True, BLACK)
            self.screen.blit(text, (rect.centerx - text.get_width() // 2,
                                    rect.centery - text.get_height() // 2))

        # 开始按钮
        btn_rect = pygame.Rect(WIDTH // 2 - 80, 500, 160, 50)
        pygame.draw.rect(self.screen, GREEN, btn_rect, border_radius=10)
        start_text = self.font_mid.render("开始游戏", True, WHITE)
        self.screen.blit(start_text, (btn_rect.centerx - start_text.get_width() // 2,
                                       btn_rect.centery - start_text.get_height() // 2))

        # 操作说明
        instr = [
            "操作说明:",
            "鼠标点击选中格子  |  数字键 1-9 填入",
            "Shift + 数字键添加/取消笔记",
            "Delete/Backspace 清除  |  H 键提示",
            "R 重新开始  |  空格暂停"
        ]
        for i, line in enumerate(instr):
            txt = self.font_small.render(line, True, DARK_GRAY)
            self.screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 570 + i * 22))

        pygame.display.flip()
        return btn_rect

    def handle_menu_click(self, pos, btn_rect):
        x, y = pos
        # 检测难度点击
        y_start = 300
        for i in range(len(self.difficulties)):
            rect = pygame.Rect(WIDTH // 2 - 80, y_start + i * 60, 160, 45)
            if rect.collidepoint(x, y):
                self.diff_index = i
                return False
        # 检测开始按钮
        if btn_rect.collidepoint(x, y):
            self.sudoku = Sudoku(self.difficulties[self.diff_index])
            self.menu_active = False
            self.show_complete = False
            return True
        return False

    def draw_grid(self):
        """绘制数独网格"""
        # 背景
        board_rect = pygame.Rect(GRID_POS_X - 10, GRID_POS_Y - 10,
                                 CELL_SIZE * 9 + 20, CELL_SIZE * 9 + 20)
        pygame.draw.rect(self.screen, LIGHT_GRAY, board_rect, border_radius=4)

        conflicts = self.sudoku.get_conflicts()
        selected = self.sudoku.selected
        note_mode = self.sudoku.note_mode

        # 绘制格子
        for r in range(9):
            for c in range(9):
                x = GRID_POS_X + c * CELL_SIZE
                y = GRID_POS_Y + r * CELL_SIZE
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

                # 背景色
                bg_color = CELL_BG
                val = self.sudoku.player_board[r][c]
                if selected == (r, c):
                    bg_color = SELECTED_COLOR
                elif val != 0 and selected and val == self.sudoku.player_board[selected[0]][selected[1]]:
                    bg_color = SAME_NUMBER_COLOR
                if (r, c) in conflicts and not self.sudoku.given[r][c]:
                    bg_color = CONFLICT_COLOR

                pygame.draw.rect(self.screen, bg_color, rect)
                pygame.draw.rect(self.screen, GRAY, rect, 1)

                # 给定数字用粗体黑色
                if val != 0:
                    if self.sudoku.given[r][c]:
                        color = BLACK
                    elif (r, c) in conflicts:
                        color = RED
                    else:
                        color = BLUE
                    text = self.font_num.render(str(val), True, color)
                    self.screen.blit(text, (rect.centerx - text.get_width() // 2,
                                            rect.centery - text.get_height() // 2))
                # 笔记数字
                elif self.sudoku.player_notes[r][c]:
                    notes = self.sudoku.player_notes[r][c]
                    for num in range(1, 10):
                        if num in notes:
                            nx = x + ((num - 1) % 3) * (CELL_SIZE // 3) + (CELL_SIZE // 6)
                            ny = y + ((num - 1) // 3) * (CELL_SIZE // 3) + (CELL_SIZE // 6)
                            nt = self.font_note.render(str(num), True, NOTE_COLOR)
                            self.screen.blit(nt, (nx - nt.get_width() // 2,
                                                   ny - nt.get_height() // 2))

        # 粗框线 (3x3 宫格边界)
        for i in range(4):
            px = GRID_POS_X + i * 3 * CELL_SIZE
            py = GRID_POS_Y + i * 3 * CELL_SIZE
            pygame.draw.line(self.screen, BLACK, (px, GRID_POS_Y),
                             (px, GRID_POS_Y + 9 * CELL_SIZE), THICK_LINE_WIDTH)
            pygame.draw.line(self.screen, BLACK, (GRID_POS_X, py),
                             (GRID_POS_X + 9 * CELL_SIZE, py), THICK_LINE_WIDTH)

        # 笔记模式指示
        if note_mode:
            mode_text = self.font_small.render("[笔记模式] N切换", True, ORANGE)
            self.screen.blit(mode_text, (WIDTH // 2 - mode_text.get_width() // 2,
                                          GRID_POS_Y + 9 * CELL_SIZE + 15))

    def draw_hud(self):
        """绘制顶部信息（难度、计时、操作提示）"""
        # 左侧：难度和状态
        diff_text = self.font_mid.render(f"难度: {self.sudoku.difficulty}", True, DARK_GRAY)
        self.screen.blit(diff_text, (20, 20))

        # 右侧：计时
        if self.sudoku.paused:
            timer_str = "已暂停"
            timer_color = ORANGE
        else:
            elapsed = self.sudoku.get_elapsed_time()
            timer_str = f"{elapsed // 60:02d}:{elapsed % 60:02d}"
            timer_color = BLACK
        timer_surf = self.font_mid.render(timer_str, True, timer_color)
        self.screen.blit(timer_surf, (WIDTH - timer_surf.get_width() - 20, 20))

        # 暂停状态
        if self.sudoku.paused:
            pause_text = self.font_large.render("PAUSED", True, ORANGE)
            self.screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, 50))

        # 顶部提示
        hint_text = self.font_small.render("R:重开  H:提示  空格:暂停  N:笔记", True, GRAY)
        self.screen.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, 65))

        # 完成提示
        if self.show_complete:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 200))
            self.screen.blit(overlay, (0, 0))
            complete_text = self.font_large.render("恭喜完成!", True, GREEN)
            self.screen.blit(complete_text, (WIDTH // 2 - complete_text.get_width() // 2,
                                              HEIGHT // 2 - 60))
            time_str = f"用时: {self._format_time(self.sudoku.get_elapsed_time())}"
            time_surf = self.font_mid.render(time_str, True, BLACK)
            self.screen.blit(time_surf, (WIDTH // 2 - time_surf.get_width() // 2,
                                          HEIGHT // 2 - 10))
            sub = self.font_small.render("按 R 重新开始  |  点击任意处继续", True, DARK_GRAY)
            self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 40))

    def _format_time(self, secs):
        return f"{secs // 60:02d}:{secs % 60:02d}"

    def get_cell_from_pos(self, pos):
        x, y = pos
        if (GRID_POS_X <= x < GRID_POS_X + 9 * CELL_SIZE and
                GRID_POS_Y <= y < GRID_POS_Y + 9 * CELL_SIZE):
            c = (x - GRID_POS_X) // CELL_SIZE
            r = (y - GRID_POS_Y) // CELL_SIZE
            return int(r), int(c)
        return None

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(30)
            if self.menu_active:
                btn_rect = self.draw_menu()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        self.handle_menu_click(event.pos, btn_rect)
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                continue

            # ------ 游戏内循环 ------
            if not self.sudoku.paused and not self.show_complete:
                self.sudoku.get_elapsed_time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.menu_active = True
                        continue

                    if self.show_complete:
                        if event.key == pygame.K_r:
                            self.sudoku = Sudoku(self.difficulties[self.diff_index])
                            self.show_complete = False
                        continue

                    if event.key == pygame.K_SPACE:
                        self.sudoku.toggle_pause()
                        continue

                    if event.key == pygame.K_r:
                        self.sudoku = Sudoku(self.difficulties[self.diff_index])
                        self.show_complete = False
                        continue

                    if event.key == pygame.K_n:
                        self.sudoku.note_mode = not self.sudoku.note_mode
                        continue

                    if event.key == pygame.K_h:
                        now = time.time()
                        if now - self.last_hint_time > 1.0:
                            self.sudoku.give_hint()
                            self.last_hint_time = now
                        continue

                    if event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                        self.sudoku.clear_cell()
                        continue

                    if self.sudoku.paused:
                        continue

                    # 数字输入
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        num = event.key - pygame.K_0
                        # Shift 进入笔记模式（即临时笔记输入）
                        if event.mod & pygame.KMOD_SHIFT:
                            old_note = self.sudoku.note_mode
                            self.sudoku.note_mode = True
                            self.sudoku.input_number(num)
                            self.sudoku.note_mode = old_note
                        else:
                            self.sudoku.input_number(num)
                            if self.sudoku.completed:
                                self.show_complete = True
                                self.complete_timer = time.time()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.show_complete:
                        self.show_complete = False
                        self.menu_active = True
                        continue
                    cell = self.get_cell_from_pos(event.pos)
                    if cell:
                        self.sudoku.select(cell[0], cell[1])

            # 绘制
            self.screen.fill(WHITE)
            self.draw_hud()
            if not self.sudoku.paused or self.show_complete:
                self.draw_grid()
            else:
                self.draw_grid()  # still draw grid but HUD shows PAUSED
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()