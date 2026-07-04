"""
Duck Hunt (打鸭子)
===================
经典射击游戏：鸭子从屏幕两侧飞出，玩家用瞄准镜点击射击。

操作说明：
- 移动鼠标：控制瞄准镜
- 左键点击：射击
- R键：重新开始
- ESC/空格：标题界面开始游戏

作者：DeepSeek v4.0 PRO
日期：2026-07-04
"""

import pygame
import random
import math
import sys

# ========== 常量定义 ==========
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 颜色
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (34, 139, 34)
GROUND_BROWN = (101, 67, 33)
TREE_DARK = (0, 100, 0)
TREE_TRUNK = (101, 67, 33)
DUCK_BODY = (220, 180, 50)
DUCK_HEAD = (180, 140, 30)
DUCK_EYE = (0, 0, 0)
DUCK_WING_DARK = (190, 150, 40)
CROSSHAIR_RED = (255, 50, 50)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GOLD = (255, 215, 0)
BROWN = (139, 90, 43)
GUNSHOT_YELLOW = (255, 255, 100)

# 鸭子类型
class DuckType:
    NORMAL = "normal"
    FAST = "fast"
    ZIGZAG = "zigzag"
    BONUS = "bonus"  # 金色鸭子，高分


class Duck:
    """鸭子类"""

    def __init__(self, screen_width, screen_height, level=1):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # 从左侧或右侧随机出现
        self.from_left = random.choice([True, False])
        self.x = -60 if self.from_left else screen_width + 60
        self.y = random.randint(80, screen_height // 2 - 20)

        # 飞行方向
        self.direction = 1 if self.from_left else -1

        # 速度随关卡增加
        base_speed = 2.0 + level * 0.3
        self.vx = base_speed * self.direction

        # 鸭子类型
        type_roll = random.random()
        if level >= 3 and type_roll < 0.1:
            self.duck_type = DuckType.BONUS
        elif level >= 2 and type_roll < 0.25:
            self.duck_type = DuckType.ZIGZAG
        elif type_roll < 0.15:
            self.duck_type = DuckType.FAST
        else:
            self.duck_type = DuckType.NORMAL

        # 根据类型调整速度
        if self.duck_type == DuckType.FAST or self.duck_type == DuckType.BONUS:
            self.vx *= 1.6
        if self.duck_type == DuckType.ZIGZAG:
            self.vx *= 1.2

        self.vy = 0
        self.zigzag_timer = 0
        self.zigzag_phase = 0

        # 飞行动画帧
        self.wing_frame = 0
        self.wing_timer = 0
        self.animation_speed = 6

        # 是否被击中
        self.hit = False
        self.hit_timer = 0
        self.fall_y_speed = 0
        self.fall_x_speed = self.vx * 0.3

        # 分数（金色鸭子更多分）
        if self.duck_type == DuckType.BONUS:
            self.points = 500
        elif self.duck_type == DuckType.FAST or self.duck_type == DuckType.ZIGZAG:
            self.points = 200
        else:
            self.points = 100

        # 尺寸
        self.size = int(36 - level * 0.5) if level > 1 else 36
        if self.size < 24:
            self.size = 24

        # 存活时间（防止鸭子飞太久）
        self.lifetime = 0
        self.max_lifetime = 600 + level * 30  # frames

    def update(self):
        """更新鸭子状态"""
        self.lifetime += 1

        if self.hit:
            # 被击中后下落
            self.hit_timer += 1
            self.fall_y_speed += 0.4
            self.y += self.fall_y_speed
            self.x += self.fall_x_speed * 0.5
            return
        else:
            # 正常飞行
            self.x += self.vx

            # Zigzag 模式：上下波动
            if self.duck_type == DuckType.ZIGZAG:
                self.zigzag_timer += 1
                self.zigzag_phase = math.sin(self.zigzag_timer * 0.1) * 3
                self.y += self.zigzag_phase
            else:
                # 普通鸭子在垂直方向微微浮动
                self.y += math.sin(self.lifetime * 0.05) * 0.5

            # 边界控制 - 确保鸭子不会飞出垂直边界太远
            if self.y < 40:
                self.y = 40
            elif self.y > self.screen_height // 2 - 10:
                self.y = self.screen_height // 2 - 10

            # 翅膀动画
            self.wing_timer += 1
            if self.wing_timer >= self.animation_speed:
                self.wing_timer = 0
                self.wing_frame = (self.wing_frame + 1) % 4

    def is_offscreen(self):
        """检查鸭子是否飞出屏幕"""
        return (self.x < -100 or self.x > self.screen_width + 100 or
                self.y > self.screen_height + 50 or
                self.lifetime > self.max_lifetime)

    def check_hit(self, mouse_x, mouse_y):
        """检测是否被击中（矩形碰撞）"""
        if self.hit:
            return False
        # 鸭子的碰撞区域
        hit_rect = pygame.Rect(self.x - self.size // 2, self.y - self.size // 2,
                               self.size, self.size)
        return hit_rect.collidepoint(mouse_x, mouse_y)

    def draw(self, screen):
        """绘制鸭子"""
        if self.hit and self.hit_timer < 5:
            # 被击中瞬间闪光效果
            self._draw_duck_body(screen, True)
            return

        if self.hit:
            # 下落中 - 翻转绘制
            self._draw_duck_body(screen, False)
        else:
            self._draw_duck_body(screen, False)

    def _draw_duck_body(self, screen, flash):
        """绘制鸭子身体"""
        x, y = int(self.x), int(self.y)
        s = self.size // 3
        direction = 1 if self.from_left else -1

        # 如果是金色鸭子，加分颜色
        body_color = GOLD if self.duck_type == DuckType.BONUS else DUCK_BODY
        head_color = GOLD if self.duck_type == DuckType.BONUS else DUCK_HEAD

        if flash:
            body_color = WHITE
            head_color = WHITE

        # 身体（椭圆）
        body_rect = pygame.Rect(x - s * direction, y - s // 2, s * 2 * direction, s)
        if direction > 0:
            body_rect = pygame.Rect(x - s, y - s // 2, s * 2, s)
        else:
            body_rect = pygame.Rect(x - s * 2, y - s // 2, s * 2, s)

        # 确保正的宽高
        if body_rect.width < 0:
            body_rect = pygame.Rect(body_rect.x + body_rect.width, body_rect.y,
                                    -body_rect.width, body_rect.height)

        # 绘制身体
        if direction > 0:
            # 朝右
            pygame.draw.ellipse(screen, body_color,
                                (x - s, y - s // 2, s * 2, s))
            # 头
            pygame.draw.circle(screen, head_color, (x + s, y - s // 4), s // 2)
            # 眼睛
            pygame.draw.circle(screen, DUCK_EYE, (x + s + s // 4, y - s // 4 - 2), 2)
            # 翅膀
            if not self.hit:
                wing_y = y + s // 4 + int(math.sin(self.wing_frame * 0.8) * 3)
                pygame.draw.ellipse(screen, DUCK_WING_DARK,
                                    (x - s // 2, wing_y, s, s // 2))
            # 嘴
            pygame.draw.polygon(screen, (255, 150, 50),
                                [(x + s + s // 2, y - s // 4),
                                 (x + s + s // 2 + 6, y - s // 4 - 2),
                                 (x + s + s // 2 + 6, y - s // 4 + 2)])
        else:
            # 朝左
            pygame.draw.ellipse(screen, body_color,
                                (x - s, y - s // 2, s * 2, s))
            # 头
            pygame.draw.circle(screen, head_color, (x - s, y - s // 4), s // 2)
            # 眼睛
            pygame.draw.circle(screen, DUCK_EYE, (x - s - s // 4, y - s // 4 - 2), 2)
            # 翅膀
            if not self.hit:
                wing_y = y + s // 4 + int(math.sin(self.wing_frame * 0.8) * 3)
                pygame.draw.ellipse(screen, DUCK_WING_DARK,
                                    (x + s // 2, wing_y, s, s // 2))
            # 嘴
            pygame.draw.polygon(screen, (255, 150, 50),
                                [(x - s - s // 2, y - s // 4),
                                 (x - s - s // 2 - 6, y - s // 4 - 2),
                                 (x - s - s // 2 - 6, y - s // 4 + 2)])


class DuckHunt:
    """游戏主类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Duck Hunt - 打鸭子")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)

        # 游戏状态
        self.state = "title"  # title, playing, round_over, game_over
        self.score = 0
        self.level = 1
        self.round = 1
        self.ducks_per_round = 3 + self.level
        self.ducks_spawned = 0
        self.ducks_hit = 0
        self.ducks_missed = 0
        self.ammo = 3  # 每只鸭子3发子弹

        # 鸭子列表
        self.ducks = []
        self.current_duck = None

        # 射击效果
        self.gunshot_effects = []  # [(x, y, timer), ...]
        self.score_popups = []  # [(x, y, text, timer, color), ...]

        # 瞄准镜位置
        self.crosshair_x = SCREEN_WIDTH // 2
        self.crosshair_y = SCREEN_HEIGHT // 2

        # 背景元素
        self.clouds = self._generate_clouds()
        self.bushes = self._generate_bushes()

        # 音效（用 pygame.mixer.Sound 生成简单音效）
        self._init_sounds()

        # 隐藏系统鼠标
        pygame.mouse.set_visible(False)

        # 射击冷却
        self.shoot_cooldown = 0

    def _init_sounds(self):
        """初始化音效（使用 pygame 生成）"""
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1)
            # 枪声 - 白噪声短脉冲
            self.sound_shoot = self._generate_sound_shot()
            # 鸭子中弹声
            self.sound_hit = self._generate_sound_hit()
            # 鸭子叫
            self.sound_quack = self._generate_sound_quack()
            self.sounds_enabled = True
        except Exception:
            self.sounds_enabled = False

    def _generate_sound_shot(self):
        """生成枪声"""
        duration = 0.15
        sample_rate = 22050
        samples = int(duration * sample_rate)
        buf = bytearray()
        for i in range(samples):
            # 白噪声，快速衰减
            t = i / sample_rate
            env = math.exp(-t * 30)
            val = int((random.random() * 2 - 1) * env * 28000)
            val = max(-32767, min(32767, val))
            buf.extend(val.to_bytes(2, 'little', signed=True))
        sound = pygame.mixer.Sound(buffer=bytes(buf))
        sound.set_volume(0.4)
        return sound

    def _generate_sound_hit(self):
        """生成击中音效"""
        duration = 0.2
        sample_rate = 22050
        samples = int(duration * sample_rate)
        buf = bytearray()
        for i in range(samples):
            t = i / sample_rate
            freq = 400 - t * 1500
            env = math.exp(-t * 15)
            val = int(math.sin(2 * math.pi * freq * t) * env * 20000)
            val = max(-32767, min(32767, val))
            buf.extend(val.to_bytes(2, 'little', signed=True))
        sound = pygame.mixer.Sound(buffer=bytes(buf))
        sound.set_volume(0.5)
        return sound

    def _generate_sound_quack(self):
        """生成鸭子叫声"""
        duration = 0.15
        sample_rate = 22050
        samples = int(duration * sample_rate)
        buf = bytearray()
        for i in range(samples):
            t = i / sample_rate
            freq = 300 + math.sin(t * 50) * 100
            env = math.exp(-t * 10)
            # 方波模拟鸭子叫
            val = int(math.sin(2 * math.pi * freq * t) * env * 12000)
            val = max(-32767, min(32767, val))
            buf.extend(val.to_bytes(2, 'little', signed=True))
        sound = pygame.mixer.Sound(buffer=bytes(buf))
        sound.set_volume(0.3)
        return sound

    def _generate_clouds(self):
        """生成云朵"""
        clouds = []
        for _ in range(8):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(20, 180)
            w = random.randint(80, 180)
            h = random.randint(30, 60)
            speed = random.uniform(0.1, 0.3)
            clouds.append({"x": x, "y": y, "w": w, "h": h, "speed": speed})
        return clouds

    def _generate_bushes(self):
        """生成草丛"""
        bushes = []
        for _ in range(6):
            x = random.randint(50, SCREEN_WIDTH - 50)
            bushes.append({"x": x, "y": SCREEN_HEIGHT - 80})
        return bushes

    def spawn_duck(self):
        """生成新的鸭子"""
        if self.current_duck is None or self.current_duck.is_offscreen():
            if self.ducks_spawned < self.ducks_per_round:
                self.current_duck = Duck(SCREEN_WIDTH, SCREEN_HEIGHT, self.level)
                self.ducks.append(self.current_duck)
                self.ducks_spawned += 1
                self.ammo = 3

                # 随机播放鸭子叫
                if self.sounds_enabled and random.random() < 0.3:
                    self.sound_quack.play()
            else:
                # 本轮结束
                self._end_round()

    def shoot(self):
        """射击"""
        mx, my = self.crosshair_x, self.crosshair_y

        # 枪声效果
        self.gunshot_effects.append([mx, my, 15])
        if self.sounds_enabled:
            self.sound_shoot.play()

        # 检测是否击中当前鸭子
        if self.current_duck and not self.current_duck.hit:
            if self.current_duck.check_hit(mx, my):
                # 击中！
                self.current_duck.hit = True
                self.ducks_hit += 1
                points = self.current_duck.points
                self.score += points

                if self.sounds_enabled:
                    self.sound_hit.play()

                # 显示得分弹出
                color = GOLD if self.current_duck.duck_type == DuckType.BONUS else WHITE
                self.score_popups.append([mx, my - 20, f"+{points}", 60, color])

                # 本轮鸭子计数减一（这只鸭子不再需要躲避）
                return

        # 没打中 - 减少弹药
        self.ammo -= 1
        if self.ammo <= 0 and self.current_duck and not self.current_duck.hit:
            # 鸭子飞走了
            self.ducks_missed += 1
            self.current_duck = None  # 强制刷新

    def _end_round(self):
        """结束本轮"""
        self.state = "round_over"
        self.round_timer = 120  # 2 秒后自动进入下一轮

    def next_round(self):
        """进入下一轮"""
        self.round += 1
        if self.round > 5:  # 每5轮升一级
            self.round = 1
            self.level += 1
        self.ducks_spawned = 0
        self.ducks = []
        self.current_duck = None
        self.ducks_per_round = 3 + self.level
        self.ammo = 3
        self.state = "playing"

    def update(self):
        """游戏主更新"""
        self.shoot_cooldown = max(0, self.shoot_cooldown - 1)

        # 更新射击效果
        for effect in self.gunshot_effects[:]:
            effect[2] -= 1
            if effect[2] <= 0:
                self.gunshot_effects.remove(effect)

        # 更新得分弹出
        for popup in self.score_popups[:]:
            popup[3] -= 1
            popup[1] -= 1.5
            if popup[3] <= 0:
                self.score_popups.remove(popup)

        # 更新云朵
        for cloud in self.clouds:
            cloud["x"] += cloud["speed"]
            if cloud["x"] > SCREEN_WIDTH + cloud["w"]:
                cloud["x"] = -cloud["w"]
                cloud["y"] = random.randint(20, 180)

        if self.state == "playing":
            # 如果没有当前鸭子，或鸭子已飞走/被击中下落完毕，生成新的
            if self.current_duck is None:
                self.spawn_duck()
            else:
                self.current_duck.update()
                # 如果鸭子已死且落出屏幕，或已飞出屏幕，生成下一只
                if self.current_duck.is_offscreen():
                    if self.current_duck.hit:
                        # 被击中的下落完毕，增加下一只
                        pass
                    self.current_duck = None

            # 检查本轮是否结束
            if self.ducks_spawned >= self.ducks_per_round and \
               (self.current_duck is None or self.current_duck.is_offscreen()):
                self._end_round()

        elif self.state == "round_over":
            self.round_timer -= 1
            if self.round_timer <= 0:
                self.next_round()

    def draw_background(self):
        """绘制背景"""
        # 天空（渐变色）
        for y in range(SCREEN_HEIGHT - 120):
            color_ratio = y / (SCREEN_HEIGHT - 120)
            r = int(135 + color_ratio * 20)
            g = int(206 - color_ratio * 30)
            b = int(235 - color_ratio * 20)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # 云朵
        for cloud in self.clouds:
            cx, cy, cw, ch = int(cloud["x"]), int(cloud["y"]), int(cloud["w"]), int(cloud["h"])
            # 多层椭圆组成云朵
            pygame.draw.ellipse(self.screen, (255, 255, 255, 200),
                                (cx, cy, cw, ch))
            pygame.draw.ellipse(self.screen, (255, 255, 255, 200),
                                (cx + cw // 4, cy - ch // 3, cw * 2 // 3, ch))
            pygame.draw.ellipse(self.screen, (240, 240, 255, 200),
                                (cx + cw // 2, cy + ch // 4, cw // 2, ch // 2))

        # 远山
        pygame.draw.polygon(self.screen, (100, 150, 100),
                            [(0, SCREEN_HEIGHT - 120),
                             (100, SCREEN_HEIGHT - 220),
                             (200, SCREEN_HEIGHT - 150),
                             (300, SCREEN_HEIGHT - 250),
                             (400, SCREEN_HEIGHT - 180),
                             (500, SCREEN_HEIGHT - 230),
                             (600, SCREEN_HEIGHT - 160),
                             (700, SCREEN_HEIGHT - 210),
                             (SCREEN_WIDTH, SCREEN_HEIGHT - 120)])

        # 草地
        grass_rect = pygame.Rect(0, SCREEN_HEIGHT - 120, SCREEN_WIDTH, 120)
        pygame.draw.rect(self.screen, GRASS_GREEN, grass_rect)

        # 草地纹理细节
        for _ in range(50):
            gx = random.randint(0, SCREEN_WIDTH)
            gy = SCREEN_HEIGHT - 120 + random.randint(0, 100)
            gh = random.randint(8, 18)
            pygame.draw.line(self.screen, (30, 120, 30), (gx, gy), (gx, gy - gh), 2)

        # 树木
        self._draw_tree(100, SCREEN_HEIGHT - 130)
        self._draw_tree(300, SCREEN_HEIGHT - 140)
        self._draw_tree(550, SCREEN_HEIGHT - 135)
        self._draw_tree(720, SCREEN_HEIGHT - 145)

        # 灌木丛
        for bush in self.bushes:
            bx, by = bush["x"], bush["y"]
            pygame.draw.ellipse(self.screen, (20, 100, 20),
                                (bx - 30, by, 60, 35))
            pygame.draw.ellipse(self.screen, (25, 110, 25),
                                (bx - 20, by - 5, 40, 25))

    def _draw_tree(self, x, y):
        """绘制一棵树"""
        # 树干
        pygame.draw.rect(self.screen, TREE_TRUNK, (x - 8, y - 30, 16, 40))
        # 树冠 - 多层圆形
        colors = [(0, 80, 0), (0, 100, 0), (0, 120, 0)]
        for i, color in enumerate(colors):
            offset = i * 8
            pygame.draw.circle(self.screen, color, (x, y - 30 - offset), 28 - i * 5)

    def draw_crosshair(self):
        """绘制瞄准镜"""
        mx, my = self.crosshair_x, self.crosshair_y

        # 外圈
        pygame.draw.circle(self.screen, CROSSHAIR_RED, (mx, my), 18, 2)
        # 内圈
        pygame.draw.circle(self.screen, CROSSHAIR_RED, (mx, my), 3, 1)
        # 十字线
        pygame.draw.line(self.screen, CROSSHAIR_RED, (mx - 25, my), (mx - 10, my), 2)
        pygame.draw.line(self.screen, CROSSHAIR_RED, (mx + 10, my), (mx + 25, my), 2)
        pygame.draw.line(self.screen, CROSSHAIR_RED, (mx, my - 25), (mx, my - 10), 2)
        pygame.draw.line(self.screen, CROSSHAIR_RED, (mx, my + 10), (mx, my + 25), 2)
        # 中心点
        pygame.draw.circle(self.screen, CROSSHAIR_RED, (mx, my), 1)

    def draw_gunshot_effects(self):
        """绘制射击效果"""
        for effect in self.gunshot_effects:
            x, y, timer = effect
            alpha = timer / 15
            size = int(30 * (1 - timer / 15) + 10)
            # 闪光
            pygame.draw.circle(self.screen, GUNSHOT_YELLOW, (x, y), size)
            # 火花粒子
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                px = x + math.cos(rad) * size * 0.5
                py = y + math.sin(rad) * size * 0.5
                pygame.draw.circle(self.screen, RED, (int(px), int(py)), int(3 * alpha))

    def draw_ui(self):
        """绘制UI信息"""
        # 分数
        score_text = self.font_medium.render(f"分数: {self.score}", True, WHITE)
        self.screen.blit(score_text, (20, 20))

        # 关卡
        level_text = self.font_small.render(f"关卡 {self.level}", True, WHITE)
        self.screen.blit(level_text, (20, 70))

        # 轮次
        round_text = self.font_small.render(f"轮次 {self.round}/5", True, WHITE)
        self.screen.blit(round_text, (20, 100))

        if self.state == "playing" and self.current_duck and not self.current_duck.hit:
            # 弹药显示
            ammo_text = self.font_small.render(f"弹药: {'●' * self.ammo}{'○' * (3 - self.ammo)}", True, WHITE)
            self.screen.blit(ammo_text, (SCREEN_WIDTH - 150, 20))

            # 本轮鸭子进度
            duck_progress = self.font_small.render(
                f"鸭子: {self.ducks_hit}/{self.ducks_per_round}", True, WHITE)
            self.screen.blit(duck_progress, (SCREEN_WIDTH - 150, 50))

    def draw_title_screen(self):
        """绘制标题画面"""
        self.draw_background()

        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # 标题
        title = self.font_large.render("DUCK HUNT", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 180))
        self.screen.blit(title, title_rect)

        # 副标题
        sub = self.font_small.render("打 鸭 子", True, GOLD)
        sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, 230))
        self.screen.blit(sub, sub_rect)

        # 操作说明
        instructions = [
            "鼠标移动 - 瞄准",
            "左键点击 - 射击",
            "每只鸭子有3发弹药",
            "金色鸭子价值 500 分！",
        ]
        for i, text in enumerate(instructions):
            inst = self.font_small.render(text, True, (200, 200, 200))
            inst_rect = inst.get_rect(center=(SCREEN_WIDTH // 2, 310 + i * 40))
            self.screen.blit(inst, inst_rect)

        # 开始提示
        blink = int(pygame.time.get_ticks() / 500) % 2 == 0
        if blink:
            start = self.font_medium.render("按 空格键 或 Enter 开始", True, GOLD)
            start_rect = start.get_rect(center=(SCREEN_WIDTH // 2, 520))
            self.screen.blit(start, start_rect)

        # 绘制一只装饰鸭子
        self._draw_title_duck()

    def _draw_title_duck(self):
        """在标题画面绘制一只装饰鸭子"""
        x = SCREEN_WIDTH // 2
        y = 120
        s = 18
        # 简化的鸭子装饰
        pygame.draw.ellipse(self.screen, DUCK_BODY, (x - s, y - s // 2, s * 2, s))
        pygame.draw.circle(self.screen, DUCK_HEAD, (x + s, y - s // 4), s // 2)
        pygame.draw.ellipse(self.screen, DUCK_WING_DARK,
                            (x - s // 2, y + s // 4, s, s // 2))

    def draw_round_over(self):
        """绘制本轮结算"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(100)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # 本轮统计
        title = self.font_large.render(f"第 {self.level}-{self.round} 轮 结束", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 240))
        self.screen.blit(title, title_rect)

        stats = [
            f"击中: {self.ducks_hit} / {self.ducks_per_round} 只鸭子",
            f"当前分数: {self.score}",
            f"下一轮: 关卡 {self.level}, 第 {self.round + 1} 轮",
        ]
        for i, text in enumerate(stats):
            stat = self.font_small.render(text, True, (200, 200, 200))
            stat_rect = stat.get_rect(center=(SCREEN_WIDTH // 2, 310 + i * 40))
            self.screen.blit(stat, stat_rect)

    def draw_game_over(self):
        """绘制游戏结束画面"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(140)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # Game Over
        title = self.font_large.render("GAME OVER", True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 220))
        self.screen.blit(title, title_rect)

        # 最终分数
        score = self.font_large.render(f"最终分数: {self.score}", True, GOLD)
        score_rect = score.get_rect(center=(SCREEN_WIDTH // 2, 300))
        self.screen.blit(score, score_rect)

        # 等级
        level = self.font_small.render(f"到达关卡 {self.level}", True, (200, 200, 200))
        level_rect = level.get_rect(center=(SCREEN_WIDTH // 2, 360))
        self.screen.blit(level, level_rect)

        # 重新开始
        blink = int(pygame.time.get_ticks() / 500) % 2 == 0
        if blink:
            restart = self.font_medium.render("按 R 键重新开始", True, WHITE)
            restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, 440))
            self.screen.blit(restart, restart_rect)

    def run(self):
        """游戏主循环"""
        running = True

        while running:
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "title":
                            running = False
                        else:
                            self.state = "title"
                    elif event.key == pygame.K_r and self.state == "game_over":
                        # 重新开始
                        self.__init__()
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        if self.state == "title":
                            self.state = "playing"
                            self.__init__()
                            self.state = "playing"

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "playing" and self.shoot_cooldown <= 0:
                        self.shoot()
                        self.shoot_cooldown = 10

                elif event.type == pygame.MOUSEMOTION:
                    self.crosshair_x, self.crosshair_y = event.pos

            # 更新
            self.update()

            # 绘制
            self.draw_background()

            if self.state == "title":
                self.draw_title_screen()

            elif self.state == "playing":
                # 绘制鸭子
                if self.current_duck:
                    self.current_duck.draw(self.screen)
                    # 绘制鸭子类型标签
                    if self.current_duck.duck_type == DuckType.BONUS and not self.current_duck.hit:
                        bonus_text = self.font_small.render("500", True, GOLD)
                        self.screen.blit(bonus_text,
                                        (self.current_duck.x - 15,
                                         self.current_duck.y - self.current_duck.size // 2 - 25))

                # 绘制射击效果
                self.draw_gunshot_effects()

                # 绘制得分弹出
                for popup in self.score_popups:
                    text = self.font_small.render(popup[2], True, popup[4])
                    self.screen.blit(text, (int(popup[0]), int(popup[1])))

                # UI
                self.draw_ui()

            elif self.state == "round_over":
                if self.current_duck:
                    self.current_duck.draw(self.screen)
                self.draw_ui()
                self.draw_round_over()

            elif self.state == "game_over":
                self.draw_game_over()

            # 瞄准镜（总是最上层）
            self.draw_crosshair()

            # 显示FPS
            fps_text = self.font_small.render(f"FPS: {int(self.clock.get_fps())}", True, (100, 100, 100))
            self.screen.blit(fps_text, (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 30))

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = DuckHunt()
    game.run()