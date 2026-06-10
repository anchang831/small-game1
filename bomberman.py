"""
炸弹人 (Bomberman) - 经典炸弹人游戏
使用 Pygame 实现，单文件运行，无外部依赖

操作说明：
  ↑↓←→ 移动角色
  空格键 放置炸弹
  R 键 重新开始

游戏规则：
  - 在网格地图上放置炸弹，炸毁软砖墙
  - 收集道具增强能力
  - 消灭所有敌人即可过关
  - 被炸弹波及或碰到敌人则游戏结束
"""

import pygame
import random
import sys
import math

# ===================== 常量定义 =====================
TILE_SIZE = 40          # 每个格子的像素大小
COLS = 15               # 地图列数
ROWS = 13               # 地图行数
SCREEN_WIDTH = COLS * TILE_SIZE
SCREEN_HEIGHT = ROWS * TILE_SIZE
FPS = 60

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (60, 60, 60)
BROWN = (139, 69, 19)
LIGHT_BROWN = (205, 133, 63)
YELLOW = (255, 255, 0)
RED = (255, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 100, 255)
ORANGE = (255, 165, 0)
PINK = (255, 100, 200)
DARK_GREEN = (0, 120, 0)

# 地图元素
EMPTY = 0
HARD_WALL = 1          # 不可破坏的墙
SOFT_WALL = 2          # 可破坏的砖墙
PLAYER = 3
ENEMY = 4
BOMB_OBJ = 5

# 游戏状态
PLAYING = 0
WIN = 1
LOSE = 2


# ===================== 游戏类 =====================
class Bomberman:
    """炸弹人游戏主类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("炸弹人 Bomberman")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("simhei", 48, bold=True)
        self.font_mid = pygame.font.SysFont("simhei", 28, bold=True)
        self.font_small = pygame.font.SysFont("simhei", 18)
        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        self.state = PLAYING
        self.map_data = self._generate_map()

        # 玩家属性
        self.player_pos = [1, 1]  # [col, row]
        self.player_pixel_pos = [1 * TILE_SIZE + TILE_SIZE // 2,
                                 1 * TILE_SIZE + TILE_SIZE // 2]
        self.player_move_target = None  # 平滑移动目标
        self.bomb_power = 1      # 炸弹威力（格数）
        self.max_bombs = 1       # 最大炸弹数
        self.speed_mult = 1      # 速度倍率
        self.alive = True

        # 炸弹和爆炸
        self.bombs = []           # [col, row, timer, power]
        self.explosions = []      # 当前爆炸效果 [(col, row), timer]
        self.explosion_set = set()  # 当前帧防重复

        # 敌人
        self.enemies = []
        self._spawn_enemies(3)

        self.invincible_timer = 0
        self.move_timer = 0
        self.frame_count = 0

    def _generate_map(self):
        """生成地图: 外围硬墙 + 内部软墙/空地"""
        grid = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]

        # 外围硬墙
        for r in range(ROWS):
            for c in range(COLS):
                if r == 0 or r == ROWS - 1 or c == 0 or c == COLS - 1:
                    grid[r][c] = HARD_WALL

        # 内部固定硬墙 (棋盘格模式)
        for r in range(2, ROWS - 1, 2):
            for c in range(2, COLS - 1, 2):
                grid[r][c] = HARD_WALL

        # 软墙（随机放置）- 确保玩家起始区域(1,1)、(1,2)、(2,1)为空
        safe_cells = {(1, 1), (1, 2), (2, 1), (1, 0), (0, 1)}
        # 也留一些敌人出生点
        enemy_spawns = {(ROWS - 2, COLS - 2), (ROWS - 3, COLS - 2), (ROWS - 2, COLS - 3)}
        safe_cells.update(enemy_spawns)

        for r in range(1, ROWS - 1):
            for c in range(1, COLS - 1):
                if grid[r][c] == HARD_WALL:
                    continue
                if (c, r) in safe_cells:
                    continue
                if random.random() < 0.55:  # 55%概率放软墙
                    grid[r][c] = SOFT_WALL

        return grid

    def _spawn_enemies(self, count):
        """生成敌人"""
        spawn_positions = [
            (COLS - 3, ROWS - 3),
            (COLS - 2, 2),
            (2, ROWS - 3),
            (COLS - 4, ROWS - 4),
            (4, ROWS - 4),
        ]
        random.shuffle(spawn_positions)
        spawned = 0
        for c, r in spawn_positions:
            if spawned >= count:
                break
            if self.map_data[r][c] == EMPTY:
                self.enemies.append({
                    'col': c, 'row': r,
                    'pixel_x': c * TILE_SIZE + TILE_SIZE // 2,
                    'pixel_y': r * TILE_SIZE + TILE_SIZE // 2,
                    'dir': random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)]),
                    'move_timer': 0,
                    'alive': True
                })
                spawned += 1

    def _is_walkable(self, col, row):
        """判断格子是否可行走"""
        if col < 0 or col >= COLS or row < 0 or row >= ROWS:
            return False
        cell = self.map_data[row][col]
        if cell == HARD_WALL or cell == SOFT_WALL:
            return False
        # 检查是否有炸弹
        for b in self.bombs:
            if b[0] == col and b[1] == row:
                return False
        return True

    def _can_place_bomb(self):
        """检查是否可以在当前位置放炸弹"""
        if not self.alive:
            return False
        c = round(self.player_pos[0])
        r = round(self.player_pos[1])
        # 检查已有炸弹数
        active_count = sum(1 for b in self.bombs if b[4])  # active flag
        if active_count >= self.max_bombs:
            return False
        # 检查当前位置是否已有炸弹
        for b in self.bombs:
            if b[0] == c and b[1] == r:
                return False
        return True

    def place_bomb(self):
        """放置炸弹"""
        if not self._can_place_bomb():
            return
        c = round(self.player_pos[0])
        r = round(self.player_pos[1])
        self.bombs.append([c, r, 120, self.bomb_power, True])  # 2秒爆炸 (120帧)
        # 音效替代: 闪烁效果

    def _explode_bomb(self, bomb):
        """炸弹爆炸，计算波及范围"""
        c, r, _, power, _ = bomb
        self.explosions.append((c, r, 15))  # 爆炸中心，15帧显示
        self.explosion_set.add((c, r))

        # 四个方向扩散
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        for dx, dy in directions:
            for i in range(1, power + 1):
                nc, nr = c + dx * i, r + dy * i
                if nc < 0 or nc >= COLS or nr < 0 or nr >= ROWS:
                    break
                cell = self.map_data[nr][nc]
                if cell == HARD_WALL:
                    break
                if cell == SOFT_WALL:
                    self.map_data[nr][nc] = EMPTY
                    # 随机掉落道具
                    if random.random() < 0.20:
                        self._spawn_powerup(nc, nr)
                    self.explosions.append((nc, nr, 15))
                    self.explosion_set.add((nc, nr))
                    break
                self.explosions.append((nc, nr, 15))
                self.explosion_set.add((nc, nr))

        # 检查玩家是否在爆炸范围内
        pc = round(self.player_pos[0])
        pr = round(self.player_pos[1])
        if (pc, pr) in self.explosion_set and self.alive:
            self.alive = False
            self.state = LOSE

        # 检查敌人
        for enemy in self.enemies:
            if not enemy['alive']:
                continue
            ec, er = enemy['col'], enemy['row']
            if (ec, er) in self.explosion_set:
                enemy['alive'] = False

        # 连锁反应：检查是否有其他炸弹被引爆
        chain_bombs = []
        for other in self.bombs:
            if other is bomb or not other[4]:
                continue
            oc, or_ = other[0], other[1]
            if (oc, or_) in self.explosion_set:
                other[4] = False
                chain_bombs.append(other)

        for cb in chain_bombs:
            self._explode_bomb(cb)

    def _spawn_powerup(self, col, row):
        """在地图位置生成道具"""
        # 随机选择一个道具类型
        types = ['bomb', 'power', 'speed']
        weights = [0.35, 0.35, 0.30]
        t = random.choices(types, weights=weights, k=1)[0]
        # 用负数表示道具：-1 炸弹数+1, -2 威力+1, -3 速度+
        if t == 'bomb':
            self.map_data[row][col] = -1
        elif t == 'power':
            self.map_data[row][col] = -2
        else:
            self.map_data[row][col] = -3

    def _check_powerup(self, col, row):
        """检查并拾取道具"""
        cell = self.map_data[row][col]
        if cell == -1:
            self.max_bombs += 1
            self.map_data[row][col] = EMPTY
        elif cell == -2:
            self.bomb_power += 1
            self.map_data[row][col] = EMPTY
        elif cell == -3:
            self.speed_mult = min(3, self.speed_mult + 1)
            self.map_data[row][col] = EMPTY

    def move_player(self, dx, dy):
        """移动玩家"""
        if not self.alive or self.player_move_target:
            return

        # 获取当前所在格子中心
        cur_c, cur_r = self.player_pos[0], self.player_pos[1]
        new_c = round(cur_c + dx)
        new_r = round(cur_r + dy)

        if self._is_walkable(new_c, new_r):
            self.player_move_target = (new_c, new_r)
            self.player_pos = [new_c, new_r]
            self._check_powerup(new_c, new_r)

    def update_player_smooth(self):
        """平滑移动玩家像素位置"""
        if not self.player_move_target:
            return

        target_c, target_r = self.player_move_target
        target_x = target_c * TILE_SIZE + TILE_SIZE // 2
        target_y = target_r * TILE_SIZE + TILE_SIZE // 2

        px, py = self.player_pixel_pos
        speed = 4.0 * self.speed_mult
        dx = target_x - px
        dy = target_y - py
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < speed:
            self.player_pixel_pos = [target_x, target_y]
            self.player_move_target = None
        else:
            self.player_pixel_pos[0] += (dx / dist) * speed
            self.player_pixel_pos[1] += (dy / dist) * speed

    def update_enemies(self):
        """更新敌人AI"""
        for enemy in self.enemies:
            if not enemy['alive']:
                continue

            enemy['move_timer'] -= 1
            if enemy['move_timer'] > 0:
                continue

            # 每15-25帧移动一次
            enemy['move_timer'] = random.randint(15, 25)

            # 随机改变方向
            if random.random() < 0.25:
                enemy['dir'] = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])

            dx, dy = enemy['dir']
            nc = enemy['col'] + dx
            nr = enemy['row'] + dy

            # 如果下一步不可走，换方向
            if not self._is_walkable(nc, nr):
                enemy['dir'] = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
                dx, dy = enemy['dir']
                nc = enemy['col'] + dx
                nr = enemy['row'] + dy
                if not self._is_walkable(nc, nr):
                    continue

            enemy['col'] = nc
            enemy['row'] = nr
            enemy['pixel_x'] = nc * TILE_SIZE + TILE_SIZE // 2
            enemy['pixel_y'] = nr * TILE_SIZE + TILE_SIZE // 2

            # 碰撞检测：碰到玩家
            pc = round(self.player_pos[0])
            pr = round(self.player_pos[1])
            if nc == pc and nr == pr and self.alive:
                self.alive = False
                self.state = LOSE

    def check_win(self):
        """检查是否过关"""
        alive_enemies = sum(1 for e in self.enemies if e['alive'])
        if alive_enemies == 0:
            self.state = WIN

    def update(self):
        """主更新循环"""
        if self.state != PLAYING:
            return

        self.frame_count += 1
        self.update_player_smooth()

        # 更新炸弹计时器
        for bomb in self.bombs[:]:
            if not bomb[4]:
                continue
            bomb[2] -= 1
            if bomb[2] <= 0:
                bomb[4] = False
                self._explode_bomb(bomb)

        # 清理已爆炸的炸弹
        self.bombs = [b for b in self.bombs if b[4]]

        # 更新爆炸动画
        self.explosions = [(c, r, t - 1) for c, r, t in self.explosions if t > 1]
        self.explosion_set.clear()

        self.update_enemies()
        self.check_win()

    # ===================== 绘制部分 =====================
    def draw_map(self):
        """绘制地图"""
        for r in range(ROWS):
            for c in range(COLS):
                cell = self.map_data[r][c]
                rect = (c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)

                if cell == HARD_WALL:
                    # 硬墙：深灰色石砖纹理
                    pygame.draw.rect(self.screen, DARK_GRAY, rect)
                    # 砖纹
                    pygame.draw.rect(self.screen, (80, 80, 80),
                                     (c * TILE_SIZE + 2, r * TILE_SIZE + 2,
                                      TILE_SIZE // 2 - 2, TILE_SIZE // 2 - 2))
                    pygame.draw.rect(self.screen, (80, 80, 80),
                                     (c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + 2,
                                      TILE_SIZE // 2 - 2, TILE_SIZE // 2 - 2))
                    pygame.draw.rect(self.screen, (80, 80, 80),
                                     (c * TILE_SIZE + 2, r * TILE_SIZE + TILE_SIZE // 2,
                                      TILE_SIZE // 2 - 2, TILE_SIZE // 2 - 2))
                    pygame.draw.rect(self.screen, (80, 80, 80),
                                     (c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE // 2,
                                      TILE_SIZE // 2 - 2, TILE_SIZE // 2 - 2))
                elif cell == SOFT_WALL:
                    # 软砖墙：棕色砖块
                    pygame.draw.rect(self.screen, BROWN, rect)
                    pygame.draw.rect(self.screen, LIGHT_BROWN,
                                     (c * TILE_SIZE + 1, r * TILE_SIZE + 1,
                                      TILE_SIZE - 2, TILE_SIZE - 2), 1)
                    # 砖纹十字
                    pygame.draw.line(self.screen, LIGHT_BROWN,
                                     (c * TILE_SIZE, r * TILE_SIZE + TILE_SIZE // 2),
                                     (c * TILE_SIZE + TILE_SIZE, r * TILE_SIZE + TILE_SIZE // 2), 1)
                    pygame.draw.line(self.screen, LIGHT_BROWN,
                                     (c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE),
                                     (c * TILE_SIZE + TILE_SIZE // 2, r * TILE_SIZE + TILE_SIZE), 1)
                elif cell == EMPTY:
                    # 空地：浅色地板
                    color = (50, 180, 50) if (c + r) % 2 == 0 else (60, 190, 60)
                    pygame.draw.rect(self.screen, color, rect)
                elif cell < 0:
                    # 道具 - 先画空地再画道具
                    color = (50, 180, 50) if (c + r) % 2 == 0 else (60, 190, 60)
                    pygame.draw.rect(self.screen, color, rect)
                    # 画道具图标
                    cx = c * TILE_SIZE + TILE_SIZE // 2
                    cy = r * TILE_SIZE + TILE_SIZE // 2
                    if cell == -1:  # 炸弹+
                        pygame.draw.circle(self.screen, YELLOW, (cx, cy), 10)
                        pygame.draw.circle(self.screen, BLACK, (cx, cy), 10, 2)
                        self._draw_text(self.screen, "B", cx, cy, BLACK, 16)
                    elif cell == -2:  # 威力+
                        pygame.draw.circle(self.screen, ORANGE, (cx, cy), 10)
                        pygame.draw.circle(self.screen, BLACK, (cx, cy), 10, 2)
                        self._draw_text(self.screen, "P", cx, cy, BLACK, 16)
                    elif cell == -3:  # 速度+
                        pygame.draw.circle(self.screen, GREEN, (cx, cy), 10)
                        pygame.draw.circle(self.screen, BLACK, (cx, cy), 10, 2)
                        self._draw_text(self.screen, "S", cx, cy, BLACK, 16)

    def draw_bombs(self):
        """绘制炸弹"""
        for c, r, timer, _, active in self.bombs:
            if not active:
                continue
            cx = c * TILE_SIZE + TILE_SIZE // 2
            cy = r * TILE_SIZE + TILE_SIZE // 2
            # 炸弹闪烁
            flash = (timer // 5) % 2 == 0
            color = RED if flash else (200, 0, 0)
            pygame.draw.circle(self.screen, BLACK, (cx + 1, cy + 1), 14)
            pygame.draw.circle(self.screen, color, (cx, cy), 13)
            pygame.draw.circle(self.screen, (100, 0, 0), (cx, cy), 13, 2)
            # 引信
            fx = cx + 8 + int(5 * math.sin(timer * 0.2))
            fy = cy - 10 + int(3 * math.cos(timer * 0.3))
            pygame.draw.line(self.screen, (150, 100, 50), (cx + 6, cy - 8), (fx, fy), 2)
            # 火花
            spark = (timer // 3) % 2 == 0
            if spark:
                pygame.draw.circle(self.screen, YELLOW, (fx, fy), 3)
                pygame.draw.circle(self.screen, ORANGE, (fx, fy), 2)

    def draw_explosions(self):
        """绘制爆炸效果"""
        for c, r, timer in self.explosions:
            cx = c * TILE_SIZE + TILE_SIZE // 2
            cy = r * TILE_SIZE + TILE_SIZE // 2
            progress = 1.0 - timer / 15.0
            radius = int(16 + 4 * math.sin(progress * math.pi))
            # 爆炸颜色从白到红到橙
            colors = [(255, 255, 200), (255, 200, 50), (255, 100, 0), (200, 50, 0)]
            idx = min(3, int(progress * 4))
            color = colors[idx]
            pygame.draw.circle(self.screen, color, (cx, cy), radius)
            pygame.draw.circle(self.screen, (255, 255, 200), (cx, cy), radius // 2)
            # 爆炸十字线
            for dx, dy in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]:
                ex = cx + dx * radius
                ey = cy + dy * radius
                if dx == 0 and dy == 0:
                    continue
                pygame.draw.line(self.screen, YELLOW, (cx, cy), (ex, ey), 3)

    def draw_player(self):
        """绘制玩家"""
        if not self.alive:
            return
        px, py = self.player_pixel_pos
        size = 24

        # 身体
        pygame.draw.rect(self.screen, BLUE,
                         (px - size // 2, py - size // 2, size, size),
                         border_radius=4)

        # 头带（红色）
        pygame.draw.rect(self.screen, RED,
                         (px - size // 2, py - size // 2, size, 6),
                         border_radius=2)

        # 眼睛
        eye_color = WHITE
        pygame.draw.circle(self.screen, eye_color, (px - 5, py - 4), 4)
        pygame.draw.circle(self.screen, eye_color, (px + 5, py - 4), 4)
        pygame.draw.circle(self.screen, BLACK, (px - 5, py - 4), 2)
        pygame.draw.circle(self.screen, BLACK, (px + 5, py - 4), 2)

        # 嘴巴（微笑）
        pygame.draw.arc(self.screen, BLACK,
                        (px - 6, py + 1, 12, 8), 0, math.pi, 2)

        # 身体上的"B"标志
        self._draw_text(self.screen, "B", px, py + 3, WHITE, 12, bold=True)

    def draw_enemies(self):
        """绘制敌人"""
        for enemy in self.enemies:
            if not enemy['alive']:
                continue
            ex, ey = enemy['pixel_x'], enemy['pixel_y']
            size = 22

            # 身体（红色怪物）
            pygame.draw.rect(self.screen, RED,
                             (ex - size // 2, ey - size // 2, size, size),
                             border_radius=6)
            # 头部毛刺
            for i in range(-1, 2):
                pygame.draw.polygon(self.screen, RED, [
                    (ex + i * 8 - 3, ey - size // 2),
                    (ex + i * 8, ey - size // 2 - 6),
                    (ex + i * 8 + 3, ey - size // 2)
                ])

            # 白色眼睛
            pygame.draw.circle(self.screen, WHITE, (ex - 5, ey - 4), 5)
            pygame.draw.circle(self.screen, WHITE, (ex + 5, ey - 4), 5)
            # 黑色瞳孔（朝玩家方向）
            pc = round(self.player_pos[0])
            pr = round(self.player_pos[1])
            dx = 1 if pc > enemy['col'] else -1 if pc < enemy['col'] else 0
            dy = 1 if pr > enemy['row'] else -1 if pr < enemy['row'] else 0
            pygame.draw.circle(self.screen, BLACK, (ex - 5 + dx * 2, ey - 4 + dy * 2), 2)
            pygame.draw.circle(self.screen, BLACK, (ex + 5 + dx * 2, ey - 4 + dy * 2), 2)

            # 嘴巴
            pygame.draw.arc(self.screen, BLACK,
                            (ex - 5, ey + 1, 10, 6), 0, math.pi, 2)

    def draw_hud(self):
        """绘制HUD信息"""
        # HUD背景
        pygame.draw.rect(self.screen, (0, 0, 0, 180),
                         (0, 0, SCREEN_WIDTH, 36))
        pygame.draw.rect(self.screen, (60, 60, 60),
                         (0, 0, SCREEN_WIDTH, 36))
        s = pygame.Surface((SCREEN_WIDTH, 36), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        self.screen.blit(s, (0, 0))

        # 显示道具信息
        info = f"炸弹: {sum(1 for b in self.bombs if b[4])}/{self.max_bombs}  |  威力: {self.bomb_power}  |  速度: {self.speed_mult}"
        self._draw_text(self.screen, info, 10, 18, WHITE, 18)

        # 显示剩余敌人
        alive = sum(1 for e in self.enemies if e['alive'])
        self._draw_text(self.screen, f"敌人: {alive}", SCREEN_WIDTH - 100, 18, WHITE, 18)

    def draw_overlay(self):
        """绘制结束画面"""
        if self.state == PLAYING:
            return

        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.set_alpha(160)
        s.fill((0, 0, 0))
        self.screen.blit(s, (0, 0))

        if self.state == WIN:
            text = "恭喜过关！"
            sub = "按 R 键重新开始"
            color = YELLOW
        else:
            text = "游戏结束！"
            sub = "按 R 键重新开始"
            color = RED

        self._draw_text(self.screen, text, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40,
                        color, 52)
        self._draw_text(self.screen, sub, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20,
                        WHITE, 26)

    def _draw_text(self, surface, text, x, y, color, size=24, bold=False):
        """通用文本绘制（支持居中或左对齐）"""
        font = pygame.font.SysFont("simhei", size, bold=bold)
        if isinstance(x, float):
            x = int(x)
        if isinstance(y, float):
            y = int(y)
        # 如果x=0表示左对齐
        if x == 0:
            img = font.render(text, True, color)
            surface.blit(img, (5, y - img.get_height() // 2))
        else:
            img = font.render(text, True, color)
            rect = img.get_rect(center=(x, y))
            surface.blit(img, rect)

    def draw(self):
        """主绘制方法"""
        self.screen.fill(BLACK)
        self.draw_map()
        self.draw_bombs()
        self.draw_explosions()
        self.draw_enemies()
        self.draw_player()
        self.draw_hud()
        self.draw_overlay()
        pygame.display.flip()

    def handle_events(self):
        """处理输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.state != PLAYING:
                    self.reset_game()
                if event.key == pygame.K_SPACE and self.state == PLAYING:
                    self.place_bomb()

        # 持续按键移动
        if self.state == PLAYING and self.alive:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -1
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = 1
            elif keys[pygame.K_UP] or keys[pygame.K_w]:
                dy = -1
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy = 1

            if dx != 0 or dy != 0:
                self.move_player(dx, dy)

        return True

    def run(self):
        """游戏主循环"""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ===================== 程序入口 =====================
if __name__ == "__main__":
    game = Bomberman()
    game.run()