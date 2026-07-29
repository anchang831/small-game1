"""
西蒙说 (Simon Says) - 经典记忆序列挑战游戏
==========================================
玩法：记住电脑展示的颜色序列，然后按相同顺序点击色块。
每轮增加一个颜色，序列越来越长，挑战你的记忆力！

操作：鼠标点击色块
难度：每轮序列长度+1，答错则游戏结束
"""

import pygame
import sys
import random
import time
import math

# 初始化 Pygame
pygame.init()
try:
    pygame.mixer.init()
    audio_available = True
except pygame.error:
    audio_available = False

# 屏幕尺寸
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("西蒙说 - Simon Says")

# 颜色定义
BLACK = (20, 20, 30)
WHITE = (240, 240, 250)
GRAY = (100, 100, 120)
DARK_GRAY = (50, 50, 65)

# 四种颜色 (亮色和暗色)
COLORS = {
    "red":    {"light": (255, 60, 60),   "dark": (180, 20, 20)},
    "green":  {"light": (60, 255, 60),   "dark": (20, 180, 20)},
    "blue":   {"light": (60, 100, 255),  "dark": (20, 50, 180)},
    "yellow": {"light": (255, 255, 60),  "dark": (200, 180, 20)},
}
COLOR_NAMES = ["red", "green", "blue", "yellow"]
COLOR_SOUND_FREQS = [261, 329, 392, 523]  # C4, E4, G4, C5

# 游戏状态
MENU = 0
PLAYING = 1
SHOWING = 2
INPUT = 3
GAME_OVER = 4

# 字体
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 32)
font_tiny = pygame.font.Font(None, 24)


def generate_sound(frequency, duration=0.15):
    """生成指定频率的方波音效"""
    import numpy as np
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    t = np.arange(n_samples)
    # 生成方波
    wave = 127 * np.sign(np.sin(2 * np.pi * frequency * t / sample_rate)) + 128
    stereo = np.repeat(wave.astype(np.uint8).reshape(-1, 1), 2, axis=1)
    buf = pygame.sndarray.make_sound(stereo)
    buf.set_volume(0.5)
    return buf


# 预生成音效
if audio_available:
    SOUNDS = {name: generate_sound(freq) for name, freq in zip(COLOR_NAMES, COLOR_SOUND_FREQS)}
    SOUND_FAIL = generate_sound(150, 0.3)
else:
    SOUNDS = {}
    SOUND_FAIL = None


def play_sound(sound):
    """安全播放音效（无音频设备时跳过）"""
    if sound and audio_available:
        sound.play()


class Button:
    """色块按钮"""

    def __init__(self, color_name, center, radius, angle_offset):
        self.color_name = color_name
        self.center = center
        self.radius = radius
        self.angle_offset = angle_offset
        self.lit = False
        self.lit_start_time = 0
        self.lit_duration = 0.3
        self.rect = None

    def get_polygon_points(self):
        """生成扇形四边形的顶点（近似圆形按钮的四分之一）"""
        cx, cy = self.center
        r = self.radius
        start_angle = self.angle_offset
        end_angle = self.angle_offset + math.pi / 2
        steps = 20
        points = [(cx, cy)]
        for i in range(steps + 1):
            angle = start_angle + (end_angle - start_angle) * i / steps
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        return points

    def draw(self, surface):
        """绘制色块"""
        color = COLORS[self.color_name]
        if self.lit:
            c = color["light"]
        else:
            c = color["dark"]

        points = self.get_polygon_points()
        pygame.draw.polygon(surface, c, points)
        # 边框
        pygame.draw.polygon(surface, BLACK, points, 3)

        # 高光效果
        if self.lit:
            # 内发光
            inner_points = self.get_polygon_points()
            inner_cx, inner_cy = self.center
            inner_r = self.radius * 0.6
            pygame.draw.polygon(surface, (255, 255, 255, 60), inner_points, 0)
            # 特殊效果：绘制白色渐变高光
            glow_points = [(inner_cx, inner_cy)]
            start_angle = self.angle_offset
            end_angle = self.angle_offset + math.pi / 2
            for i in range(10):
                angle = start_angle + (end_angle - start_angle) * i / 10
                glow_points.append((
                    inner_cx + inner_r * math.cos(angle),
                    inner_cy + inner_r * math.sin(angle)
                ))
            pygame.draw.polygon(surface, (255, 255, 255, 80), glow_points)

    def contains_point(self, pos):
        """检测点是否在扇形区域内"""
        x, y = pos
        cx, cy = self.center
        dx = x - cx
        dy = y - cy
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > self.radius:
            return False

        angle = math.atan2(dy, dx)
        if angle < 0:
            angle += 2 * math.pi

        start_angle = self.angle_offset
        end_angle = self.angle_offset + math.pi / 2

        if end_angle <= 2 * math.pi:
            return start_angle <= angle <= end_angle
        else:
            return angle >= start_angle or angle <= (end_angle - 2 * math.pi)

    def light_up(self):
        """点亮色块"""
        self.lit = True
        self.lit_start_time = time.time()

    def update(self):
        """更新色块状态（自动熄灭）"""
        if self.lit and time.time() - self.lit_start_time > self.lit_duration:
            self.lit = False


class SimonGame:
    """西蒙说游戏主类"""

    def __init__(self):
        self.reset()

    def reset(self):
        """重置游戏"""
        self.sequence = []
        self.player_input = []
        self.state = MENU
        self.round = 0
        self.high_score = 0
        self.showing_index = 0
        self.showing_timer = 0
        self.input_index = 0
        self.strict_mode = False
        self.animation_timer = 0
        self.flash_all = False

        # 创建四个色块按钮
        center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)
        radius = 200
        self.buttons = [
            Button("green", center, radius, 0),       # 右上
            Button("red", center, radius, math.pi / 2),    # 右下
            Button("yellow", center, radius, math.pi),     # 左下
            Button("blue", center, radius, 3 * math.pi / 2),  # 左上
        ]

        # 中心圆
        self.center_radius = 75

    def add_to_sequence(self):
        """在序列末尾添加一个随机颜色"""
        self.sequence.append(random.choice(COLOR_NAMES))
        self.round += 1

    def start_round(self):
        """开始新的一轮"""
        self.add_to_sequence()
        self.state = SHOWING
        self.showing_index = 0
        self.showing_timer = time.time()
        self.player_input = []
        self.input_index = 0

    def start_game(self):
        """开始游戏"""
        self.sequence = []
        self.player_input = []
        self.round = 0
        self.state = SHOWING
        self.showing_index = 0
        self.showing_timer = time.time()

    def handle_click(self, pos):
        """处理鼠标点击"""
        if self.state == MENU:
            # 检查是否点击"开始游戏"
            self.start_game()
            return

        if self.state == GAME_OVER:
            # 重新开始
            self.start_game()
            return

        if self.state == INPUT:
            for i, btn in enumerate(self.buttons):
                if btn.contains_point(pos):
                    # 播放音效
                    play_sound(SOUNDS.get(btn.color_name))
                    btn.light_up()

                    expected = self.sequence[self.input_index]
                    if btn.color_name == expected:
                        self.input_index += 1
                        if self.input_index >= len(self.sequence):
                            # 本轮完成，开始下一轮
                            self.state = SHOWING
                            self.showing_index = 0
                            self.showing_timer = time.time()
                            self.player_input = []
                            self.input_index = 0
                    else:
                        # 答错了
                        play_sound(SOUND_FAIL)
                        self.state = GAME_OVER
                        if self.round > self.high_score:
                            self.high_score = self.round
                    break

    def update(self):
        """更新游戏状态"""
        for btn in self.buttons:
            btn.update()

        if self.state == SHOWING:
            now = time.time()
            if now - self.showing_timer > 0.5:
                self.showing_timer = now
                if self.showing_index < len(self.sequence):
                    # 熄灭所有灯
                    for btn in self.buttons:
                        btn.lit = False
                    # 点亮当前要显示的颜色
                    color_name = self.sequence[self.showing_index]
                    for btn in self.buttons:
                        if btn.color_name == color_name:
                            btn.light_up()
                            play_sound(SOUNDS.get(color_name))
                            break
                    self.showing_index += 1
                else:
                    # 显示完毕，等待玩家输入
                    for btn in self.buttons:
                        btn.lit = False
                    self.state = INPUT

    def draw_center(self, surface):
        """绘制中心圆"""
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30

        # 外圈
        pygame.draw.circle(surface, DARK_GRAY, (cx, cy), self.center_radius + 5)
        pygame.draw.circle(surface, BLACK, (cx, cy), self.center_radius)

        # 内圈
        inner_radius = self.center_radius - 10
        pygame.draw.circle(surface, (30, 30, 45), (cx, cy), inner_radius)

        # 文字
        if self.state == MENU:
            text = font_medium.render("西蒙说", True, WHITE)
            text_rect = text.get_rect(center=(cx, cy - 20))
            surface.blit(text, text_rect)

            text2 = font_small.render("点击开始", True, (180, 180, 200))
            text2_rect = text2.get_rect(center=(cx, cy + 20))
            surface.blit(text2, text2_rect)

        elif self.state == SHOWING:
            text = font_small.render("观 察", True, WHITE)
            text_rect = text.get_rect(center=(cx, cy))
            surface.blit(text, text_rect)

        elif self.state == INPUT:
            remaining = len(self.sequence) - self.input_index
            text = font_small.render(f"还剩 {remaining} 步", True, WHITE)
            text_rect = text.get_rect(center=(cx, cy))
            surface.blit(text, text_rect)

        elif self.state == GAME_OVER:
            text = font_medium.render("游戏结束", True, (255, 80, 80))
            text_rect = text.get_rect(center=(cx, cy - 20))
            surface.blit(text, text_rect)

            text2 = font_small.render("点击重新开始", True, (180, 180, 200))
            text2_rect = text2.get_rect(center=(cx, cy + 20))
            surface.blit(text2, text2_rect)

    def draw(self, surface):
        """绘制整个游戏画面"""
        surface.fill(BLACK)

        # 绘制背景装饰
        for i in range(4):
            color = COLORS[COLOR_NAMES[i]]["dark"]
            alpha_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            angle = i * math.pi / 2
            points = [(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)]
            for j in range(30):
                a = angle + (math.pi / 2) * j / 30
                points.append((
                    SCREEN_WIDTH // 2 + 300 * math.cos(a),
                    SCREEN_HEIGHT // 2 - 30 + 300 * math.sin(a)
                ))
            pygame.draw.polygon(alpha_surface, (*color, 30), points)
            surface.blit(alpha_surface, (0, 0))

        # 绘制四个色块
        for btn in self.buttons:
            btn.draw(surface)

        # 绘制中心圆
        self.draw_center(surface)

        # 绘制分数信息
        round_text = font_small.render(f"回合: {self.round}", True, WHITE)
        surface.blit(round_text, (20, 20))

        high_text = font_small.render(f"最高: {self.high_score}", True, (255, 215, 0))
        high_rect = high_text.get_rect(topright=(SCREEN_WIDTH - 20, 20))
        surface.blit(high_text, high_rect)

        # 游戏说明
        if self.state == MENU:
            info_lines = [
                "记住颜色序列！",
                "按相同顺序点击色块",
                "每轮序列加长，看看你能坚持几轮！",
            ]
            for i, line in enumerate(info_lines):
                info_text = font_tiny.render(line, True, (150, 150, 170))
                info_rect = info_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80 + i * 25))
                surface.blit(info_text, info_rect)
        elif self.state == GAME_OVER:
            seq_text = font_tiny.render(
                f"正确序列: {' → '.join(self.sequence)}", True, (200, 200, 200))
            seq_rect = seq_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))
            surface.blit(seq_text, seq_rect)

        pygame.display.flip()


def main():
    """主函数"""
    clock = pygame.time.Clock()
    game = SimonGame()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    game.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    game.start_game()

        game.update()
        game.draw(screen)
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()