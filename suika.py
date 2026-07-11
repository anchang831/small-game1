"""
合成大西瓜 (Suika Game) - 水果合并物理游戏
=============================================
玩法：
  - 点击选择下落位置，释放水果
  - 相同水果碰撞会合并成更大的水果
  - 水果越大分数越高
  - 水果超出顶部线则游戏结束

操作：鼠标移动选择位置，点击释放水果
"""

import pygame
import random
import math

# ==================== 配置 ====================
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 720
FPS = 60

# 容器边界（左右墙和底部）
WALL_LEFT = 80
WALL_RIGHT = 400
WALL_BOTTOM = 660
CEILING_Y = 100  # 游戏结束线

# 水果类型定义：[名称, 半径, 颜色, 分数]
FRUIT_TYPES = [
    ["🍒 樱桃", 15, (255, 50, 50), 1],
    ["🍓 草莓", 20, (255, 100, 100), 2],
    ["🍇 葡萄", 26, (180, 50, 180), 3],
    ["🍊 橘子", 32, (255, 165, 0), 5],
    ["🍑 桃子", 38, (255, 180, 180), 8],
    ["🍎 苹果", 44, (220, 50, 50), 13],
    ["🍐 梨子", 50, (180, 220, 50), 21],
    ["🥝 猕猴桃", 56, (140, 200, 80), 34],
    ["🍈 蜜瓜", 62, (200, 220, 100), 55],
    ["🍉 西瓜", 68, (50, 180, 50), 89],
]

# 物理参数
GRAVITY = 0.35
FRICTION = 0.98
COLLISION_RESTITUTION = 0.5
COLLISION_DAMPING = 0.7

# 预览用半透明色
PREVIEW_ALPHA = 120

# ==================== 水果类 ====================
class Fruit:
    """水果对象，包含物理属性"""

    def __init__(self, fruit_type, x, y, vx=0, vy=0):
        self.type_idx = fruit_type  # 水果类型索引
        self.radius = FRUIT_TYPES[fruit_type][1]
        self.color = FRUIT_TYPES[fruit_type][2]
        self.score = FRUIT_TYPES[fruit_type][3]
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.merged = False  # 是否已被合并（标记删除）
        self.static_frames = 0  # 静止计数，用于判断是否稳定

    def update(self):
        """更新物理状态"""
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy
        self.vx *= FRICTION
        self.vy *= FRICTION

        # 检测静止状态
        speed = math.hypot(self.vx, self.vy)
        if speed < 0.5:
            self.static_frames += 1
        else:
            self.static_frames = 0

    def draw(self, surface):
        """绘制水果"""
        # 主体
        pygame.draw.circle(surface, self.color,
                           (int(self.x), int(self.y)), self.radius)
        # 高光（左上角亮斑）
        highlight_pos = (int(self.x - self.radius * 0.3),
                         int(self.y - self.radius * 0.3))
        highlight_radius = max(3, self.radius // 3)
        highlight = pygame.Surface((highlight_radius * 2, highlight_radius * 2),
                                   pygame.SRCALPHA)
        pygame.draw.circle(highlight, (255, 255, 255, 80),
                           (highlight_radius, highlight_radius), highlight_radius)
        surface.blit(highlight, (highlight_pos[0] - highlight_radius,
                                 highlight_pos[1] - highlight_radius))
        # 边框
        pygame.draw.circle(surface, (0, 0, 0, 100),
                           (int(self.x), int(self.y)), self.radius, 2)

    def get_rect(self):
        """获取碰撞矩形"""
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)


# ==================== 游戏类 ====================
class SuikaGame:
    """合成大西瓜游戏主逻辑"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("合成大西瓜 🍉")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simhei", 22)
        self.big_font = pygame.font.SysFont("simhei", 36)
        self.title_font = pygame.font.SysFont("simhei", 48)

        self.reset_game()

    def reset_game(self):
        """重置游戏状态"""
        self.fruits = []  # 所有水果
        self.next_type = random.randint(0, min(4, len(FRUIT_TYPES) - 1))  # 下一个水果类型（小水果）
        self.drop_x = SCREEN_WIDTH // 2  # 当前释放位置
        self.score = 0
        self.game_over = False
        self.merge_count = 0  # 合并计数
        self.can_drop = True  # 是否可以释放
        self.wait_frames = 0  # 等待帧数
        self.combo_text = ""  # 合并提示文字
        self.combo_timer = 0  # 合并提示计时器

    def get_next_fruit_type(self):
        """获取下一个水果类型（限制为小水果）"""
        # 前6种水果可被随机选中
        max_type = min(5, len(FRUIT_TYPES) - 1)
        return random.randint(0, max_type)

    def drop_fruit(self):
        """释放水果"""
        if self.game_over or not self.can_drop:
            return

        # 检查释放位置是否被占用
        for f in self.fruits:
            dist = math.hypot(self.drop_x - f.x, CEILING_Y - f.y)
            if dist < f.radius + FRUIT_TYPES[self.next_type][1] + 5:
                return  # 位置被占用

        new_fruit = Fruit(self.next_type, self.drop_x, CEILING_Y)
        self.fruits.append(new_fruit)
        self.next_type = self.get_next_fruit_type()
        self.can_drop = False
        self.wait_frames = 15  # 释放后短暂等待

    def check_wall_collision(self, fruit):
        """检测墙壁碰撞"""
        # 左墙
        if fruit.x - fruit.radius < WALL_LEFT:
            fruit.x = WALL_LEFT + fruit.radius
            fruit.vx = -fruit.vx * COLLISION_RESTITUTION
        # 右墙
        if fruit.x + fruit.radius > WALL_RIGHT:
            fruit.x = WALL_RIGHT - fruit.radius
            fruit.vx = -fruit.vx * COLLISION_RESTITUTION
        # 底部
        if fruit.y + fruit.radius > WALL_BOTTOM:
            fruit.y = WALL_BOTTOM - fruit.radius
            fruit.vy = -fruit.vy * COLLISION_RESTITUTION
            # 地面摩擦力
            fruit.vx *= 0.9

    def check_fruit_collision(self, a, b):
        """检测两个水果之间的碰撞"""
        dx = b.x - a.x
        dy = b.y - a.y
        dist = math.hypot(dx, dy)
        min_dist = a.radius + b.radius

        if dist == 0 or dist >= min_dist:
            return False

        # 计算重叠量
        overlap = min_dist - dist
        nx = dx / dist
        ny = dy / dist

        # 分开两个水果
        b.x += nx * overlap / 2
        b.y += ny * overlap / 2
        a.x -= nx * overlap / 2
        a.y -= ny * overlap / 2

        # 交换速度分量（弹性碰撞简化）
        rel_vx = a.vx - b.vx
        rel_vy = a.vy - b.vy
        rel_vn = rel_vx * nx + rel_vy * ny

        if rel_vn > 0:
            impulse = rel_vn * COLLISION_DAMPING
            a.vx -= impulse * nx
            a.vy -= impulse * ny
            b.vx += impulse * nx
            b.vy += impulse * ny

        return True

    def check_merge(self, a, b):
        """检测两个水果是否可以合并"""
        if a.type_idx != b.type_idx:
            return False
        if a.type_idx >= len(FRUIT_TYPES) - 1:
            return False  # 已经是最大水果，不能再合并
        if a.merged or b.merged:
            return False

        dx = b.x - a.x
        dy = b.y - a.y
        dist = math.hypot(dx, dy)
        # 合并距离比碰撞距离稍小
        min_dist = a.radius + b.radius - 4

        if dist < min_dist or dist < 5:
            return True
        return False

    def perform_merge(self, a, b):
        """执行合并"""
        new_type = a.type_idx + 1
        new_radius = FRUIT_TYPES[new_type][1]

        # 新水果在两者中间生成
        new_x = (a.x + b.x) / 2
        new_y = (a.y + b.y) / 2

        # 合并速度（向上微弹）
        new_vx = (a.vx + b.vx) / 2
        new_vy = (a.vy + b.vy) / 2 - 2

        new_fruit = Fruit(new_type, new_x, new_y, new_vx, new_vy)
        a.merged = True
        b.merged = True

        self.fruits.append(new_fruit)
        self.score += FRUIT_TYPES[new_type][3]
        self.merge_count += 1

        # 显示合并提示
        if new_type >= 8:
            self.combo_text = f"合成{FRUIT_TYPES[new_type][0]}! +{FRUIT_TYPES[new_type][3]}分"
        elif new_type >= 5:
            self.combo_text = f"合并成功! +{FRUIT_TYPES[new_type][3]}分"
        else:
            self.combo_text = f"+{FRUIT_TYPES[new_type][3]}分"
        self.combo_timer = 60

    def check_game_over(self):
        """检查游戏是否结束（水果超出天花板）"""
        for f in self.fruits:
            if f.y - f.radius < CEILING_Y + 20 and f.static_frames > 10:
                self.game_over = True
                return True
        return False

    def update(self):
        """更新游戏状态"""
        if self.game_over:
            return

        # 等待帧计数
        if self.wait_frames > 0:
            self.wait_frames -= 1
            if self.wait_frames == 0:
                self.can_drop = True

        # 更新水果物理
        for f in self.fruits:
            f.update()
            self.check_wall_collision(f)

        # 水果间碰撞检测
        for i in range(len(self.fruits)):
            for j in range(i + 1, len(self.fruits)):
                a = self.fruits[i]
                b = self.fruits[j]
                if a.merged or b.merged:
                    continue
                self.check_fruit_collision(a, b)

        # 合并检测
        merges = []
        for i in range(len(self.fruits)):
            for j in range(i + 1, len(self.fruits)):
                a = self.fruits[i]
                b = self.fruits[j]
                if a.merged or b.merged:
                    continue
                if self.check_merge(a, b):
                    merges.append((i, j))

        # 执行合并（从后往前防止索引变化）
        for i, j in reversed(merges):
            a = self.fruits[i]
            b = self.fruits[j]
            if not a.merged and not b.merged:
                self.perform_merge(a, b)

        # 移除已合并的水果
        self.fruits = [f for f in self.fruits if not f.merged]

        # 合并计时器
        if self.combo_timer > 0:
            self.combo_timer -= 1

        # 检查游戏结束
        self.check_game_over()

    def draw_bowl(self):
        """绘制容器"""
        # 底部
        pygame.draw.rect(self.screen, (80, 60, 40),
                         (WALL_LEFT, WALL_BOTTOM, WALL_RIGHT - WALL_LEFT, 10))
        # 左墙
        pygame.draw.rect(self.screen, (80, 60, 40),
                         (WALL_LEFT - 5, CEILING_Y, 5, WALL_BOTTOM - CEILING_Y))
        # 右墙
        pygame.draw.rect(self.screen, (80, 60, 40),
                         (WALL_RIGHT, CEILING_Y, 5, WALL_BOTTOM - CEILING_Y))
        # 天花板线（游戏结束线）
        pygame.draw.line(self.screen, (255, 50, 50),
                         (WALL_LEFT - 5, CEILING_Y),
                         (WALL_RIGHT + 5, CEILING_Y), 3)
        # 天花板线标签
        label = self.font.render("GAME OVER LINE", True, (255, 50, 50))
        self.screen.blit(label, (WALL_LEFT + 20, CEILING_Y - 30))

    def draw_preview(self):
        """绘制预览水果（跟随鼠标）"""
        if self.game_over or not self.can_drop:
            return

        # 绘制虚线指示下落位置
        if self.drop_x:
            pygame.draw.line(self.screen, (200, 200, 200, 100),
                             (self.drop_x, CEILING_Y + 20),
                             (self.drop_x, WALL_BOTTOM), 1,
                             )

        # 预览水果
        next_type = self.next_type
        radius = FRUIT_TYPES[next_type][1]
        color = FRUIT_TYPES[next_type][2]

        # 半透明预览
        preview_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(preview_surf, (*color, PREVIEW_ALPHA),
                           (radius, radius), radius)
        pygame.draw.circle(preview_surf, (255, 255, 255, 60),
                           (radius, radius), radius, 2)
        self.screen.blit(preview_surf,
                         (self.drop_x - radius, CEILING_Y - radius))

    def draw_hud(self):
        """绘制界面信息"""
        # 分数
        score_text = self.font.render(f"得分: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))

        # 下一个水果提示
        next_label = self.font.render("下一个:", True, (200, 200, 200))
        self.screen.blit(next_label, (10, 40))

        next_type = self.next_type
        next_radius = FRUIT_TYPES[next_type][1]
        next_color = FRUIT_TYPES[next_type][2]
        pygame.draw.circle(self.screen, next_color,
                           (60, 72), next_radius)
        pygame.draw.circle(self.screen, (255, 255, 255, 100),
                           (60, 72), next_radius, 2)

        # 水果数量
        count_text = self.font.render(f"水果: {len(self.fruits)}", True, (200, 200, 200))
        self.screen.blit(count_text, (10, 110))

        # 合并提示
        if self.combo_timer > 0:
            combo_surf = self.big_font.render(self.combo_text, True,
                                              (255, 255, 100))
            combo_alpha = min(255, self.combo_timer * 4)
            combo_surf.set_alpha(combo_alpha)
            text_rect = combo_surf.get_rect(center=(SCREEN_WIDTH // 2, 300))
            self.screen.blit(combo_surf, text_rect)

    def draw_game_over(self):
        """绘制游戏结束画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # 标题
        title = self.title_font.render("游戏结束", True, (255, 100, 100))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        self.screen.blit(title, title_rect)

        # 分数
        score_text = self.big_font.render(f"最终得分: {self.score}", True,
                                          (255, 255, 100))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        self.screen.blit(score_text, score_rect)

        # 合并次数
        merge_text = self.font.render(f"合并次数: {self.merge_count}", True,
                                      (200, 200, 200))
        merge_rect = merge_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        self.screen.blit(merge_text, merge_rect)

        # 提示
        hint = self.font.render("按 R 键重新开始", True, (200, 200, 200))
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        self.screen.blit(hint, hint_rect)

    def draw(self):
        """绘制整个游戏画面"""
        self.screen.fill((30, 30, 40))  # 深色背景

        # 绘制容器区域背景
        container_rect = pygame.Rect(WALL_LEFT, CEILING_Y,
                                     WALL_RIGHT - WALL_LEFT, WALL_BOTTOM - CEILING_Y)
        pygame.draw.rect(self.screen, (50, 45, 55), container_rect)
        pygame.draw.rect(self.screen, (60, 55, 65), container_rect, 1)

        self.draw_bowl()

        # 绘制所有水果
        for f in self.fruits:
            f.draw(self.screen)

        self.draw_preview()
        self.draw_hud()

        if self.game_over:
            self.draw_game_over()

        # 操作提示
        if not self.game_over:
            hint = self.font.render("点击鼠标释放水果", True, (150, 150, 150))
            self.screen.blit(hint, (SCREEN_WIDTH - 180, 10))

        pygame.display.flip()

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    self.reset_game()
                if event.key == pygame.K_ESCAPE:
                    return False
            if event.type == pygame.MOUSEMOTION:
                # 更新释放位置（限制在容器内）
                mx = event.pos[0]
                self.drop_x = max(WALL_LEFT + 20, min(WALL_RIGHT - 20, mx))
            if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                self.drop_fruit()
        return True

    def run(self):
        """主游戏循环"""
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()


# ==================== 入口 ====================
if __name__ == "__main__":
    game = SuikaGame()
    game.run()