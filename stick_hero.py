"""
Stick Hero (火柴人英雄)
一个经典手机游戏：火柴人通过搭建桥梁跨越平台间隙
控制方式：按住空格键/鼠标蓄力，松开释放桥
"""

import pygame
import random
import math

# 初始化
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Stick Hero - 火柴人英雄")
clock = pygame.time.Clock()
font_large = pygame.font.SysFont("simhei", 48)
font_mid = pygame.font.SysFont("simhei", 32)
font_small = pygame.font.SysFont("simhei", 24)

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
BLUE = (52, 152, 219)
GREEN = (46, 204, 113)
RED = (231, 76, 60)
ORANGE = (243, 156, 18)
LIGHT_BLUE = (174, 214, 241)
BROWN = (139, 90, 43)
SKIN = (255, 220, 177)

# 游戏常量
GROUND_Y = 500
PLATFORM_MIN_W = 80
PLATFORM_MAX_W = 150
GAP_MIN = 60
GAP_MAX = 250
STICK_GROW_SPEED = 4  # 桥生长速度（像素/帧）

# ==================== 火柴人绘制 ====================
def draw_stickman(surface, x, y, scale=1.0):
    """在指定位置绘制火柴人，x,y为脚底位置"""
    head_r = int(12 * scale)
    body_len = int(30 * scale)
    arm_len = int(18 * scale)
    leg_len = int(22 * scale)

    # 头
    pygame.draw.circle(surface, SKIN, (x, y - body_len - head_r), head_r)
    pygame.draw.circle(surface, BLACK, (x, y - body_len - head_r), head_r, 2)
    # 身体
    pygame.draw.line(surface, BLACK, (x, y - body_len), (x, y), 3)
    # 手臂
    pygame.draw.line(surface, BLACK, (x - arm_len, y - body_len + 5), (x + arm_len, y - body_len + 5), 2)
    # 左腿
    pygame.draw.line(surface, BLACK, (x, y), (x - leg_len, y + leg_len), 3)
    # 右腿
    pygame.draw.line(surface, BLACK, (x, y), (x + leg_len, y + leg_len), 3)


def draw_stickman_falling(surface, x, y, angle, scale=1.0):
    """绘制正在掉落/旋转的火柴人"""
    head_r = int(12 * scale)
    body_len = int(30 * scale)
    # 旋转整个火柴人
    pts = [
        (0, -(body_len + head_r)),  # 头中心
        (0, -body_len),
        (0, 0),
        (-18, 5),
        (18, 5),
        (-22, 22),
        (22, 22),
    ]
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    transformed = []
    for px, py in pts:
        tx = x + px * cos_a - py * sin_a
        ty = y + px * sin_a + py * cos_a
        transformed.append((tx, ty))

    pygame.draw.circle(surface, SKIN, (int(transformed[0][0]), int(transformed[0][1])), head_r)
    pygame.draw.circle(surface, BLACK, (int(transformed[0][0]), int(transformed[0][1])), head_r, 2)
    pygame.draw.line(surface, BLACK, transformed[1], transformed[2], 3)
    pygame.draw.line(surface, BLACK, transformed[3], transformed[4], 2)
    pygame.draw.line(surface, BLACK, transformed[2], transformed[5], 3)
    pygame.draw.line(surface, BLACK, transformed[2], transformed[6], 3)


# ==================== 平台类 ====================
class Platform:
    def __init__(self, x, width, is_start=False):
        self.x = x
        self.width = width
        self.height = 20
        self.y = GROUND_Y - self.height
        self.is_start = is_start

    def draw(self, surface):
        color = GREEN if self.is_start else BLUE
        pygame.draw.rect(surface, color, (self.x, self.y, self.width, self.height))
        # 顶部装饰线
        pygame.draw.line(surface, WHITE, (self.x, self.y),
                         (self.x + self.width, self.y), 3)
        # 纹理
        for i in range(3):
            tx = self.x + 10 + i * (self.width // 4)
            pygame.draw.rect(surface, (color[0] - 20, color[1] - 20, color[2] - 20),
                             (tx, self.y + 5, 8, 10), border_radius=2)

    @property
    def right(self):
        return self.x + self.width

    @property
    def center_x(self):
        return self.x + self.width // 2


# ==================== 桥类 ====================
class Stick:
    def __init__(self, x, y):
        self.x = x  # 桥起点（平台右边缘）
        self.y = y  # 桥顶部（与平台齐平）
        self.length = 0
        self.growing = True
        self.placed = False

    def grow(self):
        if self.growing and not self.placed:
            self.length += STICK_GROW_SPEED
            if self.length > 500:  # 最大长度限制
                self.length = 500

    def stop_growing(self):
        self.growing = False
        self.placed = True

    def draw(self, surface):
        if self.length > 0:
            # 桥身
            rect = (self.x, self.y - 8, self.length, 16)
            pygame.draw.rect(surface, BROWN, rect, border_radius=3)
            pygame.draw.rect(surface, DARK_GRAY, rect, 2, border_radius=3)
            # 纹理线
            for i in range(0, int(self.length), 15):
                pygame.draw.line(surface, DARK_GRAY,
                                 (self.x + i, self.y - 5),
                                 (self.x + i, self.y + 5), 1)

    @property
    def right(self):
        return self.x + self.length

    @property
    def tip_x(self):
        return self.x + self.length


# ==================== 游戏主类 ====================
class StickHero:
    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.score = 0
        self.best_score = 0
        self.game_state = "playing"  # playing | crossing | falling | gameover
        self.platforms = []
        self.stick = None
        self.hero_x = 0
        self.hero_y = GROUND_Y
        self.hero_walk_target = 0
        self.hero_walk_progress = 0
        self.fall_angle = 0
        self.fall_speed = 0
        self.fall_dir = 1  # 掉落方向
        self.cross_timer = 0
        self.final_score_shown = False

        # 生成初始平台
        start_w = 120
        start_x = 50
        self.platforms.append(Platform(start_x, start_w, is_start=True))
        self.hero_x = start_x + start_w // 2
        self._add_next_platform()

    def _add_next_platform(self):
        """在最后一个平台右侧添加一个新平台"""
        last = self.platforms[-1]
        gap = random.randint(GAP_MIN, GAP_MAX)
        pw = random.randint(PLATFORM_MIN_W, PLATFORM_MAX_W)
        new_x = last.right + gap
        self.platforms.append(Platform(new_x, pw))

    def _is_stick_perfect(self):
        """检查桥是否完美匹配间隙"""
        if len(self.platforms) < 2:
            return False
        p0 = self.platforms[-2]
        p1 = self.platforms[-1]
        gap_start = p0.right
        gap_end = p1.x
        tip = self.stick.tip_x if self.stick else gap_start
        # 完美：桥尖在平台范围内
        return gap_start <= tip <= gap_end + p1.width

    def handle_click_down(self):
        """按下鼠标/空格 - 开始生长桥"""
        if self.game_state == "playing":
            last = self.platforms[-2]
            self.stick = Stick(last.right, last.y)

    def handle_click_up(self):
        """松开鼠标/空格 - 放下桥"""
        if self.game_state == "playing" and self.stick and self.stick.growing:
            self.stick.stop_growing()
            self._check_cross()

    def _check_cross(self):
        """检查桥是否搭到下一个平台"""
        if len(self.platforms) < 2:
            return
        p0 = self.platforms[-2]
        p1 = self.platforms[-1]
        tip = self.stick.tip_x

        if tip < p1.x:
            # 桥太短，掉落到左边
            self.game_state = "falling"
            self.fall_dir = -1
            self.fall_angle = 0
            self.fall_speed = 0.05
        elif tip > p1.x + p1.width:
            # 桥太长，掉落到右边
            self.game_state = "falling"
            self.fall_dir = 1
            self.fall_angle = 0
            self.fall_speed = 0.05
        else:
            # 成功！火柴人走过去
            self.game_state = "crossing"
            self.hero_walk_target = p1.x + p1.width // 2
            self.hero_walk_progress = 0
            self.cross_timer = 0

            # 完美命中奖励
            if self._is_stick_perfect():
                self.score += 1

    def update(self):
        """每帧更新游戏状态"""
        if self.game_state == "playing":
            if self.stick and self.stick.growing:
                self.stick.grow()

        elif self.game_state == "crossing":
            # 火柴人行走动画
            self.cross_timer += 1
            total_steps = 40
            self.hero_walk_progress = min(self.cross_timer / total_steps, 1.0)
            p0 = self.platforms[-2]
            p1 = self.platforms[-1]
            start_x = p0.right
            end_x = p1.x + p1.width // 2
            self.hero_x = start_x + (end_x - start_x) * self.hero_walk_progress

            if self.hero_walk_progress >= 1.0:
                # 到达！记分，生成新平台
                self.score += 1
                self.game_state = "playing"
                self.stick = None
                self._add_next_platform()
                # 移除太远的旧平台（保持屏幕上干净）
                if len(self.platforms) > 4:
                    self.platforms.pop(0)

        elif self.game_state == "falling":
            # 掉落动画
            self.fall_angle += self.fall_speed * self.fall_dir
            self.hero_y += 6
            if self.hero_y > HEIGHT + 100:
                self.game_state = "gameover"
                self.final_score_shown = False

    def draw(self, surface):
        surface.fill(WHITE)

        # 绘制背景
        # 天空渐变
        for i in range(GROUND_Y):
            r = 135 + i * 0.05
            g = 206 + i * 0.02
            b = 235 - i * 0.05
            r = max(0, min(255, int(r)))
            g = max(0, min(255, int(g)))
            b = max(0, min(255, int(b)))
            pygame.draw.line(surface, (r, g, b), (0, i), (WIDTH, i))

        # 地面
        pygame.draw.rect(surface, DARK_GRAY, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.line(surface, BLACK, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

        # 地面纹理
        for i in range(0, WIDTH, 30):
            pygame.draw.line(surface, GRAY, (i, GROUND_Y), (i + 15, GROUND_Y + 15), 1)

        # 绘制平台
        for p in self.platforms:
            p.draw(surface)

        # 绘制桥
        if self.stick:
            self.stick.draw(surface)

        # 绘制火柴人（根据状态）
        if self.game_state == "falling":
            draw_stickman_falling(surface, self.hero_x, self.hero_y, self.fall_angle)
        elif self.game_state == "crossing":
            # 行走动画 - 轻微上下摆动
            walk_offset = abs(math.sin(self.cross_timer * 0.15)) * 3
            draw_stickman(surface, self.hero_x, self.hero_y - walk_offset)
        else:
            draw_stickman(surface, self.hero_x, self.hero_y)

        # 绘制UI
        # 分数
        score_text = font_mid.render(f"Score: {self.score}", True, BLACK)
        surface.blit(score_text, (20, 20))

        if self.best_score > 0:
            best_text = font_small.render(f"Best: {self.best_score}", True, GRAY)
            surface.blit(best_text, (20, 60))

        # 当前间隙提示
        if self.game_state == "playing" and len(self.platforms) >= 2:
            p0 = self.platforms[-2]
            p1 = self.platforms[-1]
            gap = p1.x - p0.right
            if gap > 0:
                gap_text = font_small.render(f"Gap: {gap}", True, DARK_GRAY)
                gap_center_x = p0.right + gap // 2
                surface.blit(gap_text, (gap_center_x - gap_text.get_width() // 2, GROUND_Y - 40))

        # 游戏结束
        if self.game_state == "gameover":
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            surface.blit(overlay, (0, 0))

            title = font_large.render("Game Over", True, RED)
            surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 180))

            score_text = font_mid.render(f"Score: {self.score}", True, WHITE)
            surface.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 250))

            if self.score >= self.best_score and self.score > 0:
                new_best = font_mid.render("New Best!", True, ORANGE)
                surface.blit(new_best, (WIDTH // 2 - new_best.get_width() // 2, 300))

            hint = font_small.render("Press SPACE or Click to Restart", True, WHITE)
            surface.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 360))

        # 操作提示（仅在开始几帧显示）
        if self.game_state == "playing" and self.score < 3:
            if self.stick is None:
                hint = font_small.render("Hold SPACE / Click to grow the bridge!", True, GRAY)
                surface.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 100))
            elif self.stick.growing:
                hint = font_small.render("Release to place the bridge!", True, GRAY)
                surface.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 100))

        # 完美提示
        if self.game_state == "crossing" and self._is_stick_perfect():
            perf = font_small.render("Perfect!", True, ORANGE)
            surface.blit(perf, (WIDTH // 2 - perf.get_width() // 2, HEIGHT // 2 - 50))


def main():
    game = StickHero()
    running = True

    # 读取最高分
    try:
        with open("stick_hero_best.txt", "r") as f:
            game.best_score = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        game.best_score = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    if game.game_state == "gameover":
                        # 保存最佳分数
                        if game.score > game.best_score:
                            game.best_score = game.score
                            with open("stick_hero_best.txt", "w") as f:
                                f.write(str(game.best_score))
                        game.reset_game()
                        game.best_score = game.best_score  # 保持最佳记录
                    else:
                        game.handle_click_down()

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE and game.game_state == "playing":
                    game.handle_click_up()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if game.game_state == "gameover":
                    if game.score > game.best_score:
                        game.best_score = game.score
                        with open("stick_hero_best.txt", "w") as f:
                            f.write(str(game.best_score))
                    game.reset_game()
                    game.best_score = game.best_score
                else:
                    game.handle_click_down()

            if event.type == pygame.MOUSEBUTTONUP:
                if game.game_state == "playing":
                    game.handle_click_up()

        game.update()
        game.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    # 退出时保存最佳分数
    if game.score > game.best_score:
        with open("stick_hero_best.txt", "w") as f:
            f.write(str(game.score))

    pygame.quit()


if __name__ == "__main__":
    main()