#!/usr/bin/env python3
"""
Zuma 祖玛 - 射击彩色球，三个同色相连消除
使用 Python + Pygame 实现

操作说明：
  - 鼠标移动瞄准
  - 左键点击发射
  - 右键切换当前球颜色
  - 消除所有球过关，球到达终点游戏结束
"""

import pygame
import math
import random
import sys

# ==================== 常量配置 ====================
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 620
FPS = 60

# 颜色 (R, G, B)
COLORS = {
    "bg": (20, 20, 35),
    "path": (60, 55, 80),
    "path_border": (90, 85, 110),
    "launcher": (180, 170, 200),
    "text": (255, 255, 200),
    "score": (255, 215, 0),
    "lives": (255, 80, 80),
    "game_over": (255, 50, 50),
}

# 球的颜色方案 (亮色)
BALL_COLORS = [
    (255, 60, 60),    # 红
    (60, 200, 255),   # 蓝
    (60, 220, 80),    # 绿
    (255, 210, 40),   # 黄
    (230, 130, 255),  # 紫
]

BALL_RADIUS = 12
BALL_SPEED = 1.2          # 球沿路径移动速度
SHOT_SPEED = 12.0          # 发射球飞行速度
SPAWN_INTERVAL = 90        # 生成新球间隔(帧数)
INITIAL_CHAIN_LENGTH = 8   # 初始链长度
MATCH_MIN = 3              # 最少几个消除

# ==================== 路径定义 ====================
# 路径关键点 (蛇形路径)
PATH_WAYPOINTS = [
    (80, 80),
    (720, 80),
    (720, 180),
    (180, 180),
    (180, 280),
    (620, 280),
    (620, 380),
    (120, 380),
    (120, 480),
    (400, 480),
    (400, 560),
]

# 发射器位置
LAUNCHER_POS = (400, 580)


def build_path():
    """根据路径关键点计算路径点序列和分段距离"""
    points = []
    distances = []
    total = 0.0
    for i in range(len(PATH_WAYPOINTS) - 1):
        x1, y1 = PATH_WAYPOINTS[i]
        x2, y2 = PATH_WAYPOINTS[i + 1]
        dx, dy = x2 - x1, y2 - y1
        seg_len = math.hypot(dx, dy)
        steps = max(int(seg_len / 3), 1)
        for j in range(steps):
            t = j / steps
            points.append((x1 + dx * t, y1 + dy * t))
            distances.append(total + seg_len * t)
        total += seg_len
    # 添加最后一个点
    points.append(PATH_WAYPOINTS[-1])
    distances.append(total)
    return points, distances, total


PATH_POINTS, PATH_DISTANCES, PATH_LENGTH = build_path()


def pos_on_path(distance):
    """根据距离值获取路径上的(x, y)坐标"""
    d = max(0.0, min(distance, PATH_LENGTH))
    # 二分查找
    lo, hi = 0, len(PATH_DISTANCES) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if PATH_DISTANCES[mid] <= d:
            lo = mid
        else:
            hi = mid - 1
    idx = lo
    if idx >= len(PATH_POINTS) - 1:
        return PATH_POINTS[-1]
    # 线性插值
    d1, d2 = PATH_DISTANCES[idx], PATH_DISTANCES[idx + 1]
    if d2 - d1 < 0.001:
        return PATH_POINTS[idx]
    t = (d - d1) / (d2 - d1)
    x1, y1 = PATH_POINTS[idx]
    x2, y2 = PATH_POINTS[idx + 1]
    return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)


# ==================== 粒子系统 ====================
class Particle:
    """简单粒子(消除特效)"""
    def __init__(self, x, y, color):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2, 6)
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.life = random.uniform(15, 30)
        self.max_life = self.life
        self.size = random.uniform(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1  # 重力
        self.life -= 1
        return self.life > 0

    def draw(self, screen):
        alpha = max(0, int(255 * (self.life / self.max_life)))
        size = max(1, int(self.size * (self.life / self.max_life)))
        # 使用带透明度的圆
        surf = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (size + 1, size + 1), size)
        screen.blit(surf, (int(self.x) - size - 1, int(self.y) - size - 1))


# ==================== 游戏类 ====================
class ZumaGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Zuma 祖玛")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simsun,msyh,notosanssc,notosanscjk,wenquanyimicrohei,sans-serif", 22)
        self.big_font = pygame.font.SysFont("simsun,msyh,notosanssc,notosanscjk,wenquanyimicrohei,sans-serif", 48)
        self.reset()

    def reset(self):
        """重置游戏状态"""
        self.chain = []           # 路径上的球 [(color_index, distance), ...]
        self.shot_balls = []      # 飞行中的球 [(x, y, vx, vy, color_index), ...]
        self.particles = []       # 粒子特效
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.spawn_timer = 0
        self.chain_speed = BALL_SPEED
        self.eliminating = False  # 正在消除动画中
        self.elim_timer = 0

        # 当前发射器状态
        self.current_color = random.randint(0, len(BALL_COLORS) - 1)
        self.next_color = random.randint(0, len(BALL_COLORS) - 1)
        self.aim_angle = 0

        # 生成初始链
        for i in range(INITIAL_CHAIN_LENGTH):
            color = random.randint(0, len(BALL_COLORS) - 1)
            dist = i * 30
            self.chain.append([color, dist])

        # 按距离排序
        self.chain.sort(key=lambda b: b[1])

    def spawn_new_ball(self):
        """在路径起点生成一个新球"""
        color = random.randint(0, len(BALL_COLORS) - 1)
        self.chain.append([color, 0.0])
        # 检查起点是否已被占用
        self.chain.sort(key=lambda b: b[1])

    def find_insert_position(self, distance):
        """找到给定距离在链中的插入位置(索引)"""
        if not self.chain:
            return 0
        for i, (_, d) in enumerate(self.chain):
            if d > distance:
                return i
        return len(self.chain)

    def check_matches(self, start_idx):
        """检查从start_idx开始的匹配，返回要消除的索引集合"""
        if not self.chain:
            return set()

        color = self.chain[start_idx][0]
        # 向左扩展
        left = start_idx
        while left > 0 and self.chain[left - 1][0] == color:
            left -= 1
        # 向右扩展
        right = start_idx
        while right < len(self.chain) - 1 and self.chain[right + 1][0] == color:
            right += 1

        if right - left + 1 >= MATCH_MIN:
            return set(range(left, right + 1))
        return set()

    def chain_reaction(self, removed_indices):
        """连锁反应：移除后检查相邻球是否匹配"""
        total_removed = set(removed_indices)
        changed = True
        while changed:
            changed = False
            # 重新构建链(排除已移除的)
            remaining = [b for i, b in enumerate(self.chain) if i not in total_removed]
            if not remaining:
                break
            # 检查相邻球
            i = 0
            while i < len(remaining):
                j = i
                while j < len(remaining) - 1 and remaining[j + 1][0] == remaining[i][0]:
                    j += 1
                if j - i + 1 >= MATCH_MIN:
                    # 找到匹配，标记这些球在原始链中的索引
                    for k in range(i, j + 1):
                        # 在原始链中查找这个球
                        for orig_idx, ball in enumerate(self.chain):
                            if orig_idx not in total_removed and ball[0] == remaining[k][0] and abs(ball[1] - remaining[k][1]) < 1:
                                total_removed.add(orig_idx)
                                break
                    changed = True
                    # 移除后重新开始检查
                    break
                i = j + 1
        return total_removed

    def remove_balls(self, indices):
        """移除指定索引的球，生成粒子效果"""
        for idx in sorted(indices, reverse=True):
            if idx < len(self.chain):
                color_idx = self.chain[idx][0]
                pos = pos_on_path(self.chain[idx][1])
                color = BALL_COLORS[color_idx]
                # 生成粒子
                for _ in range(15):
                    self.particles.append(Particle(pos[0], pos[1], color))
                self.chain.pop(idx)

        # 计分
        removed = len(indices)
        if removed >= 3:
            self.score += removed * 10 + (removed - 3) * 20

    def shoot(self):
        """发射球"""
        angle = self.aim_angle
        cx, cy = LAUNCHER_POS
        vx = math.cos(angle) * SHOT_SPEED
        vy = math.sin(angle) * SHOT_SPEED
        self.shot_balls.append([cx, cy, vx, vy, self.current_color])
        self.current_color = self.next_color
        self.next_color = random.randint(0, len(BALL_COLORS) - 1)

    def update(self):
        if self.game_over:
            return

        self.elim_timer = max(0, self.elim_timer - 1)

        # 1. 更新粒子
        self.particles = [p for p in self.particles if p.update()]

        # 2. 更新链上的球(移动)
        if not self.eliminating:
            for ball in self.chain:
                ball[1] += self.chain_speed

            # 检查是否有球到达终点
            for ball in self.chain:
                if ball[1] >= PATH_LENGTH:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.game_over = True
                        return
                    # 重置所有球的位置(回到起点)
                    self.chain = []
                    self.shot_balls = []
                    # 重新生成
                    for i in range(INITIAL_CHAIN_LENGTH):
                        color = random.randint(0, len(BALL_COLORS) - 1)
                        dist = i * 30
                        self.chain.append([color, dist])
                    self.chain.sort(key=lambda b: b[1])
                    return

        # 3. 生成新球
        self.spawn_timer += 1
        if self.spawn_timer >= SPAWN_INTERVAL and not self.eliminating:
            self.spawn_timer = 0
            self.spawn_new_ball()

        # 4. 更新飞行中的球
        new_shot = []
        for ball in self.shot_balls:
            x, y, vx, vy, color_idx = ball
            x += vx
            y += vy

            # 检查是否超出屏幕
            if x < -50 or x > SCREEN_WIDTH + 50 or y < -50 or y > SCREEN_HEIGHT + 50:
                continue

            # 检查是否碰到链上的球
            hit = False
            for chain_idx, (c_color, c_dist) in enumerate(self.chain):
                cx, cy = pos_on_path(c_dist)
                dx, dy = x - cx, y - cy
                dist = math.hypot(dx, dy)
                if dist < BALL_RADIUS * 2.5:
                    # 碰到球！插入到链中
                    insert_pos = self.find_insert_position(c_dist)
                    if insert_pos > chain_idx:
                        insert_pos = chain_idx + 1
                    self.chain.insert(insert_pos, [color_idx, c_dist])
                    hit = True

                    # 检查匹配
                    matches = self.check_matches(insert_pos)
                    if matches:
                        self.eliminating = True
                        self.elim_timer = 30
                        total_removed = self.chain_reaction(matches)
                        self.remove_balls(total_removed)
                    break

            if not hit:
                # 检查是否碰到路径(用于捕获)
                # 简单检查：球是否接近路径上的任何点
                for pd in range(0, int(PATH_LENGTH), 5):
                    px, py = pos_on_path(pd)
                    dx, dy = x - px, y - py
                    if math.hypot(dx, dy) < BALL_RADIUS * 2:
                        # 插入到最近的位置
                        insert_pos = self.find_insert_position(pd)
                        # 找最近的球
                        nearest_idx = -1
                        nearest_dist = float('inf')
                        for ci, (_, cd) in enumerate(self.chain):
                            if abs(cd - pd) < nearest_dist:
                                nearest_dist = abs(cd - pd)
                                nearest_idx = ci
                        if nearest_idx >= 0:
                            insert_pos = self.find_insert_position(self.chain[nearest_idx][1])
                            self.chain.insert(insert_pos, [color_idx, self.chain[nearest_idx][1]])
                        else:
                            self.chain.insert(insert_pos, [color_idx, pd])
                        hit = True

                        # 检查匹配
                        matches = self.check_matches(insert_pos)
                        if matches:
                            self.eliminating = True
                            self.elim_timer = 30
                            total_removed = self.chain_reaction(matches)
                            self.remove_balls(total_removed)
                        break

            if not hit:
                ball[0], ball[1], ball[2], ball[3] = x, y, vx, vy
                new_shot.append(ball)

        self.shot_balls = new_shot

    def draw(self):
        self.screen.fill(COLORS["bg"])

        # 1. 绘制路径
        self._draw_path()

        # 2. 绘制链上的球
        for color_idx, dist in self.chain:
            pos = pos_on_path(dist)
            self._draw_ball(int(pos[0]), int(pos[1]), color_idx)

        # 3. 绘制飞行中的球
        for x, y, vx, vy, color_idx in self.shot_balls:
            self._draw_ball(int(x), int(y), color_idx)

        # 4. 绘制粒子
        for p in self.particles:
            p.draw(self.screen)

        # 5. 绘制发射器
        self._draw_launcher()

        # 6. 绘制UI
        self._draw_ui()

        # 7. 游戏结束
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            text = self.big_font.render("GAME OVER", True, COLORS["game_over"])
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
            self.screen.blit(text, text_rect)
            text2 = self.font.render("按 R 重新开始", True, COLORS["text"])
            text2_rect = text2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            self.screen.blit(text2, text2_rect)

        pygame.display.flip()

    def _draw_path(self):
        """绘制路径"""
        # 绘制路径轨迹
        for i in range(len(PATH_POINTS) - 1):
            x1, y1 = PATH_POINTS[i]
            x2, y2 = PATH_POINTS[i + 1]
            pygame.draw.line(self.screen, COLORS["path"], (x1, y1), (x2, y2), BALL_RADIUS * 2 + 4)
            pygame.draw.line(self.screen, COLORS["path_border"], (x1, y1), (x2, y2), BALL_RADIUS * 2 + 8)

        # 绘制起点和终点标记
        start_pos = PATH_POINTS[0]
        end_pos = PATH_POINTS[-1]
        pygame.draw.circle(self.screen, (60, 200, 60), (int(start_pos[0]), int(start_pos[1])), 8)
        pygame.draw.circle(self.screen, (200, 60, 60), (int(end_pos[0]), int(end_pos[1])), 10)

    def _draw_ball(self, x, y, color_idx):
        """绘制一个彩色球"""
        color = BALL_COLORS[color_idx % len(BALL_COLORS)]
        # 球体高光效果
        pygame.draw.circle(self.screen, color, (x, y), BALL_RADIUS)
        highlight_surf = pygame.Surface((BALL_RADIUS * 2, BALL_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(highlight_surf, (255, 255, 255, 50), (BALL_RADIUS - 3, BALL_RADIUS - 3), BALL_RADIUS - 4, 2)
        self.screen.blit(highlight_surf, (x - BALL_RADIUS, y - BALL_RADIUS))
        # 边框
        pygame.draw.circle(self.screen, (80, 80, 90), (x, y), BALL_RADIUS, 1)

    def _draw_launcher(self):
        """绘制发射器"""
        cx, cy = LAUNCHER_POS
        angle = self.aim_angle

        # 发射器底座
        pygame.draw.circle(self.screen, COLORS["launcher"], (cx, cy), 18)
        pygame.draw.circle(self.screen, (100, 95, 120), (cx, cy), 18, 2)

        # 发射管
        tube_len = 35
        ex = cx + math.cos(angle) * tube_len
        ey = cy + math.sin(angle) * tube_len
        pygame.draw.line(self.screen, COLORS["launcher"], (cx, cy), (ex, ey), 6)
        pygame.draw.line(self.screen, (100, 95, 120), (cx, cy), (ex, ey), 2)

        # 当前球
        self._draw_ball(cx, cy, self.current_color)

        # 下一个球预览
        preview_x = cx + 40
        preview_y = cy + 5
        text = self.font.render("下一个:", True, COLORS["text"])
        self.screen.blit(text, (preview_x - 60, preview_y - 5))
        self._draw_ball(preview_x + 10, preview_y + 8, self.next_color)

        # 瞄准线
        aim_len = 200
        ax = cx + math.cos(angle) * aim_len
        ay = cy + math.sin(angle) * aim_len
        line_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(line_surf, (255, 255, 255, 25), (cx, cy), (ax, ay), 1)
        self.screen.blit(line_surf, (0, 0))

    def _draw_ui(self):
        """绘制界面信息"""
        # 分数
        score_text = self.font.render(f"分数: {self.score}", True, COLORS["score"])
        self.screen.blit(score_text, (20, 10))

        # 生命
        lives_text = self.font.render(f"生命: {'♥' * self.lives}", True, COLORS["lives"])
        self.screen.blit(lives_text, (20, 40))

        # 球数量
        ball_count = self.font.render(f"剩余球: {len(self.chain)}", True, COLORS["text"])
        self.screen.blit(ball_count, (SCREEN_WIDTH - 150, 10))

        # 操作提示
        help_text = self.font.render("鼠标瞄准 | 左键发射 | R 重新开始", True, (120, 120, 140))
        self.screen.blit(help_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 25))

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.reset()
            if event.key == pygame.K_ESCAPE:
                return False

        if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
            if event.button == 1:  # 左键发射
                self.shoot()
            elif event.button == 3:  # 右键切换颜色
                self.current_color = (self.current_color + 1) % len(BALL_COLORS)

        return True

    def run(self):
        running = True
        while running:
            # 鼠标位置 -> 瞄准角度
            mx, my = pygame.mouse.get_pos()
            cx, cy = LAUNCHER_POS
            dx, dy = mx - cx, my - cy
            if math.hypot(dx, dy) > 5:
                self.aim_angle = math.atan2(dy, dx)

            for event in pygame.event.get():
                if not self.handle_event(event):
                    running = False

            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


# ==================== 入口 ====================
if __name__ == "__main__":
    game = ZumaGame()
    game.run()