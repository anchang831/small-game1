"""
Plinko 弹珠机 - 经典游戏节目风格
==============================
使用 Pygame 实现的 Plinko 弹珠机游戏。
球从顶部落下，经过钉板反弹，最终落入底部槽位获得分数。

操作说明:
- 鼠标左右移动选择落球位置
- 点击鼠标左键释放球
- 按 R 键重置游戏
- 按 ESC 或 Q 退出

作者: AI 游戏开发者
日期: 2026-07-20
"""

import pygame
import random
import math

# ==================== 常量配置 ====================
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
BOARD_TOP = 80
BOARD_BOTTOM = 700
FPS = 60

# 颜色
BLACK = (20, 20, 30)
WHITE = (245, 245, 255)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 150, 255)
DARK_BLUE = (25, 25, 60)
PEG_COLOR = (180, 180, 200)
PEG_HIT = (255, 220, 100)
SLOT_COLORS = [
    (255, 100, 50),   # 红色 - 低倍率
    (255, 180, 50),   # 橙色
    (255, 255, 50),   # 黄色
    (100, 255, 100),  # 绿色
    (50, 200, 255),   # 青色
    (100, 100, 255),  # 蓝色
    (200, 100, 255),  # 紫色
    (255, 100, 200),  # 粉色
    (255, 255, 50),   # 黄色
    (255, 180, 50),   # 橙色
    (255, 100, 50),   # 红色
]
SLOT_MULTIPLIERS = [0.5, 1, 1.5, 3, 5, 10, 5, 3, 1.5, 1, 0.5]

# 物理参数
GRAVITY = 0.15
FRICTION = 0.99
BOUNCE = 0.6
PEG_RADIUS = 6
BALL_RADIUS = 8

# 钉板布局
PEG_ROWS = 12
PEG_COLS = 12
PEG_SPACING_X = 40
PEG_SPACING_Y = 36
BOARD_LEFT = (SCREEN_WIDTH - (PEG_COLS - 1) * PEG_SPACING_X) // 2

# 底部槽位
SLOT_COUNT = 11
SLOT_WIDTH = (SCREEN_WIDTH - 20) // SLOT_COUNT
SLOT_HEIGHT = 40
SLOT_TOP = BOARD_BOTTOM - SLOT_HEIGHT


class Ball:
    """弹珠球体"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = BALL_RADIUS
        self.active = True
        self.trail = []  # 运动轨迹

    def update(self, pegs, slots):
        """更新物理位置"""
        if not self.active:
            return False

        # 重力
        self.vy += GRAVITY

        # 摩擦力
        self.vx *= FRICTION

        # 更新位置
        self.x += self.vx
        self.y += self.vy

        # 记录轨迹
        self.trail.append((int(self.x), int(self.y)))
        if len(self.trail) > 50:
            self.trail.pop(0)

        # 边界碰撞（左右墙）
        left_wall = BOARD_LEFT
        right_wall = BOARD_LEFT + (PEG_COLS - 1) * PEG_SPACING_X
        if self.x - self.radius < left_wall:
            self.x = left_wall + self.radius
            self.vx = -self.vx * BOUNCE
        elif self.x + self.radius > right_wall:
            self.x = right_wall - self.radius
            self.vx = -self.vx * BOUNCE

        # 与钉子碰撞
        for peg in pegs:
            dx = self.x - peg.x
            dy = self.y - peg.y
            dist = math.hypot(dx, dy)
            min_dist = self.radius + PEG_RADIUS
            if dist < min_dist:
                # 碰撞响应
                if dist == 0:
                    dist = 0.01
                nx = dx / dist
                ny = dy / dist
                overlap = min_dist - dist
                self.x += nx * overlap
                self.y += ny * overlap

                # 速度反射
                dot = self.vx * nx + self.vy * ny
                self.vx -= 2 * dot * nx
                self.vy -= 2 * dot * ny

                # 随机扰动（增加不可预测性）
                self.vx += random.uniform(-0.5, 0.5)
                
                # 触发钉子闪烁
                peg.hit()
                break

        # 检查是否进入底部槽位
        if self.y + self.radius > SLOT_TOP:
            slot_idx = int((self.x - 10) / SLOT_WIDTH)
            slot_idx = max(0, min(SLOT_COUNT - 1, slot_idx))
            if self.y > BOARD_BOTTOM:
                self.active = False
                return slot_idx

        return False

    def draw(self, screen):
        """绘制球"""
        # 绘制轨迹
        for i, (tx, ty) in enumerate(self.trail):
            alpha = i / len(self.trail) * 0.4
            pygame.draw.circle(screen, (255, 200, 50, int(alpha * 255)),
                               (tx, ty), 2)

        # 绘制球体（带渐变效果）
        pygame.draw.circle(screen, (255, 220, 80), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (255, 255, 200), (int(self.x) - 2, int(self.y) - 2), self.radius - 3)


class Peg:
    """钉子"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = PEG_RADIUS
        self.hit_timer = 0  # 闪烁计时

    def hit(self):
        """被球击中"""
        self.hit_timer = 10

    def update(self):
        """更新闪烁状态"""
        if self.hit_timer > 0:
            self.hit_timer -= 1

    def draw(self, screen):
        """绘制钉子"""
        if self.hit_timer > 0:
            # 闪烁效果
            brightness = self.hit_timer * 25
            color = (min(255, 180 + brightness), min(255, 180 + brightness), 200)
            glow_radius = PEG_RADIUS + 4
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), glow_radius)
        else:
            # 正常钉子 - 带立体效果
            pygame.draw.circle(screen, (120, 120, 140), (int(self.x), int(self.y)), PEG_RADIUS)
            pygame.draw.circle(screen, PEG_COLOR, (int(self.x) - 1, int(self.y) - 1), PEG_RADIUS - 1)


class Slot:
    """底部槽位"""

    def __init__(self, idx, x, y, width, height, multiplier, color):
        self.idx = idx
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.multiplier = multiplier
        self.color = color
        self.highlight = False

    def draw(self, screen, font):
        """绘制槽位"""
        color = self.color
        if self.highlight:
            color = tuple(min(255, c + 80) for c in color)

        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, color, rect, border_radius=4)
        pygame.draw.rect(screen, WHITE, rect, 2, border_radius=4)

        # 显示倍率
        mult_text = f"x{self.multiplier}"
        text_surf = font.render(mult_text, True, WHITE)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)


class Plinko:
    """Plinko 游戏主类"""

    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 48)
        self.font_mid = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)

        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        # 创建钉子
        self.pegs = []
        self.create_pegs()

        # 创建底部槽位
        self.slots = []
        self.create_slots()

        # 球
        self.balls = []
        self.ball_queue = 10  # 剩余球数
        self.drop_pos = SCREEN_WIDTH // 2

        # 分数
        self.score = 0
        self.total_score = 0
        self.round_score = 0
        self.last_mult = 0
        self.show_result = False
        self.result_timer = 0

        # 游戏状态
        self.game_over = False
        self.can_drop = True

    def create_pegs(self):
        """创建钉板布局"""
        for row in range(PEG_ROWS):
            cols_in_row = PEG_COLS - row % 2  # 奇偶行交错
            offset_x = 0 if row % 2 == 0 else PEG_SPACING_X // 2
            for col in range(cols_in_row):
                x = BOARD_LEFT + col * PEG_SPACING_X + offset_x
                y = BOARD_TOP + row * PEG_SPACING_Y
                # 避开底部两行让球通过
                if row < PEG_ROWS - 2:
                    self.pegs.append(Peg(x, y))

    def create_slots(self):
        """创建底部槽位"""
        for i in range(SLOT_COUNT):
            x = 10 + i * SLOT_WIDTH
            y = SLOT_TOP
            color = SLOT_COLORS[i % len(SLOT_COLORS)]
            mult = SLOT_MULTIPLIERS[i % len(SLOT_MULTIPLIERS)]
            self.slots.append(Slot(i, x, y, SLOT_WIDTH, SLOT_HEIGHT, mult, color))

    def drop_ball(self):
        """释放一个球"""
        if self.ball_queue <= 0 or not self.can_drop:
            return

        # 从落球位置释放
        ball_x = self.drop_pos
        ball_y = BOARD_TOP - 20
        self.balls.append(Ball(ball_x, ball_y))
        self.ball_queue -= 1
        self.can_drop = False
        self.show_result = False

    def update(self):
        """更新游戏状态"""
        # 更新钉子
        for peg in self.pegs:
            peg.update()

        # 更新球
        balls_to_remove = []
        for ball in self.balls:
            if ball.active:
                result = ball.update(self.pegs, self.slots)
                if result is not False:
                    # 球进入槽位
                    slot_idx = result
                    multiplier = self.slots[slot_idx].multiplier
                    self.round_score = int(10 * multiplier)
                    self.total_score += self.round_score
                    self.last_mult = multiplier
                    self.show_result = True
                    self.result_timer = 120  # 显示结果2秒
                    self.slots[slot_idx].highlight = True
                    balls_to_remove.append(ball)
            else:
                balls_to_remove.append(ball)

        # 移除已落地的球
        for ball in balls_to_remove:
            if ball in self.balls:
                self.balls.remove(ball)

        # 结果计时
        if self.show_result:
            self.result_timer -= 1
            if self.result_timer <= 0:
                self.show_result = False
                self.can_drop = True
                # 清除高亮
                for slot in self.slots:
                    slot.highlight = False

        # 检查游戏结束
        if self.ball_queue <= 0 and len(self.balls) == 0:
            self.game_over = True

    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(DARK_BLUE)

        # 绘制背景装饰
        self._draw_background()

        # 绘制钉子
        for peg in self.pegs:
            peg.draw(self.screen)

        # 绘制槽位
        for slot in self.slots:
            slot.draw(self.screen, self.font_small)

        # 绘制球
        for ball in self.balls:
            ball.draw(self.screen)

        # 绘制落球指示器
        self._draw_drop_indicator()

        # 绘制UI信息
        self._draw_ui()

        # 绘制游戏结束
        if self.game_over:
            self._draw_game_over()

    def _draw_background(self):
        """绘制背景装饰"""
        # 绘制木板背景
        board_rect = pygame.Rect(
            BOARD_LEFT - 20, BOARD_TOP - 40,
            (PEG_COLS - 1) * PEG_SPACING_X + 40,
            BOARD_BOTTOM - BOARD_TOP + 20
        )
        pygame.draw.rect(self.screen, (30, 25, 50), board_rect, border_radius=10)
        pygame.draw.rect(self.screen, (60, 55, 80), board_rect, 2, border_radius=10)

        # 顶部装饰线
        pygame.draw.line(self.screen, GOLD,
                         (BOARD_LEFT - 10, BOARD_TOP - 30),
                         (BOARD_LEFT + (PEG_COLS - 1) * PEG_SPACING_X + 10, BOARD_TOP - 30), 2)

    def _draw_drop_indicator(self):
        """绘制落球位置指示器"""
        if self.can_drop and self.ball_queue > 0:
            # 垂直引导线
            pygame.draw.line(self.screen, (255, 255, 255, 50),
                             (self.drop_pos, BOARD_TOP - 40),
                             (self.drop_pos, BOARD_TOP + 20), 1)
            # 三角形指示器
            points = [
                (self.drop_pos, BOARD_TOP - 45),
                (self.drop_pos - 10, BOARD_TOP - 55),
                (self.drop_pos + 10, BOARD_TOP - 55),
            ]
            pygame.draw.polygon(self.screen, GOLD, points)

    def _draw_ui(self):
        """绘制UI信息"""
        # 球数
        balls_text = self.font_mid.render(f"剩余球: {self.ball_queue}", True, WHITE)
        self.screen.blit(balls_text, (20, 20))

        # 总分
        score_text = self.font_large.render(f"总分: {self.total_score}", True, GOLD)
        score_rect = score_text.get_rect(topright=(SCREEN_WIDTH - 20, 15))
        self.screen.blit(score_text, score_rect)

        # 当前回合结果
        if self.show_result:
            result_text = self.font_large.render(f"x{self.last_mult}  +{self.round_score}!", True, GOLD)
            result_rect = result_text.get_rect(center=(SCREEN_WIDTH // 2, BOARD_BOTTOM + 40))
            self.screen.blit(result_text, result_rect)

        # 操作提示
        if self.can_drop and self.ball_queue > 0:
            hint = self.font_tiny.render("点击鼠标左键释放球", True, SILVER)
            hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, BOARD_BOTTOM + 80))
            self.screen.blit(hint, hint_rect)

        # 倍率说明
        mult_hint = self.font_tiny.render("底部槽位倍率: x0.5 ~ x10", True, SILVER)
        mult_rect = mult_hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 15))
        self.screen.blit(mult_hint, mult_rect)

    def _draw_game_over(self):
        """绘制游戏结束画面"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # 游戏结束文字
        title = self.font_large.render("游戏结束!", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
        self.screen.blit(title, title_rect)

        final_score = self.font_mid.render(f"最终得分: {self.total_score}", True, WHITE)
        score_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(final_score, score_rect)

        restart = self.font_mid.render("按 R 重新开始", True, SILVER)
        restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(restart, restart_rect)

    def handle_event(self, event):
        """处理输入事件"""
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                return False
            if event.key == pygame.K_r:
                self.reset_game()
                return True

        if event.type == pygame.MOUSEMOTION:
            # 更新落球位置
            self.drop_pos = max(BOARD_LEFT + 10,
                                min(BOARD_LEFT + (PEG_COLS - 1) * PEG_SPACING_X - 10,
                                    event.pos[0]))

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键
                self.drop_ball()

        return True

    def run(self):
        """主游戏循环"""
        running = True
        while running:
            for event in pygame.event.get():
                running = self.handle_event(event)
                if not running:
                    break

            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


def main():
    """主函数"""
    pygame.init()
    pygame.display.set_caption("Plinko 弹珠机")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    game = Plinko(screen)
    game.run()


if __name__ == "__main__":
    main()