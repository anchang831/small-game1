"""
猜单词游戏 (Hangman) - 经典刽子手猜单词游戏
使用 Pygame 实现，单文件运行，无外部依赖
玩法：根据提示类别，猜出隐藏单词的所有字母，猜错6次即失败
"""

import pygame
import random
import math

# ------------------------------
# 初始化 Pygame
# ------------------------------
pygame.init()
pygame.font.init()

# ------------------------------
# 游戏配置
# ------------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 680
FPS = 60

# 颜色常量
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
LIGHT_BLUE = (173, 216, 230)
BLUE = (70, 130, 180)
DARK_BLUE = (30, 60, 120)
RED = (220, 50, 50)
GREEN = (50, 180, 80)
ORANGE = (255, 165, 0)
PURPLE = (150, 50, 200)
BG_COLOR = (245, 245, 255)
BUTTON_COLOR = (220, 220, 250)
BUTTON_HOVER = (180, 180, 230)
BUTTON_DISABLED = (180, 180, 180)
HANGMAN_COLOR = (60, 60, 60)

# ------------------------------
# 词库 - 按类别分组
# ------------------------------
WORD_CATEGORIES = {
    "动物": [
        "ELEPHANT", "GIRAFFE", "PENGUIN", "DOLPHIN", "KANGAROO",
        "CHAMELEON", "OCTOPUS", "FLAMINGO", "CHEETAH", "ORANGUTAN",
        "BUTTERFLY", "SCORPION", "PARROT", "LEOPARD", "RHINOCEROS",
    ],
    "水果": [
        "STRAWBERRY", "BLUEBERRY", "WATERMELON", "PINEAPPLE", "DRAGONFRUIT",
        "POMEGRANATE", "MANGO", "PAPAYA", "COCONUT", "LYCHEE",
    ],
    "国家": [
        "AUSTRALIA", "ARGENTINA", "PORTUGAL", "PHILIPPINES", "NETHERLANDS",
        "SWITZERLAND", "SINGAPORE", "MALAYSIA", "VENEZUELA", "KAZAKHSTAN",
    ],
    "运动": [
        "FOOTBALL", "BASKETBALL", "VOLLEYBALL", "BADMINTON", "SWIMMING",
        "SKATEBOARD", "SNOWBOARD", "GYMNASTICS", "MARATHON", "FENCING",
    ],
    "科技": [
        "KEYBOARD", "MONITOR", "ALGORITHM", "DATABASE", "BLUETOOTH",
        "MICROCHIP", "FIBEROPTIC", "ROBOTICS", "CLOUDCOMPUTING", "VIRTUALREALITY",
    ],
}

# 将所有单词展平用于随机选择（含类别信息）
ALL_WORDS = []
for cat, words in WORD_CATEGORIES.items():
    for w in words:
        ALL_WORDS.append((cat, w))


# ------------------------------
# 游戏状态类
# ------------------------------
class HangmanGame:
    def __init__(self):
        self.reset()

    def reset(self):
        """重置游戏状态"""
        # 随机选词
        category, word = random.choice(ALL_WORDS)
        self.category = category
        self.word = word
        self.guessed_letters = set()
        self.wrong_guesses = 0
        self.max_wrong = 6
        self.revealed = ["_" if c.isalpha() else c for c in word]
        self.game_over = False
        self.won = False
        self.used_letters = set()
        self.score = 0
        self.category_boxes = []  # 类别选择按钮

    def guess(self, letter):
        """猜测一个字母"""
        letter = letter.upper()
        if len(letter) != 1 or not letter.isalpha():
            return False
        if letter in self.used_letters or self.game_over:
            return False

        self.used_letters.add(letter)

        if letter in self.word:
            # 正确猜测
            for i, ch in enumerate(self.word):
                if ch == letter:
                    self.revealed[i] = letter
            # 检查是否胜利
            if "_" not in self.revealed:
                self.game_over = True
                self.won = True
                # 根据剩余错误次数加分
                self.score = max(1, 6 - self.wrong_guesses) * 10
            return True
        else:
            # 错误猜测
            self.wrong_guesses += 1
            if self.wrong_guesses >= self.max_wrong:
                self.game_over = True
                self.won = False
                self.score = 0
            return False

    def get_hint(self):
        """获取提示：显示一个未猜中的字母"""
        unrevealed = [c for c in self.word if c.isalpha() and c not in self.used_letters]
        if unrevealed:
            hint_letter = random.choice(unrevealed)
            return hint_letter
        return None


# ------------------------------
# 绘制函数
# ------------------------------
def draw_hangman(screen, wrong_guesses):
    """根据错误次数绘制绞刑架和小人"""
    base_x, base_y = 150, 480
    center_x, center_y = 150, 300

    # 底座
    pygame.draw.line(screen, HANGMAN_COLOR, (80, base_y), (220, base_y), 6)
    pygame.draw.line(screen, HANGMAN_COLOR, (120, base_y), (120, 120), 6)
    pygame.draw.line(screen, HANGMAN_COLOR, (120, 120), (200, 120), 6)
    pygame.draw.line(screen, HANGMAN_COLOR, (200, 120), (200, 180), 4)

    if wrong_guesses >= 1:
        # 头
        pygame.draw.circle(screen, HANGMAN_COLOR, (200, 210), 30, 4)
    if wrong_guesses >= 2:
        # 身体
        pygame.draw.line(screen, HANGMAN_COLOR, (200, 240), (200, 360), 4)
    if wrong_guesses >= 3:
        # 左臂
        pygame.draw.line(screen, HANGMAN_COLOR, (200, 260), (155, 310), 4)
    if wrong_guesses >= 4:
        # 右臂
        pygame.draw.line(screen, HANGMAN_COLOR, (200, 260), (245, 310), 4)
    if wrong_guesses >= 5:
        # 左腿
        pygame.draw.line(screen, HANGMAN_COLOR, (200, 360), (155, 420), 4)
    if wrong_guesses >= 6:
        # 右腿
        pygame.draw.line(screen, HANGMAN_COLOR, (200, 360), (245, 420), 4)


def draw_word_display(screen, revealed, font_large):
    """绘制单词显示区域"""
    word_str = " ".join(revealed)
    text = font_large.render(word_str, True, DARK_BLUE)
    text_rect = text.get_rect(center=(480, 240))
    screen.blit(text, text_rect)


def draw_category(screen, category, font_medium):
    """绘制类别提示"""
    cat_text = f"类别: {category}"
    text = font_medium.render(cat_text, True, PURPLE)
    text_rect = text.get_rect(center=(480, 180))
    screen.blit(text, text_rect)


def draw_used_letters(screen, used_letters, wrong_guesses, font_small, font_tiny):
    """绘制已猜测的字母"""
    # 正确字母
    # 错误字母
    wrong = [l for l in used_letters if l.isalpha()]
    # 判断对错
    # 由于我们无法在这里判断，已经在游戏逻辑中处理了

    # 显示错误计数
    err_text = font_small.render(f"错误: {wrong_guesses}/6", True, RED)
    err_rect = err_text.get_rect(center=(480, 410))
    screen.blit(err_text, err_rect)

    # 显示已用字母
    if used_letters:
        used_str = "已猜: " + ", ".join(sorted(used_letters))
        used_text = font_tiny.render(used_str, True, DARK_GRAY)
        used_rect = used_text.get_rect(center=(480, 450))
        screen.blit(used_text, used_rect)


def draw_keyboard(screen, game, font_small):
    """绘制虚拟键盘"""
    keys = "QWERTYUIOPASDFGHJKLZXCVBNM"
    start_x = 350
    start_y = 500
    key_w, key_h = 40, 40
    gap = 6

    # 三行键盘
    rows = [
        ("QWERTYUIOP", 0),
        ("ASDFGHJKL", 20),
        ("ZXCVBNM", 40),
    ]

    mouse_pos = pygame.mouse.get_pos()
    click_rects = []

    for row_str, offset_x in rows:
        row_count = len(row_str)
        total_width = row_count * (key_w + gap) - gap
        row_start_x = start_x + (390 - total_width) // 2 + offset_x

        for i, ch in enumerate(row_str):
            x = row_start_x + i * (key_w + gap)
            y = start_y + (offset_x // 20) * (key_h + gap)

            rect = pygame.Rect(x, y, key_w, key_h)

            # 颜色根据状态
            if ch in game.used_letters:
                if ch in game.word:
                    color = GREEN
                else:
                    color = RED
                text_color = WHITE
            elif rect.collidepoint(mouse_pos):
                color = BUTTON_HOVER
                text_color = BLACK
            else:
                color = BUTTON_COLOR
                text_color = BLACK

            pygame.draw.rect(screen, color, rect, border_radius=6)
            pygame.draw.rect(screen, DARK_GRAY, rect, 2, border_radius=6)

            letter_text = font_small.render(ch, True, text_color)
            letter_rect = letter_text.get_rect(center=rect.center)
            screen.blit(letter_text, letter_rect)

            click_rects.append((rect, ch))

    return click_rects


def draw_game_over(screen, game, font_large, font_medium, font_small):
    """绘制游戏结束画面"""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    if game.won:
        title = "恭喜通关!"
        title_color = GREEN
        score_text = f"得分: +{game.score}"
    else:
        title = "游戏结束"
        title_color = RED
        score_text = f"正确答案: {game.word}"

    title_surf = font_large.render(title, True, title_color)
    title_rect = title_surf.get_rect(center=(400, 250))
    screen.blit(title_surf, title_rect)

    score_surf = font_medium.render(score_text, True, WHITE)
    score_rect = score_surf.get_rect(center=(400, 320))
    screen.blit(score_surf, score_rect)

    # 重新开始按钮
    btn_rect = pygame.Rect(300, 400, 200, 60)
    mouse_pos = pygame.mouse.get_pos()
    btn_color = GREEN if btn_rect.collidepoint(mouse_pos) else (100, 200, 100)
    pygame.draw.rect(screen, btn_color, btn_rect, border_radius=12)
    pygame.draw.rect(screen, WHITE, btn_rect, 3, border_radius=12)

    btn_text = font_medium.render("再来一局", True, WHITE)
    btn_text_rect = btn_text.get_rect(center=btn_rect.center)
    screen.blit(btn_text, btn_text_rect)

    return btn_rect


def draw_hint_button(screen, font_small):
    """绘制提示按钮"""
    btn_rect = pygame.Rect(600, 430, 100, 36)
    mouse_pos = pygame.mouse.get_pos()
    btn_color = ORANGE if btn_rect.collidepoint(mouse_pos) else (240, 180, 80)
    pygame.draw.rect(screen, btn_color, btn_rect, border_radius=8)
    pygame.draw.rect(screen, DARK_GRAY, btn_rect, 2, border_radius=8)

    btn_text = font_small.render("提示", True, WHITE)
    btn_text_rect = btn_text.get_rect(center=btn_rect.center)
    screen.blit(btn_text, btn_text_rect)
    return btn_rect


def draw_title(screen, font_large):
    """绘制标题"""
    title = font_large.render("猜单词 Hangman", True, DARK_BLUE)
    title_rect = title.get_rect(center=(400, 50))
    screen.blit(title, title_rect)

    # 装饰线
    pygame.draw.line(screen, BLUE, (200, 75), (600, 75), 3)


def draw_info(screen, font_tiny, total_score):
    """绘制底部信息"""
    info = font_tiny.render(f"总分: {total_score}  |  点击字母或按键盘字母键猜词  |  ESC退出", True, DARK_GRAY)
    info_rect = info.get_rect(center=(400, 660))
    screen.blit(info, info_rect)


# ------------------------------
# 主函数
# ------------------------------
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("猜单词 Hangman")
    clock = pygame.time.Clock()

    # 字体
    font_large = pygame.font.Font(None, 72)
    font_medium = pygame.font.Font(None, 48)
    font_small = pygame.font.Font(None, 36)
    font_tiny = pygame.font.Font(None, 28)

    game = HangmanGame()
    running = True
    total_score = 0
    show_hint = False
    hint_letter = None
    hint_timer = 0

    while running:
        dt = clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        # 处理提示计时
        if hint_timer > 0:
            hint_timer -= dt
            if hint_timer <= 0:
                show_hint = False
                hint_letter = None

        # ---- 绘制 ----
        screen.fill(BG_COLOR)

        # 绘制标题
        draw_title(screen, font_large)

        # 绘制绞刑架
        draw_hangman(screen, game.wrong_guesses)

        # 绘制类别
        draw_category(screen, game.category, font_medium)

        # 绘制单词
        draw_word_display(screen, game.revealed, font_large)

        # 绘制已用字母/错误次数
        draw_used_letters(screen, game.used_letters, game.wrong_guesses, font_small, font_tiny)

        # 绘制虚拟键盘
        key_rects = draw_keyboard(screen, game, font_small)

        # 提示按钮
        hint_btn = draw_hint_button(screen, font_small)

        # 提示显示
        if show_hint and hint_letter:
            hint_surf = font_small.render(f"提示: 字母 '{hint_letter}'", True, ORANGE)
            hint_rect = hint_surf.get_rect(center=(480, 490))
            screen.blit(hint_surf, hint_rect)

        # 底部信息
        draw_info(screen, font_tiny, total_score)

        # 游戏结束覆盖层
        restart_btn = None
        if game.game_over:
            restart_btn = draw_game_over(screen, game, font_large, font_medium, font_small)

        pygame.display.flip()

        # ---- 事件处理 ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif not game.game_over:
                    if event.key == pygame.K_RETURN:
                        # 回车键提示
                        if not game.game_over:
                            hint = game.get_hint()
                            if hint:
                                hint_letter = hint
                                show_hint = True
                                hint_timer = 1500
                    elif event.key == pygame.K_BACKSPACE:
                        # 重置快捷键
                        game.reset()
                    else:
                        # 字母输入
                        key_name = pygame.key.name(event.key)
                        if len(key_name) == 1 and key_name.isalpha():
                            game.guess(key_name)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # 检查键盘按钮点击
                    if not game.game_over:
                        for rect, ch in key_rects:
                            if rect.collidepoint(mouse_pos):
                                game.guess(ch)
                                break

                        # 提示按钮
                        if hint_btn.collidepoint(mouse_pos):
                            hint = game.get_hint()
                            if hint:
                                hint_letter = hint
                                show_hint = True
                                hint_timer = 1500

                    # 重新开始按钮
                    if restart_btn and restart_btn.collidepoint(mouse_pos):
                        total_score += game.score
                        game.reset()
                        show_hint = False
                        hint_letter = None
                        hint_timer = 0

        # 游戏胜利时累积分数
        if game.game_over and game.won and game.score > 0:
            total_score += game.score
            game.score = 0  # 防止重复累加

    pygame.quit()


if __name__ == "__main__":
    main()