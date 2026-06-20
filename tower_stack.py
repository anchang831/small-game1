#!/usr/bin/env python3
"""
tower_stack.py - 堆叠高塔 (Tower Stack)
=====================
一个让玩家堆叠方块建造高塔的游戏。
方块左右移动，点击/按空格放置，未对齐部分会被切除。
游戏难度随高度增加而提升。

Date: 2026-06-20
"""

import pygame
import sys
import math

# ========== 初始化 ==========
pygame.init()
pygame.display.set_caption("堆叠高塔 - Tower Stack")

# ========== 常量 ==========
WIDTH, HEIGHT = 600, 800
FPS = 60
BG_COLOR = (15, 15, 35)
BLOCK_COLORS = [
    (255, 65, 85),    # 红
    (255, 185, 50),   # 橙
    (50, 205, 120),   # 绿
    (50, 150, 255),   # 蓝
    (180, 80, 255),   # 紫
    (255, 80, 180),   # 粉
    (0, 215, 215),    # 青
]

BLOCK_W = 120         # 初始方块宽度
BLOCK_H = 30          # 方块高度
MOVE_SPEED = 4.0      # 初始移动速度
SPEED_INC = 0.3       # 每次放置速度增量
MIN_BLOCK_W = 8       # 最小方块宽度（小于此值游戏结束）
PLATFORM_Y = 650      # 起始平台 Y 坐标
PERFECT_THRESHOLD = 4 # 完美对齐阈值（像素）

# ========== 屏幕 ==========
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 28)

# ========== 游戏状态 ==========
class GameState:
    """所有游戏状态"""
    def __init__(self):
        self.reset()

    def reset(self):
        # 塔的方块列表，每个为 (rect, color)
        base_rect = pygame.Rect(
            (WIDTH - BLOCK_W) // 2, PLATFORM_Y, BLOCK_W, BLOCK_H
        )
        self.tower = [(base_rect, (100, 100, 120))]
        self.current_w = BLOCK_W
        self.current_color = random.choice(BLOCK_COLORS)
        self.speed = MOVE_SPEED
        self.direction = 1  # 1 右, -1 左
        self.move_offset = 0.0
        self.score = 0
        self.high_score = 0
        self.state = "playing"  # playing, game_over
        self.combo = 0

        # 新方块初始水平位置
        self.reset_block_pos()

    def reset_block_pos(self):
        self.move_offset = -(WIDTH // 2) * 0.3

    def get_current_rect(self):
        x = (WIDTH - self.current_w) // 2 + self.move_offset
        y = self.tower[-1][0].top - BLOCK_H
        return pygame.Rect(x, y, self.current_w, BLOCK_H)

    def update(self):
        """更新当前方块位置"""
        if self.state != "playing":
            return

        self.move_offset += self.speed * self.direction
        current_rect = self.get_current_rect()

        # 边界反弹
        if current_rect.left < 0:
            self.direction = 1
            self.move_offset = -(WIDTH - self.current_w) // 2
        elif current_rect.right > WIDTH:
            self.direction = -1
            self.move_offset = (WIDTH - self.current_w) // 2

    def place_block(self):
        """放置当前方块"""
        if self.state != "playing":
            return

        current_rect = self.get_current_rect()
        last_rect = self.tower[-1][0]

        # 计算重叠
        overlap_left = max(current_rect.left, last_rect.left)
        overlap_right = min(current_rect.right, last_rect.right)
        overlap_w = overlap_right - overlap_left

        # 完全没对齐 → 游戏结束
        if overlap_w <= 0:
            self.state = "game_over"
            if self.score > self.high_score:
                self.high_score = self.score
            return

        # 完美对齐判定
        is_perfect = (
            abs(current_rect.left - last_rect.left) < PERFECT_THRESHOLD
            and abs(current_rect.right - last_rect.right) < PERFECT_THRESHOLD
        )

        if is_perfect:
            # 完美对齐：用原大小，加成 combo
            self.combo += 1
            bonus = min(self.combo, 10)
            placed_rect = pygame.Rect(
                last_rect.left, last_rect.top - BLOCK_H,
                self.current_w, BLOCK_H
            )
            placed_w = self.current_w
            # 闪烁效果用的颜色
            placed_color = (255, 255, 255)
        else:
            # 有偏差：切除未对齐部分
            self.combo = 0
            placed_rect = pygame.Rect(
                overlap_left, last_rect.top - BLOCK_H,
                overlap_w, BLOCK_H
            )
            placed_w = overlap_w

            # 切除的部分生成掉落的小方块
            self._spawn_falling_blocks(current_rect, overlap_left, overlap_right)

        self.tower.append((placed_rect, self.current_color))
        self.current_w = placed_w
        self.score += 1
        self.speed += SPEED_INC
        self.current_color = random.choice(BLOCK_COLORS)
        self.reset_block_pos()

        # 检测游戏结束
        if placed_w < MIN_BLOCK_W:
            self.state = "game_over"
            if self.score > self.high_score:
                self.high_score = self.score
            return

        # 更新塔里方块颜色
        if not is_perfect:
            self.tower[-1] = (placed_rect, self.current_color)

    def _spawn_falling_blocks(self, current_rect, overlap_left, overlap_right):
        """生成被切除部分掉落的方块"""
        # 左侧掉落
        left_w = overlap_left - current_rect.left
        if left_w > 2:
            left_rect = pygame.Rect(
                current_rect.left, current_rect.top, left_w, BLOCK_H
            )
            self._add_falling_block(left_rect, self.current_color, -2)

        # 右侧掉落
        right_w = current_rect.right - overlap_right
        if right_w > 2:
            right_rect = pygame.Rect(
                overlap_right, current_rect.top, right_w, BLOCK_H
            )
            self._add_falling_block(right_rect, self.current_color, 2)

    def _add_falling_block(self, rect, color, vx):
        if not hasattr(self, 'falling_blocks'):
            self.falling_blocks = []
        self.falling_blocks.append({
            'rect': rect,
            'color': color,
            'vx': vx * random.uniform(0.8, 1.5),
            'vy': random.uniform(2, 5),
            'rotation': 0,
            'rot_speed': random.uniform(-5, 5),
        })


# ========== 初始化状态 ==========
game = GameState()
game.falling_blocks = []

# ========== 绘制函数 ==========
def draw_bg():
    """绘制渐变背景"""
    for i in range(HEIGHT):
        t = i / HEIGHT
        r = int(15 + t * 10)
        g = int(15 + t * 8)
        b = int(35 + t * 15)
        pygame.draw.line(screen, (r, g, b), (0, i), (WIDTH, i))


def draw_tower():
    """绘制已堆叠的塔"""
    for i, (rect, color) in enumerate(game.tower):
        # 底座的略微阴影
        shadow_rect = rect.copy()
        shadow_rect.y += 3
        pygame.draw.rect(screen, (0, 0, 0, 60), shadow_rect, border_radius=3)
        # 方块本体
        pygame.draw.rect(screen, color, rect, border_radius=3)
        # 高光
        highlight = rect.copy()
        highlight.h = 6
        hl_color = tuple(min(c + 60, 255) for c in color)
        pygame.draw.rect(screen, hl_color, highlight, border_radius=2)


def draw_current_block():
    """绘制当前移动的方块"""
    if game.state != "playing":
        return

    rect = game.get_current_rect()
    color = game.current_color

    # 发光效果
    glow_surf = pygame.Surface((rect.w + 20, rect.h + 20), pygame.SRCALPHA)
    glow_color = (*color[:3], 80)
    pygame.draw.rect(
        glow_surf, glow_color,
        (10, 10, rect.w, rect.h), border_radius=6
    )
    screen.blit(glow_surf, (rect.left - 10, rect.top - 10))

    # 方块
    pygame.draw.rect(screen, color, rect, border_radius=3)
    # 高光
    highlight = rect.copy()
    highlight.h = 6
    hl_color = tuple(min(c + 60, 255) for c in color)
    pygame.draw.rect(screen, hl_color, highlight, border_radius=2)


def draw_falling_blocks():
    """绘制掉落的小方块"""
    if not hasattr(game, 'falling_blocks'):
        return
    to_remove = []
    for fb in game.falling_blocks:
        fb['rect'].x += fb['vx']
        fb['rect'].y += fb['vy']
        fb['vy'] += 0.2  # 重力
        fb['rotation'] += fb['rot_speed']

        # 绘制旋转效果
        surf = pygame.Surface((fb['rect'].w, fb['rect'].h), pygame.SRCALPHA)
        surf.fill(fb['color'])
        rotated = pygame.transform.rotate(surf, fb['rotation'])
        screen.blit(rotated, (fb['rect'].x, fb['rect'].y))

        if fb['rect'].y > HEIGHT + 50:
            to_remove.append(fb)

    for fb in to_remove:
        game.falling_blocks.remove(fb)


def draw_perfect_effect():
    """完美对齐时的特效"""
    if not hasattr(game, '_perfect_timer'):
        return
    if game._perfect_timer > 0:
        alpha = min(255, int(255 * game._perfect_timer / 30))
        text = font_medium.render("PERFECT!", True, (255, 255, 100))
        text.set_alpha(alpha)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
        # 缩放
        scale = 1 + (1 - game._perfect_timer / 30) * 0.5
        scaled = pygame.transform.scale(
            text,
            (int(text.get_width() * scale), int(text.get_height() * scale))
        )
        scaled.set_alpha(alpha)
        sr = scaled.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
        screen.blit(scaled, sr)
        game._perfect_timer -= 1


def draw_ui():
    """绘制 UI 信息"""
    # 分数
    score_text = font_medium.render(f"{game.score}", True, (255, 255, 255))
    screen.blit(score_text, (20, 20))

    # "SCORE" 标签
    label = font_small.render("SCORE", True, (150, 150, 180))
    screen.blit(label, (20, 60))

    # 最高分
    if game.high_score > 0:
        hs_text = font_small.render(
            f"BEST: {game.high_score}", True, (180, 180, 100)
        )
        hs_rect = hs_text.get_rect(topright=(WIDTH - 20, 20))
        screen.blit(hs_text, hs_rect)

    # 连击
    if game.combo > 1:
        combo_text = font_small.render(
            f"COMBO x{game.combo}", True, (255, 200, 50)
        )
        combo_rect = combo_text.get_rect(center=(WIDTH // 2, 30))
        screen.blit(combo_text, combo_rect)

    # 操作提示（刚开始时）
    if game.score < 3:
        hint = font_small.render(
            "按 SPACE 或 点击放置方块", True, (150, 150, 200)
        )
        hint.set_alpha(150)
        hr = hint.get_rect(center=(WIDTH // 2, HEIGHT - 40))
        screen.blit(hint, hr)


def draw_game_over():
    """绘制游戏结束画面"""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    # "GAME OVER"
    go_text = font_large.render("GAME OVER", True, (255, 80, 80))
    go_rect = go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
    screen.blit(go_text, go_rect)

    # 分数
    score_text = font_medium.render(
        f"分数: {game.score}", True, (255, 255, 255)
    )
    score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10))
    screen.blit(score_text, score_rect)

    # 最高分
    if game.score >= game.high_score and game.score > 0:
        new_record = font_small.render(
            "🎉 新纪录！", True, (255, 215, 0)
        )
        nr_rect = new_record.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 55))
        screen.blit(new_record, nr_rect)

    # 重新开始
    restart_text = font_small.render(
        "按 SPACE / ENTER / 点击 重新开始", True, (180, 180, 220)
    )
    restart_rect = restart_text.get_rect(
        center=(WIDTH // 2, HEIGHT // 2 + 110)
    )
    screen.blit(restart_text, restart_rect)


def draw_guideline():
    """绘制对齐参考线"""
    if not game.tower or game.state != "playing":
        return
    last = game.tower[-1][0]
    # 左侧辅助线
    pygame.draw.line(
        screen, (255, 255, 255, 30),
        (last.left, 0), (last.left, last.top),
        1
    )
    # 右侧辅助线
    pygame.draw.line(
        screen, (255, 255, 255, 30),
        (last.right, 0), (last.right, last.top),
        1
    )


# ========== 主循环 ==========
def main():
    running = True
    game._perfect_timer = 0
    fall_speed = 2.0

    while running:
        dt = clock.tick(FPS)

        # ---- 事件处理 ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    if game.state == "playing":
                        # 检测完美对齐
                        if hasattr(game, 'tower') and game.tower:
                            current = game.get_current_rect()
                            last = game.tower[-1][0]
                            if (abs(current.left - last.left) < PERFECT_THRESHOLD
                                    and abs(current.right - last.right) < PERFECT_THRESHOLD):
                                game._perfect_timer = 30
                        game.place_block()
                        # 在游戏结束画面按空格重启
                        if game.state == "game_over":
                            pass
                    else:
                        # 重新开始
                        game.__init__()
                        game.falling_blocks = []
                        game._perfect_timer = 0

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    if game.state == "playing":
                        current = game.get_current_rect()
                        last = game.tower[-1][0]
                        if (abs(current.left - last.left) < PERFECT_THRESHOLD
                                and abs(current.right - last.right) < PERFECT_THRESHOLD):
                            game._perfect_timer = 30
                        game.place_block()
                    else:
                        game.__init__()
                        game.falling_blocks = []
                        game._perfect_timer = 0

        # ---- 更新 ----
        game.update()

        # 检查游戏结束键（在 game_over 状态按空格）
        keys = pygame.key.get_pressed()
        if game.state == "game_over":
            if keys[pygame.K_SPACE] or keys[pygame.K_RETURN]:
                game.__init__()
                game.falling_blocks = []
                game._perfect_timer = 0

        # ---- 绘制 ----
        draw_bg()
        draw_guideline()
        draw_tower()
        draw_current_block()
        draw_falling_blocks()
        draw_perfect_effect()
        draw_ui()

        if game.state == "game_over":
            draw_game_over()

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()