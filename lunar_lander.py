"""
月球着陆器 (Lunar Lander) - 登月着陆模拟游戏
===============================
控制登月舱，在月球表面安全着陆。
使用方向键控制推进器，注意燃料有限。

操作方式:
  ↑ 或 W - 主推进器（向上）
  ← 或 A - 向左平移
  → 或 D - 向右平移
  R      - 重新开始
  ESC    - 退出

作者: AI 游戏开发者
日期: 2026-07-08
"""

import pygame
import math
import random

# ==================== 游戏配置 ====================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

# 物理参数
GRAVITY = 0.05  # 月球重力加速度
THRUST_POWER = 0.15  # 推进器推力
SIDE_THRUST = 0.08  # 侧向推力
MAX_SPEED = 8  # 最大速度
FUEL_CONSUMPTION = 0.3  # 燃料消耗速率

# 安全着陆条件
MAX_LANDING_SPEED = 1.8  # 最大安全着陆速度
MAX_LANDING_ANGLE = 15  # 最大安全着陆角度（度）

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (40, 40, 40)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 50, 255)
YELLOW = (255, 255, 50)
ORANGE = (255, 165, 0)
MOON_GRAY = (180, 180, 180)
MOON_DARK = (120, 120, 120)
SKY_COLOR = (5, 5, 20)
STAR_COLOR = (200, 200, 255)


class Lander:
    """登月舱类 - 处理物理、绘制和状态"""

    def __init__(self, x, y):
        self.reset(x, y)

    def reset(self, x=None, y=None):
        """重置登月舱状态"""
        self.x = x if x is not None else SCREEN_WIDTH // 2
        self.y = y if y is not None else 100
        self.vx = 0.0  # 水平速度
        self.vy = 0.0  # 垂直速度
        self.angle = 0.0  # 倾斜角度（度）
        self.fuel = 100.0  # 燃料
        self.thrust = False  # 主推进器
        self.thrust_left = False  # 左推进器
        self.thrust_right = False  # 右推进器
        self.alive = True
        self.landed = False
        self.crashed = False
        self.score = 0

        # 着陆腿
        self.leg_deployed = True

        # 粒子效果
        self.exhaust_particles = []

    def update(self, terrain):
        """更新登月舱物理状态"""
        if self.landed or self.crashed:
            return

        # 应用推进器
        if self.thrust and self.fuel > 0:
            # 主推进器沿飞船方向的反方向施加力
            rad = math.radians(self.angle)
            self.vx -= math.sin(rad) * THRUST_POWER
            self.vy -= math.cos(rad) * THRUST_POWER
            self.fuel -= FUEL_CONSUMPTION
            # 生成尾焰粒子
            self._add_exhaust(self.x, self.y, self.angle, 5)

        if self.thrust_left and self.fuel > 0:
            self.angle -= 2.0
            self.fuel -= FUEL_CONSUMPTION * 0.2

        if self.thrust_right and self.fuel > 0:
            self.angle += 2.0
            self.fuel -= FUEL_CONSUMPTION * 0.2

        if self.fuel < 0:
            self.fuel = 0

        # 应用重力
        self.vy += GRAVITY

        # 速度限制
        speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        if speed > MAX_SPEED:
            scale = MAX_SPEED / speed
            self.vx *= scale
            self.vy *= scale

        # 更新位置
        self.x += self.vx
        self.y += self.vy

        # 更新粒子
        self._update_particles()

        # 地面碰撞检测
        terrain_height = terrain.get_height_at(self.x)
        if self.y >= terrain_height:
            self.y = terrain_height
            self._handle_landing(terrain_height)

        # 边界检测（左右出界）
        if self.x < 0:
            self.x = 0
            self.vx = 0
        elif self.x > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH
            self.vx = 0

    def _add_exhaust(self, x, y, angle, count):
        """添加尾焰粒子"""
        rad = math.radians(angle)
        for _ in range(count):
            dx = random.uniform(-3, 3) + math.sin(rad) * random.uniform(1, 4)
            dy = random.uniform(-3, 3) + math.cos(rad) * random.uniform(1, 4)
            self.exhaust_particles.append({
                'x': x - math.sin(rad) * 20,
                'y': y + math.cos(rad) * 20,
                'vx': dx,
                'vy': dy,
                'life': random.randint(15, 30),
                'max_life': 30,
                'size': random.randint(2, 5)
            })

    def _update_particles(self):
        """更新粒子"""
        for p in self.exhaust_particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.05  # 粒子受重力
            p['life'] -= 1
            if p['life'] <= 0:
                self.exhaust_particles.remove(p)

    def _handle_landing(self, terrain_height):
        """处理着陆逻辑"""
        speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        angle_ok = abs(self.angle) <= MAX_LANDING_ANGLE

        if speed <= MAX_LANDING_SPEED and angle_ok:
            # 安全着陆
            self.landed = True
            self.vy = 0
            self.vx = 0
            # 着陆评分：燃料越多、速度越慢，分数越高
            self.score = int((100 - speed * 30) + self.fuel * 2)
            if self.score < 0:
                self.score = 0
        else:
            # 坠毁
            self.crashed = True
            self.alive = False
            self.score = 0
            # 坠毁爆炸效果
            for _ in range(50):
                self._add_exhaust(self.x, terrain_height, random.uniform(0, 360), 3)

    def draw(self, screen):
        """绘制登月舱"""
        # 绘制尾焰粒子
        for p in self.exhaust_particles:
            alpha = p['life'] / p['max_life']
            color = (
                int(255 * alpha),
                int(150 * alpha),
                int(50 * alpha * alpha)
            )
            size = int(p['size'] * alpha)
            if size > 0:
                pygame.draw.circle(screen, color, (int(p['x']), int(p['y'])), size)

        if self.crashed and not self.exhaust_particles:
            # 坠毁后显示残骸
            self._draw_wreckage(screen)
            return

        # 绘制登月舱主体
        center_x, center_y = int(self.x), int(self.y)
        rad = math.radians(self.angle)

        # 登月舱形状（从上到下：舱体、燃料箱、着陆腿）
        # 舱体（多边形）
        body_points = [
            (-12, -20), (12, -20), (15, -5), (12, 10),
            (-12, 10), (-15, -5)
        ]
        rotated_body = []
        for px, py in body_points:
            rx = px * math.cos(rad) - py * math.sin(rad)
            ry = px * math.sin(rad) + py * math.cos(rad)
            rotated_body.append((center_x + rx, center_y + ry))

        # 舱体颜色（根据状态）
        if self.landed:
            body_color = (100, 200, 100)  # 绿色 - 安全着陆
        elif self.crashed:
            body_color = (200, 50, 50)  # 红色 - 坠毁
        else:
            body_color = (200, 200, 200)  # 白色 - 正常

        pygame.draw.polygon(screen, body_color, rotated_body)
        pygame.draw.polygon(screen, WHITE, rotated_body, 2)

        # 窗户（圆形）
        wx = center_x + math.sin(rad) * (-5)
        wy = center_y - math.cos(rad) * 10
        pygame.draw.circle(screen, BLUE, (int(wx), int(wy)), 5)
        pygame.draw.circle(screen, WHITE, (int(wx), int(wy)), 5, 1)

        if not self.crashed and self.leg_deployed:
            # 着陆腿（左）
            leg1 = [(-10, 10), (-20, 22)]
            rotated_leg1 = []
            for px, py in leg1:
                rx = px * math.cos(rad) - py * math.sin(rad)
                ry = px * math.sin(rad) + py * math.cos(rad)
                rotated_leg1.append((center_x + rx, center_y + ry))
            pygame.draw.line(screen, GRAY, rotated_leg1[0], rotated_leg1[1], 3)

            # 着陆腿（右）
            leg2 = [(10, 10), (20, 22)]
            rotated_leg2 = []
            for px, py in leg2:
                rx = px * math.cos(rad) - py * math.sin(rad)
                ry = px * math.sin(rad) + py * math.cos(rad)
                rotated_leg2.append((center_x + rx, center_y + ry))
            pygame.draw.line(screen, GRAY, rotated_leg2[0], rotated_leg2[1], 3)

            # 脚垫
            for leg in [rotated_leg1, rotated_leg2]:
                pygame.draw.circle(screen, YELLOW, (int(leg[1][0]), int(leg[1][1])), 3)

        # 推进器火焰效果
        if self.thrust and self.fuel > 0 and not self.landed and not self.crashed:
            flame_length = random.randint(15, 30)
            flame_points = [
                (-8, 15), (0, 15 + flame_length), (8, 15)
            ]
            rotated_flame = []
            for px, py in flame_points:
                rx = px * math.cos(rad) - py * math.sin(rad)
                ry = px * math.sin(rad) + py * math.cos(rad)
                rotated_flame.append((center_x + rx, center_y + ry))
            pygame.draw.polygon(screen, ORANGE, rotated_flame)
            pygame.draw.polygon(screen, YELLOW, rotated_flame, 1)

    def _draw_wreckage(self, screen):
        """绘制坠毁残骸"""
        center_x, center_y = int(self.x), int(self.y)
        rad = math.radians(self.angle)

        # 破碎的残骸
        wreck_points = [
            (-15, -10), (5, -20), (18, -5), (10, 15),
            (-10, 12), (-20, 0)
        ]
        rotated = []
        for px, py in wreck_points:
            rx = px * math.cos(rad) - py * math.sin(rad)
            ry = px * math.sin(rad) + py * math.cos(rad)
            rotated.append((center_x + rx, center_y + ry))
        pygame.draw.polygon(screen, RED, rotated)
        pygame.draw.polygon(screen, DARK_GRAY, rotated, 2)

        # 爆炸碎片
        for i in range(8):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.randint(5, 20)
            px = center_x + math.cos(angle) * dist
            py = center_y + math.sin(angle) * dist
            pygame.draw.rect(screen, GRAY, (px, py, 4, 4))


class Terrain:
    """月球地形类"""

    def __init__(self):
        self.points = []
        self.landing_pads = []
        self._generate()

    def _generate(self):
        """生成随机月球表面地形"""
        self.points = []
        self.landing_pads = []

        # 生成地形点
        num_points = 40
        segment_width = SCREEN_WIDTH / (num_points - 1)

        # 基础高度线
        base_height = SCREEN_HEIGHT - 150
        prev_y = base_height

        for i in range(num_points):
            x = i * segment_width

            if i == 0 or i == num_points - 1:
                y = base_height
            else:
                # 随机起伏
                variation = random.uniform(-60, 60)
                y = base_height + variation
                # 平滑过渡
                y = (y + prev_y) / 2

            prev_y = y
            self.points.append((x, y))

        # 生成2-3个平坦着陆平台
        num_pads = random.randint(2, 3)
        pad_width = 60  # 平台宽度
        for _ in range(num_pads):
            idx = random.randint(3, num_points - 4)
            x = self.points[idx][0]
            # 确保平台平坦
            flat_y = self.points[idx][1]
            self.landing_pads.append({
                'x1': x - pad_width / 2,
                'x2': x + pad_width / 2,
                'y': flat_y,
                'color': (0, 200, 0)  # 绿色平台
            })

    def get_height_at(self, x):
        """获取指定x坐标的地形高度"""
        if x < 0 or x >= SCREEN_WIDTH:
            return SCREEN_HEIGHT

        # 找到x所在的区间
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            if x1 <= x <= x2:
                # 线性插值
                t = (x - x1) / (x2 - x1)
                return y1 + t * (y2 - y1)

        return SCREEN_HEIGHT - 100

    def is_on_landing_pad(self, x):
        """检查是否在着陆平台上"""
        for pad in self.landing_pads:
            if pad['x1'] <= x <= pad['x2']:
                return True, pad
        return False, None

    def draw(self, screen):
        """绘制地形"""
        # 绘制地形填充
        if len(self.points) > 1:
            poly_points = self.points + [(SCREEN_WIDTH, SCREEN_HEIGHT), (0, SCREEN_HEIGHT)]
            pygame.draw.polygon(screen, MOON_GRAY, poly_points)
            pygame.draw.polygon(screen, MOON_DARK, poly_points, 2)

        # 绘制着陆平台
        for pad in self.landing_pads:
            x1, x2, y = pad['x1'], pad['x2'], pad['y']
            rect = pygame.Rect(int(x1), int(y - 5), int(x2 - x1), 10)
            pygame.draw.rect(screen, pad['color'], rect)
            pygame.draw.rect(screen, GREEN, rect, 2)

            # 平台标记 "H" (Helipad)
            font = pygame.font.Font(None, 20)
            label = font.render("H", True, GREEN)
            label_rect = label.get_rect(center=(int((x1 + x2) / 2), int(y - 8)))
            screen.blit(label, label_rect)


class StarField:
    """星空背景"""

    def __init__(self):
        self.stars = []
        for _ in range(150):
            self.stars.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.uniform(0.5, 2.5),
                'brightness': random.uniform(0.3, 1.0),
                'twinkle_speed': random.uniform(0.01, 0.05)
            })
        self.time = 0

    def update(self):
        self.time += 1

    def draw(self, screen):
        for star in self.stars:
            # 闪烁效果
            brightness = star['brightness'] * (0.7 + 0.3 * math.sin(self.time * star['twinkle_speed']))
            color = (
                int(200 * brightness),
                int(200 * brightness),
                int(255 * brightness)
            )
            pygame.draw.circle(screen, color,
                               (int(star['x']), int(star['y'])),
                               int(star['size']))


class HUD:
    """抬头显示 - 显示游戏信息"""

    def __init__(self):
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)

    def draw(self, screen, lander, terrain, elapsed_time):
        """绘制HUD"""
        # 右上角信息面板
        panel_x = SCREEN_WIDTH - 220
        panel_y = 10
        panel_w = 205
        panel_h = 200

        # 半透明背景
        panel_surf = pygame.Surface((panel_w, panel_h))
        panel_surf.set_alpha(180)
        panel_surf.fill(DARK_GRAY)
        screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(screen, WHITE, (panel_x, panel_y, panel_w, panel_h), 1)

        # 信息显示
        info_lines = [
            (f"高度: {int(SCREEN_HEIGHT - terrain.get_height_at(lander.x) - (SCREEN_HEIGHT - lander.y))} m", WHITE),
            (f"垂直速度: {lander.vy:.1f} m/s", GREEN if abs(lander.vy) < MAX_LANDING_SPEED else RED),
            (f"水平速度: {lander.vx:.1f} m/s", WHITE),
            (f"倾角: {lander.angle:.1f}°", GREEN if abs(lander.angle) < MAX_LANDING_ANGLE else RED),
            (f"燃料: {lander.fuel:.0f}%", YELLOW if lander.fuel > 20 else RED),
        ]

        y_offset = panel_y + 10
        for text, color in info_lines:
            surface = self.font_small.render(text, True, color)
            screen.blit(surface, (panel_x + 10, y_offset))
            y_offset += 28

        # 时间显示
        time_text = self.font_small.render(f"时间: {elapsed_time:.1f}s", True, WHITE)
        screen.blit(time_text, (panel_x + 10, y_offset + 5))

        # 安全速度指示器
        speed = math.sqrt(lander.vx ** 2 + lander.vy ** 2)
        speed_ratio = min(speed / MAX_LANDING_SPEED, 2.0)

        # 进度条
        bar_x = panel_x + 10
        bar_y = panel_y + panel_h - 30
        bar_w = panel_w - 20
        bar_h = 12

        # 背景
        pygame.draw.rect(screen, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 1)

        # 填充
        fill_w = int(bar_w * speed_ratio)
        if speed_ratio <= 1.0:
            bar_color = GREEN
        elif speed_ratio <= 1.5:
            bar_color = YELLOW
        else:
            bar_color = RED
        pygame.draw.rect(screen, bar_color, (bar_x, bar_y, fill_w, bar_h))

        speed_label = self.font_small.render("着陆速度", True, WHITE)
        screen.blit(speed_label, (bar_x, bar_y - 18))

        # 状态消息
        if lander.landed:
            center_x = SCREEN_WIDTH // 2
            msg = "安全着陆! 按 R 重新开始"
            color = GREEN
            surface = self.font_large.render(msg, True, color)
            surface_rect = surface.get_rect(center=(center_x, 80))
            # 背景框
            bg_rect = surface_rect.inflate(20, 10)
            bg = pygame.Surface(bg_rect.size)
            bg.set_alpha(200)
            bg.fill(BLACK)
            screen.blit(bg, bg_rect)
            screen.blit(surface, surface_rect)

            # 显示分数
            score_text = self.font_medium.render(f"得分: {lander.score}", True, YELLOW)
            score_rect = score_text.get_rect(center=(center_x, 120))
            screen.blit(score_text, score_rect)

        elif lander.crashed:
            center_x = SCREEN_WIDTH // 2
            msg = "坠毁! 按 R 重新开始"
            color = RED
            surface = self.font_large.render(msg, True, color)
            surface_rect = surface.get_rect(center=(center_x, 80))
            bg_rect = surface_rect.inflate(20, 10)
            bg = pygame.Surface(bg_rect.size)
            bg.set_alpha(200)
            bg.fill(BLACK)
            screen.blit(bg, bg_rect)
            screen.blit(surface, surface_rect)

        # 操作提示
        if not lander.landed and not lander.crashed:
            hints = "↑/W=推进  ←/→/A/D=旋转  R=重开  ESC=退出"
            hint_surface = self.font_small.render(hints, True, GRAY)
            hint_rect = hint_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20))
            screen.blit(hint_surface, hint_rect)


def main():
    """主游戏函数"""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("月球着陆器 - Lunar Lander")
    clock = pygame.time.Clock()

    # 创建游戏对象
    terrain = Terrain()
    lander = Lander(SCREEN_WIDTH // 2, 100)
    star_field = StarField()
    hud = HUD()

    # 游戏状态
    running = True
    paused = False
    elapsed_time = 0.0
    frame_count = 0

    # 游戏主循环
    while running:
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    # 重新开始
                    terrain = Terrain()
                    lander = Lander(SCREEN_WIDTH // 2, 100)
                    elapsed_time = 0.0
                    frame_count = 0
                elif event.key == pygame.K_p:
                    paused = not paused

        # 按键状态检测（持续按住）
        if not paused and not lander.landed and not lander.crashed:
            keys = pygame.key.get_pressed()
            lander.thrust = keys[pygame.K_UP] or keys[pygame.K_w]
            lander.thrust_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
            lander.thrust_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

            # 更新游戏逻辑
            lander.update(terrain)
            star_field.update()

            # 更新时间
            frame_count += 1
            if frame_count % FPS == 0:
                elapsed_time += 1.0

        # 绘制
        screen.fill(SKY_COLOR)

        # 绘制星空
        star_field.draw(screen)

        # 绘制地形
        terrain.draw(screen)

        # 绘制登月舱
        lander.draw(screen)

        # 绘制HUD
        hud.draw(screen, lander, terrain, elapsed_time)

        # 更新显示
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()