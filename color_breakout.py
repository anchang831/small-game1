"""
颜色打砖块 (Color Breakout)
使用 Python tkinter 编写，完整可运行，无需外部资源
规则: 不同颜色的砖块只能被对应颜色的球击碎，改变球的颜色匹配砖块，获得更高分数
控制: 左右方向键移动挡板，空格键改变球的颜色
作者: AI Game Generator
日期: 2026-07-22
"""

import tkinter as tk
import random
from typing import List, Tuple

# 游戏常量
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
PADDLE_HEIGHT = 15
PADDLE_WIDTH = 100
PADDLE_SPEED = 15
BALL_RADIUS = 8
BALL_SPEED_BASE = 5
BRICK_ROWS = 5
BRICK_COLS = 10
BRICK_HEIGHT = 20
BRICK_WIDTH = 70
BRICK_GAP = 5
BRICK_TOP_MARGIN = 80
BRICK_LEFT_MARGIN = 25

# 颜色定义
COLORS = {
    'red': '#ff4444',
    'blue': '#4444ff',
    'green': '#44ff44',
    'yellow': '#ffff44',
    'purple': '#ff44ff'
}
COLOR_LIST = list(COLORS.keys())

class Brick:
    """砖块类"""
    def __init__(self, x: int, y: int, color_name: str):
        self.x = x
        self.y = y
        self.width = BRICK_WIDTH
        self.height = BRICK_HEIGHT
        self.color_name = color_name
        self.color_hex = COLORS[color_name]
        self.active = True

    def get_bbox(self) -> Tuple[int, int, int, int]:
        """获取边界框"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    def contains_point(self, x: float, y: float) -> bool:
        """检查点是否在砖块内"""
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)

class Game:
    """主游戏类"""
    def __init__(self, master):
        self.master = master
        master.title("颜色打砖块 - Color Breakout")

        # 创建画布
        self.canvas = tk.Canvas(
            master, width=WINDOW_WIDTH, height=WINDOW_HEIGHT,
            bg='#1a1a1a', highlightthickness=0
        )
        self.canvas.pack()

        # 游戏状态
        self.score = 0
        self.lives = 3
        self.game_running = False
        self.paused = False

        # 挡板
        self.paddle_x = WINDOW_WIDTH // 2 - PADDLE_WIDTH // 2
        self.paddle_y = WINDOW_HEIGHT - 40
        self.paddle_width = PADDLE_WIDTH

        # 球
        self.ball_x = WINDOW_WIDTH // 2
        self.ball_y = self.paddle_y - BALL_RADIUS
        self.ball_dx = 0
        self.ball_dy = 0
        self.ball_color = 'red'

        # 砖块列表
        self.bricks: List[Brick] = []

        # 按键状态
        self.keys_pressed = set()

        # 绑定事件
        master.bind('<Left>', self.on_key_down)
        master.bind('<Right>', self.on_key_down)
        master.bind('<space>', self.on_key_down)
        master.bind('<KeyRelease>', self.on_key_up)

        # 开始按钮
        self.start_button = tk.Button(
            master, text="开始游戏", command=self.start_game,
            font=('Arial', 14), bg='#44aa44', fg='white'
        )
        self.start_button_window = self.canvas.create_window(
            WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 80,
            window=self.start_button
        )

        # 绘制欢迎界面
        self.draw_welcome()

        # 游戏循环
        self.update()

    def draw_welcome(self):
        """绘制欢迎界面"""
        self.canvas.delete("all")
        title = "颜色打砖块\n(Color Breakout)"
        self.canvas.create_text(
            WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3,
            text=title, fill='white', font=('Arial', 28, 'bold'),
            justify=tk.CENTER
        )

        rules = [
            "规则说明:",
            "• 只有相同颜色的球才能击碎对应颜色的砖块",
            "• 按空格键改变球的颜色",
            "• 左右方向键移动挡板",
            "• 击碎所有砖块进入下一关"
        ]
        y_offset = WINDOW_HEIGHT // 3 + 80
        for rule in rules:
            self.canvas.create_text(
                WINDOW_WIDTH // 2, y_offset,
                text=rule, fill='#cccccc', font=('Arial', 12),
                justify=tk.CENTER
            )
            y_offset += 25

    def start_game(self):
        """开始新游戏"""
        self.score = 0
        self.lives = 3
        self.level = 1
        self.game_running = True
        self.paused = False
        self.start_button.pack_forget()
        self.create_level()
        self.reset_ball()

    def create_level(self):
        """创建当前关卡砖块"""
        self.bricks.clear()
        speed_increase = (self.level - 1) * 0.5

        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                x = BRICK_LEFT_MARGIN + col * (BRICK_WIDTH + BRICK_GAP)
                y = BRICK_TOP_MARGIN + row * (BRICK_HEIGHT + BRICK_GAP)
                color = random.choice(COLOR_LIST)
                brick = Brick(x, y, color)
                self.bricks.append(brick)

    def reset_ball(self):
        """重置球位置和速度"""
        self.ball_x = WINDOW_WIDTH // 2
        self.ball_y = self.paddle_y - BALL_RADIUS
        angle = random.uniform(-60, 60)
        import math
        rad = math.radians(angle)
        speed = BALL_SPEED_BASE + (self.level - 1) * 0.8
        self.ball_dx = speed * math.sin(rad)
        self.ball_dy = -speed * math.cos(rad)
        # 确保初始方向向上
        if self.ball_dy > 0:
            self.ball_dy = -self.ball_dy

    def on_key_down(self, event):
        """按键按下"""
        if event.keysym in ['Left', 'Right', 'space']:
            self.keys_pressed.add(event.keysym)
        if event.keysym == 'space' and self.game_running:
            # 循环切换颜色
            current_idx = COLOR_LIST.index(self.ball_color)
            next_idx = (current_idx + 1) % len(COLOR_LIST)
            self.ball_color = COLOR_LIST[next_idx]

    def on_key_up(self, event):
        """按键释放"""
        if event.keysym in self.keys_pressed:
            self.keys_pressed.discard(event.keysym)

    def update_paddle(self):
        """更新挡板位置"""
        if 'Left' in self.keys_pressed:
            self.paddle_x -= PADDLE_SPEED
        if 'Right' in self.keys_pressed:
            self.paddle_x += PADDLE_SPEED

        # 边界检查
        if self.paddle_x < 0:
            self.paddle_x = 0
        if self.paddle_x + self.paddle_width > WINDOW_WIDTH:
            self.paddle_x = WINDOW_WIDTH - self.paddle_width

    def check_collisions(self):
        """检查所有碰撞"""
        # 墙碰撞
        if self.ball_x - BALL_RADIUS <= 0:
            self.ball_x = BALL_RADIUS + 1
            self.ball_dx = -self.ball_dx
        if self.ball_x + BALL_RADIUS >= WINDOW_WIDTH:
            self.ball_x = WINDOW_WIDTH - BALL_RADIUS - 1
            self.ball_dx = -self.ball_dx
        if self.ball_y - BALL_RADIUS <= 0:
            self.ball_y = BALL_RADIUS + 1
            self.ball_dy = -self.ball_dy

        # 底部掉球 - 生命减少
        if self.ball_y + BALL_RADIUS >= WINDOW_HEIGHT:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over()
            else:
                self.reset_ball()
            return

        # 挡板碰撞
        paddle_top = self.paddle_y
        paddle_bottom = self.paddle_y + PADDLE_HEIGHT
        paddle_left = self.paddle_x
        paddle_right = self.paddle_x + self.paddle_width

        if (paddle_left <= self.ball_x <= paddle_right and
            paddle_top <= self.ball_y + BALL_RADIUS <= paddle_bottom):
            # 反射，根据击打位置改变水平速度
            hit_pos = (self.ball_x - self.paddle_x) / self.paddle_width
            import math
            max_angle = math.radians(60)
            angle = (hit_pos - 0.5) * 2 * max_angle
            speed = math.hypot(self.ball_dx, self.ball_dy)
            self.ball_dx = speed * math.sin(angle)
            self.ball_dy = -abs(speed * math.cos(angle))
            self.ball_y = paddle_top - BALL_RADIUS - 1

        # 砖块碰撞
        for brick in self.bricks:
            if not brick.active:
                continue

            if self.check_ball_brick_collision(brick):
                # 颜色匹配才能击碎
                if brick.color_name == self.ball_color:
                    brick.active = False
                    self.score += 10 * self.level
                # 不管颜色是否匹配都反弹
                self.reflect_ball_from_brick(brick)
                break

        # 检查关卡完成
        active_bricks = sum(1 for b in self.bricks if b.active)
        if active_bricks == 0:
            self.next_level()

    def check_ball_brick_collision(self, brick: Brick) -> bool:
        """检查球与砖块碰撞"""
        # 找到球最近点到矩形中心
        closest_x = max(brick.x, min(self.ball_x, brick.x + brick.width))
        closest_y = max(brick.y, min(self.ball_y, brick.y + brick.height))

        distance_x = self.ball_x - closest_x
        distance_y = self.ball_y - closest_y
        distance_squared = distance_x ** 2 + distance_y ** 2

        return distance_squared <= BALL_RADIUS ** 2

    def reflect_ball_from_brick(self, brick: Brick):
        """从砖块反弹球"""
        # 确定碰撞方向
        ball_center_x = self.ball_x
        ball_center_y = self.ball_y

        brick_center_x = brick.x + brick.width / 2
        brick_center_y = brick.y + brick.height / 2

        dx = ball_center_x - brick_center_x
        dy = ball_center_y - brick_center_y

        # 判断从哪个方向碰撞
        overlap_x = brick.width / 2 + BALL_RADIUS - abs(dx)
        overlap_y = brick.height / 2 + BALL_RADIUS - abs(dy)

        if overlap_x < overlap_y:
            # 水平碰撞
            self.ball_dx = -self.ball_dx
            if dx > 0:
                self.ball_x = brick.x + brick.width + BALL_RADIUS + 1
            else:
                self.ball_x = brick.x - BALL_RADIUS - 1
        else:
            # 垂直碰撞
            self.ball_dy = -self.ball_dy
            if dy > 0:
                self.ball_y = brick.y + brick.height + BALL_RADIUS + 1
            else:
                self.ball_y = brick.y - BALL_RADIUS - 1

    def next_level(self):
        """进入下一关"""
        self.level += 1
        self.score += self.level * 100  # 关卡奖励
        self.create_level()
        self.reset_ball()

    def game_over(self):
        """游戏结束"""
        self.game_running = False
        self.draw_game_over()

    def draw_game_over(self):
        """绘制游戏结束界面"""
        self.canvas.create_rectangle(
            WINDOW_WIDTH // 4, WINDOW_HEIGHT // 3,
            WINDOW_WIDTH * 3 // 4, WINDOW_HEIGHT * 2 // 3,
            fill='#000000', outline='white', stipple='gray50'
        )
        self.canvas.create_text(
            WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3 + 40,
            text="游戏结束\nGame Over", fill='white',
            font=('Arial', 24, 'bold'), justify=tk.CENTER
        )
        self.canvas.create_text(
            WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10,
            text=f"最终得分: {self.score}\n点击下方按钮重新开始",
            fill='#cccccc', font=('Arial', 14), justify=tk.CENTER
        )
        self.start_button = tk.Button(
            self.master, text="重新开始", command=self.start_game,
            font=('Arial', 14), bg='#44aa44', fg='white'
        )
        self.canvas.create_window(
            WINDOW_WIDTH // 2, WINDOW_HEIGHT * 2 // 3 + 20,
            window=self.start_button
        )

    def update(self):
        """游戏主循环"""
        if self.game_running and not self.paused:
            self.update_paddle()
            self.ball_x += self.ball_dx
            self.ball_y += self.ball_dy
            self.check_collisions()

        self.draw()
        # 60 FPS
        self.master.after(16, self.update)

    def draw(self):
        """绘制所有游戏元素"""
        self.canvas.delete("game")

        # 绘制得分和生命信息
        info_text = f"分数: {self.score}  生命: {self.lives}  关卡: {getattr(self, 'level', 1)}"
        self.canvas.create_text(
            10, 10, anchor='nw', text=info_text,
            fill='white', font=('Arial', 12, 'bold'), tags="game"
        )

        # 绘制当前球颜色提示
        self.canvas.create_text(
            WINDOW_WIDTH // 2, 10,
            text=f"当前颜色: {self.ball_color.upper()} (空格键切换)",
            fill=COLORS[self.ball_color], font=('Arial', 12, 'bold'),
            tags="game"
        )

        # 颜色图例
        legend_y = 30
        for i, color_name in enumerate(COLOR_LIST):
            x = 10 + i * 60
            self.canvas.create_rectangle(
                x, legend_y, x + 40, legend_y + 15,
                fill=COLORS[color_name], outline='white', tags="game"
            )

        # 绘制砖块
        for brick in self.bricks:
            if brick.active:
                x1, y1, x2, y2 = brick.get_bbox()
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=brick.color_hex, outline='#1a1a1a', width=2,
                    tags="game"
                )

        # 绘制挡板
        self.canvas.create_rectangle(
            self.paddle_x, self.paddle_y,
            self.paddle_x + self.paddle_width, self.paddle_y + PADDLE_HEIGHT,
            fill='#ffffff', outline='#888888', tags="game"
        )

        # 绘制球
        self.canvas.create_oval(
            self.ball_x - BALL_RADIUS, self.ball_y - BALL_RADIUS,
            self.ball_x + BALL_RADIUS, self.ball_y + BALL_RADIUS,
            fill=COLORS[self.ball_color], outline='white', tags="game"
        )

        # 游戏暂停提示
        if self.paused and self.game_running:
            self.canvas.create_text(
                WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2,
                text="PAUSED", fill='yellow', font=('Arial', 32, 'bold'),
                tags="game"
            )

def main():
    """主函数入口"""
    root = tk.Tk()
    root.resizable(False, False)
    app = Game(root)
    root.mainloop()

if __name__ == "__main__":
    main()
