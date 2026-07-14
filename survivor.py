"""
吸血鬼幸存者 (Vampire Survivors) - 类幸存者游戏
===============================
控制: WASD 移动
自动攻击范围内的最近敌人
收集经验宝石升级
在无尽的敌潮中尽可能生存更久！

作者: AI 游戏开发者
日期: 2026-07-14
"""

import pygame
import random
import math
import sys

# ─── 初始化 ─────────────────────────────────────────────────
pygame.init()
W, H = 800, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("吸血鬼幸存者 - Vampire Survivors")
clock = pygame.time.Clock()
font_title = pygame.font.SysFont("simhei", 42)
font_large = pygame.font.SysFont("simhei", 32)
font_mid = pygame.font.SysFont("simhei", 24)
font_small = pygame.font.SysFont("simhei", 18)

# ─── 颜色 ─────────────────────────────────────────────────
WHITE = (255, 255, 255)
BLACK = (10, 10, 15)
RED = (255, 50, 50)
GREEN = (50, 255, 80)
BLUE = (60, 120, 255)
YELLOW = (255, 220, 50)
PURPLE = (180, 60, 255)
ORANGE = (255, 160, 20)
GRAY = (80, 80, 90)
DARK = (20, 20, 30)
HP_BAR = (255, 60, 60)
HP_BG = (60, 20, 20)

# ─── 工具函数 ─────────────────────────────────────────────
def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def angle_to(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

# ─── 游戏对象 ─────────────────────────────────────────────
class Player:
    def __init__(self):
        self.x = W // 2
        self.y = H // 2
        self.r = 16
        self.speed = 3.0
        self.hp = 100
        self.max_hp = 100
        self.level = 1
        self.exp = 0
        self.exp_next = 10
        self.attack_dmg = 10
        self.attack_cd = 0.4        # 攻击间隔(秒)
        self.attack_range = 300
        self.proj_speed = 7
        self.proj_count = 1
        self.cooldown_timer = 0
        self.invincible = 0
        self.kills = 0
        self.survived = 0.0

    @property
    def pos(self):
        return (self.x, self.y)

    def update(self, dt, keys):
        dx = dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if dx != 0 or dy != 0:
            l = math.hypot(dx, dy)
            dx /= l
            dy /= l
        self.x = clamp(self.x + dx * self.speed, self.r, W - self.r)
        self.y = clamp(self.y + dy * self.speed, self.r, H - self.r)
        self.cooldown_timer = max(0, self.cooldown_timer - dt)
        self.invincible = max(0, self.invincible - dt)
        self.survived += dt

    def take_damage(self, dmg):
        if self.invincible > 0:
            return
        self.hp -= dmg
        self.invincible = 0.3

    def add_exp(self, amount):
        self.exp += amount
        while self.exp >= self.exp_next:
            self.exp -= self.exp_next
            self.level += 1
            self.exp_next = int(self.exp_next * 1.35)
            return True  # 升级
        return False

    def can_attack(self):
        return self.cooldown_timer <= 0

    def attack(self):
        self.cooldown_timer = self.attack_cd

    def draw(self, surf):
        # 闪烁效果(受伤时)
        if int(self.survived * 10) % 2 == 0 and self.invincible > 0:
            return
        pygame.draw.circle(surf, BLUE, (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), self.r, 2)
        # 血条
        bw = 36
        bx = self.x - bw // 2
        by = self.y - self.r - 10
        pygame.draw.rect(surf, HP_BG, (bx, by, bw, 5))
        hp_w = int(bw * (self.hp / self.max_hp))
        pygame.draw.rect(surf, HP_BAR, (bx, by, hp_w, 5))


class Projectile:
    def __init__(self, x, y, angle, dmg, speed):
        self.x = x
        self.y = y
        self.angle = angle
        self.dmg = dmg
        self.speed = speed
        self.r = 5
        self.alive = True

    @property
    def pos(self):
        return (self.x, self.y)

    def update(self, dt):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        if self.x < -50 or self.x > W + 50 or self.y < -50 or self.y > H + 50:
            self.alive = False

    def draw(self, surf):
        pygame.draw.circle(surf, YELLOW, (int(self.x), int(self.y)), self.r)
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), self.r, 1)


class Enemy:
    def __init__(self, x, y, etype, difficulty):
        self.x = x
        self.y = y
        self.etype = etype
        self.alive = True
        self.hit_flash = 0

        if etype == "bat":       # 蝙蝠 - 快但脆
            self.r = 10
            self.speed = 1.8 + difficulty * 0.08
            self.hp = 8 + difficulty * 2
            self.max_hp = self.hp
            self.dmg = 5 + difficulty
            self.exp_val = 2
            self.color = (120, 80, 180)
        elif etype == "skeleton":  # 骷髅 - 中等
            self.r = 14
            self.speed = 1.2 + difficulty * 0.06
            self.hp = 20 + difficulty * 4
            self.max_hp = self.hp
            self.dmg = 8 + difficulty * 1.5
            self.exp_val = 4
            self.color = (200, 200, 180)
        elif etype == "demon":   # 恶魔 - 慢但肉
            self.r = 20
            self.speed = 0.7 + difficulty * 0.04
            self.hp = 50 + difficulty * 10
            self.max_hp = self.hp
            self.dmg = 15 + difficulty * 2
            self.exp_val = 10
            self.color = (200, 40, 40)
        else:   # zombie - 基础
            self.r = 12
            self.speed = 1.0 + difficulty * 0.05
            self.hp = 15 + difficulty * 3
            self.max_hp = self.hp
            self.dmg = 6 + difficulty
            self.exp_val = 3
            self.color = (80, 160, 60)

    @property
    def pos(self):
        return (self.x, self.y)

    def update(self, dt, px, py):
        if self.hit_flash > 0:
            self.hit_flash -= dt
        ang = angle_to((self.x, self.y), (px, py))
        self.x += math.cos(ang) * self.speed
        self.y += math.sin(ang) * self.speed

    def take_damage(self, dmg):
        self.hp -= dmg
        self.hit_flash = 0.1
        if self.hp <= 0:
            self.alive = False
            return True  # 被击杀
        return False

    def draw(self, surf):
        col = self.color
        if self.hit_flash > 0:
            col = WHITE
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)), self.r)
        # 眼睛
        eye_off = self.r * 0.3
        eye_r = max(2, self.r // 5)
        pygame.draw.circle(surf, RED, (int(self.x - eye_off), int(self.y - eye_off)), eye_r)
        pygame.draw.circle(surf, RED, (int(self.x + eye_off), int(self.y - eye_off)), eye_r)
        # 血条(仅精英)
        if self.etype == "demon":
            bw = self.r * 2
            bx = self.x - bw // 2
            by = self.y - self.r - 8
            pygame.draw.rect(surf, HP_BG, (bx, by, bw, 4))
            hp_w = int(bw * (self.hp / self.max_hp))
            pygame.draw.rect(surf, RED, (bx, by, hp_w, 4))


class ExpGem:
    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        self.value = value
        self.r = 6 + value
        self.alive = True
        self.bob = random.random() * 6.28

    @property
    def pos(self):
        return (self.x, self.y)

    def update(self, dt):
        self.bob += dt * 3

    def draw(self, surf):
        r = int(self.r)
        col = GREEN if self.value < 5 else (100, 255, 255) if self.value < 10 else PURPLE
        offset = math.sin(self.bob) * 3
        px = int(self.x + offset)
        pygame.draw.circle(surf, col, (px, int(self.y)), r)
        # 发光效果
        pygame.draw.circle(surf, WHITE, (px, int(self.y)), r, 1)


# ─── 升级选项 ─────────────────────────────────────────────
UPGRADES = [
    {"name": "攻击力+", "key": "attack_dmg", "val": 5, "desc": "伤害 +5"},
    {"name": "攻速+", "key": "attack_cd", "val": -0.05, "desc": "冷却 -0.05秒"},
    {"name": "移速+", "key": "speed", "val": 0.3, "desc": "移速 +0.3"},
    {"name": "射程+", "key": "attack_range", "val": 30, "desc": "射程 +30"},
    {"name": "弹速+", "key": "proj_speed", "val": 1, "desc": "弹速 +1"},
    {"name": "弹幕+", "key": "proj_count", "val": 1, "desc": "弹幕 +1"},
    {"name": "回血", "key": "heal", "val": 30, "desc": "回复 30 HP"},
]


def apply_upgrade(player, upgrade):
    if upgrade["key"] == "heal":
        player.hp = min(player.max_hp, player.hp + upgrade["val"])
        return
    if upgrade["key"] == "attack_cd":
        player.attack_cd = max(0.08, player.attack_cd + upgrade["val"])
        return
    if upgrade["key"] == "proj_count":
        player.proj_count += upgrade["val"]
        return
    setattr(player, upgrade["key"], getattr(player, upgrade["key"]) + upgrade["val"])


# ─── 生成敌人 ─────────────────────────────────────────────
def spawn_enemy(player, difficulty):
    # 从屏幕边缘外生成
    side = random.randrange(4)
    margin = 40
    if side == 0:  # 上
        x = random.randint(0, W)
        y = -margin
    elif side == 1:  # 下
        x = random.randint(0, W)
        y = H + margin
    elif side == 2:  # 左
        x = -margin
        y = random.randint(0, H)
    else:  # 右
        x = W + margin
        y = random.randint(0, H)

    # 越靠近玩家越难
    d = dist((x, y), player.pos)
    diff = difficulty + max(0, 5 - d / 100)

    # 随机选择类型
    roll = random.random()
    if diff < 2:
        etype = "bat" if roll < 0.4 else "zombie"
    elif diff < 5:
        etype = random.choice(["bat", "zombie", "skeleton"])
    else:
        etype = random.choice(["zombie", "skeleton", "demon"])

    return Enemy(x, y, etype, diff)


# ─── 游戏状态 ─────────────────────────────────────────────
STATE_MENU = 0
STATE_PLAY = 1
STATE_LEVELUP = 2
STATE_GAMEOVER = 3


# ─── 主游戏循环 ───────────────────────────────────────────
def run_game():
    player = Player()
    projectiles = []
    enemies = []
    gems = []

    game_state = STATE_MENU
    difficulty = 0
    wave_timer = 0
    spawn_rate = 1.5       # 初始生成间隔(秒)
    enemy_cap = 30
    score = 0

    # 升级选项缓存
    upgrade_options = []
    selected_upgrade = 0

    running = True
    dt = 0

    while running:
        # ── 事件处理 ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if game_state == STATE_MENU:
                    if event.key == pygame.K_SPACE:
                        # 重置游戏
                        player = Player()
                        projectiles.clear()
                        enemies.clear()
                        gems.clear()
                        difficulty = 0
                        wave_timer = 0
                        spawn_rate = 1.5
                        score = 0
                        game_state = STATE_PLAY
                elif game_state == STATE_LEVELUP:
                    if event.key == pygame.K_UP:
                        selected_upgrade = (selected_upgrade - 1) % len(upgrade_options)
                    elif event.key == pygame.K_DOWN:
                        selected_upgrade = (selected_upgrade + 1) % len(upgrade_options)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        apply_upgrade(player, upgrade_options[selected_upgrade])
                        game_state = STATE_PLAY
                elif game_state == STATE_GAMEOVER:
                    if event.key == pygame.K_SPACE:
                        game_state = STATE_MENU
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

        keys = pygame.key.get_pressed()

        # ── 更新逻辑 ──
        if game_state == STATE_PLAY:
            dt = clock.tick(60) / 1000.0
            dt = min(dt, 0.05)  # 防止卡顿跳帧

            # 玩家更新
            player.update(dt, keys)

            # 难度随时间增加
            difficulty = player.survived * 0.03
            spawn_rate = max(0.25, 1.5 - difficulty * 0.04)
            enemy_cap = 30 + int(difficulty * 2)

            # 生成敌人
            wave_timer += dt
            if wave_timer >= spawn_rate and len(enemies) < enemy_cap:
                enemies.append(spawn_enemy(player, difficulty))
                wave_timer = 0
                # 难度高时一次生成多个
                if difficulty > 4 and random.random() < 0.3:
                    enemies.append(spawn_enemy(player, difficulty))

            # 自动攻击
            if player.can_attack():
                # 找最近敌人
                nearest = None
                near_dist = player.attack_range
                for e in enemies:
                    d = dist(player.pos, e.pos)
                    if d < near_dist:
                        near_dist = d
                        nearest = e
                if nearest:
                    player.attack()
                    ang = angle_to(player.pos, nearest.pos)
                    # 多弹幕
                    spread = 0.15
                    for i in range(player.proj_count):
                        a = ang + (i - (player.proj_count - 1) / 2) * spread
                        p = Projectile(player.x, player.y, a, player.attack_dmg, player.proj_speed)
                        projectiles.append(p)

            # 更新子弹
            for p in projectiles[:]:
                p.update(dt)
                if not p.alive:
                    projectiles.remove(p)

            # 子弹碰撞敌人
            for p in projectiles[:]:
                for e in enemies[:]:
                    if p.alive and e.alive and dist(p.pos, e.pos) < p.r + e.r:
                        killed = e.take_damage(p.dmg)
                        p.alive = False
                        if killed:
                            score += e.exp_val * 2
                            player.kills += 1
                            gems.append(ExpGem(e.x, e.y, e.exp_val))
                            enemies.remove(e)
                        break

            # 更新敌人
            for e in enemies[:]:
                e.update(dt, player.x, player.y)
                # 碰撞玩家
                if e.alive and dist(e.pos, player.pos) < e.r + player.r:
                    player.take_damage(e.dmg * dt * 5)
                    if player.hp <= 0:
                        player.hp = 0
                        game_state = STATE_GAMEOVER

            # 更新经验宝石
            for g in gems[:]:
                g.update(dt)
                # 吸引到玩家附近
                d = dist(g.pos, player.pos)
                if d < 60:
                    ang = angle_to(g.pos, player.pos)
                    g.x += math.cos(ang) * 5
                    g.y += math.sin(ang) * 5
                if d < player.r + g.r + 4:
                    leveled = player.add_exp(g.value)
                    gems.remove(g)
                    if leveled:
                        # 生成升级选项
                        upgrade_options = random.sample(UPGRADES, min(3, len(UPGRADES)))
                        selected_upgrade = 0
                        game_state = STATE_LEVELUP

            # 清理死亡敌人
            enemies = [e for e in enemies if e.alive]

        elif game_state == STATE_GAMEOVER:
            dt = clock.tick(60) / 1000.0

        else:
            dt = clock.tick(60) / 1000.0

        # ── 绘制 ──
        screen.fill(BLACK)

        if game_state == STATE_MENU:
            # 背景装饰粒子
            for _ in range(50):
                rx = random.randint(0, W)
                ry = random.randint(0, H)
                pygame.draw.circle(screen, (30, 30, 40), (rx, ry), 1)

            title = font_title.render("🧛 吸血鬼幸存者", True, RED)
            title_rect = title.get_rect(center=(W // 2, 140))
            screen.blit(title, title_rect)

            sub = font_large.render("Vampire Survivors", True, WHITE)
            sub_rect = sub.get_rect(center=(W // 2, 190))
            screen.blit(sub, sub_rect)

            tips = [
                "WASD / 方向键 - 移动",
                "自动攻击范围内最近的敌人",
                "收集经验宝石升级变强",
                "在无尽的敌潮中活下来！",
            ]
            for i, tip in enumerate(tips):
                t = font_mid.render(tip, True, GRAY)
                tr = t.get_rect(center=(W // 2, 270 + i * 40))
                screen.blit(t, tr)

            start = font_large.render("按 [空格] 开始游戏", True, YELLOW)
            sr = start.get_rect(center=(W // 2, 460))
            pygame.draw.rect(screen, (40, 40, 50), sr.inflate(40, 10), border_radius=8)
            screen.blit(start, sr)

        elif game_state == STATE_PLAY:
            # 绘制网格背景
            for x in range(0, W, 40):
                pygame.draw.line(screen, (18, 18, 25), (x, 0), (x, H), 1)
            for y in range(0, H, 40):
                pygame.draw.line(screen, (18, 18, 25), (0, y), (W, y), 1)

            # 绘制对象
            for g in gems:
                g.draw(screen)
            for e in enemies:
                e.draw(screen)
            for p in projectiles:
                p.draw(screen)
            player.draw(screen)

            # HUD
            # 血条
            hp_pct = player.hp / player.max_hp
            pygame.draw.rect(screen, HP_BG, (10, 10, 200, 18))
            pygame.draw.rect(screen, HP_BAR, (10, 10, int(200 * hp_pct), 18))
            hp_text = font_small.render(f"HP: {int(player.hp)}/{player.max_hp}", True, WHITE)
            screen.blit(hp_text, (16, 12))

            # 等级/经验
            exp_pct = player.exp / player.exp_next
            pygame.draw.rect(screen, (20, 40, 20), (10, 34, 200, 12))
            pygame.draw.rect(screen, GREEN, (10, 34, int(200 * exp_pct), 12))
            lv_text = font_small.render(f"Lv.{player.level}  EXP: {player.exp}/{player.exp_next}", True, WHITE)
            screen.blit(lv_text, (16, 34))

            # 分数/时间/击杀
            info = font_small.render(
                f"⏱ {int(player.survived)}s  💀 {player.kills}  ⭐ {score}  👾 {len(enemies)}",
                True, GRAY
            )
            screen.blit(info, (10, 52))

            # 攻击范围指示
            if player.can_attack():
                pygame.draw.circle(screen, (30, 60, 120), (int(player.x), int(player.y)),
                                   player.attack_range, 1)

        elif game_state == STATE_LEVELUP:
            # 继续绘制游戏背景(半透明)
            for x in range(0, W, 40):
                pygame.draw.line(screen, (18, 18, 25), (x, 0), (x, H), 1)
            for y in range(0, H, 40):
                pygame.draw.line(screen, (18, 18, 25), (0, y), (W, y), 1)
            for g in gems:
                g.draw(screen)
            for e in enemies:
                e.draw(screen)
            for p in projectiles:
                p.draw(screen)
            player.draw(screen)

            # 半透明遮罩
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            lv_title = font_large.render(f"🎉 升级! Lv.{player.level}", True, YELLOW)
            lv_rect = lv_title.get_rect(center=(W // 2, 100))
            screen.blit(lv_title, lv_rect)

            for i, opt in enumerate(upgrade_options):
                y = 180 + i * 80
                color = YELLOW if i == selected_upgrade else GRAY
                bg_color = (40, 40, 60) if i == selected_upgrade else (20, 20, 30)
                border = (80, 80, 120) if i == selected_upgrade else (40, 40, 50)

                rect = pygame.Rect(W // 2 - 150, y, 300, 60)
                pygame.draw.rect(screen, bg_color, rect, border_radius=8)
                pygame.draw.rect(screen, border, rect, 2, border_radius=8)

                name = font_mid.render(opt["name"], True, color)
                desc = font_small.render(opt["desc"], True, (180, 180, 180))
                screen.blit(name, (rect.x + 15, rect.y + 8))
                screen.blit(desc, (rect.x + 15, rect.y + 35))

            hint = font_small.render("↑↓ 选择, 按 Enter/空格 确认", True, GRAY)
            hint_rect = hint.get_rect(center=(W // 2, 480))
            screen.blit(hint, hint_rect)

        elif game_state == STATE_GAMEOVER:
            # 背景
            for x in range(0, W, 40):
                pygame.draw.line(screen, (25, 18, 18), (x, 0), (x, H), 1)
            for y in range(0, H, 40):
                pygame.draw.line(screen, (25, 18, 18), (0, y), (W, y), 1)

            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            go = font_title.render("💀 游戏结束", True, RED)
            go_rect = go.get_rect(center=(W // 2, 140))
            screen.blit(go, go_rect)

            stats = [
                f"生存时间: {int(player.survived)} 秒",
                f"击杀数: {player.kills}",
                f"最终等级: Lv.{player.level}",
                f"得分: {score}",
            ]
            for i, s in enumerate(stats):
                t = font_mid.render(s, True, WHITE)
                tr = t.get_rect(center=(W // 2, 230 + i * 45))
                screen.blit(t, tr)

            restart = font_large.render("按 [空格] 返回主菜单", True, YELLOW)
            rr = restart.get_rect(center=(W // 2, 460))
            pygame.draw.rect(screen, (50, 40, 40), rr.inflate(40, 10), border_radius=8)
            screen.blit(restart, rr)

            quit_t = font_small.render("按 [ESC] 退出", True, GRAY)
            qr = quit_t.get_rect(center=(W // 2, 510))
            screen.blit(quit_t, qr)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    run_game()