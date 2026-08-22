"""
Cricket - 板球击球对战
一个2D板球击球游戏，玩家控制击球手，根据时机击球得分。
类型: 体育竞技
作者: AI Game Generator
日期: 2026-08-22
"""

import pygame
import random
import math
import sys

# ==================== 初始化 ====================
pygame.init()
WIDTH, HEIGHT = 900, 620
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cricket - 板球击球对战")
clock = pygame.time.Clock()
font_small = pygame.font.SysFont("simsun", 20)
font_medium = pygame.font.SysFont("simsun", 28)
font_large = pygame.font.SysFont("simsun", 48)
font_xl = pygame.font.SysFont("simsun", 64)

# ==================== 颜色 ====================
SKY_BLUE = (135, 206, 235)
GREEN = (34, 139, 34)
PITCH_TAN = (220, 190, 140)
CREASE_WHITE = (255, 255, 255)
BROWN = (139, 69, 19)
RED = (220, 50, 50)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
DARK_GREEN = (20, 100, 20)
BALL_RED = (200, 40, 40)
SKIN = (255, 200, 150)
BLUE = (50, 100, 200)
GRAY = (180, 180, 180)
ORANGE = (255, 165, 0)

# ==================== 常量 ====================
PITCH_LEFT = 150
PITCH_RIGHT = 750
PITCH_TOP = 360
PITCH_BOTTOM = 460
BATSMAN_X = 620
BOWLER_END_X = 200
MAX_WICKETS = 10
MAX_OVERS = 10
BALLS_PER_OVER = 6

# ==================== 球类 ====================
class Ball:
    def __init__(self, length_type):
        self.x = BOWLER_END_X
        self.y = PITCH_TOP - 30
        self.vx = 0
        self.vy = 0
        self.radius = 8
        self.active = True
        self.hit = False
        self.bounce_x = 0
        self.bounce_y = 0
        self.has_bounced = False
        self.trajectory = []
        self.speed = 0
        self.length_type = length_type  # "short", "good", "full", "yorker"
        self.set_trajectory()

    def set_trajectory(self):
        """根据投球类型设置弹道"""
        types = {
            "short":  {"speed": 12, "bounce": 0.65, "height": 0.5},
            "good":   {"speed": 14, "bounce": 0.55, "height": 0.3},
            "full":   {"speed": 13, "bounce": 0.40, "height": 0.15},
            "yorker": {"speed": 16, "bounce": 0.30, "height": 0.05},
        }
        t = types.get(self.length_type, types["good"])
        self.speed = t["speed"]
        self.bounce_x = PITCH_LEFT + (PITCH_RIGHT - PITCH_LEFT) * t["bounce"]
        self.bounce_y = PITCH_TOP + random.randint(-10, 10)
        self.vx = self.speed * 0.7
        self.vy = -self.speed * 0.5

    def update(self):
        if not self.active:
            return
        # 重力
        self.vy += 0.3
        self.x += self.vx
        self.y += self.vy
        self.trajectory.append((int(self.x), int(self.y)))

        # 弹跳
        if not self.has_bounced and self.y >= self.bounce_y and self.x >= self.bounce_x - 20:
            self.has_bounced = True
            self.vy = -abs(self.vy) * 0.4
            self.vx *= 0.85

        # 边界检查
        if self.y > PITCH_BOTTOM + 50 or self.x > WIDTH + 20 or self.x < -20:
            self.active = False

    def draw(self, surface):
        if not self.active:
            return
        # 轨迹拖尾
        for i, (tx, ty) in enumerate(self.trajectory[-8:]):
            alpha = int(255 * (i + 1) / 8)
            pygame.draw.circle(surface, (200, 50, 50, alpha), (tx, ty), max(2, self.radius - 3))
        # 球
        pygame.draw.circle(surface, BALL_RED, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (180, 30, 30), (int(self.x), int(self.y)), self.radius, 2)
        # 缝线
        pygame.draw.line(surface, WHITE, (int(self.x) - 3, int(self.y)), (int(self.x) + 3, int(self.y)), 1)

# ==================== 击球手 ====================
class Batsman:
    def __init__(self):
        self.x = BATSMAN_X
        self.y = PITCH_TOP + 30
        self.swing_angle = 0
        self.is_swinging = False
        self.swing_timer = 0
        self.body_color = SKIN
        self.shirt_color = (255, 255, 255)

    def swing(self):
        if not self.is_swinging:
            self.is_swinging = True
            self.swing_angle = -60
            self.swing_timer = 15

    def update(self):
        if self.is_swinging:
            self.swing_timer -= 1
            self.swing_angle += 10
            if self.swing_timer <= 0:
                self.is_swinging = False
                self.swing_angle = 0

    def draw(self, surface):
        bx, by = self.x, self.y
        # 身体
        pygame.draw.circle(surface, self.body_color, (bx, by - 30), 15)  # 头
        pygame.draw.rect(surface, self.shirt_color, (bx - 12, by - 15, 24, 35))  # 身体
        # 腿
        pygame.draw.line(surface, SKIN, (bx - 5, by + 20), (bx - 10, by + 45), 4)
        pygame.draw.line(surface, SKIN, (bx + 5, by + 20), (bx + 10, by + 45), 4)
        # 护具
        pygame.draw.rect(surface, (200, 200, 200), (bx - 14, by + 5, 28, 15))  # 护垫
        # 球棒
        bat_length = 45
        bat_x = bx + 15
        bat_y = by - 5
        if self.is_swinging:
            angle_rad = math.radians(self.swing_angle)
            ex = bat_x + math.cos(angle_rad) * bat_length
            ey = bat_y + math.sin(angle_rad) * bat_length
            pygame.draw.line(surface, (180, 120, 50), (bat_x, bat_y), (ex, ey), 5)
        else:
            # 静态球棒 - 扛在肩上
            pygame.draw.line(surface, (180, 120, 50), (bat_x, bat_y), (bat_x + 20, bat_y - 30), 5)

# ==================== 投球手 ====================
class Bowler:
    def __init__(self):
        self.x = BOWLER_END_X + 30
        self.y = PITCH_TOP - 80
        self.runup_progress = 0
        self.is_bowling = False
        self.ball_released = False
        self.arm_angle = 0
        self.length_type = "good"
        self.delivery_timer = 0

    def start_bowling(self):
        self.is_bowling = True
        self.runup_progress = 0
        self.ball_released = False
        self.arm_angle = -90
        self.length_type = random.choice(["short", "good", "good", "full", "yorker"])
        self.delivery_timer = 0

    def update(self):
        if not self.is_bowling:
            return
        self.delivery_timer += 1
        if self.delivery_timer < 30:
            # 助跑
            self.runup_progress = min(1.0, self.delivery_timer / 30)
            self.x = BOWLER_END_X + 30 - self.runup_progress * 40
        elif self.delivery_timer < 45:
            # 投球动作
            self.arm_angle += 12
        elif self.delivery_timer == 45:
            # 释放球
            self.ball_released = True
        elif self.delivery_timer > 60:
            self.is_bowling = False

    def draw(self, surface):
        if not self.is_bowling:
            return
        bx, by = int(self.x), int(self.y)
        # 身体
        pygame.draw.circle(surface, SKIN, (bx, by - 25), 14)  # 头
        pygame.draw.rect(surface, BLUE, (bx - 10, by - 10, 20, 30))  # 身体
        # 腿
        leg_offset = int(self.runup_progress * 15)
        pygame.draw.line(surface, SKIN, (bx - 4, by + 20), (bx - 8 - leg_offset, by + 40), 4)
        pygame.draw.line(surface, SKIN, (bx + 4, by + 20), (bx + 8 + leg_offset, by + 40), 4)
        # 手臂（投球动作）
        arm_len = 30
        angle_rad = math.radians(self.arm_angle)
        ax = bx + math.cos(angle_rad) * arm_len
        ay = by - 5 + math.sin(angle_rad) * arm_len
        pygame.draw.line(surface, SKIN, (bx, by - 5), (ax, ay), 4)
        # 手中的球
        if not self.ball_released and self.delivery_timer >= 35:
            pygame.draw.circle(surface, BALL_RED, (int(ax), int(ay)), 6)

# ==================== 场地 ====================
class Field:
    def __init__(self):
        self.boundary_radius = 280
        self.center_x = 450
        self.center_y = 410
        self.fielders = []
        for _ in range(6):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(100, self.boundary_radius - 30)
            self.fielders.append({
                "x": self.center_x + math.cos(angle) * dist,
                "y": self.center_y + math.sin(angle) * dist,
                "target_x": self.center_x + math.cos(angle) * dist,
                "target_y": self.center_y + math.sin(angle) * dist,
                "speed": random.uniform(1, 2),
            })

    def draw(self, surface):
        # 外场圆形边界
        pygame.draw.circle(surface, DARK_GREEN, (self.center_x, self.center_y), self.boundary_radius, 3)
        pygame.draw.circle(surface, WHITE, (self.center_x, self.center_y), self.boundary_radius, 1)
        # 内场
        pygame.draw.circle(surface, (50, 160, 50), (self.center_x, self.center_y), 140, 2)
        # 击球手
        for f in self.fielders:
            pygame.draw.circle(surface, BLUE, (int(f["x"]), int(f["y"])), 10)
            pygame.draw.circle(surface, WHITE, (int(f["x"]), int(f["y"])), 10, 1)

    def update(self, ball_x, ball_y):
        """让外野手追球"""
        if ball_x == 0 and ball_y == 0:
            # 回到原位
            for f in self.fielders:
                dx = f["target_x"] - f["x"]
                dy = f["target_y"] - f["y"]
                dist = math.hypot(dx, dy)
                if dist > 2:
                    f["x"] += dx / dist * f["speed"]
                    f["y"] += dy / dist * f["speed"]
            return

        # 追球
        for f in self.fielders:
            dx = ball_x - f["x"]
            dy = ball_y - f["y"]
            dist = math.hypot(dx, dy)
            if dist > 5:
                f["x"] += dx / dist * f["speed"] * 2
                f["y"] += dy / dist * f["speed"] * 2

# ==================== 游戏主类 ====================
class CricketGame:
    def __init__(self):
        self.reset()
        self.field = Field()

    def reset(self):
        self.runs = 0
        self.wickets = 0
        self.balls_bowled = 0
        self.ball_history = []
        self.state = "ready"  # ready, bowling, batting, result, game_over
        self.ball = None
        self.batsman = Batsman()
        self.bowler = Bowler()
        self.result_text = ""
        self.result_timer = 0
        self.result_color = WHITE
        self.combo = 0
        self.current_runs = 0
        self.ball_trajectory = []
        self.hit_angle = 0
        self.hit_speed = 0
        self.ball_flight = []
        self.show_hint = True
        self.hint_timer = 180

    def start_delivery(self):
        if self.state == "ready" or self.state == "result":
            self.state = "bowling"
            self.bowler.start_bowling()

    def update(self):
        self.batsman.update()

        if self.state == "bowling":
            self.bowler.update()
            if self.bowler.ball_released and self.ball is None:
                self.ball = Ball(self.bowler.length_type)
                self.state = "batting"
                self.show_hint = False

        elif self.state == "batting":
            if self.ball and self.ball.active:
                self.ball.update()
                # 球过了击球手
                if self.ball.x > BATSMAN_X + 40:
                    self.handle_miss()
            else:
                self.handle_miss()

        elif self.state == "result":
            self.field.update(
                self.ball_flight[-1][0] if self.ball_flight else (0, 0),
                self.ball_flight[-1][1] if self.ball_flight else (0, 0)
            )
            self.result_timer -= 1
            if self.ball_flight:
                fx, fy = self.ball_flight[-1]
                # 简化：球飞行一段时间后结束
                if len(self.ball_flight) > 30 + self.current_runs * 10:
                    self.end_ball()
            if self.result_timer <= 0:
                self.end_ball()

        # 提示计时
        if self.show_hint:
            self.hint_timer -= 1
            if self.hint_timer <= 0:
                self.show_hint = False

    def handle_swing(self):
        if self.state != "batting" or not self.ball or not self.ball.active:
            return
        if self.batsman.is_swinging:
            return

        self.batsman.swing()

        # 计算击球质量
        hit_x = BATSMAN_X
        ball_x = self.ball.x
        ball_y = self.ball.y
        pitch_center_y = (PITCH_TOP + PITCH_BOTTOM) // 2

        # 距离理想击球点的偏移
        dist_x = abs(ball_x - hit_x)
        dist_y = abs(ball_y - pitch_center_y)
        timing_quality = max(0, 1.0 - (dist_x / 100 + dist_y / 80) / 2)

        # 随机因素
        luck = random.uniform(-0.2, 0.2)
        quality = max(0, min(1.0, timing_quality + luck))

        self.ball.hit = True
        self.ball.active = False

        # 根据质量计算结果
        if quality < 0.2:
            self.handle_out("Bowled!")
        elif quality < 0.35:
            self.handle_out("Caught!")
        elif quality < 0.5:
            self.handle_runs(0)
        else:
            runs = self.calculate_runs(quality)
            self.handle_runs(runs)

    def calculate_runs(self, quality):
        if quality > 0.95:
            return random.choice([6, 4, 6, 4])
        elif quality > 0.85:
            return random.choice([4, 3, 4, 2])
        elif quality > 0.75:
            return random.choice([3, 2, 4, 1])
        elif quality > 0.65:
            return random.choice([2, 1, 3, 1])
        elif quality > 0.5:
            return random.choice([1, 2, 0, 1])
        else:
            return 0

    def handle_runs(self, runs):
        self.runs += runs
        self.current_runs = runs
        self.balls_bowled += 1
        self.ball_history.append(runs)

        if runs == 0:
            self.result_text = "Dot Ball! No run"
            self.result_color = GRAY
        elif runs == 1:
            self.result_text = "1 run"
            self.result_color = WHITE
        elif runs == 2:
            self.result_text = "2 runs!"
            self.result_color = WHITE
        elif runs == 3:
            self.result_text = "3 runs!"
            self.result_color = YELLOW
        elif runs == 4:
            self.result_text = "FOUR! BOUNDARY!"
            self.result_color = YELLOW
        elif runs == 6:
            self.result_text = "SIX! MAXIMUM!"
            self.result_color = ORANGE

        # 计算球飞行轨迹
        self.ball_flight = []
        angle = random.uniform(-60, 60) - 90 if random.random() < 0.5 else random.uniform(-60, 60) + 90
        self.hit_angle = angle
        spd = 8 + runs * 2
        fx, fy = BATSMAN_X, PITCH_TOP + 30
        for i in range(60):
            progress = i / 60
            fx += math.cos(math.radians(angle)) * spd * 0.7
            fy += math.sin(math.radians(angle)) * spd * 0.7 - progress * 2
            self.ball_flight.append((fx, fy))

        self.state = "result"
        self.result_timer = 90

    def handle_miss(self):
        self.balls_bowled += 1
        self.ball_history.append(0)
        if self.ball and self.ball.has_bounced:
            # 有概率被击中身体或出局
            if random.random() < 0.3:
                self.handle_out("Bowled!")
                return
        self.result_text = "Dot Ball! No run"
        self.result_color = GRAY
        self.state = "result"
        self.result_timer = 60
        self.ball_flight = []
        self.current_runs = 0

    def handle_out(self, reason):
        self.wickets += 1
        self.balls_bowled += 1
        self.ball_history.append("W")
        self.result_text = f"OUT! {reason}"
        self.result_color = RED
        self.state = "result"
        self.result_timer = 120
        self.ball_flight = []
        self.current_runs = 0

        if self.wickets >= MAX_WICKETS:
            self.state = "game_over"

    def end_ball(self):
        self.field.update(0, 0)
        self.ball = None
        self.ball_flight = []
        self.ball_trajectory = []
        if self.state != "game_over":
            if self.balls_bowled >= MAX_OVERS * BALLS_PER_OVER or self.wickets >= MAX_WICKETS:
                self.state = "game_over"
            else:
                self.state = "ready"

    def draw(self, surface):
        # 天空
        surface.fill(SKY_BLUE)
        # 草地
        pygame.draw.rect(surface, GREEN, (0, PITCH_TOP + 50, WIDTH, HEIGHT - PITCH_TOP - 50))
        # 外场圆
        self.field.draw(surface)
        # 球场
        pygame.draw.rect(surface, PITCH_TAN, (PITCH_LEFT, PITCH_TOP, PITCH_RIGHT - PITCH_LEFT, PITCH_BOTTOM - PITCH_TOP))
        # 三柱门（击球手端）
        for i in range(3):
            sx = BATSMAN_X + 10 + i * 8
            pygame.draw.line(surface, BROWN, (sx, PITCH_TOP + 10), (sx, PITCH_TOP + 30), 3)
        # 三柱门（投球手端）
        for i in range(3):
            sx = BOWLER_END_X + 10 + i * 8
            pygame.draw.line(surface, BROWN, (sx, PITCH_TOP + 10), (sx, PITCH_TOP + 30), 3)
        # 击球线
        pygame.draw.line(surface, CREASE_WHITE, (BATSMAN_X, PITCH_TOP), (BATSMAN_X, PITCH_BOTTOM), 2)
        # 投球线
        pygame.draw.line(surface, CREASE_WHITE, (BOWLER_END_X + 20, PITCH_TOP), (BOWLER_END_X + 20, PITCH_BOTTOM), 2)

        # 角色
        self.batsman.draw(surface)
        self.bowler.draw(surface)

        # 球
        if self.ball and self.ball.active:
            self.ball.draw(surface)

        # 球飞行轨迹
        if self.ball_flight:
            for i, (fx, fy) in enumerate(self.ball_flight):
                if i % 3 == 0 and 0 <= fx <= WIDTH and 0 <= fy <= HEIGHT:
                    alpha = max(0, 255 - i * 4)
                    pygame.draw.circle(surface, (255, 100, 50, alpha), (int(fx), int(fy)), 4)

        # 计分板
        self.draw_scoreboard(surface)

        # 结果文字
        if self.result_text and self.result_timer > 0:
            text = font_large.render(self.result_text, True, self.result_color)
            text_rect = text.get_rect(center=(WIDTH // 2, 150))
            # 背景
            bg = pygame.Surface((text_rect.width + 20, text_rect.height + 10))
            bg.set_alpha(180)
            bg.fill(BLACK)
            surface.blit(bg, (text_rect.x - 10, text_rect.y - 5))
            surface.blit(text, text_rect)

        # 提示
        if self.show_hint:
            hint = font_medium.render("点击 SPACE 或点击鼠标击球！", True, YELLOW)
            hint_rect = hint.get_rect(center=(WIDTH // 2, 100))
            bg = pygame.Surface((hint_rect.width + 20, hint_rect.height + 10))
            bg.set_alpha(200)
            bg.fill(BLACK)
            surface.blit(bg, (hint_rect.x - 10, hint_rect.y - 5))
            surface.blit(hint, hint_rect)

    def draw_scoreboard(self, surface):
        # 计分板背景
        sb = pygame.Surface((200, 120))
        sb.set_alpha(200)
        sb.fill(BLACK)
        surface.blit(sb, (10, 10))

        # 得分
        score_text = font_medium.render(f"Score: {self.runs}/{self.wickets}", True, WHITE)
        surface.blit(score_text, (20, 15))

        # 总局数
        total_balls = self.balls_bowled
        overs = total_balls // BALLS_PER_OVER
        balls = total_balls % BALLS_PER_OVER
        overs_text = font_small.render(f"Overs: {overs}.{balls} / {MAX_OVERS}.0", True, WHITE)
        surface.blit(overs_text, (20, 50))

        # 击球率
        if total_balls > 0:
            sr = (self.runs / total_balls) * 100
        else:
            sr = 0
        sr_text = font_small.render(f"Strike Rate: {sr:.1f}", True, WHITE)
        surface.blit(sr_text, (20, 75))

        # 最近球记录
        hist_text = "Recent: "
        for b in self.ball_history[-8:]:
            if b == "W":
                hist_text += "W "
            elif b == 0:
                hist_text += ". "
            elif b == 4:
                hist_text += "4 "
            elif b == 6:
                hist_text += "6 "
            else:
                hist_text += str(b) + " "
        if not self.ball_history:
            hist_text += "-"
        h = font_small.render(hist_text, True, WHITE)
        surface.blit(h, (20, 100))

        # 游戏结束
        if self.state == "game_over":
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            surface.blit(overlay, (0, 0))

            if self.wickets >= MAX_WICKETS:
                title = font_xl.render("All Out!", True, RED)
            else:
                title = font_xl.render("Game Over!", True, YELLOW)

            title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
            surface.blit(title, title_rect)

            final = font_large.render(f"Final Score: {self.runs}/{self.wickets}", True, WHITE)
            final_rect = final.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10))
            surface.blit(final, final_rect)

            restart = font_medium.render("Press ENTER to play again", True, WHITE)
            restart_rect = restart.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70))
            surface.blit(restart, restart_rect)

            quit_text = font_small.render("Press ESC to quit", True, WHITE)
            quit_rect = quit_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 110))
            surface.blit(quit_text, quit_rect)

# ==================== 主循环 ====================
def main():
    game = CricketGame()
    running = True
    delivery_ready = True
    delivery_timer = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    if game.state == "game_over":
                        pass
                    elif game.state == "ready":
                        game.start_delivery()
                    else:
                        game.handle_swing()
                elif event.key == pygame.K_RETURN:
                    if game.state == "game_over":
                        game = CricketGame()
                elif event.key == pygame.K_s:
                    if game.state == "ready":
                        game.start_delivery()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if game.state == "game_over":
                        pass
                    elif game.state == "ready":
                        game.start_delivery()
                    else:
                        game.handle_swing()

        # 自动投球
        if game.state == "ready" and delivery_ready:
            delivery_timer += 1
            if delivery_timer > 60:
                game.start_delivery()
                delivery_timer = 0
                delivery_ready = False
        if game.state != "ready":
            delivery_ready = True
            delivery_timer = 0

        game.update()

        game.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()