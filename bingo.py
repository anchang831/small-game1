"""
宾果游戏 (Bingo) - 经典数字宾果对战
- 玩家 vs AI 电脑
- 5x5 宾果卡片
- B(1-15) I(16-30) N(31-45) G(46-60) O(61-75)
- 先完成一行/列/对角线者获胜
"""

import pygame
import random
import sys

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 60, 60)
GREEN = (60, 200, 60)
BLUE = (60, 120, 255)
YELLOW = (255, 220, 50)
PURPLE = (180, 60, 255)
ORANGE = (255, 160, 40)
GRAY = (180, 180, 180)
DARK = (40, 40, 60)
LIGHT_BLUE = (200, 220, 255)
LIGHT_GREEN = (200, 255, 200)
LIGHT_RED = (255, 200, 200)
GOLD = (255, 215, 0)

# 窗口设置
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 680
CARD_SIZE = 5
CELL_SIZE = 64
CARD_X_OFFSET = 60
CARD_Y_OFFSET = 120
AI_CARD_X_OFFSET = 520
AI_CARD_Y_OFFSET = 120
LABEL_COLORS = {
    'B': (255, 80, 80),
    'I': (255, 200, 50),
    'N': (80, 200, 80),
    'G': (80, 150, 255),
    'O': (200, 100, 255),
}


class BingoCard:
    """宾果卡片类"""

    def __init__(self, is_ai=False):
        self.is_ai = is_ai
        self.grid = [[0] * CARD_SIZE for _ in range(CARD_SIZE)]
        self.marked = [[False] * CARD_SIZE for _ in range(CARD_SIZE)]
        self._generate()

    def _generate(self):
        """生成随机宾果卡片"""
        ranges = [(1, 15), (16, 30), (31, 45), (46, 60), (61, 75)]
        for col in range(CARD_SIZE):
            numbers = random.sample(range(ranges[col][0], ranges[col][1] + 1), CARD_SIZE)
            for row in range(CARD_SIZE):
                self.grid[row][col] = numbers[row]
        # 中央是FREE空间
        self.marked[2][2] = True
        self.grid[2][2] = 0

    def mark_number(self, num):
        """标记叫到的数字"""
        for row in range(CARD_SIZE):
            for col in range(CARD_SIZE):
                if self.grid[row][col] == num and not self.marked[row][col]:
                    self.marked[row][col] = True
                    return True
        return False

    def check_bingo(self):
        """检查是否达成宾果"""
        # 检查行
        for row in range(CARD_SIZE):
            if all(self.marked[row][col] for col in range(CARD_SIZE)):
                return True, ('row', row)
        # 检查列
        for col in range(CARD_SIZE):
            if all(self.marked[row][col] for row in range(CARD_SIZE)):
                return True, ('col', col)
        # 检查对角线
        if all(self.marked[i][i] for i in range(CARD_SIZE)):
            return True, ('diag', 0)
        if all(self.marked[i][CARD_SIZE - 1 - i] for i in range(CARD_SIZE)):
            return True, ('diag', 1)
        return False, None

    def get_marked_count(self):
        """获取已标记数量"""
        return sum(sum(row) for row in self.marked)


class BingoGame:
    """宾果游戏主类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("宾果 Bingo")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont('simhei', 48, bold=True)
        self.font_medium = pygame.font.SysFont('simhei', 32, bold=True)
        self.font_small = pygame.font.SysFont('simhei', 24)
        self.font_tiny = pygame.font.SysFont('simhei', 18)
        self.font_number = pygame.font.SysFont('arial', 22, bold=True)

        self.player_card = BingoCard(is_ai=False)
        self.ai_card = BingoCard(is_ai=True)
        self.called_numbers = []
        self.current_number = None
        self.animating_number = False
        self.anim_timer = 0
        self.game_over = False
        self.winner = None  # 'player', 'ai', 'draw'
        self.win_line = None
        self.win_owner = None
        self.flash_timer = 0
        self.message = "点击 SPACE 开始叫号"
        self.message_timer = 0
        self.ai_mark_delay = 0
        self.ai_marking = False
        self.round = 0

        # 尝试加载中文字体，如果失败用系统字体
        self._init_fonts()

    def _init_fonts(self):
        """初始化字体"""
        chinese_fonts = ['simhei', 'simsun', 'msyh', 'notosanscjk', 'wqy-zenhei', 'wqy-microhei']
        for font_name in chinese_fonts:
            try:
                test_font = pygame.font.SysFont(font_name, 16)
                test_surf = test_font.render('测试', True, BLACK)
                if test_surf.get_width() > 0:
                    self.font_large = pygame.font.SysFont(font_name, 48, bold=True)
                    self.font_medium = pygame.font.SysFont(font_name, 32, bold=True)
                    self.font_small = pygame.font.SysFont(font_name, 24)
                    self.font_tiny = pygame.font.SysFont(font_name, 18)
                    return
            except:
                continue

    def call_number(self):
        """叫一个数字"""
        available = [n for n in range(1, 76) if n not in self.called_numbers]
        if not available:
            return None
        num = random.choice(available)
        self.called_numbers.append(num)
        self.current_number = num
        self.animating_number = True
        self.anim_timer = 60
        self.round += 1
        return num

    def get_column_label(self, num):
        """获取数字对应的列标签"""
        if num <= 15:
            return 'B'
        elif num <= 30:
            return 'I'
        elif num <= 45:
            return 'N'
        elif num <= 60:
            return 'G'
        else:
            return 'O'

    def draw_card(self, card, x_offset, y_offset, label, reveal=False):
        """绘制宾果卡片"""
        # 标题
        title_color = GREEN if label == '玩家' else RED
        title = self.font_medium.render(label, True, title_color)
        self.screen.blit(title, (x_offset + 60, y_offset - 40))

        # 列标签
        for col in range(CARD_SIZE):
            letter = ['B', 'I', 'N', 'G', 'O'][col]
            color = LABEL_COLORS[letter]
            lbl = self.font_medium.render(letter, True, color)
            lx = x_offset + col * CELL_SIZE + CELL_SIZE // 2 - lbl.get_width() // 2
            self.screen.blit(lbl, (lx, y_offset - 5))

        # 绘制格子
        for row in range(CARD_SIZE):
            for col in range(CARD_SIZE):
                x = x_offset + col * CELL_SIZE
                y = y_offset + row * CELL_SIZE + 30

                # 格子背景
                is_marked = card.marked[row][col]
                is_free = (row == 2 and col == 2)

                if is_free:
                    bg_color = GOLD
                elif is_marked:
                    bg_color = (100, 255, 100) if not card.is_ai else (255, 150, 150)
                else:
                    bg_color = WHITE

                pygame.draw.rect(self.screen, bg_color, (x, y, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(self.screen, DARK, (x, y, CELL_SIZE, CELL_SIZE), 2)

                # 数字
                num = card.grid[row][col]
                if is_free:
                    text = self.font_tiny.render('FREE', True, BLACK)
                    tx = x + CELL_SIZE // 2 - text.get_width() // 2
                    ty = y + CELL_SIZE // 2 - text.get_height() // 2
                    self.screen.blit(text, (tx, ty))
                elif num > 0:
                    if reveal or not card.is_ai:
                        text = self.font_number.render(str(num), True, BLACK)
                        tx = x + CELL_SIZE // 2 - text.get_width() // 2
                        ty = y + CELL_SIZE // 2 - text.get_height() // 2
                        self.screen.blit(text, (tx, ty))
                    else:
                        # AI 卡片隐藏
                        text = self.font_tiny.render('?', True, GRAY)
                        tx = x + CELL_SIZE // 2 - text.get_width() // 2
                        ty = y + CELL_SIZE // 2 - text.get_height() // 2
                        self.screen.blit(text, (tx, ty))

        # 已标记数量
        count = card.get_marked_count()
        count_text = self.font_tiny.render(f"已标记: {count}/24", True, DARK)
        self.screen.blit(count_text, (x_offset + 20, y_offset + CARD_SIZE * CELL_SIZE + 40))

    def draw_ball(self, num, x, y, radius, highlight=False):
        """绘制数字球"""
        label = self.get_column_label(num)
        color = LABEL_COLORS[label]

        # 阴影
        pygame.draw.circle(self.screen, (0, 0, 0, 80), (x + 3, y + 3), radius)

        # 主球体
        pygame.draw.circle(self.screen, color, (x, y), radius)
        pygame.draw.circle(self.screen, WHITE, (x, y), radius, 2)

        # 高光
        if highlight:
            pygame.draw.circle(self.screen, YELLOW, (x, y), radius + 4, 3)

        # 数字
        text = self.font_medium.render(f"{label}{num}", True, WHITE)
        tx = x - text.get_width() // 2
        ty = y - text.get_height() // 2
        self.screen.blit(text, (tx, ty))

    def draw_ui(self):
        """绘制界面"""
        # 背景
        self.screen.fill(DARK)

        # 顶部标题
        title = self.font_large.render("🎯 宾果 BINGO", True, GOLD)
        tx = WINDOW_WIDTH // 2 - title.get_width() // 2
        self.screen.blit(title, (tx, 15))

        # 当前叫号区域
        current_x = WINDOW_WIDTH // 2
        current_y = 90

        # 已叫号码数量
        count_text = self.font_tiny.render(f"已叫号: {len(self.called_numbers)}/75", True, WHITE)
        self.screen.blit(count_text, (current_x - count_text.get_width() // 2, current_y - 25))

        if self.current_number:
            pygame.draw.circle(self.screen, BLACK, (current_x + 2, current_y + 2), 35)
            self.draw_ball(self.current_number, current_x, current_y, 35, self.animating_number)

        # 玩家卡片
        self.draw_card(self.player_card, CARD_X_OFFSET, CARD_Y_OFFSET, '玩家')

        # AI 卡片
        self.draw_card(self.ai_card, AI_CARD_X_OFFSET, AI_CARD_Y_OFFSET, 'AI 电脑', reveal=False)

        # 分隔线
        pygame.draw.line(self.screen, GRAY, (480, 100), (480, WINDOW_HEIGHT - 20), 2)

        # 消息
        if self.message:
            msg_color = GREEN if 'win' in self.message.lower() or '获胜' in self.message else (
                RED if '输' in self.message else WHITE)
            msg = self.font_small.render(self.message, True, msg_color)
            mx = WINDOW_WIDTH // 2 - msg.get_width() // 2
            my = WINDOW_HEIGHT - 40
            self.screen.blit(msg, (mx, my))

        # 操作提示
        if not self.game_over:
            hint = self.font_tiny.render("SPACE: 叫号 | R: 重新开始 | ESC: 退出", True, GRAY)
            hx = WINDOW_WIDTH // 2 - hint.get_width() // 2
            self.screen.blit(hint, (hx, WINDOW_HEIGHT - 20))

        # 最近叫号历史
        history_x = 10
        history_y = 550
        history_label = self.font_tiny.render("最近叫号:", True, WHITE)
        self.screen.blit(history_label, (history_x, history_y))

        recent = self.called_numbers[-10:] if len(self.called_numbers) > 10 else self.called_numbers
        for i, num in enumerate(recent):
            label = self.get_column_label(num)
            color = LABEL_COLORS[label]
            pygame.draw.circle(self.screen, color, (history_x + 20 + i * 38, history_y + 30), 14)
            t = self.font_tiny.render(f"{label}{num}", True, WHITE)
            tx = history_x + 20 + i * 38 - t.get_width() // 2
            ty = history_y + 30 - t.get_height() // 2
            self.screen.blit(t, (tx, ty))

    def check_winner(self):
        """检查获胜者"""
        player_bingo, player_line = self.player_card.check_bingo()
        ai_bingo, ai_line = self.ai_card.check_bingo()

        if player_bingo and ai_bingo:
            return 'draw', None
        elif player_bingo:
            return 'player', player_line
        elif ai_bingo:
            return 'ai', ai_line
        return None, None

    def ai_turn(self):
        """AI 自动标记"""
        if self.current_number:
            self.ai_card.mark_number(self.current_number)
            self.ai_marking = True

    def reset_game(self):
        """重置游戏"""
        self.player_card = BingoCard(is_ai=False)
        self.ai_card = BingoCard(is_ai=True)
        self.called_numbers = []
        self.current_number = None
        self.animating_number = False
        self.anim_timer = 0
        self.game_over = False
        self.winner = None
        self.win_line = None
        self.win_owner = None
        self.flash_timer = 0
        self.message = "点击 SPACE 开始叫号"
        self.message_timer = 0
        self.ai_mark_delay = 0
        self.ai_marking = False
        self.round = 0

    def run(self):
        """游戏主循环"""
        running = True
        while running:
            self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        if self.game_over:
                            self.reset_game()
                    elif event.key == pygame.K_SPACE and not self.game_over and not self.animating_number:
                        if len(self.called_numbers) < 75:
                            num = self.call_number()
                            if num:
                                # 玩家标记
                                self.player_card.mark_number(num)
                                # AI标记
                                self.ai_card.mark_number(num)
                                self.message = ""

                                # 检查胜负
                                winner, win_line = self.check_winner()
                                if winner:
                                    self.game_over = True
                                    self.winner = winner
                                    self.win_line = win_line
                                    if winner == 'player':
                                        self.message = "🎉 恭喜你获胜！按 R 重新开始"
                                    elif winner == 'ai':
                                        self.message = "😞 AI 获胜！按 R 重新开始"
                                    else:
                                        self.message = "🤝 平局！按 R 重新开始"
                                else:
                                    # 显示当前叫号
                                    label = self.get_column_label(num)
                                    self.message = f"叫号: {label}{num}"
                        else:
                            self.message = "所有号码已叫完！"

            # 动画更新
            if self.animating_number:
                self.anim_timer -= 1
                if self.anim_timer <= 0:
                    self.animating_number = False

            # 绘制
            self.draw_ui()

            # 游戏结束闪烁效果
            if self.game_over:
                self.flash_timer += 1
                if self.flash_timer % 30 < 15:
                    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                    overlay.set_alpha(60)
                    if self.winner == 'player':
                        overlay.fill((0, 200, 0))
                    elif self.winner == 'ai':
                        overlay.fill((200, 0, 0))
                    else:
                        overlay.fill((200, 200, 0))
                    self.screen.blit(overlay, (0, 0))

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    game = BingoGame()
    game.run()