"""
Galaga (大蜜蜂) - 经典街机固定屏幕射击游戏
Python + Pygame 实现
日期: 2026-08-25

玩法:
- 左右移动战机，空格/鼠标左键射击
- 消灭所有敌机过关
- 敌机会俯冲攻击，可能捕获你的战机
- 解救被捕获战机可合体获得双倍火力
- 每关有 BONUS 阶段（敌机编队飞行射击）
"""

import pygame
import sys
import random
import math

# ---------- 常量 ----------
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 700
FPS = 60

# 颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 80)
PURPLE = (200, 50, 255)
ORANGE = (255, 150, 50)
CYAN = (50, 255, 255)

# 玩家
PLAYER_SPEED = 5
BULLET_SPEED = -10
ENEMY_BULLET_SPEED = 5

# 敌机编队
FORM_ROWS = 5
FORM_COLS = 10
FORM_LEFT = 60
FORM_TOP = 80
FORM_SPACING_X = 38
FORM_SPACING_Y = 38
FORM_MOVE_SPEED = 0.5
FORM_MOVE_DOWN = 3

# 游戏状态
STATE_ATTRACT = 0      # 标题画面
STATE_PLAYING = 1      # 游戏中
STATE_BONUS = 2        # BONUS 阶段
STATE_GAMEOVER = 3     # 游戏结束
STATE_TRANSITION = 4   # 关卡过渡


# ---------- 玩家类 ----------
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # 绘制三角形战机
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self._draw_ship(self.image, CYAN)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = PLAYER_SPEED
        self.shoot_cooldown = 0
        self.shoot_delay = 8
        self.double_shot = False  # 双倍火力
        self.invincible = 0
        self.lives = 3
        self.captured = False
        self.respawn_timer = 0

    @staticmethod
    def _draw_ship(surface, color):
        cx, cy = 16, 16
        # 机身
        points = [(cx, cy - 14), (cx - 12, cy + 8), (cx, cy + 4), (cx + 12, cy + 8)]
        pygame.draw.polygon(surface, color, points, 0)
        pygame.draw.polygon(surface, WHITE, points, 1)
        # 机翼
        wing_points = [(cx - 6, cy + 2), (cx - 16, cy + 12), (cx - 6, cy + 8)]
        pygame.draw.polygon(surface, color, wing_points, 0)
        wing_points2 = [(cx + 6, cy + 2), (cx + 16, cy + 12), (cx + 6, cy + 8)]
        pygame.draw.polygon(surface, color, wing_points2, 0)
        # 座舱
        pygame.draw.circle(surface, WHITE, (cx, cy - 6), 3)

    def update(self):
        if self.captured:
            return
        if self.respawn_timer > 0:
            self.respawn_timer -= 1
            return
        if self.invincible > 0:
            self.invincible -= 1
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

    def shoot(self):
        if self.captured or self.respawn_timer > 0 or self.shoot_cooldown > 0:
            return []
        self.shoot_cooldown = self.shoot_delay
        bullets = []
        b = Bullet(self.rect.centerx, self.rect.top)
        bullets.append(b)
        if self.double_shot:
            b2 = Bullet(self.rect.centerx - 8, self.rect.top)
            b3 = Bullet(self.rect.centerx + 8, self.rect.top)
            bullets.append(b2)
            bullets.append(b3)
        return bullets

    def respawn(self):
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 30
        self.invincible = 90
        self.respawn_timer = 30
        self.double_shot = False
        self.captured = False

    def draw(self, surface):
        if self.captured:
            return
        if self.respawn_timer > 0:
            if self.respawn_timer % 6 < 3:
                surface.blit(self.image, self.rect)
            return
        if self.invincible > 0 and self.invincible % 6 < 3:
            return  # 闪烁
        surface.blit(self.image, self.rect)


# ---------- 子弹类 ----------
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, is_enemy=False):
        super().__init__()
        self.is_enemy = is_enemy
        if is_enemy:
            self.image = pygame.Surface((6, 12))
            self.image.fill(RED)
            # 加一点细节
            pygame.draw.circle(self.image, YELLOW, (3, 3), 2)
        else:
            self.image = pygame.Surface((4, 14))
            self.image.fill(CYAN)
            pygame.draw.line(self.image, WHITE, (2, 0), (2, 14), 2)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = ENEMY_BULLET_SPEED if is_enemy else BULLET_SPEED

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()


# ---------- 敌机类 ----------
class Enemy(pygame.sprite.Sprite):
    # 敌机类型定义: (color, score, hp)
    TYPES = {
        'A': (PURPLE, 50, 1),    # 紫色 - 普通
        'B': (RED, 100, 1),      # 红色 - 快速
        'C': (GREEN, 150, 2),    # 绿色 - 双血
        'D': (ORANGE, 200, 3),   # 橙色 - 三血/旗舰
    }

    def __init__(self, etype, form_col, form_row):
        super().__init__()
        self.etype = etype
        self.color, self.score_value, self.max_hp = self.TYPES[etype]
        self.hp = self.max_hp
        self.form_col = form_col
        self.form_row = form_row

        # 绘制敌机
        size = 28
        self.base_image = pygame.Surface((size, size), pygame.SRCALPHA)
        self._draw_enemy(self.base_image, self.color)

        self.image = self.base_image.copy()
        self.rect = self.image.get_rect()

        # 编队位置
        self.form_x = FORM_LEFT + form_col * FORM_SPACING_X
        self.form_y = FORM_TOP + form_row * FORM_SPACING_Y
        self.rect.x = self.form_x
        self.rect.y = self.form_y

        # 状态
        self.in_formation = True
        self.diving = False
        self.returning = False
        self.captured_player = None  # 是否捕获了玩家
        self.return_timer = 0

        # 俯冲参数
        self.dive_angle = 0
        self.dive_speed = 0
        self.dive_target_x = 0
        self.start_x = 0
        self.start_y = 0
        self.dive_phase = 0  # 0:进入俯冲, 1:攻击, 2:拉起

        # 闪烁效果
        self.hit_timer = 0

    @staticmethod
    def _draw_enemy(surface, color):
        cx, cy = 14, 14
        # 主体
        body = [(cx, cy - 10), (cx - 10, cy + 4), (cx, cy), (cx + 10, cy + 4)]
        pygame.draw.polygon(surface, color, body, 0)
        pygame.draw.polygon(surface, WHITE, body, 1)
        # 翅膀
        wing1 = [(cx - 6, cy - 2), (cx - 13, cy + 6), (cx - 6, cy + 4)]
        wing2 = [(cx + 6, cy - 2), (cx + 13, cy + 6), (cx + 6, cy + 4)]
        pygame.draw.polygon(surface, color, wing1, 0)
        pygame.draw.polygon(surface, color, wing2, 0)
        # 眼睛
        pygame.draw.circle(surface, WHITE, (cx - 4, cy - 4), 3)
        pygame.draw.circle(surface, WHITE, (cx + 4, cy - 4), 3)
        pygame.draw.circle(surface, BLACK, (cx - 4, cy - 4), 1)
        pygame.draw.circle(surface, BLACK, (cx + 4, cy - 4), 1)

    def start_dive(self, player_x):
        """开始俯冲攻击"""
        self.in_formation = False
        self.diving = True
        self.start_x = self.rect.x
        self.start_y = self.rect.y
        self.dive_target_x = player_x + random.randint(-20, 20)
        self.dive_angle = 0
        self.dive_speed = 3 + random.random() * 2
        self.dive_phase = 0

    def update(self, formation_offset_x=0, formation_offset_y=0):
        if self.hit_timer > 0:
            self.hit_timer -= 1

        if self.in_formation:
            # 跟随编队移动
            self.rect.x = self.form_x + formation_offset_x
            self.rect.y = self.form_y + formation_offset_y

        elif self.diving:
            # 俯冲攻击 - 正弦波路径
            if self.dive_phase == 0:
                # 向下俯冲
                dx = self.dive_target_x - self.start_x
                dy = SCREEN_HEIGHT - self.start_y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    vx = dx / dist * self.dive_speed
                    vy = dy / dist * self.dive_speed
                    self.rect.x += vx
                    self.rect.y += vy + math.sin(self.rect.y * 0.05) * 1.5
                if self.rect.y > SCREEN_HEIGHT - 100:
                    self.dive_phase = 1
            elif self.dive_phase == 1:
                # 到达底部，开始拉起
                self.rect.y -= self.dive_speed * 0.5
                self.rect.x += math.sin(self.rect.y * 0.1) * 2
                if self.rect.y < self.start_y + 50:
                    self.dive_phase = 2
            elif self.dive_phase == 2:
                # 返回编队位置
                tx = self.form_x + formation_offset_x
                ty = self.form_y + formation_offset_y
                dx = tx - self.rect.x
                dy = ty - self.rect.y
                self.rect.x += dx * 0.05
                self.rect.y += dy * 0.05
                if abs(dx) < 2 and abs(dy) < 2:
                    self.rect.x = tx
                    self.rect.y = ty
                    self.diving = False
                    self.in_formation = True

        elif self.returning:
            if self.return_timer > 0:
                self.return_timer -= 1
                self.rect.y -= 2
            else:
                self.returning = False
                self.in_formation = True
                self.rect.x = self.form_x + formation_offset_x
                self.rect.y = self.form_y + formation_offset_y

        # 边界
        self.rect.clamp_ip(pygame.Rect(-10, -10, SCREEN_WIDTH + 20, SCREEN_HEIGHT + 20))

    def draw(self, surface):
        if self.hit_timer > 0 and self.hit_timer % 4 < 2:
            # 被击中闪烁白色
            flash_img = self.base_image.copy()
            flash_img.fill(WHITE, special_flags=pygame.BLEND_MAX)
            surface.blit(flash_img, self.rect)
        else:
            surface.blit(self.image, self.rect)

    def hit(self):
        self.hp -= 1
        self.hit_timer = 10
        return self.hp <= 0


# ---------- 星尘背景 ----------
class StarField:
    def __init__(self):
        self.stars = []
        for _ in range(80):
            self.stars.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'speed': random.uniform(0.3, 1.5),
                'size': random.randint(1, 3),
                'brightness': random.randint(100, 255)
            })

    def update(self):
        for star in self.stars:
            star['y'] += star['speed']
            if star['y'] > SCREEN_HEIGHT:
                star['y'] = 0
                star['x'] = random.randint(0, SCREEN_WIDTH)

    def draw(self, surface):
        for star in self.stars:
            c = star['brightness']
            pygame.draw.circle(surface, (c, c, c), (int(star['x']), int(star['y'])), star['size'])


# ---------- 粒子特效 ----------
class Particle:
    def __init__(self, x, y, color, vel_x=0, vel_y=0, size=3, lifetime=30):
        self.x = x
        self.y = y
        self.vx = vel_x + random.uniform(-3, 3)
        self.vy = vel_y + random.uniform(-3, 3)
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1  # 重力
        self.lifetime -= 1
        self.size = max(0, self.size - 0.1)

    def draw(self, surface):
        alpha = int(255 * self.lifetime / self.max_lifetime)
        c = self.color
        pygame.draw.circle(surface, (c[0], c[1], c[2]), (int(self.x), int(self.y)), int(self.size))

    @property
    def dead(self):
        return self.lifetime <= 0 or self.size <= 0


# ---------- 游戏主类 ----------
class GalagaGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Galaga 大蜜蜂 - 2026-08-25")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 42)
        self.font_small = pygame.font.Font(None, 28)

        self.starfield = StarField()
        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        self.state = STATE_ATTRACT
        self.score = 0
        self.high_score = 0
        self.level = 1
        self.player = None
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.enemies = []
        self.particles = []
        self.formation_offset_x = 0
        self.formation_offset_y = 0
        self.formation_direction = 1
        self.formation_move_counter = 0
        self.dive_timer = 0
        self.dive_interval = 120
        self.bonus_timer = 0
        self.bonus_duration = 300
        self.bonus_enemies = []
        self.transition_timer = 0
        self.gameover_timer = 0
        self.combo_count = 0
        self.combo_timer = 0
        self.screen_shake = 0
        self.attract_frame = 0

    def start_game(self):
        """开始新游戏"""
        self.state = STATE_PLAYING
        self.score = 0
        self.level = 1
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50)
        self.bullets.empty()
        self.enemy_bullets.empty()
        self.particles.clear()
        self.spawn_formation()
        self.dive_timer = 180  # 初始等待时间稍长

    def spawn_formation(self):
        """生成敌机编队"""
        self.enemies.clear()
        self.formation_offset_x = 0
        self.formation_offset_y = 0
        self.formation_direction = 1

        for row in range(FORM_ROWS):
            for col in range(FORM_COLS):
                # 根据行和列选择类型
                if row == 0 and col in [4, 5]:
                    etype = 'D'  # 旗舰
                elif row == 1 and col in [3, 4, 5, 6]:
                    etype = 'C'  # 双血
                elif row == 2:
                    etype = 'B' if col % 2 == 0 else 'A'
                else:
                    etype = 'A'
                enemy = Enemy(etype, col, row)
                self.enemies.append(enemy)

    def spawn_bonus_enemies(self):
        """生成 BONUS 阶段的敌机编队"""
        self.bonus_enemies.clear()
        colors = [RED, GREEN, BLUE, YELLOW, PURPLE, ORANGE, CYAN, WHITE]
        for i in range(20):
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(30, 200)
            size = 20
            enemy = pygame.Surface((size, size), pygame.SRCALPHA)
            c = random.choice(colors)
            pygame.draw.polygon(enemy, c, [(10, 0), (0, 20), (20, 20)])
            pygame.draw.polygon(enemy, WHITE, [(10, 4), (4, 16), (16, 16)], 1)
            self.bonus_enemies.append({
                'x': x,
                'y': y,
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(-1, 1),
                'surface': enemy,
                'rect': enemy.get_rect(center=(x, y)),
                'score': random.randint(50, 300)
            })

    def update(self):
        self.starfield.update()

        if self.state == STATE_ATTRACT:
            self.attract_frame += 1
            return

        if self.state == STATE_PLAYING:
            self.update_playing()
        elif self.state == STATE_BONUS:
            self.update_bonus()
        elif self.state == STATE_GAMEOVER:
            self.update_gameover()
        elif self.state == STATE_TRANSITION:
            self.update_transition()

        # 更新粒子
        self.particles = [p for p in self.particles if not p.dead]
        for p in self.particles:
            p.update()

        # 屏幕震动
        if self.screen_shake > 0:
            self.screen_shake -= 1

    def update_playing(self):
        if self.player:
            self.player.update()

            # 射击
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                bullets = self.player.shoot()
                for b in bullets:
                    self.bullets.add(b)

        # 更新子弹
        self.bullets.update()
        self.enemy_bullets.update()

        # 更新编队移动
        self.update_formation()

        # 敌机俯冲AI
        self.update_enemy_ai()

        # 更新所有敌机
        for enemy in self.enemies:
            enemy.update(self.formation_offset_x, self.formation_offset_y)

        # 碰撞检测
        self.check_collisions()

        # 检查是否所有敌机被消灭或已俯冲
        active_enemies = [e for e in self.enemies if not e.diving]
        if len(active_enemies) == 0:
            # 进入 BONUS 阶段
            self.start_bonus_phase()

        # 连击计时
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo_count = 0

    def update_formation(self):
        """编队移动逻辑"""
        self.formation_move_counter += 1
        if self.formation_move_counter >= 2:
            self.formation_move_counter = 0
            self.formation_offset_x += FORM_MOVE_SPEED * self.formation_direction

            # 检查边界
            max_x = max((e.form_x for e in self.enemies if e.in_formation), default=0)
            min_x = min((e.form_x for e in self.enemies if e.in_formation), default=0)
            if max_x + self.formation_offset_x > SCREEN_WIDTH - 40:
                self.formation_direction = -1
                self.formation_offset_y += FORM_MOVE_DOWN
            elif min_x + self.formation_offset_x < 20:
                self.formation_direction = 1
                self.formation_offset_y += FORM_MOVE_DOWN

    def update_enemy_ai(self):
        """敌机AI：决定何时俯冲"""
        # 只让编队中的敌机俯冲
        in_formation = [e for e in self.enemies if e.in_formation and not e.diving]
        if not in_formation or not self.player or self.player.captured:
            return

        self.dive_timer -= 1
        if self.dive_timer <= 0:
            # 选择1-3架敌机俯冲
            num_divers = min(random.randint(1, 3), len(in_formation))
            divers = random.sample(in_formation, num_divers)
            for enemy in divers:
                enemy.start_dive(self.player.rect.centerx)
            # 根据关卡调整俯冲频率
            base_interval = max(40, 120 - self.level * 8)
            self.dive_timer = base_interval + random.randint(0, 60)

    def check_collisions(self):
        if not self.player:
            return

        # 玩家子弹 vs 敌机
        for bullet in list(self.bullets):
            if bullet.is_enemy:
                continue
            hit_enemies = []
            for enemy in self.enemies:
                if bullet.rect.colliderect(enemy.rect):
                    if enemy.hit():
                        hit_enemies.append(enemy)
                    bullet.kill()
                    break
            for enemy in hit_enemies:
                self.destroy_enemy(enemy)

        # 敌机子弹 vs 玩家
        if self.player.invincible <= 0 and not self.player.captured and self.player.respawn_timer <= 0:
            for bullet in list(self.enemy_bullets):
                if bullet.rect.colliderect(self.player.rect):
                    bullet.kill()
                    self.player_hit()
                    break

        # 敌机 vs 玩家（俯冲碰撞）
        if self.player.invincible <= 0 and not self.player.captured and self.player.respawn_timer <= 0:
            for enemy in self.enemies:
                if enemy.diving and enemy.rect.colliderect(self.player.rect):
                    if enemy.etype == 'D' and random.random() < 0.3:
                        # 旗舰有概率捕获玩家
                        self.capture_player(enemy)
                    else:
                        self.player_hit()
                    break

    def destroy_enemy(self, enemy):
        """摧毁敌机"""
        # 加分（带连击加成）
        self.combo_count += 1
        self.combo_timer = 120
        combo_bonus = min(self.combo_count, 10)
        points = enemy.score_value * (1 + combo_bonus * 0.1)
        self.score += int(points)

        if self.score > self.high_score:
            self.high_score = self.score

        # 爆炸粒子
        for _ in range(15):
            self.particles.append(Particle(
                enemy.rect.centerx, enemy.rect.centery,
                enemy.color, size=random.randint(2, 5),
                lifetime=random.randint(15, 30)
            ))

        # 如果敌机捕获了玩家，释放玩家
        if enemy.captured_player:
            self.rescue_player(enemy)

        self.enemies.remove(enemy)

        # 屏幕震动
        self.screen_shake = 4

    def player_hit(self):
        """玩家被击中"""
        self.player.lives -= 1
        # 爆炸粒子
        for _ in range(20):
            self.particles.append(Particle(
                self.player.rect.centerx, self.player.rect.centery,
                CYAN, size=random.randint(2, 6),
                lifetime=random.randint(20, 40)
            ))
        self.screen_shake = 8

        if self.player.lives <= 0:
            self.state = STATE_GAMEOVER
            self.gameover_timer = 180
        else:
            self.player.respawn()

    def capture_player(self, enemy):
        """捕获玩家"""
        self.player.captured = True
        enemy.captured_player = self.player
        self.player.rect.centerx = enemy.rect.centerx
        self.player.rect.centery = enemy.rect.centery + 20
        # 显示捕获特效
        for _ in range(10):
            self.particles.append(Particle(
                self.player.rect.centerx, self.player.rect.centery,
                RED, size=2, lifetime=20
            ))

    def rescue_player(self, enemy):
        """解救被捕获的玩家"""
        if self.player and self.player.captured:
            self.player.captured = False
            self.player.double_shot = True
            self.player.rect.centerx = SCREEN_WIDTH // 2
            self.player.rect.bottom = SCREEN_HEIGHT - 30
            self.player.invincible = 60
            # 解救特效
            for _ in range(20):
                self.particles.append(Particle(
                    self.player.rect.centerx, self.player.rect.centery,
                    YELLOW, size=random.randint(2, 4),
                    lifetime=random.randint(20, 40)
                ))
            self.score += 500  # 解救奖励分

    def start_bonus_phase(self):
        """进入 BONUS 阶段"""
        self.state = STATE_BONUS
        self.bonus_timer = self.bonus_duration
        self.spawn_bonus_enemies()
        self.bullets.empty()
        self.enemy_bullets.empty()

    def update_bonus(self):
        """更新 BONUS 阶段"""
        self.bonus_timer -= 1

        if self.player:
            self.player.update()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                bullets = self.player.shoot()
                for b in bullets:
                    self.bullets.add(b)

        self.bullets.update()

        # 移动 BONUS 敌机
        for be in self.bonus_enemies:
            be['x'] += be['vx']
            be['y'] += be['vy']
            if be['x'] < 20 or be['x'] > SCREEN_WIDTH - 20:
                be['vx'] *= -1
            if be['y'] < 20 or be['y'] > 300:
                be['vy'] *= -1
            be['rect'].center = (be['x'], be['y'])

        # 射击 BONUS 敌机
        for bullet in list(self.bullets):
            if bullet.is_enemy:
                continue
            for be in list(self.bonus_enemies):
                if bullet.rect.colliderect(be['rect']):
                    bullet.kill()
                    self.score += be['score']
                    self.bonus_enemies.remove(be)
                    # 粒子
                    for _ in range(8):
                        self.particles.append(Particle(
                            be['x'], be['y'], YELLOW,
                            size=random.randint(2, 4), lifetime=15
                        ))
                    break

        if self.bonus_timer <= 0 or len(self.bonus_enemies) == 0:
            self.end_bonus_phase()

    def end_bonus_phase(self):
        """结束 BONUS 阶段"""
        self.level += 1
        self.state = STATE_TRANSITION
        self.transition_timer = 120

    def update_transition(self):
        """更新关卡过渡"""
        self.transition_timer -= 1
        if self.transition_timer <= 0:
            self.state = STATE_PLAYING
            self.spawn_formation()
            self.dive_timer = 180

    def update_gameover(self):
        """更新游戏结束"""
        self.gameover_timer -= 1
        if self.gameover_timer <= 0:
            self.state = STATE_ATTRACT

    def draw(self):
        self.screen.fill(BLACK)

        # 屏幕震动偏移
        offset_x = 0
        offset_y = 0
        if self.screen_shake > 0:
            offset_x = random.randint(-3, 3)
            offset_y = random.randint(-3, 3)

        # 绘制星尘
        self.starfield.draw(self.screen)

        if self.state == STATE_ATTRACT:
            self.draw_attract()
        else:
            # 绘制游戏内容
            with pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA) as game_surface:
                game_surface.fill((0, 0, 0, 0))

                if self.state == STATE_BONUS:
                    self.draw_bonus(game_surface)
                else:
                    # 绘制敌机
                    for enemy in self.enemies:
                        enemy.draw(game_surface)

                    # 绘制子弹
                    self.bullets.draw(game_surface)
                    self.enemy_bullets.draw(game_surface)

                # 绘制玩家
                if self.player:
                    self.player.draw(game_surface)

                # 绘制粒子
                for p in self.particles:
                    p.draw(game_surface)

                self.screen.blit(game_surface, (offset_x, offset_y))

            # 绘制HUD
            self.draw_hud()

            # 绘制过渡/结束画面
            if self.state == STATE_TRANSITION:
                self.draw_transition()
            elif self.state == STATE_GAMEOVER:
                self.draw_gameover()

        pygame.display.flip()

    def draw_attract(self):
        """绘制标题画面"""
        # 闪烁的标题
        bright = 200 + int(55 * math.sin(self.attract_frame * 0.05))
        title_color = (bright, bright, 50)

        title = self.font_large.render("GALAGA", True, title_color)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(title, title_rect)

        # 副标题
        sub = self.font_small.render("大 蜜 蜂", True, YELLOW)
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, 260))
        self.screen.blit(sub, sub_rect)

        # 装饰 - 敌机编队
        for i in range(8):
            c = [PURPLE, RED, GREEN, ORANGE][i % 4]
            cx = 140 + i * 28
            cy = 340
            Enemy._draw_enemy(self.screen, c)
            # 实际绘制小尺寸
            s = pygame.Surface((20, 20), pygame.SRCALPHA)
            Enemy._draw_enemy(s, c)
            self.screen.blit(s, (cx, cy))

        # 操作说明
        instr_y = 430
        instrs = [
            "← → 或 A/D 移动",
            "SPACE 或 鼠标左键 射击",
            "消灭所有敌机过关",
            "解救被俘战机获得双倍火力!",
        ]
        for i, text in enumerate(instrs):
            instr = self.font_small.render(text, True, WHITE)
            instr_rect = instr.get_rect(center=(SCREEN_WIDTH // 2, instr_y + i * 35))
            self.screen.blit(instr, instr_rect)

        # 最高分
        if self.high_score > 0:
            hs = self.font_medium.render(f"HIGH SCORE: {self.high_score}", True, YELLOW)
            hs_rect = hs.get_rect(center=(SCREEN_WIDTH // 2, 620))
            self.screen.blit(hs, hs_rect)

        # 开始提示（闪烁）
        if self.attract_frame % 60 < 40:
            start = self.font_medium.render("按 ENTER 开始游戏", True, GREEN)
            start_rect = start.get_rect(center=(SCREEN_WIDTH // 2, 560))
            self.screen.blit(start, start_rect)

    def draw_hud(self):
        """绘制HUD信息"""
        # 分数
        score_text = self.font_small.render(f"SCORE: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        # 最高分
        hs_text = self.font_small.render(f"HIGH: {self.high_score}", True, YELLOW)
        self.screen.blit(hs_text, (10, 38))

        # 关卡
        level_text = self.font_small.render(f"LEVEL {self.level}", True, CYAN)
        self.screen.blit(level_text, (SCREEN_WIDTH - 120, 10))

        # 生命数
        lives_text = self.font_small.render(f"LIVES: {self.player.lives if self.player else 0}", True, GREEN)
        self.screen.blit(lives_text, (SCREEN_WIDTH - 120, 38))

        # 双倍火力指示
        if self.player and self.player.double_shot:
            double_text = self.font_small.render("★ DOUBLE", True, YELLOW)
            self.screen.blit(double_text, (SCREEN_WIDTH // 2 - 50, 10))

        # 连击指示
        if self.combo_count > 1 and self.combo_timer > 0:
            combo_text = self.font_small.render(f"COMBO x{self.combo_count}", True, ORANGE)
            self.screen.blit(combo_text, (SCREEN_WIDTH // 2 - 50, 38))

    def draw_bonus(self, surface):
        """绘制 BONUS 阶段"""
        # 绘制 BONUS 敌机
        for be in self.bonus_enemies:
            surface.blit(be['surface'], be['rect'])

        # BONUS 文字
        bonus_color = [YELLOW, ORANGE, WHITE][(pygame.time.get_ticks() // 200) % 3]
        bonus_text = self.font_medium.render("BONUS STAGE!", True, bonus_color)
        bonus_rect = bonus_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
        surface.blit(bonus_text, bonus_rect)

        # 剩余时间
        time_left = self.bonus_timer // 60
        time_text = self.font_small.render(f"TIME: {time_left}", True, WHITE)
        time_rect = time_text.get_rect(center=(SCREEN_WIDTH // 2, 390))
        surface.blit(time_text, time_rect)

    def draw_transition(self):
        """绘制关卡过渡"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        text = self.font_large.render(f"LEVEL {self.level}", True, CYAN)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text, text_rect)

        sub = self.font_small.render("GET READY!", True, WHITE)
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(sub, sub_rect)

    def draw_gameover(self):
        """绘制游戏结束"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        text = self.font_large.render("GAME OVER", True, RED)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(text, text_rect)

        score = self.font_medium.render(f"SCORE: {self.score}", True, WHITE)
        score_rect = score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(score, score_rect)

        if self.score >= self.high_score and self.score > 0:
            hs = self.font_medium.render("NEW HIGH SCORE!", True, YELLOW)
            hs_rect = hs.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
            self.screen.blit(hs, hs_rect)

        if self.gameover_timer > 120:
            restart = self.font_small.render("按 ENTER 重新开始", True, GREEN)
            restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 110))
            self.screen.blit(restart, restart_rect)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if self.state == STATE_ATTRACT:
                        self.start_game()
                    elif self.state == STATE_GAMEOVER and self.gameover_timer > 120:
                        self.start_game()
                if event.key == pygame.K_SPACE:
                    if self.state == STATE_ATTRACT:
                        self.start_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    if self.state == STATE_ATTRACT:
                        self.start_game()

        # 鼠标射击
        if self.state in (STATE_PLAYING, STATE_BONUS) and self.player:
            mouse_buttons = pygame.mouse.get_pressed()
            if mouse_buttons[0]:
                bullets = self.player.shoot()
                for b in bullets:
                    self.bullets.add(b)

        return True

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ---------- 入口 ----------
if __name__ == "__main__":
    game = GalagaGame()
    game.run()