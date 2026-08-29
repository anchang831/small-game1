#!/usr/bin/env python3
"""
棒球 (Baseball) - 2D棒球打击训练
玩法: 投手投出不同球种, 玩家在适当时机按空格挥棒
打击质量: 全垒打 (完美) > 安打 (良好) > 界外球 (偏差) > 挥棒落空 (差)
3好球 = 1出局, 3出局 = 游戏结束
"""

import pygame
import random
import math

# ── 常量 ──────────────────────────────────────────────
WIDTH, HEIGHT = 900, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 40, 40)
GREEN = (40, 200, 60)
BLUE = (50, 130, 255)
YELLOW = (255, 220, 0)
ORANGE = (255, 160, 20)
BROWN = (160, 100, 40)
SKY = (80, 160, 240)
GRASS = (40, 160, 50)
DIRT = (200, 170, 130)
SAND = (230, 210, 170)
BAT_COLOR = (180, 120, 60)
SKIN = (240, 200, 160)
UNIFORM_HOME = (200, 200, 200)
UNIFORM_AWAY = (180, 60, 60)

# ── 游戏主类 ──────────────────────────────────────────
class BaseballGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("⚾ 棒球打击训练 - 按空格挥棒")
        self.clock = pygame.time.Clock()
        font_name = pygame.font.match_font("simsun", "notosanscjk", "arial")
        self.font_lg = pygame.font.Font(font_name, 52)
        self.font_md = pygame.font.Font(font_name, 34)
        self.font_sm = pygame.font.Font(font_name, 22)
        self.font_xs = pygame.font.Font(font_name, 18)
        self.reset()

    def reset(self):
        """重置游戏状态"""
        self.score = 0
        self.strikes = 0
        self.outs = 0
        self.hits = 0
        self.at_bat = 0

        # 投手/球/击球状态
        self.state = "ready"            # ready | windup | pitch | swing | result | game_over
        self.state_timer = 0
        self.result_text = ""
        self.result_color = WHITE

        # 球
        self.ball_pos = [120, 340]
        self.ball_v = [0, 0]
        self.ball_visible = False
        self.ball_trail = []
        self.pitch_type = "fastball"
        self.pitch_speed = 0

        # 击球
        self.swing_angle = -30
        self.is_swinging = False
        self.swing_timer = 0
        self.hit_active = False
        self.hit_pos = [0, 0]
        self.hit_v = [0, 0]
        self.hit_trail = []
        self.hit_spark = []

        # 投手动画
        self.pitcher_frame = 0

        # 节奏
        self.game_time = 0

    # ── 事件处理 ──────────────────────────────────────
    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    if self.state == "pitch" and self.ball_visible:
                        self.do_swing()
                    elif self.state == "game_over":
                        self.reset()
                if e.key == pygame.K_r and self.state == "game_over":
                    self.reset()
        return True

    # ── 挥棒 ──────────────────────────────────────────
    def do_swing(self):
        self.state = "swing"
        self.is_swinging = True
        self.swing_timer = 0
        self.swing_angle = 0

        # 判断击球时机: 球与好球带的距离
        zone_cx, zone_cy = 680, 320
        dx = self.ball_pos[0] - zone_cx
        dy = self.ball_pos[1] - zone_cy
        dist = math.hypot(dx, dy)

        # 球是否在好球带范围内
        in_zone = (650 < self.ball_pos[0] < 710 and
                   290 < self.ball_pos[1] < 350)

        if dist < 20 and in_zone:
            # 完美 — 全垒打
            self.result_text = "全垒打!!! HOME RUN! +5分"
            self.result_color = YELLOW
            self.score += 5
            self.hits += 1
            self.launch_hit(12, -10)
        elif dist < 50 and in_zone:
            # 良好 — 安打
            self.result_text = "安打! HIT! +2分"
            self.result_color = GREEN
            self.score += 2
            self.hits += 1
            self.launch_hit(8, -6)
        elif dist < 100 and in_zone:
            # 偏差 — 界外球
            self.result_text = "界外球! FOUL! (好球数不变)"
            self.result_color = BLUE
            self.launch_hit(4, -4)
        elif in_zone or self.ball_pos[0] > 650:
            # 好球区内挥空 / 好球
            self.result_text = "挥棒落空! STRIKE!"
            self.result_color = RED
            self.strikes += 1
            self.is_swinging = False
            self.check_out()
        else:
            # 坏球也挥了
            self.result_text = "挥空了! 坏球"
            self.result_color = ORANGE
            self.is_swinging = False

        self.state_timer = 90   # 显示结果 1.5 秒

    def launch_hit(self, vx, vy):
        """击出球后的轨迹"""
        self.hit_active = True
        self.hit_pos = self.ball_pos[:]
        self.hit_v = [vx + random.uniform(-1, 1), vy + random.uniform(-1, 1)]
        self.hit_trail = []
        self.hit_spark = []
        self.ball_visible = False
        self.is_swinging = False

    def check_out(self):
        if self.strikes >= 3:
            self.outs += 1
            self.strikes = 0
            self.at_bat += 1
            if self.outs >= 3:
                self.state = "game_over"
                self.result_text = f"比赛结束! 得分: {self.score}"
                self.result_color = YELLOW
            else:
                self.result_text = f"三振出局! 第{self.outs}出局"
                self.result_color = RED

    # ── 更新逻辑 ──────────────────────────────────────
    def update(self):
        self.game_time += 1

        if self.state == "ready":
            self.state_timer += 1
            self.pitcher_frame = (self.pitcher_frame + 1) % 120
            if self.state_timer > 60:
                self.start_pitch()

        elif self.state == "pitch":
            self.update_pitch()

        elif self.state == "swing":
            self.update_swing()
            if self.state_timer > 0:
                self.state_timer -= 1
                if self.state_timer <= 0:
                    self.state = "result" if not self.hit_active else "result"
                    self.state_timer = 90

        elif self.state == "result":
            self.state_timer -= 1
            # 棒球飞行的物理
            if self.hit_active:
                self.hit_pos[0] += self.hit_v[0]
                self.hit_pos[1] += self.hit_v[1]
                self.hit_v[1] += 0.25   # 重力
                self.hit_trail.append(self.hit_pos[:])
                if len(self.hit_trail) > 35:
                    self.hit_trail.pop(0)
                # 火花效果
                for _ in range(2):
                    self.hit_spark.append([
                        self.hit_pos[0] + random.uniform(-6, 6),
                        self.hit_pos[1] + random.uniform(-6, 6),
                        random.uniform(2, 5),
                        random.randint(5, 15)
                    ])
                self.hit_spark = [s for s in self.hit_spark if s[3] > 0]
                for s in self.hit_spark:
                    s[3] -= 1
                # 飞出屏幕
                if (self.hit_pos[0] > WIDTH + 50 or self.hit_pos[1] < -50 or
                        self.hit_pos[1] > HEIGHT + 50):
                    self.hit_active = False
            if self.state_timer <= 0:
                self.reset_pitch()

        elif self.state == "game_over":
            pass

    def start_pitch(self):
        self.state = "pitch"
        self.state_timer = 0
        self.pitcher_frame = 0

        # 随机球种
        self.pitch_type = random.choices(
            ["fastball", "curveball", "changeup", "knuckleball"],
            weights=[40, 25, 20, 15]
        )[0]
        speeds = {"fastball": 8, "curveball": 6, "changeup": 4.5, "knuckleball": 5}
        self.pitch_speed = speeds[self.pitch_type]

        # 球从投手位置出发
        self.ball_pos = [130, 345]
        self.ball_v = [0, 0]
        self.ball_visible = True
        self.ball_trail = []

    def update_pitch(self):
        self.pitcher_frame += 1
        speed = self.pitch_speed

        # 不同球种的运动轨迹
        if self.pitch_type == "fastball":
            self.ball_pos[0] += speed * 1.1
            self.ball_pos[1] += random.uniform(-0.2, 0.2)
            drift = 0
        elif self.pitch_type == "curveball":
            self.ball_pos[0] += speed
            # 向右下坠
            t = (self.ball_pos[0] - 130) / 600
            self.ball_pos[1] += 0.5 + math.sin(t * math.pi) * 1.5
            drift = 0.3
        elif self.pitch_type == "changeup":
            self.ball_pos[0] += speed * 0.8
            self.ball_pos[1] += random.uniform(-0.5, 0.5)
            drift = 0
        else:  # knuckleball — 蝴蝶球飘忽不定
            self.ball_pos[0] += speed * 0.9
            self.ball_pos[1] += math.sin(self.game_time * 0.15) * 2
            drift = 0

        # 轨迹记录
        self.ball_trail.append(self.ball_pos[:])
        if len(self.ball_trail) > 20:
            self.ball_trail.pop(0)

        # 判断球是否通过本垒板
        if self.ball_pos[0] > 750:
            # 没有挥棒 — 判断好坏球
            in_zone = (650 < self.ball_pos[0] < 710 and
                       290 < self.ball_pos[1] < 350)
            if in_zone:
                self.result_text = "好球! STRIKE!"
                self.result_color = RED
                self.strikes += 1
                self.check_out()
            else:
                self.result_text = "坏球! BALL!"
                self.result_color = BLUE
            self.state = "result"
            self.state_timer = 60
            self.ball_visible = False
            self.is_swinging = False

    def update_swing(self):
        if self.is_swinging:
            self.swing_timer += 1
            self.swing_angle = min(self.swing_timer * 12, 180)
            if self.swing_angle >= 180:
                self.is_swinging = False

    def reset_pitch(self):
        """重置到投球准备状态"""
        self.state = "ready"
        self.state_timer = 0
        self.ball_visible = False
        self.ball_trail = []
        self.hit_active = False
        self.hit_trail = []
        self.hit_spark = []
        self.result_text = ""

    # ── 绘制 ──────────────────────────────────────────
    def draw(self):
        self.screen.fill(SKY)

        # ── 球场背景 ──
        # 草地
        pygame.draw.rect(self.screen, GRASS, (0, 380, WIDTH, HEIGHT - 380))
        # 内野泥土
        pygame.draw.polygon(self.screen, DIRT, [
            (WIDTH // 2 - 200, 380),
            (WIDTH // 2, 280),
            (WIDTH // 2 + 200, 380),
            (WIDTH // 2, 480),
        ])
        # 本垒板区域
        pygame.draw.polygon(self.screen, SAND, [
            (640, 370), (720, 370), (700, 420), (660, 420)
        ])
        # 垒包
        for bx, by in [(WIDTH // 2, 480), (WIDTH // 2 + 150, 400),
                        (WIDTH // 2, 320), (WIDTH // 2 - 150, 400)]:
            pygame.draw.rect(self.screen, WHITE, (bx - 8, by - 8, 16, 16))
            pygame.draw.rect(self.screen, BLACK, (bx - 8, by - 8, 16, 16), 1)

        # ── 好球带 ──
        pygame.draw.rect(self.screen, WHITE, (650, 290, 60, 60), 2, 4)
        # 本垒板
        pygame.draw.polygon(self.screen, WHITE, [
            (678, 355), (682, 355), (685, 362), (680, 368), (675, 362)
        ])

        # ── 投手 ──
        self.draw_pitcher()

        # ── 打击者 ──
        self.draw_batter()

        # ── 球 ──
        if self.ball_visible:
            self.draw_ball()

        # ── 击出球轨迹 ──
        if self.hit_active:
            self.draw_hit_ball()

        # ── 球种提示 ──
        if self.state == "pitch" and self.ball_visible:
            names = {"fastball": "快速球", "curveball": "曲球",
                     "changeup": "变速球", "knuckleball": "蝴蝶球"}
            colors = {"fastball": RED, "curveball": GREEN,
                      "changeup": BLUE, "knuckleball": YELLOW}
            label = self.font_sm.render(
                f"球种: {names[self.pitch_type]}", True, colors[self.pitch_type])
            self.screen.blit(label, (WIDTH // 2 - 50, 10))

        # ── 计分板 ──
        self.draw_ui()

        # ── 结果文字 ──
        if self.result_text and self.state != "game_over":
            shadow = self.font_lg.render(self.result_text, True, BLACK)
            text = self.font_lg.render(self.result_text, True, self.result_color)
            sr = shadow.get_rect(center=(WIDTH // 2 + 2, 182))
            tr = text.get_rect(center=(WIDTH // 2, 180))
            self.screen.blit(shadow, sr)
            self.screen.blit(text, tr)

        # ── 游戏结束 ──
        if self.state == "game_over":
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            self.screen.blit(s, (0, 0))

            texts = [
                (self.font_lg, "比赛结束!", RED, (WIDTH // 2, HEIGHT // 2 - 70)),
                (self.font_md, f"最终得分: {self.score}", WHITE, (WIDTH // 2, HEIGHT // 2)),
                (self.font_md, f"安打: {self.hits}  出局: {self.outs}", WHITE, (WIDTH // 2, HEIGHT // 2 + 45)),
                (self.font_sm, "按 R 重新开始 / 按空格继续", (200, 200, 200), (WIDTH // 2, HEIGHT // 2 + 100)),
            ]
            for font, txt, color, pos in texts:
                surf = font.render(txt, True, color)
                rect = surf.get_rect(center=pos)
                self.screen.blit(surf, rect)

        # ── 操作提示 ──
        if self.state == "pitch" and self.ball_visible:
            hint = self.font_sm.render("按 空格键 挥棒!", True, YELLOW)
            hr = hint.get_rect(center=(WIDTH // 2, 560))
            self.screen.blit(hint, hr)
        elif self.state == "ready":
            hint = self.font_sm.render("投手准备中...", True, WHITE)
            hr = hint.get_rect(center=(WIDTH // 2, 560))
            self.screen.blit(hint, hr)

        pygame.display.flip()

    # ── 子绘制函数 ────────────────────────────────────
    def draw_pitcher(self):
        px, py = 130, 360
        # 身体
        pygame.draw.circle(self.screen, SKIN, (px, py - 40), 18)  # 头
        pygame.draw.rect(self.screen, UNIFORM_AWAY, (px - 16, py - 20, 32, 45))  # 身体
        # 手臂
        if self.state == "pitch" and self.ball_visible:
            arm_angle = 30 + math.sin(self.pitcher_frame * 0.08) * 25
        else:
            arm_angle = -30 + math.sin(self.pitcher_frame * 0.03) * 20
        arm_len = 38
        ax = px + math.cos(math.radians(arm_angle)) * arm_len
        ay = py - 15 + math.sin(math.radians(arm_angle)) * arm_len
        pygame.draw.line(self.screen, SKIN, (px, py - 15), (ax, ay), 6)
        # 腿
        leg_swing = math.sin(self.pitcher_frame * 0.05) * 8 if self.state == "pitch" else 0
        pygame.draw.line(self.screen, WHITE, (px - 8, py + 25),
                         (px - 15 + leg_swing, py + 55), 7)
        pygame.draw.line(self.screen, WHITE, (px + 8, py + 25),
                         (px + 15 - leg_swing, py + 55), 7)
        # 投手板
        pygame.draw.rect(self.screen, (80, 60, 40), (px - 15, py + 55, 30, 8))

    def draw_batter(self):
        bx, by = 620, 360
        # 身体
        pygame.draw.circle(self.screen, SKIN, (bx, by - 40), 18)  # 头
        pygame.draw.rect(self.screen, UNIFORM_HOME, (bx - 16, by - 20, 32, 45))
        # 腿
        pygame.draw.line(self.screen, (60, 60, 60), (bx - 8, by + 25),
                         (bx - 18, by + 58), 7)
        pygame.draw.line(self.screen, (60, 60, 60), (bx + 8, by + 25),
                         (bx + 12, by + 58), 7)
        # 球棒
        bat_len = 70
        if self.is_swinging:
            angle = self.swing_angle
        else:
            angle = -30 + math.sin(self.game_time * 0.03) * 5  # 待机微动
        rad = math.radians(angle)
        ex = bx + math.cos(rad) * bat_len
        ey = by - 10 + math.sin(rad) * bat_len
        # 球棒阴影
        pygame.draw.line(self.screen, (100, 60, 30),
                         (bx + 2, by - 8 + 2), (ex + 2, ey + 2), 10)
        # 球棒本体
        pygame.draw.line(self.screen, BAT_COLOR, (bx, by - 10), (ex, ey), 10)
        # 握把
        pygame.draw.line(self.screen, (40, 40, 40), (bx, by - 10),
                         (bx + math.cos(rad) * 18, by - 10 + math.sin(rad) * 18), 8)
        # 打击头盔
        pygame.draw.arc(self.screen, (60, 60, 60),
                        (bx - 18, by - 58, 36, 30), 0, math.pi, 4)

    def draw_ball(self):
        # 轨迹拖尾
        for i, p in enumerate(self.ball_trail):
            alpha = max(0, 255 - i * 15)
            size = max(2, 6 - i * 0.2)
            pygame.draw.circle(self.screen, (255, 255, 255, alpha),
                               (int(p[0]), int(p[1])), int(size))
        # 球本体
        bx, by = int(self.ball_pos[0]), int(self.ball_pos[1])
        pygame.draw.circle(self.screen, WHITE, (bx, by), 8)
        pygame.draw.circle(self.screen, RED, (bx, by), 8, 1)
        # 缝线
        for i in range(2):
            angle = self.game_time * 0.1 + i * math.pi
            sx = bx + math.cos(angle) * 5
            sy = by + math.sin(angle) * 5
            pygame.draw.circle(self.screen, RED, (int(sx), int(sy)), 2)

    def draw_hit_ball(self):
        # 轨迹拖尾
        for i, p in enumerate(self.hit_trail):
            alpha = max(0, 200 - i * 6)
            size = max(2, 6 - i * 0.12)
            c = (255, min(255, 255 - i * 8), min(255, 100 - i * 3))
            pygame.draw.circle(self.screen, (*c, alpha),
                               (int(p[0]), int(p[1])), int(size))
        # 火花
        for s in self.hit_spark:
            alpha = int(s[3] / 15 * 255)
            pygame.draw.circle(self.screen, (255, 200, 50, alpha),
                               (int(s[0]), int(s[1])), int(s[2]))
        # 球本体
        bx, by = int(self.hit_pos[0]), int(self.hit_pos[1])
        if 0 < bx < WIDTH and 0 < by < HEIGHT:
            pygame.draw.circle(self.screen, WHITE, (bx, by), 7)
            pygame.draw.circle(self.screen, RED, (bx, by), 7, 1)

    def draw_ui(self):
        # 计分板背景
        pygame.draw.rect(self.screen, (0, 0, 0, 160), (10, 10, 180, 130))
        pygame.draw.rect(self.screen, WHITE, (10, 10, 180, 130), 2)

        texts = [
            (self.font_md, f"得分: {self.score}", YELLOW, (20, 15)),
            (self.font_sm, f"好球: {self.strikes}/3", RED, (20, 52)),
            (self.font_sm, f"出局: {self.outs}/3", ORANGE, (20, 78)),
            (self.font_sm, f"安打: {self.hits}", GREEN, (20, 104)),
        ]
        for font, txt, color, pos in texts:
            surf = font.render(txt, True, color)
            self.screen.blit(surf, pos)

        # 好球指示器
        for i in range(3):
            color = RED if i < self.strikes else (60, 60, 60)
            pygame.draw.circle(self.screen, color, (160 + i * 20, 60), 7)

    # ── 主循环 ────────────────────────────────────────
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()


if __name__ == "__main__":
    game = BaseballGame()
    game.run()