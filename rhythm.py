"""
节奏大师 (Rhythm Game)
- 4 个音轨，按 A S D F 键击打下落音符
- 支持长按音符、连击评分
- 纯 Pygame 实现，无外部资源依赖
"""

import pygame
import random
import sys
import math

# ==================== 常量 ====================
WIDTH, HEIGHT = 480, 700
FPS = 60

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 80)
PURPLE = (200, 50, 255)
ORANGE = (255, 150, 50)
GRAY = (60, 60, 60)
LIGHT_GRAY = (150, 150, 150)
DARK = (20, 20, 30)
HIT_ZONE_COLOR = (80, 200, 255)
LANE_BG = (30, 30, 45)

# 音轨设置
LANE_COUNT = 4
LANE_KEYS = [pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f]
LANE_NAMES = ["A", "S", "D", "F"]
LANE_COLORS = [(255, 80, 80), (80, 255, 80), (80, 150, 255), (255, 255, 80)]
LANE_WIDTH = 80
LANE_GAP = 10
LANES_START_X = (WIDTH - LANE_COUNT * LANE_WIDTH - (LANE_COUNT - 1) * LANE_GAP) // 2

# 判定区
HIT_ZONE_Y = HEIGHT - 160
HIT_ZONE_HEIGHT = 6
PERFECT_RANGE = 25      # ±25px = Perfect
GOOD_RANGE = 50         # ±50px = Good
BAD_RANGE = 80          # ±80px = Bad

# 音符
NOTE_SPEED_BASE = 4.0
NOTE_SPEED_INCREASE = 0.3
SPAWN_INTERVAL_BASE = 55  # 帧

# 评分
SCORE_PERFECT = 300
SCORE_GOOD = 150
SCORE_BAD = 20

# ==================== 状态 ====================
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("节奏大师 - Rhythm Game")
clock = pygame.time.Clock()
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 28)
font_tiny = pygame.font.Font(None, 20)


class Note:
    """单个音符"""

    def __init__(self, lane, y, is_hold=False, hold_duration=0):
        self.lane = lane
        self.x = self._lane_x()
        self.y = y
        self.radius = 16
        self.is_hold = is_hold
        self.hold_duration = hold_duration  # 长按持续帧数
        self.hold_remaining = hold_duration if is_hold else 0
        self.hit = False
        self.missed = False
        self.judgment = None  # "perfect", "good", "bad"
        self.judgment_timer = 0
        self.active = True  # 是否仍在游戏中

    def _lane_x(self):
        return LANES_START_X + self.lane * (LANE_WIDTH + LANE_GAP) + LANE_WIDTH // 2

    def update(self):
        if not self.active:
            return
        self.y += NOTE_SPEED_BASE
        # 超出底部判定为 Miss
        if self.y > HIT_ZONE_Y + BAD_RANGE + 50:
            if not self.hit:
                self.missed = True
                self.active = False
                return "miss"
        if self.judgment_timer > 0:
            self.judgment_timer -= 1
        return None

    def check_hit(self, hold_held=False):
        """检测是否在判定区内被击中"""
        if self.hit or not self.active:
            return None
        dist = abs(self.y - HIT_ZONE_Y)
        if dist <= PERFECT_RANGE:
            return self._hit("perfect")
        elif dist <= GOOD_RANGE:
            return self._hit("good")
        elif dist <= BAD_RANGE:
            return self._hit("bad")
        return None

    def _hit(self, judgment):
        self.hit = True
        self.judgment = judgment
        self.judgment_timer = 20
        if judgment == "perfect":
            self.active = False
        elif judgment == "good":
            self.active = False
        elif judgment == "bad":
            self.active = False
        return judgment

    def draw(self, surface):
        if not self.active:
            return
        color = LANE_COLORS[self.lane]
        # 音符主体 - 菱形
        points = []
        r = self.radius
        cx, cy = self.x, self.y
        for i in range(4):
            angle = math.radians(45 + i * 90)
            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            points.append((px, py))
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, WHITE, points, 2)

        # 如果是长按音符，画延长线
        if self.is_hold and not self.hit:
            hold_len = min(self.hold_duration * 0.5, 60)
            end_y = self.y + hold_len
            for dy in range(0, int(hold_len), 4):
                alpha = 255 - int(dy / hold_len * 200)
                c = tuple(max(0, min(255, v - (255 - alpha))) for v in color)
                pygame.draw.rect(
                    surface,
                    c,
                    (self.x - 4, self.y + dy, 8, 4),
                )

        # 长按提示文字
        if self.is_hold:
            txt = font_tiny.render("HOLD", True, WHITE)
            surface.blit(txt, (self.x - 18, self.y - 30))

    def draw_judgment(self, surface):
        """绘制判定文字"""
        if self.judgment and self.judgment_timer > 0:
            color_map = {
                "perfect": (255, 255, 100),
                "good": GREEN,
                "bad": LIGHT_GRAY,
            }
            text_map = {
                "perfect": "PERFECT!",
                "good": "GOOD",
                "bad": "BAD",
            }
            color = color_map.get(self.judgment, WHITE)
            text = text_map.get(self.judgment, "")
            txt_surf = font_small.render(text, True, color)
            alpha = int(self.judgment_timer / 20 * 255)
            txt_surf.set_alpha(alpha)
            surface.blit(txt_surf, (self.x - txt_surf.get_width() // 2, self.y - 50))


class RhythmGame:
    """节奏大师主游戏类"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.notes = []
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.perfect_count = 0
        self.good_count = 0
        self.bad_count = 0
        self.miss_count = 0
        self.frame_count = 0
        self.spawn_counter = 0
        self.game_over = False
        self.difficulty = 1
        self.note_speed = NOTE_SPEED_BASE
        self.spawn_interval = SPAWN_INTERVAL_BASE
        self.hold_key_states = {k: False for k in LANE_KEYS}
        self.combo_display_timer = 0
        self.judgment_texts = []  # 浮动判定文字
        self.background_offset = 0
        self.particles = []

        # 生成初始音符队列
        self._generate_notes(15)

    def _generate_notes(self, count):
        """生成一批音符"""
        for _ in range(count):
            lane = random.randint(0, LANE_COUNT - 1)
            y_offset = -100 - random.randint(0, 600)
            is_hold = random.random() < 0.15  # 15% 概率长按
            hold_dur = random.randint(30, 80) if is_hold else 0
            self.notes.append(Note(lane, y_offset, is_hold, hold_dur))

    def _add_particles(self, x, y, color, count=8):
        """添加粒子效果"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": 20,
                "color": color,
                "size": random.randint(2, 5),
            })

    def handle_event(self, event):
        if self.game_over:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.reset()
            return

        if event.type == pygame.KEYDOWN:
            if event.key in LANE_KEYS:
                lane = LANE_KEYS.index(event.key)
                self.hold_key_states[event.key] = True
                self._hit_lane(lane)
            elif event.key == pygame.K_ESCAPE:
                self.game_over = True

        elif event.type == pygame.KEYUP:
            if event.key in LANE_KEYS:
                self.hold_key_states[event.key] = False

    def _hit_lane(self, lane):
        """击打指定音轨"""
        # 找到该音轨最接近判定区的音符
        best_note = None
        best_dist = BAD_RANGE + 1
        for note in self.notes:
            if not note.active or note.hit or note.lane != lane:
                continue
            dist = abs(note.y - HIT_ZONE_Y)
            if dist < best_dist:
                best_dist = dist
                best_note = note

        if best_note is None:
            return

        result = best_note.check_hit()
        if result:
            self._apply_result(result, best_note)

    def _apply_result(self, judgment, note):
        """根据判定结果计分"""
        if judgment == "perfect":
            score_gain = SCORE_PERFECT
            self.combo += 1
            self.perfect_count += 1
            self._add_particles(note.x, note.y, LANE_COLORS[note.lane], 12)
        elif judgment == "good":
            score_gain = SCORE_GOOD
            self.combo += 1
            self.good_count += 1
            self._add_particles(note.x, note.y, LANE_COLORS[note.lane], 6)
        elif judgment == "bad":
            score_gain = SCORE_BAD
            self.combo = 0
            self.bad_count += 1
        else:
            return

        # 连击加成
        combo_bonus = min(self.combo // 10, 5)
        score_gain += combo_bonus * 50

        self.score += score_gain
        self.max_combo = max(self.max_combo, self.combo)
        self.combo_display_timer = 60

        # 更新难度
        self.difficulty = 1 + self.score // 5000
        self.note_speed = NOTE_SPEED_BASE + self.difficulty * 0.2
        self.spawn_interval = max(25, SPAWN_INTERVAL_BASE - self.difficulty * 3)

    def update(self):
        if self.game_over:
            return

        self.frame_count += 1

        # 更新音符
        for note in self.notes[:]:
            result = note.update()
            if result == "miss":
                self.combo = 0
                self.miss_count += 1

        # 移除失效音符
        self.notes = [n for n in self.notes if n.active or n.judgment_timer > 0]

        # 生成新音符
        self.spawn_counter += 1
        if self.spawn_counter >= self.spawn_interval:
            self.spawn_counter = 0
            self._generate_notes(1)

        # 更新粒子
        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.1  # 重力
            p["life"] -= 1
            if p["life"] <= 0:
                self.particles.remove(p)

        # 背景滚动
        self.background_offset = (self.background_offset + 1) % 30

        # 判定是否结束
        if self.combo_display_timer > 0:
            self.combo_display_timer -= 1

    def draw(self, surface):
        # 背景
        surface.fill(DARK)
        self._draw_background(surface)

        # 判定区
        self._draw_hit_zone(surface)

        # 音轨背景
        self._draw_lanes(surface)

        # 音符
        for note in self.notes:
            note.draw(surface)

        # 判定文字
        for note in self.notes:
            note.draw_judgment(surface)

        # 粒子
        for p in self.particles:
            alpha = int(p["life"] / 20 * 255)
            c = tuple(v for v in p["color"])
            pygame.draw.circle(surface, c, (int(p["x"]), int(p["y"])), p["size"])

        # HUD
        self._draw_hud(surface)

        # 结束画面
        if self.game_over:
            self._draw_game_over(surface)

    def _draw_background(self, surface):
        """绘制动态背景"""
        for i in range(12):
            y = (i * 60 + self.background_offset * 2) % (HEIGHT + 60) - 30
            alpha = 30 + 20 * math.sin(i * 0.5 + self.frame_count * 0.02)
            pygame.draw.line(
                surface,
                (40, 40, 60),
                (WIDTH // 2 - 150 + i * 25, y),
                (WIDTH // 2 - 150 + i * 25, y + 20),
                1
            )

        # 扫描线 (用半透明 Surface)
        scanline = pygame.Surface((WIDTH, 2), pygame.SRCALPHA)
        scanline.fill((0, 0, 0, 15))
        for i in range(0, HEIGHT, 4):
            surface.blit(scanline, (0, i))

    def _draw_lanes(self, surface):
        """绘制音轨"""
        for i in range(LANE_COUNT):
            x = LANES_START_X + i * (LANE_WIDTH + LANE_GAP)
            rect = pygame.Rect(x, 0, LANE_WIDTH, HEIGHT)
            pygame.draw.rect(surface, LANE_BG, rect)
            pygame.draw.rect(surface, (50, 50, 70), rect, 1)

            # 按键提示
            if self.hold_key_states[LANE_KEYS[i]]:
                glow = pygame.Surface((LANE_WIDTH, HEIGHT), pygame.SRCALPHA)
                glow.fill((*LANE_COLORS[i], 30))
                surface.blit(glow, (x, 0))

            # 底部键名
            key_text = font_medium.render(LANE_NAMES[i], True, LANE_COLORS[i])
            surface.blit(key_text, (x + LANE_WIDTH // 2 - key_text.get_width() // 2, HEIGHT - 50))

    def _draw_hit_zone(self, surface):
        """绘制判定区域"""
        x = LANES_START_X
        w = LANE_COUNT * LANE_WIDTH + (LANE_COUNT - 1) * LANE_GAP

        # 判定线
        pygame.draw.line(surface, HIT_ZONE_COLOR, (x, HIT_ZONE_Y), (x + w, HIT_ZONE_Y), 3)

        # Perfect 区域 (半透明)
        perfect_surf = pygame.Surface((w, PERFECT_RANGE * 2), pygame.SRCALPHA)
        perfect_surf.fill((*HIT_ZONE_COLOR, 20))
        surface.blit(perfect_surf, (x, HIT_ZONE_Y - PERFECT_RANGE))
        perfect_border = pygame.Surface((w, PERFECT_RANGE * 2), pygame.SRCALPHA)
        perfect_border.fill((*HIT_ZONE_COLOR, 8))
        surface.blit(perfect_border, (x + 2, HIT_ZONE_Y - PERFECT_RANGE + 2))

        # Good 区域 (半透明)
        good_surf = pygame.Surface((w, GOOD_RANGE * 2), pygame.SRCALPHA)
        good_surf.fill((*HIT_ZONE_COLOR, 10))
        surface.blit(good_surf, (x, HIT_ZONE_Y - GOOD_RANGE))

        # 脉动效果
        pulse = 40 + 20 * math.sin(self.frame_count * 0.1)
        glow_surf = pygame.Surface((w, 6), pygame.SRCALPHA)
        glow_surf.fill((*HIT_ZONE_COLOR, int(pulse)))
        surface.blit(glow_surf, (x, HIT_ZONE_Y - 3))

    def _draw_hud(self, surface):
        """绘制 HUD"""
        # 分数
        score_text = font_large.render(str(self.score), True, WHITE)
        surface.blit(score_text, (20, 15))

        # 连击
        if self.combo >= 2:
            combo_text = font_medium.render(f"{self.combo} COMBO", True, YELLOW)
            surface.blit(combo_text, (20, 70))

        # 统计
        stats_text = font_tiny.render(
            f"Perfect: {self.perfect_count}  Good: {self.good_count}  Bad: {self.bad_count}  Miss: {self.miss_count}",
            True,
            LIGHT_GRAY,
        )
        surface.blit(stats_text, (20, 115))

        # 难度
        diff_text = font_tiny.render(f"Level {self.difficulty}", True, ORANGE)
        surface.blit(diff_text, (WIDTH - 100, 20))

        # 底部操作提示
        hint = font_tiny.render("A S D F = 击打  |  ESC = 退出  |  SPACE = 重新开始", True, GRAY)
        surface.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 20))

    def _draw_game_over(self, surface):
        """绘制结束画面"""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        title = font_large.render("GAME OVER", True, RED)
        surface.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 150))

        final_score = font_medium.render(f"Final Score: {self.score}", True, WHITE)
        surface.blit(final_score, (WIDTH // 2 - final_score.get_width() // 2, HEIGHT // 2 - 80))

        stats = font_small.render(
            f"Perfect: {self.perfect_count}  Good: {self.good_count}  Bad: {self.bad_count}  Miss: {self.miss_count}",
            True,
            LIGHT_GRAY,
        )
        surface.blit(stats, (WIDTH // 2 - stats.get_width() // 2, HEIGHT // 2 - 30))

        combo_text = font_small.render(f"Max Combo: {self.max_combo}", True, YELLOW)
        surface.blit(combo_text, (WIDTH // 2 - combo_text.get_width() // 2, HEIGHT // 2 + 10))

        restart = font_small.render("Press SPACE to Restart", True, GREEN)
        surface.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT // 2 + 70))


def main():
    game = RhythmGame()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_event(event)

        game.update()
        game.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()