"""
雪仗大战 (Snowball Fight)
======================
控制角色躲避并反击敌人的雪球攻击！
- ← → 移动
- SPACE 投掷雪球
- 消灭敌人得分，躲避雪球保命

作者: AI Game Developer
日期: 2026-07-05
"""

import pygame
import random
import sys
import math

# ==================== 初始化 ====================
pygame.init()
pygame.mixer.init()

# ==================== 常量 ====================
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 150, 255)
DARK_BLUE = (50, 80, 180)
RED = (255, 60, 60)
GREEN = (60, 200, 100)
YELLOW = (255, 255, 100)
BROWN = (139, 90, 43)
SKIN = (255, 220, 180)
GRAY = (180, 180, 190)
SNOW_COLOR = (230, 240, 255)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("雪仗大战 - Snowball Fight")
clock = pygame.time.Clock()
font_large = pygame.font.SysFont("simhei", 60, bold=True)
font_medium = pygame.font.SysFont("simhei", 36, bold=True)
font_small = pygame.font.SysFont("simhei", 24, bold=True)


# ==================== 工具函数 ====================
def draw_text(text, font, color, x, y, center=True):
    """绘制文字，默认居中"""
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(img, rect)


# ==================== 雪球类 ====================
class Snowball:
    """雪球 - 飞行物"""

    def __init__(self, x, y, vx, vy, radius=8, color=WHITE):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.color = color
        self.active = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        # 超出屏幕则失效
        if (self.y < -20 or self.y > HEIGHT + 20 or
                self.x < -20 or self.x > WIDTH + 20):
            self.active = False

    def draw(self, surface):
        # 雪球阴影
        pygame.draw.circle(surface, (180, 200, 220),
                           (int(self.x) + 2, int(self.y) + 2), self.radius)
        # 雪球主体
        pygame.draw.circle(surface, self.color,
                           (int(self.x), int(self.y)), self.radius)
        # 高光
        pygame.draw.circle(surface, (255, 255, 255),
                           (int(self.x) - 2, int(self.y) - 2), self.radius // 3)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)


# ==================== 玩家类 ====================
class Player:
    """玩家 - 雪人造型"""

    def __init__(self):
        self.width = 40
        self.height = 60
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - 100
        self.speed = 6
        self.lives = 3
        self.invincible = 0  # 无敌帧
        self.cooldown = 0  # 攻击冷却
        self.score = 0

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, keys):
        # 移动
        if keys[pygame.K_LEFT] and self.x > 0:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] and self.x < WIDTH - self.width:
            self.x += self.speed

        # 冷却递减
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.invincible > 0:
            self.invincible -= 1

    def draw(self, surface):
        # 无敌闪烁效果
        if self.invincible > 0 and self.invincible % 6 < 3:
            return

        cx = self.x + self.width // 2
        # 身体（下雪球）
        pygame.draw.circle(surface, WHITE, (cx, self.y + 40), 22)
        # 身体阴影
        pygame.draw.circle(surface, (220, 230, 240), (cx, self.y + 44), 22)
        # 头部（上雪球）
        pygame.draw.circle(surface, WHITE, (cx, self.y + 15), 18)
        # 帽子
        hat_rect = pygame.Rect(cx - 14, self.y - 5, 28, 18)
        pygame.draw.rect(surface, DARK_BLUE, hat_rect)
        pygame.draw.rect(surface, DARK_BLUE, (cx - 20, self.y + 5, 40, 5))
        # 眼睛
        pygame.draw.circle(surface, BLACK, (cx - 6, self.y + 12), 3)
        pygame.draw.circle(surface, BLACK, (cx + 6, self.y + 12), 3)
        # 鼻子（胡萝卜）
        nose_points = [(cx, self.y + 17),
                       (cx + 12, self.y + 18),
                       (cx, self.y + 19)]
        pygame.draw.polygon(surface, (255, 140, 50), nose_points)
        # 围巾
        pygame.draw.rect(surface, RED, (cx - 14, self.y + 24, 28, 6))
        pygame.draw.rect(surface, RED, (cx + 6, self.y + 24, 8, 14))
        # 手臂（树枝）
        # 左臂
        pygame.draw.line(surface, BROWN, (cx - 20, self.y + 30),
                         (cx - 35, self.y + 20), 3)
        pygame.draw.line(surface, BROWN, (cx - 35, self.y + 20),
                         (cx - 40, self.y + 12), 2)
        # 右臂
        pygame.draw.line(surface, BROWN, (cx + 20, self.y + 30),
                         (cx + 38, self.y + 20), 3)
        pygame.draw.line(surface, BROWN, (cx + 38, self.y + 20),
                         (cx + 42, self.y + 12), 2)

    def can_shoot(self):
        return self.cooldown == 0

    def shoot(self):
        """发射雪球"""
        if self.can_shoot():
            self.cooldown = 15
            cx = self.x + self.width // 2
            return Snowball(cx, self.y - 5, 0, -10, radius=8, color=WHITE)
        return None

    def hit(self):
        """被击中"""
        if self.invincible == 0:
            self.lives -= 1
            self.invincible = 60  # 1秒无敌
            return True
        return False


# ==================== 敌人类 ====================
class Enemy:
    """敌人 - 雪人造型，从上方出现"""

    def __init__(self, level=1):
        self.width = 36
        self.height = 50
        self.x = random.randint(40, WIDTH - 40 - self.width)
        self.y = -self.height
        self.speed = 1 + level * 0.3
        self.direction = random.choice([-1, 1])
        self.move_timer = 0
        self.shoot_timer = random.randint(60, 120)  # 射击间隔
        self.level = level
        self.health = 1
        self.active = True

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, snowballs):
        # 进入屏幕
        if self.y < 30:
            self.y += 2
            return

        # 水平移动
        self.x += self.speed * self.direction
        # 边界反弹
        if self.x <= 10 or self.x >= WIDTH - self.width - 10:
            self.direction *= -1

        # 射击计时
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot_timer = random.randint(60, 180) - self.level * 5
            if self.shoot_timer < 30:
                self.shoot_timer = 30
            cx = self.x + self.width // 2
            # 略微瞄准玩家
            snowballs.append(
                Snowball(cx, self.y + self.height, random.uniform(-1, 1),
                         4 + self.level * 0.3, radius=7, color=GRAY)
            )

    def draw(self, surface):
        cx = self.x + self.width // 2
        # 身体
        pygame.draw.circle(surface, WHITE, (cx, self.y + 32), 18)
        # 头部
        pygame.draw.circle(surface, WHITE, (cx, self.y + 12), 14)
        # 帽子
        hat_color = (180, 50, 50) if self.level > 2 else DARK_BLUE
        pygame.draw.rect(surface, hat_color, (cx - 10, self.y - 2, 20, 14))
        pygame.draw.rect(surface, hat_color, (cx - 16, self.y + 6, 32, 4))
        # 眼睛（红色/黑色）
        eye_color = RED if self.level > 3 else BLACK
        pygame.draw.circle(surface, eye_color, (cx - 4, self.y + 10), 3)
        pygame.draw.circle(surface, eye_color, (cx + 4, self.y + 10), 3)
        # 嘴巴（邪恶微笑）
        pygame.draw.arc(surface, BLACK, (cx - 6, self.y + 12, 12, 8),
                        math.radians(0), math.radians(180), 2)
        # 纽扣
        for i in range(2):
            pygame.draw.circle(surface, BLACK, (cx, self.y + 26 + i * 8), 2)

    def hit(self):
        """被击中"""
        self.health -= 1
        if self.health <= 0:
            self.active = False
            return True
        return False


# ==================== 雪花粒子（背景） ====================
class Snowflake:
    """飘落的雪花装饰"""

    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(-HEIGHT, 0)
        self.size = random.randint(2, 5)
        self.speed = random.uniform(1, 3)
        self.wobble = random.uniform(0, math.pi * 2)
        self.wobble_speed = random.uniform(0.02, 0.05)

    def update(self):
        self.y += self.speed
        self.wobble += self.wobble_speed
        self.x += math.sin(self.wobble) * 0.5
        if self.y > HEIGHT + 10:
            self.y = -10
            self.x = random.randint(0, WIDTH)

    def draw(self, surface):
        alpha = int(150 + 105 * math.sin(self.wobble + self.y * 0.01))
        color = (255, 255, 255, alpha)
        # 由于pygame的draw不支持alpha，用surface代替
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, alpha),
                           (self.size, self.size), self.size)
        surface.blit(s, (int(self.x), int(self.y)))


# ==================== 游戏主类 ====================
class Game:
    def __init__(self):
        self.reset()
        self.snowflakes = [Snowflake() for _ in range(60)]

    def reset(self):
        self.player = Player()
        self.enemies = []
        self.player_snowballs = []
        self.enemy_snowballs = []
        self.score = 0
        self.level = 1
        self.spawn_timer = 0
        self.max_enemies = 3
        self.state = "playing"  # playing, game_over, paused
        self.particles = []  # 击中特效
        self.combo = 0
        self.high_score = self.load_high_score()

    def load_high_score(self):
        try:
            with open("snowball_highscore.txt", "r") as f:
                return int(f.read())
        except:
            return 0

    def save_high_score(self):
        try:
            with open("snowball_highscore.txt", "w") as f:
                f.write(str(self.high_score))
        except:
            pass

    def spawn_enemy(self):
        """生成敌人"""
        if len(self.enemies) < self.max_enemies and self.spawn_timer <= 0:
            self.enemies.append(Enemy(self.level))
            self.spawn_timer = max(30, 90 - self.level * 5)

    def add_particles(self, x, y, color, count=12):
        """添加击中特效"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": 20,
                "color": color,
                "size": random.randint(3, 6)
            })

    def update_particles(self):
        """更新粒子特效"""
        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.2  # 重力
            p["life"] -= 1
            p["size"] *= 0.95
            if p["life"] <= 0:
                self.particles.remove(p)

    def draw_particles(self):
        """绘制粒子特效"""
        for p in self.particles:
            alpha = int(255 * p["life"] / 20)
            color = (*p["color"][:3], alpha)
            size = max(1, int(p["size"]))
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (size, size), size)
            screen.blit(s, (int(p["x"]), int(p["y"])))

    def handle_collisions(self):
        """处理碰撞"""
        player = self.player
        # 玩家雪球 vs 敌人
        for sb in self.player_snowballs[:]:
            if not sb.active:
                continue
            sb_rect = sb.get_rect()
            for enemy in self.enemies[:]:
                if not enemy.active:
                    continue
                if sb_rect.colliderect(enemy.rect):
                    sb.active = False
                    if enemy.hit():
                        self.add_particles(enemy.x + enemy.width // 2,
                                           enemy.y + enemy.height // 2,
                                           (200, 200, 255))
                        self.score += 10 * self.level
                        self.combo += 1
                        if self.combo > 1:
                            self.score += 5 * self.combo  # 连击奖励
                    break

        # 敌人雪球 vs 玩家
        for sb in self.enemy_snowballs[:]:
            if not sb.active:
                continue
            sb_rect = sb.get_rect()
            if sb_rect.colliderect(player.rect):
                sb.active = False
                if player.hit():
                    self.add_particles(player.x + player.width // 2,
                                       player.y + player.height // 2,
                                       (200, 200, 255), count=20)
                    self.combo = 0
                    if player.lives <= 0:
                        self.state = "game_over"
                        if self.score > self.high_score:
                            self.high_score = self.score
                            self.save_high_score()

        # 玩家雪球 vs 敌人雪球（对撞消除）
        for psb in self.player_snowballs[:]:
            if not psb.active:
                continue
            psb_rect = psb.get_rect()
            for esb in self.enemy_snowballs[:]:
                if not esb.active:
                    continue
                if psb_rect.colliderect(esb.get_rect()):
                    psb.active = False
                    esb.active = False
                    self.add_particles(
                        (psb.x + esb.x) // 2, (psb.y + esb.y) // 2,
                        (200, 220, 255), count=8
                    )
                    break

    def update(self, keys):
        if self.state == "game_over":
            if keys[pygame.K_r]:
                self.reset()
            return

        # 更新玩家
        self.player.update(keys)
        if keys[pygame.K_SPACE]:
            sb = self.player.shoot()
            if sb:
                self.player_snowballs.append(sb)

        # 更新雪球
        for sb in self.player_snowballs[:]:
            sb.update()
            if not sb.active:
                self.player_snowballs.remove(sb)
        for sb in self.enemy_snowballs[:]:
            sb.update()
            if not sb.active:
                self.enemy_snowballs.remove(sb)

        # 生成敌人
        self.spawn_timer -= 1
        self.spawn_enemy()

        # 更新敌人
        for enemy in self.enemies[:]:
            enemy.update(self.enemy_snowballs)
            if not enemy.active:
                self.enemies.remove(enemy)

        # 更新敌人雪球（从敌人列表传递的已经处理了）
        # 额外处理敌人雪球
        for sb in self.enemy_snowballs[:]:
            if not sb.active:
                self.enemy_snowballs.remove(sb)

        # 碰撞检测
        self.handle_collisions()

        # 更新背景雪花
        for sf in self.snowflakes:
            sf.update()

        # 更新粒子
        self.update_particles()

        # 升级
        if self.score > 0 and self.score // 50 > self.level - 1:
            self.level = min(10, self.score // 50 + 1)
            self.max_enemies = min(8, 3 + self.level)

    def draw_bg(self):
        """绘制背景"""
        # 渐变天空
        for i in range(HEIGHT):
            r = int(180 + 60 * (1 - i / HEIGHT))
            g = int(200 + 55 * (1 - i / HEIGHT))
            b = int(255)
            pygame.draw.line(screen, (r, g, b), (0, i), (WIDTH, i))

        # 雪地
        snow_rect = pygame.Rect(0, HEIGHT - 40, WIDTH, 40)
        pygame.draw.rect(screen, (240, 248, 255), snow_rect)
        # 雪地起伏
        for x in range(0, WIDTH, 8):
            h = math.sin(x * 0.05) * 5
            pygame.draw.rect(screen, (235, 243, 255),
                             (x, HEIGHT - 40 + h, 8, 5))

        # 背景树木
        for i in range(3):
            tx = 100 + i * 300
            tree_top = HEIGHT - 60
            # 树干
            pygame.draw.rect(screen, BROWN, (tx - 6, tree_top - 20, 12, 30))
            # 树冠（雪覆盖）
            pygame.draw.polygon(screen, (30, 80, 30),
                               [(tx, tree_top - 50),
                                (tx - 25, tree_top - 10),
                                (tx + 25, tree_top - 10)])
            pygame.draw.polygon(screen, (200, 220, 230),
                               [(tx, tree_top - 50),
                                (tx - 25, tree_top - 10),
                                (tx + 25, tree_top - 10)], 4)

        # 背景雪花
        for sf in self.snowflakes:
            sf.draw(screen)

    def draw_hud(self):
        """绘制HUD"""
        # 分数
        draw_text(f"分数: {self.score}", font_small, WHITE, 100, 30, center=False)
        # 等级
        draw_text(f"等级: {self.level}", font_small, WHITE, 100, 60, center=False)
        # 生命值（雪球图标）
        for i in range(self.player.lives):
            pygame.draw.circle(screen, WHITE, (WIDTH - 120 + i * 30, 35), 10)
            pygame.draw.circle(screen, (200, 220, 240),
                               (WIDTH - 120 + i * 30, 35), 10, 2)

        # 连击
        if self.combo > 1:
            combo_color = (255, 255, 100) if self.combo < 5 else (255, 150, 50)
            if self.combo >= 10:
                combo_color = (255, 50, 50)
            draw_text(f"{self.combo}x 连击!", font_small, combo_color,
                      WIDTH // 2, 30)

    def draw_game_over(self):
        """绘制游戏结束界面"""
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 30))
        screen.blit(overlay, (0, 0))

        draw_text("游戏结束", font_large, (255, 100, 100), WIDTH // 2, HEIGHT // 2 - 80)
        draw_text(f"最终得分: {self.score}", font_medium, WHITE,
                  WIDTH // 2, HEIGHT // 2 - 10)
        draw_text(f"最高记录: {self.high_score}", font_medium, YELLOW,
                  WIDTH // 2, HEIGHT // 2 + 40)

        if self.score >= self.high_score and self.score > 0:
            draw_text("★ 新纪录！★", font_medium, (255, 215, 0),
                      WIDTH // 2, HEIGHT // 2 + 90)

        draw_text("按 R 重新开始", font_small, WHITE,
                  WIDTH // 2, HEIGHT // 2 + 150)

    def draw(self):
        self.draw_bg()
        self.draw_particles()

        # 绘制敌人雪球（在敌人下方）
        for sb in self.enemy_snowballs:
            if sb.active:
                sb.draw(screen)

        # 绘制敌人
        for enemy in self.enemies:
            if enemy.active:
                enemy.draw(screen)

        # 绘制玩家雪球
        for sb in self.player_snowballs:
            if sb.active:
                sb.draw(screen)

        # 绘制玩家
        self.player.draw(screen)

        self.draw_hud()

        if self.state == "game_over":
            self.draw_game_over()

    def run(self):
        """游戏主循环"""
        running = True
        while running:
            keys = pygame.key.get_pressed()
            dt = clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            self.update(keys)
            self.draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ==================== 启动游戏 ====================
if __name__ == "__main__":
    game = Game()
    game.run()