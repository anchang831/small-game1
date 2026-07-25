"""
Bubble Trouble (泡泡大作战)
======================
经典街机游戏：玩家在底部左右移动，发射子弹击碎弹跳的泡泡。
泡泡被击中会分裂成更小的泡泡，直到彻底消失。
避免被任何泡泡碰到，坚持越久得分越高！

操作方式：
  - 方向键 ← → 或 A/D 移动
  - 空格键 发射子弹
  - 支持键盘连发

作者: AI Game Generator
日期: 2026-07-25
"""

import pygame
import math
import random
import sys

# ==================== 游戏配置 ====================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 颜色定义 (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 130, 255)
YELLOW = (255, 255, 80)
ORANGE = (255, 165, 0)
PURPLE = (180, 80, 255)
CYAN = (0, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (30, 30, 30)

# 泡泡颜色池
BUBBLE_COLORS = [RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE, CYAN]

# 泡泡大小等级 (半径)
BUBBLE_SIZES = [
    {"radius": 40, "speed": 1.8, "score": 10, "label": "大"},
    {"radius": 25, "speed": 2.8, "score": 20, "label": "中"},
    {"radius": 14, "speed": 4.0, "score": 40, "label": "小"},
]

# 玩家配置
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 20
PLAYER_SPEED = 6
PLAYER_LIVES = 3

# 子弹配置
BULLET_SPEED = 12
BULLET_WIDTH = 4
BULLET_HEIGHT = 14
MAX_BULLETS = 5  # 同时最多子弹数


class Bubble:
    """泡泡类 - 在屏幕内弹跳，可被击碎分裂"""

    def __init__(self, x, y, size_index):
        """
        size_index: 0=大, 1=中, 2=小
        """
        self.size_index = size_index
        config = BUBBLE_SIZES[size_index]
        self.radius = config["radius"]
        self.speed = config["speed"]
        self.score = config["score"]

        # 随机生成颜色
        self.color = random.choice(BUBBLE_COLORS)

        # 随机初始移动方向 (角度)
        angle = random.uniform(0.2, math.pi - 0.2)  # 避免完全水平
        self.vx = math.cos(angle) * self.speed
        self.vy = math.sin(angle) * self.speed
        # 保证向下弹
        if self.vy < 0.5:
            self.vy = 0.5

        self.x = x
        self.y = y

        # 闪光效果
        self.glow_offset = random.uniform(0, math.pi * 2)

    def update(self):
        """更新位置，处理边界反弹"""
        self.x += self.vx
        self.y += self.vy

        # 左右边界反弹
        if self.x - self.radius <= 0:
            self.x = self.radius
            self.vx = abs(self.vx)
        elif self.x + self.radius >= SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.vx = -abs(self.vx)

        # 上边界反弹 (不反弹下边界，防止无限弹跳)
        if self.y - self.radius <= 0:
            self.y = self.radius
            self.vy = abs(self.vy)

        # 下边界反弹 (防止掉出屏幕)
        if self.y + self.radius >= SCREEN_HEIGHT - 40:
            self.y = SCREEN_HEIGHT - 40 - self.radius
            self.vy = -abs(self.vy)

        # 更新闪光效果
        self.glow_offset += 0.05

    def draw(self, surface):
        """绘制泡泡，带光泽效果"""
        # 外发光
        glow_radius = self.radius + 4
        glow_alpha = 40
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        glow_color = (*self.color[:3], glow_alpha)
        pygame.draw.circle(glow_surf, glow_color,
                          (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surf, (self.x - glow_radius, self.y - glow_radius))

        # 主体
        pygame.draw.circle(surface, self.color,
                          (int(self.x), int(self.y)), self.radius)

        # 高光 (左上角的光泽)
        highlight_x = self.x - self.radius * 0.25
        highlight_y = self.y - self.radius * 0.25
        highlight_radius = self.radius * 0.4
        highlight_color = (255, 255, 255, 60)
        highlight_surf = pygame.Surface(
            (highlight_radius * 2, highlight_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(highlight_surf, highlight_color,
                          (highlight_radius, highlight_radius), highlight_radius)
        surface.blit(highlight_surf,
                    (highlight_x - highlight_radius, highlight_y - highlight_radius))

        # 大小标签
        label = BUBBLE_SIZES[self.size_index]["label"]
        font = pygame.font.SysFont("simhei", 14)
        label_surf = font.render(label, True, WHITE)
        label_rect = label_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(label_surf, label_rect)

    def get_rect(self):
        """获取碰撞矩形"""
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                          self.radius * 2, self.radius * 2)


class Player:
    """玩家类 - 底部移动的炮台"""

    def __init__(self):
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT - 50
        self.speed = PLAYER_SPEED
        self.lives = PLAYER_LIVES
        self.invincible_timer = 0  # 受伤后无敌时间
        self.blink_timer = 0

    def update(self, keys):
        """处理玩家移动"""
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            self.blink_timer += 1

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed

        # 限制在屏幕内
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))

    def draw(self, surface):
        """绘制玩家 (炮台造型)"""
        # 无敌闪烁效果
        if self.invincible_timer > 0 and (self.blink_timer // 6) % 2 == 0:
            return

        cx = self.x + self.width // 2
        cy = self.y + self.height // 2

        # 底座
        base_color = (100, 200, 255)
        pygame.draw.rect(surface, base_color,
                        (self.x, self.y, self.width, self.height),
                        border_radius=4)

        # 炮管
        pygame.draw.rect(surface, (200, 220, 255),
                        (cx - 4, self.y - 12, 8, 16),
                        border_radius=2)

        # 炮口
        pygame.draw.circle(surface, (255, 100, 100),
                          (cx, self.y - 14), 5)

        # 装饰线条
        pygame.draw.line(surface, (50, 100, 150),
                        (self.x + 5, cy), (self.x + self.width - 5, cy), 2)

    def get_rect(self):
        """获取碰撞矩形"""
        return pygame.Rect(self.x, self.y - 12, self.width, self.height + 12)

    def hit(self):
        """玩家被击中"""
        if self.invincible_timer > 0:
            return False
        self.lives -= 1
        self.invincible_timer = 90  # 1.5秒无敌
        self.blink_timer = 0
        return True


class Bullet:
    """子弹类 - 向上飞行"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = BULLET_SPEED
        self.width = BULLET_WIDTH
        self.height = BULLET_HEIGHT
        self.active = True

    def update(self):
        """更新子弹位置"""
        self.y -= self.speed
        if self.y < -self.height:
            self.active = False

    def draw(self, surface):
        """绘制子弹 (发光弹头)"""
        # 拖尾效果
        for i in range(3):
            alpha = 100 - i * 30
            trail_surf = pygame.Surface((self.width + 2, self.height + 2),
                                        pygame.SRCALPHA)
            pygame.draw.rect(trail_surf, (255, 255, 100, alpha),
                            (0, i * 3, self.width, self.height - i * 3),
                            border_radius=2)
            surface.blit(trail_surf, (self.x - 1, self.y + i * 3))

        # 子弹主体
        pygame.draw.rect(surface, (255, 255, 200),
                        (self.x, self.y, self.width, self.height),
                        border_radius=2)
        # 高光
        pygame.draw.rect(surface, (255, 255, 255),
                        (self.x + 1, self.y + 1, self.width - 2, self.height // 2),
                        border_radius=1)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


class Particle:
    """粒子特效类"""

    def __init__(self, x, y, color, count=15):
        self.particles = []
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8)
            self.particles.append({
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": random.randint(15, 35),
                "max_life": 35,
                "radius": random.uniform(2, 5),
                "color": color,
            })

    def update(self):
        """更新粒子状态"""
        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.15  # 重力
            p["life"] -= 1
            if p["life"] <= 0:
                self.particles.remove(p)

    def draw(self, surface):
        """绘制粒子"""
        for p in self.particles:
            alpha = int(255 * (p["life"] / p["max_life"]))
            color = (*p["color"][:3], alpha)
            particle_surf = pygame.Surface(
                (int(p["radius"] * 2), int(p["radius"] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, color,
                              (int(p["radius"]), int(p["radius"])),
                              int(p["radius"]))
            surface.blit(particle_surf,
                        (int(p["x"] - p["radius"]), int(p["y"] - p["radius"])))

    def is_dead(self):
        return len(self.particles) == 0


class Game:
    """游戏主类"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Bubble Trouble - 泡泡大作战")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("simhei", 48)
        self.font_medium = pygame.font.SysFont("simhei", 28)
        self.font_small = pygame.font.SysFont("simhei", 18)

        # 尝试加载音效 (如果没有则跳过)
        self.sound_shoot = None
        self.sound_pop = None
        self.sound_hit = None
        try:
            pygame.mixer.init()
            self.sound_shoot = self._create_sound_shoot()
            self.sound_pop = self._create_sound_pop()
            self.sound_hit = self._create_sound_hit()
        except Exception:
            pass

        self.reset_game()

    def _create_sound_shoot(self):
        """生成射击音效"""
        duration = 0.08
        sample_rate = 22050
        samples = int(duration * sample_rate)
        sound = pygame.mixer.Sound(buffer=bytes(
            [int(127 * math.sin(2 * math.pi * 800 * t / sample_rate) *
                 max(0, 1 - t / (duration * sample_rate)))
             for t in range(samples) for _ in range(2)])
        )
        return sound

    def _create_sound_pop(self):
        """生成泡泡破裂音效"""
        duration = 0.15
        sample_rate = 22050
        samples = int(duration * sample_rate)
        sound = pygame.mixer.Sound(buffer=bytes(
            [int(127 * math.sin(2 * math.pi * 400 * t / sample_rate) *
                 math.exp(-3 * t / sample_rate) *
                 (1 - t / (duration * sample_rate)))
             for t in range(samples) for _ in range(2)])
        )
        return sound

    def _create_sound_hit(self):
        """生成受伤音效"""
        duration = 0.2
        sample_rate = 22050
        samples = int(duration * sample_rate)
        sound = pygame.mixer.Sound(buffer=bytes(
            [int(127 * math.sin(2 * math.pi * 200 * t / sample_rate) *
                 math.sin(2 * math.pi * 3 * t / sample_rate) *
                 max(0, 1 - t / (duration * sample_rate)))
             for t in range(samples) for _ in range(2)])
        )
        return sound

    def reset_game(self):
        """重置游戏状态"""
        self.player = Player()
        self.bubbles = []
        self.bullets = []
        self.particles = []
        self.score = 0
        self.level = 1
        self.game_over = False
        self.win = False
        self.state = "playing"  # playing, game_over, win
        self.shoot_cooldown = 0
        self.combo = 0
        self.combo_timer = 0

        # 初始生成大泡泡
        self._spawn_initial_bubbles()

    def _spawn_initial_bubbles(self):
        """生成初始泡泡"""
        count = 3 + self.level
        for _ in range(count):
            x = random.randint(80, SCREEN_WIDTH - 80)
            y = random.randint(60, SCREEN_HEIGHT // 2)
            self.bubbles.append(Bubble(x, y, 0))

    def _spawn_particles(self, x, y, color):
        """生成粒子特效"""
        self.particles.append(Particle(x, y, color, count=20))

    def handle_events(self):
        """处理输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.state == "playing":
                        self._shoot()
                    elif self.state in ("game_over", "win"):
                        # 重新开始
                        if event.key == pygame.K_r:
                            self.reset_game()

                if event.key == pygame.K_r and self.state in ("game_over", "win"):
                    self.reset_game()

                if event.key == pygame.K_ESCAPE:
                    return False

        # 持续按键射击
        if self.state == "playing":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                self._shoot()

        return True

    def _shoot(self):
        """发射子弹"""
        if self.shoot_cooldown > 0:
            return

        # 检查子弹数量上限
        active_bullets = sum(1 for b in self.bullets if b.active)
        if active_bullets >= MAX_BULLETS:
            return

        cx = self.player.x + self.player.width // 2
        bullet = Bullet(cx - BULLET_WIDTH // 2, self.player.y - 20)
        self.bullets.append(bullet)
        self.shoot_cooldown = 12  # 发射间隔

        if self.sound_shoot:
            self.sound_shoot.play()

    def _split_bubble(self, bubble):
        """泡泡分裂: 大→中→小→消失"""
        if bubble.size_index < 2:  # 还可以分裂
            new_size = bubble.size_index + 1
            # 分裂成两个小一号的泡泡，往不同方向
            for offset_x in [-20, 20]:
                new_bubble = Bubble(
                    bubble.x + offset_x,
                    bubble.y,
                    new_size
                )
                # 让分裂后的泡泡向两侧分开
                if offset_x < 0:
                    new_bubble.vx = -abs(new_bubble.vx) * 0.8
                else:
                    new_bubble.vx = abs(new_bubble.vx) * 0.8
                new_bubble.vy = abs(new_bubble.vy) * 0.8
                self.bubbles.append(new_bubble)

    def update(self):
        """更新游戏逻辑"""
        if self.state != "playing":
            return

        keys = pygame.key.get_pressed()
        self.player.update(keys)

        # 冷却递减
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        # 连击计时
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.combo = 0

        # 更新子弹
        for bullet in self.bullets:
            bullet.update()

        # 移除失效子弹
        self.bullets = [b for b in self.bullets if b.active]

        # 更新泡泡
        for bubble in self.bubbles:
            bubble.update()

        # 子弹与泡泡碰撞检测
        for bullet in self.bullets[:]:
            if not bullet.active:
                continue
            bullet_rect = bullet.get_rect()
            for bubble in self.bubbles[:]:
                if bullet_rect.colliderect(bubble.get_rect()):
                    # 命中！
                    bullet.active = False
                    self.bubbles.remove(bubble)

                    # 粒子特效
                    self._spawn_particles(bubble.x, bubble.y, bubble.color)

                    # 音效
                    if self.sound_pop:
                        self.sound_pop.play()

                    # 连击加分
                    self.combo += 1
                    self.combo_timer = 60  # 1秒内连击有效
                    combo_bonus = min(self.combo, 10)
                    self.score += bubble.score * combo_bonus

                    # 分裂泡泡
                    self._split_bubble(bubble)
                    break

        # 泡泡与玩家碰撞检测
        player_rect = self.player.get_rect()
        for bubble in self.bubbles[:]:
            if player_rect.colliderect(bubble.get_rect()):
                if self.player.hit():
                    # 粒子特效
                    self._spawn_particles(bubble.x, bubble.y, RED)
                    if self.sound_hit:
                        self.sound_hit.play()

                    if self.player.lives <= 0:
                        self.state = "game_over"
                        return

        # 更新粒子
        for particle in self.particles[:]:
            particle.update()
            if particle.is_dead():
                self.particles.remove(particle)

        # 检查是否通关 (所有泡泡消失)
        if len(self.bubbles) == 0:
            self.level += 1
            self._spawn_initial_bubbles()

    def draw_hud(self):
        """绘制界面信息"""
        # 分数
        score_text = self.font_medium.render(
            f"分数: {self.score}", True, WHITE)
        self.screen.blit(score_text, (15, 12))

        # 等级
        level_text = self.font_medium.render(
            f"等级: {self.level}", True, CYAN)
        self.screen.blit(level_text, (15, 48))

        # 生命值
        lives_text = self.font_small.render(
            f"生命: {'♥' * self.player.lives}", True, RED)
        self.screen.blit(lives_text, (15, 84))

        # 连击显示
        if self.combo > 1 and self.combo_timer > 0:
            combo_text = self.font_medium.render(
                f"连击 x{self.combo}", True, YELLOW)
            self.screen.blit(combo_text, (SCREEN_WIDTH - 150, 15))

        # 泡泡数量
        bubble_count = self.font_small.render(
            f"泡泡: {len(self.bubbles)}", True, GRAY)
        self.screen.blit(bubble_count, (SCREEN_WIDTH - 120, 50))

        # 操作提示
        hint = self.font_small.render(
            "← → 移动 | 空格 射击", True, GRAY)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - 100, 12))

    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(DARK_GRAY)

        # 背景网格装饰
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(self.screen, (40, 40, 40), (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(self.screen, (40, 40, 40), (0, y), (SCREEN_WIDTH, y), 1)

        if self.state == "playing":
            # 绘制泡泡
            for bubble in self.bubbles:
                bubble.draw(self.screen)

            # 绘制子弹
            for bullet in self.bullets:
                bullet.draw(self.screen)

            # 绘制玩家
            self.player.draw(self.screen)

        elif self.state == "game_over":
            # 游戏结束画面
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(160)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))

            # 依然绘制游戏元素
            for bubble in self.bubbles:
                bubble.draw(self.screen)
            for bullet in self.bullets:
                bullet.draw(self.screen)
            for particle in self.particles:
                particle.draw(self.screen)

            # 游戏结束文字
            go_text = self.font_large.render("GAME OVER", True, RED)
            go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, 220))
            self.screen.blit(go_text, go_rect)

            score_text = self.font_medium.render(
                f"最终得分: {self.score}  |  等级: {self.level}", True, WHITE)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
            self.screen.blit(score_text, score_rect)

            restart_text = self.font_small.render(
                "按 R 重新开始  |  按 ESC 退出", True, GRAY)
            restart_rect = restart_text.get_rect(
                center=(SCREEN_WIDTH // 2, 360))
            self.screen.blit(restart_text, restart_rect)

        # 绘制粒子特效 (始终在最上层)
        for particle in self.particles:
            particle.draw(self.screen)

        # HUD
        self.draw_hud()

        pygame.display.flip()

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


def main():
    """入口函数"""
    print("=" * 50)
    print("  Bubble Trouble - 泡泡大作战")
    print("=" * 50)
    print("  操作说明:")
    print("  - 方向键 ← → 移动炮台")
    print("  - 空格键 发射子弹")
    print("  - 击碎泡泡得分，大泡泡分裂成小泡泡")
    print("  - 避免被泡泡碰到！")
    print("=" * 50)
    game = Game()
    game.run()


if __name__ == "__main__":
    main()