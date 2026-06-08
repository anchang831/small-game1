#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
涂鸦跳跃 (Doodle Jump) - 经典竖直弹跳游戏
===========================================
控制角色不断向上跳跃, 踩中平台即可继续上升。
左右方向键控制移动, 掉落屏幕底部则游戏结束。

操作: ← → 移动, R 重新开始, ESC/关闭窗口退出
"""

import pygame
import random
import sys

# ======================== 游戏配置 ========================
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 650
FPS = 60

# 颜色 (RGB)
COLOR_BG = (220, 240, 255)          # 淡蓝色天空
COLOR_PLATFORM = (80, 180, 80)      # 绿色平台
COLOR_PLATFORM_BREAK = (220, 100, 80)  # 红色(破碎平台)
COLOR_PLATFORM_MOVE = (80, 130, 220)   # 蓝色(移动平台)
COLOR_PLAYER = (240, 180, 50)       # 橙色角色
COLOR_PLAYER_EYE = (50, 50, 50)     # 眼睛
COLOR_TEXT = (30, 30, 30)
COLOR_SCORE = (60, 60, 60)
COLOR_GAMEOVER = (200, 50, 50)

# 物理参数
GRAVITY = 0.45
JUMP_VELOCITY = -11.5              # 踩到平台时的向上速度
MOVE_SPEED = 5.5
PLAYER_WIDTH = 28
PLAYER_HEIGHT = 32

# 平台参数
PLATFORM_WIDTH = 62
PLATFORM_HEIGHT = 14
PLATFORM_MIN_GAP = 55              # 平台最小垂直间距
PLATFORM_MAX_GAP = 85              # 平台最大垂直间距
BREAK_PLATFORM_CHANCE = 0.18       # 破碎平台概率
MOVE_PLATFORM_CHANCE = 0.15        # 移动平台概率
MAX_PLATFORMS = 16                 # 屏幕上最大平台数量

# 窗口标题
pygame.display.set_caption("涂鸦跳跃 Doodle Jump")


class Player:
    """玩家角色类"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.vel_x = 0
        self.vel_y = 0
        self.on_platform = False
        # 左右朝向 (1=右, -1=左)
        self.direction = 1

    def move_left(self):
        """向左移动"""
        self.vel_x = -MOVE_SPEED
        self.direction = -1

    def move_right(self):
        """向右移动"""
        self.vel_x = MOVE_SPEED
        self.direction = 1

    def stop(self):
        """停止水平移动"""
        self.vel_x = 0

    def update(self):
        """更新角色物理状态"""
        self.vel_y += GRAVITY
        self.x += self.vel_x
        self.y += self.vel_y

        # 左右边界环绕
        if self.x < -self.width // 2:
            self.x = WINDOW_WIDTH - self.width // 2
        elif self.x > WINDOW_WIDTH - self.width // 2:
            self.x = -self.width // 2

    def jump(self):
        """跳跃"""
        self.vel_y = JUMP_VELOCITY
        self.on_platform = False

    def get_rect(self):
        """获取碰撞矩形"""
        return pygame.Rect(
            int(self.x), int(self.y),
            self.width, self.height
        )

    def draw(self, surface):
        """绘制角色 — 简单涂鸦小人风格"""
        rect = self.get_rect()

        # 身体 (椭圆)
        body_rect = pygame.Rect(
            rect.x + 2, rect.y + 8,
            rect.width - 4, rect.height - 10
        )
        pygame.draw.ellipse(surface, COLOR_PLAYER, body_rect)

        # 头部 (圆形)
        head_center = (rect.centerx, rect.y + 6)
        head_radius = 8
        pygame.draw.circle(surface, COLOR_PLAYER, head_center, head_radius)

        # 眼睛
        eye_offset_x = 4 * self.direction
        eye_y = rect.y + 5
        pygame.draw.circle(surface, COLOR_PLAYER_EYE,
                          (rect.centerx + eye_offset_x - 2, eye_y), 2)
        pygame.draw.circle(surface, COLOR_PLAYER_EYE,
                          (rect.centerx + eye_offset_x + 2, eye_y), 2)

        # 腿 (两条线)
        leg_start = (rect.centerx, rect.bottom - 4)
        leg_end1 = (rect.centerx - 5, rect.bottom)
        leg_end2 = (rect.centerx + 5, rect.bottom)
        pygame.draw.line(surface, COLOR_PLAYER, leg_start, leg_end1, 2)
        pygame.draw.line(surface, COLOR_PLAYER, leg_start, leg_end2, 2)


class Platform:
    """平台类"""

    def __init__(self, x, y, ptype="normal"):
        self.x = x
        self.y = y
        self.width = PLATFORM_WIDTH
        self.height = PLATFORM_HEIGHT
        self.type = ptype  # "normal", "break", "move"
        self.broken = False
        self.move_dir = 1
        self.move_speed = 1.8
        self.move_range = 80
        self.orig_x = x

        # 破碎平台动画计时
        self.break_timer = 0

    def get_rect(self):
        return pygame.Rect(
            int(self.x), int(self.y),
            self.width, self.height
        )

    def update(self):
        """更新平台状态 (移动平台)"""
        if self.type == "move" and not self.broken:
            self.x += self.move_speed * self.move_dir
            if abs(self.x - self.orig_x) > self.move_range:
                self.move_dir *= -1

    def draw(self, surface):
        """绘制平台"""
        if self.broken:
            return  # 破碎后不再绘制

        rect = self.get_rect()

        if self.type == "normal":
            color = COLOR_PLATFORM
        elif self.type == "break":
            color = COLOR_PLATFORM_BREAK
        else:  # move
            color = COLOR_PLATFORM_MOVE

        # 平台主体 (圆角矩形用普通矩形+小圆角效果)
        pygame.draw.rect(surface, color, rect, border_radius=4)

        # 高光线
        highlight = pygame.Rect(rect.x + 4, rect.y + 2, rect.width - 8, 4)
        pygame.draw.rect(surface, (
            min(255, color[0] + 60),
            min(255, color[1] + 60),
            min(255, color[2] + 60)
        ), highlight, border_radius=2)

        # 破碎平台标记 - 裂纹线
        if self.type == "break":
            mid_x = rect.centerx
            mid_y = rect.centery
            pygame.draw.line(surface, (180, 60, 40),
                           (mid_x - 10, mid_y - 2), (mid_x + 10, mid_y + 2), 2)
            pygame.draw.line(surface, (180, 60, 40),
                           (mid_x - 5, mid_y + 2), (mid_x + 5, mid_y - 2), 2)

        # 移动平台标记 - 小箭头
        if self.type == "move":
            pygame.draw.polygon(surface, (40, 80, 180), [
                (rect.centerx, rect.y + 3),
                (rect.centerx - 5, rect.y + 9),
                (rect.centerx + 5, rect.y + 9)
            ])


class Game:
    """游戏主类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("simhei", 48, bold=True)
        self.font_medium = pygame.font.SysFont("simhei", 28)
        self.font_small = pygame.font.SysFont("simhei", 20)

        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        # 玩家初始在中间下方
        self.player = Player(WINDOW_WIDTH // 2 - PLAYER_WIDTH // 2,
                             WINDOW_HEIGHT - 120)
        self.platforms = []
        self.score = 0
        self.high_score = getattr(self, 'high_score', 0)
        self.game_over = False
        self.scroll_y = 0  # 屏幕滚动偏移
        self.max_height = self.player.y  # 记录最高位置

        # 生成初始平台
        self._generate_initial_platforms()

        # 粒子效果列表
        self.particles = []

    def _generate_initial_platforms(self):
        """生成游戏初始的底部平台"""
        # 第一个平台在玩家正下方
        start_x = WINDOW_WIDTH // 2 - PLATFORM_WIDTH // 2
        start_y = self.player.y + PLAYER_HEIGHT + 15
        self.platforms.append(Platform(start_x, start_y, "normal"))

        # 向上生成更多平台
        y = start_y - PLATFORM_MIN_GAP
        while y > 50:
            self._add_random_platform(y)
            y -= random.randint(PLATFORM_MIN_GAP, PLATFORM_MAX_GAP)

    def _add_random_platform(self, y):
        """在指定 y 位置添加随机类型平台"""
        x = random.randint(20, WINDOW_WIDTH - PLATFORM_WIDTH - 20)

        # 避免平台重叠
        for p in self.platforms:
            if abs(p.y - y) < 30 and abs(p.x - x) < PLATFORM_WIDTH + 10:
                x = random.randint(20, WINDOW_WIDTH - PLATFORM_WIDTH - 20)
                break

        rand = random.random()
        if rand < BREAK_PLATFORM_CHANCE:
            ptype = "break"
        elif rand < BREAK_PLATFORM_CHANCE + MOVE_PLATFORM_CHANCE:
            ptype = "move"
        else:
            ptype = "normal"

        self.platforms.append(Platform(x, y, ptype))

    def handle_events(self):
        """处理输入事件"""
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_r and self.game_over:
                    self.reset_game()

        # 游戏进行中处理移动
        if not self.game_over:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.player.move_left()
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.player.move_right()
            else:
                self.player.stop()

            # 如果按住上键可以跳得更高 (小技巧)
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                if self.player.vel_y < -2:
                    self.player.vel_y -= 0.15

        return True

    def update(self):
        """更新游戏逻辑"""
        if self.game_over:
            self._update_particles()
            return

        self.player.update()

        # --- 检测平台碰撞 (仅在向下运动时) ---
        if self.player.vel_y >= 0:
            player_rect = self.player.get_rect()
            for platform in self.platforms:
                if platform.broken:
                    continue

                plat_rect = platform.get_rect()
                # 碰撞检测: 脚踩在平台顶部
                if (player_rect.bottom >= plat_rect.top
                        and player_rect.bottom <= plat_rect.top + 12
                        and player_rect.right - 8 > plat_rect.left
                        and player_rect.left + 8 < plat_rect.right
                        and self.player.vel_y >= 0):

                    # 破碎平台: 踩到后破碎
                    if platform.type == "break":
                        platform.broken = True
                        self._spawn_break_particles(platform)
                        continue

                    # 普通/移动平台: 弹跳
                    self.player.y = plat_rect.top - self.player.height
                    self.player.jump()
                    break

        # --- 更新平台位置 (屏幕滚动) ---
        self._update_scroll()

        # --- 在屏幕上方生成新平台 ---
        self._update_platforms()

        # --- 检测是否掉落死亡 ---
        if self.player.y > WINDOW_HEIGHT + 50:
            self.game_over = True
            if self.score > self.high_score:
                self.high_score = self.score
            self._spawn_death_particles()

        # --- 更新粒子 ---
        self._update_particles()

    def _update_scroll(self):
        """根据玩家位置滚动屏幕"""
        scroll_threshold = WINDOW_HEIGHT * 0.45
        if self.player.y < scroll_threshold:
            diff = scroll_threshold - self.player.y
            self.player.y = scroll_threshold
            self.scroll_y += diff

            # 更新所有平台位置
            for platform in self.platforms:
                platform.y += diff

            # 更新最高分
            current_height = int(self.scroll_y)
            if current_height > self.score:
                self.score = current_height

    def _update_platforms(self):
        """管理平台的生成与移除"""
        # 移除超出屏幕底部的平台
        self.platforms = [p for p in self.platforms
                         if p.y < WINDOW_HEIGHT + 50 and not p.broken]

        # 寻找最低平台的位置
        min_y = min(p.y for p in self.platforms) if self.platforms else 0

        # 在屏幕上方补充平台
        while len(self.platforms) < MAX_PLATFORMS:
            new_y = min_y - random.randint(PLATFORM_MIN_GAP, PLATFORM_MAX_GAP)
            if new_y > -50:
                self._add_random_platform(new_y)
                min_y = new_y
            else:
                break

        # 更新移动平台
        for p in self.platforms:
            p.update()

    def _spawn_break_particles(self, platform):
        """破碎平台产生碎片粒子"""
        rect = platform.get_rect()
        for _ in range(8):
            self.particles.append({
                'x': rect.centerx + random.randint(-20, 20),
                'y': rect.centery + random.randint(-8, 8),
                'vx': random.uniform(-3, 3),
                'vy': random.uniform(-5, -1),
                'size': random.randint(3, 7),
                'color': COLOR_PLATFORM_BREAK,
                'life': 30
            })

    def _spawn_death_particles(self):
        """死亡时产生粒子"""
        rect = self.player.get_rect()
        for _ in range(15):
            self.particles.append({
                'x': rect.centerx + random.randint(-15, 15),
                'y': rect.centery + random.randint(-15, 15),
                'vx': random.uniform(-4, 4),
                'vy': random.uniform(-4, 4),
                'size': random.randint(4, 8),
                'color': COLOR_PLAYER,
                'life': 45
            })

    def _update_particles(self):
        """更新粒子效果"""
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.15
            p['life'] -= 1
            if p['life'] <= 0:
                self.particles.remove(p)

    def draw(self):
        """绘制所有内容"""
        self.screen.fill(COLOR_BG)

        # 绘制背景装饰 - 云朵 (静态装饰)
        self._draw_bg_clouds()

        # 绘制平台
        for platform in self.platforms:
            platform.draw(self.screen)

        # 绘制角色 (如果未死亡或刚死)
        if not self.game_over or self.particles:
            self.player.draw(self.screen)

        # 绘制粒子
        for p in self.particles:
            alpha = min(255, p['life'] * 8)
            color = p['color']
            size = max(1, int(p['size'] * (p['life'] / 30)))
            pygame.draw.circle(
                self.screen, color,
                (int(p['x']), int(p['y'])), size
            )

        # 绘制分数
        score_text = self.font_medium.render(
            f"分数: {self.score}", True, COLOR_SCORE)
        self.screen.blit(score_text, (15, 15))

        # 绘制最高分
        if self.high_score > 0:
            high_text = self.font_small.render(
                f"最高: {self.high_score}", True, COLOR_SCORE)
            self.screen.blit(high_text, (15, 48))

        # 绘制游戏结束画面
        if self.game_over:
            self._draw_game_over()

        # 绘制操作提示
        if self.score < 10 and not self.game_over:
            tip = self.font_small.render("← → 方向键移动", True, (140, 140, 140))
            tip_rect = tip.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 30))
            self.screen.blit(tip, tip_rect)

        pygame.display.flip()

    def _draw_bg_clouds(self):
        """绘制背景云朵装饰"""
        # 简单云朵 - 几个圆形
        clouds_pos = [
            (60, 80, 30), (80, 75, 25), (50, 85, 20),
            (300, 150, 35), (330, 140, 25), (290, 155, 22),
            (150, 200, 28), (180, 195, 20),
            (350, 280, 30), (370, 275, 22),
            (40, 320, 25), (20, 315, 20),
        ]
        for cx, cy, r in clouds_pos:
            # 根据滚动偏移调整云朵位置 (缓慢移动)
            cy_offset = cy - self.scroll_y * 0.05
            while cy_offset < -50:
                cy_offset += 600
            while cy_offset > 650:
                cy_offset -= 600
            pygame.draw.circle(self.screen, (255, 255, 255, 180),
                             (cx, int(cy_offset)), r)
            pygame.draw.circle(self.screen, (255, 255, 255, 180),
                             (cx + r // 2, int(cy_offset - r // 3)), r - 5)

    def _draw_game_over(self):
        """绘制游戏结束界面"""
        # 半透明遮罩
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Game Over 标题
        title = self.font_large.render("游戏结束", True, COLOR_GAMEOVER)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60))
        self.screen.blit(title, title_rect)

        # 分数
        score_text = self.font_medium.render(
            f"得分: {self.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.screen.blit(score_text, score_rect)

        # 最高分
        high_text = self.font_medium.render(
            f"最高分: {self.high_score}", True, (255, 220, 80))
        high_rect = high_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40))
        self.screen.blit(high_text, high_rect)

        # 重新开始提示
        restart_text = self.font_small.render(
            "按 R 重新开始", True, (200, 200, 200))
        restart_rect = restart_text.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 90))
        self.screen.blit(restart_text, restart_rect)

    def run(self):
        """游戏主循环"""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ======================== 入口 ========================
if __name__ == "__main__":
    game = Game()
    game.run()