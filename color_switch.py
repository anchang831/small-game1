#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Color Switch - 颜色跳跳
点击/空格让小球跳跃，穿过旋转圆环中与小球颜色匹配的缺口。
每穿过一个圆环得1分，收集星星可改变小球颜色。
碰到不匹配颜色的环段则游戏结束。

控制方式:
  - 鼠标点击 / 空格键: 跳跃
  - 游戏结束后点击/空格: 重新开始
"""

import pygame
import random
import math
import sys

# ==================== 初始化 ====================
pygame.init()
WIDTH, HEIGHT = 420, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Color Switch - 颜色跳跳")
clock = pygame.time.Clock()
FPS = 60

# ==================== 颜色配置 ====================
COLORS = {
    "red":    (255, 60, 60),
    "green":  (60, 255, 60),
    "blue":   (60, 100, 255),
    "yellow": (255, 255, 60),
    "orange": (255, 160, 40),
    "pink":   (255, 60, 180),
    "cyan":   (60, 255, 255),
    "purple": (200, 60, 255),
}
COLOR_NAMES = list(COLORS.keys())
PRIMARY_COLORS = ["red", "green", "blue", "yellow"]

# ==================== 游戏常量 ====================
BALL_RADIUS = 14
RING_RADIUS = 110
RING_THICKNESS = 22
INNER_RADIUS = RING_RADIUS - RING_THICKNESS // 2
OUTER_RADIUS = RING_RADIUS + RING_THICKNESS // 2
GRAVITY = 0.45
JUMP_VEL = -10.5
SCROLL_SPEED = 1.6
BG_COLOR = (18, 18, 30)
RING_SPACING = 160  # Vertical spacing between rings


# ==================== 字体 ====================
def make_font(size, bold=False):
    """尝试加载系统字体，失败则用默认字体"""
    try:
        return pygame.font.SysFont("Arial", size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


font_large = make_font(48, bold=True)
font_medium = make_font(32, bold=True)
font_small = make_font(22)


# ==================== 背景星空 ====================
class StarField:
    """装饰性星空背景"""

    def __init__(self):
        self.stars = []
        for _ in range(80):
            self.stars.append({
                "x": random.randint(0, WIDTH),
                "y": random.randint(0, HEIGHT),
                "brightness": random.randint(40, 160),
                "size": random.choice([1, 2]),
                "twinkle_speed": random.uniform(0.5, 2.0),
                "phase": random.uniform(0, math.pi * 2),
            })

    def draw(self, screen, frame_count):
        for star in self.stars:
            b = star["brightness"]
            twinkle = int(b * (0.6 + 0.4 * math.sin(frame_count * 0.02 * star["twinkle_speed"] + star["phase"])))
            twinkle = max(0, min(255, twinkle))
            color = (twinkle, twinkle, min(255, twinkle + 30))
            if star["size"] == 2:
                pygame.draw.circle(screen, color, (star["x"], star["y"]), 2)
            else:
                screen.set_at((star["x"], star["y"]), color)


# ==================== 小球 ====================
class Ball:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 130
        self.vy = 0
        self.color = random.choice(PRIMARY_COLORS)
        self.radius = BALL_RADIUS
        self.alive = True

    def jump(self):
        if self.alive:
            self.vy = JUMP_VEL

    def update(self):
        if not self.alive:
            return
        self.vy += GRAVITY
        self.y += self.vy
        # 防止飞出顶部
        if self.y < self.radius:
            self.y = self.radius
            self.vy = 0

    def draw(self, screen):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        col = COLORS[self.color]

        # 外发光
        for i in range(4, 0, -1):
            alpha = 60 - i * 10
            s = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*col, alpha), (r * 2, r * 2), r + i * 4)
            screen.blit(s, (cx - r * 2, cy - r * 2))

        # 球体
        pygame.draw.circle(screen, col, (cx, cy), r)
        # 高光
        pygame.draw.circle(screen, (255, 255, 255), (cx - 4, cy - 4), 4)
        # 小高光
        pygame.draw.circle(screen, (255, 255, 255, 180), (cx - 2, cy - 2), 2)

    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 130
        self.vy = 0
        self.color = random.choice(PRIMARY_COLORS)
        self.alive = True


# ==================== 圆环障碍 ====================
class Ring:
    def __init__(self, y):
        self.x = WIDTH // 2
        self.y = y
        self.radius = RING_RADIUS
        self.thickness = RING_THICKNESS
        self.inner_r = INNER_RADIUS
        self.outer_r = OUTER_RADIUS
        self.angle = random.uniform(0, math.pi / 2)
        self.speed = random.uniform(0.8, 2.2) * random.choice([-1, 1])
        # 4个颜色段
        self.colors = [random.choice(PRIMARY_COLORS) for _ in range(4)]
        self.passed = False  # 是否已被小球穿过(计分用)
        self.scored = False  # 是否已计分

    def update(self):
        self.angle += self.speed * 0.018
        self.y += SCROLL_SPEED

    def draw(self, screen):
        """绘制圆环的4个彩色弧段"""
        for i in range(4):
            start_a = self.angle + i * math.pi / 2
            end_a = start_a + math.pi / 2 - 0.04  # 小间隙让段分离
            color = COLORS[self.colors[i]]
            rect = (self.x - self.radius, self.y - self.radius,
                    self.radius * 2, self.radius * 2)
            # 绘制弧段
            pygame.draw.arc(screen, color, rect, start_a, end_a, self.thickness)

        # 绘制内圈边缘(装饰)
        pygame.draw.circle(screen, (40, 40, 60), (self.x, self.y), self.inner_r, 1)

    def check_collision(self, ball):
        """
        检测小球与圆环的碰撞。
        如果小球处于圆环的环体区域且颜色不匹配，返回 True。
        """
        dx = ball.x - self.x
        dy = ball.y - self.y
        dist = math.hypot(dx, dy)

        # 判断小球是否在环体区域
        if dist < self.inner_r - ball.radius * 0.7:
            return False  # 在中心空洞内，安全
        if dist > self.outer_r + ball.radius * 0.7:
            return False  # 在圆环外部，安全

        # 计算小球相对于圆心的角度
        angle = math.atan2(dy, dx)
        if angle < 0:
            angle += 2 * math.pi

        # 确定所在的颜色段索引
        rel_angle = (angle - self.angle) % (2 * math.pi)
        segment = int(rel_angle / (math.pi / 2))

        # 颜色不匹配 → 碰撞
        return ball.color != self.colors[segment]

    def is_off_screen(self):
        return self.y > HEIGHT + 200

    def is_above_ball(self, ball_y):
        return self.y < ball_y - 30


# ==================== 星星(颜色切换) ====================
class Star:
    def __init__(self, y):
        self.x = WIDTH // 2
        self.y = y
        self.radius = 12
        self.color = random.choice(COLOR_NAMES)
        self.collected = False
        self.pulse = 0

    def update(self):
        self.y += SCROLL_SPEED
        self.pulse += 0.05

    def draw(self, screen):
        if self.collected:
            return
        cx, cy = int(self.x), int(self.y)
        r = self.radius + int(2 * math.sin(self.pulse))
        col = COLORS[self.color]

        # 发光
        s = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*col, 50), (r * 2, r * 2), r + 6)
        screen.blit(s, (cx - r * 2, cy - r * 2))

        # 五角星
        points = []
        for i in range(10):
            angle = -math.pi / 2 + i * math.pi / 5
            rad = r if i % 2 == 0 else r * 0.4
            points.append((cx + rad * math.cos(angle), cy + rad * math.sin(angle)))
        pygame.draw.polygon(screen, col, points)
        pygame.draw.polygon(screen, (255, 255, 255), points, 2)

        # 颜色名称提示
        # 绘制小色块指示颜色
        pygame.draw.circle(screen, col, (cx, cy + r + 10), 5)

    def check_collected(self, ball):
        if self.collected or not ball.alive:
            return False
        dx = ball.x - self.x
        dy = ball.y - self.y
        if math.hypot(dx, dy) < ball.radius + self.radius:
            self.collected = True
            ball.color = self.color
            return True
        return False

    def is_off_screen(self):
        return self.y > HEIGHT + 100


# ==================== 粒子特效 ====================
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2, 7)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 3
        self.color = color
        self.life = 1.0
        self.decay = random.uniform(0.015, 0.035)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15
        self.life -= self.decay

    def draw(self, screen):
        if self.life <= 0:
            return
        alpha = int(self.life * 255)
        r = int(4 * self.life) + 1
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (r, r), r)
        screen.blit(s, (int(self.x) - r, int(self.y) - r))

    @property
    def dead(self):
        return self.life <= 0


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=30):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def update(self):
        self.particles = [p for p in self.particles if not p.dead]
        for p in self.particles:
            p.update()

    def draw(self, screen):
        for p in self.particles:
            p.draw(screen)


# ==================== 主游戏 ====================
def main():
    ball = Ball()
    rings = []
    stars = []
    particles = ParticleSystem()
    score = 0
    best_score = 0
    game_over = False
    running = True
    frame_count = 0
    starfield = StarField()
    # 死亡闪烁计时
    death_timer = 0

    # 生成初始圆环
    for i in range(6):
        y = HEIGHT - 80 - i * RING_SPACING
        rings.append(Ring(y))

    while running:
        dt = clock.tick(FPS)
        frame_count += 1

        # ========== 事件处理 ==========
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game_over:
                        # 重新开始
                        ball = Ball()
                        rings.clear()
                        stars.clear()
                        particles = ParticleSystem()
                        score = 0
                        game_over = False
                        death_timer = 0
                        for i in range(6):
                            y = HEIGHT - 80 - i * RING_SPACING
                            rings.append(Ring(y))
                    else:
                        ball.jump()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_over:
                    ball = Ball()
                    rings.clear()
                    stars.clear()
                    particles = ParticleSystem()
                    score = 0
                    game_over = False
                    death_timer = 0
                    for i in range(6):
                        y = HEIGHT - 80 - i * RING_SPACING
                        rings.append(Ring(y))
                else:
                    ball.jump()

        # ========== 更新逻辑 ==========
        if not game_over:
            ball.update()

            # 生成新圆环
            if rings:
                highest = min(rings, key=lambda r: r.y)
                if highest.y > 50:
                    new_y = highest.y - RING_SPACING
                    rings.append(Ring(new_y))
                    # 30%概率生成星星
                    if random.random() < 0.3:
                        stars.append(Star(new_y - 70))

            # 更新圆环
            for ring in rings[:]:
                ring.update()

                # 检测碰撞
                if ball.alive and ring.check_collision(ball):
                    ball.alive = False
                    game_over = True
                    death_timer = 60
                    # 爆炸粒子
                    particles.emit(ball.x, ball.y, COLORS[ball.color], 50)
                    if score > best_score:
                        best_score = score

                # 计分：小球穿过圆环
                if not ring.scored and ring.is_above_ball(ball.y):
                    ring.scored = True
                    if ball.alive:
                        score += 1

                # 移除屏幕外的圆环
                if ring.is_off_screen():
                    rings.remove(ring)

            # 更新星星
            for star in stars[:]:
                star.update()
                if star.check_collected(ball):
                    particles.emit(star.x, star.y, COLORS[star.color], 20)
                if star.is_off_screen():
                    stars.remove(star)

            # 小球掉出屏幕
            if ball.y > HEIGHT + 100:
                game_over = True
                ball.alive = False
                if score > best_score:
                    best_score = score

            # 更新粒子
            particles.update()

        # ========== 绘制 ==========
        screen.fill(BG_COLOR)
        starfield.draw(screen, frame_count)

        # 绘制圆环（半透明处理死亡时的闪烁）
        if game_over and death_timer > 0:
            death_timer -= 1
            alpha = 255 if death_timer % 6 < 3 else 100
            # 简单闪烁效果
            if death_timer % 6 < 3:
                for ring in rings:
                    ring.draw(screen)
        else:
            for ring in rings:
                ring.draw(screen)

        # 绘制星星
        for star in stars:
            star.draw(screen)

        # 绘制粒子
        particles.draw(screen)

        # 绘制小球
        ball.draw(screen)

        # ========== UI 绘制 ==========
        # 分数
        score_text = font_medium.render(str(score), True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(WIDTH // 2, 50))
        # 分数背景
        score_bg = pygame.Surface((score_rect.w + 30, score_rect.h + 10), pygame.SRCALPHA)
        score_bg.fill((0, 0, 0, 100))
        screen.blit(score_bg, (score_rect.x - 15, score_rect.y - 5))
        screen.blit(score_text, score_rect)

        # 当前颜色指示器
        if ball.alive:
            color_indicator = pygame.Surface((30, 30))
            color_indicator.fill(COLORS[ball.color])
            screen.blit(color_indicator, (WIDTH // 2 - 15, 80))
            pygame.draw.rect(screen, (255, 255, 255), (WIDTH // 2 - 15, 80, 30, 30), 2)

        # 最高分
        best_text = font_small.render(f"Best: {best_score}", True, (150, 150, 180))
        screen.blit(best_text, (15, 15))

        # 操作提示
        if score < 3 and not game_over:
            hint = font_small.render("Click or SPACE to jump!", True, (180, 180, 200))
            hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT - 60))
            hint_bg = pygame.Surface((hint_rect.w + 20, hint_rect.h + 10), pygame.SRCALPHA)
            hint_bg.fill((0, 0, 0, 120))
            screen.blit(hint_bg, (hint_rect.x - 10, hint_rect.y - 5))
            screen.blit(hint, hint_rect)

        # 游戏结束画面
        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            go_text = font_large.render("GAME OVER", True, (255, 80, 80))
            go_rect = go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            screen.blit(go_text, go_rect)

            final_score = font_medium.render(f"Score: {score}", True, (255, 255, 255))
            final_rect = final_score.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10))
            screen.blit(final_score, final_rect)

            if score == best_score and score > 0:
                new_best = font_small.render("NEW BEST!", True, (255, 215, 0))
                new_rect = new_best.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
                screen.blit(new_best, new_rect)

            restart_text = font_small.render("Click or SPACE to Restart", True, (200, 200, 200))
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
            screen.blit(restart_text, restart_rect)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()