"""
Lights Out 关灯游戏
===================
经典电子谜题游戏：点击灯光切换其及相邻灯的状态，目标是将所有灯熄灭。

规则：
- 5x5 网格，每盏灯可亮(黄)可灭(黑)
- 点击一盏灯会切换它及其上下左右邻居的状态
- 目标：熄灭所有灯
- 使用最少步数完成挑战！

作者：AI 游戏开发者
日期：2026-08-02
"""

import pygame
import random
import sys
from copy import deepcopy

# ==================== 常量设置 ====================
GRID_SIZE = 5            # 5x5 网格
CELL_SIZE = 100           # 每格像素
GAP = 6                   # 格间距
MARGIN_X = 60             # 左右边距
MARGIN_Y = 120            # 上边距（给标题留空间）

# 颜色定义
COLOR_BG = (30, 30, 40)           # 深色背景
COLOR_GRID_BG = (20, 20, 28)      # 网格背景
COLOR_LIGHT_ON = (255, 220, 50)   # 灯亮 - 暖黄色
COLOR_LIGHT_ON_GLOW = (255, 200, 30)  # 灯亮发光
COLOR_LIGHT_OFF = (35, 35, 45)    # 灯灭 - 深灰
COLOR_LIGHT_OFF_BORDER = (50, 50, 65)  # 灯灭边框
COLOR_LIGHT_ON_BORDER = (255, 200, 20) # 灯亮边框
COLOR_TEXT = (220, 220, 230)      # 文字颜色
COLOR_TITLE = (255, 220, 50)      # 标题颜色
COLOR_BUTTON = (60, 60, 80)       # 按钮背景
COLOR_BUTTON_HOVER = (80, 80, 110) # 按钮悬停
COLOR_BUTTON_TEXT = (220, 220, 230)
COLOR_MOVE_COUNT = (180, 180, 200)
COLOR_VICTORY = (50, 220, 100)    # 胜利绿色
COLOR_PARTICLE = (255, 220, 50)   # 粒子颜色

# 窗口尺寸
WINDOW_WIDTH = GRID_SIZE * (CELL_SIZE + GAP) + MARGIN_X * 2 - GAP
WINDOW_HEIGHT = GRID_SIZE * (CELL_SIZE + GAP) + MARGIN_Y * 2 - GAP
FPS = 60


class Particle:
    """胜利时的粒子特效"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        angle = random.uniform(0, 360)
        speed = random.uniform(2, 8)
        self.vx = speed * pygame.math.Vector2(1, 0).rotate(angle).x
        self.vy = speed * pygame.math.Vector2(1, 0).rotate(angle).y
        self.life = random.randint(30, 80)
        self.max_life = self.life
        self.size = random.randint(3, 7)
        # 随机颜色（金色/暖色系）
        self.color = (
            random.randint(200, 255),
            random.randint(150, 220),
            random.randint(20, 80),
        )

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1  # 重力
        self.life -= 1
        return self.life > 0

    def draw(self, screen):
        alpha = self.life / self.max_life
        size = int(self.size * alpha)
        if size > 0:
            color = tuple(int(c * alpha) for c in self.color)
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), size)


class LightsOut:
    """Lights Out 游戏主逻辑"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Lights Out - 关灯游戏")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 56)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 28)

        # 游戏状态
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.move_count = 0
        self.game_over = False
        self.particles = []
        self.particle_timer = 0
        self.hover_cell = None  # 鼠标悬停的格子

        # 按钮
        self.new_game_btn = pygame.Rect(
            WINDOW_WIDTH // 2 - 80, WINDOW_HEIGHT - 70, 160, 45
        )
        self.hint_btn = pygame.Rect(
            WINDOW_WIDTH // 2 - 80, WINDOW_HEIGHT - 125, 160, 40
        )
        self.showing_hint = False
        self.hint_cells = []

        # 启动新游戏
        self.new_game()

    def new_game(self):
        """生成一个可解的随机谜题"""
        # 从一个熄灭状态开始，随机按若干次（保证可解）
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.move_count = 0
        self.game_over = False
        self.particles = []
        self.showing_hint = False
        self.hint_cells = []

        # 随机按 15-30 次产生谜题
        steps = random.randint(15, 30)
        for _ in range(steps):
            r = random.randint(0, GRID_SIZE - 1)
            c = random.randint(0, GRID_SIZE - 1)
            self._toggle(r, c)

        # 如果恰好全灭（概率极低），重新生成
        if self._check_win():
            self.new_game()
            return

    def _toggle(self, row, col):
        """切换指定位置及其邻居的灯状态"""
        self.grid[row][col] ^= 1
        if row > 0:
            self.grid[row - 1][col] ^= 1
        if row < GRID_SIZE - 1:
            self.grid[row + 1][col] ^= 1
        if col > 0:
            self.grid[row][col - 1] ^= 1
        if col < GRID_SIZE - 1:
            self.grid[row][col + 1] ^= 1

    def _check_win(self):
        """检查是否所有灯都已熄灭"""
        for row in self.grid:
            if any(row):
                return False
        return True

    def handle_click(self, pos):
        """处理鼠标点击"""
        if self.game_over:
            # 获胜后点击任意位置重新开始
            self.new_game()
            return

        # 检查按钮
        if self.new_game_btn.collidepoint(pos):
            self.new_game()
            return
        if self.hint_btn.collidepoint(pos):
            self._show_hint()
            return

        # 检查网格点击
        cell = self._pos_to_cell(pos)
        if cell:
            row, col = cell
            self._toggle(row, col)
            self.move_count += 1
            self.showing_hint = False
            self.hint_cells = []

            if self._check_win():
                self.game_over = True
                # 产生胜利粒子特效
                for _ in range(60):
                    self.particles.append(Particle(
                        random.randint(MARGIN_X, WINDOW_WIDTH - MARGIN_X),
                        random.randint(MARGIN_Y, WINDOW_HEIGHT - MARGIN_Y),
                    ))

    def _show_hint(self):
        """显示提示：标记一个能熄灭最多灯的位置"""
        self.showing_hint = True
        self.hint_cells = []
        best_score = -1
        best_moves = []

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                score = 0
                if self.grid[r][c]:
                    score += 1
                if r > 0 and self.grid[r - 1][c]:
                    score += 1
                if r < GRID_SIZE - 1 and self.grid[r + 1][c]:
                    score += 1
                if c > 0 and self.grid[r][c - 1]:
                    score += 1
                if c < GRID_SIZE - 1 and self.grid[r][c + 1]:
                    score += 1
                # 更偏好灭掉亮着的灯
                score = (score, -abs(r - GRID_SIZE // 2) - abs(c - GRID_SIZE // 2))
                if score > best_score:
                    best_score = score
                    best_moves = [(r, c)]
                elif score == best_score:
                    best_moves.append((r, c))

        self.hint_cells = best_moves[:3] if best_moves else []

    def _pos_to_cell(self, pos):
        """将屏幕坐标转换为网格坐标"""
        x, y = pos
        col = (x - MARGIN_X) // (CELL_SIZE + GAP)
        row = (y - MARGIN_Y) // (CELL_SIZE + GAP)
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            # 检查是否在有效区域内
            cell_x = MARGIN_X + col * (CELL_SIZE + GAP)
            cell_y = MARGIN_Y + row * (CELL_SIZE + GAP)
            if cell_x <= x <= cell_x + CELL_SIZE and cell_y <= y <= cell_y + CELL_SIZE:
                return row, col
        return None

    def update(self):
        """更新粒子效果"""
        if self.game_over:
            self.particle_timer += 1
            # 持续产生新粒子
            if self.particle_timer % 3 == 0:
                for _ in range(3):
                    self.particles.append(Particle(
                        random.randint(MARGIN_X, WINDOW_WIDTH - MARGIN_X),
                        random.randint(MARGIN_Y, WINDOW_HEIGHT - MARGIN_Y),
                    ))
            self.particles = [p for p in self.particles if p.update()]
        else:
            # 更新鼠标悬停
            self.hover_cell = self._pos_to_cell(pygame.mouse.get_pos())

    def draw(self):
        """绘制所有内容"""
        self.screen.fill(COLOR_BG)

        # 绘制标题
        title = self.font_large.render("LIGHTS OUT", True, COLOR_TITLE)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 35))
        self.screen.blit(title, title_rect)

        # 绘制副标题
        subtitle = self.font_small.render("熄灯挑战 — 点击熄灭所有灯", True, COLOR_MOVE_COUNT)
        sub_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, 70))
        self.screen.blit(subtitle, sub_rect)

        # 绘制步数
        moves_text = self.font_medium.render(f"步数: {self.move_count}", True, COLOR_MOVE_COUNT)
        moves_rect = moves_text.get_rect(center=(WINDOW_WIDTH // 2, 105))
        self.screen.blit(moves_text, moves_rect)

        # 绘制网格背景
        grid_bg_rect = pygame.Rect(
            MARGIN_X - 10, MARGIN_Y - 10,
            GRID_SIZE * (CELL_SIZE + GAP) + 20 - GAP,
            GRID_SIZE * (CELL_SIZE + GAP) + 20 - GAP
        )
        pygame.draw.rect(self.screen, COLOR_GRID_BG, grid_bg_rect, border_radius=10)

        # 绘制网格
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = MARGIN_X + col * (CELL_SIZE + GAP)
                y = MARGIN_Y + row * (CELL_SIZE + GAP)
                is_on = self.grid[row][col] == 1
                is_hover = (row, col) == self.hover_cell and not self.game_over
                is_hint = (row, col) in self.hint_cells

                # 灯体矩形
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

                if is_on:
                    # 亮灯
                    if is_hover:
                        color = (255, 240, 100)
                    else:
                        color = COLOR_LIGHT_ON
                    border_color = COLOR_LIGHT_ON_BORDER
                    # 发光效果
                    glow_rect = rect.inflate(8, 8)
                    for i in range(3):
                        glow_r = glow_rect.inflate(i * 6, i * 6)
                        alpha = 40 - i * 12
                        if alpha > 0:
                            glow_surf = pygame.Surface(glow_r.size, pygame.SRCALPHA)
                            glow_surf.fill((255, 220, 50, alpha))
                            self.screen.blit(glow_surf, glow_r)
                else:
                    # 灭灯
                    if is_hover:
                        color = (50, 50, 65)
                    else:
                        color = COLOR_LIGHT_OFF
                    border_color = COLOR_LIGHT_OFF_BORDER

                # 绘制灯体
                pygame.draw.rect(self.screen, color, rect, border_radius=8)
                pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=8)

                # 提示高亮
                if is_hint:
                    hint_rect = rect.inflate(4, 4)
                    pygame.draw.rect(self.screen, (0, 200, 255, 100), hint_rect, 3, border_radius=10)

                # 亮灯时画中心光晕
                if is_on:
                    center = (x + CELL_SIZE // 2, y + CELL_SIZE // 2)
                    for radius in range(CELL_SIZE // 3, 0, -6):
                        alpha = max(0, 60 - radius * 3)
                        color_glow = (255, 220, 50, alpha)
                        glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                        pygame.draw.circle(glow_surf, color_glow, (radius, radius), radius)
                        self.screen.blit(glow_surf, (center[0] - radius, center[1] - radius))

        # 绘制粒子特效
        for p in self.particles:
            p.draw(self.screen)

        # 绘制胜利信息
        if self.game_over:
            # 半透明遮罩
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            self.screen.blit(overlay, (0, 0))

            victory_text = self.font_large.render("🎉 全部熄灭！", True, COLOR_VICTORY)
            victory_rect = victory_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30))
            self.screen.blit(victory_text, victory_rect)

            sub_text = self.font_medium.render(f"用了 {self.move_count} 步！点击任意位置重新开始", True, COLOR_TEXT)
            sub_rect = sub_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 30))
            self.screen.blit(sub_text, sub_rect)

        # 绘制按钮
        self._draw_button(self.new_game_btn, "新游戏", self.new_game_btn.collidepoint(pygame.mouse.get_pos()))
        self._draw_button(self.hint_btn, "提示", self.hint_btn.collidepoint(pygame.mouse.get_pos()),
                         disabled=self.game_over)

        pygame.display.flip()

    def _draw_button(self, rect, text, hover=False, disabled=False):
        """绘制按钮"""
        if disabled:
            color = (40, 40, 50)
            text_color = (80, 80, 90)
        elif hover:
            color = COLOR_BUTTON_HOVER
            text_color = (255, 255, 255)
        else:
            color = COLOR_BUTTON
            text_color = COLOR_BUTTON_TEXT

        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, (80, 80, 110), rect, 1, border_radius=8)

        text_surf = self.font_small.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

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
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r or event.key == pygame.K_n:
                        self.new_game()
                    elif event.key == pygame.K_h:
                        self._show_hint()

            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = LightsOut()
    game.run()