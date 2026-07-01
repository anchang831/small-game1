"""
霓虹弹幕 (Neon Danmaku) — 子弹地狱射击游戏
============================================
控制方式: ← → ↑ ↓ 移动，Z 键射击
规则: 躲避敌人弹幕，消灭敌人获取高分！
特点: 多种子弹模式、粒子特效、连击系统、霓虹视觉风格

运行: python danmaku.py
"""

import pygame
import random
import math
import sys

# ========== 初始化 ==========
pygame.init()
pygame.font.init()
try:
    pygame.mixer.init()
except pygame.error:
    pass

# ========== 常量 ==========
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 680
FPS = 60
PLAYER_SPEED = 5
BULLET_SPEED = 8
ENEMY_BULLET_SPEED = 3
MAX_LIVES = 3
INVINCIBLE_FRAMES = 90  # 约1.5秒

# 颜色 (霓虹风格)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
NEON_CYAN = (0, 255, 255)
NEON_PINK = (255, 0, 128)
NEON_GREEN = (0, 255, 128)
NEON_ORANGE = (255, 128, 0)
NEON_PURPLE = (180, 0, 255)
NEON_YELLOW = (255, 255, 0)
NEON_RED = (255, 32, 32)
NEON_BLUE = (64, 128, 255)
DARK_BG = (8, 8, 24)

# ========== 屏幕设置 ==========
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("霓虹弹幕 - Neon Danmaku")
clock = pygame.time.Clock()
font_large = pygame.font.Font(None, 64)
font_mid = pygame.font.Font(None, 36)
font_small = pygame.font.Font(None, 24)

# ========== 工具函数 ==========
def draw_glow_circle(surf, color, pos, radius, glow_radius=None):
    """绘制发光圆"""
    if glow_radius is None:
        glow_radius = radius * 2
    for i in range(3):
        alpha = 80 - i * 25
        if alpha <= 0:
            continue
        r = glow_radius - i * (glow_radius - radius) // 3
        glow_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        glow_color = (*color[:3], alpha)
        pygame.draw.circle(glow_surf, glow_color, (r, r), r)
        surf.blit(glow_surf, (pos[0] - r, pos[1] - r))
    pygame.draw.circle(surf, color, pos, radius)

def draw_neon_text(surf, text, font, color, pos, glow=True):
    """绘制霓虹文字"""
    if glow:
        glow_surf = font.render(text, True, (*color[:3], 60))
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            surf.blit(glow_surf, (pos[0] + dx, pos[1] + dy))
    text_surf = font.render(text, True, color)
    surf.blit(text_surf, pos)

# ========== 粒子系统 ==========
class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, life=None, size=None):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx if vx is not None else random.uniform(-3, 3)
        self.vy = vy if vy is not None else random.uniform(-3, 3)
        self.life = life if life is not None else random.randint(20, 40)
        self.max_life = self.life
        self.size = size if size is not None else random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.98
        self.vy *= 0.98
        self.life -= 1
        return self.life > 0

    def draw(self, surf):
        alpha = int(255 * (self.life / self.max_life))
        size = self.size * (self.life / self.max_life)
        if size > 0.5:
            c = (*self.color[:3], alpha)
            s = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, c, (int(size), int(size)), int(size))
            surf.blit(s, (int(self.x - size), int(self.y - size)))

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=20):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1, 5)
            self.particles.append(Particle(
                x, y, color,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed
            ))

    def update(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw(self, surf):
        for p in self.particles:
            p.draw(surf)

# ========== 星空背景 ==========
class Star:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.speed = random.uniform(0.3, 1.5)
        self.brightness = random.randint(50, 200)
        self.size = random.choice([1, 1, 1, 2, 2, 3])

    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, surf):
        alpha = self.brightness + random.randint(-20, 20)
        alpha = max(30, min(255, alpha))
        c = (alpha, alpha, alpha)
        pygame.draw.circle(surf, c, (int(self.x), int(self.y)), self.size)

# ========== 玩家类 ==========
class Player:
    def __init__(self):
        self.reset()
        self.trail = []

    def reset(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 80
        self.radius = 14
        self.lives = MAX_LIVES
        self.invincible = 0
        self.shoot_cooldown = 0
        self.shoot_delay = 8

    def update(self, keys):
        # 移动
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += PLAYER_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= PLAYER_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += PLAYER_SPEED

        # 对角线速度归一化
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        self.x += dx
        self.y += dy
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))

        # 拖尾
        self.trail.append((self.x, self.y))
        if len(self.trail) > 15:
            self.trail.pop(0)

        # 无敌计时
        if self.invincible > 0:
            self.invincible -= 1

        # 射击冷却
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def can_shoot(self):
        return self.shoot_cooldown == 0

    def shoot(self):
        self.shoot_cooldown = self.shoot_delay
        return Bullet(self.x, self.y - self.radius, -BULLET_SPEED, is_player=True)

    def hit(self):
        if self.invincible == 0:
            self.lives -= 1
            self.invincible = INVINCIBLE_FRAMES
            return True
        return False

    def draw(self, surf):
        # 拖尾
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(100 * i / len(self.trail))
            size = self.radius * (0.3 + 0.7 * i / len(self.trail))
            if size > 1:
                c = (*NEON_CYAN[:3], alpha)
                s = pygame.Surface((int(size * 2), int(size * 2)), pygame.SRCALPHA)
                pygame.draw.circle(s, c, (int(size), int(size)), int(size))
                surf.blit(s, (int(tx - size), int(ty - size)))

        # 无敌闪烁
        if self.invincible > 0 and (self.invincible // 6) % 2 == 0:
            return

        # 玩家飞船 (三角形)
        points = [
            (self.x, self.y - self.radius),
            (self.x - self.radius * 0.8, self.y + self.radius * 0.7),
            (self.x, self.y + self.radius * 0.3),
            (self.x + self.radius * 0.8, self.y + self.radius * 0.7),
        ]
        # 发光
        for i in range(3):
            glow_color = (*NEON_CYAN[:3], 40 - i * 10)
            offset = (3 - i) * 2
            glow_points = [(px, py + offset) for px, py in points]
            g_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(g_surf, glow_color, glow_points)
            surf.blit(g_surf, (0, 0))
        pygame.draw.polygon(surf, NEON_CYAN, points, 0)

        # 引擎火焰
        flicker = random.randint(-3, 3)
        flame_y = self.y + self.radius * 0.3
        flame_points = [
            (self.x - 4, flame_y),
            (self.x, flame_y + 10 + flicker),
            (self.x + 4, flame_y),
        ]
        pygame.draw.polygon(surf, NEON_ORANGE, flame_points, 0)
        pygame.draw.polygon(surf, NEON_YELLOW, [
            (self.x - 2, flame_y),
            (self.x, flame_y + 6 + flicker // 2),
            (self.x + 2, flame_y),
        ], 0)

# ========== 子弹类 ==========
class Bullet:
    def __init__(self, x, y, vy, vx=0, is_player=False, color=None):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.is_player = is_player
        self.radius = 4 if is_player else 3
        self.color = color if color else (NEON_CYAN if is_player else NEON_PINK)
        self.active = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if (self.y < -20 or self.y > SCREEN_HEIGHT + 20 or
                self.x < -20 or self.x > SCREEN_WIDTH + 20):
            self.active = False

    def draw(self, surf):
        draw_glow_circle(surf, self.color, (int(self.x), int(self.y)), self.radius)

# ========== 敌人类 ==========
class Enemy:
    def __init__(self, x, y, kind=0, wave=1):
        self.x = x
        self.y = y
        self.kind = kind  # 0=普通, 1=散射, 2=螺旋, 3=Boss
        self.radius = 18 + kind * 4
        self.hp = 1 + kind + wave // 5
        self.max_hp = self.hp
        self.wave = wave
        self.active = True
        self.shoot_timer = random.randint(30, 90)
        self.shoot_delay = max(20, 80 - wave * 2)
        self.move_timer = 0
        self.move_pattern = random.choice(['sine', 'straight', 'zigzag'])
        self.phase = random.uniform(0, math.pi * 2)

        # 颜色
        self.colors = [NEON_GREEN, NEON_ORANGE, NEON_PURPLE, NEON_RED]
        self.color = self.colors[kind] if kind < 4 else NEON_RED

    def update(self, player_x, player_y):
        # 移动
        if self.move_pattern == 'sine':
            self.x += math.sin(self.phase + self.move_timer * 0.03) * 1.5
            self.y += 0.8
        elif self.move_pattern == 'straight':
            self.y += 1.2
        elif self.move_pattern == 'zigzag':
            if self.move_timer % 60 < 30:
                self.x += 1.5
            else:
                self.x -= 1.5
            self.y += 1.0

        self.move_timer += 1
        self.phase += 0.02

        # 边界检查
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))

        # 出屏
        if self.y > SCREEN_HEIGHT + 50:
            self.active = False

        # 射击
        self.shoot_timer -= 1
        bullets = []
        if self.shoot_timer <= 0:
            self.shoot_timer = self.shoot_delay
            bullets = self._create_bullets(player_x, player_y)
        return bullets

    def _create_bullets(self, player_x, player_y):
        bullets = []
        if self.kind == 0:  # 普通: 瞄准玩家
            dx = player_x - self.x
            dy = player_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                speed = ENEMY_BULLET_SPEED
                vx = dx / dist * speed
                vy = dy / dist * speed
                bullets.append(Bullet(self.x, self.y + self.radius, vy, vx,
                                      color=NEON_PINK))

        elif self.kind == 1:  # 散射: 扇形弹幕
            for angle in range(-30, 31, 10):
                rad = math.radians(angle + 90)
                speed = ENEMY_BULLET_SPEED * 0.8
                vx = math.cos(rad) * speed
                vy = math.sin(rad) * speed
                bullets.append(Bullet(self.x, self.y + self.radius, vy, vx,
                                      color=NEON_ORANGE))

        elif self.kind == 2:  # 螺旋: 旋转弹幕
            self.phase += 0.3
            for i in range(3):
                rad = self.phase + i * math.pi * 2 / 3
                speed = ENEMY_BULLET_SPEED * 0.7
                vx = math.cos(rad) * speed
                vy = math.sin(rad) * speed
                bullets.append(Bullet(self.x, self.y + self.radius, vy, vx,
                                      color=NEON_PURPLE))

        elif self.kind == 3:  # Boss: 多重弹幕
            # 圆形爆发
            for i in range(16):
                rad = math.radians(i * 360 / 16) + self.move_timer * 0.05
                speed = ENEMY_BULLET_SPEED * 0.6
                vx = math.cos(rad) * speed
                vy = math.sin(rad) * speed
                bullets.append(Bullet(self.x, self.y, vy, vx,
                                      color=NEON_RED))
            # 瞄准弹
            dx = player_x - self.x
            dy = player_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                speed = ENEMY_BULLET_SPEED * 0.9
                vx = dx / dist * speed
                vy = dy / dist * speed
                bullets.append(Bullet(self.x, self.y, vy, vx,
                                      color=NEON_YELLOW, radius=5))

        return bullets

    def take_damage(self, dmg=1):
        self.hp -= dmg
        if self.hp <= 0:
            self.active = False
            return True  # 被消灭
        return False

    def draw(self, surf):
        # 发光
        for i in range(3):
            alpha = 60 - i * 15
            r = self.radius + (3 - i) * 4
            c = (*self.color[:3], alpha)
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, c, (r, r), r)
            surf.blit(s, (int(self.x - r), int(self.y - r)))

        # 本体
        if self.kind < 3:
            points = []
            segments = 6
            for i in range(segments):
                rad = math.radians(i * 360 / segments - 90) + self.move_timer * 0.02
                r = self.radius * (0.6 + 0.4 * math.sin(self.phase + i))
                px = self.x + math.cos(rad) * r
                py = self.y + math.sin(rad) * r
                points.append((px, py))
            pygame.draw.polygon(surf, self.color, points, 0)
            pygame.draw.polygon(surf, WHITE, points, 1)
        else:
            # Boss: 大型菱形 + 旋转边框
            for i in range(4):
                rad = math.radians(i * 90 - 45) + self.move_timer * 0.03
                r = self.radius
                px = self.x + math.cos(rad) * r
                py = self.y + math.sin(rad) * r
                glow_c = (*self.color[:3], 80)
                draw_glow_circle(surf, glow_c, (int(px), int(py)), 6)
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius, 3)

        # 血条
        if self.hp < self.max_hp:
            bar_w = self.radius * 2
            bar_h = 4
            bar_x = self.x - bar_w // 2
            bar_y = self.y - self.radius - 10
            pygame.draw.rect(surf, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(surf, NEON_GREEN,
                             (bar_x, bar_y, bar_w * self.hp / self.max_hp, bar_h))

# ========== 游戏主类 ==========
class DanmakuGame:
    def __init__(self):
        self.reset()

    def reset(self):
        self.player = Player()
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.particles = ParticleSystem()
        self.stars = [Star() for _ in range(100)]
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.wave = 0
        self.wave_timer = 60  # 波次间隔
        self.spawn_timer = 0
        self.game_over = False
        self.paused = False
        self.enemies_per_wave = 3
        self.wave_active = False

    def start_wave(self):
        self.wave += 1
        self.wave_active = True
        self.enemies_per_wave = min(3 + self.wave * 2, 20)
        self.spawn_timer = 0

        # Boss 每5波出现
        if self.wave % 5 == 0:
            boss = Enemy(SCREEN_WIDTH // 2, -30, kind=3, wave=self.wave)
            self.enemies.append(boss)
        else:
            # 普通敌人
            for _ in range(self.enemies_per_wave):
                kind = random.choices(
                    [0, 1, 2],
                    weights=[max(30 - self.wave, 5), min(20 + self.wave, 40),
                             min(10 + self.wave * 2, 30)]
                )[0]
                kind = min(kind, 2)
                x = random.randint(60, SCREEN_WIDTH - 60)
                y = random.randint(-80, -20)
                self.enemies.append(Enemy(x, y, kind, self.wave))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_p and not self.game_over:
                    self.paused = not self.paused
                if self.game_over and event.key == pygame.K_r:
                    self.reset()
                if self.game_over and event.key == pygame.K_q:
                    return False
                if not self.game_over and event.key == pygame.K_z:
                    if self.player.can_shoot():
                        self.bullets.append(self.player.shoot())
        return True

    def update(self):
        if self.game_over or self.paused:
            return

        # 星空
        for star in self.stars:
            star.update()

        # 玩家
        keys = pygame.key.get_pressed()
        self.player.update(keys)

        # 按住Z连续射击
        if keys[pygame.K_z] and not self.game_over:
            if self.player.can_shoot():
                self.bullets.append(self.player.shoot())

        # 波次管理
        if not self.wave_active:
            self.wave_timer -= 1
            if self.wave_timer <= 0:
                self.start_wave()
                self.wave_timer = 60
        else:
            # 检查是否所有敌人都被消灭了
            active_enemies = [e for e in self.enemies if e.active]
            if not active_enemies:
                # 等待子弹也清空
                active_bullets = [b for b in self.enemy_bullets if b.active]
                if not active_bullets:
                    self.wave_active = False
                    self.wave_timer = 90  # 下一波前休息

        # 玩家子弹
        for b in self.bullets:
            b.update()

        # 敌人子弹
        for b in self.enemy_bullets:
            b.update()

        # 敌人
        for e in self.enemies:
            if e.active:
                new_bullets = e.update(self.player.x, self.player.y)
                self.enemy_bullets.extend(new_bullets)

        # 碰撞检测: 玩家子弹 vs 敌人
        for b in self.bullets:
            if not b.active:
                continue
            for e in self.enemies:
                if not e.active:
                    continue
                dist = math.hypot(b.x - e.x, b.y - e.y)
                if dist < e.radius + b.radius:
                    b.active = False
                    if e.take_damage(1):
                        # 敌人被消灭
                        self.score += 100 * (1 + self.wave // 3)
                        self.combo += 1
                        self.max_combo = max(self.max_combo, self.combo)
                        # 粒子效果
                        self.particles.emit(e.x, e.y, e.color, 30)
                        if self.combo >= 10:
                            self.particles.emit(e.x, e.y, NEON_YELLOW, 15)
                    else:
                        # 敌人受伤
                        self.particles.emit(b.x, b.y, NEON_YELLOW, 5)
                    break

        # 碰撞检测: 敌人子弹 vs 玩家
        for b in self.enemy_bullets:
            if not b.active:
                continue
            dist = math.hypot(b.x - self.player.x, b.y - self.player.y)
            if dist < self.player.radius + b.radius:
                b.active = False
                if self.player.hit():
                    self.particles.emit(self.player.x, self.player.y, NEON_CYAN, 40)
                    self.combo = 0
                    if self.player.lives <= 0:
                        self.game_over = True
                        self.particles.emit(self.player.x, self.player.y,
                                            NEON_RED, 60)

        # 碰撞检测: 玩家 vs 敌人 (相撞)
        for e in self.enemies:
            if not e.active:
                continue
            dist = math.hypot(self.player.x - e.x, self.player.y - e.y)
            if dist < self.player.radius + e.radius:
                e.active = False
                self.particles.emit(e.x, e.y, e.color, 30)
                if self.player.hit():
                    self.particles.emit(self.player.x, self.player.y, NEON_CYAN, 40)
                    self.combo = 0
                    if self.player.lives <= 0:
                        self.game_over = True
                        self.particles.emit(self.player.x, self.player.y,
                                            NEON_RED, 60)

        # 清理
        self.bullets = [b for b in self.bullets if b.active]
        self.enemy_bullets = [b for b in self.enemy_bullets if b.active]
        self.enemies = [e for e in self.enemies if e.active]

        # 粒子
        self.particles.update()

    def draw(self):
        screen.fill(DARK_BG)

        # 星空
        for star in self.stars:
            star.draw(screen)

        if self.paused:
            # 暂停状态
            for e in self.enemies:
                e.draw(screen)
            for b in self.bullets:
                b.draw(screen)
            for b in self.enemy_bullets:
                b.draw(screen)
            self.player.draw(screen)
            self.particles.draw(screen)

            # 暂停文字
            pause_text = font_large.render("暂停", True, NEON_CYAN)
            pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(pause_text, pause_rect)
            draw_neon_text(screen, "按 P 继续", font_mid, NEON_CYAN,
                          (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 50))
        elif self.game_over:
            # 游戏结束
            self.particles.draw(screen)

            draw_neon_text(screen, "游戏结束", font_large, NEON_RED,
                          (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 - 80))
            draw_neon_text(screen, f"最终得分: {self.score}", font_mid, NEON_YELLOW,
                          (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
            draw_neon_text(screen, f"最高连击: {self.max_combo}", font_mid, NEON_CYAN,
                          (SCREEN_WIDTH // 2 - 90, SCREEN_HEIGHT // 2 + 40))
            draw_neon_text(screen, "按 R 重新开始 | 按 Q 退出", font_small, WHITE,
                          (SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 + 90))
        else:
            # 游玩状态
            for e in self.enemies:
                e.draw(screen)
            for b in self.bullets:
                b.draw(screen)
            for b in self.enemy_bullets:
                b.draw(screen)
            self.player.draw(screen)
            self.particles.draw(screen)

        # HUD (始终显示)
        self.draw_hud(screen)

        pygame.display.flip()

    def draw_hud(self, surf):
        # 得分
        draw_neon_text(surf, f"得分: {self.score}", font_mid, WHITE, (10, 10), glow=False)
        # 波次
        draw_neon_text(surf, f"第 {self.wave} 波", font_mid, NEON_CYAN,
                      (SCREEN_WIDTH // 2 - 50, 10), glow=False)
        # 连击
        if self.combo > 0:
            combo_color = NEON_GREEN if self.combo < 10 else NEON_YELLOW if self.combo < 30 else NEON_RED
            draw_neon_text(surf, f"连击 x{self.combo}", font_small, combo_color,
                          (SCREEN_WIDTH // 2 - 50, 40), glow=False)

        # 生命值
        lives_text = "♥ " * self.player.lives
        draw_neon_text(surf, lives_text.strip(), font_mid, NEON_RED,
                      (SCREEN_WIDTH - 120, 10), glow=False)

        # 操作提示
        if self.wave == 0 and not self.wave_active:
            draw_neon_text(surf, "← → ↑ ↓ 移动 | Z 射击 | P 暂停", font_small, WHITE,
                          (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT - 30), glow=False)

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            clock.tick(FPS)
        pygame.quit()
        sys.exit()

# ========== 入口 ==========
if __name__ == "__main__":
    game = DanmakuGame()
    game.run()