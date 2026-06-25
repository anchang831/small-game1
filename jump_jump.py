"""
跳一跳 (Jump Jump) - 微信跳一跳风格小游戏
玩法: 按住鼠标左键/空格键蓄力，松开跳跃到下一个平台
按 R 键重新开始，ESC 退出

作者: AI Game Generator
日期: 2026-06-25
"""

import pygame
import random
import math
import sys

# ==================== 常量设置 ====================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
DARK_GRAY = (80, 80, 80)
PLATFORM_COLOR = (70, 180, 70)
PLATFORM_BORDER = (40, 140, 40)
PLAYER_COLOR = (100, 150, 255)
PLAYER_BORDER = (50, 100, 200)
CURRENT_PLATFORM_COLOR = (255, 200, 50)
CURRENT_PLATFORM_BORDER = (200, 150, 0)
BG_COLOR = (240, 248, 255)


class Platform:
    """平台类 - 玩家跳跃的目标"""

    def __init__(self, x, y, width=100):
        self.x = x
        self.y = y
        self.width = width
        self.height = 22
        self.is_current = False  # 是否为玩家当前所在平台

    def draw(self, screen, camera_x, camera_y):
        """绘制平台"""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y

        # 跳过屏幕外的平台
        if screen_x + self.width < -50 or screen_x > SCREEN_WIDTH + 50:
            return
        if screen_y + self.height < -50 or screen_y > SCREEN_HEIGHT + 50:
            return

        rect = pygame.Rect(int(screen_x), int(screen_y),
                           int(self.width), int(self.height))

        if self.is_current:
            color = CURRENT_PLATFORM_COLOR
            border = CURRENT_PLATFORM_BORDER
        else:
            color = PLATFORM_COLOR
            border = PLATFORM_BORDER

        # 绘制圆角矩形（简化版：矩形 + 圆角效果）
        pygame.draw.rect(screen, color, rect, border_radius=6)
        pygame.draw.rect(screen, border, rect, 3, border_radius=6)

        # 平台顶部高光
        highlight = pygame.Rect(int(screen_x) + 6, int(screen_y) + 2,
                                int(self.width) - 12, 6)
        pygame.draw.rect(screen, (min(color[0] + 60, 255),
                                  min(color[1] + 60, 255),
                                  min(color[2] + 60, 255)),
                         highlight, border_radius=3)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def get_center_x(self):
        return self.x + self.width / 2


class Player:
    """玩家角色"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 28  # 边长
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = True
        self.landing_scale = 1.0  # 落地压扁动画

    def update(self):
        """更新物理状态"""
        self.x += self.vel_x
        self.y += self.vel_y
        if not self.on_ground:
            self.vel_y += 0.6  # 重力

        # 恢复压扁动画
        if self.landing_scale < 1.0:
            self.landing_scale += 0.05
            if self.landing_scale > 1.0:
                self.landing_scale = 1.0

    def draw(self, screen, camera_x, camera_y):
        """绘制玩家"""
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y

        # 压扁效果
        w = self.size * (2.0 - self.landing_scale)
        h = self.size * self.landing_scale
        rect = pygame.Rect(int(screen_x - (w - self.size) / 2),
                           int(screen_y - (h - self.size) / 2),
                           int(w), int(h))

        # 绘制玩家（方块 + 小圆眼睛）
        pygame.draw.rect(screen, PLAYER_COLOR, rect, border_radius=5)
        pygame.draw.rect(screen, PLAYER_BORDER, rect, 3, border_radius=5)

        # 眼睛
        eye_size = 4
        eye_y = rect.y + rect.h * 0.3
        # 左眼
        pygame.draw.circle(screen, WHITE,
                           (rect.x + rect.w * 0.3, eye_y), eye_size + 1)
        pygame.draw.circle(screen, BLACK,
                           (rect.x + rect.w * 0.3, eye_y), eye_size)
        # 右眼
        pygame.draw.circle(screen, WHITE,
                           (rect.x + rect.w * 0.7, eye_y), eye_size + 1)
        pygame.draw.circle(screen, BLACK,
                           (rect.x + rect.w * 0.7, eye_y), eye_size)

    def get_rect(self):
        return pygame.Rect(self.x - self.size / 2,
                           self.y - self.size / 2,
                           self.size, self.size)

    def jump(self, power):
        """蓄力跳跃，power 范围 0.0 ~ 1.0"""
        # 抛物线角度：约 60~75 度（越蓄力角度越平）
        angle = math.radians(75 - power * 20)
        speed = 6 + power * 18  # 速度范围 6~24
        self.vel_x = speed * math.cos(angle)
        self.vel_y = -speed * math.sin(angle)  # 向上为负
        self.on_ground = False

    def land(self):
        """着陆"""
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = True
        self.landing_scale = 0.7  # 压扁


class Game:
    """游戏主控制器"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("跳一跳 - Jump Jump 🎮")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("simhei, Microsoft YaHei, notosans", 42)
        self.font_medium = pygame.font.SysFont("simhei, Microsoft YaHei, notosans", 28)
        self.font_small = pygame.font.SysFont("simhei, Microsoft YaHei, notosans", 20)

        self.best_score = 0
        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        self.platforms = []
        self.player = None
        self.camera_x = 0
        self.camera_y = 0

        self.score = 0
        self.state = "ready"  # ready | charging | jumping | game_over

        self.charge_power = 0
        self.charging = False
        self.current_platform_index = 0

        # 生成初始平台
        self._generate_initial_platforms()

    def _generate_initial_platforms(self):
        """生成初始平台序列"""
        # 起始平台
        start_x = 150
        start_y = SCREEN_HEIGHT - 250
        p0 = Platform(start_x, start_y, 150)
        p0.is_current = True
        self.platforms.append(p0)

        # 后续平台
        for i in range(6):
            self._add_new_platform()

        # 玩家站在起始平台中间靠右
        self.player = Player(
            p0.x + p0.width * 0.65,
            p0.y - 14    # 站在平台表面（减去半高）
        )

        # 相机初始位置
        self.camera_x = 0
        self.camera_y = 0

    def _add_new_platform(self):
        """在末尾添加一个新平台"""
        last = self.platforms[-1]
        # 随机间隔和偏移
        dx = random.randint(140, 320)
        dy = random.randint(-120, 40)  # 上下浮动
        w = random.randint(70, 150)

        new_x = last.x + last.width + dx
        new_y = max(100, min(SCREEN_HEIGHT - 100, last.y + dy))

        self.platforms.append(Platform(new_x, new_y, w))

    def _cleanup_platforms(self):
        """移除屏幕后方太远的平台"""
        if self.player:
            cutoff = self.player.x - SCREEN_WIDTH
            self.platforms = [p for p in self.platforms
                              if p.x + p.width > cutoff]

    def handle_events(self):
        """处理输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_r and self.state == "game_over":
                    self.reset_game()
                elif event.key == pygame.K_SPACE:
                    if self.state == "ready":
                        self._start_charge()
                    elif self.state == "game_over":
                        self.reset_game()

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE and self.state == "charging":
                    self._release_charge()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    if self.state == "ready":
                        self._start_charge()
                    elif self.state == "game_over":
                        self.reset_game()

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.state == "charging":
                    self._release_charge()

        # 鼠标按住蓄力
        if self.charging and self.state == "charging":
            self.charge_power += 0.025
            if self.charge_power > 1.0:
                self.charge_power = 1.0

        return True

    def _start_charge(self):
        """开始蓄力"""
        self.state = "charging"
        self.charging = True
        self.charge_power = 0

    def _release_charge(self):
        """释放蓄力，执行跳跃"""
        self.charging = False
        power = self.charge_power
        self.player.jump(power)
        self.state = "jumping"
        # 取消当前平台的标记
        if self.current_platform_index < len(self.platforms):
            self.platforms[self.current_platform_index].is_current = False

    def update(self):
        """更新游戏逻辑"""
        if self.state != "jumping":
            return

        self.player.update()

        # 检查是否落在平台上
        if self.player.vel_y >= 0:  # 下落过程中
            player_rect = self.player.get_rect()

            for i, platform in enumerate(self.platforms):
                plat_rect = platform.get_rect()
                # 检测碰撞：玩家底部进入平台范围
                overlap_x = (player_rect.x < plat_rect.x + plat_rect.w and
                             player_rect.x + player_rect.w > plat_rect.x)
                if overlap_x:
                    player_bottom = player_rect.y + player_rect.h
                    plat_top = plat_rect.y
                    # 玩家底部与平台顶部足够接近
                    if (player_bottom >= plat_top and
                        player_bottom <= plat_top + 20 and
                        player_rect.y < plat_top):

                        self.player.y = plat_top - self.player.size / 2
                        self.player.land()
                        self.state = "ready"

                        # 更新当前平台
                        self.current_platform_index = i
                        platform.is_current = True

                        # 计分
                        if i > 0:
                            self.score += 1
                            if self.score > self.best_score:
                                self.best_score = self.score

                        # 平台补给
                        while len(self.platforms) < 8:
                            self._add_new_platform()

                        # 清理远处平台
                        self._cleanup_platforms()
                        return

        # 检查是否掉落
        if self.player.y > self.camera_y + SCREEN_HEIGHT + 200:
            self.state = "game_over"

    def update_camera(self):
        """更新相机位置，平滑跟随"""
        if self.player:
            target_x = self.player.x - SCREEN_WIDTH * 0.35
            target_y = self.player.y - SCREEN_HEIGHT * 0.45
            self.camera_x += (target_x - self.camera_x) * 0.08
            self.camera_y += (target_y - self.camera_y) * 0.08

    def draw(self):
        """渲染画面"""
        self.screen.fill(BG_COLOR)

        # 绘制背景格子装饰
        self._draw_background()

        # 绘制平台
        for platform in self.platforms:
            platform.draw(self.screen, self.camera_x, self.camera_y)

        # 绘制玩家
        if self.player:
            self.player.draw(self.screen, self.camera_x, self.camera_y)

        # 绘制蓄力条
        if self.charging and self.state == "charging":
            self._draw_charge_bar()

        # 绘制UI
        self._draw_ui()

        # 游戏结束画面
        if self.state == "game_over":
            self._draw_game_over()

        # 初始提示
        if self.state == "ready" and self.score == 0:
            self._draw_instruction()

        pygame.display.flip()

    def _draw_background(self):
        """绘制背景网格装饰"""
        grid_size = 60
        offset_x = -self.camera_x % grid_size
        offset_y = -self.camera_y % grid_size

        for x in range(-grid_size, SCREEN_WIDTH + grid_size, grid_size):
            for y in range(-grid_size, SCREEN_HEIGHT + grid_size, grid_size):
                px = x + offset_x
                py = y + offset_y
                pygame.draw.circle(self.screen, (220, 230, 240),
                                   (int(px), int(py)), 2)

    def _draw_charge_bar(self):
        """绘制蓄力条"""
        bar_w = 220
        bar_h = 18
        bar_x = (SCREEN_WIDTH - bar_w) // 2
        bar_y = SCREEN_HEIGHT - 80

        # 背景
        pygame.draw.rect(self.screen, (200, 200, 200),
                         (bar_x, bar_y, bar_w, bar_h), border_radius=9)
        # 填充
        fill = int(bar_w * self.charge_power)
        # 颜色从绿到黄到红渐变
        r = int(255 * self.charge_power)
        g = int(255 * (1 - self.charge_power))
        color = (r, g, 50)
        if fill > 0:
            pygame.draw.rect(self.screen, color,
                             (bar_x, bar_y, fill, bar_h), border_radius=9)
        # 边框
        pygame.draw.rect(self.screen, DARK_GRAY,
                         (bar_x, bar_y, bar_w, bar_h), 2, border_radius=9)

        # 文字
        power_text = self.font_small.render(
            f"蓄力: {int(self.charge_power * 100)}%", True, DARK_GRAY)
        self.screen.blit(power_text,
                         (bar_x + bar_w // 2 - power_text.get_width() // 2,
                          bar_y - 25))

    def _draw_ui(self):
        """绘制UI信息"""
        # 当前得分
        score_surf = self.font_large.render(f"{self.score}", True, BLACK)
        self.screen.blit(score_surf, (25, 15))

        # 得分标签
        label = self.font_small.render("得分", True, DARK_GRAY)
        self.screen.blit(label, (25, 60))

        # 最高分
        best_surf = self.font_medium.render(
            f"最高: {self.best_score}", True, DARK_GRAY)
        self.screen.blit(best_surf, (25, 90))

    def _draw_instruction(self):
        """绘制操作提示"""
        texts = [
            "按住 空格/鼠标左键 蓄力",
            "松开跳跃到下一个平台",
            "按 R 键重新开始"
        ]
        y_offset = SCREEN_HEIGHT - 40
        for text in reversed(texts):
            surf = self.font_small.render(text, True, (150, 150, 150))
            x = (SCREEN_WIDTH - surf.get_width()) // 2
            self.screen.blit(surf, (x, y_offset))
            y_offset -= 25

    def _draw_game_over(self):
        """绘制游戏结束画面"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # 游戏结束文字
        go_text = self.font_large.render("游戏结束", True, WHITE)
        self.screen.blit(go_text,
                         (SCREEN_WIDTH // 2 - go_text.get_width() // 2,
                          SCREEN_HEIGHT // 2 - 100))

        # 最终得分
        final_score = self.font_large.render(
            f"得分: {self.score}", True, (255, 220, 50))
        self.screen.blit(final_score,
                         (SCREEN_WIDTH // 2 - final_score.get_width() // 2,
                          SCREEN_HEIGHT // 2 - 35))

        # 最高分
        best = self.font_medium.render(
            f"最高记录: {self.best_score}", True, (200, 200, 200))
        self.screen.blit(best,
                         (SCREEN_WIDTH // 2 - best.get_width() // 2,
                          SCREEN_HEIGHT // 2 + 20))

        # 重新开始提示
        restart = self.font_medium.render(
            "按 空格/回车/R 重新开始", True, WHITE)
        self.screen.blit(restart,
                         (SCREEN_WIDTH // 2 - restart.get_width() // 2,
                          SCREEN_HEIGHT // 2 + 80))

    def run(self):
        """游戏主循环"""
        running = True
        while running:
            self.clock.tick(FPS)
            running = self.handle_events()
            self.update()
            self.update_camera()
            self.draw()

        pygame.quit()
        sys.exit()


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()