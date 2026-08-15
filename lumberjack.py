#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lumberjack - 伐木工
一个快速反应砍树游戏，玩家需要交替按左右方向键砍树，躲避树枝。
使用 Pygame 实现，单文件运行，无外部依赖。

玩法:
- 按 ← / → 方向键砍树
- 如果砍的方向有树枝，游戏结束
- 速度越来越快，考验反应力
- 交替砍树有连击加分
- 砍得越深得分越高
"""

import pygame
import random
import sys
import math

# ============================================================
# 初始化
# ============================================================
pygame.init()
pygame.display.set_caption("伐木工 Lumberjack")

# ============================================================
# 常量
# ============================================================
WIDTH, HEIGHT = 600, 750
FPS = 60
BG_COLOR = (135, 206, 235)  # 天蓝

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BROWN = (101, 67, 33)
DARK_BROWN = (70, 40, 15)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
LIGHT_GREEN = (50, 180, 50)
GRASS_TOP = (60, 180, 60)
GRASS_BOTTOM = (40, 140, 40)
CHOP_COLOR = (210, 180, 140)
RED = (200, 50, 50)
YELLOW = (255, 255, 0)

# 树干参数
TREE_WIDTH = 60
TREE_X = WIDTH // 2 - TREE_WIDTH // 2

# 树枝参数
BRANCH_LENGTH = 85
BRANCH_HEIGHT = 16

# 砍伐区域判定范围
CHOP_TOLERANCE = 45

# 字体
try:
    font_large = pygame.font.SysFont("simsun", 48)
    font_medium = pygame.font.SysFont("simsun", 32)
    font_small = pygame.font.SysFont("simsun", 24)
except Exception:
    font_large = pygame.font.Font(None, 48)
    font_medium = pygame.font.Font(None, 32)
    font_small = pygame.font.Font(None, 24)

# 屏幕对象
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()


# ============================================================
# 粒子系统 (木屑特效)
# ============================================================
class Particle:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = random.uniform(3, 7)
        self.life = random.randint(20, 35)
        self.max_life = self.life
        self.color = random.choice([
            (210, 180, 140), (190, 160, 120),
            (160, 130, 90), (220, 190, 150)
        ])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15  # 重力
        self.life -= 1
        self.size = max(1, self.size * 0.97)

    def draw(self, surf):
        alpha = self.life / self.max_life
        c = tuple(int(v * alpha) for v in self.color)
        s = max(1, int(self.size))
        pygame.draw.rect(surf, c, (self.x, self.y, s, s))


# ============================================================
# 树枝
# ============================================================
class Branch:
    def __init__(self, side, y):
        self.side = side          # "left" 或 "right"
        self.y = y
        self.w = BRANCH_LENGTH
        self.h = BRANCH_HEIGHT
        if side == "left":
            self.x = TREE_X - BRANCH_LENGTH
        else:
            self.x = TREE_X + TREE_WIDTH

    def draw(self, surf):
        # 树枝主体
        rect = pygame.Rect(self.x, self.y, self.w, self.h)
        pygame.draw.rect(surf, DARK_GREEN, rect.inflate(4, 2))
        pygame.draw.rect(surf, GREEN, rect)
        # 树叶 (小圆点)
        lx = self.x + self.w - 10 if self.side == "left" else self.x + 10
        pygame.draw.circle(surf, LIGHT_GREEN, (int(lx), int(self.y + self.h // 2)), 7)
        # 树枝高光
        pygame.draw.line(surf, (60, 200, 60),
                         (self.x, self.y + 2), (self.x + self.w, self.y + 2), 1)


# ============================================================
# 游戏主类
# ============================================================
class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        # 树参数
        self.tree_height = 650        # 剩余树干高度
        self.tree_y = 50              # 树干顶部 Y 坐标
        self.branches = []            # 树枝列表
        self.score = 0                # 当前分数
        self.speed = 1.0              # 当前速度倍率
        self.game_over = False        # 是否结束
        self.particles = []           # 粒子列表
        self.chop_count = 0           # 砍伐次数
        self.last_side = None         # 上次砍的方向
        self.tree_sway = 0.0          # 树摇晃角度
        self.combo = 0                # 连击计数
        self._init_branches()

    def _init_branches(self):
        """生成初始树枝"""
        self.branches.clear()
        y = self.tree_y + self.tree_height - 60
        for _ in range(8):
            side = random.choice(["left", "right"])
            self.branches.append(Branch(side, y))
            y -= random.randint(50, 90)

    def chop(self, side):
        """尝试砍树"""
        if self.game_over:
            return

        # 连击：交替砍树有加分
        if side == self.last_side:
            self.combo = 0
        else:
            self.combo += 1
        self.last_side = side

        # 检查砍伐位置是否有树枝
        chop_y = self.tree_y + self.tree_height - 5
        for b in self.branches:
            if b.side == side and abs(b.y - chop_y) < CHOP_TOLERANCE:
                self.game_over = True
                return

        # 成功砍树
        self.tree_height -= 12
        self.tree_y += 6
        self.chop_count += 1
        self.score += 1 + self.combo // 3
        self.speed = 1.0 + self.chop_count * 0.012

        # 生成木屑粒子
        cx = TREE_X if side == "left" else TREE_X + TREE_WIDTH
        cy = self.tree_y + self.tree_height - 5
        vx_dir = -1 if side == "left" else 1
        for _ in range(6):
            vx = random.uniform(1, 4) * vx_dir
            vy = random.uniform(-4, -0.5)
            self.particles.append(Particle(cx, cy, vx, vy))

        # 生成新树枝 (从顶部)
        if self.branches:
            top_y = min(b.y for b in self.branches)
            for _ in range(random.randint(1, 2)):
                new_y = top_y - random.randint(40, 70)
                self.branches.append(Branch(random.choice(["left", "right"]), new_y))
                top_y = new_y

    def update(self):
        """更新游戏状态"""
        # 更新粒子
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()

        # 游戏结束时的摇晃动画
        if self.game_over:
            self.tree_sway += 0.08

    def draw(self, surf):
        """绘制画面"""
        # ---- 天空背景 ----
        surf.fill(BG_COLOR)

        # 云朵装饰
        for cx, cy, r, cr in [(100, 70, 30, 25), (130, 60, 25, 20),
                              (160, 70, 30, 25), (450, 110, 25, 20),
                              (480, 100, 20, 16), (510, 110, 25, 20)]:
            pygame.draw.circle(surf, WHITE, (cx, cy), r)
            pygame.draw.circle(surf, (240, 248, 255), (cx + 20, cy - 10), cr)

        # ---- 地面 ----
        ground_y = self.tree_y + self.tree_height
        grass_rect = pygame.Rect(0, ground_y, WIDTH, HEIGHT - ground_y)
        for i in range(grass_rect.height):
            t = i / max(1, grass_rect.height)
            r = int(GRASS_TOP[0] * (1 - t) + GRASS_BOTTOM[0] * t)
            g = int(GRASS_TOP[1] * (1 - t) + GRASS_BOTTOM[1] * t)
            b = int(GRASS_TOP[2] * (1 - t) + GRASS_BOTTOM[2] * t)
            pygame.draw.line(surf, (r, g, b), (0, ground_y + i), (WIDTH, ground_y + i))
        pygame.draw.rect(surf, DARK_GREEN, (0, ground_y, WIDTH, 3))

        # ---- 树枝 ----
        branch_sway = 0
        if self.game_over:
            branch_sway = int(math.sin(self.tree_sway) * 4)
        visible = [b for b in self.branches
                   if self.tree_y - 50 < b.y < self.tree_y + self.tree_height + 50]
        for b in visible:
            b.draw(surf)

        # ---- 树干 ----
        sway = int(math.sin(self.tree_sway) * 4) if self.game_over else 0
        tx = TREE_X + sway
        ty = self.tree_y
        th = max(5, self.tree_height)

        for i in range(th):
            shade = max(60, 120 - i * 0.08)
            c = (int(shade), int(shade * 0.6), int(shade * 0.3))
            pygame.draw.line(surf, c, (tx, ty + i), (tx + TREE_WIDTH, ty + i))

        # 树皮纹理
        for i in range(0, th, 25):
            y = ty + i
            pygame.draw.line(surf, DARK_BROWN, (tx + 5, y), (tx + TREE_WIDTH - 5, y), 1)
        # 树皮竖纹
        for offset in [12, 30, 48]:
            pygame.draw.line(surf, (80, 50, 20), (tx + offset, ty), (tx + offset, ty + th), 1)

        # 砍痕 (V形刻痕)
        for i in range(min(self.chop_count, 30)):
            my = ty + th - 8 - i * 14
            if my > ty + 5:
                sd = "left" if i % 2 == 0 else "right"
                if sd == "left":
                    pts = [(tx, my), (tx - 14, my - 4), (tx, my + 4), (tx + 4, my)]
                else:
                    pts = [(tx + TREE_WIDTH, my), (tx + TREE_WIDTH + 14, my - 4),
                           (tx + TREE_WIDTH, my + 4), (tx + TREE_WIDTH - 4, my)]
                pygame.draw.polygon(surf, CHOP_COLOR, pts)

        # ---- 树冠 ----
        crown_y = ty - 30
        ccx = WIDTH // 2 + sway
        pygame.draw.circle(surf, GREEN, (ccx, crown_y), 35)
        pygame.draw.circle(surf, LIGHT_GREEN, (ccx - 12, crown_y - 18), 20)
        pygame.draw.circle(surf, LIGHT_GREEN, (ccx + 12, crown_y - 14), 20)

        # ---- 粒子 ----
        for p in self.particles:
            p.draw(surf)

        # ---- UI ---- (分数、速度等)
        # 分数面板
        score_bg = pygame.Surface((160, 45))
        score_bg.set_alpha(180)
        score_bg.fill((50, 50, 50))
        surf.blit(score_bg, (10, 10))
        score_t = font_medium.render(f"得分: {self.score}", True, WHITE)
        surf.blit(score_t, (20, 15))

        # 速度
        speed_t = font_small.render(f"速度 {self.speed:.1f}x", True, BLACK)
        surf.blit(speed_t, (WIDTH - 130, 20))

        # 连击提示
        if self.combo >= 3:
            combo_t = font_small.render(f"连击 x{self.combo // 3 + 1}", True, YELLOW)
            surf.blit(combo_t, (WIDTH // 2 - 50, 15))

        # 新手提示
        if self.chop_count == 0:
            hint = font_small.render("← → 砍树，躲避树枝！", True, YELLOW)
            shadow = font_small.render("← → 砍树，躲避树枝！", True, BLACK)
            hr = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80))
            surf.blit(shadow, hr.move(2, 2))
            surf.blit(hint, hr)

        # ---- 游戏结束 ----
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(140)
            overlay.fill(BLACK)
            surf.blit(overlay, (0, 0))

            go = font_large.render("游戏结束!", True, RED)
            surf.blit(go, go.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80)))

            fs = font_medium.render(f"最终得分: {self.score}", True, WHITE)
            surf.blit(fs, fs.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))

            # 评价
            if self.score >= 100:
                rank = "砍树大师!"
            elif self.score >= 50:
                rank = "优秀伐木工!"
            elif self.score >= 20:
                rank = "熟练工!"
            elif self.score >= 10:
                rank = "初学者"
            else:
                rank = "手滑了..."
            rank_t = font_small.render(rank, True, YELLOW)
            surf.blit(rank_t, rank_t.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))

            rt = font_small.render("按 R 重新开始  |  ESC 退出", True, WHITE)
            surf.blit(rt, rt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80)))


# ============================================================
# 主循环
# ============================================================
def main():
    game = Game()
    running = True

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and game.game_over:
                    game.reset()
                elif event.key == pygame.K_LEFT:
                    game.chop("left")
                elif event.key == pygame.K_RIGHT:
                    game.chop("right")

        game.update()
        game.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()