"""
Peggle（弹球消除）
==================
玩法：从底部发射小球，球在彩色钉子间弹跳碰撞。
      消除所有橙色钉子即可过关！
      
操作：
  - 鼠标移动控制发射角度
  - 点击鼠标左键发射小球
  - R 键重新开始当前关卡
  - ESC 退出游戏

依赖：pygame（pip install pygame）
运行：python peggle.py
"""

import pygame
import math
import random
import sys

# 初始化 Pygame
pygame.init()

# ============ 常量设置 ============
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

# 颜色定义
COLORS = {
    "bg": (20, 20, 40),
    "orange": (255, 140, 0),
    "orange_glow": (255, 180, 50),
    "blue": (60, 120, 255),
    "blue_glow": (100, 160, 255),
    "green": (50, 200, 50),
    "purple": (200, 50, 200),
    "red": (255, 60, 60),
    "white": (255, 255, 255),
    "gray": (100, 100, 100),
    "paddle": (200, 200, 100),
    "ball": (255, 255, 100),
    "ball_glow": (255, 255, 200),
    "launcher": (150, 150, 150),
    "wall": (80, 80, 120),
}

# 游戏区域
PLAY_LEFT = 50
PLAY_RIGHT = 750
PLAY_TOP = 60
PLAY_BOTTOM = 650

# 钉子参数
PEG_RADIUS = 12
PEG_SPACING_X = 38
PEG_SPACING_Y = 34
PEG_ROWS = 16

# 球参数
BALL_RADIUS = 8
LAUNCH_POWER = 18

# 物理参数
GRAVITY = 0.15
FRICTION = 0.98
BOUNCE_FACTOR = 0.85


class Peg:
    """单个钉子"""

    def __init__(self, x, y, color_type="blue"):
        self.x = x
        self.y = y
        self.radius = PEG_RADIUS
        self.color_type = color_type  # "orange" or "blue"
        self.active = True
        self.hit_flash = 0  # 击中闪烁计时

    def get_color(self):
        """获取当前颜色"""
        if self.color_type == "orange":
            return COLORS["orange"], COLORS["orange_glow"]
        else:
            return COLORS["blue"], COLORS["blue_glow"]

    def draw(self, screen):
        """绘制钉子"""
        if not self.active and self.hit_flash <= 0:
            return

        if self.hit_flash > 0:
            # 击中后闪烁消失效果
            alpha = min(255, self.hit_flash * 30)
            color = (255, 255, 255)
            glow_color = (255, 255, 200)
            self.hit_flash -= 1
            if self.hit_flash <= 0:
                self.active = False
                return
        else:
            color, glow_color = self.get_color()

        # 发光效果
        glow_surf = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        if self.hit_flash > 0:
            glow_radius = self.radius * 2
            glow_color_rgba = (*glow_color, 150)
        else:
            glow_radius = self.radius * 1.5
            glow_color_rgba = (*glow_color, 80)
        pygame.draw.circle(glow_surf, glow_color_rgba,
                          (glow_radius, glow_radius), glow_radius)
        screen.blit(glow_surf,
                   (self.x - glow_radius, self.y - glow_radius))

        # 主球体
        pygame.draw.circle(screen, color,
                          (int(self.x), int(self.y)), self.radius)

        # 高光
        highlight_color = (min(255, color[0] + 80),
                          min(255, color[1] + 80),
                          min(255, color[2] + 80))
        pygame.draw.circle(screen, highlight_color,
                          (int(self.x - 3), int(self.y - 3)), self.radius // 3)


class Ball:
    """弹球"""

    def __init__(self, x, y):
        self.start_x = x
        self.start_y = y
        self.reset()

    def reset(self):
        """重置球到发射位置"""
        self.x = self.start_x
        self.y = self.start_y
        self.vx = 0
        self.vy = 0
        self.active = False  # False = 等待发射
        self.launched = False

    def launch(self, angle_deg):
        """以指定角度发射球"""
        angle_rad = math.radians(angle_deg)
        self.vx = LAUNCH_POWER * math.cos(angle_rad)
        self.vy = -LAUNCH_POWER * math.sin(angle_rad)
        self.active = True
        self.launched = True

    def update(self, pegs):
        """更新物理位置和碰撞"""
        if not self.active:
            return False  # 没碰到橙色钉子

        # 应用重力
        self.vy += GRAVITY

        # 应用摩擦（空气阻力）
        self.vx *= FRICTION
        self.vy *= FRICTION

        # 更新位置
        self.x += self.vx
        self.y += self.vy

        # 左右墙壁碰撞
        if self.x - BALL_RADIUS < PLAY_LEFT:
            self.x = PLAY_LEFT + BALL_RADIUS
            self.vx = -self.vx * BOUNCE_FACTOR
        elif self.x + BALL_RADIUS > PLAY_RIGHT:
            self.x = PLAY_RIGHT - BALL_RADIUS
            self.vx = -self.vx * BOUNCE_FACTOR

        # 上墙碰撞
        if self.y - BALL_RADIUS < PLAY_TOP:
            self.y = PLAY_TOP + BALL_RADIUS
            self.vy = -self.vy * BOUNCE_FACTOR

        # 超出底部
        if self.y + BALL_RADIUS > PLAY_BOTTOM:
            self.active = False
            return False

        # 与钉子碰撞检测
        hit_orange = False
        for peg in pegs:
            if not peg.active:
                continue
            dx = self.x - peg.x
            dy = self.y - peg.y
            dist = math.sqrt(dx * dx + dy * dy)
            min_dist = BALL_RADIUS + peg.radius

            if dist < min_dist:
                # 碰撞响应
                if dist > 0:
                    overlap = min_dist - dist
                    nx = dx / dist
                    ny = dy / dist
                    self.x += nx * overlap
                    self.y += ny * overlap

                    # 反射速度
                    dot = self.vx * nx + self.vy * ny
                    self.vx = (self.vx - 2 * dot * nx) * BOUNCE_FACTOR
                    self.vy = (self.vy - 2 * dot * ny) * BOUNCE_FACTOR

                # 标记钉子被击中
                peg.active = False
                peg.hit_flash = 8

                if peg.color_type == "orange":
                    hit_orange = True

                # 轻微随机扰动，防止卡住
                self.vx += random.uniform(-0.5, 0.5)

        return hit_orange


class PeggleGame:
    """游戏主类"""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Peggle 弹球消除")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)

        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        self.level = 1
        self.score = 0
        self.total_orange = 0
        self.cleared_orange = 0
        self.balls_remaining = 10
        self.game_state = "aiming"  # aiming, flying, clearing, game_over, win
        self.particles = []

        self.create_level()

        # 发射器
        launcher_x = SCREEN_WIDTH // 2
        launcher_y = PLAY_BOTTOM - 30
        self.ball = Ball(launcher_x, launcher_y)
        self.aim_angle = 80  # 角度（0=水平右，90=垂直上）

    def create_level(self):
        """创建关卡钉子布局"""
        self.pegs = []

        # 根据关卡调整布局
        orange_ratio = min(0.25 + self.level * 0.02, 0.40)
        offset_x = (SCREEN_WIDTH - (PEG_SPACING_X * 18)) / 2
        offset_y = PLAY_TOP + 40

        for row in range(PEG_ROWS):
            # 每行交替偏移
            x_offset = offset_x + (row % 2) * (PEG_SPACING_X // 2)
            pegs_in_row = 18 - (row % 2)

            for col in range(pegs_in_row):
                x = x_offset + col * PEG_SPACING_X
                y = offset_y + row * PEG_SPACING_Y

                # 检查是否在游戏区域内
                if x < PLAY_LEFT + PEG_RADIUS or x > PLAY_RIGHT - PEG_RADIUS:
                    continue
                if y < PLAY_TOP + PEG_RADIUS or y > PLAY_BOTTOM - 100:
                    continue

                # 随机决定颜色
                if random.random() < orange_ratio:
                    color_type = "orange"
                else:
                    color_type = "blue"

                peg = Peg(x, y, color_type)
                self.pegs.append(peg)
                if color_type == "orange":
                    self.total_orange += 1

    def handle_events(self):
        """处理输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_r:
                    self.reset_game()
                    return True

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.game_state == "aiming":
                    # 发射球
                    self.ball.launch(self.aim_angle)
                    self.game_state = "flying"
                    self.balls_remaining -= 1
                elif self.game_state == "win":
                    # 进入下一关
                    self.level += 1
                    self.balls_remaining = 10
                    self.cleared_orange = 0
                    self.total_orange = 0
                    self.create_level()
                    self.ball.reset()
                    self.ball.x = SCREEN_WIDTH // 2
                    self.ball.y = PLAY_BOTTOM - 30
                    self.game_state = "aiming"
                elif self.game_state == "game_over":
                    # 重新开始
                    self.reset_game()

        # 鼠标控制瞄准角度
        if self.game_state == "aiming":
            mx, my = pygame.mouse.get_pos()
            dx = mx - self.ball.x
            dy = my - self.ball.y
            if dy < 0:  # 只能向上瞄准
                angle = math.degrees(math.atan2(-dy, dx))
                self.aim_angle = max(10, min(170, angle))

        return True

    def update(self):
        """更新游戏逻辑"""
        if self.game_state == "flying":
            hit_orange = self.ball.update(self.pegs)
            if hit_orange:
                self.score += 100
                self.cleared_orange += 1

                # 生成粒子效果
                self.spawn_particles(self.ball.x, self.ball.y, COLORS["orange"])

            # 检查球是否停止
            if not self.ball.active:
                self.game_state = "clearing"
                # 标记所有闪烁结束
                for peg in self.pegs:
                    if peg.hit_flash > 0:
                        peg.hit_flash -= 1

        if self.game_state == "clearing":
            # 检查是否还有闪烁的钉子
            has_flash = any(p.hit_flash > 0 for p in self.pegs if not p.active)
            if not has_flash:
                # 检查是否赢了
                if self.cleared_orange >= self.total_orange:
                    self.game_state = "win"
                    self.score += self.balls_remaining * 200  # 剩余球奖励
                elif self.balls_remaining <= 0:
                    self.game_state = "game_over"
                else:
                    # 准备下一球
                    self.ball.reset()
                    self.ball.x = SCREEN_WIDTH // 2
                    self.ball.y = PLAY_BOTTOM - 30
                    self.game_state = "aiming"

        # 更新粒子效果
        self.update_particles()

    def spawn_particles(self, x, y, color):
        """生成粒子特效"""
        for _ in range(12):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 6)
            particle = {
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": 30,
                "color": color,
                "size": random.uniform(2, 5),
            }
            self.particles.append(particle)

    def update_particles(self):
        """更新粒子效果"""
        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.1
            p["life"] -= 1
            p["size"] *= 0.97
            if p["life"] <= 0 or p["size"] < 0.5:
                self.particles.remove(p)

    def draw_launcher(self):
        """绘制发射器"""
        # 发射器底座
        base_rect = pygame.Rect(
            self.ball.x - 20, self.ball.y - 10, 40, 20
        )
        pygame.draw.rect(self.screen, COLORS["launcher"], base_rect,
                        border_radius=5)

        # 瞄准线
        if self.game_state == "aiming":
            angle_rad = math.radians(self.aim_angle)
            end_x = self.ball.x + math.cos(angle_rad) * 100
            end_y = self.ball.y - math.sin(angle_rad) * 100

            # 虚线瞄准线
            dash_len = 8
            gap_len = 6
            dx = end_x - self.ball.x
            dy = end_y - self.ball.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                dx /= dist
                dy /= dist
                for i in range(0, int(dist), dash_len + gap_len):
                    sx = self.ball.x + dx * i
                    sy = self.ball.y - dy * i  # 屏幕y轴向下
                    ex = self.ball.x + dx * min(i + dash_len, dist)
                    ey = self.ball.y - dy * min(i + dash_len, dist)
                    pygame.draw.line(self.screen, (255, 255, 255, 128),
                                    (sx, sy), (ex, ey), 2)

    def draw_walls(self):
        """绘制墙壁"""
        # 左右上三面墙
        wall_color = COLORS["wall"]
        wall_width = 8

        # 左墙
        pygame.draw.rect(self.screen, wall_color,
                        (PLAY_LEFT - wall_width, PLAY_TOP,
                         wall_width, PLAY_BOTTOM - PLAY_TOP))
        # 右墙
        pygame.draw.rect(self.screen, wall_color,
                        (PLAY_RIGHT, PLAY_TOP,
                         wall_width, PLAY_BOTTOM - PLAY_TOP))
        # 上墙
        pygame.draw.rect(self.screen, wall_color,
                        (PLAY_LEFT - wall_width, PLAY_TOP - wall_width,
                         PLAY_RIGHT - PLAY_LEFT + wall_width * 2, wall_width))

    def draw_hud(self):
        """绘制 HUD 信息"""
        # 分数
        score_text = self.font_medium.render(f"分数: {self.score}", True, COLORS["white"])
        self.screen.blit(score_text, (20, 10))

        # 关卡
        level_text = self.font_medium.render(f"关卡: {self.level}", True, COLORS["white"])
        self.screen.blit(level_text, (SCREEN_WIDTH // 2 - 50, 10))

        # 剩余橙色钉子
        orange_left = self.total_orange - self.cleared_orange
        orange_text = self.font_medium.render(
            f"橙色目标: {orange_left}", True, COLORS["orange"]
        )
        self.screen.blit(orange_text, (SCREEN_WIDTH - 220, 10))

        # 剩余球数
        balls_text = self.font_small.render(
            f"剩余球: {'●' * self.balls_remaining}", True, COLORS["white"]
        )
        self.screen.blit(balls_text, (20, PLAY_BOTTOM - 60))

    def draw_game_over(self):
        """绘制游戏结束画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title = self.font_large.render("游戏结束", True, COLORS["red"])
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 250))

        score_text = self.font_medium.render(f"最终得分: {self.score}", True, COLORS["white"])
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 310))

        hint = self.font_small.render("点击鼠标重新开始", True, COLORS["gray"])
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 370))

    def draw_win(self):
        """绘制过关画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        title = self.font_large.render("🎉 恭喜过关！", True, COLORS["orange"])
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 220))

        score_text = self.font_medium.render(
            f"得分: {self.score}", True, COLORS["white"]
        )
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 280))

        bonus_text = self.font_small.render(
            f"剩余球奖励: +{self.balls_remaining * 200}", True, COLORS["green"]
        )
        self.screen.blit(bonus_text, (SCREEN_WIDTH // 2 - bonus_text.get_width() // 2, 330))

        hint = self.font_small.render("点击进入下一关", True, COLORS["gray"])
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 380))

    def draw_trajectory_preview(self):
        """绘制弹道预览（简化的抛物线）"""
        if self.game_state != "aiming":
            return

        angle_rad = math.radians(self.aim_angle)
        sim_x = self.ball.x
        sim_y = self.ball.y
        sim_vx = LAUNCH_POWER * math.cos(angle_rad)
        sim_vy = -LAUNCH_POWER * math.sin(angle_rad)

        points = [(sim_x, sim_y)]
        for _ in range(60):
            sim_vy += GRAVITY
            sim_x += sim_vx
            sim_y += sim_vy
            points.append((sim_x, sim_y))

            # 检查墙壁碰撞
            if sim_x < PLAY_LEFT or sim_x > PLAY_RIGHT or sim_y > PLAY_BOTTOM:
                break

        # 绘制轨迹点
        for i, (px, py) in enumerate(points):
            if i % 3 == 0:
                alpha = max(0, 255 - i * 4)
                color = (255, 255, 200, alpha)
                surf = pygame.Surface((4, 4), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (2, 2), 2)
                self.screen.blit(surf, (px - 2, py - 2))

    def draw(self):
        """绘制整个画面"""
        self.screen.fill(COLORS["bg"])

        # 绘制墙壁
        self.draw_walls()

        # 绘制钉子
        for peg in self.pegs:
            peg.draw(self.screen)

        # 绘制底部（发射区域标识）
        pygame.draw.rect(self.screen, (30, 30, 50),
                        (PLAY_LEFT, PLAY_BOTTOM - 80,
                         PLAY_RIGHT - PLAY_LEFT, 80))

        # 绘制轨迹预览
        self.draw_trajectory_preview()

        # 绘制发射器
        self.draw_launcher()

        # 绘制球
        if self.ball.active or self.game_state == "aiming":
            # 发光
            glow_surf = pygame.Surface((BALL_RADIUS * 6, BALL_RADIUS * 6), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 255, 100, 60),
                             (BALL_RADIUS * 3, BALL_RADIUS * 3), BALL_RADIUS * 2.5)
            self.screen.blit(glow_surf,
                           (self.ball.x - BALL_RADIUS * 3, self.ball.y - BALL_RADIUS * 3))
            # 球体
            pygame.draw.circle(self.screen, COLORS["ball"],
                             (int(self.ball.x), int(self.ball.y)), BALL_RADIUS)
            pygame.draw.circle(self.screen, COLORS["ball_glow"],
                             (int(self.ball.x - 2), int(self.ball.y - 2)), BALL_RADIUS // 2)

        # 绘制粒子
        for p in self.particles:
            alpha = int(255 * (p["life"] / 30))
            color = (*p["color"][:3], alpha)
            surf = pygame.Surface((int(p["size"] * 2), int(p["size"] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, color,
                             (int(p["size"]), int(p["size"])), int(p["size"]))
            self.screen.blit(surf, (int(p["x"] - p["size"]), int(p["y"] - p["size"])))

        # HUD
        self.draw_hud()

        # 提示信息
        if self.game_state == "aiming":
            hint = self.font_small.render("点击鼠标发射", True, COLORS["gray"])
            self.screen.blit(hint, (SCREEN_WIDTH // 2 - 50, PLAY_BOTTOM - 30))

        elif self.game_state == "game_over":
            self.draw_game_over()
        elif self.game_state == "win":
            self.draw_win()

        pygame.display.flip()

    def run(self):
        """主游戏循环"""
        running = True
        while running:
            running = self.handle_events()
            if not running:
                break
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


def main():
    """入口函数"""
    game = PeggleGame()
    game.run()


if __name__ == "__main__":
    main()