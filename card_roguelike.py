"""
卡牌Roguelike — 简化版杀戮尖塔 (Slay the Spire Lite)
=====================================================
游戏类型: 卡牌策略Roguelike
玩法: 使用卡牌战斗，击败敌人，获得新卡，挑战BOSS
操作: 鼠标点击卡牌使用，点击"结束回合"按钮
依赖: Python 3 + Pygame 2.x
"""

import pygame
import random
import sys

# ======================== 初始化 ========================
pygame.init()
WIDTH, HEIGHT = 900, 680
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("卡牌Roguelike — 简化版杀戮尖塔")
clock = pygame.time.Clock()
font_large = pygame.font.SysFont("simhei", 28, bold=True)
font_mid = pygame.font.SysFont("simhei", 22)
font_small = pygame.font.SysFont("simhei", 18)
font_log = pygame.font.SysFont("simsun", 16)

# 颜色
WHITE = (255, 255, 255)
BLACK = (10, 10, 10)
RED = (220, 50, 50)
GREEN = (50, 200, 80)
BLUE = (50, 100, 220)
GOLD = (255, 215, 0)
GRAY = (100, 100, 100)
LIGHT_GRAY = (180, 180, 180)
DARK = (30, 30, 40)
CARD_BG = (45, 50, 65)
CARD_HOVER = (65, 70, 90)
BLOCK_BLUE = (80, 160, 255)
HP_RED = (220, 60, 60)
ENERGY_YELLOW = (255, 220, 50)
BG_TOP = (25, 25, 40)
BG_BOT = (40, 35, 55)

# ======================== 卡牌定义 ========================
CARD_TEMPLATES = [
    {"name": "打击", "cost": 1, "type": "attack", "desc": "造成6点伤害", "dmg": 6, "block": 0, "heal": 0, "hits": 1},
    {"name": "防御", "cost": 1, "type": "skill", "desc": "获得5点格挡", "dmg": 0, "block": 5, "heal": 0, "hits": 1},
    {"name": "重击", "cost": 2, "type": "attack", "desc": "造成14点伤害", "dmg": 14, "block": 0, "heal": 0, "hits": 1},
    {"name": "治愈", "cost": 1, "type": "skill", "desc": "回复8点生命", "dmg": 0, "block": 0, "heal": 8, "hits": 1},
    {"name": "双重打击", "cost": 1, "type": "attack", "desc": "造成4点伤害×2", "dmg": 4, "block": 0, "heal": 0, "hits": 2},
    {"name": "铁壁", "cost": 2, "type": "skill", "desc": "获得12点格挡", "dmg": 0, "block": 12, "heal": 0, "hits": 1},
    {"name": "狂怒", "cost": 0, "type": "attack", "desc": "造成5点伤害", "dmg": 5, "block": 0, "heal": 0, "hits": 1},
    {"name": "吸血", "cost": 1, "type": "attack", "desc": "造成7点伤害,回复3HP", "dmg": 7, "block": 0, "heal": 3, "hits": 1},
    {"name": "闪电打击", "cost": 2, "type": "attack", "desc": "造成9点伤害×2", "dmg": 9, "block": 0, "heal": 0, "hits": 2},
    {"name": "坚毅", "cost": 1, "type": "skill", "desc": "获得8点格挡", "dmg": 0, "block": 8, "heal": 0, "hits": 1},
    {"name": "火焰斩", "cost": 3, "type": "attack", "desc": "造成22点伤害", "dmg": 22, "block": 0, "heal": 0, "hits": 1},
    {"name": "生命汲取", "cost": 2, "type": "attack", "desc": "造成10伤,回复5HP", "dmg": 10, "block": 0, "heal": 5, "hits": 1},
]

# ======================== 敌人定义 ========================
ENEMY_TEMPLATES = [
    {"name": "史莱姆", "hp": 18, "dmg": 5, "color": (80, 200, 80)},
    {"name": "蝙蝠", "hp": 14, "dmg": 7, "color": (160, 80, 200)},
    {"name": "骷髅", "hp": 22, "dmg": 6, "color": (220, 220, 200)},
    {"name": "幽灵", "hp": 20, "dmg": 8, "color": (180, 160, 220)},
    {"name": "暗影", "hp": 28, "dmg": 9, "color": (100, 60, 120)},
    {"name": "狼人", "hp": 25, "dmg": 10, "color": (180, 100, 60)},
]

BOSS_TEMPLATES = [
    {"name": "巨魔", "hp": 45, "dmg": 10, "color": (120, 180, 50)},
    {"name": "石像鬼", "hp": 50, "dmg": 12, "color": (160, 150, 140)},
    {"name": "暗影领主", "hp": 55, "dmg": 14, "color": (80, 40, 100)},
    {"name": "龙", "hp": 60, "dmg": 16, "color": (200, 80, 30)},
]


# ======================== 游戏状态 ========================
class Game:
    """管理游戏全局状态"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.floor = 1
        self.max_floor = 3
        self.state = "menu"  # menu | playing | won | lost
        self.log = []
        self.enemy = None
        self.battle_log = []
        self.reward_cards = []
        self.show_reward = False
        self.start_new_run()

    def start_new_run(self):
        """开始新的一局"""
        self.floor = 1
        self.state = "playing"
        self.player = Player()
        self.enemy = self.generate_enemy()
        self.player.reset_battle()
        self.battle_log = ["— 战斗开始 —"]
        self.show_reward = False
        self.reward_cards = []

    def generate_enemy(self):
        """根据层数生成敌人"""
        if self.floor < self.max_floor:
            t = random.choice(ENEMY_TEMPLATES)
            hp_scale = 1 + (self.floor - 1) * 0.3
            return Enemy(t["name"], int(t["hp"] * hp_scale),
                         int(t["dmg"] * (1 + (self.floor - 1) * 0.2)), t["color"])
        else:
            t = random.choice(BOSS_TEMPLATES)
            return Enemy(t["name"], t["hp"], t["dmg"], t["color"], is_boss=True)

    def next_floor(self):
        """进入下一层"""
        self.floor += 1
        if self.floor > self.max_floor:
            self.state = "won"
            return
        self.enemy = self.generate_enemy()
        self.player.reset_battle()
        self.battle_log = [f"— 第{self.floor}层 —"]
        self.show_reward = False

    def add_log(self, msg):
        self.battle_log.append(msg)
        if len(self.battle_log) > 30:
            self.battle_log.pop(0)

    def update(self):
        if self.state == "playing" and self.enemy and self.enemy.hp <= 0:
            # 敌人死亡，显示奖励
            if not self.show_reward:
                self.show_reward = True
                self.reward_cards = random.sample(CARD_TEMPLATES, 3)
                self.add_log(f"击败了{self.enemy.name}！选择一张奖励卡牌")

    def select_reward(self, idx):
        """选择奖励卡牌"""
        if 0 <= idx < len(self.reward_cards):
            self.player.add_card(self.reward_cards[idx])
            self.add_log(f"获得卡牌: {self.reward_cards[idx]['name']}")
        self.show_reward = False
        self.next_floor()


class Player:
    """玩家状态"""

    def __init__(self):
        self.max_hp = 80
        self.hp = self.max_hp
        self.max_energy = 3
        self.energy = self.max_energy
        self.block = 0
        self.deck = []
        self.hand = []
        self.discard = []
        self.draw_pile = []
        self._init_deck()

    def _init_deck(self):
        """初始卡组：5打击 + 5防御"""
        self.deck = []
        for _ in range(5):
            self.deck.append(CARD_TEMPLATES[0])  # 打击
        for _ in range(5):
            self.deck.append(CARD_TEMPLATES[1])  # 防御
        random.shuffle(self.deck)

    def add_card(self, card_template):
        """添加卡牌到卡组"""
        self.deck.append(card_template)
        random.shuffle(self.deck)

    def reset_battle(self):
        """重置战斗状态"""
        self.energy = self.max_energy
        self.block = 0
        self.hand = []
        self.discard = []
        self.draw_pile = self.deck.copy()
        random.shuffle(self.draw_pile)
        self.draw_hand()

    def draw_hand(self):
        """抽牌至5张"""
        self.hand = []
        self.draw_cards(5)

    def draw_cards(self, n):
        """抽n张牌"""
        for _ in range(n):
            if not self.draw_pile:
                self.draw_pile = self.discard.copy()
                random.shuffle(self.draw_pile)
                self.discard = []
            if self.draw_pile:
                self.hand.append(self.draw_pile.pop())
        # 限制手牌上限10
        if len(self.hand) > 10:
            excess = self.hand[10:]
            self.discard.extend(excess)
            self.hand = self.hand[:10]

    def use_card(self, card, enemy, game):
        """使用卡牌"""
        if self.energy < card["cost"]:
            return False
        self.energy -= card["cost"]
        # 从手牌移除
        if card in self.hand:
            self.hand.remove(card)

        total_dmg = 0
        # 攻击效果
        if card["dmg"] > 0:
            for _ in range(card["hits"]):
                dmg = card["dmg"]
                # 检查敌人是否有格挡
                if enemy.block > 0:
                    if enemy.block >= dmg:
                        enemy.block -= dmg
                        dmg = 0
                    else:
                        dmg -= enemy.block
                        enemy.block = 0
                enemy.hp -= dmg
                total_dmg += dmg
            game.add_log(f"使用 {card['name']} → 造成 {total_dmg} 点伤害")

        # 格挡效果
        if card["block"] > 0:
            self.block += card["block"]
            game.add_log(f"使用 {card['name']} → 获得 {card['block']} 点格挡")

        # 治疗效果
        if card["heal"] > 0:
            old_hp = self.hp
            self.hp = min(self.max_hp, self.hp + card["heal"])
            actual_heal = self.hp - old_hp
            game.add_log(f"使用 {card['name']} → 回复 {actual_heal} 点生命")

        # 使用后弃牌
        self.discard.append(card)

        if enemy.hp <= 0:
            pass  # 由game.update处理

        return True

    def end_turn(self):
        """结束回合"""
        # 剩余格挡消失
        self.block = 0
        # 手牌全弃
        self.discard.extend(self.hand)
        self.hand = []
        # 重置能量
        self.energy = self.max_energy
        # 抽牌
        self.draw_hand()

    def take_damage(self, dmg):
        """受到伤害（计算格挡）"""
        if self.block > 0:
            if self.block >= dmg:
                self.block -= dmg
                dmg = 0
            else:
                dmg -= self.block
                self.block = 0
        self.hp -= dmg
        if self.hp < 0:
            self.hp = 0
        return dmg


class Enemy:
    """敌人"""

    def __init__(self, name, hp, dmg, color, is_boss=False):
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.dmg = dmg
        self.color = color
        self.is_boss = is_boss
        self.block = 0
        self.intent = "attack"

    def act(self, player, game):
        """敌人行动"""
        if self.hp <= 0:
            return
        dmg = self.dmg
        # 10%几率格挡
        if random.random() < 0.1 and not self.is_boss:
            self.block += 4
            game.add_log(f"{self.name} 防御，获得4点格挡")
            return

        dealt = player.take_damage(dmg)
        game.add_log(f"{self.name} 攻击 → 造成 {dealt} 点伤害")


# ======================== 绘制函数 ========================
def draw_gradient_bg():
    """绘制渐变背景"""
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(BG_TOP[0] * (1 - ratio) + BG_BOT[0] * ratio)
        g = int(BG_TOP[1] * (1 - ratio) + BG_BOT[1] * ratio)
        b = int(BG_TOP[2] * (1 - ratio) + BG_BOT[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))


def draw_text(text, font, color, x, y, center=True):
    """绘制文字，默认居中"""
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surf, rect)
    return rect


def draw_rounded_rect(surf, color, rect, radius=8):
    """绘制圆角矩形"""
    x, y, w, h = rect
    pygame.draw.rect(surf, color, (x + radius, y, w - 2 * radius, h))
    pygame.draw.rect(surf, color, (x, y + radius, w, h - 2 * radius))
    pygame.draw.circle(surf, color, (x + radius, y + radius), radius)
    pygame.draw.circle(surf, color, (x + w - radius - 1, y + radius), radius)
    pygame.draw.circle(surf, color, (x + radius, y + h - radius - 1), radius)
    pygame.draw.circle(surf, color, (x + w - radius - 1, y + h - radius - 1), radius)


def draw_hp_bar(x, y, w, h, cur, max_hp, color, label=""):
    """绘制血条"""
    # 背景
    pygame.draw.rect(screen, (60, 30, 30), (x, y, w, h), border_radius=4)
    # 当前血量
    ratio = max(0, cur / max_hp)
    fw = int(w * ratio)
    if fw > 0:
        pygame.draw.rect(screen, color, (x, y, fw, h), border_radius=4)
    # 边框
    pygame.draw.rect(screen, WHITE, (x, y, w, h), 1, border_radius=4)
    # 文字
    txt = f"{label}{cur}/{max_hp}"
    draw_text(txt, font_small, WHITE, x + w // 2, y + h // 2)


def draw_card(card, x, y, w, h, hover=False):
    """绘制单张卡牌"""
    bg = CARD_HOVER if hover else CARD_BG
    draw_rounded_rect(screen, bg, (x, y, w, h))
    pygame.draw.rect(screen, LIGHT_GRAY, (x, y, w, h), 2, border_radius=8)

    # 费用标记
    cost_color = ENERGY_YELLOW if card["cost"] <= 1 else (255, 150, 50) if card["cost"] == 2 else (255, 80, 80)
    pygame.draw.circle(screen, cost_color, (x + 22, y + 22), 12)
    draw_text(str(card["cost"]), font_mid, BLACK, x + 22, y + 22)

    # 卡牌名称
    name_color = (255, 180, 100) if card["type"] == "attack" else (100, 200, 255)
    draw_text(card["name"], font_small, name_color, x + w // 2, y + 38)

    # 卡牌描述
    desc = card["desc"]
    draw_text(desc, font_small, LIGHT_GRAY, x + w // 2, y + h - 22)


def draw_battle_log(game):
    """绘制战斗日志"""
    log_x = 20
    log_y = 170
    log_w = 240
    log_h = 320
    draw_rounded_rect(screen, (20, 20, 30, 200), (log_x, log_y, log_w, log_h))
    pygame.draw.rect(screen, GRAY, (log_x, log_y, log_w, log_h), 1, border_radius=6)
    draw_text("战斗日志", font_small, GOLD, log_x + log_w // 2, log_y + 14)

    # 显示最近15条日志
    logs = game.battle_log[-15:]
    for i, msg in enumerate(logs):
        c = WHITE if "→" in msg else LIGHT_GRAY
        draw_text(msg, font_log, c, log_x + 10, log_y + 32 + i * 18, center=False)


def draw_menu(game):
    """绘制主菜单"""
    draw_gradient_bg()
    draw_text("卡牌Roguelike", font_large, GOLD, WIDTH // 2, 180)
    draw_text("简化版杀戮尖塔", font_large, WHITE, WIDTH // 2, 225)
    draw_text("点击任意位置开始游戏", font_mid, LIGHT_GRAY, WIDTH // 2, 350)
    draw_text("使用卡牌战斗，击败敌人，获得新卡，挑战BOSS！", font_small, GRAY, WIDTH // 2, 400)
    draw_text("操作: 点击卡牌使用 | 点击[结束回合]结束当前回合", font_small, GRAY, WIDTH // 2, 430)


def draw_game_over(game):
    """绘制游戏结束画面"""
    draw_gradient_bg()
    if game.state == "won":
        draw_text("🎉 恭喜通关！", font_large, GOLD, WIDTH // 2, 220)
        draw_text("你击败了所有BOSS！", font_mid, WHITE, WIDTH // 2, 280)
    else:
        draw_text("💀 游戏结束", font_large, RED, WIDTH // 2, 220)
        draw_text(f"你倒在了第{game.floor}层", font_mid, WHITE, WIDTH // 2, 280)
    draw_text(f"最终生命值: {game.player.hp}/{game.player.max_hp}", font_mid, GREEN, WIDTH // 2, 330)
    draw_text("点击任意位置重新开始", font_mid, LIGHT_GRAY, WIDTH // 2, 400)


def draw_battle(game):
    """绘制战斗画面"""
    draw_gradient_bg()
    p = game.player
    e = game.enemy

    # ===== 顶部信息栏 =====
    info_y = 10
    # 玩家信息（左）
    draw_rounded_rect(screen, (30, 30, 50, 180), (10, info_y, 300, 120))
    draw_text(f"第{game.floor}层", font_mid, GOLD, 160, info_y + 14)
    draw_hp_bar(20, info_y + 32, 280, 20, p.hp, p.max_hp, HP_RED, "HP: ")
    # 格挡条
    if p.block > 0:
        draw_hp_bar(20, info_y + 56, 280, 16, p.block, 30, BLOCK_BLUE, "格挡: ")
    # 能量
    energy_str = "⚡" * p.energy + "·" * (p.max_energy - p.energy)
    draw_text(f"能量: {energy_str}", font_mid, ENERGY_YELLOW, 160, info_y + 82)

    # 敌人信息（右）
    draw_rounded_rect(screen, (50, 30, 30, 180), (WIDTH - 310, info_y, 300, 120))
    boss_tag = " [BOSS]" if e.is_boss else ""
    draw_text(f"{e.name}{boss_tag}", font_mid, e.color, WIDTH - 160, info_y + 14)
    draw_hp_bar(WIDTH - 300, info_y + 32, 280, 20, e.hp, e.max_hp, RED, "HP: ")
    if e.block > 0:
        draw_hp_bar(WIDTH - 300, info_y + 56, 280, 16, e.block, 30, BLOCK_BLUE, "格挡: ")

    # 敌人意图
    intent_text = "意图: 攻击"
    draw_text(intent_text, font_small, (255, 200, 200), WIDTH - 160, info_y + 82)
    draw_text(f"伤害: {e.dmg}", font_small, RED, WIDTH - 160, info_y + 102)

    # ===== 敌人形象（中间） =====
    enemy_center_x = WIDTH // 2
    enemy_center_y = 280
    size = 80 if not e.is_boss else 110
    # 绘制敌人身体
    pygame.draw.circle(screen, e.color, (enemy_center_x, enemy_center_y), size)
    pygame.draw.circle(screen, WHITE, (enemy_center_x, enemy_center_y), size, 2)
    # 眼睛
    eye_off = size // 3
    pygame.draw.circle(screen, WHITE, (enemy_center_x - eye_off, enemy_center_y - 8), 10)
    pygame.draw.circle(screen, WHITE, (enemy_center_x + eye_off, enemy_center_y - 8), 10)
    pygame.draw.circle(screen, BLACK, (enemy_center_x - eye_off, enemy_center_y - 8), 5)
    pygame.draw.circle(screen, BLACK, (enemy_center_x + eye_off, enemy_center_y - 8), 5)
    # 嘴巴
    if e.hp > e.max_hp * 0.3:
        pygame.draw.arc(screen, WHITE, (enemy_center_x - 20, enemy_center_y + 10, 40, 25), 0, 3.14, 2)
    else:
        pygame.draw.arc(screen, WHITE, (enemy_center_x - 20, enemy_center_y + 15, 40, 25), 3.14, 6.28, 2)

    # ===== 战斗日志 =====
    draw_battle_log(game)

    # ===== 结束回合按钮 =====
    btn_x, btn_y, btn_w, btn_h = WIDTH - 160, 500, 130, 40
    btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
    draw_rounded_rect(screen, (60, 60, 80), btn_rect)
    pygame.draw.rect(screen, ENERGY_YELLOW, btn_rect, 2, border_radius=8)
    draw_text("结束回合", font_mid, ENERGY_YELLOW, btn_x + btn_w // 2, btn_y + btn_h // 2)

    # ===== 手牌区域 =====
    hand_y = 555
    card_w, card_h = 110, 110
    spacing = 8
    total_w = len(p.hand) * (card_w + spacing) - spacing
    start_x = (WIDTH - total_w) // 2

    mouse_x, mouse_y = pygame.mouse.get_pos()
    game.hover_card_idx = -1

    for i, card in enumerate(p.hand):
        cx = start_x + i * (card_w + spacing)
        cy = hand_y
        hover = cx <= mouse_x <= cx + card_w and cy <= mouse_y <= cy + card_h
        if hover:
            game.hover_card_idx = i
        draw_card(card, cx, cy, card_w, card_h, hover)

    # ===== 奖励选择界面 =====
    if game.show_reward:
        draw_reward_overlay(game)


def draw_reward_overlay(game):
    """绘制奖励选择界面"""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    draw_text("选择一张奖励卡牌", font_large, GOLD, WIDTH // 2, 200)

    card_w, card_h = 140, 160
    spacing = 30
    total_w = len(game.reward_cards) * (card_w + spacing) - spacing
    start_x = (WIDTH - total_w) // 2
    y = 250

    game.reward_rects = []
    for i, card in enumerate(game.reward_cards):
        cx = start_x + i * (card_w + spacing)
        draw_card(card, cx, y, card_w, card_h, hover=False)
        game.reward_rects.append(pygame.Rect(cx, y, card_w, card_h))


# ======================== 主循环 ========================
def main():
    game = Game()
    running = True

    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                if game.state == "menu":
                    game.start_new_run()
                    continue

                if game.state in ("won", "lost"):
                    game.reset()
                    continue

                if game.state == "playing":
                    # 奖励选择
                    if game.show_reward:
                        for i, rect in enumerate(game.reward_rects):
                            if rect.collidepoint(mx, my):
                                game.select_reward(i)
                        continue

                    # 结束回合按钮
                    btn_x, btn_y, btn_w, btn_h = WIDTH - 160, 500, 130, 40
                    if btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h:
                        p = game.player
                        p.end_turn()
                        game.add_log("— 玩家回合结束 —")
                        # 敌人行动
                        game.enemy.act(p, game)
                        # 检查玩家是否死亡
                        if p.hp <= 0:
                            game.state = "lost"
                            game.add_log("你被击败了...")
                        continue

                    # 使用卡牌
                    p = game.player
                    hand_y = 555
                    card_w, card_h = 110, 110
                    spacing = 8
                    total_w = len(p.hand) * (card_w + spacing) - spacing
                    start_x = (WIDTH - total_w) // 2

                    for i, card in enumerate(p.hand):
                        cx = start_x + i * (card_w + spacing)
                        cy = hand_y
                        if cx <= mx <= cx + card_w and cy <= my <= cy + card_h:
                            if p.use_card(card, game.enemy, game):
                                pass  # 用卡成功，日志已加
                            else:
                                game.add_log("能量不足！")

        # ===== 更新 =====
        game.update()

        # ===== 绘制 =====
        screen.fill(BLACK)
        if game.state == "menu":
            draw_menu(game)
        elif game.state in ("won", "lost"):
            draw_game_over(game)
        else:
            draw_battle(game)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()