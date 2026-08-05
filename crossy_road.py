"""
Crossy Road - 无尽过马路
====================
经典跳跃过马路游戏，控制角色不断向前跳跃，
躲避车流，越过障碍，挑战最高分！

操作: 方向键/WASD控制跳跃方向
"""

import pygame
import random
import sys

# ==================== 初始化 ====================
pygame.init()
pygame.display.set_caption("Crossy Road - 无尽过马路")

# ==================== 常量定义 ====================
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 720
LANE_HEIGHT = 72
GRID_SIZE = 60
FPS = 60

# 颜色
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
GREEN = (76, 175, 80)
DARK_GREEN = (56, 142, 60)
ROAD_COLOR = (55, 55, 55)
ROAD_LINE = (80, 80, 80)
GRASS_LIGHT = (100, 200, 100)
GRASS_DARK = (90, 190, 90)
RIVER_COLOR = (33, 150, 243)
DARK_RIVER = (25, 130, 220)
YELLOW = (255, 235, 59)
RED = (244, 67, 54)
BLUE = (33, 150, 243)
BROWN = (121, 85, 72)
ORANGE = (255, 152, 0)
PURPLE = (156, 39, 176)
GRAY = (158, 158, 158)
DARK_GRAY = (80, 80, 80)

# ==================== 游戏状态 ====================
class GameState:
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2

# ==================== 玩家类 ====================
class Player:
    def __init__(self):
        self.reset()

    def reset(self):
        """重置玩家状态"""
        # 网格坐标 (col, row)
        self.grid_x = 4
        self.grid_y = 0
        # 屏幕坐标（用于平滑动画）
        self.screen_x = self.grid_x * GRID_SIZE + (SCREEN_WIDTH - GRID_SIZE) // 2
        self.screen_y = SCREEN_HEIGHT - 120
        # 目标坐标（动画插值）
        self.target_x = self.screen_x
        self.target_y = self.screen_y
        # 动画进度 0~1
        self.anim_progress = 1.0
        self.is_moving = False
        self.alive = True
        self.score = 0
        self.best_score = 0
        # 视觉大小
        self.size = 40

    def move(self, dx, dy, lanes_data):
        """尝试向(dx, dy)方向移动"""
        if self.is_moving or not self.alive:
            return False

        new_gx = self.grid_x + dx
        new_gy = self.grid_y + dy

        # 边界检查
        if new_gx < 0 or new_gx > 7:
            return False
        # 不能后退超过起点
        if new_gy < 0:
            return False

        # 计算目标屏幕坐标
        new_sx = new_gx * GRID_SIZE + (SCREEN_WIDTH - GRID_SIZE) // 2
        new_sy = self.screen_y - dy * LANE_HEIGHT

        self.grid_x = new_gx
        self.grid_y = new_gy
        self.target_x = new_sx
        self.target_y = new_sy
        self.is_moving = True
        self.anim_progress = 0.0

        # 每前进一行加一分
        if dy > 0:
            self.score += 1

        return True

    def update(self, dt):
        """更新动画"""
        if self.is_moving:
            self.anim_progress += dt * 6.0  # 跳跃速度
            if self.anim_progress >= 1.0:
                self.anim_progress = 1.0
                self.is_moving = False

            # 缓动函数（跳跃弧线）
            t = self.anim_progress
            self.screen_x = self.target_x
            self.screen_y = self.target_y
            # 跳跃弧线让y方向有弹性效果
            jump_offset = -25 * (4 * t * (1 - t))  # 抛物线弧高

            # 实际绘制时使用偏移，但位置还是目标位置
            self._jump_offset = jump_offset
        else:
            self._jump_offset = 0

    def draw(self, screen):
        """绘制玩家"""
        x = self.screen_x + 30
        y = self.screen_y + LANE_HEIGHT // 2 + (self._jump_offset if hasattr(self, '_jump_offset') else 0)

        # 身体（圆形）
        body_color = YELLOW
        if not self.alive:
            body_color = GRAY
            # 死亡闪烁效果
            if pygame.time.get_ticks() % 200 < 100:
                return

        # 身体
        pygame.draw.circle(screen, body_color, (x, y - 8), 18)
        # 头部
        pygame.draw.circle(screen, body_color, (x, y - 28), 14)
        # 眼睛
        eye_color = BLACK
        pygame.draw.circle(screen, eye_color, (x - 5, y - 30), 3)
        pygame.draw.circle(screen, eye_color, (x + 5, y - 30), 3)
        # 眼睛高光
        pygame.draw.circle(screen, WHITE, (x - 4, y - 31), 1)
        pygame.draw.circle(screen, WHITE, (x + 6, y - 31), 1)
        # 嘴巴（喙）
        pygame.draw.polygon(screen, ORANGE, [
            (x, y - 24),
            (x + 8, y - 22),
            (x, y - 20)
        ])
        # 翅膀
        pygame.draw.ellipse(screen, body_color, (x - 22, y - 14, 10, 16))
        pygame.draw.ellipse(screen, body_color, (x + 12, y - 14, 10, 16))
        # 脚
        foot_color = ORANGE
        pygame.draw.ellipse(screen, foot_color, (x - 8, y + 4, 8, 6))
        pygame.draw.ellipse(screen, foot_color, (x + 2, y + 4, 8, 6))

# ==================== 车辆类 ====================
class Car:
    def __init__(self, lane_y, direction, speed, car_type=0):
        self.lane_y = lane_y
        self.direction = direction  # 1: right, -1: left
        self.speed = speed
        self.car_type = car_type
        self.width = random.choice([60, 80, 100])
        self.height = 36

        if direction == 1:
            self.x = -self.width
        else:
            self.x = SCREEN_WIDTH

        # 颜色方案
        self.colors = [
            (RED, (200, 50, 50)),       # 红色
            (BLUE, (50, 100, 200)),      # 蓝色
            (GREEN, (50, 180, 80)),      # 绿色
            (ORANGE, (220, 140, 20)),    # 橙色
            (PURPLE, (140, 60, 180)),    # 紫色
            (YELLOW, (200, 200, 50)),    # 黄色
            (WHITE, (200, 200, 200)),    # 白色
            (GRAY, (120, 120, 120)),     # 灰色
        ]
        self.main_color, self.dark_color = random.choice(self.colors)

    def update(self, dt, speed_multiplier):
        """更新车辆位置"""
        self.x += self.direction * self.speed * speed_multiplier * 60 * dt

    def draw(self, screen, camera_y):
        """绘制车辆"""
        y = self.lane_y - camera_y
        if y < -50 or y > SCREEN_HEIGHT + 50:
            return

        # 车身
        car_rect = pygame.Rect(self.x, y - self.height // 2, self.width, self.height)
        pygame.draw.rect(screen, self.main_color, car_rect, border_radius=6)

        # 车窗
        window_w = 12
        window_h = 14
        window_y = y - 7
        if self.direction == 1:  # 向右
            pygame.draw.rect(screen, self.dark_color,
                           (self.x + 12, window_y, window_w, window_h), border_radius=3)
            pygame.draw.rect(screen, self.dark_color,
                           (self.x + self.width - 24, window_y, window_w, window_h), border_radius=3)
        else:
            pygame.draw.rect(screen, self.dark_color,
                           (self.x + 8, window_y, window_w, window_h), border_radius=3)
            pygame.draw.rect(screen, self.dark_color,
                           (self.x + self.width - 20, window_y, window_w, window_h), border_radius=3)

        # 车轮
        wheel_color = DARK_GRAY
        wheel_w, wheel_h = 8, 12
        pygame.draw.ellipse(screen, wheel_color, (self.x + 8, y - self.height // 2 - 2, wheel_w, wheel_h))
        pygame.draw.ellipse(screen, wheel_color, (self.x + self.width - 16, y - self.height // 2 - 2, wheel_w, wheel_h))
        pygame.draw.ellipse(screen, wheel_color, (self.x + 8, y + self.height // 2 - 10, wheel_w, wheel_h))
        pygame.draw.ellipse(screen, wheel_color, (self.x + self.width - 16, y + self.height // 2 - 10, wheel_w, wheel_h))

        # 车灯
        light_color = YELLOW
        if self.direction == 1:
            pygame.draw.circle(screen, light_color, (self.x + self.width - 4, y - 6), 4)
            pygame.draw.circle(screen, light_color, (self.x + self.width - 4, y + 6), 4)
        else:
            pygame.draw.circle(screen, light_color, (self.x + 4, y - 6), 4)
            pygame.draw.circle(screen, light_color, (self.x + 4, y + 6), 4)

    def get_rect(self):
        """获取碰撞矩形"""
        return pygame.Rect(self.x, self.lane_y - self.height // 2, self.width, self.height)

    def is_off_screen(self):
        """判断是否超出屏幕"""
        if self.direction == 1 and self.x > SCREEN_WIDTH + 50:
            return True
        if self.direction == -1 and self.x < -self.width - 50:
            return True
        return False

# ==================== 车道类 ====================
class Lane:
    """车道基类"""
    def __init__(self, lane_type, row_index):
        self.type = lane_type  # 'grass', 'road'
        self.row_index = row_index
        self.y = row_index * LANE_HEIGHT
        self.cars = []
        self.spawn_timer = 0
        self.spawn_interval = random.uniform(1.5, 3.0)
        self.car_speed = random.uniform(100, 200)
        self.direction = random.choice([-1, 1])
        self.has_crossed = False  # 标记玩家是否已穿过此车道

    def update(self, dt, speed_multiplier):
        """更新车道及车辆"""
        if self.type == 'road':
            # 更新现有车辆
            for car in self.cars[:]:
                car.update(dt, speed_multiplier)
                if car.is_off_screen():
                    self.cars.remove(car)

            # 生成新车
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_interval:
                self.spawn_timer = 0
                self.spawn_interval = random.uniform(0.8, 2.5) / max(speed_multiplier, 0.5)
                self.cars.append(Car(self.y, self.direction, self.car_speed))

    def draw(self, screen, camera_y):
        """绘制车道"""
        y = self.y - camera_y
        if y < -LANE_HEIGHT or y > SCREEN_HEIGHT + LANE_HEIGHT:
            return

        if self.type == 'grass':
            # 草地方格
            for col in range(8):
                color = GRASS_LIGHT if (col + self.row_index) % 2 == 0 else GRASS_DARK
                pygame.draw.rect(screen, color,
                               (col * GRID_SIZE, y, GRID_SIZE, LANE_HEIGHT))
            # 草地装饰 - 小花
            if random.randint(0, 3) == 0:
                flower_x = random.randint(0, 7) * GRID_SIZE + 20
                flower_y = y + random.randint(10, LANE_HEIGHT - 10)
                pygame.draw.circle(screen, (255, 200, 200), (flower_x, flower_y), 3)
                pygame.draw.circle(screen, (255, 255, 200), (flower_x + 20, flower_y + 10), 3)

        elif self.type == 'road':
            # 路面
            pygame.draw.rect(screen, ROAD_COLOR, (0, y, SCREEN_WIDTH, LANE_HEIGHT))
            # 车道分隔线（虚线）
            for x in range(0, SCREEN_WIDTH, 60):
                pygame.draw.rect(screen, ROAD_LINE, (x, y + LANE_HEIGHT // 2 - 2, 30, 4))
            # 路肩
            pygame.draw.rect(screen, DARK_GRAY, (0, y, SCREEN_WIDTH, 4))
            pygame.draw.rect(screen, DARK_GRAY, (0, y + LANE_HEIGHT - 4, SCREEN_WIDTH, 4))

            # 绘制车辆
            for car in self.cars:
                car.draw(screen, 0)  # camera_y 已通过 lane.y 计算

    def check_collision(self, player_rect, camera_y):
        """检查与车辆碰撞"""
        if self.type != 'road':
            return False
        player_y = self.y - camera_y + LANE_HEIGHT // 2
        for car in self.cars:
            car_rect = car.get_rect()
            car_rect.y -= camera_y
            # 简化碰撞检测
            if abs(player_rect.centerx - car_rect.centerx) < (player_rect.width // 2 + car_rect.width // 2 - 8) and \
               abs(player_y - car_rect.centery) < (player_rect.height // 2 + car_rect.height // 2 - 8):
                return True
        return False

# ==================== 游戏主类 ====================
class CrossyRoadGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        self.font_tiny = pygame.font.Font(None, 24)

        self.state = GameState.MENU
        self.player = Player()
        self.lanes = []
        self.camera_y = 0
        self.speed_multiplier = 1.0
        self.difficulty_timer = 0
        self.game_over_timer = 0
        self.particles = []  # 粒子效果
        self.bg_offset = 0
        self.total_lanes_created = 0  # 跟踪已创建车道数

        # 背景星星
        self.stars = [(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT))
                      for _ in range(50)]

        self._init_lanes()

    def _init_lanes(self):
        """初始化车道"""
        self.lanes.clear()
        self.total_lanes_created = 0
        # 初始车道：玩家站在第0行（草地）
        self.lanes.append(Lane('grass', 0))
        self.total_lanes_created = 1
        # 前面生成10行
        for i in range(1, 12):
            self._add_lane()

    def _add_lane(self):
        """添加新车道"""
        lane_type = 'road' if random.random() < 0.55 else 'grass'
        lane = Lane(lane_type, self.total_lanes_created)
        # 难度提升
        if self.total_lanes_created > 3:
            lane.car_speed = random.uniform(120, 180 + self.total_lanes_created * 5)
            lane.direction = random.choice([-1, 1])
        self.lanes.append(lane)
        self.total_lanes_created += 1

    def reset(self):
        """重置游戏"""
        self.player.reset()
        self._init_lanes()
        self.camera_y = 0
        self.speed_multiplier = 1.0
        self.difficulty_timer = 0
        self.game_over_timer = 0
        self.particles.clear()
        self.state = GameState.PLAYING

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.reset()
                    elif event.key == pygame.K_ESCAPE:
                        return False

                elif self.state == GameState.PLAYING:
                    dx, dy = 0, 0
                    if event.key in (pygame.K_UP, pygame.K_w):
                        dx, dy = 0, 1
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        dx, dy = 0, -1
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        dx, dy = -1, 0
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        dx, dy = 1, 0
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU
                        return True

                    if dx != 0 or dy != 0:
                        self.player.move(dx, dy, self.lanes)
                        # 玩家前进时产生粒子效果
                        if dy > 0:
                            self._add_particles(
                                self.player.screen_x + 30,
                                self.player.screen_y + LANE_HEIGHT // 2,
                                (YELLOW, ORANGE, WHITE), 5
                            )

                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.reset()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = GameState.MENU

        return True

    def _add_particles(self, x, y, colors, count):
        """添加粒子效果"""
        for _ in range(count):
            self.particles.append({
                'x': x, 'y': y,
                'vx': random.uniform(-80, 80),
                'vy': random.uniform(-120, -30),
                'life': random.uniform(0.3, 0.8),
                'max_life': random.uniform(0.3, 0.8),
                'color': random.choice(colors),
                'size': random.randint(3, 6)
            })

    def update_particles(self, dt):
        """更新粒子"""
        for p in self.particles[:]:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += 200 * dt  # 重力
            p['life'] -= dt
            if p['life'] <= 0:
                self.particles.remove(p)

    def update(self, dt):
        """更新游戏状态"""
        if self.state != GameState.PLAYING:
            return

        # 更新玩家
        self.player.update(dt)

        # 更新难度
        self.difficulty_timer += dt
        if self.difficulty_timer > 5:
            self.difficulty_timer = 0
            self.speed_multiplier = min(2.5, self.speed_multiplier + 0.1)

        # 更新车道
        for lane in self.lanes:
            lane.update(dt, self.speed_multiplier)

        # 更新粒子
        self.update_particles(dt)

        # 更新摄像机跟随玩家
        target_cam = self.player.grid_y * LANE_HEIGHT - SCREEN_HEIGHT + 150
        target_cam = max(0, target_cam)
        self.camera_y += (target_cam - self.camera_y) * dt * 5

        # 动态生成新车道
        visible_top = int(self.camera_y // LANE_HEIGHT) - 1
        visible_bottom = int((self.camera_y + SCREEN_HEIGHT) // LANE_HEIGHT) + 2

        # 确保有足够车道在可见区域上方
        max_row = max(lane.row_index for lane in self.lanes) if self.lanes else 0
        while max_row < visible_bottom + 3:
            self._add_lane()
            max_row = max(lane.row_index for lane in self.lanes)

        # 移除下方过远的车道
        min_row = max(0, visible_top - 5)
        self.lanes = [l for l in self.lanes if l.row_index >= min_row]

        # 碰撞检测
        player_rect = pygame.Rect(
            self.player.screen_x + 15,
            self.player.screen_y + LANE_HEIGHT // 2 - 12,
            30, 24
        )

        # 找到玩家所在车道
        player_world_y = self.player.grid_y * LANE_HEIGHT
        for lane in self.lanes:
            if abs(lane.y - player_world_y) < LANE_HEIGHT // 2:
                if lane.check_collision(player_rect, self.camera_y):
                    self._on_game_over()
                break

        # 边界死亡（掉出左右边界）
        if self.player.grid_x < -2 or self.player.grid_x > 9:
            self._on_game_over()

        # 更新最高分
        self.player.best_score = max(self.player.best_score, self.player.score)

    def _on_game_over(self):
        """游戏结束处理"""
        self.player.alive = False
        self.state = GameState.GAME_OVER
        self.game_over_timer = 0
        self._add_particles(
            self.player.screen_x + 30,
            self.player.screen_y + LANE_HEIGHT // 2,
            (RED, ORANGE, YELLOW, WHITE), 20
        )

    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(BLACK)

        if self.state == GameState.MENU:
            self._draw_menu()
        elif self.state == GameState.PLAYING:
            self._draw_game()
        elif self.state == GameState.GAME_OVER:
            self._draw_game()
            self._draw_game_over_overlay()

        pygame.display.flip()

    def _draw_menu(self):
        """绘制主菜单"""
        # 背景渐变
        for i in range(SCREEN_HEIGHT):
            r = int(10 + i * 0.01)
            g = int(20 + i * 0.02)
            b = int(40 + i * 0.03)
            pygame.draw.line(self.screen, (min(r, 60), min(g, 80), min(b, 120)),
                           (0, i), (SCREEN_WIDTH, i))

        # 星星
        for star in self.stars:
            alpha = random.randint(50, 200)
            pygame.draw.circle(self.screen, (alpha, alpha, alpha),
                             star, random.randint(1, 2))

        # 标题
        title = self.font_large.render("CROSSY ROAD", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 180))
        self.screen.blit(title, title_rect)

        # 副标题
        sub = self.font_small.render("无尽过马路", True, WHITE)
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, 230))
        self.screen.blit(sub, sub_rect)

        # 小鸡图标
        temp_player = Player()
        temp_player.screen_x = SCREEN_WIDTH // 2 - 30
        temp_player.screen_y = 310
        temp_player._jump_offset = 0
        temp_player.draw(self.screen)

        # 操作说明
        instructions = [
            "按 SPACE 开始游戏",
            "",
            "操作方式:",
            "↑/W  向前跳",
            "↓/S  向后跳",
            "←/A  向左跳",
            "→/D  向右跳",
            "",
            "躲避车辆，不断前进！"
        ]

        y_offset = 400
        for line in instructions:
            if line == "":
                y_offset += 12
                continue
            is_highlight = "SPACE" in line or "操作方式" in line
            color = YELLOW if is_highlight else WHITE
            text = self.font_tiny.render(line, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 30

    def _draw_game(self):
        """绘制游戏主画面"""
        # 绘制所有车道
        for lane in self.lanes:
            lane.draw(self.screen, self.camera_y)

        # 绘制粒子
        for p in self.particles:
            alpha = int(255 * (p['life'] / p['max_life']))
            pygame.draw.circle(self.screen, p['color'],
                             (int(p['x']), int(p['y'] - self.camera_y + self.player.grid_y * LANE_HEIGHT)),
                             max(1, int(p['size'] * (p['life'] / p['max_life']))))

        # 绘制玩家
        self.player.draw(self.screen)

        # 绘制HUD
        self._draw_hud()

    def _draw_hud(self):
        """绘制HUD信息"""
        # 分数
        score_text = self.font_medium.render(f"{self.player.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 40))
        # 分数背景
        bg_rect = score_rect.inflate(30, 10)
        pygame.draw.rect(self.screen, (0, 0, 0, 128), bg_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255, 50), bg_rect, 2, border_radius=10)
        self.screen.blit(score_text, score_rect)

        # 分数标签
        label = self.font_tiny.render("SCORE", True, GRAY)
        label_rect = label.get_rect(center=(SCREEN_WIDTH // 2, 18))
        self.screen.blit(label, label_rect)

        # 最高分
        best_text = self.font_tiny.render(f"最高: {self.player.best_score}", True, YELLOW)
        best_rect = best_text.get_rect(topright=(SCREEN_WIDTH - 20, 20))
        self.screen.blit(best_text, best_rect)

        # 速度指示（难度）
        speed_text = self.font_tiny.render(f"速度 x{self.speed_multiplier:.1f}", True, GRAY)
        speed_rect = speed_text.get_rect(topleft=(20, 20))
        self.screen.blit(speed_text, speed_rect)

    def _draw_game_over_overlay(self):
        """绘制游戏结束覆盖层"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # 游戏结束文字
        game_over = self.font_large.render("GAME OVER", True, RED)
        game_over_rect = game_over.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        self.screen.blit(game_over, game_over_rect)

        # 分数
        score_text = self.font_medium.render(f"得分: {self.player.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        self.screen.blit(score_text, score_rect)

        # 最高分
        best_text = self.font_small.render(f"最高分: {self.player.best_score}", True, YELLOW)
        best_rect = best_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        self.screen.blit(best_text, best_rect)

        # 提示
        hint = self.font_small.render("按 SPACE 重新开始", True, WHITE)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        # 闪烁效果
        if pygame.time.get_ticks() % 1000 < 500:
            self.screen.blit(hint, hint_rect)

        # ESC返回
        esc = self.font_tiny.render("ESC 返回主菜单", True, GRAY)
        esc_rect = esc.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
        self.screen.blit(esc, esc_rect)

    def run(self):
        """游戏主循环"""
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)  # 防止卡顿导致dt过大

            running = self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()

# ==================== 启动游戏 ====================
if __name__ == "__main__":
    game = CrossyRoadGame()
    game.run()