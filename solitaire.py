"""
纸牌接龙 (Solitaire / Klondike)
=============================
经典单机纸牌游戏，使用 Python + Pygame 实现。
目标：将所有的牌按花色（♠♥♦♣）从 A 到 K 移到右上角的四个基础牌堆。

操作方式：
- 点击牌堆顶部的牌可选中
- 点击目标位置可移动牌
- 双击牌可自动移到基础牌堆
- 点击发牌堆可翻一张牌
- 右键点击可撤销选中

游戏规则：
1. 桌面上有7列牌，从左到右依次为1-7张，只有最上面的牌是翻开的
2. 发牌堆（左上角）每次翻一张牌到弃牌堆
3. 基础牌堆（右上角）按花色从A到K排列
4. 桌面上的牌按红黑交替、递减顺序排列
5. 桌面上的牌可以移动一列或多列（必须按顺序）
6. 空列只能放K
7. 获胜条件：所有牌都移到基础牌堆

作者：AI 游戏开发者
日期：2026-07-23
"""

import pygame
import random
import sys

# ============================================================
# 常量定义
# ============================================================
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

# 颜色
COLORS = {
    "bg": (0, 100, 0),          # 背景绿色
    "card_back": (25, 60, 140),  # 牌背蓝色
    "card_front": (255, 255, 255),  # 牌面白色
    "card_border": (0, 0, 0),    # 边框黑色
    "red": (200, 30, 30),        # 红心/方块
    "black": (30, 30, 30),       # 黑桃/梅花
    "selected": (255, 255, 0, 100),  # 选中高亮
    "foundation_bg": (0, 80, 0),  # 基础牌堆背景
    "text": (255, 255, 200),
    "stock_hint": (200, 200, 100),
    "win_bg": (0, 0, 0, 180),
}

# 牌面尺寸
CARD_WIDTH = 70
CARD_HEIGHT = 100
CARD_RADIUS = 8

# 布局位置
MARGIN_X = 30
MARGIN_Y = 20
TOP_Y = 30
TABLEAU_TOP = 160
CARD_OFFSET_Y = 25  # 桌面上叠牌时的垂直偏移

# 发牌堆位置
STOCK_X = MARGIN_X
STOCK_Y = TOP_Y
WASTE_X = STOCK_X + CARD_WIDTH + 15
WASTE_Y = TOP_Y

# 基础牌堆位置（右上角）
FOUNDATION_X = SCREEN_WIDTH - MARGIN_X - 4 * (CARD_WIDTH + 15)
FOUNDATION_Y = TOP_Y

# 桌面列起始位置
TABLEAU_X = MARGIN_X
TABLEAU_Y = TABLEAU_TOP


# ============================================================
# 牌和游戏逻辑类
# ============================================================

class Card:
    """一张扑克牌"""

    SUITS = ["♠", "♥", "♦", "♣"]
    RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

    def __init__(self, suit, rank, face_up=False):
        self.suit = suit
        self.rank = rank
        self.rank_index = self.RANKS.index(rank)  # 0-12
        self.suit_index = self.SUITS.index(suit)  # 0-3
        self.face_up = face_up
        self.color = "red" if suit in ("♥", "♦") else "black"
        self.x = 0
        self.y = 0
        self.width = CARD_WIDTH
        self.height = CARD_HEIGHT

    def is_red(self):
        return self.color == "red"

    def is_black(self):
        return self.color == "black"

    def get_rect(self):
        """返回牌的矩形区域"""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface):
        """绘制牌"""
        rect = self.get_rect()
        if self.face_up:
            # 牌面
            pygame.draw.rect(surface, COLORS["card_front"], rect, border_radius=CARD_RADIUS)
            pygame.draw.rect(surface, COLORS["card_border"], rect, width=2, border_radius=CARD_RADIUS)
            # 花色和点数
            color = COLORS["red"] if self.is_red() else COLORS["black"]
            font_size = 20
            font = pygame.font.SysFont("simhei", font_size, bold=True)
            # 左上角
            rank_text = font.render(self.rank, True, color)
            suit_text = font.render(self.suit, True, color)
            surface.blit(rank_text, (self.x + 5, self.y + 3))
            surface.blit(suit_text, (self.x + 5, self.y + 22))
            # 右下角（倒转）
            if self.rank != "10":
                rank_text2 = font.render(self.rank, True, color)
            else:
                rank_text2 = font.render(self.rank, True, color)
            suit_text2 = font.render(self.suit, True, color)
            # 绘制中心花色（大号）
            center_font = pygame.font.SysFont("simhei", 36, bold=True)
            center_suit = center_font.render(self.suit, True, color)
            sx = self.x + (CARD_WIDTH - center_suit.get_width()) // 2
            sy = self.y + (CARD_HEIGHT - center_suit.get_height()) // 2
            surface.blit(center_suit, (sx, sy))
            # 右下角（倒转）
            r2 = pygame.transform.rotate(rank_text2, 180)
            s2 = pygame.transform.rotate(suit_text2, 180)
            surface.blit(r2, (self.x + CARD_WIDTH - 5 - r2.get_width(), self.y + CARD_HEIGHT - 3 - r2.get_height()))
            surface.blit(s2, (self.x + CARD_WIDTH - 5 - s2.get_width(), self.y + CARD_HEIGHT - 22 - s2.get_height()))
        else:
            # 牌背
            pygame.draw.rect(surface, COLORS["card_back"], rect, border_radius=CARD_RADIUS)
            pygame.draw.rect(surface, COLORS["card_border"], rect, width=2, border_radius=CARD_RADIUS)
            # 牌背花纹
            inner = pygame.Rect(self.x + 8, self.y + 8, CARD_WIDTH - 16, CARD_HEIGHT - 16)
            pygame.draw.rect(surface, (40, 80, 180), inner, border_radius=CARD_RADIUS - 2)
            pygame.draw.rect(surface, (60, 100, 200), inner, width=2, border_radius=CARD_RADIUS - 2)
            # 中心图案
            pattern_font = pygame.font.SysFont("simhei", 24, bold=True)
            pattern = pattern_font.render("♠♥♦♣", True, (100, 150, 220))
            px = self.x + (CARD_WIDTH - pattern.get_width()) // 2
            py = self.y + (CARD_HEIGHT - pattern.get_height()) // 2
            surface.blit(pattern, (px, py))

    def contains_point(self, x, y):
        """判断点是否在牌内"""
        return self.get_rect().collidepoint(x, y)


class SolitaireGame:
    """纸牌接龙游戏主逻辑"""

    def __init__(self):
        self.reset()

    def reset(self):
        """重置游戏"""
        # 创建一副牌
        self.deck = []
        for suit in Card.SUITS:
            for rank in Card.RANKS:
                self.deck.append(Card(suit, rank, face_up=False))
        random.shuffle(self.deck)

        # 发牌堆（未翻的牌）
        self.stock = []
        # 弃牌堆（从发牌堆翻出的牌）
        self.waste = []
        # 基础牌堆（4个，按花色从A到K）
        self.foundations = [[] for _ in range(4)]
        # 桌面列（7列）
        self.tableau = [[] for _ in range(7)]

        # 发牌到桌面
        for i in range(7):
            for j in range(i, 7):
                card = self.deck.pop()
                if j == i:  # 每列最下面一张翻开
                    card.face_up = True
                self.tableau[j].append(card)

        # 剩余的牌放入发牌堆
        self.stock = self.deck[:]

        # 选中状态
        self.selected_cards = []  # 选中的牌列表
        self.selected_source = None  # "tableau", "waste", "foundation"
        self.selected_source_idx = -1

        # 游戏状态
        self.game_won = False
        self.move_count = 0
        self.auto_complete = False

        # 更新位置
        self.update_positions()

    def update_positions(self):
        """更新所有牌的位置"""
        # 发牌堆
        for i, card in enumerate(self.stock):
            card.x = STOCK_X
            card.y = STOCK_Y

        # 弃牌堆
        for i, card in enumerate(self.waste):
            card.x = WASTE_X
            card.y = WASTE_Y

        # 基础牌堆
        for i, pile in enumerate(self.foundations):
            for j, card in enumerate(pile):
                card.x = FOUNDATION_X + i * (CARD_WIDTH + 15)
                card.y = FOUNDATION_Y

        # 桌面列
        for i, pile in enumerate(self.tableau):
            for j, card in enumerate(pile):
                card.x = TABLEAU_X + i * (CARD_WIDTH + 15)
                card.y = TABLEAU_Y + j * CARD_OFFSET_Y

    def draw_stock(self, surface):
        """绘制发牌堆"""
        if self.stock:
            # 绘制牌背
            rect = pygame.Rect(STOCK_X, STOCK_Y, CARD_WIDTH, CARD_HEIGHT)
            pygame.draw.rect(surface, COLORS["card_back"], rect, border_radius=CARD_RADIUS)
            pygame.draw.rect(surface, COLORS["card_border"], rect, width=2, border_radius=CARD_RADIUS)
            # 显示剩余数量
            font = pygame.font.SysFont("simhei", 14)
            text = font.render(f"{len(self.stock)}", True, COLORS["stock_hint"])
            surface.blit(text, (STOCK_X + CARD_WIDTH - 22, STOCK_Y + CARD_HEIGHT - 18))
        else:
            # 空发牌堆 - 点击可重置
            rect = pygame.Rect(STOCK_X, STOCK_Y, CARD_WIDTH, CARD_HEIGHT)
            pygame.draw.rect(surface, COLORS["foundation_bg"], rect, border_radius=CARD_RADIUS)
            pygame.draw.rect(surface, COLORS["card_border"], rect, width=2, border_radius=CARD_RADIUS)
            # 显示重置图标
            font = pygame.font.SysFont("simhei", 24)
            text = font.render("↻", True, COLORS["stock_hint"])
            tx = STOCK_X + (CARD_WIDTH - text.get_width()) // 2
            ty = STOCK_Y + (CARD_HEIGHT - text.get_height()) // 2
            surface.blit(text, (tx, ty))

    def draw_waste(self, surface):
        """绘制弃牌堆"""
        if self.waste:
            self.waste[-1].draw(surface)
        else:
            rect = pygame.Rect(WASTE_X, WASTE_Y, CARD_WIDTH, CARD_HEIGHT)
            pygame.draw.rect(surface, COLORS["foundation_bg"], rect, border_radius=CARD_RADIUS)
            pygame.draw.rect(surface, COLORS["card_border"], rect, width=2, border_radius=CARD_RADIUS)

    def draw_foundations(self, surface):
        """绘制基础牌堆"""
        for i, pile in enumerate(self.foundations):
            x = FOUNDATION_X + i * (CARD_WIDTH + 15)
            y = FOUNDATION_Y
            if pile:
                pile[-1].draw(surface)
            else:
                rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
                pygame.draw.rect(surface, COLORS["foundation_bg"], rect, border_radius=CARD_RADIUS)
                pygame.draw.rect(surface, COLORS["card_border"], rect, width=2, border_radius=CARD_RADIUS)
                # 显示花色提示
                font = pygame.font.SysFont("simhei", 28)
                suit = Card.SUITS[i]
                color = COLORS["red"] if suit in ("♥", "♦") else COLORS["black"]
                text = font.render(suit, True, color)
                tx = x + (CARD_WIDTH - text.get_width()) // 2
                ty = y + (CARD_HEIGHT - text.get_height()) // 2
                surface.blit(text, (tx, ty))

    def draw_tableau(self, surface):
        """绘制桌面列"""
        for i, pile in enumerate(self.tableau):
            for j, card in enumerate(pile):
                card.draw(surface)

    def draw_selection(self, surface):
        """绘制选中高亮"""
        if not self.selected_cards:
            return
        for card in self.selected_cards:
            rect = card.get_rect()
            # 黄色边框
            pygame.draw.rect(surface, (255, 255, 0), rect, width=3, border_radius=CARD_RADIUS)

    def draw(self, surface):
        """绘制整个游戏"""
        surface.fill(COLORS["bg"])

        # 绘制桌面列（先绘制，让选中高亮在上面）
        self.draw_tableau(surface)

        # 绘制发牌堆、弃牌堆、基础牌堆
        self.draw_stock(surface)
        self.draw_waste(surface)
        self.draw_foundations(surface)

        # 绘制选中高亮
        self.draw_selection(surface)

        # 绘制移动计数
        font = pygame.font.SysFont("simhei", 18)
        text = font.render(f"步数: {self.move_count}", True, COLORS["text"])
        surface.blit(text, (SCREEN_WIDTH // 2 - 30, 10))

        # 绘制帮助信息
        help_font = pygame.font.SysFont("simhei", 14)
        help_text = help_font.render("左键选择/移动 | 双击自动移到基础堆 | 右键取消选择 | R键重新开始", True, COLORS["text"])
        surface.blit(help_text, (SCREEN_WIDTH // 2 - help_text.get_width() // 2, SCREEN_HEIGHT - 25))

        # 胜利画面
        if self.game_won:
            self.draw_win_screen(surface)

    def draw_win_screen(self, surface):
        """绘制胜利画面"""
        # 半透明遮罩
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        s.fill(COLORS["win_bg"])
        surface.blit(s, (0, 0))

        font_big = pygame.font.SysFont("simhei", 64, bold=True)
        font_small = pygame.font.SysFont("simhei", 32)

        # 胜利文字
        title = font_big.render("🎉 恭喜通关！ 🎉", True, (255, 215, 0))
        tx = (SCREEN_WIDTH - title.get_width()) // 2
        ty = SCREEN_HEIGHT // 2 - 60
        surface.blit(title, (tx, ty))

        # 步数统计
        stats = font_small.render(f"总步数: {self.move_count}", True, (255, 255, 255))
        sx = (SCREEN_WIDTH - stats.get_width()) // 2
        sy = SCREEN_HEIGHT // 2 + 20
        surface.blit(stats, (sx, sy))

        # 重新开始提示
        restart = font_small.render("按 R 键重新开始", True, (200, 200, 200))
        rx = (SCREEN_WIDTH - restart.get_width()) // 2
        ry = SCREEN_HEIGHT // 2 + 70
        surface.blit(restart, (rx, ry))

    def handle_click(self, pos, button=1):
        """处理鼠标点击
        button: 1=左键, 3=右键
        """
        x, y = pos

        if self.game_won:
            return

        if button == 3:  # 右键取消选中
            self.selected_cards = []
            self.selected_source = None
            self.selected_source_idx = -1
            return

        # 左键点击
        # 先检查是否点击了发牌堆
        if self.stock and pygame.Rect(STOCK_X, STOCK_Y, CARD_WIDTH, CARD_HEIGHT).collidepoint(x, y):
            self.click_stock()
            return

        # 空发牌堆 - 重置
        if not self.stock and pygame.Rect(STOCK_X, STOCK_Y, CARD_WIDTH, CARD_HEIGHT).collidepoint(x, y):
            self.reset_stock()
            return

        # 如果已经有选中的牌，尝试移动
        if self.selected_cards:
            # 检查是否点击了基础牌堆
            for i in range(4):
                fx = FOUNDATION_X + i * (CARD_WIDTH + 15)
                fy = FOUNDATION_Y
                if pygame.Rect(fx, fy, CARD_WIDTH, CARD_HEIGHT).collidepoint(x, y):
                    if self.try_move_to_foundation(self.selected_cards, i):
                        self.selected_cards = []
                        self.selected_source = None
                        self.selected_source_idx = -1
                        return
                    break

            # 检查是否点击了桌面列
            for i, pile in enumerate(self.tableau):
                # 计算该列的可点击区域
                if pile:
                    top_card = pile[-1]
                    click_rect = top_card.get_rect()
                    # 如果列有多个牌，扩大点击区域
                    if len(pile) > 1:
                        click_rect = pygame.Rect(
                            pile[0].x, pile[0].y,
                            CARD_WIDTH, pile[0].y + len(pile) * CARD_OFFSET_Y - pile[0].y + CARD_HEIGHT - CARD_OFFSET_Y
                        )
                    if click_rect.collidepoint(x, y):
                        if self.try_move_to_tableau(self.selected_cards, i):
                            self.selected_cards = []
                            self.selected_source = None
                            self.selected_source_idx = -1
                            return
                        break

            # 如果点击了弃牌堆顶部，但选中的不是弃牌堆的牌，切换到弃牌堆选择
            if self.waste:
                waste_rect = self.waste[-1].get_rect()
                if waste_rect.collidepoint(x, y) and self.selected_source != "waste":
                    self.selected_cards = []
                    self.selected_source = None
                    self.selected_source_idx = -1
                    self.click_waste()
                    return

            # 点击其他地方取消选中
            self.selected_cards = []
            self.selected_source = None
            self.selected_source_idx = -1
            return

        # 没有选中牌，尝试选择
        # 检查弃牌堆
        if self.waste:
            waste_rect = self.waste[-1].get_rect()
            if waste_rect.collidepoint(x, y):
                self.click_waste()
                return

        # 检查基础牌堆
        for i, pile in enumerate(self.foundations):
            if pile:
                fx = FOUNDATION_X + i * (CARD_WIDTH + 15)
                fy = FOUNDATION_Y
                if pygame.Rect(fx, fy, CARD_WIDTH, CARD_HEIGHT).collidepoint(x, y):
                    # 双击自动完成外，点击基础牌堆不做选择
                    return
            else:
                fx = FOUNDATION_X + i * (CARD_WIDTH + 15)
                fy = FOUNDATION_Y
                if pygame.Rect(fx, fy, CARD_WIDTH, CARD_HEIGHT).collidepoint(x, y):
                    return

        # 检查桌面列
        for i in range(len(self.tableau) - 1, -1, -1):  # 从右到左检查
            pile = self.tableau[i]
            if not pile:
                # 空列
                rect = pygame.Rect(TABLEAU_X + i * (CARD_WIDTH + 15), TABLEAU_Y, CARD_WIDTH, CARD_HEIGHT)
                if rect.collidepoint(x, y):
                    # 空列点击无效（除非有选中牌，但上面已经处理了）
                    return
                continue

            # 从最上面开始检查
            for j in range(len(pile) - 1, -1, -1):
                card = pile[j]
                if card.face_up and card.contains_point(x, y):
                    # 选中这张牌及下面的所有牌
                    self.selected_cards = pile[j:]
                    self.selected_source = "tableau"
                    self.selected_source_idx = i
                    return
                elif not card.face_up:
                    # 如果是盖着的牌点击翻牌
                    if card.contains_point(x, y):
                        last_card = pile[-1]
                        if last_card is card:  # 只有最上面的盖牌才能翻
                            card.face_up = True
                            self.move_count += 1
                            return
                    break  # 遇到盖牌就不再往下检查

    def click_stock(self):
        """点击发牌堆 - 翻一张牌到弃牌堆"""
        if not self.stock:
            return
        card = self.stock.pop()
        card.face_up = True
        self.waste.append(card)
        self.move_count += 1
        self.update_positions()

    def reset_stock(self):
        """重置发牌堆（弃牌堆的牌回到发牌堆）"""
        if self.stock or not self.waste:
            return
        self.stock = self.waste[::-1]
        self.waste = []
        for card in self.stock:
            card.face_up = False
        self.move_count += 1
        self.update_positions()

    def click_waste(self):
        """点击弃牌堆顶部 - 选中"""
        if not self.waste:
            return
        self.selected_cards = [self.waste[-1]]
        self.selected_source = "waste"
        self.selected_source_idx = -1

    def try_move_to_foundation(self, cards, foundation_idx):
        """尝试将牌移到基础牌堆"""
        if len(cards) != 1:
            return False
        card = cards[0]
        pile = self.foundations[foundation_idx]

        # 检查花色是否匹配
        expected_suit = Card.SUITS[foundation_idx]
        if card.suit != expected_suit:
            return False

        # 检查点数
        if not pile:
            if card.rank == "A":
                self._do_move_to_foundation(card, foundation_idx)
                return True
            return False
        else:
            top = pile[-1]
            if card.rank_index == top.rank_index + 1:
                self._do_move_to_foundation(card, foundation_idx)
                return True
            return False

    def _do_move_to_foundation(self, card, foundation_idx):
        """执行移到基础牌堆"""
        # 从源位置移除
        if self.selected_source == "waste":
            self.waste.remove(card)
        elif self.selected_source == "tableau":
            pile = self.tableau[self.selected_source_idx]
            if card in pile:
                idx = pile.index(card)
                # 移除 card 及之后的所有牌（但移到基础只能一张）
                del pile[idx:]
                # 翻开新顶牌
                if pile and not pile[-1].face_up:
                    pile[-1].face_up = True
        elif self.selected_source == "foundation":
            return

        # 添加到基础牌堆
        self.foundations[foundation_idx].append(card)
        self.move_count += 1
        self.update_positions()

        # 检查是否获胜
        self.check_win()

    def try_move_to_tableau(self, cards, tableau_idx):
        """尝试将牌移到桌面列"""
        if not cards:
            return False
        first_card = cards[0]
        pile = self.tableau[tableau_idx]

        if not pile:
            # 空列只能放K
            if first_card.rank == "K":
                self._do_move_to_tableau(cards, tableau_idx)
                return True
            return False
        else:
            top = pile[-1]
            # 检查颜色是否交替
            if first_card.is_red() == top.is_red():
                return False
            # 检查点数是否递减（top比first大1）
            if first_card.rank_index == top.rank_index - 1:
                self._do_move_to_tableau(cards, tableau_idx)
                return True
            return False

    def _do_move_to_tableau(self, cards, tableau_idx):
        """执行移到桌面列"""
        # 从源位置移除
        source_pile = None
        if self.selected_source == "waste":
            source_pile = self.waste
        elif self.selected_source == "tableau":
            source_pile = self.tableau[self.selected_source_idx]
        elif self.selected_source == "foundation":
            source_pile = self.foundations[self.selected_source_idx]

        if source_pile is None:
            return

        for card in cards:
            if card in source_pile:
                source_pile.remove(card)

        # 翻开源列的新顶牌
        if self.selected_source == "tableau":
            src_pile = self.tableau[self.selected_source_idx]
            if src_pile and not src_pile[-1].face_up:
                src_pile[-1].face_up = True

        # 添加到目标列
        self.tableau[tableau_idx].extend(cards)
        self.move_count += 1
        self.update_positions()

    def handle_double_click(self, pos):
        """处理双击 - 自动移到基础牌堆"""
        if self.game_won:
            return
        x, y = pos

        # 检查点击了哪个牌
        clicked_card = None
        source = None
        source_idx = -1

        # 检查弃牌堆
        if self.waste:
            waste_card = self.waste[-1]
            if waste_card.get_rect().collidepoint(x, y):
                clicked_card = waste_card
                source = "waste"
                source_idx = -1

        # 检查桌面列
        if clicked_card is None:
            for i, pile in enumerate(self.tableau):
                for j in range(len(pile) - 1, -1, -1):
                    card = pile[j]
                    if card.face_up and card.contains_point(x, y):
                        # 只选最上面的牌
                        if j == len(pile) - 1:
                            clicked_card = card
                            source = "tableau"
                            source_idx = i
                        break

        if clicked_card is None:
            return

        # 尝试移到基础牌堆
        self.selected_cards = [clicked_card]
        self.selected_source = source
        self.selected_source_idx = source_idx

        for i in range(4):
            if self.try_move_to_foundation([clicked_card], i):
                self.selected_cards = []
                self.selected_source = None
                self.selected_source_idx = -1
                return

        self.selected_cards = []
        self.selected_source = None
        self.selected_source_idx = -1

    def check_win(self):
        """检查是否获胜"""
        for pile in self.foundations:
            if len(pile) != 13:
                return
        self.game_won = True

    def auto_complete_check(self):
        """自动完成检测 - 可以自动移到基础堆的牌"""
        # 简单实现：检查弃牌堆和桌面列顶牌是否能移到基础堆
        moved = True
        while moved:
            moved = False
            # 检查弃牌堆顶
            if self.waste:
                card = self.waste[-1]
                for i in range(4):
                    if self.try_move_to_foundation([card], i):
                        self.selected_cards = [card]
                        self.selected_source = "waste"
                        self._do_move_to_foundation(card, i)
                        self.selected_cards = []
                        self.selected_source = None
                        self.selected_source_idx = -1
                        moved = True
                        break
            if moved:
                continue
            # 检查桌面列顶牌
            for i, pile in enumerate(self.tableau):
                if pile and pile[-1].face_up:
                    card = pile[-1]
                    for j in range(4):
                        if self.try_move_to_foundation([card], j):
                            self.selected_cards = [card]
                            self.selected_source = "tableau"
                            self.selected_source_idx = i
                            self._do_move_to_foundation(card, j)
                            self.selected_cards = []
                            self.selected_source = None
                            self.selected_source_idx = -1
                            moved = True
                            break
                if moved:
                    break


# ============================================================
# 主程序
# ============================================================

def main():
    """游戏主函数"""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("纸牌接龙 Solitaire")
    clock = pygame.time.Clock()

    game = SolitaireGame()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset()
                elif event.key == pygame.K_a:
                    # A键开启自动完成
                    game.auto_complete = not game.auto_complete
                elif event.key == pygame.K_ESCAPE:
                    game.selected_cards = []
                    game.selected_source = None
                    game.selected_source_idx = -1

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        # 检测双击
                        pass
                    game.handle_click(event.pos, button=1)
                elif event.button == 3:  # 右键
                    game.handle_click(event.pos, button=3)

            elif event.type == pygame.MOUSEBUTTONUP:
                pass

            elif event.type == pygame.MOUSEMOTION:
                # 拖拽移动（简化版，只做选中不拖拽）
                pass

        # 检查双击
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]:
            pass

        # 自动完成
        if game.auto_complete and not game.game_won:
            game.auto_complete_check()

        game.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()