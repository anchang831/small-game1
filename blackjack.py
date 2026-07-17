"""
21点 (Blackjack) - 经典赌场纸牌游戏
===============================
玩法: 玩家与庄家对战，目标是手牌点数尽可能接近21但不超过21。
A 可算1或11点，J/Q/K 算10点，其他牌按面值计算。

操作:
- Hit (H): 要牌
- Stand (S): 停牌
- Double Down (D): 加倍（仅限首两张牌）
- 点击筹码下注，点击 Deal 发牌
"""

import pygame
import random
import sys

# ======================== 初始化 ========================
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("21点 Blackjack")
clock = pygame.time.Clock()
FPS = 60

# ======================== 颜色 ========================
GREEN = (27, 110, 50)
DARK_GREEN = (20, 85, 38)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
GOLD = (255, 215, 0)
DARK_GOLD = (200, 160, 0)
BLUE = (30, 80, 200)
DARK_BLUE = (20, 55, 150)
GRAY = (180, 180, 180)
DARK_GRAY = (80, 80, 80)
LIGHT_GRAY = (220, 220, 220)

# ======================== 字体 ========================
FONT_TITLE = pygame.font.SysFont("simhei", 36, bold=True)
FONT_LARGE = pygame.font.SysFont("simhei", 28, bold=True)
FONT_MED = pygame.font.SysFont("simhei", 22)
FONT_SMALL = pygame.font.SysFont("simhei", 18)
FONT_CARD = pygame.font.SysFont("simhei", 24, bold=True)

# ======================== 牌组 ========================
SUITS = ["♠", "♥", "♦", "♣"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


class Card:
    """一张扑克牌"""

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank
        self.face_up = True

    @property
    def value(self):
        if self.rank == "A":
            return 11
        elif self.rank in ("J", "Q", "K"):
            return 10
        return int(self.rank)

    def __repr__(self):
        return f"{self.rank}{self.suit}"


class Deck:
    """一副或多副牌"""

    def __init__(self, num_decks=6):
        self.cards = []
        for _ in range(num_decks):
            for suit in SUITS:
                for rank in RANKS:
                    self.cards.append(Card(suit, rank))
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop()


def hand_value(cards):
    """计算手牌点数，A 自动按最优方式计算"""
    total = sum(c.value for c in cards)
    aces = sum(1 for c in cards if c.rank == "A")
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total


def is_blackjack(cards):
    """是否为黑杰克(21点)"""
    return len(cards) == 2 and hand_value(cards) == 21


def is_bust(cards):
    """是否爆牌"""
    return hand_value(cards) > 21


# ======================== 绘制函数 ========================
def draw_card(card, x, y, width=70, height=100):
    """绘制一张牌"""
    if not card.face_up:
        # 牌背
        pygame.draw.rect(screen, BLUE, (x, y, width, height), border_radius=6)
        pygame.draw.rect(screen, DARK_BLUE, (x + 3, y + 3, width - 6, height - 6), border_radius=4)
        # 牌背花纹
        for i in range(3, width - 3, 8):
            for j in range(3, height - 3, 8):
                px = x + i + (j % 16) // 8 * 4
                pygame.draw.circle(screen, BLUE, (px, y + j), 1)
        return
    # 牌面
    is_red = card.suit in ("♥", "♦")
    color = RED if is_red else BLACK
    pygame.draw.rect(screen, WHITE, (x, y, width, height), border_radius=6)
    pygame.draw.rect(screen, BLACK, (x, y, width, height), 2, border_radius=6)
    # 左上角
    rank_surf = FONT_CARD.render(card.rank, True, color)
    suit_surf = FONT_SMALL.render(card.suit, True, color)
    screen.blit(rank_surf, (x + 5, y + 3))
    screen.blit(suit_surf, (x + 5, y + 24))
    # 中心大花色
    center_surf = FONT_LARGE.render(card.suit, True, color)
    sr = center_surf.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(center_surf, sr)


def draw_button(text, x, y, w, h, color, hover_color, text_color=WHITE, disabled=False):
    """绘制按钮，返回是否点击"""
    mouse = pygame.mouse.get_pos()
    clicked = pygame.mouse.get_pressed()[0]
    rect = pygame.Rect(x, y, w, h)
    is_hover = rect.collidepoint(mouse) and not disabled

    color = hover_color if is_hover else color
    if disabled:
        color = DARK_GRAY

    pygame.draw.rect(screen, color, rect, border_radius=8)
    if not disabled:
        pygame.draw.rect(screen, WHITE, rect, 2, border_radius=8)

    surf = FONT_MED.render(text, True, text_color if not disabled else GRAY)
    sr = surf.get_rect(center=rect.center)
    screen.blit(surf, sr)

    if is_hover and clicked and not disabled:
        pygame.time.wait(150)
        return True
    return False


def draw_chip(value, x, y, selected=False):
    """绘制筹码"""
    radius = 22
    color_map = {
        1: (200, 200, 200),
        5: (50, 120, 220),
        10: (50, 180, 80),
        25: (220, 60, 60),
        100: (50, 50, 50),
        500: (180, 50, 180),
    }
    color = color_map.get(value, (200, 200, 200))
    if selected:
        pygame.draw.circle(screen, GOLD, (x, y), radius + 3)
    pygame.draw.circle(screen, color, (x, y), radius)
    pygame.draw.circle(screen, WHITE, (x, y), radius - 4, 2)
    val_surf = FONT_SMALL.render(str(value), True, WHITE if value != 1 else BLACK)
    vr = val_surf.get_rect(center=(x, y))
    screen.blit(val_surf, vr)


# ======================== 游戏状态 ========================
class GameState:
    """管理游戏状态"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.deck = Deck(6)
        self.player_hand = []
        self.dealer_hand = []
        self.chips = 500
        self.bet = 0
        self.phase = "bet"  # bet | play | dealer_turn | result
        self.result_text = ""
        self.result_color = WHITE
        self.insurance_bet = 0
        self.can_double = True
        self.can_split = False
        self.message = "请下注"

    def new_round(self):
        """开始新一局"""
        self.player_hand = []
        self.dealer_hand = []
        self.phase = "bet"
        self.result_text = ""
        self.can_double = True
        self.message = "请下注"

    def deal(self):
        """发牌"""
        if self.bet <= 0:
            self.message = "请先下注!"
            return
        if self.bet > self.chips:
            self.message = "筹码不足!"
            return

        self.chips -= self.bet
        self.player_hand = [self.deck.draw(), self.deck.draw()]
        self.dealer_hand = [self.deck.draw(), self.deck.draw()]
        self.dealer_hand[1].face_up = False  # 暗牌
        self.phase = "play"
        self.message = "选择操作"

        # 检查玩家是否黑杰克
        if is_blackjack(self.player_hand):
            self.dealer_hand[1].face_up = True
            self.phase = "result"
            if is_blackjack(self.dealer_hand):
                self.result_text = "双方都是21点，平局!"
                self.result_color = GOLD
                self.chips += self.bet
            else:
                self.result_text = "Blackjack! 你赢了 1.5倍!"
                self.result_color = GOLD
                self.chips += int(self.bet * 2.5)
            self.message = self.result_text

    def hit(self):
        """要牌"""
        if self.phase != "play":
            return
        self.can_double = False
        self.player_hand.append(self.deck.draw())
        if is_bust(self.player_hand):
            self.phase = "result"
            self.result_text = "爆牌! 你输了!"
            self.result_color = RED
            self.message = self.result_text

    def stand(self):
        """停牌，庄家回合"""
        if self.phase != "play":
            return
        self.phase = "dealer_turn"
        self.dealer_hand[1].face_up = True
        self._dealer_play()

    def double_down(self):
        """加倍"""
        if self.phase != "play" or not self.can_double:
            return
        if self.chips < self.bet:
            self.message = "筹码不足，无法加倍!"
            return
        self.chips -= self.bet
        self.bet *= 2
        self.can_double = False
        self.player_hand.append(self.deck.draw())
        if is_bust(self.player_hand):
            self.phase = "result"
            self.result_text = "加倍爆牌! 你输了!"
            self.result_color = RED
            self.message = self.result_text
        else:
            self.phase = "dealer_turn"
            self.dealer_hand[1].face_up = True
            self._dealer_play()

    def _dealer_play(self):
        """庄家自动要牌"""
        while hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.draw())
        self.phase = "result"
        self._resolve()

    def _resolve(self):
        """结算结果"""
        p_val = hand_value(self.player_hand)
        d_val = hand_value(self.dealer_hand)

        if is_bust(self.dealer_hand):
            self.result_text = f"庄家爆牌! 你赢了! ({p_val} vs {d_val})"
            self.result_color = GOLD
            self.chips += self.bet * 2
        elif p_val > d_val:
            self.result_text = f"你赢了! ({p_val} vs {d_val})"
            self.result_color = GOLD
            self.chips += self.bet * 2
        elif p_val == d_val:
            self.result_text = f"平局! ({p_val} vs {d_val})"
            self.result_color = GOLD
            self.chips += self.bet
        else:
            self.result_text = f"你输了! ({p_val} vs {d_val})"
            self.result_color = RED
        self.message = self.result_text

    def place_bet(self, amount):
        """下注"""
        if self.phase != "bet":
            return
        if amount > self.chips:
            self.message = "筹码不足!"
            return
        self.bet += amount


# ======================== 主循环 ========================
def main():
    game = GameState()
    running = True

    # 筹码区域
    chip_values = [1, 5, 10, 25, 100]
    chip_positions = [(WIDTH // 2 - 160 + i * 80, HEIGHT - 45) for i in range(5)]

    while running:
        dt = clock.tick(FPS)

        # ---- 事件处理 ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if game.phase == "play":
                    if event.key == pygame.K_h:
                        game.hit()
                    elif event.key == pygame.K_s:
                        game.stand()
                    elif event.key == pygame.K_d:
                        game.double_down()
                if game.phase == "result" and event.key == pygame.K_SPACE:
                    game.new_round()
                if game.phase == "bet" and event.key == pygame.K_RETURN:
                    game.deal()

        # ---- 鼠标点击 ----
        if pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()

            # 筹码点击
            if game.phase == "bet":
                for i, (cx, cy) in enumerate(chip_positions):
                    if (mx - cx) ** 2 + (my - cy) ** 2 < 25 ** 2:
                        game.place_bet(chip_values[i])

        # ---- 绘制 ----
        screen.fill(GREEN)

        # 桌面纹理
        for i in range(0, WIDTH, 40):
            for j in range(0, HEIGHT, 40):
                if (i // 40 + j // 40) % 2 == 0:
                    pygame.draw.rect(screen, DARK_GREEN, (i, j, 40, 40))

        # ---- 标题 ----
        title_surf = FONT_TITLE.render("♠ 21点 Blackjack ♥", True, GOLD)
        title_rect = title_surf.get_rect(center=(WIDTH // 2, 28))
        screen.blit(title_surf, title_rect)

        # ---- 信息 ----
        info_text = f"筹码: ${game.chips}  |  下注: ${game.bet}"
        info_surf = FONT_MED.render(info_text, True, WHITE)
        screen.blit(info_surf, (20, 60))

        # ---- 消息 ----
        msg_surf = FONT_LARGE.render(game.message, True, game.result_color if game.phase == "result" else WHITE)
        msg_rect = msg_surf.get_rect(center=(WIDTH // 2, 95))
        screen.blit(msg_surf, msg_rect)

        # ---- 庄家手牌 ----
        dealer_label = FONT_MED.render("庄家: " + (str(hand_value(game.dealer_hand)) if game.dealer_hand and (
                game.phase in ("result", "dealer_turn") or game.dealer_hand[0].face_up) else "?"), True, WHITE)
        screen.blit(dealer_label, (20, 120))

        dealer_start_x = 20
        for i, card in enumerate(game.dealer_hand):
            draw_card(card, dealer_start_x + i * 80, 140)

        # ---- 玩家手牌 ----
        player_label = FONT_MED.render("玩家: " + (str(hand_value(game.player_hand)) if game.player_hand else ""), True,
                                       WHITE)
        screen.blit(player_label, (20, 270))

        player_start_x = 20
        for i, card in enumerate(game.player_hand):
            draw_card(card, player_start_x + i * 80, 290)

        # ---- 操作按钮 ----
        btn_y = 420
        btn_w, btn_h = 120, 45

        if game.phase == "bet":
            if draw_button("发牌 (Enter)", WIDTH // 2 - 60, btn_y, 120, btn_h, BLUE, DARK_BLUE, disabled=game.bet <= 0):
                game.deal()
            # 清零按钮
            if draw_button("清零", WIDTH // 2 + 80, btn_y, 80, btn_h, DARK_GRAY, GRAY, disabled=game.bet <= 0):
                game.chips += game.bet
                game.bet = 0

        elif game.phase == "play":
            if draw_button("要牌 (H)", WIDTH // 2 - 190, btn_y, btn_w, btn_h, BLUE, DARK_BLUE):
                game.hit()
            if draw_button("停牌 (S)", WIDTH // 2 - 60, btn_y, btn_w, btn_h, BLUE, DARK_BLUE):
                game.stand()
            if draw_button("加倍 (D)", WIDTH // 2 + 70, btn_y, btn_w, btn_h, GOLD, DARK_GOLD,
                           disabled=not game.can_double or game.chips < game.bet):
                game.double_down()

        elif game.phase == "result":
            if draw_button("再来一局 (Space)", WIDTH // 2 - 100, btn_y, 200, btn_h, GOLD, DARK_GOLD):
                game.new_round()

        # ---- 筹码 ----
        if game.phase == "bet":
            for i, (cx, cy) in enumerate(chip_positions):
                draw_chip(chip_values[i], cx, cy)

        # ---- 操作提示 ----
        tips = []
        if game.phase == "bet":
            tips = ["点击筹码下注，按 Enter 发牌", "ESC - 退出"]
        elif game.phase == "play":
            tips = ["H - 要牌  |  S - 停牌  |  D - 加倍"]
        elif game.phase == "result":
            tips = ["Space - 再来一局  |  ESC - 退出"]
        else:
            tips = ["ESC - 退出"]

        for i, tip in enumerate(tips):
            tip_surf = FONT_SMALL.render(tip, True, LIGHT_GRAY)
            screen.blit(tip_surf, (WIDTH // 2 - tip_surf.get_width() // 2, HEIGHT - 90 + i * 22))

        # ---- 更新 ----
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()