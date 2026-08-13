"""
Paper.io 纸片大作战
==================
一个经典的领土争夺游戏，玩家通过移动画圈来占领地盘，
同时要躲避敌人的追击。
- 方向键/WASD 控制移动
- 空格键重新开始
- 占领最大领土者获胜

Author: AI Game Developer
Date: 2026-08-13
"""

import pygame
import random
import math
import sys

# ======================== 配置 ========================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 20  # 网格大小
COLS = SCREEN_WIDTH // GRID_SIZE
ROWS = SCREEN_HEIGHT // GRID_SIZE
FPS = 60

# 颜色
COLORS = {
    'bg': (30, 30, 40),
    'grid': (50, 50, 60),
    'border': (200, 200, 200),
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'red': (255, 60, 60),
    'blue': (60, 120, 255),
    'green': (60, 200, 60),
    'yellow': (255, 220, 40),
    'orange': (255, 140, 40),
    'purple': (200, 60, 255),
    'cyan': (40, 220, 255),
    'pink': (255, 80, 180),
    'gray': (100, 100, 100),
    'dark_gray': (60, 60, 70),
}

PLAYER_COLORS = [
    ('red', 'blue', 'green', 'yellow', 'orange', 'purple', 'cyan', 'pink'),
    (COLORS['red'], COLORS['blue'], COLORS['green'], COLORS['yellow'],
     COLORS['orange'], COLORS['purple'], COLORS['cyan'], COLORS['pink']),
]

# 玩家初始配置
PLAYER_CONFIG = [
    {'name': '玩家', 'start': (5, 5), 'color_idx': 0},
    {'name': 'Bot-1', 'start': (COLS - 6, 5), 'color_idx': 1},
    {'name': 'Bot-2', 'start': (5, ROWS - 6), 'color_idx': 2},
    {'name': 'Bot-3', 'start': (COLS - 6, ROWS - 6), 'color_idx': 3},
]


# ======================== 工具函数 ========================
def get_neighbors(x, y):
    """获取网格的四个邻居"""
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < COLS and 0 <= ny < ROWS:
            yield nx, ny


def flood_fill(grid, start_x, start_y, target_id, fill_id):
    """洪水填充算法：将 grid 中所有连通的 target_id 格子填充为 fill_id"""
    if grid[start_y][start_x] != target_id:
        return False
    stack = [(start_x, start_y)]
    filled = []
    while stack:
        x, y = stack.pop()
        if 0 <= x < COLS and 0 <= y < ROWS and grid[y][x] == target_id:
            grid[y][x] = fill_id
            filled.append((x, y))
            for nx, ny in get_neighbors(x, y):
                if grid[ny][nx] == target_id:
                    stack.append((nx, ny))
    return True


def is_enclosed(grid, trail, territory_id):
    """检查 trail 是否形成一个封闭区域（简单的边界检测）"""
    if len(trail) < 4:
        return False

    # 用 BFS 检查 trail 外部是否与边界相连
    visited = set()
    for ty in range(ROWS):
        for tx in range(COLS):
            if grid[ty][tx] != territory_id and (tx, ty) not in trail:
                # 从非领土、非 trail 的格子开始 BFS
                queue = [(tx, ty)]
                local_visited = set()
                touches_border = False
                while queue and not touches_border:
                    cx, cy = queue.pop(0)
                    if (cx, cy) in visited or (cx, cy) in trail:
                        continue
                    if grid[cy][cx] == territory_id:
                        continue
                    visited.add((cx, cy))
                    local_visited.add((cx, cy))
                    if cx == 0 or cx == COLS - 1 or cy == 0 or cy == ROWS - 1:
                        touches_border = True
                        break
                    for nx, ny in get_neighbors(cx, cy):
                        if (nx, ny) not in visited and (nx, ny) not in trail and grid[ny][nx] != territory_id:
                            queue.append((nx, ny))
                if not touches_border:
                    return True
    return False


# ======================== 玩家类 ========================
class Player:
    """玩家 / AI 基类"""

    def __init__(self, game, config):
        self.game = game
        self.name = config['name']
        self.start_x, self.start_y = config['start']
        self.color_idx = config['color_idx']
        self.color_name = PLAYER_COLORS[0][self.color_idx]
        self.color = PLAYER_COLORS[1][self.color_idx]
        self.light_color = self._lighten(self.color, 40)
        self.dark_color = self._lighten(self.color, -60)

        # 位置（网格坐标）
        self.grid_x = self.start_x * GRID_SIZE + GRID_SIZE // 2
        self.grid_y = self.start_y * GRID_SIZE + GRID_SIZE // 2
        self.pixel_x = self.grid_x
        self.pixel_y = self.grid_y

        # 状态
        self.alive = True
        self.direction = (0, 0)  # (dx, dy)
        self.next_direction = (0, 0)
        self.speed = 3.5  # 像素/帧
        self.trail = []  # 轨迹上的网格坐标列表
        self.is_moving = False
        self.territory_count = 0
        self.score = 0
        self.respawn_timer = 0

        # 移动锁定（刚占领后短暂锁定，防止立即死亡）
        self.move_lock = 0

    def _lighten(self, color, amount):
        r = max(0, min(255, color[0] + amount))
        g = max(0, min(255, color[1] + amount))
        b = max(0, min(255, color[2] + amount))
        return (int(r), int(g), int(b))

    @property
    def grid_pos(self):
        return (int(self.grid_x // GRID_SIZE), int(self.grid_y // GRID_SIZE))

    def set_direction(self, dx, dy):
        """设置移动方向，不允许反向"""
        if self.direction == (-dx, -dy):
            return
        self.next_direction = (dx, dy)

    def start_moving(self):
        """开始移动（设置方向后调用）"""
        if self.next_direction != (0, 0):
            self.direction = self.next_direction
            self.is_moving = True

    def die(self):
        """玩家死亡"""
        self.alive = False
        self.respawn_timer = 120  # 2秒后复活
        # 清除轨迹
        self.trail = []
        self.is_moving = False
        self.direction = (0, 0)
        self.next_direction = (0, 0)

    def respawn(self):
        """复活"""
        # 找一个安全位置
        start_x = random.randint(2, COLS - 3)
        start_y = random.randint(2, ROWS - 3)
        self.grid_x = start_x * GRID_SIZE + GRID_SIZE // 2
        self.grid_y = start_y * GRID_SIZE + GRID_SIZE // 2
        self.pixel_x = self.grid_x
        self.pixel_y = self.grid_y
        self.alive = True
        self.direction = (0, 0)
        self.next_direction = (0, 0)
        self.trail = []
        self.is_moving = False
        self.move_lock = 30

    def close_trail(self):
        """闭合轨迹，将轨迹内的区域占领"""
        if len(self.trail) < 4:
            self.trail = []
            return

        grid = self.game.grid
        trail_set = set(self.trail)

        # 使用 flood fill 找到被包围的区域
        # 从轨迹外部开始填充，看哪些格子无法到达边界
        outer_visited = set()
        queue = []

        # 从边界开始 BFS
        for x in range(COLS):
            for y in [0, ROWS - 1]:
                if (x, y) not in trail_set and grid[y][x] != self.color_idx:
                    queue.append((x, y))
        for y in range(ROWS):
            for x in [0, COLS - 1]:
                if (x, y) not in trail_set and grid[y][x] != self.color_idx:
                    queue.append((x, y))

        while queue:
            x, y = queue.pop(0)
            if (x, y) in outer_visited or (x, y) in trail_set:
                continue
            if grid[y][x] == self.color_idx:
                continue
            outer_visited.add((x, y))
            for nx, ny in get_neighbors(x, y):
                if (nx, ny) not in outer_visited and (nx, ny) not in trail_set and grid[ny][nx] != self.color_idx:
                    queue.append((nx, ny))

        # 所有不在 outer_visited 且不是 trail 的格子就是被包围的区域
        claimed = 0
        for y in range(ROWS):
            for x in range(COLS):
                if (x, y) not in outer_visited and (x, y) not in trail_set:
                    if grid[y][x] != self.color_idx:  # 不是自己的领土
                        grid[y][x] = self.color_idx
                        claimed += 1

        # 将轨迹也变成领土
        for x, y in self.trail:
            grid[y][x] = self.color_idx

        self.territory_count += claimed
        self.trail = []
        self.move_lock = 15  # 短暂无敌

        # 如果其他玩家在刚占领的领土上，让他们死亡
        for other in self.game.players:
            if other is not self and other.alive:
                ox, oy = other.grid_pos
                if grid[oy][ox] == self.color_idx:
                    other.die()

    def update(self):
        """更新玩家状态"""
        if not self.alive:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.respawn()
            return

        if self.move_lock > 0:
            self.move_lock -= 1

        # 应用方向
        if self.next_direction != (0, 0):
            self.direction = self.next_direction
            self.next_direction = (0, 0)

        if self.direction == (0, 0):
            return

        self.is_moving = True

        # 移动
        dx, dy = self.direction
        self.pixel_x += dx * self.speed
        self.pixel_y += dy * self.speed

        # 边界检测
        self.pixel_x = max(GRID_SIZE // 2, min(SCREEN_WIDTH - GRID_SIZE // 2, self.pixel_x))
        self.pixel_y = max(GRID_SIZE // 2, min(SCREEN_HEIGHT - GRID_SIZE // 2, self.pixel_y))

        # 检查是否到达新网格
        new_gx = int(self.pixel_x // GRID_SIZE)
        new_gy = int(self.pixel_y // GRID_SIZE)
        old_gx = int(self.grid_x // GRID_SIZE)
        old_gy = int(self.grid_y // GRID_SIZE)

        if (new_gx, new_gy) != (old_gx, old_gy):
            self.grid_x = new_gx * GRID_SIZE + GRID_SIZE // 2
            self.grid_y = new_gy * GRID_SIZE + GRID_SIZE // 2

            # 添加轨迹
            if (new_gx, new_gy) not in self.trail:
                self.trail.append((new_gx, new_gy))

            # 检查是否踩到自己的领土（闭合轨迹）
            grid = self.game.grid
            if grid[new_gy][new_gx] == self.color_idx and len(self.trail) > 3 and self.move_lock <= 0:
                self.close_trail()
                return

            # 检查是否踩到别人的领土
            if grid[new_gy][new_gx] != -1 and grid[new_gy][new_gx] != self.color_idx and self.move_lock <= 0:
                self.die()
                return

            # 检查是否踩到别人的轨迹
            for other in self.game.players:
                if other is not self and other.alive and other.is_moving:
                    if (new_gx, new_gy) in other.trail:
                        other.die()  # 踩别人轨迹的人让对方死
                        break

            # 检查自己是否踩到自己的轨迹（闭合检测）
            if len(self.trail) > 3 and self.move_lock <= 0:
                if (new_gx, new_gy) in self.trail[:-1]:
                    self.close_trail()
                    return

            # 限制轨迹长度
            if len(self.trail) > 500:
                self.trail.pop(0)

    def draw(self, screen):
        """绘制玩家"""
        if not self.alive:
            return

        # 绘制轨迹
        if len(self.trail) > 1:
            trail_color = self.light_color
            for i, (tx, ty) in enumerate(self.trail):
                rect = pygame.Rect(tx * GRID_SIZE, ty * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                alpha = 0.3 + 0.7 * (i / len(self.trail))
                c = (
                    int(trail_color[0] * alpha),
                    int(trail_color[1] * alpha),
                    int(trail_color[2] * alpha),
                )
                pygame.draw.rect(screen, c, rect)
                pygame.draw.rect(screen, self.dark_color, rect, 1)

        # 绘制玩家身体
        body_rect = pygame.Rect(
            self.pixel_x - GRID_SIZE // 2 + 1,
            self.pixel_y - GRID_SIZE // 2 + 1,
            GRID_SIZE - 2,
            GRID_SIZE - 2,
        )
        pygame.draw.rect(screen, self.color, body_rect)
        pygame.draw.rect(screen, self.light_color, body_rect, 2)

        # 眼睛（表示方向）
        dx, dy = self.direction
        if dx != 0 or dy != 0:
            eye_off_x = dx * 4
            eye_off_y = dy * 4
            eye_rect = pygame.Rect(
                self.pixel_x + eye_off_x - 3,
                self.pixel_y + eye_off_y - 3,
                6, 6,
            )
            pygame.draw.rect(screen, COLORS['white'], eye_rect)
            pygame.draw.rect(screen, COLORS['black'], eye_rect, 1)


# ======================== AI 类 ========================
class AIPlayer(Player):
    """AI 玩家"""

    def __init__(self, game, config):
        super().__init__(game, config)
        self.change_dir_timer = 0
        self.personality = random.choice(['aggressive', 'explorer', 'defensive'])

    def update(self):
        """AI 更新逻辑"""
        if not self.alive:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.respawn()
            return

        if self.move_lock > 0:
            self.move_lock -= 1

        # AI 决策
        self.change_dir_timer -= 1
        if self.change_dir_timer <= 0:
            self._ai_decision()
            self.change_dir_timer = random.randint(5, 20)

        # 调用父类更新
        super().update()

    def _ai_decision(self):
        """AI 决策逻辑"""
        gx, gy = self.grid_pos
        dx, dy = self.direction
        grid = self.game.grid

        # 可用的方向
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        random.shuffle(directions)

        # 避免反向
        safe_dirs = [d for d in directions if d != (-dx, -dy)]

        # 检查前方是否有危险
        danger_ahead = False
        look_ahead = 3
        for i in range(1, look_ahead + 1):
            nx, ny = gx + dx * i, gy + dy * i
            if nx < 0 or nx >= COLS or ny < 0 or ny >= ROWS:
                danger_ahead = True
                break
            if grid[ny][nx] != -1 and grid[ny][nx] != self.color_idx:
                danger_ahead = True
                break
            # 检查其他玩家的轨迹
            for other in self.game.players:
                if other is not self and other.alive and other.is_moving:
                    if (nx, ny) in other.trail:
                        danger_ahead = True
                        break
            if danger_ahead:
                break

        if danger_ahead:
            # 找安全方向
            for d in safe_dirs:
                nx, ny = gx + d[0], gy + d[1]
                if 0 <= nx < COLS and 0 <= ny < ROWS:
                    if grid[ny][nx] == -1 or grid[ny][nx] == self.color_idx:
                        if not any((nx, ny) in other.trail for other in self.game.players
                                   if other is not self and other.alive and other.is_moving):
                            self.set_direction(d[0], d[1])
                            return

        # 正常移动：优先向空地多的地方走
        best_dir = None
        best_score = -1
        for d in safe_dirs:
            nx, ny = gx + d[0], gy + d[1]
            if nx < 0 or nx >= COLS or ny < 0 or ny >= ROWS:
                continue
            if grid[ny][nx] != -1 and grid[ny][nx] != self.color_idx:
                continue
            # 检查是否会被其他玩家轨迹阻挡
            blocked = False
            for other in self.game.players:
                if other is not self and other.alive and other.is_moving:
                    if (nx, ny) in other.trail:
                        blocked = True
                        break
            if blocked:
                continue

            # 计算该方向开放空间大小
            score = self._count_open_space(nx, ny, 5)
            if score > best_score:
                best_score = score
                best_dir = d

        if best_dir:
            self.set_direction(best_dir[0], best_dir[1])
        elif safe_dirs:
            self.set_direction(safe_dirs[0][0], safe_dirs[0][1])

    def _count_open_space(self, x, y, max_dist):
        """计算某个位置周围有多少空地"""
        count = 0
        grid = self.game.grid
        for dy in range(-max_dist, max_dist + 1):
            for dx in range(-max_dist, max_dist + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < COLS and 0 <= ny < ROWS:
                    if grid[ny][nx] == -1:
                        count += 1
        return count


# ======================== 游戏主类 ========================
class PaperIO:
    """纸片大作战主游戏"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Paper.io 纸片大作战")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('simsun', 18, bold=True)
        self.big_font = pygame.font.SysFont('simsun', 48, bold=True)
        self.title_font = pygame.font.SysFont('simsun', 36, bold=True)

        # 游戏网格：-1 = 空地，0-7 = 玩家索引
        self.grid = [[-1 for _ in range(COLS)] for _ in range(ROWS)]

        self.players = []
        self.human_idx = 0
        self.running = True
        self.game_over = False
        self.winner = None
        self.frame_count = 0

        self._init_game()

    def _init_game(self):
        """初始化游戏"""
        self.grid = [[-1 for _ in range(COLS)] for _ in range(ROWS)]
        self.players = []
        self.game_over = False
        self.winner = None

        # 创建玩家
        num_bots = 3  # 3个AI对手
        configs = [PLAYER_CONFIG[0]] + [PLAYER_CONFIG[i + 1] for i in range(num_bots)]

        for i, config in enumerate(configs):
            if i == 0:
                player = Player(self, config)
            else:
                player = AIPlayer(self, config)
            self.players.append(player)

        self.human_idx = 0

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_SPACE:
                        self._init_game()
                    return

                player = self.players[self.human_idx]
                if not player.alive:
                    continue

                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    player.set_direction(0, -1)
                    player.start_moving()
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    player.set_direction(0, 1)
                    player.start_moving()
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    player.set_direction(-1, 0)
                    player.start_moving()
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    player.set_direction(1, 0)
                    player.start_moving()
                elif event.key == pygame.K_SPACE:
                    # 空格键可以重新开始
                    pass

        # 持续按住按键
        if not self.game_over:
            player = self.players[self.human_idx]
            if player.alive:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_UP] or keys[pygame.K_w]:
                    player.set_direction(0, -1)
                    player.start_moving()
                elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    player.set_direction(0, 1)
                    player.start_moving()
                elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    player.set_direction(-1, 0)
                    player.start_moving()
                elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    player.set_direction(1, 0)
                    player.start_moving()

    def update(self):
        """更新游戏状态"""
        if self.game_over:
            return

        self.frame_count += 1

        # 更新所有玩家
        for player in self.players:
            player.update()

        # 更新网格中的领土（定期清理）
        if self.frame_count % 60 == 0:
            self._update_territory_counts()

        # 检查游戏结束条件（只剩一个人或时间到）
        alive_players = [p for p in self.players if p.alive]
        if len(alive_players) <= 1 and self.frame_count > 180:  # 3秒后开始检查
            if alive_players:
                self.game_over = True
                self.winner = alive_players[0]
            else:
                self.game_over = True
                self.winner = max(self.players, key=lambda p: p.territory_count)

        # 长时间后按领土面积决定胜负
        if self.frame_count > 3600:  # 60秒
            self.game_over = True
            self.winner = max(self.players, key=lambda p: p.territory_count)

    def _update_territory_counts(self):
        """更新所有玩家的领土计数"""
        counts = {i: 0 for i in range(len(self.players))}
        for y in range(ROWS):
            for x in range(COLS):
                cell = self.grid[y][x]
                if cell >= 0 and cell < len(self.players):
                    counts[cell] += 1

        for i, player in enumerate(self.players):
            player.territory_count = counts[i]
            player.score = counts[i]

    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(COLORS['bg'])

        # 绘制网格线
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, COLORS['grid'], (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, COLORS['grid'], (0, y), (SCREEN_WIDTH, y), 1)

        # 绘制领土
        for y in range(ROWS):
            for x in range(COLS):
                cell = self.grid[y][x]
                if cell >= 0 and cell < len(self.players):
                    color = PLAYER_COLORS[1][cell]
                    # 淡化领土颜色
                    faded = (
                        color[0] // 3,
                        color[1] // 3,
                        color[2] // 3,
                    )
                    rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    pygame.draw.rect(self.screen, faded, rect)

        # 绘制所有玩家
        for player in self.players:
            player.draw(self.screen)

        # 绘制UI
        self._draw_ui()

        # 绘制游戏结束画面
        if self.game_over:
            self._draw_game_over()

        pygame.display.flip()

    def _draw_ui(self):
        """绘制UI信息"""
        # 顶部信息栏背景
        pygame.draw.rect(self.screen, (0, 0, 0, 180), (0, 0, SCREEN_WIDTH, 40))
        pygame.draw.rect(self.screen, COLORS['dark_gray'], (0, 0, SCREEN_WIDTH, 40), 2)

        # 玩家列表
        x_offset = 10
        for i, player in enumerate(self.players):
            if not player.alive:
                continue
            color = PLAYER_COLORS[1][i]
            # 颜色指示器
            pygame.draw.rect(self.screen, color, (x_offset, 8, 24, 24))
            pygame.draw.rect(self.screen, COLORS['white'], (x_offset, 8, 24, 24), 1)

            # 名字和分数
            name = player.name
            if i == self.human_idx:
                name += " ★"
            text = self.font.render(f"{name}: {player.territory_count}", True, COLORS['white'])
            self.screen.blit(text, (x_offset + 30, 11))

            # 分割线
            if i < len(self.players) - 1:
                pygame.draw.line(self.screen, COLORS['gray'],
                                 (x_offset + 170, 5), (x_offset + 170, 35), 1)

            x_offset += 180

        # 操作提示
        hint = self.font.render("方向键/WASD移动 | 空格重新开始", True, COLORS['gray'])
        self.screen.blit(hint, (SCREEN_WIDTH - 280, 11))

        # 底部状态栏
        alive_count = sum(1 for p in self.players if p.alive)
        status = self.font.render(f"存活: {alive_count}/{len(self.players)}", True, COLORS['gray'])
        self.screen.blit(status, (10, SCREEN_HEIGHT - 25))

    def _draw_game_over(self):
        """绘制游戏结束画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        if self.winner:
            color = PLAYER_COLORS[1][self.winner.color_idx]
            name = self.winner.name
            if self.winner == self.players[self.human_idx]:
                title = "恭喜你赢了！"
            else:
                title = f"{name} 获胜！"

            title_text = self.big_font.render(title, True, color)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
            self.screen.blit(title_text, title_rect)

            score_text = self.title_font.render(
                f"领土: {self.winner.territory_count} 格", True, COLORS['white'])
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(score_text, score_rect)

        # 排行榜
        sorted_players = sorted(self.players, key=lambda p: p.territory_count, reverse=True)
        rank_text = self.font.render("排行榜:", True, COLORS['white'])
        self.screen.blit(rank_text, (SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 + 40))

        for i, p in enumerate(sorted_players):
            rank_color = PLAYER_COLORS[1][p.color_idx]
            txt = f"#{i + 1} {p.name}: {p.territory_count}格"
            t = self.font.render(txt, True, rank_color if p.alive else COLORS['gray'])
            self.screen.blit(t, (SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 2 + 65 + i * 25))

        restart_text = self.font.render("按 空格键 重新开始", True, COLORS['white'])
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 190))
        self.screen.blit(restart_text, restart_rect)

    def run(self):
        """主循环"""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ======================== 入口 ========================
if __name__ == '__main__':
    game = PaperIO()
    game.run()