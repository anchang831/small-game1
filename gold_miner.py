"""
黄金矿工 (Gold Miner) - 经典钩爪抓金矿游戏
===========================================
使用 Pygame 实现，单文件运行，无需外部资源

玩法说明:
- 钩爪左右来回摆动
- 按 空格键 / ↓ 方向键 释放钩爪
- 钩爪抓住金矿/钻石/石块后自动收回
- 在限定时间内达到目标分数即可过关
- 不同物品分值不同 (金矿按大小、钻石最高、石块最低)
- 每过一关，难度提升 (物品价值降低或目标分数提高)

操作:
  空格/↓ : 释放/发射钩爪
  ESC    : 退出游戏
  R      : 重试当前关卡 (游戏结束后)
"""

import pygame
import random
import math
import sys

# ============================================================
# 常量定义
# ============================================================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 颜色
COLOR_SKY = (135, 206, 235)        # 天空蓝
COLOR_GRASS = (34, 139, 34)        # 草地绿
COLOR_DIRT = (139, 119, 80)        # 泥土棕
COLOR_DIRT_DARK = (101, 67, 33)    # 深泥土
COLOR_GOLD = (255, 215, 0)         # 金色
COLOR_GOLD_DARK = (218, 165, 32)   # 暗金
COLOR_DIAMOND = (0, 255, 255)      # 青色 (钻石)
COLOR_ROCK = (128, 128, 128)       # 灰色 (石块)
COLOR_HOOK = (192, 192, 192)       # 银灰 (钩爪)
COLOR_ROPE = (139, 90, 43)         # 绳索棕
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_RED = (255, 50, 50)
COLOR_GREEN = (50, 200, 50)
COLOR_BROWN = (101, 67, 33)

# 游戏区域: 地表线 (草地顶部)
GROUND_Y = 100
# 物品生成区域
MINE_TOP = GROUND_Y + 20
MINE_BOTTOM = SCREEN_HEIGHT - 30

# 钩爪参数
HOOK_ORIGIN_X = SCREEN_WIDTH // 2  # 钩爪原点X (矿工位置)
HOOK_ORIGIN_Y = GROUND_Y - 10      # 钩爪原点Y
HOOK_SWING_SPEED = 1.2             # 摆动角速度 (弧度/秒)
HOOK_EXTEND_SPEED = 8               # 伸展速度 (像素/帧)
HOOK_RETRACT_SPEED = 6              # 收回速度 (像素/帧)
HOOK_MAX_LENGTH = 550               # 最大绳长
HOOK_GRAB_DISTANCE = 30             # 抓取判定距离
HOOK_ANGLE_MIN = -80                # 最小角度 (度)
HOOK_ANGLE_MAX = 80                 # 最大角度 (度)

# 物品类型
TYPE_GOLD_SMALL = 0     # 小金块
TYPE_GOLD_MEDIUM = 1    # 中金块
TYPE_GOLD_LARGE = 2     # 大金块
TYPE_DIAMOND = 3        # 钻石
TYPE_ROCK = 4           # 石块

# 物品属性: (名称, 分值, 颜色, 半径)
ITEM_PROPS = {
    TYPE_GOLD_SMALL:  ("小金块", 50,  COLOR_GOLD, 10),
    TYPE_GOLD_MEDIUM: ("中金块", 150, COLOR_GOLD, 18),
    TYPE_GOLD_LARGE:  ("大金块", 300, COLOR_GOLD_DARK, 26),
    TYPE_DIAMOND:     ("钻石",   500, COLOR_DIAMOND, 12),
    TYPE_ROCK:        ("石块",   20,  COLOR_ROCK, 16),
}

# 关卡配置
LEVELS = [
    {"target": 500,  "time": 60, "item_count": 8,  "rock_ratio": 0.2},
    {"target": 800,  "time": 55, "item_count": 10, "rock_ratio": 0.25},
    {"target": 1200, "time": 50, "item_count": 12, "rock_ratio": 0.3},
    {"target": 1600, "time": 45, "item_count": 14, "rock_ratio": 0.35},
    {"target": 2000, "time": 40, "item_count": 16, "rock_ratio": 0.4},
]


class Item:
    """地下可抓取物品"""

    def __init__(self, x, y, item_type):
        self.x = x
        self.y = y
        self.type = item_type
        self.name, self.value, self.color, self.radius = ITEM_PROPS[item_type]
        self.caught = False
        self.angle_offset = random.uniform(-0.3, 0.3)  # 闪烁偏移
        self.pulse = 0

    def draw(self, screen):
        """绘制物品"""
        self.pulse += 0.05
        pulse_radius = self.radius + int(2 * math.sin(self.pulse + self.angle_offset))

        # 阴影
        pygame.draw.circle(screen, (60, 40, 20), (self.x + 2, self.y + 2), self.radius)

        if self.type == TYPE_DIAMOND:
            # 钻石: 菱形绘制
            points = []
            for i in range(4):
                angle = math.radians(45 + i * 90)
                px = self.x + pulse_radius * math.cos(angle)
                py = self.y + pulse_radius * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(screen, self.color, points)
            pygame.draw.polygon(screen, COLOR_WHITE, points, 2)
            # 高光
            inner = []
            for i in range(4):
                angle = math.radians(45 + i * 90)
                px = self.x + pulse_radius * 0.4 * math.cos(angle)
                py = self.y + pulse_radius * 0.4 * math.sin(angle)
                inner.append((px, py))
            pygame.draw.polygon(screen, (200, 255, 255), inner)
        else:
            # 金矿/石块: 圆形加光泽
            pygame.draw.circle(screen, self.color, (self.x, self.y), pulse_radius)
            pygame.draw.circle(screen, COLOR_WHITE, (self.x, self.y), pulse_radius, 2)
            # 高光
            highlight_x = self.x - pulse_radius * 0.3
            highlight_y = self.y - pulse_radius * 0.3
            highlight_r = pulse_radius * 0.35
            pygame.draw.circle(screen, (255, 255, 200),
                               (int(highlight_x), int(highlight_y)), int(highlight_r))

        # 如果是大金块额外加星标
        if self.type == TYPE_GOLD_LARGE:
            star_size = 5
            star_points = []
            for i in range(10):
                a = math.radians(i * 36 - 90)
                r = star_size if i % 2 == 0 else star_size * 0.4
                star_points.append((self.x + r * math.cos(a), self.y - pulse_radius - 10 + r * math.sin(a)))
            pygame.draw.polygon(screen, (255, 255, 100), star_points)
            pygame.draw.polygon(screen, COLOR_GOLD, star_points, 1)

    def get_rect(self):
        """获取碰撞矩形"""
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)


class Hook:
    """钩爪系统: 摆动、伸展、抓取"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.angle = 0                    # 当前角度 (弧度)
        self.length = 0                   # 当前绳长
        self.swing_dir = 1                # 摆动方向: 1右 -1左
        self.state = "swing"              # swing / extending / retracting
        self.grabbed_item = None          # 抓到的物品引用
        self.target_x = HOOK_ORIGIN_X     # 钩爪尖端X
        self.target_y = HOOK_ORIGIN_Y     # 钩爪尖端Y

    def get_tip_position(self):
        """计算钩爪尖端位置"""
        rad = math.radians(self.angle)
        tx = HOOK_ORIGIN_X + self.length * math.sin(rad)
        ty = HOOK_ORIGIN_Y + self.length * math.cos(rad)
        return tx, ty

    def update(self, items):
        """更新钩爪状态"""
        if self.state == "swing":
            # 左右摆动
            self.angle += HOOK_SWING_SPEED * self.swing_dir
            if self.angle > HOOK_ANGLE_MAX:
                self.angle = HOOK_ANGLE_MAX
                self.swing_dir = -1
            elif self.angle < HOOK_ANGLE_MIN:
                self.angle = HOOK_ANGLE_MIN
                self.swing_dir = 1
            # 更新尖端位置
            self.target_x, self.target_y = self.get_tip_position()

        elif self.state == "extending":
            # 伸展绳索
            self.length += HOOK_EXTEND_SPEED
            self.target_x, self.target_y = self.get_tip_position()

            # 检查是否超出最大长度或超出屏幕
            if self.length >= HOOK_MAX_LENGTH or self.target_y >= SCREEN_HEIGHT:
                self.state = "retracting"
                return

            # 碰撞检测: 检查是否抓到物品
            for item in items:
                if item.caught:
                    continue
                dx = self.target_x - item.x
                dy = self.target_y - item.y
                dist = math.hypot(dx, dy)
                if dist < HOOK_GRAB_DISTANCE + item.radius:
                    self.grabbed_item = item
                    item.caught = True
                    self.state = "retracting"
                    break

        elif self.state == "retracting":
            # 收回绳索 (有物品时速度变慢)
            speed = HOOK_RETRACT_SPEED
            if self.grabbed_item:
                speed = HOOK_RETRACT_SPEED * 0.7

            self.length -= speed
            if self.length < 0:
                self.length = 0
                self.state = "swing"
                # 如果抓到了物品，计入分数
                grabbed = self.grabbed_item
                self.grabbed_item = None
                self.target_x, self.target_y = self.get_tip_position()
                return grabbed  # 返回抓到的物品

            self.target_x, self.target_y = self.get_tip_position()

            # 如果有抓到的物品，让它跟随钩爪
            if self.grabbed_item:
                self.grabbed_item.x = self.target_x
                self.grabbed_item.y = self.target_y

        return None

    def fire(self):
        """发射钩爪"""
        if self.state == "swing":
            self.state = "extending"

    def draw(self, screen):
        """绘制绳索和钩爪"""
        # 绳索
        if self.length > 0:
            pygame.draw.line(screen, COLOR_ROPE,
                             (HOOK_ORIGIN_X, HOOK_ORIGIN_Y),
                             (self.target_x, self.target_y), 3)

        # 钩爪 (在尖端绘制一个爪形)
        tip_x, tip_y = self.target_x, self.target_y
        rad = math.radians(self.angle)

        if self.state == "swing":
            # 摆动状态: 绘制一个钩子
            claw_size = 12
            # 主钩
            claw_angle = rad
            for offset in [-0.4, 0, 0.4]:
                cx = tip_x + claw_size * math.sin(claw_angle + offset)
                cy = tip_y + claw_size * math.cos(claw_angle + offset)
                pygame.draw.line(screen, COLOR_HOOK,
                                 (tip_x, tip_y), (cx, cy), 3)
            # 钩尖
            pygame.draw.circle(screen, COLOR_HOOK, (int(tip_x), int(tip_y)), 5)
        else:
            # 伸展/收回: 绘制爪形
            claw_size = 10
            spread = 0.6 if self.state == "extending" else 0.3
            for offset in [-spread, 0, spread]:
                angle_off = rad + offset
                end_x = tip_x + claw_size * math.sin(angle_off)
                end_y = tip_y + claw_size * math.cos(angle_off)
                pygame.draw.line(screen, COLOR_HOOK,
                                 (tip_x, tip_y), (end_x, end_y), 3)
            # 中心点
            pygame.draw.circle(screen, (200, 200, 200), (int(tip_x), int(tip_y)), 4)


class GoldMiner:
    """游戏主类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("黄金矿工 Gold Miner")
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.Font(None, 48)
        self.font_large = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)

        # 音效用 pygame.mixer.Sound 生成简单的beep
        pygame.mixer.init(frequency=22050, size=-16, channels=1)
        self.sound_grab = self._create_beep(880, 0.1)
        self.sound_score = self._create_beep(1200, 0.15)
        self.sound_level_up = self._create_beep(660, 0.3)
        self.sound_fail = self._create_beep(300, 0.4)

        self.reset_game()

    def _create_beep(self, freq, duration):
        """生成简单的蜂鸣音效"""
        sample_rate = 22050
        samples = int(sample_rate * duration)
        buf = bytearray()
        for i in range(samples):
            t = i / sample_rate
            # 简单的正弦波 + 衰减
            amplitude = int(8000 * (1 - i / samples) * math.sin(2 * math.pi * freq * t))
            buf.extend(amplitude.to_bytes(2, 'little', signed=True))
        try:
            sound = pygame.mixer.Sound(buffer=bytes(buf))
            return sound
        except Exception:
            return None

    def reset_game(self):
        """重置游戏状态"""
        self.score = 0
        self.level = 0
        self.time_left = 60
        self.game_over = False
        self.level_complete = False
        self.show_message = ""
        self.message_timer = 0
        self.start_level()

    def start_level(self):
        """开始当前关卡"""
        if self.level >= len(LEVELS):
            # 通关! 循环回第一关但提高难度
            self.level = 0
            # 分数奖励
            self.score += 500

        config = LEVELS[self.level]
        self.target_score = config["target"]
        self.time_left = config["time"]
        self.level_complete = False
        self.show_message = f"第 {self.level + 1} 关 - 目标: {self.target_score} 分"
        self.message_timer = 120  # 显示2秒

        # 生成物品
        self.items = []
        self._generate_items(
            config["item_count"],
            config["rock_ratio"]
        )

        # 重置钩爪
        self.hook = Hook()

    def _generate_items(self, count, rock_ratio):
        """在地下区域随机生成物品"""
        # 划分网格以均匀分布
        cols = 6
        rows = max(3, count // cols + 1)
        cell_w = (SCREEN_WIDTH - 60) / cols
        cell_h = (MINE_BOTTOM - MINE_TOP) / rows

        positions = []
        for r in range(rows):
            for c in range(cols):
                x = 40 + c * cell_w + random.uniform(10, cell_w - 20)
                y = MINE_TOP + r * cell_h + random.uniform(10, cell_h - 20)
                positions.append((x, y))

        random.shuffle(positions)
        positions = positions[:count]

        # 生成物品类型 (保证至少有一个钻石和大金块)
        types = []
        types.append(TYPE_DIAMOND)
        types.append(TYPE_GOLD_LARGE)
        types.append(TYPE_GOLD_MEDIUM)

        for _ in range(count - 3):
            if random.random() < rock_ratio:
                types.append(TYPE_ROCK)
            else:
                r = random.random()
                if r < 0.5:
                    types.append(TYPE_GOLD_SMALL)
                elif r < 0.8:
                    types.append(TYPE_GOLD_MEDIUM)
                else:
                    types.append(TYPE_GOLD_LARGE)

        random.shuffle(types)

        for i, pos in enumerate(positions):
            item = Item(pos[0], pos[1], types[i])
            self.items.append(item)

    def handle_events(self):
        """处理用户输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_SPACE or event.key == pygame.K_DOWN:
                    if self.game_over:
                        if event.key == pygame.K_r or event.key == pygame.K_SPACE:
                            self.reset_game()
                    elif self.level_complete:
                        self.next_level()
                    else:
                        self.hook.fire()
                if event.key == pygame.K_r and self.game_over:
                    self.reset_game()
        return True

    def next_level(self):
        """进入下一关"""
        self.level += 1
        self.start_level()

    def update(self):
        """更新游戏状态"""
        if self.game_over or self.level_complete:
            return

        # 更新消息计时器
        if self.message_timer > 0:
            self.message_timer -= 1

        # 更新钩爪
        grabbed = self.hook.update(self.items)
        if grabbed:
            self.score += grabbed.value
            self.items.remove(grabbed)
            if self.sound_score:
                self.sound_score.play()
            self.show_message = f"+{grabbed.value} {grabbed.name}!"
            self.message_timer = 60

        # 更新计时器 (每秒减1)
        # 使用帧计数近似: 60帧 = 1秒
        if pygame.time.get_ticks() % FPS == 0 and not self.hook.state == "retracting":
            self.time_left -= 1

        # 检查是否通关
        if self.score >= self.target_score and not self.level_complete:
            self.level_complete = True
            self.show_message = "🎉 过关! 按空格进入下一关 🎉"
            self.message_timer = 9999
            if self.sound_level_up:
                self.sound_level_up.play()

        # 检查超时
        if self.time_left <= 0:
            self.game_over = True
            self.show_message = "⏰ 时间到! 按 R 重新开始 ⏰"
            self.message_timer = 9999
            if self.sound_fail:
                self.sound_fail.play()

    def draw_background(self):
        """绘制背景"""
        # 天空
        self.screen.fill(COLOR_SKY)

        # 太阳
        pygame.draw.circle(self.screen, (255, 255, 100), (680, 50), 35)
        pygame.draw.circle(self.screen, (255, 255, 200), (680, 50), 25)

        # 地面 (草地)
        grass_rect = pygame.Rect(0, GROUND_Y - 15, SCREEN_WIDTH, 25)
        pygame.draw.rect(self.screen, COLOR_GRASS, grass_rect)
        # 草地纹理 - 小草
        for i in range(0, SCREEN_WIDTH, 12):
            h = random.randint(5, 12)
            pygame.draw.line(self.screen, (20, 100, 20),
                             (i, GROUND_Y - 15),
                             (i, GROUND_Y - 15 - h), 2)

        # 泥土层
        dirt_rect = pygame.Rect(0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y)
        pygame.draw.rect(self.screen, COLOR_DIRT, dirt_rect)

        # 泥土纹理 (小点)
        for _ in range(200):
            dx = random.randint(0, SCREEN_WIDTH)
            dy = random.randint(GROUND_Y + 5, SCREEN_HEIGHT - 5)
            pygame.draw.circle(self.screen, COLOR_DIRT_DARK, (dx, dy), random.randint(1, 3))

    def draw_miner(self):
        """绘制矿工角色"""
        mx, my = HOOK_ORIGIN_X, HOOK_ORIGIN_Y

        # 身体
        body_rect = pygame.Rect(mx - 15, my - 25, 30, 28)
        pygame.draw.ellipse(self.screen, (200, 150, 100), body_rect)

        # 头
        pygame.draw.circle(self.screen, (255, 220, 180), (mx, my - 35), 14)

        # 安全帽
        hat_rect = pygame.Rect(mx - 16, my - 48, 32, 12)
        pygame.draw.ellipse(self.screen, (255, 200, 0), hat_rect)
        # 帽檐
        pygame.draw.rect(self.screen, (255, 200, 0),
                         (mx - 18, my - 40, 36, 4))

        # 眼睛
        pygame.draw.circle(self.screen, COLOR_BLACK, (mx - 5, my - 37), 2)
        pygame.draw.circle(self.screen, COLOR_BLACK, (mx + 5, my - 37), 2)

        # 微笑
        pygame.draw.arc(self.screen, COLOR_RED,
                        (mx - 6, my - 32, 12, 8), 0, math.pi, 2)

        # 手臂 (绳子连着)
        pygame.draw.line(self.screen, (200, 150, 100),
                         (mx + 12, my - 10),
                         (mx + 20, my + 5), 4)

        # 矿工名字
        name_surf = self.font_small.render("矿工", True, COLOR_WHITE)
        name_rect = name_surf.get_rect(midtop=(mx, my + 5))
        self.screen.blit(name_surf, name_rect)

    def draw_ui(self):
        """绘制UI信息"""
        # 分数
        score_text = f"得分: {self.score}  / 目标: {self.target_score}"
        score_surf = self.font_large.render(score_text, True, COLOR_WHITE)
        self.screen.blit(score_surf, (20, 12))

        # 关卡
        level_text = f"第 {self.level + 1} 关"
        level_surf = self.font_large.render(level_text, True, COLOR_WHITE)
        level_rect = level_surf.get_rect(topright=(SCREEN_WIDTH - 20, 12))
        self.screen.blit(level_surf, level_rect)

        # 计时器
        time_color = COLOR_RED if self.time_left < 15 else COLOR_WHITE
        time_text = f"时间: {self.time_left}s"
        time_surf = self.font_large.render(time_text, True, time_color)
        time_rect = time_surf.get_rect(topright=(SCREEN_WIDTH - 20, 48))
        self.screen.blit(time_surf, time_rect)

        # 进度条: 得分进度
        bar_x, bar_y = 20, 50
        bar_w, bar_h = 300, 16
        # 背景
        pygame.draw.rect(self.screen, (60, 60, 60),
                         (bar_x, bar_y, bar_w, bar_h), border_radius=8)
        # 进度
        progress = min(1.0, self.score / max(1, self.target_score))
        fill_w = int(bar_w * progress)
        fill_color = COLOR_GREEN if progress >= 1.0 else COLOR_GOLD
        if fill_w > 0:
            pygame.draw.rect(self.screen, fill_color,
                             (bar_x, bar_y, fill_w, bar_h), border_radius=8)
        # 边框
        pygame.draw.rect(self.screen, COLOR_WHITE,
                         (bar_x, bar_y, bar_w, bar_h), 2, border_radius=8)
        # 百分数
        pct_text = f"{int(progress * 100)}%"
        pct_surf = self.font_small.render(pct_text, True, COLOR_BLACK)
        pct_rect = pct_surf.get_rect(center=(bar_x + bar_w // 2, bar_y + bar_h // 2))
        self.screen.blit(pct_surf, pct_rect)

        # 消息提示 (居中)
        if self.message_timer > 0:
            msg_alpha = 255
            if self.message_timer < 30:
                msg_alpha = int(255 * self.message_timer / 30)
            msg_surf = self.font_large.render(self.show_message, True, COLOR_WHITE)
            msg_surf.set_alpha(msg_alpha)
            msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            # 背景框
            bg_rect = msg_rect.inflate(30, 16)
            bg_surf = pygame.Surface(bg_rect.size)
            bg_surf.set_alpha(160)
            bg_surf.fill(COLOR_BLACK)
            self.screen.blit(bg_surf, bg_rect)
            self.screen.blit(msg_surf, msg_rect)

        # 游戏结束提示
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(COLOR_BLACK)
            self.screen.blit(overlay, (0, 0))

            title = self.font_title.render("游戏结束", True, COLOR_RED)
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
            self.screen.blit(title, title_rect)

            result = self.font_large.render(
                f"最终得分: {self.score}  |  到达关卡: {self.level + 1}",
                True, COLOR_WHITE
            )
            result_rect = result.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(result, result_rect)

            hint = self.font_small.render("按 R 或 空格 重新开始 | ESC 退出", True, COLOR_GOLD)
            hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(hint, hint_rect)

        # 操作提示
        if self.hook.state == "swing" and not self.game_over and not self.level_complete:
            hint = self.font_small.render("按 空格/↓ 释放钩爪", True, (255, 255, 200))
            hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20))
            self.screen.blit(hint, hint_rect)

    def draw(self):
        """绘制所有内容"""
        self.draw_background()
        self.draw_miner()

        # 绘制物品
        for item in self.items:
            item.draw(self.screen)

        # 绘制钩爪
        self.hook.draw(self.screen)

        # 绘制UI
        self.draw_ui()

        pygame.display.flip()

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


# ============================================================
# 程序入口
# ============================================================
if __name__ == "__main__":
    game = GoldMiner()
    game.run()