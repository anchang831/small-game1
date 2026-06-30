"""
瞄准训练 (Aim Trainer) - 射击准度练习游戏
======================================
控制方式：鼠标点击目标
规则：在30秒内尽可能多地点击目标，考验你的瞄准速度和精度
特点：目标逐渐变小，连击加成，实时统计

运行: python aim_trainer.py
"""

import pygame
import random
import math
import time

# ========== 初始化 ==========
pygame.init()
pygame.font.init()

# ========== 常量 ==========
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GAME_DURATION = 30  # 游戏时长（秒）
BG_COLOR = (15, 15, 35)
TEXT_COLOR = (255, 255, 255)
ACCENT_COLOR = (0, 200, 255)
COMBO_COLOR = (255, 215, 0)

# ========== 屏幕 ==========
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("瞄准训练 Aim Trainer")
clock = pygame.time.Clock()

# ========== 字体 ==========
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 30)
font_tiny = pygame.font.Font(None, 22)


class Target:
    """目标类 - 屏幕上出现的可点击目标"""

    def __init__(self):
        self.radius = 40
        self.x = random.randint(self.radius + 10, SCREEN_WIDTH - self.radius - 10)
        self.y = random.randint(self.radius + 10, SCREEN_HEIGHT - self.radius - 10)
        self.color = (
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255),
        )
        self.birth_time = time.time()
        self.hit = False
        self.hit_time = 0
        self.pulse_phase = random.uniform(0, 2 * math.pi)

    def update(self, current_time):
        """更新目标动画"""
        self.pulse_phase += 0.05

    def draw(self, surface):
        """绘制目标"""
        if self.hit:
            # 命中后显示扩散动画
            elapsed = time.time() - self.hit_time
            if elapsed < 0.3:
                progress = elapsed / 0.3
                alpha = int(255 * (1 - progress))
                r = int(self.radius * (1 + progress * 2))
                # 使用白色扩散圈
                for i in range(3):
                    radius = int(r * (1 + i * 0.3))
                    pygame.draw.circle(surface, (255, 255, 255, alpha // (i + 1)),
                                       (int(self.x), int(self.y)), radius, max(1, 3 - i))
            return

        # 脉冲呼吸效果
        pulse = math.sin(self.pulse_phase) * 3
        draw_radius = int(self.radius + pulse)

        # 外发光
        glow_radius = draw_radius + 8
        for i in range(4):
            alpha = 30 - i * 7
            if alpha > 0:
                glow_color = (self.color[0], self.color[1], self.color[2], alpha)
                s = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, glow_color, (glow_radius, glow_radius), glow_radius - i * 2)
                surface.blit(s, (int(self.x - glow_radius), int(self.y - glow_radius)),
                             special_flags=pygame.BLEND_ALPHA_SDL2)

        # 主圆
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), draw_radius)

        # 内圈高光（3D效果）
        highlight_radius = draw_radius - 5
        pygame.draw.circle(surface, (255, 255, 255, 60),
                           (int(self.x - 3), int(self.y - 3)), highlight_radius, 2)

        # 瞄准十字中心
        cross_size = 6
        pygame.draw.line(surface, (255, 255, 255),
                         (int(self.x - cross_size), int(self.y)),
                         (int(self.x + cross_size), int(self.y)), 1)
        pygame.draw.line(surface, (255, 255, 255),
                         (int(self.x), int(self.y - cross_size)),
                         (int(self.x), int(self.y + cross_size)), 1)

    def is_clicked(self, pos):
        """检测是否被点击"""
        dx = pos[0] - self.x
        dy = pos[1] - self.y
        return dx * dx + dy * dy <= self.radius * self.radius

    def shrink(self, amount=3):
        """缩小目标（增加难度）"""
        self.radius = max(12, self.radius - amount)


class Particle:
    """命中特效粒子"""

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 8)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0
        self.decay = random.uniform(0.02, 0.04)
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15  # 重力
        self.life -= self.decay
        return self.life > 0

    def draw(self, surface):
        alpha = int(self.life * 255)
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (self.size, self.size), self.size)
        surface.blit(s, (int(self.x - self.size), int(self.y - self.size)),
                     special_flags=pygame.BLEND_ALPHA_SDL2)


class AimTrainer:
    """游戏主类"""

    def __init__(self):
        self.reset()

    def reset(self):
        """重置游戏状态"""
        self.score = 0
        self.hits = 0
        self.misses = 0
        self.combo = 0
        self.max_combo = 0
        self.start_time = 0
        self.time_left = GAME_DURATION
        self.game_state = "start"  # start, playing, ended
        self.targets = []
        self.particles = []
        self.floating_texts = []  # 飘字效果
        self.difficulty_level = 1
        self.total_shots = 0
        self.spawn_target()
        self.reaction_times = []
        self.last_target_spawn_time = 0
        self.show_combo_text = False
        self.combo_text_timer = 0

    def spawn_target(self):
        """生成新目标"""
        self.targets = [Target()]
        # 根据难度调整初始大小
        if self.difficulty_level > 1:
            self.targets[0].radius = max(12, 40 - (self.difficulty_level - 1) * 2)
        self.last_target_spawn_time = time.time()

    def handle_click(self, pos):
        """处理鼠标点击"""
        if self.game_state == "start":
            self.start_game()
            return

        if self.game_state != "playing":
            return

        self.total_shots += 1
        hit = False

        for target in self.targets[:]:
            if target.is_clicked(pos):
                # 命中
                reaction = time.time() - target.birth_time
                self.reaction_times.append(reaction)
                target.hit = True
                target.hit_time = time.time()
                self.hits += 1
                self.combo += 1
                self.max_combo = max(self.max_combo, self.combo)
                hit = True

                # 计算分数（含连击加成）
                base_score = 100
                combo_bonus = min(self.combo * 10, 100)
                difficulty_bonus = self.difficulty_level * 5
                score_gain = base_score + combo_bonus + difficulty_bonus
                self.score += score_gain

                # 粒子效果
                for _ in range(20):
                    self.particles.append(Particle(target.x, target.y, target.color))

                # 飘字
                combo_text = f"+{score_gain}"
                if self.combo >= 3:
                    combo_text += f" COMBOx{self.combo}!"
                self.floating_texts.append({
                    "text": combo_text,
                    "x": target.x,
                    "y": target.y,
                    "vy": -2,
                    "life": 1.0,
                    "color": COMBO_COLOR if self.combo >= 3 else (255, 255, 255),
                    "size": 28 if self.combo >= 3 else 22,
                })

                # 目标缩小（难度递增）
                if self.hits % 3 == 0 and self.targets[0].radius > 12:
                    self.targets[0].shrink(2)

                # 隔一段时间生成新目标
                break

        if not hit and self.game_state == "playing":
            self.misses += 1
            self.combo = 0
            # 点击miss特效
            self.floating_texts.append({
                "text": "MISS!",
                "x": pos[0],
                "y": pos[1],
                "vy": -2,
                "life": 1.0,
                "color": (255, 50, 50),
                "size": 24,
            })
            # 红色叉效果
            for _ in range(8):
                self.particles.append(Particle(pos[0], pos[1], (255, 50, 50)))

    def start_game(self):
        """开始游戏"""
        self.reset()
        self.game_state = "playing"
        self.start_time = time.time()

    def update(self):
        """每帧更新"""
        current_time = time.time()

        if self.game_state == "playing":
            elapsed = current_time - self.start_time
            self.time_left = max(0, GAME_DURATION - elapsed)

            # 难度递增
            self.difficulty_level = min(20, 1 + self.hits // 5)

            # 目标更新
            for target in self.targets[:]:
                target.update(current_time)
                if target.hit and current_time - target.hit_time > 0.3:
                    self.targets.remove(target)
                    self.spawn_target()

            # 时间到
            if self.time_left <= 0:
                self.game_state = "ended"

        # 粒子更新
        self.particles = [p for p in self.particles if p.update()]

        # 飘字更新
        for ft in self.floating_texts[:]:
            ft["y"] += ft["vy"]
            ft["life"] -= 0.02
            if ft["life"] <= 0:
                self.floating_texts.remove(ft)

    def draw_start_screen(self):
        """绘制开始界面"""
        # 背景
        screen.fill(BG_COLOR)

        # 网格背景
        self._draw_grid()

        # 标题
        title = font_large.render("🎯 瞄准训练", True, ACCENT_COLOR)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 180))
        screen.blit(title, title_rect)

        subtitle = font_medium.render("Aim Trainer", True, TEXT_COLOR)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 240))
        screen.blit(subtitle, subtitle_rect)

        # 说明
        instructions = [
            "点击屏幕上出现的 targets 得分",
            "连击越多，分数加成越高",
            "目标会随着得分增加而缩小",
            "游戏时长: 30秒",
        ]
        y_offset = 320
        for line in instructions:
            text = font_small.render(line, True, (180, 180, 200))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            screen.blit(text, text_rect)
            y_offset += 35

        # 开始提示
        blink = int((time.time() * 3) % 2)
        if blink:
            start_text = font_medium.render("点击任意位置开始", True, (255, 255, 100))
            start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, 480))
            screen.blit(start_text, start_rect)

        # 底部信息
        tip = font_tiny.render("鼠标左键点击目标 · 考验你的反应速度", True, (100, 100, 130))
        tip_rect = tip.get_rect(center=(SCREEN_WIDTH // 2, 560))
        screen.blit(tip, tip_rect)

    def draw_game_screen(self):
        """绘制游戏界面"""
        screen.fill(BG_COLOR)

        # 背景网格
        self._draw_grid()

        # 绘制粒子
        for p in self.particles:
            p.draw(screen)

        # 绘制目标
        for target in self.targets:
            target.draw(screen)

        # 绘制飘字
        for ft in self.floating_texts:
            alpha = int(ft["life"] * 255)
            font = pygame.font.Font(None, ft["size"])
            text = font.render(ft["text"], True, ft["color"])
            text.set_alpha(alpha)
            text_rect = text.get_rect(center=(int(ft["x"]), int(ft["y"])))
            screen.blit(text, text_rect)

        # HUD
        self._draw_hud()

    def draw_end_screen(self):
        """绘制结束界面"""
        screen.fill(BG_COLOR)
        self._draw_grid()

        # 标题
        over_text = font_large.render("⏱ 时间到!", True, ACCENT_COLOR)
        over_rect = over_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        screen.blit(over_text, over_rect)

        # 统计信息
        accuracy = (self.hits / self.total_shots * 100) if self.total_shots > 0 else 0
        avg_reaction = (sum(self.reaction_times) / len(self.reaction_times) * 1000) \
            if self.reaction_times else 0

        stats = [
            (f"最终得分", f"{self.score}"),
            (f"命中", f"{self.hits}"),
            (f"未命中", f"{self.misses}"),
            (f"命中率", f"{accuracy:.1f}%"),
            (f"最高连击", f"{self.max_combo}"),
            (f"平均反应时间", f"{avg_reaction:.0f} ms"),
            (f"难度等级", f"Lv.{self.difficulty_level}"),
        ]

        y_offset = 150
        for label, value in stats:
            label_text = font_small.render(label, True, (180, 180, 200))
            screen.blit(label_text, (SCREEN_WIDTH // 2 - 200, y_offset))

            value_text = font_small.render(value, True, COMBO_COLOR if "分" in label else TEXT_COLOR)
            screen.blit(value_text, (SCREEN_WIDTH // 2 + 50, y_offset))
            y_offset += 42

        # 评分等级
        grade = self._get_grade(accuracy, self.hits)
        grade_text = font_large.render(f"评级: {grade}", True, ACCENT_COLOR)
        grade_rect = grade_text.get_rect(center=(SCREEN_WIDTH // 2, 460))
        screen.blit(grade_text, grade_rect)

        # 重新开始
        restart_text = font_medium.render("点击重新开始", True, (255, 255, 100))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, 530))
        screen.blit(restart_text, restart_rect)

    def _draw_grid(self):
        """绘制背景网格"""
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(screen, (25, 25, 50), (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(screen, (25, 25, 50), (0, y), (SCREEN_WIDTH, y), 1)

    def _draw_hud(self):
        """绘制游戏HUD"""
        # 时间
        time_color = (255, 80, 80) if self.time_left <= 5 else TEXT_COLOR
        time_text = font_medium.render(f"{int(self.time_left // 60)}:{int(self.time_left % 60):02d}",
                                       True, time_color)
        screen.blit(time_text, (20, 15))

        # 分数
        score_text = font_medium.render(f"得分: {self.score}", True, TEXT_COLOR)
        score_rect = score_text.get_rect(midtop=(SCREEN_WIDTH // 2, 15))
        screen.blit(score_text, score_rect)

        # 连击
        if self.combo >= 3:
            combo_text = font_small.render(f"🔥 连击 x{self.combo}", True, COMBO_COLOR)
            combo_rect = combo_text.get_rect(midtop=(SCREEN_WIDTH // 2, 60))
            screen.blit(combo_text, combo_rect)

        # 命中率
        accuracy = (self.hits / self.total_shots * 100) if self.total_shots > 0 else 0
        acc_text = font_small.render(f"命中率: {accuracy:.0f}% | 命中: {self.hits} | 未命中: {self.misses}",
                                     True, (180, 180, 200))
        acc_rect = acc_text.get_rect(topright=(SCREEN_WIDTH - 20, 20))
        screen.blit(acc_text, acc_rect)

        # 难度
        diff_text = font_tiny.render(f"难度 Lv.{self.difficulty_level}", True, (120, 120, 150))
        screen.blit(diff_text, (20, 60))

        # 进度条
        progress = self.time_left / GAME_DURATION
        bar_width = 200
        bar_height = 6
        bar_x = SCREEN_WIDTH - bar_width - 20
        bar_y = SCREEN_HEIGHT - 30
        pygame.draw.rect(screen, (50, 50, 70), (bar_x, bar_y, bar_width, bar_height), border_radius=3)
        if progress > 0:
            bar_color = (255, 80, 80) if self.time_left <= 5 else ACCENT_COLOR
            pygame.draw.rect(screen, bar_color,
                             (bar_x, bar_y, int(bar_width * progress), bar_height), border_radius=3)

    def _get_grade(self, accuracy, hits):
        """根据表现评分"""
        score = self.score
        if score >= 5000 and accuracy >= 90:
            return "S+"
        elif score >= 3500 and accuracy >= 80:
            return "S"
        elif score >= 2500 and accuracy >= 70:
            return "A"
        elif score >= 1500 and accuracy >= 60:
            return "B"
        elif score >= 800 and accuracy >= 40:
            return "C"
        else:
            return "D"

    def draw(self):
        """绘制当前帧"""
        if self.game_state == "start":
            self.draw_start_screen()
        elif self.game_state == "playing":
            self.draw_game_screen()
        elif self.game_state == "ended":
            self.draw_end_screen()

        pygame.display.flip()

    def run(self):
        """游戏主循环"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键
                        self.handle_click(event.pos)

            self.update()
            self.draw()
            clock.tick(FPS)

        pygame.quit()


# ========== 程序入口 ==========
if __name__ == "__main__":
    game = AimTrainer()
    game.run()