"""
dr_mario.py - Dr. Mario 马里奥医生 药丸消除病毒游戏

玩法说明：
  - 彩色药丸从瓶口下落，玩家需要移动和旋转药丸
  - 将同色药丸块与病毒连成4个及以上（横竖均可）即可消除
  - 消除所有病毒即获胜，药丸堆满瓶子则失败
  - 一次性消除越多、连锁消除得分越高

操作方式：
  ← →  左右移动
  ↑     旋转药丸
  ↓     加速下落
  空格  直接落底
  R     重新开始

依赖：pip install pygame
"""

import pygame
import random
import sys
import math

# ─── 游戏常量 ─────────────────────────────────────────────
GRID_COLS = 8
GRID_ROWS = 16
CELL = 30
BOARD_L = 110
BOARD_T = 40
WIN_W = 520
WIN_H = 540

# 颜色
BLACK = (10, 10, 10)
WHITE = (240, 240, 240)
GRAY = (70, 70, 70)
DARK = (30, 30, 30)
RED = (255, 60, 60)
YELLOW = (255, 230, 60)
BLUE = (60, 160, 255)
GREEN = (60, 255, 100)
COLORS = {1: RED, 2: YELLOW, 3: BLUE}
VIRUS_COLORS = {1: (200, 30, 30), 2: (200, 180, 30), 3: (30, 120, 210)}

FPS = 60
INITIAL_SPEED = 28  # 下落间隔帧数
VIRUS_PER_COLOR = 4


class DrMario:
    """Dr. Mario 主游戏类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Dr. Mario — 马里奥医生")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simsun", 18)
        self.big_font = pygame.font.SysFont("simsun", 40)
        self.small_font = pygame.font.SysFont("simsun", 14)
        self.reset_game()

    # ─── 初始化 ───────────────────────────────────────────

    def reset_game(self):
        """重置游戏状态"""
        # 0=空, >0=药丸块(颜色ID), <0=病毒(-颜色ID)
        self.grid = [[0] * GRID_COLS for _ in range(GRID_ROWS)]
        self.score = 0
        self.combo = 0
        self.virus_left = 0
        self.game_over = False
        self.won = False
        self.speed = INITIAL_SPEED
        self.fall_timer = 0
        self.clearing = False
        self.clear_anim = []  # 消除动画帧
        self.anim_timer = 0

        self._place_viruses()
        self._spawn_pill()

    def _place_viruses(self):
        """在底部区域随机放置病毒"""
        for color_id in (1, 2, 3):
            for _ in range(VIRUS_PER_COLOR):
                for _ in range(200):
                    row = random.randint(GRID_ROWS - 7, GRID_ROWS - 2)
                    col = random.randint(1, GRID_COLS - 2)
                    if self.grid[row][col] == 0:
                        self.grid[row][col] = -color_id
                        self.virus_left += 1
                        break

    def _spawn_pill(self):
        """生成新药丸（两个半块，颜色随机）"""
        c1 = random.randint(1, 3)
        c2 = random.randint(1, 3)
        self.pill = {
            "blocks": [
                {"r": 0, "c": GRID_COLS // 2 - 1, "color": c1},
                {"r": 0, "c": GRID_COLS // 2, "color": c2},
            ],
            "rot": 0,  # 0=水平, 1=垂直(左块在上)
        }
        self.pill_active = True

        if self._collides(self.pill["blocks"]):
            self.game_over = True
            self.pill_active = False

    # ─── 碰撞检测 ─────────────────────────────────────────

    def _collides(self, blocks):
        """检测一组块是否与网格或边界碰撞"""
        for b in blocks:
            r, c = b["r"], b["c"]
            if not (0 <= r < GRID_ROWS and 0 <= c < GRID_COLS):
                return True
            if self.grid[r][c] != 0:
                return True
        return False

    # ─── 药丸操作 ─────────────────────────────────────────

    def _move(self, dr, dc):
        """移动药丸，成功返回 True"""
        if not self.pill_active or self.game_over or self.clearing:
            return False
        new = [{"r": b["r"] + dr, "c": b["c"] + dc, "color": b["color"]}
               for b in self.pill["blocks"]]
        if not self._collides(new):
            self.pill["blocks"] = new
            return True
        return False

    def _rotate(self):
        """旋转药丸"""
        if not self.pill_active or self.game_over or self.clearing:
            return
        b = self.pill["blocks"]
        r0, c0 = b[0]["r"], b[0]["c"]

        if self.pill["rot"] == 0:  # 水平→垂直
            new = [
                {"r": r0, "c": c0, "color": b[0]["color"]},
                {"r": r0 + 1, "c": c0, "color": b[1]["color"]},
            ]
        else:  # 垂直→水平
            new = [
                {"r": r0, "c": c0, "color": b[0]["color"]},
                {"r": r0, "c": c0 + 1, "color": b[1]["color"]},
            ]
        # 墙踢：如果旋转后碰撞，尝试左右微移
        if not self._collides(new):
            self.pill["blocks"] = new
            self.pill["rot"] = 1 - self.pill["rot"]
            return
        for kick in (-1, 1, -2, 2):
            kicked = [{"r": b["r"], "c": b["c"] + kick, "color": b["color"]} for b in new]
            if not self._collides(kicked):
                self.pill["blocks"] = kicked
                self.pill["rot"] = 1 - self.pill["rot"]
                return

    def _drop(self):
        """直接落底"""
        if not self.pill_active or self.game_over or self.clearing:
            return
        while self._move(1, 0):
            pass
        self._lock()

    def _lock(self):
        """将药丸固定到网格"""
        if not self.pill_active:
            return
        for b in self.pill["blocks"]:
            self.grid[b["r"]][b["c"]] = b["color"]
        self.pill_active = False
        self._check_matches()

    # ─── 匹配消除 ─────────────────────────────────────────

    def _check_matches(self):
        """查找并消除所有 4+ 连接的相同颜色（BFS）"""
        visited = [[False] * GRID_COLS for _ in range(GRID_ROWS)]
        all_to_clear = []
        any_cleared = False

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if self.grid[r][c] == 0 or visited[r][c]:
                    continue
                color = abs(self.grid[r][c])
                # BFS 找同色连通区域
                group = []
                stack = [(r, c)]
                visited[r][c] = True
                while stack:
                    cr, cc = stack.pop()
                    if abs(self.grid[cr][cc]) != color:
                        continue
                    group.append((cr, cc))
                    for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS and not visited[nr][nc]:
                            if self.grid[nr][nc] != 0 and abs(self.grid[nr][nc]) == color:
                                visited[nr][nc] = True
                                stack.append((nr, nc))

                # 连通区域 >= 4 且至少有一个药丸块
                if len(group) >= 4:
                    has_pill = any(self.grid[r][c] > 0 for r, c in group)
                    if has_pill:
                        all_to_clear.extend(group)
                        any_cleared = True

        if any_cleared:
            self.clearing = True
            self.clear_anim = all_to_clear
            self.anim_timer = 12  # 动画帧数
            self.combo += 1
            self.score += len(all_to_clear) * 10 * self.combo
        else:
            self.combo = 0
            self._after_clear()

    def _after_clear(self):
        """消除完成后的处理：下落 + 再检查 + 生成新药丸"""
        self.clearing = False
        self.clear_anim = []
        self._apply_gravity()
        # 检查是否有新的匹配
        self._check_matches()
        if not self.clearing:
            # 检查是否胜利
            if self.virus_left <= 0:
                self.won = True
                self.game_over = True
            self._spawn_pill()

    def _apply_gravity(self):
        """让悬空的块下落"""
        for c in range(GRID_COLS):
            write_row = GRID_ROWS - 1
            for r in range(GRID_ROWS - 1, -1, -1):
                # 跳过正在消除的块
                if (r, c) in self.clear_anim:
                    continue
                if self.grid[r][c] != 0:
                    self.grid[write_row][c] = self.grid[r][c]
                    write_row -= 1
            for r in range(write_row, -1, -1):
                self.grid[r][c] = 0

    # ─── 更新逻辑 ─────────────────────────────────────────

    def update(self):
        """每帧更新"""
        if self.game_over:
            return

        # 消除动画进行中
        if self.clearing:
            self.anim_timer -= 1
            if self.anim_timer <= 0:
                # 真正清除块
                for r, c in self.clear_anim:
                    if self.grid[r][c] < 0:
                        self.virus_left -= 1
                    self.grid[r][c] = 0
                self._after_clear()
            return

        # 自动下落
        if self.pill_active:
            self.fall_timer += 1
            if self.fall_timer >= self.speed:
                self.fall_timer = 0
                if not self._move(1, 0):
                    self._lock()

    # ─── 渲染 ─────────────────────────────────────────────

    def draw(self):
        """绘制所有内容"""
        self.screen.fill(BLACK)

        # 绘制瓶子背景
        bx, by = BOARD_L - 4, BOARD_T - 4
        bw, bh = GRID_COLS * CELL + 8, GRID_ROWS * CELL + 8
        # 瓶身阴影
        pygame.draw.rect(self.screen, (20, 20, 30), (bx + 2, by + 2, bw, bh), border_radius=6)
        pygame.draw.rect(self.screen, GRAY, (bx, by, bw, bh), 2, border_radius=6)

        # 瓶口
        neck_w = CELL * 4
        neck_x = BOARD_L + (GRID_COLS * CELL - neck_w) // 2
        pygame.draw.rect(self.screen, GRAY, (neck_x - 2, BOARD_T - 18, neck_w + 4, 16), 2, border_radius=3)

        # 绘制网格线（暗线）
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                x = BOARD_L + c * CELL
                y = BOARD_T + r * CELL
                if (r + c) % 2 == 0:
                    color = (22, 22, 30)
                else:
                    color = (18, 18, 25)
                pygame.draw.rect(self.screen, color, (x, y, CELL, CELL))

        # 绘制已固定的块
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                val = self.grid[r][c]
                if val == 0:
                    continue
                x = BOARD_L + c * CELL
                y = BOARD_T + r * CELL
                rect = pygame.Rect(x, y, CELL, CELL)

                if (r, c) in self.clear_anim and self.clearing:
                    # 消除动画：闪烁缩小
                    t = self.anim_timer / 12.0
                    size = int(CELL * t)
                    if size > 0:
                        anim_rect = pygame.Rect(0, 0, size, size)
                        anim_rect.center = rect.center
                        color = COLORS[abs(val)]
                        pygame.draw.rect(self.screen, color, anim_rect, border_radius=4)
                    continue

                abs_val = abs(val)
                if val > 0:  # 药丸块
                    self._draw_pill_block(x, y, abs_val)
                else:  # 病毒
                    self._draw_virus_block(x, y, abs_val)

        # 绘制当前活动药丸
        if self.pill_active:
            for b in self.pill["blocks"]:
                x = BOARD_L + b["c"] * CELL
                y = BOARD_T + b["r"] * CELL
                self._draw_pill_block(x, y, b["color"], alpha=255)

        # 绘制信息面板
        self._draw_info()

        # 游戏结束/胜利覆盖层
        if self.game_over:
            overlay = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            msg = "🎉 恭喜通关！" if self.won else "💊 游戏结束"
            color = GREEN if self.won else RED
            surf = self.big_font.render(msg, True, color)
            self.screen.blit(surf, (WIN_W // 2 - surf.get_width() // 2, WIN_H // 2 - 50))
            sub = self.font.render("按 R 重新开始", True, WHITE)
            self.screen.blit(sub, (WIN_W // 2 - sub.get_width() // 2, WIN_H // 2 + 10))

        pygame.display.flip()

    def _draw_pill_block(self, x, y, color_id, alpha=255):
        """绘制药丸块（圆角矩形+高光）"""
        rect = pygame.Rect(x + 2, y + 2, CELL - 4, CELL - 4)
        color = COLORS[color_id]
        s = pygame.Surface((CELL - 4, CELL - 4), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=5)
        # 高光
        highlight = pygame.Rect(4, 3, CELL - 14, 6)
        pygame.draw.rect(s, (255, 255, 255, min(80, alpha)), highlight, border_radius=3)
        self.screen.blit(s, (x + 2, y + 2))

    def _draw_virus_block(self, x, y, color_id):
        """绘制病毒块（带病毒标记）"""
        rect = pygame.Rect(x + 2, y + 2, CELL - 4, CELL - 4)
        color = COLORS[color_id]
        pygame.draw.rect(self.screen, color, rect, border_radius=5)
        # 病毒标记：中间白色圆圈 + 刺突
        cx, cy = x + CELL // 2, y + CELL // 2
        # 刺突
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            sx = cx + int(8 * math.cos(rad))
            sy = cy + int(8 * math.sin(rad))
            pygame.draw.circle(self.screen, (255, 255, 255, 200), (sx, sy), 3)
        # 白色底
        pygame.draw.circle(self.screen, WHITE, (cx, cy), 6)
        # 病毒眼
        pygame.draw.circle(self.screen, color, (cx - 2, cy - 1), 2)
        pygame.draw.circle(self.screen, color, (cx + 2, cy - 1), 2)

    def _draw_info(self):
        """绘制右侧信息面板"""
        ix = GRID_COLS * CELL + BOARD_L + 30
        iy = BOARD_T
        lines = [
            ("Dr. Mario", self.big_font, YELLOW),
            ("", None, None),
            (f"得分: {self.score}", self.font, WHITE),
            (f"病毒: {self.virus_left}", self.font, RED if self.virus_left > 0 else GREEN),
            (f"连击: x{self.combo}", self.font, YELLOW),
            ("", None, None),
            ("操作:", self.font, GRAY),
            ("← →  移动", self.small_font, WHITE),
            ("↑   旋转", self.small_font, WHITE),
            ("↓   加速", self.small_font, WHITE),
            ("空格 落底", self.small_font, WHITE),
            ("R   重开", self.small_font, WHITE),
            ("", None, None),
            ("规则:", self.small_font, GRAY),
            ("同色4+连接消除", self.small_font, WHITE),
            ("清除所有病毒获胜", self.small_font, WHITE),
        ]
        y = iy
        for text, font, color in lines:
            if text:
                surf = font.render(text, True, color)
                self.screen.blit(surf, (ix, y))
                y += surf.get_height() + 4
            else:
                y += 10

    # ─── 事件处理 ─────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.reset_game()
                return
            if self.game_over:
                return
            if event.key == pygame.K_LEFT:
                self._move(0, -1)
            elif event.key == pygame.K_RIGHT:
                self._move(0, 1)
            elif event.key == pygame.K_DOWN:
                if self._move(1, 0):
                    self.fall_timer = 0
            elif event.key == pygame.K_UP:
                self._rotate()
            elif event.key == pygame.K_SPACE:
                self._drop()

    # ─── 主循环 ───────────────────────────────────────────

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.handle_event(event)
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = DrMario()
    game.run()