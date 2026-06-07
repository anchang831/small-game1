"""
小行星 (Asteroids) - 经典街机游戏
===============================
控制飞船在太空中躲避并击碎小行星。

操作说明:
  ←/→  旋转飞船
  ↑     推进加速
  空格  发射子弹
  R     重新开始(游戏结束后)

日期: 2026-06-07
"""

import pygame
import math
import random

# ─── 初始化 Pygame ───────────────────────────────────────────
pygame.init()
WIDTH, HEIGHT = 900, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("小行星 Asteroids")
clock = pygame.time.Clock()
font_large = pygame.font.SysFont("Arial", 48, bold=True)
font_small = pygame.font.SysFont("Arial", 20)
font_score = pygame.font.SysFont("Arial", 28, bold=True)

# ─── 颜色 ──────────────────────────────────────────────────────
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
RED = (255, 50, 50)
YELLOW = (255, 255, 100)
CYAN = (100, 255, 255)

# ─── 工具函数 ─────────────────────────────────────────────────
def wrap_position(pos):
    """让物体从屏幕一侧穿到另一侧（环绕效果）。"""
    x, y = pos
    x %= WIDTH
    y %= HEIGHT
    return (x, y)


def angle_to_vector(angle):
    """角度（度）转换为方向向量。"""
    rad = math.radians(angle)
    return (math.cos(rad), math.sin(rad))


def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


# ─── 子弹 ─────────────────────────────────────────────────────
class Bullet:
    SPEED = 10

    def __init__(self, pos, angle):
        dx, dy = angle_to_vector(angle)
        self.x, self.y = pos
        self.vx = dx * self.SPEED
        self.vy = -dy * self.SPEED
        self.radius = 3
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        # 超出屏幕即消失
        if not (0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT):
            self.alive = False
        else:
            self.alive = True

    def draw(self, surface):
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius)


# ─── 飞船 ─────────────────────────────────────────────────────
class Ship:
    ROTATION_SPEED = 5       # 度/帧
    ACCELERATION = 0.25
    FRICTION = 0.985
    MAX_SPEED = 8
    SHOOT_COOLDOWN = 12      # 帧

    def __init__(self):
        self.reset()

    def reset(self):
        self.x = WIDTH / 2
        self.y = HEIGHT / 2
        self.angle = 0              # 度，0=向上
        self.vx = 0
        self.vy = 0
        self.radius = 15
        self.cooldown = 0
        self.invincible = 90        # 重生后无敌帧数
        self.alive = True

    def update(self, keys, bullets):
        if not self.alive:
            return

        # 旋转
        if keys[pygame.K_LEFT]:
            self.angle += self.ROTATION_SPEED
        if keys[pygame.K_RIGHT]:
            self.angle -= self.ROTATION_SPEED

        # 推进
        if keys[pygame.K_UP]:
            dx, dy = angle_to_vector(self.angle)
            self.vx += dx * self.ACCELERATION
            self.vy -= dy * self.ACCELERATION
            # 产生推进火焰粒子（仅视觉装饰）
            draw_thrust = True
        else:
            draw_thrust = False

        # 摩擦限速
        self.vx *= self.FRICTION
        self.vy *= self.FRICTION
        speed = math.hypot(self.vx, self.vy)
        if speed > self.MAX_SPEED:
            self.vx = self.vx / speed * self.MAX_SPEED
            self.vy = self.vy / speed * self.MAX_SPEED

        # 移动
        self.x += self.vx
        self.y += self.vy
        self.x, self.y = wrap_position((self.x, self.y))

        # 发射子弹
        self.cooldown = max(0, self.cooldown - 1)
        if keys[pygame.K_SPACE] and self.cooldown == 0:
            self.cooldown = self.SHOOT_COOLDOWN
            bullets.append(Bullet((self.x, self.y), self.angle))

        # 无敌倒计时
        self.invincible = max(0, self.invincible - 1)

        return draw_thrust

    def draw(self, surface, draw_thrust=False):
        if not self.alive:
            return
        # 无敌时闪烁
        if self.invincible > 0 and (self.invincible // 4) % 2 == 0:
            return

        cx, cy = self.x, self.y
        # 飞船三角的三个顶点
        dx, dy = angle_to_vector(self.angle)
        tip = (cx + dx * 20, cy - dy * 20)
        left = (cx - dy * 12 - dx * 10, cy - dx * 12 + dy * 10)
        right = (cx + dy * 12 - dx * 10, cy + dx * 12 + dy * 10)
        pygame.draw.polygon(surface, WHITE, [tip, left, right], 2)

        # 推进火焰
        if draw_thrust:
            flame_len = 8 + random.randint(0, 6)
            flame_tip = (cx - dx * flame_len, cy + dy * flame_len)
            fl = (cx - dy * 6 - dx * 4, cy - dx * 6 + dy * 4)
            fr = (cx + dy * 6 - dx * 4, cy + dx * 6 + dy * 4)
            pygame.draw.polygon(surface, YELLOW, [fl, flame_tip, fr])


# ─── 小行星 ───────────────────────────────────────────────────
class Asteroid:
    SIZES = {
        3: {"radius": 50, "speed": 1.2, "points": 20},
        2: {"radius": 30, "speed": 1.8, "points": 50},
        1: {"radius": 15, "speed": 2.5, "points": 100},
    }

    def __init__(self, pos=None, size=3):
        self.size = size
        info = self.SIZES[size]
        self.radius = info["radius"]

        if pos:
            self.x, self.y = pos
        else:
            # 随机生成在屏幕边缘附近
            edge = random.choice(["top", "bottom", "left", "right"])
            if edge == "top":
                self.x, self.y = random.randint(0, WIDTH), -self.radius
            elif edge == "bottom":
                self.x, self.y = random.randint(0, WIDTH), HEIGHT + self.radius
            elif edge == "left":
                self.x, self.y = -self.radius, random.randint(0, HEIGHT)
            else:
                self.x, self.y = WIDTH + self.radius, random.randint(0, HEIGHT)

        # 随机方向
        angle = random.uniform(0, 360)
        speed = info["speed"] * random.uniform(0.8, 1.2)
        dx, dy = angle_to_vector(angle)
        self.vx = dx * speed
        self.vy = -dy * speed

        # 生成不规则多边形顶点，使每颗小行星看起来不同
        num_verts = random.randint(8, 12)
        self.vertices = []
        for i in range(num_verts):
            a = 2 * math.pi * i / num_verts
            r = self.radius * random.uniform(0.7, 1.0)
            self.vertices.append((math.cos(a) * r, math.sin(a) * r))

        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.x, self.y = wrap_position((self.x, self.y))

    def draw(self, surface):
        if not self.alive:
            return
        pts = [(self.x + vx, self.y + vy) for vx, vy in self.vertices]
        pygame.draw.polygon(surface, GRAY, pts, 2)
        # 内部微光
        pygame.draw.polygon(surface, (40, 40, 40), pts, 1)

    def split(self):
        """小行星被击碎后分裂成两个更小的。"""
        new_asteroids = []
        if self.size > 1:
            for _ in range(2):
                new_asteroids.append(Asteroid(pos=(self.x, self.y), size=self.size - 1))
        return new_asteroids

    def get_points(self):
        return self.SIZES[self.size]["points"]


# ─── 粒子特效 ─────────────────────────────────────────────────
class Particle:
    def __init__(self, pos, color, speed=3, lifetime=20):
        self.x, self.y = pos
        angle = random.uniform(0, 360)
        dx, dy = angle_to_vector(angle)
        spd = random.uniform(1, speed)
        self.vx = dx * spd
        self.vy = -dy * spd
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.96
        self.vy *= 0.96
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface):
        ratio = self.lifetime / self.max_lifetime
        alpha = int(255 * ratio)
        r, g, b = self.color
        pygame.draw.circle(surface, (r, g, b), (int(self.x), int(self.y)), max(1, int(3 * ratio)))


# ─── 主游戏类 ─────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.ship = Ship()
        self.bullets = []
        self.asteroids = []
        self.particles = []
        self.score = 0
        self.lives = 3
        self.level = 0
        self.state = "playing"  # playing / gameover
        self.next_level_ready = False
        self.level_timer = 0

        # 生成初始小行星
        self.spawn_asteroids(4)

    def spawn_asteroids(self, count):
        for _ in range(count):
            self.asteroids.append(Asteroid(size=3))

    def start_new_level(self):
        self.level += 1
        count = min(3 + self.level, 12)
        self.spawn_asteroids(count)
        self.next_level_ready = False

    def emit_explosion(self, pos, color, count=20):
        for _ in range(count):
            self.particles.append(Particle(pos, color, speed=5, lifetime=25))

    def update(self, keys):
        if self.state == "gameover":
            if keys[pygame.K_r]:
                self.reset()
            return

        # 更新飞船
        draw_thrust = self.ship.update(keys, self.bullets)

        # 更新子弹
        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.alive]

        # 更新小行星
        for a in self.asteroids:
            a.update()

        # 更新粒子
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

        # ─── 碰撞检测 ───
        # 子弹 vs 小行星
        new_asteroids = []
        for a in self.asteroids:
            if not a.alive:
                continue
            hit = False
            for b in self.bullets:
                if distance((a.x, a.y), (b.x, b.y)) < a.radius:
                    b.alive = False
                    hit = True
                    self.score += a.get_points()
                    self.emit_explosion((a.x, a.y), GRAY, 15)
                    new_asteroids.extend(a.split())
                    break
            if not hit:
                new_asteroids.append(a)
        self.asteroids = new_asteroids
        self.bullets = [b for b in self.bullets if b.alive]

        # 飞船 vs 小行星
        if self.ship.alive and self.ship.invincible == 0:
            for a in self.asteroids:
                if a.alive and distance((self.ship.x, self.ship.y), (a.x, a.y)) < self.ship.radius + a.radius:
                    # 飞船被撞毁
                    self.emit_explosion((self.ship.x, self.ship.y), CYAN, 30)
                    self.ship.alive = False
                    self.lives -= 1
                    # 小行星也被撞碎
                    new_asteroids.extend(a.split())
                    a.alive = False
                    break
        self.asteroids = [a for a in self.asteroids if a.alive]

        # 飞船重生
        if not self.ship.alive:
            if self.lives <= 0:
                self.state = "gameover"
            else:
                self.ship = Ship()
                # 重生时短暂无敌

        # 检查是否清空所有小行星 -> 下一关
        if len(self.asteroids) == 0 and self.state == "playing":
            if not self.next_level_ready:
                self.next_level_ready = True
                self.level_timer = 60  # 等待1秒进入下一关
            else:
                self.level_timer -= 1
                if self.level_timer <= 0:
                    self.start_new_level()

        return draw_thrust

    def draw(self, surface, draw_thrust=False):
        surface.fill(BLACK)

        # 绘制星星背景（静止）
        for _ in range(80):
            sx = (hash(str(_) + "x") % WIDTH)
            sy = (hash(str(_) + "y") % HEIGHT)
            brightness = (hash(str(_) + "b") % 100) + 155
            pygame.draw.circle(surface, (brightness, brightness, brightness), (sx, sy), 1)

        # 绘制游戏对象
        self.ship.draw(surface, draw_thrust)
        for a in self.asteroids:
            a.draw(surface)
        for b in self.bullets:
            b.draw(surface)
        for p in self.particles:
            p.draw(surface)

        # 绘制 HUD
        score_text = font_score.render(f"得分: {self.score}", True, WHITE)
        surface.blit(score_text, (20, 15))
        lives_text = font_score.render(f"生命: {self.lives}", True, CYAN)
        surface.blit(lives_text, (20, 50))
        level_text = font_score.render(f"关卡: {self.level}", True, WHITE)
        surface.blit(level_text, (20, 85))

        # 剩余小行星数
        ast_count = font_small.render(f"小行星: {len(self.asteroids)}", True, GRAY)
        surface.blit(ast_count, (20, 120))

        # 游戏结束
        if self.state == "gameover":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            surface.blit(overlay, (0, 0))

            go_text = font_large.render("游戏结束", True, RED)
            go_rect = go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
            surface.blit(go_text, go_rect)

            score_text2 = font_large.render(f"最终得分: {self.score}", True, WHITE)
            score_rect2 = score_text2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            surface.blit(score_text2, score_rect2)

            restart_text = font_small.render("按 R 键重新开始", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80))
            surface.blit(restart_text, restart_rect)


# ─── 主循环 ───────────────────────────────────────────────────
def main():
    game = Game()
    running = True
    draw_thrust = False

    while running:
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        draw_thrust = game.update(keys)
        game.draw(screen, draw_thrust)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()