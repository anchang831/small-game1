"""
Wordle 猜词游戏 - Pygame 实现
玩法: 6次机会猜中一个5字母单词
- 绿色: 字母位置正确
- 黄色: 单词包含该字母但位置不对
- 灰色: 单词不包含该字母
"""

import pygame
import random
import sys

# ======================== 配置 ========================
SCREEN_WIDTH = 520
SCREEN_HEIGHT = 700
GRID_SIZE = 62
GRID_GAP = 8
GRID_OFFSET_X = (SCREEN_WIDTH - 5 * (GRID_SIZE + GRID_GAP)) // 2
GRID_OFFSET_Y = 80
KEYBOARD_ROWS = [
    "QWERTYUIOP",
    "ASDFGHJKL",
    "ZXCVBNM",
]
KEY_WIDTH = 44
KEY_HEIGHT = 52
KEY_GAP = 4
KEYBOARD_Y = 420

# 颜色
COLOR_BG = (18, 18, 19)
COLOR_EMPTY = (58, 58, 60)
COLOR_GREEN = (83, 141, 78)
COLOR_YELLOW = (181, 159, 59)
COLOR_GRAY = (58, 58, 60)
COLOR_TEXT = (248, 248, 248)
COLOR_BORDER = (58, 58, 60)
COLOR_KEY_TEXT = (248, 248, 248)
COLOR_KEY_BG = (129, 131, 132)
COLOR_OVERLAY = (0, 0, 0, 180)

# ======================== 单词库 ========================
# 常见5字母英文单词 (约500个)
WORD_LIST = [
    "ABOUT", "ABOVE", "ABUSE", "ACTOR", "ACUTE", "ADMIT", "ADOPT", "ADULT", "AFTER", "AGAIN",
    "AGENT", "AGREE", "AHEAD", "ALARM", "ALBUM", "ALERT", "ALIKE", "ALIVE", "ALLOW", "ALONE",
    "ALONG", "ALTER", "ANGEL", "ANGER", "ANGLE", "ANGRY", "APART", "APPLE", "APPLY", "ARENA",
    "ARGUE", "ARISE", "ARRAY", "ASIDE", "ASSET", "AVOID", "AWARD", "AWARE", "BADLY", "BAKER",
    "BASES", "BASIC", "BEACH", "BEGAN", "BEING", "BELOW", "BENCH", "BILLY", "BIRTH", "BLACK",
    "BLADE", "BLAME", "BLAND", "BLANK", "BLAST", "BLAZE", "BLEED", "BLEND", "BLESS", "BLIND",
    "BLOCK", "BLOOD", "BLOOM", "BLOWN", "BOARD", "BONUS", "BOOST", "BOUND", "BRAIN", "BRAND",
    "BRAVE", "BREAD", "BREAK", "BREED", "BRICK", "BRIEF", "BROAD", "BROKE", "BROOK", "BRUSH",
    "BUILD", "BUILT", "BUNCH", "BURST", "CABIN", "CABLE", "CANDY", "CARRY", "CATCH", "CAUSE",
    "CEASE", "CHAIN", "CHAIR", "CHAOS", "CHARM", "CHART", "CHASE", "CHEAP", "CHECK", "CHEEK",
    "CHESS", "CHEST", "CHIEF", "CHILD", "CHILL", "CHIPS", "CHOIR", "CHORD", "CIVIL", "CLAIM",
    "CLASH", "CLASS", "CLEAN", "CLEAR", "CLERK", "CLIMB", "CLING", "CLOCK", "CLONE", "CLOSE",
    "CLOTH", "CLOUD", "COACH", "COAST", "COLOR", "COMET", "COMIC", "CORAL", "COUCH", "COUNT",
    "COURT", "COVER", "CRACK", "CRAFT", "CRANE", "CRASH", "CRAWL", "CRAZY", "CREAM", "CREEK",
    "CREPT", "CRIME", "CRISP", "CROSS", "CROWD", "CROWN", "CRUDE", "CRUEL", "CRUSH", "CURVE",
    "CYCLE", "DAIRY", "DANCE", "DEATH", "DEBUG", "DECAY", "DECOR", "DEITY", "DELAY", "DELTA",
    "DEMON", "DENSE", "DEPTH", "DERBY", "DESKTOP",  # 移除 DESKTOP（6字母），替换
    "DIARY", "DIGIT", "DIMLY", "DIRTY", "DISCO", "DITCH", "DIZZY", "DOLLY", "DONOR", "DOUBT",
    "DOUGH", "DOZEN", "DRAFT", "DRAIN", "DRAKE", "DRAMA", "DRANK", "DRAWN", "DREAM", "DRESS",
    "DRIED", "DRIFT", "DRILL", "DRINK", "DRIVE", "DROVE", "DROWN", "DRUMS", "DRUNK", "DYING",
    "EAGER", "EAGLE", "EARLY", "EARTH", "EIGHT", "EITHER", "ELECT", "ELITE", "ELSE", "EMAIL",
    "EMPTY", "ENEMY", "ENJOY", "ENTER", "ENTRY", "EQUAL", "ERROR", "ESSAY", "EVENT", "EVERY",
    "EVICT", "EXACT", "EXILE", "EXIST", "EXTRA", "FAINT", "FAIRY", "FAITH", "FALSE", "FANCY",
    "FATAL", "FAULT", "FEAST", "FENCE", "FEVER", "FIBER", "FIELD", "FIFTH", "FIFTY", "FIGHT",
    "FINAL", "FINGER", "FINISH", "FIRE", "FIRST", "FISH", "FIXED", "FLAG", "FLAME", "FLASH",
    "FLEET", "FLESH", "FLICK", "FLOAT", "FLOCK", "FLOOD", "FLOOR", "FLOUR", "FLUID", "FLUSH",
    "FLUTE", "FOCAL", "FOCUS", "FORCE", "FORGE", "FORTH", "FORUM", "FOUND", "FRAME", "FRANK",
    "FRAUD", "FRESH", "FRONT", "FROST", "FROZE", "FRUIT", "FULLY", "FUNGI", "FUNNY", "GHOST",
    "GIANT", "GIVEN", "GLASS", "GLEAM", "GLOBE", "GLOOM", "GLORY", "GLOSS", "GLOVE", "GLUED",
    "GODLY", "GOING", "GOOSE", "GRACE", "GRADE", "GRAIN", "GRAND", "GRANT", "GRAPE", "GRAPH",
    "GRASP", "GRASS", "GRAVE", "GREAT", "GREEN", "GREET", "GRIEF", "GRIND", "GROAN", "GROOM",
    "GROUP", "GROVE", "GROWN", "GUARD", "GUESS", "GUEST", "GUIDE", "GUILT", "GULCH", "GUMBO",
    "HABIT", "HAPPY", "HARSH", "HAVEN", "HEART", "HEAVY", "HEDGE", "HELLO", "HENCE", "HERBS",
    "HONOR", "HORSE", "HOTEL", "HOUSE", "HUMAN", "HUMOR", "HURRY", "IDEAL", "IMAGE", "IMPLY",
    "INDEX", "INDIE", "INNER", "INPUT", "IRONY", "ISSUE", "IVORY", "JEWEL", "JOINT", "JOKER",
    "JUDGE", "JUICE", "JUICY", "JUMBO", "KICKS", "KNIFE", "KNOCK", "KNOWN", "LABEL", "LASER",
    "LATER", "LAUGH", "LAYER", "LEARN", "LEAVE", "LEMON", "LEVEL", "LEVER", "LIGHT", "LIMIT",
    "LINER", "LIVER", "LOCAL", "LOGIC", "LOOSE", "LOVER", "LOWER", "LOYAL", "LUCKY", "LUNAR",
    "LUNCH", "LYRIC", "MAJOR", "MAKER", "MANOR", "MAPLE", "MARCH", "MARRY", "MASON", "MATCH",
    "MAYOR", "MEDIA", "MERCY", "MERGE", "MERIT", "METAL", "METER", "MIGHT", "MINOR", "MINUS",
    "MIRTH", "MODEL", "MONEY", "MONTH", "MORAL", "MOTOR", "MOUNT", "MOUSE", "MOUTH", "MOVIE",
    "MUSIC", "NAIVE", "NARROW", "NASTY", "NATION", "NATURE", "NEARBY", "NEEDLE", "NEGATE", "NERVE",
    "NEVER", "NEWLY", "NIGHT", "NINJA", "NOBLE", "NOISE", "NORTH", "NOTED", "NOVEL", "NURSE",
    "NYMPH", "OCCUR", "OCEAN", "OFFER", "OFTEN", "OLIVE", "ONSET", "OPERA", "ORBIT", "ORDER",
    "OTHER", "OUGHT", "OUTER", "OVERT", "OWNER", "OXIDE", "OZONE", "PAINT", "PANEL", "PANIC",
    "PAPER", "PARTY", "PASTE", "PATCH", "PAUSE", "PEACE", "PEARL", "PENAL", "PENNY", "PHASE",
    "PHONE", "PHOTO", "PIANO", "PIECE", "PILOT", "PITCH", "PIXEL", "PLACE", "PLAIN", "PLANE",
    "PLANT", "PLATE", "PLAZA", "PLEAD", "PLUCK", "PLUMB", "PLUME", "PLUMP", "PLUNGE", "POINT",
    "POLAR", "POUND", "POWER", "PRESS", "PRICE", "PRIDE", "PRIME", "PRINT", "PRIOR", "PRIZE",
    "PROBE", "PROOF", "PROSE", "PROUD", "PROVE", "PROXY", "PSALM", "PULSE", "PUNCH", "PUPIL",
    "PURSE", "QUEEN", "QUEST", "QUEUE", "QUICK", "QUIET", "QUILT", "QUITE", "QUOTA", "QUOTE",
    "RADAR", "RADIO", "RAISE", "RALLY", "RANCH", "RANGE", "RAPID", "RATIO", "REACH", "REACT",
    "REALM", "REBEL", "REIGN", "RELAX", "RENEW", "REPLY", "RIDER", "RIDGE", "RIFLE", "RIGHT",
    "RIGID", "RISKY", "RIVAL", "RIVER", "ROBIN", "ROBOT", "ROCKY", "ROGUE", "ROOMY", "ROUND",
    "ROUTE", "ROVER", "ROYAL", "RUGBY", "RUINS", "RULER", "RURAL", "SAINT", "SALAD", "SAUCE",
    "SCALE", "SCARE", "SCENE", "SCENT", "SCOPE", "SCORE", "SCOUT", "SCRAP", "SEIZE", "SENSE",
    "SERVE", "SEVEN", "SHADE", "SHAFT", "SHAKE", "SHALL", "SHAME", "SHAPE", "SHARE", "SHARK",
    "SHARP", "SHAVE", "SHEEP", "SHEER", "SHEET", "SHELF", "SHELL", "SHIFT", "SHINE", "SHIRE",
    "SHIRT", "SHOCK", "SHORE", "SHORT", "SHOUT", "SIGHT", "SILLY", "SINCE", "SIXTH", "SIXTY",
    "SIZED", "SKILL", "SKULL", "SLAVE", "SLEEP", "SLICE", "SLIDE", "SLOPE", "SMALL", "SMART",
    "SMELL", "SMILE", "SMOKE", "SNAKE", "SOLAR", "SOLID", "SOLVE", "SORRY", "SOUND", "SOUTH",
    "SPACE", "SPARE", "SPARK", "SPEAK", "SPEED", "SPELL", "SPEND", "SPICE", "SPINE", "SPITE",
    "SPLIT", "SPOKE", "SPOON", "SPORT", "SPRAY", "SQUAD", "STACK", "STAFF", "STAGE", "STAKE",
    "STALE", "STALL", "STAMP", "STAND", "STARE", "STARK", "START", "STATE", "STAYS", "STEAK",
    "STEAL", "STEAM", "STEEL", "STEEP", "STEER", "STERN", "STICK", "STIFF", "STILL", "STOCK",
    "STONE", "STOOD", "STOOL", "STORE", "STORM", "STORY", "STOVE", "STRAP", "STRAW", "STRAY",
    "STRIP", "STUCK", "STUDY", "STUFF", "STYLE", "SUGAR", "SUITE", "SUNNY", "SUPER", "SURGE",
    "SWAMP", "SWARM", "SWEAR", "SWEAT", "SWEEP", "SWEET", "SWEPT", "SWIFT", "SWING", "SWIRL",
    "SWORD", "SWORE", "SWORN", "TABLE", "TASTE", "TEACH", "TEETH", "TEMPO", "TENET", "TENSE",
    "TERMS", "TESTY", "TEXAS", "THANK", "THEFT", "THEIR", "THEME", "THERE", "THESE", "THICK",
    "THIEF", "THING", "THINK", "THIRD", "THORN", "THOSE", "THREE", "THREW", "THROW", "THUMB",
    "TIDAL", "TIGER", "TIGHT", "TIMER", "TITLE", "TODAY", "TOKEN", "TOPIC", "TORCH", "TOTAL",
    "TOUCH", "TOUGH", "TOWEL", "TOWER", "TOXIC", "TRACE", "TRACK", "TRADE", "TRAIL", "TRAIN",
    "TRAIT", "TRASH", "TREAT", "TREND", "TRIAL", "TRIBE", "TRICK", "TRIED", "TRIES", "TROOP",
    "TRUCK", "TRULY", "TRUMP", "TRUNK", "TRUST", "TRUTH", "TUMOR", "TWICE", "TWIST", "ULTRA",
    "UNCLE", "UNDER", "UNION", "UNITE", "UNITY", "UNTIL", "UPPER", "UPSET", "URBAN", "USAGE",
    "USUAL", "UTTER", "VALID", "VALUE", "VAULT", "VERSE", "VIDEO", "VIGOR", "VINYL", "VIOLA",
    "VIRAL", "VIRUS", "VISIT", "VITAL", "VIVID", "VOCAL", "VODKA", "VOICE", "VOTER", "WAGON",
    "WASTE", "WATCH", "WATER", "WEARY", "WEAVE", "WEDGE", "WEIGH", "WEIRD", "WHALE", "WHEAT",
    "WHEEL", "WHERE", "WHICH", "WHILE", "WHITE", "WHOLE", "WHOSE", "WIDEN", "WIDTH", "WITCH",
    "WOMAN", "WORLD", "WORRY", "WORSE", "WORST", "WORTH", "WOULD", "WOUND", "WRATH", "WRITE",
    "WRONG", "WROTE", "YACHT", "YIELD", "YOUNG", "YOUTH", "ZEBRA",
]

# 确保单词都是5字母
VALID_WORDS = [w for w in WORD_LIST if len(w) == 5]


class WordleGame:
    """Wordle 游戏主逻辑"""

    def __init__(self):
        self.target_word = random.choice(VALID_WORDS)
        self.guesses = []           # 已猜测的单词列表
        self.current_guess = ""     # 当前正在输入的字母
        self.max_attempts = 6
        self.game_over = False
        self.won = False
        self.letter_status = {}     # 字母状态: {char: 'green'|'yellow'|'gray'}
        self.flip_animation = 0     # 简单翻转动画计时
        self.show_result = False    # 是否显示结果弹窗
        self.result_timer = 0

    def add_letter(self, letter):
        """添加字母到当前猜测"""
        if len(self.current_guess) < 5 and not self.game_over:
            self.current_guess += letter

    def remove_letter(self):
        """删除最后一个字母"""
        if len(self.current_guess) > 0 and not self.game_over:
            self.current_guess = self.current_guess[:-1]

    def submit_guess(self):
        """提交当前猜测"""
        if self.game_over or len(self.current_guess) != 5:
            return False

        word = self.current_guess.upper()
        self.guesses.append(word)

        # 检查结果
        target = list(self.target_word)
        result = [''] * 5
        target_used = [False] * 5

        # 第一遍: 标记绿色(位置正确)
        for i in range(5):
            if word[i] == target[i]:
                result[i] = 'green'
                target_used[i] = True

        # 第二遍: 标记黄色(字母正确但位置不对)
        for i in range(5):
            if result[i] == 'green':
                continue
            for j in range(5):
                if not target_used[j] and word[i] == target[j]:
                    result[i] = 'yellow'
                    target_used[j] = True
                    break

        # 第三遍: 标记灰色
        for i in range(5):
            if result[i] == '':
                result[i] = 'gray'

        # 更新字母状态
        for i, letter in enumerate(word):
            current = self.letter_status.get(letter)
            if result[i] == 'green':
                self.letter_status[letter] = 'green'
            elif result[i] == 'yellow' and current != 'green':
                self.letter_status[letter] = 'yellow'
            elif result[i] == 'gray' and current not in ('green', 'yellow'):
                self.letter_status[letter] = 'gray'

        # 检查是否胜利
        if word == self.target_word:
            self.won = True
            self.game_over = True
            self.show_result = True
            self.result_timer = 60
        elif len(self.guesses) >= self.max_attempts:
            self.game_over = True
            self.show_result = True
            self.result_timer = 120

        self.current_guess = ""
        return True

    def get_result_for_guess(self, guess_idx):
        """获取某次猜测的每个字母结果"""
        if guess_idx >= len(self.guesses):
            return None
        word = self.guesses[guess_idx]
        target = list(self.target_word)
        result = [''] * 5
        target_used = [False] * 5

        for i in range(5):
            if word[i] == target[i]:
                result[i] = 'green'
                target_used[i] = True

        for i in range(5):
            if result[i] == 'green':
                continue
            for j in range(5):
                if not target_used[j] and word[i] == target[j]:
                    result[i] = 'yellow'
                    target_used[j] = True
                    break

        for i in range(5):
            if result[i] == '':
                result[i] = 'gray'

        return result


def draw_text(surface, text, x, y, font, color=COLOR_TEXT, center=True):
    """绘制文字"""
    text_surf = font.render(text, True, color)
    if center:
        rect = text_surf.get_rect(center=(x, y))
    else:
        rect = text_surf.get_rect(topleft=(x, y))
    surface.blit(text_surf, rect)


def draw_rounded_rect(surface, rect, color, radius=8):
    """绘制圆角矩形"""
    r = rect
    pygame.draw.rect(surface, color, r, border_radius=radius)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Wordle 猜词游戏")
    clock = pygame.time.Clock()

    # 字体
    title_font = pygame.font.SysFont("Arial", 36, bold=True)
    letter_font = pygame.font.SysFont("Arial", 34, bold=True)
    key_font = pygame.font.SysFont("Arial", 22, bold=True)
    message_font = pygame.font.SysFont("Arial", 28, bold=True)
    small_font = pygame.font.SysFont("Arial", 16)

    game = WordleGame()
    message = ""
    message_timer = 0
    running = True

    # 键盘位置计算
    keyboard_keys = []
    for row_idx, row in enumerate(KEYBOARD_ROWS):
        row_keys = []
        for col_idx, letter in enumerate(row):
            total_width = len(row) * (KEY_WIDTH + KEY_GAP) - KEY_GAP
            row_start = (SCREEN_WIDTH - total_width) // 2
            x = row_start + col_idx * (KEY_WIDTH + KEY_GAP)
            y = KEYBOARD_Y + row_idx * (KEY_HEIGHT + KEY_GAP)
            row_keys.append({
                'letter': letter,
                'rect': pygame.Rect(x, y, KEY_WIDTH, KEY_HEIGHT),
                'color': COLOR_KEY_BG,
            })
        keyboard_keys.append(row_keys)

    while running:
        screen.fill(COLOR_BG)

        # ---- 事件处理 ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if game.show_result:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        game = WordleGame()
                        message = ""
                        message_timer = 0
                    continue

                if event.key == pygame.K_RETURN:
                    if len(game.current_guess) == 5:
                        if game.current_guess.upper() not in VALID_WORDS:
                            message = "单词不在词库中!"
                            message_timer = 90
                        else:
                            was = game.submit_guess()
                            if was:
                                message = ""
                                message_timer = 0
                elif event.key == pygame.K_BACKSPACE:
                    game.remove_letter()
                elif event.key == pygame.K_ESCAPE:
                    running = False
                elif event.unicode.isalpha():
                    game.add_letter(event.unicode.upper())

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if game.show_result:
                    game = WordleGame()
                    message = ""
                    message_timer = 0
                    continue
                for row in keyboard_keys:
                    for key in row:
                        if key['rect'].collidepoint(mx, my):
                            game.add_letter(key['letter'])
                            break
                # 检测回车键(虚拟)
                # 检测删除键(虚拟)

        # ---- 更新键盘颜色 ----
        for row in keyboard_keys:
            for key in row:
                letter = key['letter']
                status = game.letter_status.get(letter)
                if status == 'green':
                    key['color'] = COLOR_GREEN
                elif status == 'yellow':
                    key['color'] = COLOR_YELLOW
                elif status == 'gray':
                    key['color'] = COLOR_GRAY
                else:
                    key['color'] = COLOR_KEY_BG

        # ---- 消息计时 ----
        if message_timer > 0:
            message_timer -= 1
        else:
            message = ""

        # ---- 绘制标题 ----
        draw_text(screen, "WORDLE", SCREEN_WIDTH // 2, 35, title_font, (83, 141, 78))

        # ---- 绘制网格 ----
        for row_idx in range(game.max_attempts):
            for col_idx in range(5):
                x = GRID_OFFSET_X + col_idx * (GRID_SIZE + GRID_GAP)
                y = GRID_OFFSET_Y + row_idx * (GRID_SIZE + GRID_GAP)
                rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)

                if row_idx < len(game.guesses):
                    # 已提交的猜测
                    letter = game.guesses[row_idx][col_idx]
                    results = game.get_result_for_guess(row_idx)
                    color = COLOR_GREEN if results[col_idx] == 'green' else \
                        COLOR_YELLOW if results[col_idx] == 'yellow' else COLOR_GRAY
                    draw_rounded_rect(screen, rect, color, 4)
                    draw_text(screen, letter, rect.centerx, rect.centery, letter_font, COLOR_TEXT)
                elif row_idx == len(game.guesses):
                    # 当前正在输入的
                    if col_idx < len(game.current_guess):
                        color = COLOR_EMPTY
                        draw_rounded_rect(screen, rect, color, 4)
                        pygame.draw.rect(screen, COLOR_BORDER, rect, 2, border_radius=4)
                        draw_text(screen, game.current_guess[col_idx], rect.centerx, rect.centery, letter_font, COLOR_TEXT)
                    else:
                        draw_rounded_rect(screen, rect, COLOR_EMPTY, 4)
                        pygame.draw.rect(screen, COLOR_BORDER, rect, 2, border_radius=4)
                else:
                    # 空行
                    draw_rounded_rect(screen, rect, COLOR_EMPTY, 4)
                    pygame.draw.rect(screen, COLOR_BORDER, rect, 2, border_radius=4)

        # ---- 绘制键盘 ----
        for row in keyboard_keys:
            for key in row:
                draw_rounded_rect(screen, key['rect'], key['color'], 6)
                draw_text(screen, key['letter'], key['rect'].centerx, key['rect'].centery, key_font, COLOR_KEY_TEXT)

        # ---- 绘制消息 ----
        if message:
            msg_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 40)
            msg_rect.center = (SCREEN_WIDTH // 2, GRID_OFFSET_Y - 30)
            draw_rounded_rect(screen, msg_rect, (30, 30, 30), 8)
            draw_text(screen, message, SCREEN_WIDTH // 2, msg_rect.centery, message_font, (255, 100, 100))

        # ---- 绘制结果弹窗 ----
        if game.show_result:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            result_bg = pygame.Rect(0, 0, 320, 200)
            result_bg.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)
            draw_rounded_rect(screen, result_bg, (30, 30, 30), 16)
            pygame.draw.rect(screen, (80, 80, 80), result_bg, 2, border_radius=16)

            if game.won:
                draw_text(screen, "🎉 恭喜你赢了! 🎉", SCREEN_WIDTH // 2, result_bg.top + 50,
                          message_font, (83, 141, 78))
                attempts = len(game.guesses)
                draw_text(screen, f"用了 {attempts}/6 次", SCREEN_WIDTH // 2, result_bg.top + 95,
                          small_font, COLOR_TEXT)
            else:
                draw_text(screen, "😢 游戏结束", SCREEN_WIDTH // 2, result_bg.top + 40,
                          message_font, (255, 100, 100))
                draw_text(screen, f"答案是: {game.target_word}", SCREEN_WIDTH // 2, result_bg.top + 90,
                          letter_font, (181, 159, 59))

            draw_text(screen, "点击或按空格键重新开始", SCREEN_WIDTH // 2, result_bg.top + 150,
                      small_font, (150, 150, 150))

        # ---- 提示文字 ----
        if not game.game_over:
            hint = "输入字母 → 回车提交"
            draw_text(screen, hint, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 25, small_font, (100, 100, 100))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()