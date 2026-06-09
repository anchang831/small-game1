"""
推箱子 (Sokoban) - 经典益智游戏
使用 Pygame 实现, 单文件运行, 无外部依赖

操作说明:
  - 方向键/ WASD : 移动
  - Z / U       : 撤回一步
  - R           : 重置当前关卡
  - N           : 下一关
  - P           : 上一关
  - ESC         : 退出

作者: AI Game Generator
日期: 2026-06-09
"""

import pygame
import sys

# ---- 颜色常量 ----
COLORS = {
    "floor":    (255, 255, 255),   # 白色地板
    "wall":     (100, 100, 100),   # 灰色墙壁
    "box":      (210, 150, 50),    # 橙色箱子
    "target":   (255, 80, 80),     # 红色目标点
    "player":   (50, 130, 220),    # 蓝色玩家
    "box_done": (50, 200, 80),     # 绿色箱子 (到位)
    "bg":       (30, 30, 35),      # 深色背景
    "text":     (240, 240, 240),   # 浅色文字
    "panel":    (45, 45, 55),      # 信息面板
}

# ---- 关卡地图 ----
# 编码: 0=地板, 1=墙, 2=箱子, 3=目标, 4=玩家, 5=箱子到位, 6=玩家在目标
# 每关格式: (地图二维列表, 名称)
LEVELS = [
    # 关卡 1 - 入门
    (
        [
            [1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 1],
            [1, 4, 2, 3, 0, 1],
            [1, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1],
        ],
        "第 1 关 - 初入仓库"
    ),
    # 关卡 2
    (
        [
            [1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 1],
            [1, 4, 2, 0, 0, 0, 1],
            [1, 0, 0, 0, 3, 0, 1],
            [1, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1],
        ],
        "第 2 关 - 直线推运"
    ),
    # 关卡 3
    (
        [
            [1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 1],
            [1, 0, 2, 0, 0, 0, 1],
            [1, 0, 0, 4, 2, 0, 1],
            [1, 0, 0, 3, 0, 0, 1],
            [1, 0, 0, 3, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1],
        ],
        "第 3 关 - 双箱入洞"
    ),
    # 关卡 4
    (
        [
            [1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 2, 0, 0, 2, 0, 1],
            [1, 0, 0, 4, 0, 0, 0, 1],
            [1, 0, 0, 3, 0, 0, 0, 1],
            [1, 0, 0, 3, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1],
        ],
        "第 4 关 - 左右开弓"
    ),
    # 关卡 5 - 经典
    (
        [
            [1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 1],
            [1, 0, 2, 0, 0, 0, 1],
            [1, 0, 4, 2, 0, 0, 1],
            [1, 0, 0, 0, 3, 0, 1],
            [1, 0, 0, 3, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1],
        ],
        "第 5 关 - 拐角难题"
    ),
    # 关卡 6
    (
        [
            [1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 2, 0, 3, 2, 0, 1],
            [1, 0, 0, 4, 0, 0, 0, 1],
            [1, 0, 0, 0, 3, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 2, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1],
        ],
        "第 6 关 - 三角布局"
    ),
    # 关卡 7
    (
        [
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 2, 0, 0, 2, 0, 0, 1],
            [1, 0, 0, 0, 4, 0, 0, 0, 1],
            [1, 0, 0, 0, 3, 0, 0, 0, 1],
            [1, 0, 2, 0, 3, 0, 2, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
        "第 7 关 - 交错纵横"
    ),
    # 关卡 8 - 困难
    (
        [
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 2, 0, 2, 0, 2, 0, 1],
            [1, 0, 0, 4, 0, 0, 0, 0, 1],
            [1, 0, 3, 0, 3, 0, 3, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
        "第 8 关 - 三箱齐下"
    ),
]


class Sokoban:
    """推箱子游戏主类"""

    CELL_SIZE = 70       # 每格像素
    INFO_HEIGHT = 80     # 底部信息栏高度

    def __init__(self):
        """初始化游戏"""
        pygame.init()
        # 根据最大关卡尺寸计算窗口大小
        self.max_cols = max(len(row) for level, _ in LEVELS for row in level)
        self.max_rows = max(len(level) for level, _ in LEVELS)
        self.win_width = self.max_cols * self.CELL_SIZE
        self.win_height = self.max_rows * self.CELL_SIZE + self.INFO_HEIGHT

        self.screen = pygame.display.set_mode((self.win_width, self.win_height))
        pygame.display.set_caption("推箱子 Sokoban")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("simhei, notosanscjk, microsoftyahei, sans-serif", 24)
        self.big_font = pygame.font.SysFont("simhei, notosanscjk, microsoftyahei, sans-serif", 48)

        self.current_level = 0
        self.moves = 0
        self.undo_stack = []      # 存储 (玩家之前位置, 箱子位置) 用于撤回
        self.message = ""
        self.message_timer = 0
        self.levels_total = len(LEVELS)

        self.reset_level()

    def reset_level(self):
        """重置当前关卡到初始状态"""
        level_data, _ = LEVELS[self.current_level]
        # 深拷贝地图
        self.grid = [row[:] for row in level_data]
        self.moves = 0
        self.undo_stack.clear()
        self.find_player()
        self.calc_targets()

    def calc_targets(self):
        """计算目标点总数和当前位置的已到位箱子数"""
        self.total_targets = 0
        for row in self.grid:
            for cell in row:
                if cell == 3 or cell == 6:
                    self.total_targets += 1

    def find_player(self):
        """查找玩家位置并保存"""
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell == 4 or cell == 6:  # 玩家或玩家在目标上
                    self.player_x = x
                    self.player_y = y
                    return

    def is_won(self):
        """检查是否所有箱子都已到位"""
        boxes_placed = 0
        for row in self.grid:
            for cell in row:
                if cell == 5:  # 箱子在目标上
                    boxes_placed += 1
        return boxes_placed == self.total_targets and self.total_targets > 0

    def move(self, dx, dy):
        """尝试移动玩家, dx/dy 为方向偏移"""
        nx = self.player_x + dx
        ny = self.player_y + dy

        # 边界/墙壁检查
        if not (0 <= ny < len(self.grid) and 0 <= nx < len(self.grid[ny])):
            return False
        if self.grid[ny][nx] == 1:
            return False

        # 箱子处理
        if self.grid[ny][nx] in (2, 5):  # 箱子或已到位箱子
            bx = nx + dx
            by = ny + dy
            if not (0 <= by < len(self.grid) and 0 <= bx < len(self.grid[by])):
                return False
            if self.grid[by][bx] in (1, 2, 5):
                return False

            # 保存撤回信息: (玩家旧位置, 箱子旧位置, 箱子新位置旧值)
            self.undo_stack.append((
                (self.player_x, self.player_y, self.grid[self.player_y][self.player_x]),
                (nx, ny, self.grid[ny][nx]),
                (bx, by, self.grid[by][bx]),
            ))

            # 移动箱子
            if self.grid[by][bx] == 3:
                self.grid[by][bx] = 5  # 箱子推到目标
            else:
                self.grid[by][bx] = 2

            # 移除旧箱子
            if self.grid[ny][nx] == 5:
                self.grid[ny][nx] = 3  # 原来箱子的位置是目标
            else:
                self.grid[ny][nx] = 0

            # 移动玩家
            old_cell = self.grid[self.player_y][self.player_x]
            self.grid[self.player_y][self.player_x] = 3 if old_cell == 6 else 0
            if self.grid[ny][nx] == 3:
                self.grid[ny][nx] = 6  # 玩家站在目标上
                self.player_x, self.player_y = nx, ny
            else:
                self.grid[ny][nx] = 4
                self.player_x, self.player_y = nx, ny
        else:
            # 普通移动 (没有箱子)
            self.undo_stack.append((
                (self.player_x, self.player_y, self.grid[self.player_y][self.player_x]),
                (nx, ny, self.grid[ny][nx]),
                None,
            ))

            old_cell = self.grid[self.player_y][self.player_x]
            self.grid[self.player_y][self.player_x] = 3 if old_cell == 6 else 0
            if self.grid[ny][nx] == 3:
                self.grid[ny][nx] = 6
            else:
                self.grid[ny][nx] = 4
            self.player_x, self.player_y = nx, ny

        self.moves += 1

        # 检查胜利
        if self.is_won():
            self.message = "🎉 过关！按 N 进入下一关"
            self.message_timer = 300

        return True

    def undo(self):
        """撤回上一步操作"""
        if not self.undo_stack:
            return

        data = self.undo_stack.pop()
        player_data = data[0]
        box_data = data[1]
        box_new_data = data[2]

        # 恢复箱子新位置
        if box_new_data is not None:
            bx, by, bval = box_new_data
            self.grid[by][bx] = bval

        # 恢复箱子旧位置
        px_before, py_before, pval = player_data
        bx_old, by_old, bval_old = box_data
        self.grid[by_old][bx_old] = bval_old

        # 恢复玩家位置
        self.grid[py_before][px_before] = pval
        self.player_x, self.player_y = px_before, py_before

        self.moves -= 1
        if self.moves < 0:
            self.moves = 0

    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(COLORS["bg"])

        offset_x = (self.win_width - len(self.grid[0]) * self.CELL_SIZE) // 2
        offset_y = (self.win_height - self.INFO_HEIGHT - len(self.grid) * self.CELL_SIZE) // 2

        # 绘制网格和元素
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                rect = pygame.Rect(
                    offset_x + x * self.CELL_SIZE,
                    offset_y + y * self.CELL_SIZE,
                    self.CELL_SIZE, self.CELL_SIZE
                )

                if cell == 1:
                    # 墙壁 - 深灰色立体效果
                    pygame.draw.rect(self.screen, (80, 80, 90), rect)
                    pygame.draw.rect(self.screen, (60, 60, 70), rect, 2)
                    # 砖纹
                    for i in range(0, self.CELL_SIZE, 10):
                        pygame.draw.line(self.screen, (70, 70, 80),
                                         (rect.x, rect.y + i),
                                         (rect.right, rect.y + i), 1)
                    for i in range(0, self.CELL_SIZE, 15):
                        offset = 5 if (i // 15) % 2 == 0 else 0
                        pygame.draw.line(self.screen, (70, 70, 80),
                                         (rect.x + i + offset, rect.y),
                                         (rect.x + i + offset, rect.bottom), 1)
                else:
                    # 地板
                    lighter = (245, 245, 240) if (x + y) % 2 == 0 else (235, 235, 225)
                    pygame.draw.rect(self.screen, lighter, rect)
                    pygame.draw.rect(self.screen, (220, 220, 210), rect, 1)

                if cell == 3 or cell == 6:
                    # 目标点 - 红色菱形
                    cx = rect.centerx
                    cy = rect.centery
                    r = self.CELL_SIZE // 6
                    points = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
                    pygame.draw.polygon(self.screen, COLORS["target"], points)
                    pygame.draw.polygon(self.screen, (200, 40, 40), points, 2)

                if cell == 2:
                    # 箱子 - 立体橙色
                    margin = 6
                    box_rect = rect.inflate(-margin * 2, -margin * 2)
                    pygame.draw.rect(self.screen, COLORS["box"], box_rect, border_radius=5)
                    pygame.draw.rect(self.screen, (180, 120, 30), box_rect, 2, border_radius=5)
                    # 高光
                    hl_rect = box_rect.inflate(-8, -8)
                    pygame.draw.rect(self.screen, (230, 180, 80), hl_rect, border_radius=3)

                elif cell == 5:
                    # 箱子到位 - 立体绿色 + 标记
                    margin = 6
                    box_rect = rect.inflate(-margin * 2, -margin * 2)
                    pygame.draw.rect(self.screen, COLORS["box_done"], box_rect, border_radius=5)
                    pygame.draw.rect(self.screen, (30, 160, 50), box_rect, 2, border_radius=5)
                    # 对勾标记
                    cx, cy = rect.centerx, rect.centery
                    pts = [(cx - 10, cy), (cx - 3, cy + 8), (cx + 12, cy - 8)]
                    pygame.draw.lines(self.screen, (255, 255, 255), False, pts, 3)

                if cell == 4 or cell == 6:
                    # 玩家 - 蓝色圆形
                    cx = rect.centerx
                    cy = rect.centery
                    r = self.CELL_SIZE // 2 - 8
                    pygame.draw.circle(self.screen, COLORS["player"], (cx, cy), r)
                    pygame.draw.circle(self.screen, (30, 100, 200), (cx, cy), r, 2)
                    # 眼睛
                    eye_offset = r // 3
                    eye_r = 3
                    pygame.draw.circle(self.screen, (255, 255, 255),
                                     (cx - eye_offset, cy - eye_offset // 2), eye_r)
                    pygame.draw.circle(self.screen, (255, 255, 255),
                                     (cx + eye_offset, cy - eye_offset // 2), eye_r)
                    pygame.draw.circle(self.screen, (0, 0, 0),
                                     (cx - eye_offset, cy - eye_offset // 2), eye_r // 2)
                    pygame.draw.circle(self.screen, (0, 0, 0),
                                     (cx + eye_offset, cy - eye_offset // 2), eye_r // 2)

        # ---- 底部信息栏 ----
        panel_rect = pygame.Rect(0, self.win_height - self.INFO_HEIGHT,
                                 self.win_width, self.INFO_HEIGHT)
        pygame.draw.rect(self.screen, COLORS["panel"], panel_rect)
        pygame.draw.line(self.screen, (70, 70, 80),
                        (0, panel_rect.top), (self.win_width, panel_rect.top), 2)

        level_name = LEVELS[self.current_level][1]
        info_lines = [
            f"{level_name}   步数: {self.moves}",
            "方向键/WASD移动 | Z撤回 | R重置 | N/P切换关卡 | ESC退出"
        ]

        y_text = panel_rect.top + 15
        if self.message and self.message_timer > 0:
            # 显示胜利消息
            msg_surf = self.big_font.render(self.message, True, (255, 220, 50))
            msg_rect = msg_surf.get_rect(center=(self.win_width // 2, self.win_height // 4))
            self.screen.blit(msg_surf, msg_rect)

        for i, line in enumerate(info_lines):
            text_surf = self.font.render(line, True, COLORS["text"])
            text_rect = text_surf.get_rect(midtop=(self.win_width // 2, y_text))
            self.screen.blit(text_surf, text_rect)
            y_text += 28

        pygame.display.flip()

    def run(self):
        """游戏主循环"""
        running = True
        while running:
            self.clock.tick(30)

            if self.message_timer > 0:
                self.message_timer -= 1
            else:
                self.message = ""

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    # 方向键 / WASD
                    dx, dy = 0, 0
                    if event.key in (pygame.K_UP, pygame.K_w):
                        dy = -1
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        dy = 1
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        dx = -1
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        dx = 1
                    elif event.key in (pygame.K_z, pygame.K_u):
                        self.undo()
                        self.message = ""
                    elif event.key == pygame.K_r:
                        self.reset_level()
                        self.message = ""
                    elif event.key == pygame.K_n:
                        self.current_level = (self.current_level + 1) % self.levels_total
                        self.reset_level()
                        self.message = ""
                    elif event.key == pygame.K_p:
                        self.current_level = (self.current_level - 1) % self.levels_total
                        self.reset_level()
                        self.message = ""
                    elif event.key == pygame.K_ESCAPE:
                        running = False

                    if (dx != 0 or dy != 0) and not self.is_won():
                        self.move(dx, dy)

            self.draw()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Sokoban()
    game.run()