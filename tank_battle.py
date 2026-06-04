"""
坦克大战 (Tank Battle) - 经典坦克对战游戏
========================================
控制你的坦克，消灭敌方坦克，保护基地！

操作说明：
  - 方向键 ↑ ↓ ← → 移动坦克
  - 空格键 发射子弹
  - R 键 重新开始游戏

游戏规则：
  - 消灭所有敌方坦克即可过关
  - 保护基地（底部旗帜）不被摧毁
  - 每关有 5 辆敌方坦克
  - 注意躲避敌方子弹！
"""

import pygame
import random
import math

# ==================== 常量定义 ====================
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 650
PLAY_AREA_TOP = 50          # 顶部留白区域
PLAY_AREA_HEIGHT = 600      # 游戏区高度
GRID_SIZE = 30              # 网格大小
GRID_COLS = 20              # 列数 (600/30)
GRID_ROWS = 20              # 行数 (600/30)
FPS = 60

# 颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 50, 50)
GREEN = (0, 255, 0)
BLUE = (50, 50, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
BROWN = (139, 69, 19)
ORANGE = (255, 165, 0)
SKY_BLUE = (100, 149, 237)

# 方向
UP, DOWN, LEFT, RIGHT = 0, 1, 2, 3

# ==================== 游戏对象 ====================

class Brick:
    """砖块 - 可以被子弹摧毁"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
        self.active = True

    def draw(self, screen):
        if not self.active:
            return
        # 绘制砖块纹理
        rect = self.rect
        pygame.draw.rect(screen, BROWN, rect)
        # 砖块纹路
        pygame.draw.line(screen, DARK_GRAY, (rect.x, rect.y + rect.h // 2),
                         (rect.x + rect.w, rect.y + rect.h // 2), 1)
        pygame.draw.line(screen, DARK_GRAY, (rect.x + rect.w // 2, rect.y),
                         (rect.x + rect.w // 2, rect.y + rect.h), 1)
        # 边框
        pygame.draw.rect(screen, DARK_GRAY, rect, 1)


class Steel:
    """钢墙 - 不可摧毁"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
        self.active = True

    def draw(self, screen):
        if not self.active:
            return
        rect = self.rect
        pygame.draw.rect(screen, GRAY, rect)
        # 金属光泽效果
        pygame.draw.rect(screen, WHITE, (rect.x + 3, rect.y + 3, rect.w - 6, rect.h - 6))
        pygame.draw.rect(screen, DARK_GRAY, (rect.x + 5, rect.y + 5, rect.w - 10, rect.h - 10))
        pygame.draw.rect(screen, GRAY, rect, 1)


class Base:
    """基地（旗帜）- 被摧毁则游戏结束"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
        self.active = True

    def draw(self, screen):
        if not self.active:
            # 被摧毁的基地
            rect = self.rect
            pygame.draw.rect(screen, RED, rect)
            pygame.draw.line(screen, BLACK, (rect.x, rect.y),
                             (rect.x + rect.w, rect.y + rect.h), 3)
            pygame.draw.line(screen, BLACK, (rect.x + rect.w, rect.y),
                             (rect.x, rect.y + rect.h), 3)
            return
        rect = self.rect
        cx, cy = rect.centerx, rect.centery
        # 旗杆
        pygame.draw.line(screen, DARK_GRAY, (cx, cy - 10), (cx, cy + 10), 3)
        # 旗帜
        flag_points = [(cx, cy - 10), (cx + 10, cy - 6), (cx, cy - 2)]
        pygame.draw.polygon(screen, GREEN, flag_points)
        # 底座
        pygame.draw.rect(screen, BROWN, (cx - 12, cy + 8, 24, 6))
        # 周围保护
        pygame.draw.rect(screen, DARK_GRAY, rect, 2)


class Bullet:
    """子弹"""
    def __init__(self, x, y, direction, owner="player"):
        self.x = x
        self.y = y
        self.direction = direction
        self.owner = owner
        self.speed = 8
        self.size = 6
        self.active = True
        self.rect = pygame.Rect(x - self.size // 2, y - self.size // 2,
                                self.size, self.size)

    def update(self):
        if not self.active:
            return
        if self.direction == UP:
            self.y -= self.speed
        elif self.direction == DOWN:
            self.y += self.speed
        elif self.direction == LEFT:
            self.x -= self.speed
        elif self.direction == RIGHT:
            self.x += self.speed
        self.rect.center = (self.x, self.y)

        # 边界检测
        if (self.y < PLAY_AREA_TOP or self.y > PLAY_AREA_TOP + PLAY_AREA_HEIGHT
                or self.x < 0 or self.x > SCREEN_WIDTH):
            self.active = False

    def draw(self, screen):
        if not self.active:
            return
        color = YELLOW if self.owner == "player" else RED
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size // 2)
        # 发光效果
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size // 4)


class Tank:
    """坦克基类"""
    def __init__(self, x, y, color, direction=UP):
        self.x = x
        self.y = y
        self.color = color
        self.direction = direction
        self.size = GRID_SIZE - 4
        self.speed = 2
        self.hp = 1
        self.active = True
        self.shoot_cooldown = 0
        self.max_cooldown = 20
        self.rect = pygame.Rect(x, y, self.size, self.size)

    def get_center(self):
        return (self.x + self.size // 2, self.y + self.size // 2)

    def can_shoot(self):
        return self.shoot_cooldown <= 0

    def shoot(self):
        """发射子弹，返回 Bullet 对象"""
        if not self.can_shoot():
            return None
        self.shoot_cooldown = self.max_cooldown
        cx, cy = self.get_center()
        # 根据方向调整子弹起始位置
        offset = self.size // 2 + 5
        if self.direction == UP:
            bullet = Bullet(cx, cy - offset, UP, "player" if self.color == YELLOW else "enemy")
        elif self.direction == DOWN:
            bullet = Bullet(cx, cy + offset, DOWN, "player" if self.color == YELLOW else "enemy")
        elif self.direction == LEFT:
            bullet = Bullet(cx - offset, cy, LEFT, "player" if self.color == YELLOW else "enemy")
        else:
            bullet = Bullet(cx + offset, cy, RIGHT, "player" if self.color == YELLOW else "enemy")
        return bullet

    def update_cooldown(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def draw(self, screen):
        if not self.active:
            return
        # 坦克主体（圆形）
        cx, cy = self.get_center()
        pygame.draw.circle(screen, self.color, (cx, cy), self.size // 2)
        # 炮管
        length = self.size // 2 + 4
        if self.direction == UP:
            end = (cx, cy - length)
        elif self.direction == DOWN:
            end = (cx, cy + length)
        elif self.direction == LEFT:
            end = (cx - length, cy)
        else:
            end = (cx + length, cy)
        pygame.draw.line(screen, WHITE, (cx, cy), end, 5)
        # 炮塔
        pygame.draw.circle(screen, DARK_GRAY, (cx, cy), self.size // 4)
        # 履带装饰
        offset = self.size // 2
        if self.direction in (UP, DOWN):
            pygame.draw.rect(screen, DARK_GRAY,
                             (self.x, self.y + 2, 4, self.size - 4))
            pygame.draw.rect(screen, DARK_GRAY,
                             (self.x + self.size - 4, self.y + 2, 4, self.size - 4))
        else:
            pygame.draw.rect(screen, DARK_GRAY,
                             (self.x + 2, self.y, self.size - 4, 4))
            pygame.draw.rect(screen, DARK_GRAY,
                             (self.x + 2, self.y + self.size - 4, self.size - 4, 4))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)


class PlayerTank(Tank):
    """玩家坦克"""
    def __init__(self, x, y):
        super().__init__(x, y, YELLOW, UP)
        self.speed = 3
        self.max_cooldown = 15
        self.lives = 3

    def move(self, dx, dy, bricks, steel_walls, base, enemy_tanks):
        """移动坦克，处理碰撞"""
        new_x = self.x + dx
        new_y = self.y + dy

        # 边界检测
        if new_x < 0:
            new_x = 0
        if new_x + self.size > SCREEN_WIDTH:
            new_x = SCREEN_WIDTH - self.size
        if new_y < PLAY_AREA_TOP:
            new_y = PLAY_AREA_TOP
        if new_y + self.size > PLAY_AREA_TOP + PLAY_AREA_HEIGHT:
            new_y = PLAY_AREA_TOP + PLAY_AREA_HEIGHT - self.size

        temp_rect = pygame.Rect(new_x, new_y, self.size, self.size)

        # 砖块碰撞
        for brick in bricks:
            if brick.active and temp_rect.colliderect(brick.rect):
                return  # 撞到障碍物，不移动

        # 钢墙碰撞
        for steel in steel_walls:
            if steel.active and temp_rect.colliderect(steel.rect):
                return

        # 基地碰撞
        if base and base.active and temp_rect.colliderect(base.rect):
            return

        # 敌方坦克碰撞
        for enemy in enemy_tanks:
            if enemy.active and temp_rect.colliderect(enemy.get_rect()):
                return

        self.x = new_x
        self.y = new_y
        self.rect = self.get_rect()


class EnemyTank(Tank):
    """敌方坦克"""
    def __init__(self, x, y):
        super().__init__(x, y, RED, DOWN)
        self.speed = 1
        self.max_cooldown = 30
        self.direction_change_timer = 0
        self.direction_change_delay = 60  # 每60帧改变一次方向

    def update_ai(self, bricks, steel_walls, base, player, other_enemies):
        """AI 移动逻辑"""
        if not self.active:
            return

        self.direction_change_timer += 1

        # 定期改变方向或撞墙时改变
        if self.direction_change_timer >= self.direction_change_delay:
            self.direction_change_timer = 0
            self.direction = random.randint(0, 3)

        # 尝试移动
        dx, dy = 0, 0
        if self.direction == UP:
            dy = -self.speed
        elif self.direction == DOWN:
            dy = self.speed
        elif self.direction == LEFT:
            dx = -self.speed
        elif self.direction == RIGHT:
            dx = self.speed

        new_x = self.x + dx
        new_y = self.y + dy

        # 边界检测
        hit_boundary = False
        if new_x < 0 or new_x + self.size > SCREEN_WIDTH:
            hit_boundary = True
        if new_y < PLAY_AREA_TOP or new_y + self.size > PLAY_AREA_TOP + PLAY_AREA_HEIGHT:
            hit_boundary = True

        if hit_boundary:
            self.direction = random.randint(0, 3)
            return

        temp_rect = pygame.Rect(new_x, new_y, self.size, self.size)

        # 砖块碰撞
        for brick in bricks:
            if brick.active and temp_rect.colliderect(brick.rect):
                self.direction = random.randint(0, 3)
                return

        # 钢墙碰撞
        for steel in steel_walls:
            if steel.active and temp_rect.colliderect(steel.rect):
                self.direction = random.randint(0, 3)
                return

        # 基地碰撞
        if base and base.active and temp_rect.colliderect(base.rect):
            self.direction = random.randint(0, 3)
            return

        # 其他敌方坦克碰撞
        for other in other_enemies:
            if other != self and other.active and temp_rect.colliderect(other.get_rect()):
                self.direction = random.randint(0, 3)
                return

        # 玩家坦克碰撞
        if player and player.active and temp_rect.colliderect(player.get_rect()):
            self.direction = random.randint(0, 3)
            return

        self.x = new_x
        self.y = new_y
        self.rect = self.get_rect()

        # 随机射击 - 有一定概率朝玩家方向射击，但主要随机
        if random.random() < 0.02:
            # 朝玩家方向射击的概率
            if player and player.active:
                px, py = player.get_center()
                ex, ey = self.get_center()
                if abs(px - ex) < 100:
                    self.direction = UP if py < ey else DOWN
                elif abs(py - ey) < 100:
                    self.direction = LEFT if px < ex else RIGHT
            self.max_cooldown = 15  # 快速射击


# ==================== 游戏主类 ====================

class TankBattle:
    """坦克大战主游戏"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("坦克大战 Tank Battle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simsun", 22)
        self.big_font = pygame.font.SysFont("simsun", 48)
        self.running = True
        self.game_over = False
        self.victory = False
        self.level = 1
        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        self.bricks = []
        self.steel_walls = []
        self.bullets = []
        self.enemy_tanks = []
        self.player = None
        self.base = None
        self.enemies_spawned = 0
        self.enemies_per_level = 5
        self.enemies_killed = 0
        self.spawn_timer = 0
        self.spawn_delay = 120  # 2秒后生成新敌人
        self.level = 1

        # 生成地图
        self.generate_map()

        # 玩家坦克
        player_x = GRID_COLS // 2 * GRID_SIZE + (GRID_SIZE - 26) // 2
        player_y = PLAY_AREA_TOP + (GRID_ROWS - 2) * GRID_SIZE + (GRID_SIZE - 26) // 2
        self.player = PlayerTank(player_x, player_y)

        # 基地
        base_x = GRID_COLS // 2 * GRID_SIZE + (GRID_SIZE - 30) // 2
        base_y = PLAY_AREA_TOP + (GRID_ROWS - 1) * GRID_SIZE + (GRID_SIZE - 30) // 2
        self.base = Base(base_x, base_y)

    def generate_map(self):
        """生成游戏地图"""
        self.bricks.clear()
        self.steel_walls.clear()

        # 生成砖墙 - 一些对称的砖块布局
        brick_patterns = [
            # 顶部两排砖块
            [(4, 1), (5, 1), (6, 1), (7, 1), (12, 1), (13, 1), (14, 1), (15, 1)],
            [(3, 2), (7, 2), (12, 2), (16, 2)],
            [(3, 3), (4, 3), (5, 3), (6, 3), (7, 3), (12, 3), (13, 3), (14, 3), (15, 3), (16, 3)],
            # 中间障碍
            [(0, 5), (1, 5), (2, 5), (3, 5)],
            [(16, 5), (17, 5), (18, 5), (19, 5)],
            [(0, 8), (1, 8), (2, 8), (3, 8), (4, 8), (5, 8)],
            [(14, 8), (15, 8), (16, 8), (17, 8), (18, 8), (19, 8)],
            [(8, 5), (9, 5), (10, 5), (11, 5)],
            [(8, 8), (9, 8), (10, 8), (11, 8)],
            # 下方障碍
            [(0, 12), (1, 12), (2, 12)],
            [(17, 12), (18, 12), (19, 12)],
            [(6, 12), (7, 12), (8, 12), (11, 12), (12, 12), (13, 12)],
            # 基地周围保护
            [(8, 17), (9, 17), (10, 17), (11, 17)],
            [(8, 18), (9, 18), (10, 18), (11, 18)],
            [(7, 18), (7, 19)],
            [(12, 18), (12, 19)],
        ]

        for pattern in brick_patterns:
            for col, row in pattern:
                x = col * GRID_SIZE + (GRID_SIZE - 30) // 2
                y = PLAY_AREA_TOP + row * GRID_SIZE + (GRID_SIZE - 30) // 2
                self.bricks.append(Brick(x, y))

        # 钢墙 - 某些位置
        steel_positions = [(4, 10), (5, 10), (14, 10), (15, 10)]
        for col, row in steel_positions:
            x = col * GRID_SIZE + (GRID_SIZE - 30) // 2
            y = PLAY_AREA_TOP + row * GRID_SIZE + (GRID_SIZE - 30) // 2
            self.steel_walls.append(Steel(x, y))

    def spawn_enemy(self):
        """生成敌方坦克"""
        if self.enemies_spawned >= self.enemies_per_level:
            return
        if len(self.enemy_tanks) >= 4:  # 最多同时存在4个敌人
            return

        # 在顶部随机位置生成
        spawn_cols = [1, 5, 9, 13, 17]
        random.shuffle(spawn_cols)
        for col in spawn_cols:
            x = col * GRID_SIZE + (GRID_SIZE - 26) // 2
            y = PLAY_AREA_TOP + (GRID_SIZE - 26) // 2
            new_rect = pygame.Rect(x, y, GRID_SIZE - 4, GRID_SIZE - 4)

            # 检查是否与其他物体重叠
            collision = False
            for enemy in self.enemy_tanks:
                if enemy.active and new_rect.colliderect(enemy.get_rect()):
                    collision = True
                    break
            if self.player and self.player.active and new_rect.colliderect(self.player.get_rect()):
                collision = True
            if collision:
                continue

            enemy = EnemyTank(x, y)
            self.enemy_tanks.append(enemy)
            self.enemies_spawned += 1
            break

    def handle_collisions(self):
        """处理所有碰撞"""
        # 子弹 vs 砖块
        for bullet in self.bullets[:]:
            if not bullet.active:
                continue
            if bullet.owner == "player":
                # 玩家子弹 vs 敌方坦克
                for enemy in self.enemy_tanks[:]:
                    if enemy.active and bullet.rect.colliderect(enemy.get_rect()):
                        bullet.active = False
                        enemy.active = False
                        self.enemies_killed += 1
                        break

            # 所有子弹 vs 砖块
            for brick in self.bricks[:]:
                if brick.active and bullet.rect.colliderect(brick.rect):
                    bullet.active = False
                    brick.active = False
                    break

            # 所有子弹 vs 钢墙
            for steel in self.steel_walls:
                if steel.active and bullet.rect.colliderect(steel.rect):
                    bullet.active = False
                    break

            # 所有子弹 vs 基地
            if self.base and self.base.active and bullet.rect.colliderect(self.base.rect):
                bullet.active = False
                self.base.active = False
                self.game_over = True

            # 敌方子弹 vs 玩家
            if bullet.owner == "enemy" and self.player and self.player.active:
                if bullet.rect.colliderect(self.player.get_rect()):
                    bullet.active = False
                    self.player.active = False
                    self.player.lives -= 1
                    if self.player.lives <= 0:
                        self.game_over = True
                    else:
                        # 重生玩家
                        player_x = GRID_COLS // 2 * GRID_SIZE + (GRID_SIZE - 26) // 2
                        player_y = PLAY_AREA_TOP + (GRID_ROWS - 2) * GRID_SIZE + (GRID_SIZE - 26) // 2
                        self.player = PlayerTank(player_x, player_y)

            # 敌方子弹 vs 玩家子弹（互相对消）
            if bullet.owner == "enemy":
                for other_bullet in self.bullets:
                    if other_bullet.owner == "player" and other_bullet.active:
                        if bullet.rect.colliderect(other_bullet.rect):
                            bullet.active = False
                            other_bullet.active = False
                            break

        # 移除无效子弹
        self.bullets = [b for b in self.bullets if b.active]

        # 移除无效敌人
        self.enemy_tanks = [e for e in self.enemy_tanks if e.active]

    def check_victory(self):
        """检查是否过关"""
        if self.enemies_killed >= self.enemies_per_level:
            self.victory = True
            return True
        return False

    def handle_events(self):
        """处理输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    if self.game_over or self.victory:
                        self.__init__()
                        return
                if event.key == pygame.K_SPACE:
                    if self.player and self.player.active and self.player.can_shoot():
                        bullet = self.player.shoot()
                        if bullet:
                            self.bullets.append(bullet)

    def update(self):
        """更新游戏状态"""
        if self.game_over or self.victory:
            return

        # 玩家移动
        keys = pygame.key.get_pressed()
        if self.player and self.player.active:
            dx, dy = 0, 0
            if keys[pygame.K_UP]:
                self.player.direction = UP
                dy = -self.player.speed
            elif keys[pygame.K_DOWN]:
                self.player.direction = DOWN
                dy = self.player.speed
            elif keys[pygame.K_LEFT]:
                self.player.direction = LEFT
                dx = -self.player.speed
            elif keys[pygame.K_RIGHT]:
                self.player.direction = RIGHT
                dx = self.player.speed
            if dx != 0 or dy != 0:
                self.player.move(dx, dy, self.bricks, self.steel_walls,
                                 self.base, self.enemy_tanks)
            self.player.update_cooldown()

        # 敌方 AI
        for enemy in self.enemy_tanks:
            if enemy.active:
                enemy.update_ai(self.bricks, self.steel_walls, self.base,
                                self.player,
                                [e for e in self.enemy_tanks if e != enemy])
                enemy.update_cooldown()
                # 敌方射击
                if enemy.can_shoot() and random.random() < 0.03:
                    bullet = enemy.shoot()
                    if bullet:
                        self.bullets.append(bullet)

        # 生成敌人
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_delay:
            self.spawn_timer = 0
            self.spawn_enemy()

        # 更新子弹
        for bullet in self.bullets:
            bullet.update()

        # 碰撞处理
        self.handle_collisions()

        # 检查胜利
        self.check_victory()

    def draw_info_bar(self):
        """绘制顶部信息栏"""
        # 背景
        pygame.draw.rect(self.screen, DARK_GRAY, (0, 0, SCREEN_WIDTH, PLAY_AREA_TOP))
        pygame.draw.line(self.screen, GRAY, (0, PLAY_AREA_TOP),
                         (SCREEN_WIDTH, PLAY_AREA_TOP), 2)

        # 生命数
        lives_text = f"生命: {self.player.lives if self.player else 0}"
        lives_surf = self.font.render(lives_text, True, WHITE)
        self.screen.blit(lives_surf, (10, 12))

        # 关卡
        level_text = f"第 {self.level} 关"
        level_surf = self.font.render(level_text, True, WHITE)
        level_surf_rect = level_surf.get_rect(center=(SCREEN_WIDTH // 2, 25))
        self.screen.blit(level_surf, level_surf_rect)

        # 敌人数
        enemy_text = f"敌人: {self.enemies_killed}/{self.enemies_per_level}"
        enemy_surf = self.font.render(enemy_text, True, WHITE)
        enemy_surf_rect = enemy_surf.get_rect(right=SCREEN_WIDTH - 10, centery=25)
        self.screen.blit(enemy_surf, enemy_surf_rect)

    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(BLACK)

        # 绘制游戏区域背景
        pygame.draw.rect(self.screen, (30, 30, 30),
                         (0, PLAY_AREA_TOP, SCREEN_WIDTH, PLAY_AREA_HEIGHT))

        # 绘制网格（淡灰色，辅助视觉）
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = col * GRID_SIZE
                y = PLAY_AREA_TOP + row * GRID_SIZE
                if (row + col) % 2 == 0:
                    color = (40, 40, 40)
                else:
                    color = (35, 35, 35)
                pygame.draw.rect(self.screen, color, (x, y, GRID_SIZE, GRID_SIZE))

        # 绘制砖块
        for brick in self.bricks:
            brick.draw(self.screen)

        # 绘制钢墙
        for steel in self.steel_walls:
            steel.draw(self.screen)

        # 绘制基地
        if self.base:
            self.base.draw(self.screen)

        # 绘制玩家坦克
        if self.player:
            self.player.draw(self.screen)

        # 绘制敌方坦克
        for enemy in self.enemy_tanks:
            enemy.draw(self.screen)

        # 绘制子弹
        for bullet in self.bullets:
            bullet.draw(self.screen)

        # 绘制信息栏
        self.draw_info_bar()

        # 绘制游戏结束/胜利画面
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            game_over_text = self.big_font.render("游戏结束", True, RED)
            go_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
            self.screen.blit(game_over_text, go_rect)

            restart_text = self.font.render("按 R 键重新开始", True, WHITE)
            rt_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            self.screen.blit(restart_text, rt_rect)

        elif self.victory:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            victory_text = self.big_font.render("胜利！", True, GREEN)
            vt_rect = victory_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
            self.screen.blit(victory_text, vt_rect)

            restart_text = self.font.render("按 R 键重新开始", True, WHITE)
            rt_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            self.screen.blit(restart_text, rt_rect)

        pygame.display.flip()

    def run(self):
        """游戏主循环"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()


# ==================== 程序入口 ====================
if __name__ == "__main__":
    game = TankBattle()
    game.run()