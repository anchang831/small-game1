"""
飞镖游戏 (Darts 501)
经典 501 计分玩法：从 501 分开始，每轮投 3 镖，先精确减到 0 分者获胜。
操作：鼠标移动瞄准 → 按住左键蓄力 → 松开投掷
"""

import pygame
import math
import random

# 常量
WIDTH, HEIGHT = 900, 700
FPS = 60
BOARD_CENTER = (450, 340)
BOARD_RADIUS = 200
SCOREBOARD_Y = 20

# 颜色
BLACK = (20, 20, 20)
WHITE = (255, 255, 255)
RED = (220, 40, 40)
GREEN = (40, 180, 40)
CREAM = (245, 230, 200)
BLACK_ACCENT = (30, 30, 30)
GRAY = (180, 180, 180)
GOLD = (255, 215, 0)
DARK_RED = (160, 20, 20)
DARK_GREEN = (20, 120, 20)
BLUE = (60, 120, 255)
LIGHT_BLUE = (180, 210, 255)

# 飞镖盘分区半径比例（从外到内）
RING_DOUBLE = 1.0       # 外双倍区 (r=1.0 到 r=0.85)
RING_OUTER_SINGLE = 0.85  # 外单倍区 (r=0.85 到 r=0.60)
RING_TRIPLE = 0.60      # 三倍区 (r=0.60 到 r=0.45)
RING_INNER_SINGLE = 0.45  # 内单倍区 (r=0.45 到 r=0.15)
RING_25 = 0.15          # 25 分环 (r=0.15 到 r=0.06)
RING_BULLSEYE = 0.06    # 靶心 (r=0.06)

# 20 个扇区的分值（按顺时针顺序，从顶部开始）
SCORE_SLICES = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]


class Dart:
    """飞镖对象"""
    def __init__(self, start_pos, target_pos, power):
        self.start_x, self.start_y = start_pos
        self.target_x, self.target_y = target_pos
        self.power = power  # 0.0 ~ 1.0
        # 计算投掷轨迹
        dx = self.target_x - self.start_x
        dy = self.target_y - self.start_y
        dist = math.hypot(dx, dy)
        if dist == 0:
            dist = 1
        self.vx = (dx / dist) * power * 12
        self.vy = (dy / dist) * power * 12
        self.x = self.start_x
        self.y = self.start_y
        self.trail = []
        self.stuck = False
        self.stuck_pos = None
        self.angle = math.atan2(dy, dx) + math.pi / 2  # 飞镖旋转角度

    def update(self):
        """更新飞镖位置（飞行轨迹）"""
        if self.stuck:
            return
        self.trail.append((self.x, self.y))
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3  # 重力
        # 检查是否到达靶面
        dx = self.x - BOARD_CENTER[0]
        dy = self.y - BOARD_CENTER[1]
        if math.hypot(dx, dy) > BOARD_RADIUS + 30 or len(self.trail) > 80:
            self.stuck = True
            self.stuck_pos = (self.x, self.y)

    def draw(self, screen):
        """绘制飞镖"""
        if not self.stuck_pos and len(self.trail) > 0:
            # 绘制飞行轨迹
            if len(self.trail) > 1:
                pts = self.trail[-8:]
                for i in range(len(pts) - 1):
                    alpha = i / len(pts)
                    pygame.draw.line(screen, (200, 200, 200, int(alpha * 100)),
                                     pts[i], pts[i + 1], 1)
            # 绘制飞镖
            dart_center = (int(self.x), int(self.y))
            # 镖身
            end_x = self.x - math.sin(self.angle) * 15
            end_y = self.y + math.cos(self.angle) * 15
            pygame.draw.line(screen, GOLD, dart_center, (int(end_x), int(end_y)), 3)
            # 镖头
            tip_x = self.x + math.sin(self.angle) * 8
            tip_y = self.y - math.cos(self.angle) * 8
            pygame.draw.line(screen, SILVER, dart_center, (int(tip_x), int(tip_y)), 3)
            # 镖尾
            tail_x = self.x - math.sin(self.angle) * 22
            tail_y = self.y + math.cos(self.angle) * 22
            pygame.draw.line(screen, RED, dart_center, (int(tail_x), int(tail_y)), 2)
        elif self.stuck_pos:
            sx, sy = self.stuck_pos
            # 绘制插在靶上的飞镖
            end_x = sx - math.sin(self.angle) * 15
            end_y = sy + math.cos(self.angle) * 15
            pygame.draw.line(screen, GOLD, (int(sx), int(sy)), (int(end_x), int(end_y)), 3)
            tip_x = sx + math.sin(self.angle) * 8
            tip_y = sy - math.cos(self.angle) * 8
            pygame.draw.line(screen, SILVER, (int(sx), int(sy)), (int(tip_x), int(tip_y)), 3)
            tail_x = sx - math.sin(self.angle) * 22
            tail_y = sy + math.cos(self.angle) * 22
            pygame.draw.line(screen, RED, (int(sx), int(sy)), (int(tail_x), int(tail_y)), 2)


SILVER = (192, 192, 192)


def draw_dartboard(screen, center, radius):
    """绘制飞镖盘"""
    x, y = center

    # 外圈黑色边框
    pygame.draw.circle(screen, BLACK, center, radius + 8)
    pygame.draw.circle(screen, GRAY, center, radius + 3)

    # 绘制 20 个扇区
    slice_angle = 2 * math.pi / 20
    # 起始偏移：12点钟方向（-90度），且偏移半个扇区使20在顶部
    offset = -math.pi / 2 - slice_angle / 2

    for i in range(20):
        start_angle = offset + i * slice_angle
        end_angle = start_angle + slice_angle
        mid_angle = start_angle + slice_angle / 2
        score = SCORE_SLICES[i]

        # 绘制双倍区（外环）
        is_red = (i % 2 == 0)
        color = RED if is_red else CREAM
        draw_sector(screen, center, radius * RING_DOUBLE, radius * RING_OUTER_SINGLE,
                    start_angle, end_angle, color)

        # 外单倍区
        color = BLACK if is_red else WHITE
        draw_sector(screen, center, radius * RING_OUTER_SINGLE, radius * RING_TRIPLE,
                    start_angle, end_angle, color)

        # 三倍区
        color = RED if is_red else CREAM
        draw_sector(screen, center, radius * RING_TRIPLE, radius * RING_INNER_SINGLE,
                    start_angle, end_angle, color)

        # 内单倍区
        color = BLACK if is_red else WHITE
        draw_sector(screen, center, radius * RING_INNER_SINGLE, radius * RING_25,
                    start_angle, end_angle, color)

        # 标记分值（在外单倍区绘制数字）
        label_r = radius * 0.72
        lx = x + math.cos(mid_angle) * label_r
        ly = y + math.sin(mid_angle) * label_r
        font = pygame.font.Font(None, 24)
        text = font.render(str(score), True, GOLD if is_red else BLACK)
        text_rect = text.get_rect(center=(int(lx), int(ly)))
        screen.blit(text, text_rect)

    # 25 分环
    pygame.draw.circle(screen, GREEN, center, int(radius * RING_25 + 2))
    pygame.draw.circle(screen, RED, center, int(radius * RING_25) - 2)

    # 靶心
    pygame.draw.circle(screen, RED, center, int(radius * RING_BULLSEYE + 2))
    pygame.draw.circle(screen, GREEN, center, int(radius * RING_BULLSEYE) - 2)

    # 靶心中间的小红点
    pygame.draw.circle(screen, DARK_RED, center, 4)

    # 金属丝（分割线）
    for i in range(20):
        angle = offset + i * slice_angle
        end_x = x + math.cos(angle) * radius
        end_y = y + math.sin(angle) * radius
        pygame.draw.line(screen, GRAY, center, (int(end_x), int(end_y)), 1)

    # 双倍和三倍区边界
    pygame.draw.circle(screen, GRAY, center, int(radius * RING_OUTER_SINGLE), 1)
    pygame.draw.circle(screen, GRAY, center, int(radius * RING_TRIPLE), 1)
    pygame.draw.circle(screen, GRAY, center, int(radius * RING_INNER_SINGLE), 1)
    pygame.draw.circle(screen, GRAY, center, int(radius * RING_25), 1)


def draw_sector(screen, center, outer_r, inner_r, start_angle, end_angle, color):
    """绘制扇形环"""
    if outer_r <= 0 or inner_r <= 0:
        return
    x, y = center
    points = []
    # 外弧
    steps = max(3, int((end_angle - start_angle) * 30))
    for i in range(steps + 1):
        a = start_angle + (end_angle - start_angle) * i / steps
        px = x + math.cos(a) * outer_r
        py = y + math.sin(a) * outer_r
        points.append((px, py))
    # 内弧（反向）
    for i in range(steps, -1, -1):
        a = start_angle + (end_angle - start_angle) * i / steps
        px = x + math.cos(a) * inner_r
        py = y + math.sin(a) * inner_r
        points.append((px, py))
    if len(points) >= 3:
        pygame.draw.polygon(screen, color, points)


def calculate_score(hit_pos):
    """计算飞镖命中得分"""
    dx = hit_pos[0] - BOARD_CENTER[0]
    dy = hit_pos[1] - BOARD_CENTER[1]
    dist = math.hypot(dx, dy)

    # 超出靶面
    if dist > BOARD_RADIUS:
        return 0

    # 计算扇区
    angle = math.atan2(dy, dx)
    slice_angle = 2 * math.pi / 20
    # 角度偏移（与绘制对齐）
    offset = -math.pi / 2 - slice_angle / 2
    # 将角度映射到扇区
    raw_index = (angle - offset) / slice_angle
    # 处理负值
    index = int(raw_index) % 20
    base_score = SCORE_SLICES[index]

    # 计算倍率
    ratio = dist / BOARD_RADIUS
    if ratio <= RING_BULLSEYE:
        return 50  # 靶心
    elif ratio <= RING_25:
        return 25  # 25 分环
    elif ratio <= RING_INNER_SINGLE:
        return base_score  # 内单倍区
    elif ratio <= RING_TRIPLE:
        return base_score * 3  # 三倍区
    elif ratio <= RING_OUTER_SINGLE:
        return base_score  # 外单倍区
    elif ratio <= RING_DOUBLE:
        return base_score * 2  # 双倍区
    return base_score


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("飞镖游戏 Darts 501")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 28)
        self.running = True
        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        self.scores = [501, 501]  # 玩家1, 玩家2
        self.current_player = 0
        self.dart_count = 0  # 本轮已投飞镖数 (0-2)
        self.dart_limit = 3
        self.darts = []  # 当前飞镖列表
        self.throw_history = [[], []]  # 投掷历史
        self.round_history = [[], []]  # 每轮得分历史
        self.game_over = False
        self.winner = None
        self.aim_pos = (WIDTH // 2, HEIGHT // 2)
        self.aiming = False
        self.power = 0.0
        self.charging = False
        self.show_result = False
        self.result_text = ""
        self.result_timer = 0
        self.throw_ready = True
        self.transition_timer = 0

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    self.reset_game()
                if event.key == pygame.K_ESCAPE:
                    self.running = False

            if not self.game_over and self.throw_ready and not self.show_result:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.charging = True
                    self.power = 0.0
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.charging:
                        self.charging = False
                        self.throw_dart()

        if not self.charging and not self.show_result and not self.game_over:
            self.aim_pos = pygame.mouse.get_pos()

    def throw_dart(self):
        """投掷飞镖"""
        if self.dart_count >= self.dart_limit:
            return

        # 添加一些随机抖动（使游戏有挑战性）
        spread = (1.0 - self.power) * 6 + 2
        tx = self.aim_pos[0] + random.gauss(0, spread)
        ty = self.aim_pos[1] + random.gauss(0, spread)

        # 飞镖从屏幕底部飞出
        start_pos = (WIDTH // 2 + random.randint(-20, 20), HEIGHT + 30)
        dart = Dart(start_pos, (tx, ty), self.power)
        self.darts.append(dart)

        self.dart_count += 1
        self.throw_ready = False

    def update(self):
        """更新游戏状态"""
        # 蓄力
        if self.charging:
            self.power = min(1.0, self.power + 0.02)

        # 更新飞镖
        all_stuck = True
        for dart in self.darts:
            if not dart.stuck:
                all_stuck = False
                break
        if self.throw_ready:
            return

        # 更新飞镖位置
        for dart in self.darts:
            if not dart.stuck:
                dart.update()
                # 检查是否接近靶面
                dx = dart.x - BOARD_CENTER[0]
                dy = dart.y - BOARD_CENTER[1]
                if math.hypot(dx, dy) <= BOARD_RADIUS + 5:
                    dart.stuck = True
                    dart.stuck_pos = (dart.x, dart.y)
                    # 稍微调整位置到靶面上
                    angle = math.atan2(dy, dx)
                    adj_dist = BOARD_RADIUS * 0.95
                    dart.stuck_pos = (
                        BOARD_CENTER[0] + math.cos(angle) * adj_dist,
                        BOARD_CENTER[1] + math.sin(angle) * adj_dist
                    )

        # 检查所有飞镖是否都已停下
        all_stuck = all(d.stuck for d in self.darts)
        if all_stuck and len(self.darts) > 0 and not self.show_result:
            self.calculate_round_score()

    def calculate_round_score(self):
        """计算本轮得分"""
        round_score = 0
        for dart in self.darts:
            if dart.stuck_pos:
                score = calculate_score(dart.stuck_pos)
                round_score += score
                self.throw_history[self.current_player].append(score)

        # 检查是否爆镖（超过剩余分数）
        remaining = self.scores[self.current_player]
        if round_score > remaining:
            # 爆镖，本轮不得分
            self.result_text = f"爆镖！超过剩余分数 ({remaining})，本轮不得分！"
            round_score = 0
            self.throw_history[self.current_player] = (
                self.throw_history[self.current_player][:-3]
            )
        elif remaining - round_score == 0:
            # 正好归零
            self.scores[self.current_player] = 0
            self.game_over = True
            self.winner = self.current_player
            self.result_text = f"玩家 {self.current_player + 1} 获胜！🎯"
            self.show_result = True
            self.result_timer = 120
            return
        else:
            new_score = remaining - round_score
            self.scores[self.current_player] = new_score
            self.result_text = f"本轮得分: {round_score}，剩余: {new_score}"

        self.round_history[self.current_player].append(round_score)
        self.show_result = True
        self.result_timer = 90

    def next_turn(self):
        """切换到下一位玩家"""
        self.show_result = False
        self.darts = []
        self.dart_count = 0
        self.throw_ready = True
        self.current_player = 1 - self.current_player

    def draw(self):
        """绘制画面"""
        self.screen.fill(BLACK_ACCENT)

        # 绘制飞镖盘
        draw_dartboard(self.screen, BOARD_CENTER, BOARD_RADIUS)

        # 绘制飞镖
        for dart in self.darts:
            dart.draw(self.screen)

        # 绘制瞄准线
        if self.charging and not self.game_over:
            # 蓄力指示器
            mx, my = self.aim_pos
            pygame.draw.line(self.screen, (255, 255, 255, 100),
                             (WIDTH // 2, HEIGHT + 30), (mx, my), 1)
            # 蓄力条
            bar_x, bar_y = WIDTH - 60, HEIGHT // 2 - 100
            bar_w, bar_h = 30, 200
            pygame.draw.rect(self.screen, GRAY, (bar_x, bar_y, bar_w, bar_h), 2)
            fill_h = int(self.power * bar_h)
            power_color = (int(255 * self.power), int(255 * (1 - self.power)), 50)
            pygame.draw.rect(self.screen, power_color,
                             (bar_x + 2, bar_y + bar_h - fill_h, bar_w - 4, fill_h))
            # 蓄力文字
            pct = int(self.power * 100)
            pct_text = self.font_small.render(f"{pct}%", True, WHITE)
            self.screen.blit(pct_text, (bar_x - 10, bar_y + bar_h + 10))
        elif not self.game_over and self.throw_ready and not self.show_result:
            # 准星
            mx, my = self.aim_pos
            pygame.draw.circle(self.screen, (255, 50, 50, 150), (mx, my), 5, 2)
            pygame.draw.line(self.screen, (255, 50, 50, 100),
                             (mx - 10, my), (mx + 10, my), 1)
            pygame.draw.line(self.screen, (255, 50, 50, 100),
                             (mx, my - 10), (mx, my + 10), 1)

        # 绘制计分板
        self.draw_scoreboard()

        # 绘制回合信息
        if self.show_result and self.result_text:
            # 半透明背景
            overlay = pygame.Surface((WIDTH, 80), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, HEIGHT - 80))
            result_surf = self.font_medium.render(self.result_text, True, GOLD)
            result_rect = result_surf.get_rect(center=(WIDTH // 2, HEIGHT - 40))
            self.screen.blit(result_surf, result_rect)

        # 游戏结束画面
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            winner_text = f"玩家 {self.winner + 1} 获胜！"
            win_surf = self.font_large.render(winner_text, True, GOLD)
            win_rect = win_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
            self.screen.blit(win_surf, win_rect)
            restart_surf = self.font_medium.render("按 R 键重新开始", True, WHITE)
            restart_rect = restart_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            self.screen.blit(restart_surf, restart_rect)

        # 提示信息
        if not self.game_over and self.throw_ready and not self.show_result:
            hint = "按住左键蓄力，松开投掷"
            hint_surf = self.font_small.render(hint, True, GRAY)
            self.screen.blit(hint_surf, (20, HEIGHT - 35))

        pygame.display.flip()

    def draw_scoreboard(self):
        """绘制计分板"""
        # 顶部计分板背景
        pygame.draw.rect(self.screen, (30, 30, 40), (0, 0, WIDTH, 90))
        pygame.draw.line(self.screen, GRAY, (0, 90), (WIDTH, 90), 1)

        # 玩家 1
        p1_color = BLUE if self.current_player == 0 and not self.game_over else GRAY
        p1_label = self.font_medium.render(f"玩家 1", True, p1_color)
        self.screen.blit(p1_label, (50, 10))
        p1_score = self.font_large.render(f"{self.scores[0]}", True, WHITE)
        self.screen.blit(p1_score, (60, 40))

        # 分隔线
        pygame.draw.line(self.screen, GRAY, (WIDTH // 2 - 100, 10),
                         (WIDTH // 2 - 100, 80), 1)

        # 中间：当前回合/飞镖信息
        turn_text = f"第 {len(self.round_history[0]) + len(self.round_history[1]) + 1} 回合"
        turn_surf = self.font_small.render(turn_text, True, GRAY)
        turn_rect = turn_surf.get_rect(center=(WIDTH // 2, 20))
        self.screen.blit(turn_surf, turn_rect)

        dart_dots = ""
        for i in range(self.dart_limit):
            if i < self.dart_count:
                dart_dots += "● "
            else:
                dart_dots += "○ "
        dart_surf = self.font_small.render(dart_dots.strip(), True, GOLD)
        dart_rect = dart_surf.get_rect(center=(WIDTH // 2, 50))
        self.screen.blit(dart_surf, dart_rect)

        # 当前玩家指示
        player_ind = f"← 当前玩家" if self.current_player == 0 else ""
        ind_surf = self.font_small.render(player_ind, True, BLUE)
        self.screen.blit(ind_surf, (50, 70))

        # 分隔线
        pygame.draw.line(self.screen, GRAY, (WIDTH // 2 + 100, 10),
                         (WIDTH // 2 + 100, 80), 1)

        # 玩家 2
        p2_color = BLUE if self.current_player == 1 and not self.game_over else GRAY
        p2_label = self.font_medium.render(f"玩家 2", True, p2_color)
        self.screen.blit(p2_label, (WIDTH - 200, 10))
        p2_score = self.font_large.render(f"{self.scores[1]}", True, WHITE)
        self.screen.blit(p2_score, (WIDTH - 190, 40))

        player_ind2 = "← 当前玩家" if self.current_player == 1 else ""
        ind_surf2 = self.font_small.render(player_ind2, True, BLUE)
        p2_label_w = p2_label.get_width()
        self.screen.blit(ind_surf2, (WIDTH - 200, 70))

        # 最近投掷历史
        for p in range(2):
            if self.throw_history[p]:
                recent = self.throw_history[p][-3:]
                hist_text = " ".join(str(s) for s in recent)
                hist_surf = self.font_small.render(hist_text, True, GRAY)
                if p == 0:
                    self.screen.blit(hist_surf, (50, 90))
                else:
                    self.screen.blit(hist_surf, (WIDTH - 200, 90))

    def run(self):
        """主循环"""
        while self.running:
            self.handle_events()
            self.update()

            # 结果计时器
            if self.show_result and not self.game_over:
                self.result_timer -= 1
                if self.result_timer <= 0:
                    self.next_turn()

            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()