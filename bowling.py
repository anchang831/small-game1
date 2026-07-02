#!/usr/bin/env python3
"""
bowling.py - 保龄球游戏

经典十瓶保龄球模拟游戏。鼠标左右移动瞄准，按住左键向下拖拽蓄力，松开发球。
标准10局计分制，包含 Strike/Spare 奖励分计算。

操作说明:
  Mouse Move   → 左右瞄准
  Click+Drag ↓ → 蓄力（拖拽越远力度越大）
  Release      → 发球
  R            → 重新开始
  ESC          → 退出
"""

import pygame
import math
import sys
from enum import Enum

# ── 常量 ──────────────────────────────────────────────
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
FPS = 60

# 球道区域（俯视图，上方为球瓶区，下方为发球区）
LANE_LEFT = 320
LANE_RIGHT = 580
LANE_WIDTH = LANE_RIGHT - LANE_LEFT
LANE_TOP = 90
LANE_BOTTOM = 580
LANE_HEIGHT = LANE_BOTTOM - LANE_TOP

BALL_RADIUS = 11
PIN_RADIUS = 8
BALL_START_Y = LANE_BOTTOM - 40

# 颜色
COLOR_BG = (30, 30, 40)
COLOR_LANE = (180, 150, 110)
COLOR_LANE_BORDER = (140, 110, 80)
COLOR_GUTTER = (50, 50, 60)
COLOR_BALL = (200, 60, 60)
COLOR_BALL_SHINE = (255, 150, 150)
COLOR_PIN = (240, 235, 225)
COLOR_PIN_STRIPE = (200, 50, 50)
COLOR_PIN_DOWN = (180, 170, 160)
COLOR_TEXT = (255, 255, 230)
COLOR_ACCENT = (255, 200, 50)

# 物理参数
FRICTION = 0.98
PIN_FRICTION = 0.96
WALL_BOUNCE = 0.4
BALL_PIN_BOUNCE = 0.5
PIN_PIN_BOUNCE = 0.3
KNOCK_DOWN_DIST = 28       # 位移超过此距离即判为击倒
SETTLE_VELOCITY = 0.5      # 静止判定阈值

# 球瓶布局
PIN_SPACING = 24
PIN_ROW_OFFSETS = [4, 3, 2, 1]
PIN_CENTER_X = (LANE_LEFT + LANE_RIGHT) // 2
PIN_START_Y = LANE_TOP + 40


# ── 工具函数 ──────────────────────────────────────
def pin_positions():
    """返回10个球瓶在三角形排列中的 (x, y) 坐标"""
    positions = []
    for row, count in enumerate(PIN_ROW_OFFSETS):
        y = PIN_START_Y + row * (PIN_SPACING * math.sqrt(3) / 2)
        row_width = (count - 1) * PIN_SPACING
        for col in range(count):
            x = PIN_CENTER_X - row_width / 2 + col * PIN_SPACING
            positions.append((x, y))
    return positions


def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def clamp(val, lo, hi):
    return max(lo, min(hi, val))


# ── 游戏状态 ──────────────────────────────────────
class GameState(Enum):
    AIM = 1        # 瞄准
    POWER = 2      # 蓄力
    ROLLING = 3    # 球运动中
    SETTLING = 4   # 球瓶稳定中
    FRAME_END = 5  # 展示结果
    GAME_OVER = 6  # 游戏结束


# ── 球瓶 ──────────────────────────────────────────
class Pin:
    def __init__(self, x, y):
        self.start_x = x
        self.start_y = y
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.active = True
        self.knocked = False

    def reset(self):
        self.x = self.start_x
        self.y = self.start_y
        self.vx = 0.0
        self.vy = 0.0
        self.active = True
        self.knocked = False

    def update(self):
        if not self.active:
            return
        self.x += self.vx
        self.y += self.vy
        # 边界碰撞
        if self.x - PIN_RADIUS < LANE_LEFT:
            self.x = LANE_LEFT + PIN_RADIUS
            self.vx = -self.vx * WALL_BOUNCE
        elif self.x + PIN_RADIUS > LANE_RIGHT:
            self.x = LANE_RIGHT - PIN_RADIUS
            self.vx = -self.vx * WALL_BOUNCE
        if self.y - PIN_RADIUS < LANE_TOP:
            self.y = LANE_TOP + PIN_RADIUS
            self.vy = -self.vy * WALL_BOUNCE
        elif self.y + PIN_RADIUS > LANE_BOTTOM:
            self.y = LANE_BOTTOM - PIN_RADIUS
            self.vy = -self.vy * WALL_BOUNCE
        # 摩擦力
        self.vx *= PIN_FRICTION
        self.vy *= PIN_FRICTION
        if abs(self.vx) < 0.05 and abs(self.vy) < 0.05:
            self.vx = 0
            self.vy = 0
        # 判定击倒
        if distance((self.x, self.y), (self.start_x, self.start_y)) > KNOCK_DOWN_DIST:
            self.knocked = True

    def draw(self, surface):
        if not self.active:
            return
        offset_y = 3 if self.knocked else 0
        color = COLOR_PIN_DOWN if self.knocked else COLOR_PIN
        pygame.draw.circle(surface, color,
                           (int(self.x), int(self.y + offset_y)), PIN_RADIUS)
        if not self.knocked:
            r = pygame.Rect(int(self.x) - PIN_RADIUS + 2,
                            int(self.y) - 2, (PIN_RADIUS - 2) * 2, 4)
            pygame.draw.ellipse(surface, COLOR_PIN_STRIPE, r)


# ── 球 ────────────────────────────────────────────
class Ball:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = PIN_CENTER_X
        self.y = BALL_START_Y
        self.vx = 0.0
        self.vy = 0.0
        self.rolling = False
        self.active = True

    def launch(self, aim_x, power):
        dx = aim_x - self.x
        dy = LANE_TOP + 20 - self.y
        dist = math.hypot(dx, dy)
        if dist < 1:
            dx, dy = 0, -1
            dist = 1
        speed = 4 + power * 16
        self.vx = dx / dist * speed
        self.vy = dy / dist * speed
        self.rolling = True
        self.active = True

    def update(self):
        if not self.rolling:
            return
        self.x += self.vx
        self.y += self.vy
        if self.x - BALL_RADIUS < LANE_LEFT:
            self.x = LANE_LEFT + BALL_RADIUS
            self.vx = -self.vx * WALL_BOUNCE
        elif self.x + BALL_RADIUS > LANE_RIGHT:
            self.x = LANE_RIGHT - BALL_RADIUS
            self.vx = -self.vx * WALL_BOUNCE
        if self.y - BALL_RADIUS < LANE_TOP:
            self.y = LANE_TOP + BALL_RADIUS
            self.vy = -self.vy * WALL_BOUNCE
        elif self.y > LANE_BOTTOM + 50:
            self.rolling = False
            self.active = False
        self.vx *= FRICTION
        self.vy *= FRICTION
        if abs(self.vx) < 0.05 and abs(self.vy) < 0.05:
            self.vx = 0
            self.vy = 0
            if self.y > BALL_START_Y - 10:
                self.rolling = False

    def draw(self, surface):
        if not self.active and not self.rolling:
            return
        pygame.draw.circle(surface, COLOR_BALL,
                           (int(self.x), int(self.y)), BALL_RADIUS)
        pygame.draw.circle(surface, COLOR_BALL_SHINE,
                           (int(self.x) - 3, int(self.y) - 3), 4)


# ── 保龄球游戏主类 ────────────────────────────────
class BowlingGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Bowling - 保龄球")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("simhei", 48, bold=True)
        self.font_mid = pygame.font.SysFont("simhei", 28, bold=True)
        self.font_small = pygame.font.SysFont("simhei", 20)
        self.reset_game()

    # ── 初始化/重置 ──────────────────────────────
    def reset_game(self):
        self.state = GameState.AIM
        self.ball = Ball()
        self.pins = [Pin(x, y) for x, y in pin_positions()]
        self.frame = 1
        self.roll = 1
        self.rolls = []         # 每投记录: (pins_in_this_roll, is_strike, is_spare)
        self.frame_scores = [None] * 10
        self.prev_knocked = 0
        self.aim_x = PIN_CENTER_X
        self.power = 0.0
        self.dragging = False
        self.drag_start_y = 0
        self.settle_timer = 0
        self.message = ""

    # ── 帧分组 ──────────────────────────────────
    def get_tenth_rolls(self):
        """返回第10局的所有投球记录"""
        # 先找出前9局消耗了多少个rolls
        idx = 0
        for f in range(1, 10):
            if idx >= len(self.rolls):
                return []
            p1, st, _ = self.rolls[idx]
            if st:
                idx += 1
            else:
                idx += 2
        return list(self.rolls[idx:])

    def get_frame_rolls(self):
        """将 self.rolls 按帧分组"""
        frames = []
        idx = 0
        for f in range(1, 11):
            if idx >= len(self.rolls):
                break
            p1, strike, _ = self.rolls[idx]
            if f < 10:
                if strike:
                    frames.append((10, True, False, [p1]))
                    idx += 1
                else:
                    if idx + 1 < len(self.rolls):
                        p2, _, _ = self.rolls[idx + 1]
                        spare = (p1 + p2 == 10)
                        frames.append((p1 + p2, False, spare, [p1, p2]))
                        idx += 2
                    else:
                        break
            else:
                tenth = []
                while idx < len(self.rolls):
                    tenth.append(self.rolls[idx][0])
                    idx += 1
                total = sum(tenth)
                st = len(tenth) >= 1 and tenth[0] == 10
                sp = (not st and len(tenth) >= 2 and tenth[0] + tenth[1] == 10)
                frames.append((total, st, sp, tenth))
        return frames

    # ── 计分 ──────────────────────────────────────
    def calc_score(self):
        frames = self.get_frame_rolls()
        scores = []
        total = 0
        for fi, (pins, strike, spare, rolls) in enumerate(frames):
            if fi == 9:
                total += pins
                scores.append(total)
                continue
            if strike:
                bonus = 0
                cnt = 0
                for f2 in range(fi + 1, min(fi + 4, len(frames))):
                    for rp in frames[f2][3]:
                        if cnt < 2:
                            bonus += rp
                            cnt += 1
                total += 10 + bonus
            elif spare:
                bonus = frames[fi + 1][3][0] if fi + 1 < len(frames) else 0
                total += 10 + bonus
            else:
                total += pins
            scores.append(total)
        self.frame_scores = scores + [None] * (10 - len(scores))
        return total

    # ── 碰撞检测 ──────────────────────────────────
    def check_collisions(self):
        ball = self.ball
        if not ball.rolling:
            return
        # 球 vs 球瓶
        for pin in self.pins:
            if not pin.active or pin.knocked:
                continue
            d = distance((ball.x, ball.y), (pin.x, pin.y))
            if d < BALL_RADIUS + PIN_RADIUS:
                dx = pin.x - ball.x
                dy = pin.y - ball.y
                if d < 1:
                    dx, dy = 0, -1
                    d = 1
                force = math.hypot(ball.vx, ball.vy) * BALL_PIN_BOUNCE
                pin.vx += dx / d * force
                pin.vy += dy / d * force
                ball.vx -= dx / d * force * 0.3
                ball.vy -= dy / d * force * 0.3
        # 球瓶 vs 球瓶
        for i, p1 in enumerate(self.pins):
            if not p1.active or p1.knocked:
                continue
            for j, p2 in enumerate(self.pins):
                if j <= i or not p2.active or p2.knocked:
                    continue
                d = distance((p1.x, p1.y), (p2.x, p2.y))
                if d < PIN_RADIUS * 2:
                    dx = p2.x - p1.x
                    dy = p2.y - p1.y
                    if d < 1:
                        continue
                    overlap = PIN_RADIUS * 2 - d
                    p1.x -= dx / d * overlap / 2
                    p1.y -= dy / d * overlap / 2
                    p2.x += dx / d * overlap / 2
                    p2.y += dy / d * overlap / 2
                    force = math.hypot(p1.vx - p2.vx, p1.vy - p2.vy) * PIN_PIN_BOUNCE
                    p1.vx += dx / d * force
                    p1.vy += dy / d * force
                    p2.vx -= dx / d * force
                    p2.vy -= dy / d * force

    # ── 更新 ──────────────────────────────────────
    def update(self):
        if self.state == GameState.ROLLING:
            self.ball.update()
            self.check_collisions()
            for p in self.pins:
                p.update()
            if not self.ball.rolling or not self.ball.active:
                self.state = GameState.SETTLING
                self.settle_timer = 0
        elif self.state == GameState.SETTLING:
            self.settle_timer += 1
            settled = all(
                not p.active or (abs(p.vx) < SETTLE_VELOCITY and abs(p.vy) < SETTLE_VELOCITY)
                for p in self.pins
            )
            if settled and self.settle_timer > 30:
                self.end_roll()
        elif self.state == GameState.FRAME_END:
            self.settle_timer += 1
            if self.settle_timer > 90:
                self.next_roll()

    # ── 结束一次投球 ──────────────────────────────
    def end_roll(self):
        now_knocked = sum(1 for p in self.pins if p.knocked)
        new_knocked = now_knocked - self.prev_knocked
        is_strike = (self.roll == 1 and now_knocked == 10)
        is_spare = (self.roll == 2 and now_knocked == 10)

        self.rolls.append((new_knocked, is_strike, is_spare))
        self.prev_knocked = now_knocked

        # 消息
        if is_strike:
            self.message = "🔥 STRIKE! 🔥"
        elif is_spare:
            self.message = "✨ SPARE! ✨"
        elif new_knocked > 0:
            self.message = f"击倒 {new_knocked} 瓶!"
        else:
            self.message = "😅 没击中..."

        # 判断是否需要继续投球（第10局特别处理）
        if self.frame < 10:
            frame_done = is_strike or self.roll >= 2
        else:
            tenth = self.get_tenth_rolls()
            # 第10局规则:
            # - 第1球strike → 需要总共3球
            # - 前2球spare → 需要总共3球
            # - 其他 → 2球结束
            need_third = (
                (len(tenth) >= 1 and tenth[0][1]) or          # 第1球strike
                (len(tenth) >= 2 and tenth[0][0] + tenth[1][0] == 10)  # spare
            )
            frame_done = (len(tenth) >= 3) or (len(tenth) >= 2 and not need_third)

        if frame_done:
            self.state = GameState.FRAME_END
            self.settle_timer = 0
        else:
            # 继续投球（同一帧内的第2球或第10局的奖励球）
            self.roll += 1
            if self.frame == 10:
                # 第10局奖励球：如果前一球是strike，重置球瓶
                tenth = self.get_tenth_rolls()
                if len(tenth) >= 2 and tenth[-2][1]:
                    self.reset_pins()
                elif len(tenth) == 2 and tenth[0][0] + tenth[1][0] == 10:
                    self.reset_pins()
            self.ball.reset()
            self.state = GameState.AIM
            self.power = 0.0
            self.dragging = False

    # ── 进入下一投/下一局 ──────────────────────────
    def next_roll(self):
        if self.frame >= 10:
            self.state = GameState.GAME_OVER
            self.calc_score()
            return
        total_knocked = sum(1 for p in self.pins if p.knocked)
        if total_knocked == 10 or self.roll >= 2:
            self.frame += 1
            self.roll = 1
            self.prev_knocked = 0
            self.reset_pins()
        else:
            self.roll = 2
            self.ball.reset()
        self.state = GameState.AIM
        self.power = 0.0
        self.dragging = False

    def reset_pins(self):
        for p in self.pins:
            p.reset()
        self.ball.reset()
        self.prev_knocked = 0

    # ── 绘图 ──────────────────────────────────────
    def draw_lane(self, surface):
        r = pygame.Rect(LANE_LEFT, LANE_TOP, LANE_WIDTH, LANE_HEIGHT)
        pygame.draw.rect(surface, COLOR_LANE, r)
        pygame.draw.rect(surface, COLOR_LANE_BORDER, r, 3)
        pygame.draw.rect(surface, COLOR_GUTTER, (LANE_LEFT - 20, LANE_TOP, 20, LANE_HEIGHT))
        pygame.draw.rect(surface, COLOR_GUTTER, (LANE_RIGHT, LANE_TOP, 20, LANE_HEIGHT))
        # 标记点
        for y in range(LANE_TOP + 80, LANE_BOTTOM, 60):
            for off in [-40, 0, 40]:
                x = PIN_CENTER_X + off
                if LANE_LEFT < x < LANE_RIGHT:
                    pygame.draw.circle(surface, (160, 130, 90), (x, y), 3)
        # 箭头
        for off in [-60, -30, 0, 30, 60]:
            x = PIN_CENTER_X + off
            if LANE_LEFT + 20 < x < LANE_RIGHT - 20:
                pygame.draw.polygon(surface, (160, 130, 90), [
                    (x, LANE_TOP + 60), (x - 6, LANE_TOP + 75), (x + 6, LANE_TOP + 75)
                ])

    def draw_aim(self, surface):
        if self.state not in (GameState.AIM, GameState.POWER):
            return
        start = (self.ball.x, self.ball.y)
        end = (self.aim_x, LANE_TOP + 20)
        for i in range(0, 100, 8):
            t1, t2 = i / 100, (i + 4) / 100
            x1 = start[0] + (end[0] - start[0]) * t1
            y1 = start[1] + (end[1] - start[1]) * t1
            x2 = start[0] + (end[0] - start[0]) * t2
            y2 = start[1] + (end[1] - start[1]) * t2
            if i % 16 == 0:
                pygame.draw.line(surface, (255, 100, 100, 128), (x1, y1), (x2, y2), 2)
        pygame.draw.circle(surface, (255, 100, 100),
                           (int(self.aim_x), int(LANE_TOP + 20)), 5, 2)

    def draw_power_bar(self, surface):
        if self.state not in (GameState.AIM, GameState.POWER):
            return
        bx, by, bw, bh = LANE_RIGHT + 40, LANE_TOP + 50, 24, 300
        pygame.draw.rect(surface, (60, 60, 70), (bx, by, bw, bh))
        fh = int(self.power * bh)
        if fh > 0:
            c = (int(50 + self.power * 200), int(200 - self.power * 150), 80)
            pygame.draw.rect(surface, c, (bx, by + bh - fh, bw, fh))
        pygame.draw.rect(surface, (200, 200, 200), (bx, by, bw, bh), 2)
        lbl = self.font_small.render("力度", True, (200, 200, 200))
        surface.blit(lbl, (bx - 10, by - 30))

    def draw_hud(self, surface):
        # 局数
        t = self.font_mid.render(f"第 {self.frame}/10 局 · 第 {self.roll} 球", True, COLOR_TEXT)
        surface.blit(t, (30, 20))
        # 计分板
        cur = 0
        parts = []
        for i, s in enumerate(self.frame_scores):
            if s is not None:
                cur = s
                parts.append(f"[{s}]")
            else:
                parts.append("[--]")
        score_text = self.font_small.render(f"得分: {cur}", True, COLOR_ACCENT)
        surface.blit(score_text, (30, 630))
        # 提示
        if self.state == GameState.AIM:
            hint = self.font_small.render(
                "👆 按住鼠标左键向下拖拽蓄力，松开发球", True, (180, 200, 255))
            surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 650))
        elif self.state == GameState.GAME_OVER:
            ot = self.font_large.render(f"🏆 游戏结束！总分: {cur}", True, COLOR_ACCENT)
            surface.blit(ot, (SCREEN_WIDTH // 2 - ot.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            rt = self.font_mid.render("按 R 重新开始 · ESC 退出", True, COLOR_TEXT)
            surface.blit(rt, (SCREEN_WIDTH // 2 - rt.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

    def draw_message(self, surface):
        if self.message and self.state == GameState.FRAME_END:
            txt = self.font_large.render(self.message, True, COLOR_ACCENT)
            x, y = SCREEN_WIDTH // 2 - txt.get_width() // 2, SCREEN_HEIGHT // 2 - 60
            bg = pygame.Surface((txt.get_width() + 40, txt.get_height() + 20))
            bg.set_alpha(180)
            bg.fill((0, 0, 0))
            surface.blit(bg, (x - 20, y - 10))
            surface.blit(txt, (x, y))
            sub = self.font_small.render("按任意键继续...", True, COLOR_TEXT)
            surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, y + 60))

    # ── 事件处理 ──────────────────────────────────
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_r:
                    self.reset_game()
                    return True
                if self.state == GameState.FRAME_END:
                    self.settle_timer = 999
                    continue
            if self.state in (GameState.AIM, GameState.POWER):
                if event.type == pygame.MOUSEMOTION:
                    mx, _ = event.pos
                    self.aim_x = clamp(mx, LANE_LEFT + 20, LANE_RIGHT - 20)
                    if self.state == GameState.AIM:
                        self.ball.x = clamp(mx, LANE_LEFT + BALL_RADIUS + 10,
                                            LANE_RIGHT - BALL_RADIUS - 10)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == GameState.AIM:
                        self.state = GameState.POWER
                        self.dragging = True
                        self.drag_start_y = event.pos[1]
                if event.type == pygame.MOUSEMOTION and self.dragging:
                    dy = event.pos[1] - self.drag_start_y
                    self.power = clamp(dy / 250, 0.0, 1.0) if dy > 0 else 0.0
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.state == GameState.POWER and self.dragging:
                        self.dragging = False
                        if self.power > 0.05:
                            self.ball.launch(self.aim_x, self.power)
                            self.state = GameState.ROLLING
                        else:
                            self.state = GameState.AIM
                            self.power = 0.0
        return True

    # ── 主循环 ────────────────────────────────────
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.screen.fill(COLOR_BG)
            self.draw_lane(self.screen)
            self.draw_aim(self.screen)
            self.draw_power_bar(self.screen)
            for p in self.pins:
                p.draw(self.screen)
            self.ball.draw(self.screen)
            self.draw_hud(self.screen)
            self.draw_message(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()


# ── 入口 ──────────────────────────────────────────
if __name__ == "__main__":
    BowlingGame().run()