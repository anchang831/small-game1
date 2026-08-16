"""
Yahtzee (快艇骰子) - 经典骰子组合计分游戏
=============================
玩法：掷5个骰子，每轮最多3次重掷机会，
选择计分类别获得分数，13轮后总分最高者获胜。
单人游戏，挑战高分！

操作：
- 点击骰子锁定/解锁（重掷时保留）
- 点击"掷骰子"按钮投掷
- 点击右侧计分表选择计分类别
"""

import pygame
import random
import sys

# ==================== 常量 ====================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 680
FPS = 60

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
LIGHT_GRAY = (240, 240, 240)
RED = (220, 50, 50)
GREEN = (50, 180, 80)
BLUE = (50, 100, 220)
DARK_BLUE = (30, 60, 160)
YELLOW = (255, 200, 50)
ORANGE = (255, 140, 0)
PURPLE = (160, 50, 200)
BG_COLOR = (30, 30, 50)
DICE_COLORS = [
    (240, 60, 60),   # 1 - 红
    (60, 200, 60),   # 2 - 绿
    (60, 100, 240),  # 3 - 蓝
    (240, 200, 20),  # 4 - 黄
    (240, 120, 40),  # 5 - 橙
    (180, 60, 220),  # 6 - 紫
]

# 计分类别
CATEGORIES = [
    ("ones", "点数1", 0),
    ("twos", "点数2", 1),
    ("threes", "点数3", 2),
    ("fours", "点数4", 3),
    ("fives", "点数5", 4),
    ("sixes", "点数6", 5),
    ("three_kind", "三条", 6),
    ("four_kind", "四条", 7),
    ("full_house", "葫芦", 8),
    ("small_straight", "小顺", 9),
    ("large_straight", "大顺", 10),
    ("yahtzee", "快艇", 11),
    ("chance", "幸运", 12),
]

# 计分规则说明
CATEGORY_DESC = {
    "ones": "只计点数1的骰子之和",
    "twos": "只计点数2的骰子之和",
    "threes": "只计点数3的骰子之和",
    "fours": "只计点数4的骰子之和",
    "fives": "只计点数5的骰子之和",
    "sixes": "只计点数6的骰子之和",
    "three_kind": "至少3个相同，计所有骰子之和",
    "four_kind": "至少4个相同，计所有骰子之和",
    "full_house": "3个相同+2个相同，得25分",
    "small_straight": "4个连续点数，得30分",
    "large_straight": "5个连续点数，得40分",
    "yahtzee": "5个相同，得50分",
    "chance": "计所有骰子之和",
}


# ==================== 骰子类 ====================
class Die:
    """单个骰子"""
    SIZE = 80
    PADDING = 8
    DOT_RADIUS = 6

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.value = 1
        self.locked = False
        self.rect = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.roll_animation = 0

    def roll(self):
        """随机掷骰子"""
        if not self.locked:
            self.value = random.randint(1, 6)
            self.roll_animation = 8

    def update(self):
        """更新动画"""
        if self.roll_animation > 0:
            self.roll_animation -= 1
            if self.roll_animation % 2 == 0:
                self.value = random.randint(1, 6)

    def draw(self, screen):
        """绘制骰子"""
        color = DICE_COLORS[self.value - 1] if not self.locked else DARK_GRAY
        # 骰子背景
        rect = self.rect.inflate(-4, -4)
        shadow_rect = rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(screen, (0, 0, 0, 80), shadow_rect, border_radius=10)
        pygame.draw.rect(screen, color, rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, rect, 2, border_radius=10)

        # 锁定标记
        if self.locked:
            lock_font = pygame.font.SysFont("simhei", 20)
            lock_text = lock_font.render("🔒", True, WHITE)
            screen.blit(lock_text, (self.x + self.SIZE - 28, self.y + 2))

        # 骰子点数
        dot_positions = self._get_dot_positions()
        for dx, dy in dot_positions:
            cx = self.x + self.SIZE // 2 + dx
            cy = self.y + self.SIZE // 2 + dy
            pygame.draw.circle(screen, WHITE, (cx, cy), self.DOT_RADIUS)

    def _get_dot_positions(self):
        """根据骰子值返回圆点位置"""
        cx, cy = 0, 0
        r = self.DOT_RADIUS
        s = self.SIZE // 4
        positions = {
            1: [(0, 0)],
            2: [(-s, -s), (s, s)],
            3: [(-s, -s), (0, 0), (s, s)],
            4: [(-s, -s), (s, -s), (-s, s), (s, s)],
            5: [(-s, -s), (s, -s), (0, 0), (-s, s), (s, s)],
            6: [(-s, -s), (s, -s), (-s, 0), (s, 0), (-s, s), (s, s)],
        }
        return positions.get(self.value, [(0, 0)])


# ==================== 游戏主类 ====================
class YahtzeeGame:
    """快艇骰子游戏主类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Yahtzee 快艇骰子")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("simhei", 36)
        self.font_medium = pygame.font.SysFont("simhei", 24)
        self.font_small = pygame.font.SysFont("simhei", 18)
        self.font_tiny = pygame.font.SysFont("simhei", 14)

        # 骰子
        dice_start_x = 60
        dice_y = 160
        self.dice = [Die(dice_start_x + i * 100, dice_y) for i in range(5)]

        # 按钮
        btn_width, btn_height = 180, 50
        self.roll_btn = pygame.Rect(120, 340, btn_width, btn_height)
        self.reset_btn = pygame.Rect(120, 410, btn_width, btn_height)

        # 计分状态
        self.score_used = {cat[0]: False for cat in CATEGORIES}
        self.score_values = {cat[0]: None for cat in CATEGORIES}
        self.roll_count = 0
        self.max_rolls = 3
        self.round_num = 1
        self.max_rounds = 13
        self.game_over = False
        self.message = "点击骰子锁定，掷骰子开始！"
        self.message_timer = 0
        self.selected_category = None
        self.animating = False

        # 分数显示
        self.score_entries = []
        self._init_score_entries()

        # 高亮当前鼠标悬停的计分项
        self.hover_category = None

    def _init_score_entries(self):
        """初始化计分表位置"""
        x = 450
        y = 50
        self.score_entries = []
        for i, (key, name, _) in enumerate(CATEGORIES):
            rect = pygame.Rect(x, y + i * 38, 200, 34)
            self.score_entries.append((key, name, rect))

    def reset_game(self):
        """重置游戏"""
        for d in self.dice:
            d.value = 1
            d.locked = False
        self.score_used = {cat[0]: False for cat in CATEGORIES}
        self.score_values = {cat[0]: None for cat in CATEGORIES}
        self.roll_count = 0
        self.round_num = 1
        self.game_over = False
        self.message = "新游戏！点击骰子锁定，掷骰子开始！"
        self.message_timer = 120
        self.selected_category = None

    def roll_dice(self):
        """掷骰子"""
        if self.game_over:
            return
        if self.roll_count >= self.max_rolls:
            self.set_message("已达最大掷骰次数，请选择计分类别！")
            return

        self.roll_count += 1
        for d in self.dice:
            d.roll()
        self.set_message(f"第 {self.roll_count} 次投掷")

    def set_message(self, msg):
        """设置消息"""
        self.message = msg
        self.message_timer = 180

    def get_dice_values(self):
        """获取当前骰子值列表"""
        return [d.value for d in self.dice]

    def calculate_score(self, category_key):
        """计算指定类别的得分"""
        values = self.get_dice_values()
        counts = [0] * 7
        for v in values:
            counts[v] += 1

        if category_key in ("ones", "twos", "threes", "fours", "fives", "sixes"):
            num = {"ones": 1, "twos": 2, "threes": 3, "fours": 4, "fives": 5, "sixes": 6}[category_key]
            return num * counts[num]

        if category_key == "three_kind":
            if any(c >= 3 for c in counts):
                return sum(values)
            return 0

        if category_key == "four_kind":
            if any(c >= 4 for c in counts):
                return sum(values)
            return 0

        if category_key == "full_house":
            has_three = any(c >= 3 for c in counts)
            has_two = any(c >= 2 for c in counts)
            # 去掉三条占用的那部分
            three_val = next((i for i, c in enumerate(counts) if c >= 3), 0)
            remaining = [c for i, c in enumerate(counts) if i != three_val]
            if has_three and (has_two and any(c >= 2 for c in remaining)):
                return 25
            # 特殊情况：5个相同也算葫芦
            if any(c == 5 for c in counts):
                return 25
            return 0

        if category_key == "small_straight":
            if self._has_straight(values, 4):
                return 30
            return 0

        if category_key == "large_straight":
            if self._has_straight(values, 5):
                return 40
            return 0

        if category_key == "yahtzee":
            if any(c == 5 for c in counts):
                return 50 + self._get_yahtzee_bonus()
            return 0

        if category_key == "chance":
            return sum(values)

        return 0

    def _has_straight(self, values, length):
        """检查是否有连续顺子"""
        unique = sorted(set(values))
        if len(unique) < length:
            return False
        for i in range(len(unique) - length + 1):
            if unique[i + length - 1] - unique[i] == length - 1:
                return True
        return False

    def _get_yahtzee_bonus(self):
        """计算额外快艇加分"""
        bonus = 0
        if self.score_used.get("yahtzee", False) and self.score_values.get("yahtzee", 0) == 50:
            bonus = 100
        return bonus

    def select_category(self, category_key):
        """选择计分类别"""
        if self.game_over:
            return
        if self.score_used[category_key]:
            self.set_message("该类别已计分！")
            return
        if self.roll_count == 0:
            self.set_message("请先掷骰子！")
            return

        # 计算得分并记录
        score = self.calculate_score(category_key)
        self.score_values[category_key] = score
        self.score_used[category_key] = True
        self.round_num += 1

        # 重置骰子和掷骰次数
        for d in self.dice:
            d.locked = False
        self.roll_count = 0

        self.set_message(f"得分 {score}！")

        # 检查游戏结束
        if self.round_num > self.max_rounds:
            self.game_over = True
            total = self.get_total_score()
            bonus = self.get_upper_bonus()
            self.set_message(f"游戏结束！总分: {total} (含上限奖励: {bonus})")

    def get_upper_total(self):
        """计算上部分区总分（1-6点）"""
        total = 0
        for i in range(6):
            key = CATEGORIES[i][0]
            if self.score_used[key]:
                total += self.score_values[key]
        return total

    def get_upper_bonus(self):
        """计算上限奖励（>=63分得35分）"""
        if self.get_upper_total() >= 63:
            return 35
        return 0

    def get_total_score(self):
        """计算总分"""
        total = 0
        for key, used in self.score_used.items():
            if used:
                total += self.score_values[key]
        total += self.get_upper_bonus()
        return total

    def handle_click(self, pos):
        """处理鼠标点击"""
        if self.animating:
            return

        # 点击骰子
        for d in self.dice:
            if d.rect.collidepoint(pos) and self.roll_count > 0:
                d.locked = not d.locked
                return

        # 掷骰子按钮
        if self.roll_btn.collidepoint(pos) and not self.game_over:
            self.roll_dice()
            return

        # 重置按钮
        if self.reset_btn.collidepoint(pos):
            self.reset_game()
            return

        # 计分表
        for key, name, rect in self.score_entries:
            if rect.collidepoint(pos) and not self.game_over:
                self.select_category(key)
                return

    def update(self):
        """更新游戏状态"""
        for d in self.dice:
            d.update()
        if self.message_timer > 0:
            self.message_timer -= 1

    def draw(self):
        """绘制画面"""
        self.screen.fill(BG_COLOR)

        # 标题
        title = self.font_large.render("🎲 Yahtzee 快艇骰子", True, YELLOW)
        self.screen.blit(title, (50, 20))

        # 轮次和掷骰次数
        round_text = self.font_medium.render(
            f"轮次: {self.round_num}/{self.max_rounds}  |  掷骰: {self.roll_count}/{self.max_rolls}",
            True, WHITE
        )
        self.screen.blit(round_text, (50, 75))

        # 绘制骰子
        for d in self.dice:
            d.draw(self.screen)

        # 骰子标签
        for i, d in enumerate(self.dice):
            label = self.font_small.render(f"骰子{i+1}", True, WHITE)
            self.screen.blit(label, (d.x + 15, d.y - 25))

        # 按钮
        self._draw_button(self.roll_btn, "🎲 掷骰子", GREEN, (60, 200, 60))
        self._draw_button(self.reset_btn, "🔄 重新开始", BLUE, (50, 100, 220))

        # 消息
        if self.message and self.message_timer > 0:
            msg_color = GREEN if "得分" in self.message or "结束" in self.message else WHITE
            msg = self.font_small.render(self.message, True, msg_color)
            self.screen.blit(msg, (50, 480))

        # 计分表
        self._draw_scoreboard()

        # 游戏结束画面
        if self.game_over:
            self._draw_game_over()

        pygame.display.flip()

    def _draw_button(self, rect, text, color, hover_color):
        """绘制按钮"""
        mouse_pos = pygame.mouse.get_pos()
        is_hover = rect.collidepoint(mouse_pos)
        btn_color = hover_color if is_hover else color

        shadow = rect.copy()
        shadow.x += 3
        shadow.y += 3
        pygame.draw.rect(self.screen, (0, 0, 0, 100), shadow, border_radius=10)
        pygame.draw.rect(self.screen, btn_color, rect, border_radius=10)
        pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=10)

        txt = self.font_medium.render(text, True, WHITE)
        tx = rect.x + (rect.width - txt.get_width()) // 2
        ty = rect.y + (rect.height - txt.get_height()) // 2
        self.screen.blit(txt, (tx, ty))

    def _draw_scoreboard(self):
        """绘制计分表"""
        # 标题
        header = self.font_medium.render("📊 计分表", True, YELLOW)
        self.screen.blit(header, (450, 20))

        # 绘制上半部分隔线（1-6点之后）
        for i, (key, name, rect) in enumerate(self.score_entries):
            used = self.score_used[key]
            hover = rect.collidepoint(pygame.mouse.get_pos())

            # 背景色
            bg_color = None
            if hover and not used and not self.game_over:
                bg_color = (60, 60, 100)
            elif used:
                bg_color = (40, 50, 40)
            else:
                bg_color = (40, 40, 60)

            pygame.draw.rect(self.screen, bg_color, rect, border_radius=5)
            if hover and not used and not self.game_over:
                pygame.draw.rect(self.screen, YELLOW, rect, 2, border_radius=5)

            # 类别名称
            name_color = DARK_GRAY if used else WHITE
            if hover and not used:
                name_color = YELLOW
            txt = self.font_small.render(name, True, name_color)
            self.screen.blit(txt, (rect.x + 8, rect.y + 7))

            # 得分
            if used:
                score_text = self.font_small.render(str(self.score_values[key]), True, GREEN)
            else:
                score_text = self.font_small.render("-", True, DARK_GRAY)
                # 如果有掷骰，显示预览分数
                if self.roll_count > 0 and not self.game_over:
                    preview = self.calculate_score(key)
                    if preview > 0:
                        score_text = self.font_small.render(str(preview), True, (120, 120, 120))
            self.screen.blit(score_text, (rect.x + 150, rect.y + 7))

        # 汇总行
        y_offset = 50 + len(CATEGORIES) * 38 + 10

        # 上限奖励
        bonus = self.get_upper_bonus()
        bonus_rect = pygame.Rect(450, y_offset, 200, 34)
        pygame.draw.rect(self.screen, (50, 50, 80), bonus_rect, border_radius=5)
        bonus_txt = self.font_small.render(f"上限奖励 (+35)", True, YELLOW if bonus > 0 else DARK_GRAY)
        self.screen.blit(bonus_txt, (bonus_rect.x + 8, bonus_rect.y + 7))
        bonus_val = self.font_small.render(str(bonus), True, YELLOW if bonus > 0 else DARK_GRAY)
        self.screen.blit(bonus_val, (bonus_rect.x + 150, bonus_rect.y + 7))

        y_offset += 38

        # 上部分区小计
        upper_total = self.get_upper_total()
        upper_rect = pygame.Rect(450, y_offset, 200, 34)
        pygame.draw.rect(self.screen, (50, 50, 80), upper_rect, border_radius=5)
        upper_txt = self.font_small.render(f"上部小计 (≥63得+35)", True, WHITE)
        self.screen.blit(upper_txt, (upper_rect.x + 8, upper_rect.y + 7))
        upper_val = self.font_small.render(str(upper_total), True, WHITE)
        self.screen.blit(upper_val, (upper_rect.x + 150, upper_rect.y + 7))

        y_offset += 38

        # 总分
        total = self.get_total_score()
        total_rect = pygame.Rect(450, y_offset, 200, 40)
        pygame.draw.rect(self.screen, (80, 80, 60), total_rect, border_radius=8)
        pygame.draw.rect(self.screen, YELLOW, total_rect, 2, border_radius=8)
        total_txt = self.font_medium.render(f"总分: {total}", True, YELLOW)
        tx = total_rect.x + (total_rect.width - total_txt.get_width()) // 2
        ty = total_rect.y + (total_rect.height - total_txt.get_height()) // 2
        self.screen.blit(total_txt, (tx, ty))

        # 右上角提示
        if self.roll_count > 0 and not self.game_over:
            hint = self.font_tiny.render("点击右侧计分项确认得分", True, (150, 150, 150))
            self.screen.blit(hint, (450, y_offset + 48))

    def _draw_game_over(self):
        """绘制游戏结束画面"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # 游戏结束文字
        total = self.get_total_score()
        gt = self.font_large.render(f"🎉 游戏结束！", True, YELLOW)
        st = self.font_medium.render(f"最终总分: {total}", True, WHITE)
        bonus = self.get_upper_bonus()
        bt = self.font_small.render(f"(其中上限奖励: {bonus} 分)", True, GRAY)
        rt = self.font_small.render("点击「重新开始」再来一局", True, GRAY)

        cx = SCREEN_WIDTH // 2
        self.screen.blit(gt, (cx - gt.get_width() // 2, 200))
        self.screen.blit(st, (cx - st.get_width() // 2, 260))
        self.screen.blit(bt, (cx - bt.get_width() // 2, 300))
        self.screen.blit(rt, (cx - rt.get_width() // 2, 340))

    def run(self):
        """主循环"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)

            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ==================== 启动游戏 ====================
if __name__ == "__main__":
    game = YahtzeeGame()
    game.run()