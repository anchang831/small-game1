"""
打字大战 (Typing War) - 一个单词打字练习游戏
===============================================
玩法: 单词从天空坠落，输入正确单词即可消除。
      打错或单词到达底部会扣生命。
      每消除10个单词难度提升一级。

操作: 直接键盘输入字母，按 Enter 确认输入
      按 Backspace 删除上一个字母
      按 ESC 暂停/继续

作者: AI 游戏生成器
日期: 2026-07-30
"""

import pygame
import random
import sys
from typing import List, Tuple

# ==================== 游戏配置 ====================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 颜色定义
BLACK = (20, 20, 30)
WHITE = (255, 255, 255)
RED = (255, 60, 60)
GREEN = (60, 255, 60)
BLUE = (60, 120, 255)
YELLOW = (255, 255, 80)
PURPLE = (200, 80, 255)
ORANGE = (255, 160, 40)
CYAN = (40, 255, 255)
PINK = (255, 100, 200)
GRAY = (100, 100, 120)
DARK_GRAY = (40, 40, 55)

# 单词颜色列表
WORD_COLORS = [RED, GREEN, BLUE, YELLOW, PURPLE, ORANGE, CYAN, PINK]

# 单词库（按难度分组）
WORDS_EASY = [
    "cat", "dog", "sun", "run", "big", "red", "hat", "pen", "cup", "bus",
    "fish", "bird", "tree", "book", "ball", "star", "rain", "door", "bell", "kite",
    "happy", "apple", "water", "house", "mouse", "tiger", "robot", "pizza", "music", "hello",
]

WORDS_MEDIUM = [
    "python", "gaming", "planet", "rocket", "silver", "shadow", "dragon", "magic", "ocean", "forest",
    "bridge", "castle", "garden", "island", "jungle", "knight", "light", "monkey", "night", "orange",
    "puzzle", "queen", "river", "school", "tiger", "umbrella", "valley", "window", "yellow", "zebra",
]

WORDS_HARD = [
    "adventure", "brilliant", "champion", "diamond", "elevator", "fantasy", "galaxy", "horizon", "infinite", "journey",
    "kingdom", "liberty", "mystery", "notebook", "octopus", "penguin", "rainbow", "sandwich", "thunder", "universe",
    "volcano", "whisper", "explorer", "crystal", "monster", "treasure", "victory", "warrior", "ancient", "battery",
]

WORDS_INSANE = [
    "atmosphere", "background", "catastrophe", "democracy", "efficiency", "fundamental", "geography", "historical",
    "identify", "knowledge", "laboratory", "magnificent", "nightmare", "observation", "particular", "question",
    "revolution", "satisfaction", "temperature", "understand", "vegetable", "watermelon", "yesterday", "zip",
    "championship", "extraordinary", "unbelievable", "contradiction", "misunderstanding", "characterization",
]


def get_word_list(level: int) -> List[str]:
    """根据当前难度等级返回单词列表"""
    if level <= 2:
        return WORDS_EASY
    elif level <= 4:
        return WORDS_EASY + WORDS_MEDIUM
    elif level <= 6:
        return WORDS_MEDIUM + WORDS_HARD
    elif level <= 8:
        return WORDS_HARD
    else:
        return WORDS_HARD + WORDS_INSANE


# ==================== 游戏对象 ====================

class FallingWord:
    """一个正在下落的单词"""

    def __init__(self, word: str, speed: float, x: float, y: float):
        self.word = word
        self.speed = speed
        self.x = x
        self.y = y
        self.color = random.choice(WORD_COLORS)
        self.font_size = max(24, 38 - len(word))
        self.font = pygame.font.Font(None, self.font_size)
        self.text_surface = self.font.render(word, True, self.color)
        self.rect = self.text_surface.get_rect(center=(x, y))
        self.alive = True

    def update(self) -> None:
        """更新位置"""
        self.y += self.speed
        self.rect.centery = int(self.y)

    def draw(self, screen: pygame.Surface) -> None:
        """绘制单词"""
        # 发光效果
        glow_surface = self.font.render(self.word, True, (*self.color[:3], 60))
        for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
            screen.blit(glow_surface, (self.rect.x + dx, self.rect.y + dy))
        screen.blit(self.text_surface, self.rect)

    def is_off_screen(self, screen_height: int) -> bool:
        """检查是否超出屏幕底部"""
        return self.y > screen_height + 30


class Particle:
    """消除单词时的粒子特效"""

    def __init__(self, x: float, y: float, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-8, 2)
        self.color = color
        self.size = random.randint(3, 8)
        self.life = 1.0
        self.decay = random.uniform(0.015, 0.035)

    def update(self) -> None:
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  # 重力
        self.life -= self.decay
        self.size = max(1, self.size - 0.1)

    def draw(self, screen: pygame.Surface) -> None:
        if self.life > 0:
            alpha = max(0, min(255, int(self.life * 255)))
            color = (*self.color[:3], alpha)
            surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (self.size, self.size), int(self.size))
            screen.blit(surf, (int(self.x - self.size), int(self.y - self.size)))


class ComboDisplay:
    """连击显示"""

    def __init__(self, count: int, x: float, y: float):
        self.count = count
        self.x = x
        self.y = y
        self.life = 1.0
        self.font = pygame.font.Font(None, 48 if count >= 5 else 36)

    def update(self) -> None:
        self.y -= 1.5
        self.life -= 0.02

    def draw(self, screen: pygame.Surface) -> None:
        if self.life > 0:
            alpha = int(self.life * 255)
            color = YELLOW if self.count >= 5 else WHITE
            text = f"{self.count}x 连击!" if self.count >= 3 else ""
            if text:
                surf = self.font.render(text, True, color)
                surf.set_alpha(alpha)
                rect = surf.get_rect(center=(int(self.x), int(self.y)))
                screen.blit(surf, rect)


class Background:
    """动态背景 - 星空效果"""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.stars = []
        for _ in range(100):
            self.stars.append({
                "x": random.randint(0, width),
                "y": random.randint(0, height),
                "speed": random.uniform(0.3, 1.5),
                "size": random.randint(1, 3),
                "brightness": random.randint(100, 255),
            })

    def update(self) -> None:
        for star in self.stars:
            star["y"] += star["speed"]
            if star["y"] > self.height:
                star["y"] = 0
                star["x"] = random.randint(0, self.width)

    def draw(self, screen: pygame.Surface) -> None:
        for star in self.stars:
            alpha = star["brightness"]
            surf = pygame.Surface((star["size"] * 2, star["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (alpha, alpha, alpha, alpha), (star["size"], star["size"]), star["size"])
            screen.blit(surf, (int(star["x"]), int(star["y"])))


# ==================== 主游戏类 ====================

class TypingWar:
    """打字大战主游戏"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("打字大战 - Typing War")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        self.font_tiny = pygame.font.Font(None, 24)

        self.reset_game()

    def reset_game(self) -> None:
        """重置游戏状态"""
        # 游戏状态
        self.score = 0
        self.lives = 3
        self.level = 1
        self.combo = 0
        self.max_combo = 0
        self.words_cleared = 0
        self.words_missed = 0

        # 游戏对象
        self.falling_words: List[FallingWord] = []
        self.particles: List[Particle] = []
        self.combo_displays: List[ComboDisplay] = []
        self.background = Background(SCREEN_WIDTH, SCREEN_HEIGHT)

        # 玩家输入
        self.player_input = ""
        self.input_active = True

        # 游戏状态
        self.paused = False
        self.game_over = False
        self.state = "playing"  # playing, paused, game_over

        # 生成参数
        self.spawn_timer = 0
        self.spawn_interval = 90  # 帧数间隔
        self.word_speed = 1.2

        # 输入错误提示
        self.input_error = False
        self.error_timer = 0

        # 统计
        self.total_spawned = 0
        self.accuracy = 0.0
        self.total_attempts = 0
        self.successful_attempts = 0

    def spawn_word(self) -> None:
        """生成一个新的下落单词"""
        word_list = get_word_list(self.level)
        word = random.choice(word_list)

        # 确保不生成已经在屏幕上的单词（避免重复）
        max_attempts = 10
        while max_attempts > 0 and any(w.word == word for w in self.falling_words):
            word = random.choice(word_list)
            max_attempts -= 1

        x = random.randint(80, SCREEN_WIDTH - 80)
        # 用当前速度乘以一个随机因子，让单词有不同速度
        speed = self.word_speed * random.uniform(0.8, 1.3)
        self.falling_words.append(FallingWord(word, speed, x, -30))
        self.total_spawned += 1

    def handle_input(self, event: pygame.event.Event) -> None:
        """处理键盘输入"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == "playing":
                    self.state = "paused"
                elif self.state == "paused":
                    self.state = "playing"
                return

            if self.state != "playing":
                return

            if event.key == pygame.K_BACKSPACE:
                if self.player_input:
                    self.player_input = self.player_input[:-1]
                    self.input_error = False
            elif event.key == pygame.K_RETURN:
                if self.player_input:
                    self.total_attempts += 1
                    self.check_word_match()
            elif event.key == pygame.K_SPACE:
                # 空格键输入空格，忽略
                pass
            else:
                # 输入字母
                char = event.unicode.lower()
                if char.isalpha():
                    self.player_input += char
                    self.input_error = False

    def check_word_match(self) -> None:
        """检查玩家输入的单词是否匹配"""
        matched = False
        for fw in self.falling_words:
            if fw.word == self.player_input and fw.alive:
                # 匹配成功！
                fw.alive = False
                self.words_cleared += 1
                self.combo += 1
                self.successful_attempts += 1
                matched = True

                # 计算分数（基础分 + 长度奖励 + 连击奖励）
                base_score = max(10, 5 * len(fw.word))
                combo_bonus = int(base_score * min(2.0, self.combo * 0.1))
                score_gain = base_score + combo_bonus
                self.score += score_gain

                # 更新最大连击
                if self.combo > self.max_combo:
                    self.max_combo = self.combo

                # 生成粒子特效
                for _ in range(15):
                    self.particles.append(Particle(fw.rect.centerx, fw.rect.centery, fw.color))

                # 显示连击
                if self.combo >= 3:
                    self.combo_displays.append(ComboDisplay(self.combo, fw.rect.centerx, fw.rect.centery))

                # 从列表移除
                self.falling_words.remove(fw)

                # 每消除10个单词升级
                if self.words_cleared % 10 == 0:
                    self.level_up()

                self.player_input = ""
                break

        if not matched:
            # 匹配失败
            self.combo = 0
            self.input_error = True
            self.error_timer = 30
            self.player_input = ""

    def level_up(self) -> None:
        """升级"""
        self.level += 1
        self.word_speed = min(4.0, 1.2 + self.level * 0.25)
        self.spawn_interval = max(25, 90 - self.level * 5)

    def update(self) -> None:
        """更新游戏状态"""
        if self.state != "playing":
            return

        # 更新背景
        self.background.update()

        # 更新错误计时器
        if self.input_error:
            self.error_timer -= 1
            if self.error_timer <= 0:
                self.input_error = False

        # 生成新单词
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            self.spawn_word()

        # 更新下落单词
        for fw in self.falling_words[:]:
            fw.update()
            if fw.is_off_screen(SCREEN_HEIGHT):
                self.falling_words.remove(fw)
                self.lives -= 1
                self.words_missed += 1
                self.combo = 0
                if self.lives <= 0:
                    self.game_over = True
                    self.state = "game_over"

        # 更新粒子
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

        # 更新连击显示
        for cd in self.combo_displays[:]:
            cd.update()
            if cd.life <= 0:
                self.combo_displays.remove(cd)

        # 计算准确率
        if self.total_attempts > 0:
            self.accuracy = (self.successful_attempts / self.total_attempts) * 100

    def draw(self) -> None:
        """绘制游戏画面"""
        self.screen.fill(BLACK)

        # 绘制背景星空
        self.background.draw(self.screen)

        if self.state == "game_over":
            self.draw_game_over()
        else:
            # 绘制下落单词
            for fw in self.falling_words:
                fw.draw(self.screen)

            # 绘制粒子
            for p in self.particles:
                p.draw(self.screen)

            # 绘制连击显示
            for cd in self.combo_displays:
                cd.draw(self.screen)

            # 绘制HUD
            self.draw_hud()

            # 绘制输入框
            self.draw_input_box()

            # 绘制暂停
            if self.state == "paused":
                self.draw_pause_overlay()

        pygame.display.flip()

    def draw_hud(self) -> None:
        """绘制顶部信息栏"""
        # 半透明背景
        hud_surf = pygame.Surface((SCREEN_WIDTH, 50), pygame.SRCALPHA)
        hud_surf.fill((0, 0, 0, 128))
        self.screen.blit(hud_surf, (0, 0))

        # 分数
        score_text = self.font_small.render(f"分数: {self.score}", True, WHITE)
        self.screen.blit(score_text, (15, 12))

        # 等级
        level_text = self.font_small.render(f"等级: {self.level}", True, CYAN)
        self.screen.blit(level_text, (200, 12))

        # 生命值（心形 ❤）
        lives_text = self.font_small.render(f"生命: {'❤' * self.lives}{'♡' * (3 - self.lives)}", True, RED)
        self.screen.blit(lives_text, (380, 12))

        # 连击
        if self.combo >= 2:
            combo_text = self.font_small.render(f"连击: {self.combo}x", True, YELLOW)
            combo_rect = combo_text.get_rect()
            combo_rect.right = SCREEN_WIDTH - 15
            combo_rect.top = 12
            self.screen.blit(combo_text, combo_rect)

        # 已消除/已出现
        stats_text = self.font_tiny.render(f"消除: {self.words_cleared} | 出现: {self.total_spawned}", True, GRAY)
        self.screen.blit(stats_text, (15, 40))

        # 准确率
        if self.total_attempts > 0:
            acc_text = self.font_tiny.render(f"准确率: {self.accuracy:.1f}%", True, GRAY)
            acc_rect = acc_text.get_rect()
            acc_rect.right = SCREEN_WIDTH - 15
            acc_rect.top = 40
            self.screen.blit(acc_text, acc_rect)

    def draw_input_box(self) -> None:
        """绘制输入框"""
        box_y = SCREEN_HEIGHT - 60
        box_height = 45
        box_width = 400
        box_x = (SCREEN_WIDTH - box_width) // 2

        # 输入框背景
        color = RED if self.input_error else (60, 60, 80)
        pygame.draw.rect(self.screen, color, (box_x, box_y, box_width, box_height), border_radius=8)
        pygame.draw.rect(self.screen, WHITE if self.input_active else GRAY, (box_x, box_y, box_width, box_height), 2, border_radius=8)

        # 输入文字
        display_text = self.player_input if self.player_input else "输入单词后按 Enter..."
        text_color = WHITE if self.player_input else GRAY
        text_surf = self.font_medium.render(display_text, True, text_color)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + box_height // 2))
        self.screen.blit(text_surf, text_rect)

        # 光标闪烁
        if self.state == "playing" and (pygame.time.get_ticks() // 500) % 2 == 0 and self.player_input:
            cursor_x = text_rect.right + 2
            cursor_y = box_y + 8
            pygame.draw.line(self.screen, WHITE, (cursor_x, cursor_y), (cursor_x, cursor_y + box_height - 16), 2)

        # 提示文字
        hint_text = self.font_tiny.render("输入单词 → Enter 确认 | Backspace 删除 | ESC 暂停", True, GRAY)
        hint_rect = hint_text.get_rect(center=(SCREEN_WIDTH // 2, box_y - 15))
        self.screen.blit(hint_text, hint_rect)

    def draw_pause_overlay(self) -> None:
        """绘制暂停遮罩"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # 暂停文字
        pause_text = self.font_large.render("游 戏 暂 停", True, WHITE)
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(pause_text, pause_rect)

        resume_text = self.font_small.render("按 ESC 继续游戏", True, GRAY)
        resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(resume_text, resume_rect)

    def draw_game_over(self) -> None:
        """绘制游戏结束画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # 标题
        title_text = self.font_large.render("游 戏 结 束", True, RED)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title_text, title_rect)

        # 游戏统计
        stats = [
            (f"最终分数: {self.score}", WHITE),
            (f"达到等级: {self.level}", CYAN),
            (f"消除单词: {self.words_cleared}", GREEN),
            (f"漏掉单词: {self.words_missed}", RED),
            (f"最大连击: {self.max_combo}x", YELLOW),
            (f"最高准确率: {self.accuracy:.1f}%", GRAY),
        ]

        y_offset = 200
        for text, color in stats:
            surf = self.font_medium.render(text, True, color)
            rect = surf.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(surf, rect)
            y_offset += 50

        # 评级
        rating = self.get_rating()
        rating_text = self.font_large.render(f"评级: {rating}", True, self.get_rating_color(rating))
        rating_rect = rating_text.get_rect(center=(SCREEN_WIDTH // 2, y_offset + 30))
        self.screen.blit(rating_text, rating_rect)

        # 提示重新开始
        restart_text = self.font_small.render("按 ENTER 重新开始 | 按 ESC 退出", True, GRAY)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        self.screen.blit(restart_text, restart_rect)

    def get_rating(self) -> str:
        """根据表现评级"""
        if self.score >= 5000 and self.accuracy >= 90:
            return "S"
        elif self.score >= 3000 and self.accuracy >= 80:
            return "A"
        elif self.score >= 1500 and self.accuracy >= 70:
            return "B"
        elif self.score >= 500:
            return "C"
        else:
            return "D"

    def get_rating_color(self, rating: str) -> Tuple[int, int, int]:
        colors = {"S": YELLOW, "A": GREEN, "B": CYAN, "C": ORANGE, "D": GRAY}
        return colors.get(rating, WHITE)

    def run(self) -> None:
        """主游戏循环"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if self.state == "game_over":
                        if event.key == pygame.K_RETURN:
                            self.reset_game()
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                            pygame.quit()
                            sys.exit()
                    else:
                        self.handle_input(event)

            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


# ==================== 启动入口 ====================
if __name__ == "__main__":
    game = TypingWar()
    game.run()