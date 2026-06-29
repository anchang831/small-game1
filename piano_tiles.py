"""
Piano Tiles (别踩白块/钢琴块)
一个经典的反应力游戏：黑色方块从顶部下落，玩家必须点击黑色方块。

操作：
- 鼠标点击黑色方块得分
- 点击白色方块或漏掉黑色方块则游戏结束
- 速度随分数增加

作者: DeepSeek v4.0 PRO
日期: 2026-06-29
"""

import pygame
import random
import sys

# ==================== 游戏配置 ====================
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
GRID_COLS = 4          # 4列
TILE_WIDTH = SCREEN_WIDTH // GRID_COLS  # 每列宽度
TILE_HEIGHT = 150      # 每个方块高度
FPS = 60

# 颜色 (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 0)
COLORS = [
    (50, 50, 50),      # 黑键默认
    (70, 70, 70),      # 黑键悬停
]


class Tile:
    """单个下落方块"""

    def __init__(self, col, y_pos):
        self.col = col  # 0-3, 对应4列
        self.x = col * TILE_WIDTH
        self.y = y_pos
        self.width = TILE_WIDTH
        self.height = TILE_HEIGHT
        self.is_black = True  # 所有方块都是黑色（需要点击的）
        self.clicked = False
        self.missed = False
        self.fade_alpha = 255

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def contains_point(self, pos):
        """判断一个点是否在方块区域内"""
        return self.get_rect().collidepoint(pos)


class PianoTiles:
    """主游戏类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Piano Tiles - 别踩白块")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("simhei", 48, bold=True)
        self.font_mid = pygame.font.SysFont("simhei", 32)
        self.font_small = pygame.font.SysFont("simhei", 24)
        self.font_tiny = pygame.font.SysFont("simhei", 18)

        # 尝试加载中文字体
        self._init_font()

        self.reset_game()

    def _init_font(self):
        """初始化字体，优先使用中文字体"""
        chinese_fonts = ["simhei", "microsoftyahei", "notosanscjk",
                         "wqymicrohei", "fangsong", "songti"]
        for font_name in chinese_fonts:
            try:
                test_font = pygame.font.SysFont(font_name, 24)
                if test_font.render("测试", True, WHITE).get_width() > 0:
                    self.font_large = pygame.font.SysFont(font_name, 48, bold=True)
                    self.font_mid = pygame.font.SysFont(font_name, 32)
                    self.font_small = pygame.font.SysFont(font_name, 24)
                    self.font_tiny = pygame.font.SysFont(font_name, 18)
                    break
            except Exception:
                continue

    def reset_game(self):
        """重置游戏状态"""
        self.tiles = []          # 所有下落的方块
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.speed = 4.0         # 初始下落速度
        self.spawn_timer = 0
        self.spawn_interval = 10  # 每10帧生成一行
        self.game_over = False
        self.started = False     # 等待点击开始

        # 当前行是否有方块 (确保每一行至少有一个黑块)
        self.current_row_has_tile = False
        self.tiles_in_current_row = []

        # 用于生成行的计数器
        self.row_y = -TILE_HEIGHT

        # 特效
        self.effects = []        # 点击特效

        # 记录最后点击时间用于连击显示
        self.last_hit_time = 0
        self.combo_display_timer = 0

        # 高分数
        self.high_score = 0

    def spawn_row(self):
        """生成一行的方块：随机选1-2列放置黑块"""
        # 每行必定有1-2个黑块（必须点击的）
        num_tiles = random.randint(1, 2)

        # 随机选择列
        columns = random.sample(range(GRID_COLS), num_tiles)
        for col in columns:
            tile = Tile(col, self.row_y)
            self.tiles.append(tile)

    def handle_click(self, pos):
        """处理鼠标点击"""
        if not self.started:
            self.started = True
            return

        if self.game_over:
            # 点击重新开始
            self.reset_game()
            self.started = True
            return

        # 从最底部的方块开始检查（更符合视觉直觉）
        clicked_tile = None
        # 找到最靠近底部且包含点击位置的黑色方块
        for tile in reversed(self.tiles):
            if not tile.clicked and not tile.missed and tile.contains_point(pos):
                clicked_tile = tile
                break

        if clicked_tile:
            # 点击到黑色方块 - 得分！
            clicked_tile.clicked = True
            self.score += 1
            self.combo += 1
            if self.combo > self.max_combo:
                self.max_combo = self.combo
            self.combo_display_timer = 30  # 显示连击约0.5秒

            # 添加点击特效
            self.effects.append({
                "x": clicked_tile.x + TILE_WIDTH // 2,
                "y": clicked_tile.y + TILE_HEIGHT // 2,
                "radius": 10,
                "alpha": 200,
                "growing": True,
            })

            # 每得5分加速一次
            if self.score % 5 == 0:
                self.speed = min(self.speed + 0.5, 12.0)

            # 播放音效（可选）- 用视觉反馈替代
        else:
            # 点击到空白区域（白色区域）- 游戏结束
            self._game_over_action("不要踩白块！")

    def update(self):
        """更新游戏状态"""
        if not self.started or self.game_over:
            return

        self.spawn_timer += 1

        # 定时生成新行
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            self.row_y += TILE_HEIGHT
            self.spawn_row()

        # 更新所有方块位置
        for tile in self.tiles:
            if not tile.clicked:
                tile.y += self.speed

        # 检查是否有黑色方块被漏掉（滑出屏幕底部）
        for tile in self.tiles:
            if (not tile.clicked and not tile.missed
                    and tile.y > SCREEN_HEIGHT):
                tile.missed = True
                self._game_over_action("漏掉了黑块！")
                return

        # 更新特效
        for effect in self.effects[:]:
            if effect["growing"]:
                effect["radius"] += 2
                effect["alpha"] -= 10
                if effect["alpha"] <= 0:
                    self.effects.remove(effect)

        # 更新连击显示计时器
        if self.combo_display_timer > 0:
            self.combo_display_timer -= 1
        else:
            self.combo = 0

        # 清理已点击的旧方块（防止内存暴涨）
        self.tiles = [t for t in self.tiles if t.y < SCREEN_HEIGHT + TILE_HEIGHT]

    def _game_over_action(self, reason):
        """游戏结束"""
        self.game_over = True
        if self.score > self.high_score:
            self.high_score = self.score

    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(WHITE)

        # 绘制网格线（浅灰色）
        for i in range(1, GRID_COLS):
            x = i * TILE_WIDTH
            pygame.draw.line(self.screen, GRAY, (x, 0), (x, SCREEN_HEIGHT), 2)

        # 绘制所有方块
        for tile in self.tiles:
            if tile.missed:
                continue
            rect = tile.get_rect()

            if tile.clicked:
                # 点击过的方块：绿色渐变消失
                color = (100, 200, 100)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, BLACK, rect, 2)
            else:
                # 未点击的黑色方块
                pygame.draw.rect(self.screen, BLACK, rect)
                # 边缘高光效果
                highlight_rect = pygame.Rect(
                    rect.x + 4, rect.y + 4, rect.width - 8, 6
                )
                pygame.draw.rect(self.screen, DARK_GRAY, highlight_rect)
                pygame.draw.rect(self.screen, WHITE, rect, 2)

        # 绘制底部红线区域（提示危险区）
        danger_rect = pygame.Rect(0, SCREEN_HEIGHT - 5, SCREEN_WIDTH, 5)
        pygame.draw.rect(self.screen, RED, danger_rect)

        # 绘制点击特效
        for effect in self.effects:
            color = (255, 215, 0, max(0, effect["alpha"]))
            s = pygame.Surface((effect["radius"] * 2, effect["radius"] * 2),
                               pygame.SRCALPHA)
            pygame.draw.circle(s, (*color[:3], max(0, effect["alpha"])),
                               (effect["radius"], effect["radius"]),
                               effect["radius"], 3)
            self.screen.blit(s, (effect["x"] - effect["radius"],
                                 effect["y"] - effect["radius"]))

        # 绘制分数
        score_text = self.font_mid.render(f"分数: {self.score}", True, BLACK)
        self.screen.blit(score_text, (15, 15))

        # 绘制最高分
        if self.high_score > 0:
            hs_text = self.font_tiny.render(f"最高: {self.high_score}", True, DARK_GRAY)
            self.screen.blit(hs_text, (15, 52))

        # 绘制连击
        if self.combo >= 3 and self.combo_display_timer > 0:
            combo_text = self.font_mid.render(
                f"连击 x{self.combo}!", True, (255, 100, 0)
            )
            combo_rect = combo_text.get_rect(
                center=(SCREEN_WIDTH // 2, 120)
            )
            self.screen.blit(combo_text, combo_rect)

        # 绘制速度指示
        speed_text = self.font_tiny.render(
            f"速度: {self.speed:.1f}", True, DARK_GRAY
        )
        self.screen.blit(speed_text, (15, 75))

        # 未开始 -- 显示开始提示
        if not self.started:
            self._draw_overlay("Piano Tiles", "点击任意位置开始",
                               "点击下落的黑色方块得分", WHITE)

        # 游戏结束
        if self.game_over:
            self._draw_game_over()

        pygame.display.flip()

    def _draw_overlay(self, title, subtitle1, subtitle2, color):
        """绘制半透明覆盖层及文字"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(WHITE)
        self.screen.blit(overlay, (0, 0))

        title_text = self.font_large.render(title, True, BLACK)
        title_rect = title_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80)
        )
        self.screen.blit(title_text, title_rect)

        sub1_text = self.font_small.render(subtitle1, True, DARK_GRAY)
        sub1_rect = sub1_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        )
        self.screen.blit(sub1_text, sub1_rect)

        sub2_text = self.font_small.render(subtitle2, True, GRAY)
        sub2_rect = sub2_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)
        )
        self.screen.blit(sub2_text, sub2_rect)

    def _draw_game_over(self):
        """绘制游戏结束画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(WHITE)
        self.screen.blit(overlay, (0, 0))

        # 游戏结束标题
        go_text = self.font_large.render("游戏结束", True, RED)
        go_rect = go_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100)
        )
        self.screen.blit(go_text, go_rect)

        # 分数
        score_text = self.font_mid.render(
            f"得分: {self.score}", True, BLACK
        )
        score_rect = score_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)
        )
        self.screen.blit(score_text, score_rect)

        # 最高分
        hs_label = "新纪录!" if self.score >= self.high_score and self.score > 0 else "最高分"
        hs_color = YELLOW if self.score >= self.high_score and self.score > 0 else BLACK
        hs_text = self.font_small.render(
            f"{hs_label}: {self.high_score}", True, hs_color
        )
        hs_rect = hs_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 5)
        )
        self.screen.blit(hs_text, hs_rect)

        # 最大连击
        combo_text = self.font_tiny.render(
            f"最大连击: {self.max_combo}", True, DARK_GRAY
        )
        combo_rect = combo_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 45)
        )
        self.screen.blit(combo_text, combo_rect)

        # 重新开始提示
        restart_text = self.font_small.render("点击重新开始", True, BLUE)
        restart_rect = restart_text.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100)
        )
        self.screen.blit(restart_text, restart_rect)

    def run(self):
        """主循环"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键
                        self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


def main():
    """入口函数"""
    game = PianoTiles()
    game.run()


if __name__ == "__main__":
    main()