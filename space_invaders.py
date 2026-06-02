"""
太空侵略者 (Space Invaders) — 经典街机射击游戏
控制飞船左右移动，击落入侵的外星人军团！
"""

import pygame
import random
import sys

# ─── 初始化 Pygame ───
pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    # 无音频设备时跳过音频初始化
    pass

# ─── 常量定义 ───
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

# 颜色 (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
PURPLE = (180, 0, 255)
ORANGE = (255, 165, 0)
DARK_GREEN = (0, 180, 0)

# ─── 游戏设置 ───
PLAYER_SPEED = 6
BULLET_SPEED = -9  # 负值表示向上
ALIEN_BULLET_SPEED = 5
ALIEN_COLS = 8
ALIEN_ROWS = 4
ALIEN_H_SPEED = 1.5    # 水平移动速度
ALIEN_DROP_DIST = 20   # 每次下降距离
SHOOT_COOLDOWN = 8     # 外星人射击冷却 (帧数)


# ─── 玩家类 ───
class Player(pygame.sprite.Sprite):
    """玩家飞船"""

    def __init__(self):
        super().__init__()
        # 绘制飞船：一个梯形 + 炮管
        self.image = pygame.Surface((50, 35), pygame.SRCALPHA)
        # 主体
        pygame.draw.rect(self.image, CYAN, (5, 15, 40, 15))       # 机身
        pygame.draw.polygon(self.image, CYAN, [(10, 15), (25, 0), (40, 15)])  # 机头
        pygame.draw.rect(self.image, CYAN, (22, 0, 6, 10))        # 炮管
        # 侧翼
        pygame.draw.polygon(self.image, CYAN, [(0, 25), (5, 15), (5, 30)])
        pygame.draw.polygon(self.image, CYAN, [(50, 25), (45, 15), (45, 30)])

        self.rect = self.image.get_rect()
        self.rect.midbottom = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20)
        self.speed = PLAYER_SPEED
        self.lives = 3
        self.invincible = 0  # 无敌帧计数

    def update(self):
        """处理输入并更新位置"""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 5:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH - 5:
            self.rect.x += self.speed

        # 无敌闪烁效果
        if self.invincible > 0:
            self.invincible -= 1
            self.image.set_alpha(128 if (self.invincible // 4) % 2 else 255)
        else:
            self.image.set_alpha(255)

    def shoot(self, group):
        """发射子弹"""
        bullet = Bullet(self.rect.centerx, self.rect.top)
        group.add(bullet)

    def hit(self):
        """被击中"""
        if self.invincible <= 0:
            self.lives -= 1
            self.invincible = 90  # 1.5 秒无敌
            return True
        return False


# ─── 玩家子弹类 ───
class Bullet(pygame.sprite.Sprite):
    """玩家发射的子弹"""

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((4, 15))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x, y)

    def update(self):
        self.rect.y += BULLET_SPEED
        if self.rect.bottom < 0:
            self.kill()


# ─── 外星人类 ───
class Alien(pygame.sprite.Sprite):
    """外星入侵者"""

    def __init__(self, x, y, row):
        super().__init__()
        size = 30
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)

        # 不同行的外星人颜色不同
        colors = [PURPLE, RED, ORANGE, GREEN]
        color = colors[row % len(colors)]

        # 绘制外星人造型
        body_color = color
        # 身体
        pygame.draw.ellipse(self.image, body_color, (3, 8, size - 6, size - 10))
        # 头部
        pygame.draw.circle(self.image, body_color, (size // 2, 10), 8)
        # 眼睛
        pygame.draw.circle(self.image, WHITE, (size // 2 - 5, 8), 3)
        pygame.draw.circle(self.image, WHITE, (size // 2 + 5, 8), 3)
        pygame.draw.circle(self.image, BLACK, (size // 2 - 5, 8), 1.5)
        pygame.draw.circle(self.image, BLACK, (size // 2 + 5, 8), 1.5)
        # 触角
        pygame.draw.line(self.image, body_color, (size // 2 - 7, 5), (size // 2 - 11, 0), 2)
        pygame.draw.line(self.image, body_color, (size // 2 + 7, 5), (size // 2 + 11, 0), 2)

        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.start_x = x
        self.row = row
        self.frame_counter = random.randint(0, 30)  # 让动画不同步

    def update(self):
        """外星人动画：轻微浮动效果"""
        self.frame_counter += 1
        offset = pygame.math.Vector2(0, 0)
        if self.frame_counter % 60 < 30:
            offset.y = 1
        else:
            offset.y = 0
        self.rect.y += offset.y


# ─── 外星人子弹类 ───
class AlienBullet(pygame.sprite.Sprite):
    """外星人发射的子弹"""

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((4, 10))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.midtop = (x, y)

    def update(self):
        self.rect.y += ALIEN_BULLET_SPEED
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


# ─── 爆炸特效类 ───
class Explosion(pygame.sprite.Sprite):
    """简单的爆炸动画"""

    def __init__(self, center):
        super().__init__()
        self.images = []
        # 生成 5 帧爆炸动画
        for i in range(5):
            surf = pygame.Surface((40, 40), pygame.SRCALPHA)
            radius = 5 + i * 4
            alpha = 255 - i * 50
            color_list = [YELLOW, ORANGE, RED, RED, (100, 0, 0)]
            pygame.draw.circle(surf, color_list[i], (20, 20), radius)
            surf.set_alpha(alpha)
            self.images.append(surf)

        self.image = self.images[0]
        self.rect = self.image.get_rect(center=center)
        self.frame = 0

    def update(self):
        self.frame += 1
        if self.frame >= len(self.images):
            self.kill()
        else:
            self.image = self.images[self.frame]


# ─── 闪烁得分文字类 ───
class ScorePopup(pygame.sprite.Sprite):
    """消灭外星人时显示得分"""

    def __init__(self, center, score):
        super().__init__()
        self.font = pygame.font.Font(None, 28)
        self.text = f"+{score}"
        self.image = self.font.render(self.text, True, YELLOW)
        self.rect = self.image.get_rect(center=center)
        self.life = 30  # 持续帧数

    def update(self):
        self.rect.y -= 1
        self.life -= 1
        self.image.set_alpha(int(self.life / 30 * 255))
        if self.life <= 0:
            self.kill()


# ─── 星星背景类 ───
class StarBackground:
    """动态星空背景"""

    def __init__(self):
        self.stars = []
        for _ in range(120):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            speed = random.uniform(0.3, 1.2)
            brightness = random.randint(80, 255)
            self.stars.append([x, y, speed, brightness])

    def update(self):
        for star in self.stars:
            star[1] += star[2]
            if star[1] > SCREEN_HEIGHT:
                star[1] = 0
                star[0] = random.randint(0, SCREEN_WIDTH)

    def draw(self, screen):
        for x, y, _, brightness in self.stars:
            screen.set_at((int(x), int(y)), (brightness, brightness, brightness))


# ─── 游戏主类 ───
class SpaceInvaders:
    """游戏主控制器"""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("太空侵略者 | Space Invaders")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.Font(None, 64)
        self.font_small = pygame.font.Font(None, 32)

        self.star_bg = StarBackground()
        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        # 精灵组
        self.all_sprites = pygame.sprite.Group()
        self.player_group = pygame.sprite.GroupSingle()
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.alien_bullets = pygame.sprite.Group()
        self.effects = pygame.sprite.Group()

        # 玩家
        self.player = Player()
        self.player_group.add(self.player)

        # 外星人
        self.create_aliens()

        # 游戏状态
        self.score = 0
        self.level = 1
        self.alien_h_speed = ALIEN_H_SPEED
        self.alien_dir = 1  # 1=右, -1=左
        self.alien_down_counter = 0
        self.alien_should_drop = False
        self.enemy_shoot_timer = 0

        # 游戏流程
        self.game_state = "playing"  # playing / game_over / victory
        self.game_over_delay = 0
        self.victory_delay = 0

    def create_aliens(self):
        """创建外星人阵列"""
        self.aliens.empty()
        spacing_x = 65
        spacing_y = 55
        start_x = (SCREEN_WIDTH - (ALIEN_COLS - 1) * spacing_x) // 2 - 15
        start_y = 60

        for row in range(ALIEN_ROWS):
            for col in range(ALIEN_COLS):
                x = start_x + col * spacing_x
                y = start_y + row * spacing_y
                alien = Alien(x, y, row)
                self.aliens.add(alien)

        # 设置边界
        self.update_alien_bounds()

    def update_alien_bounds(self):
        """更新外星人群体的左右边界"""
        if len(self.aliens) == 0:
            self.left_bound = SCREEN_WIDTH
            self.right_bound = 0
            return

        self.left_bound = min(a.rect.left for a in self.aliens)
        self.right_bound = max(a.rect.right for a in self.aliens)

    def handle_events(self):
        """处理输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.game_state == "playing":
                        self.player.shoot(self.bullets)
                    elif self.game_state in ("game_over", "victory"):
                        # 重新开始
                        self.reset_game()
                if event.key == pygame.K_ESCAPE:
                    return False
        return True

    def update_aliens(self):
        """更新外星人运动"""
        if len(self.aliens) == 0:
            return

        # 水平移动
        for alien in self.aliens:
            alien.rect.x += self.alien_h_speed * self.alien_dir

        # 检测边界碰撞
        self.update_alien_bounds()
        if self.right_bound >= SCREEN_WIDTH - 10:
            self.alien_dir = -1
            self.alien_should_drop = True
        elif self.left_bound <= 10:
            self.alien_dir = 1
            self.alien_should_drop = True

        # 下降
        if self.alien_should_drop:
            for alien in self.aliens:
                alien.rect.y += ALIEN_DROP_DIST
            self.alien_should_drop = False

        # 检测是否到达底线
        for alien in self.aliens:
            if alien.rect.bottom >= SCREEN_HEIGHT - 100:
                self.game_state = "game_over"
                return

    def alien_shoot(self):
        """外星人随机射击"""
        if len(self.aliens) == 0:
            return

        self.enemy_shoot_timer += 1
        # 外星人越少，射击频率越高
        shoot_chance = max(2, SHOOT_COOLDOWN - (ALIEN_ROWS * ALIEN_COLS - len(self.aliens)) // 4)
        if self.enemy_shoot_timer >= shoot_chance:
            self.enemy_shoot_timer = 0
            # 随机选一个外星人射击
            shooter = random.choice(list(self.aliens))
            bullet = AlienBullet(shooter.rect.centerx, shooter.rect.bottom)
            self.alien_bullets.add(bullet)

    def check_collisions(self):
        """检测碰撞"""
        # 玩家子弹 vs 外星人
        hits = pygame.sprite.groupcollide(self.bullets, self.aliens, True, False)
        for bullet, alien_list in hits.items():
            for alien in alien_list:
                # 计分：行越高分越多
                score_value = (ALIEN_ROWS - alien.row) * 10
                self.score += score_value
                # 特效
                self.effects.add(Explosion(alien.rect.center))
                self.effects.add(ScorePopup(alien.rect.center, score_value))
                alien.kill()

        # 外星人子弹 vs 玩家
        hits = pygame.sprite.spritecollide(self.player, self.alien_bullets, True)
        if hits:
            if self.player.hit():
                self.effects.add(Explosion(self.player.rect.center))
                if self.player.lives <= 0:
                    self.game_state = "game_over"

        # 外星人撞玩家
        hits = pygame.sprite.spritecollide(self.player, self.aliens, False)
        if hits:
            if self.player.hit():
                self.effects.add(Explosion(self.player.rect.center))
                if self.player.lives <= 0:
                    self.game_state = "game_over"

        # 检测胜利
        if len(self.aliens) == 0 and self.game_state == "playing":
            self.game_state = "victory"

    def draw_hud(self):
        """绘制界面信息"""
        # 得分
        score_text = self.font_small.render(f"得分: {self.score}", True, WHITE)
        self.screen.blit(score_text, (20, 15))

        # 生命值
        lives_text = self.font_small.render(f"生命: {'♥' * self.player.lives}", True, RED)
        self.screen.blit(lives_text, (20, 50))

        # 等级 (外星人数量)
        alien_count = len(self.aliens)
        count_text = self.font_small.render(f"剩余: {alien_count}", True, CYAN)
        self.screen.blit(count_text, (SCREEN_WIDTH - 140, 15))

    def draw_game_over(self):
        """绘制游戏结束画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # 大标题
        title = self.font_large.render("GAME OVER", True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(title, title_rect)

        # 最终得分
        score_text = self.font_small.render(f"最终得分: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        self.screen.blit(score_text, score_rect)

        # 提示
        hint = self.font_small.render("按 SPACE 重新开始 | ESC 退出", True, YELLOW)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(hint, hint_rect)

    def draw_victory(self):
        """绘制胜利画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        title = self.font_large.render("胜 利 !", True, GREEN)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(title, title_rect)

        score_text = self.font_small.render(f"得分: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        self.screen.blit(score_text, score_rect)

        hint = self.font_small.render("按 SPACE 再来一局 | ESC 退出", True, YELLOW)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(hint, hint_rect)

    def run(self):
        """游戏主循环"""
        running = True
        while running:
            # 控制帧率
            self.clock.tick(FPS)

            # 事件处理
            running = self.handle_events()

            # 更新逻辑
            if self.game_state == "playing":
                self.player_group.update()
                self.bullets.update()
                self.alien_bullets.update()
                self.update_aliens()
                self.alien_shoot()
                self.check_collisions()

            # 更新特效（始终更新）
            self.effects.update()
            self.star_bg.update()

            # ─── 渲染 ───
            self.screen.fill(BLACK)
            self.star_bg.draw(self.screen)

            # 绘制精灵
            self.aliens.draw(self.screen)
            self.bullets.draw(self.screen)
            self.alien_bullets.draw(self.screen)
            self.effects.draw(self.screen)
            self.player_group.draw(self.screen)

            # 绘制 HUD
            self.draw_hud()

            # 游戏结束/胜利画面
            if self.game_state == "game_over":
                self.draw_game_over()
            elif self.game_state == "victory":
                self.draw_victory()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ─── 程序入口 ───
if __name__ == "__main__":
    game = SpaceInvaders()
    game.run()