import tkinter as tk
import random


class PongGame:
    def __init__(self, root):
        self.root = root
        self.root.title("双人乒乓球 - Pong")
        self.root.resizable(False, False)

        self.WIDTH = 800
        self.HEIGHT = 600
        self.PADDLE_WIDTH = 15
        self.PADDLE_HEIGHT = 100
        self.BALL_SIZE = 15
        self.PADDLE_SPEED = 5
        self.BALL_SPEED_X = 4
        self.BALL_SPEED_Y = 4

        self.score_p1 = 0
        self.score_p2 = 0

        self.canvas = tk.Canvas(root, width=self.WIDTH, height=self.HEIGHT, bg="black")
        self.canvas.pack()

        self.score_text = self.canvas.create_text(
            self.WIDTH // 2, 50, text=f"{self.score_p1} : {self.score_p2}",
            fill="white", font=("Arial", 40, "bold")
        )

        self.paddle1 = self.canvas.create_rectangle(
            50, self.HEIGHT // 2 - self.PADDLE_HEIGHT // 2,
            50 + self.PADDLE_WIDTH, self.HEIGHT // 2 + self.PADDLE_HEIGHT // 2,
            fill="white"
        )
        self.paddle2 = self.canvas.create_rectangle(
            self.WIDTH - 50 - self.PADDLE_WIDTH, self.HEIGHT // 2 - self.PADDLE_HEIGHT // 2,
            self.WIDTH - 50, self.HEIGHT // 2 + self.PADDLE_HEIGHT // 2,
            fill="white"
        )

        self.ball = self.canvas.create_oval(
            self.WIDTH // 2 - self.BALL_SIZE // 2, self.HEIGHT // 2 - self.BALL_SIZE // 2,
            self.WIDTH // 2 + self.BALL_SIZE // 2, self.HEIGHT // 2 + self.BALL_SIZE // 2,
            fill="white"
        )

        self.p1_up = False
        self.p1_down = False
        self.p2_up = False
        self.p2_down = False

        self.ball_dx = self.BALL_SPEED_X * random.choice([-1, 1])
        self.ball_dy = self.BALL_SPEED_Y * random.choice([-1, 1])

        self.running = True
        self.setup_controls()
        self.game_loop()

    def setup_controls(self):
        self.root.bind("<w>", lambda e: self.set_paddle1_movement("up", True))
        self.root.bind("<s>", lambda e: self.set_paddle1_movement("down", True))
        self.root.bind("<KeyRelease-w>", lambda e: self.set_paddle1_movement("up", False))
        self.root.bind("<KeyRelease-s>", lambda e: self.set_paddle1_movement("down", False))

        self.root.bind("<Up>", lambda e: self.set_paddle2_movement("up", True))
        self.root.bind("<Down>", lambda e: self.set_paddle2_movement("down", True))
        self.root.bind("<KeyRelease-Up>", lambda e: self.set_paddle2_movement("up", False))
        self.root.bind("<KeyRelease-Down>", lambda e: self.set_paddle2_movement("down", False))

    def set_paddle1_movement(self, direction, is_pressed):
        if direction == "up":
            self.p1_up = is_pressed
        else:
            self.p1_down = is_pressed

    def set_paddle2_movement(self, direction, is_pressed):
        if direction == "up":
            self.p2_up = is_pressed
        else:
            self.p2_down = is_pressed

    def update_paddles(self):
        p1_coords = self.canvas.coords(self.paddle1)
        if self.p1_up and p1_coords[1] > 0:
            self.canvas.move(self.paddle1, 0, -self.PADDLE_SPEED)
        if self.p1_down and p1_coords[3] < self.HEIGHT:
            self.canvas.move(self.paddle1, 0, self.PADDLE_SPEED)

        p2_coords = self.canvas.coords(self.paddle2)
        if self.p2_up and p2_coords[1] > 0:
            self.canvas.move(self.paddle2, 0, -self.PADDLE_SPEED)
        if self.p2_down and p2_coords[3] < self.HEIGHT:
            self.canvas.move(self.paddle2, 0, self.PADDLE_SPEED)

    def update_ball(self):
        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)
        ball_coords = self.canvas.coords(self.ball)

        if ball_coords[1] <= 0 or ball_coords[3] >= self.HEIGHT:
            self.ball_dy *= -1

        p1_coords = self.canvas.coords(self.paddle1)
        p2_coords = self.canvas.coords(self.paddle2)

        if (ball_coords[0] <= p1_coords[2] and
            ball_coords[2] >= p1_coords[0] and
            ball_coords[1] <= p1_coords[3] and
            ball_coords[3] >= p1_coords[1]):
            self.ball_dx = abs(self.ball_dx)

        if (ball_coords[2] >= p2_coords[0] and
            ball_coords[0] <= p2_coords[2] and
            ball_coords[1] <= p2_coords[3] and
            ball_coords[3] >= p2_coords[1]):
            self.ball_dx = -abs(self.ball_dx)

        if ball_coords[0] <= 0:
            self.score_p2 += 1
            self.update_score()
            self.reset_ball()

        if ball_coords[2] >= self.WIDTH:
            self.score_p1 += 1
            self.update_score()
            self.reset_ball()

    def reset_ball(self):
        self.canvas.coords(
            self.ball,
            self.WIDTH // 2 - self.BALL_SIZE // 2,
            self.HEIGHT // 2 - self.BALL_SIZE // 2,
            self.WIDTH // 2 + self.BALL_SIZE // 2,
            self.HEIGHT // 2 + self.BALL_SIZE // 2
        )
        self.ball_dx = self.BALL_SPEED_X * random.choice([-1, 1])
        self.ball_dy = self.BALL_SPEED_Y * random.choice([-1, 1])

    def update_score(self):
        self.canvas.itemconfig(self.score_text, text=f"{self.score_p1} : {self.score_p2}")

    def game_loop(self):
        if self.running:
            self.update_paddles()
            self.update_ball()
            self.root.after(16, self.game_loop)


def main():
    root = tk.Tk()
    game = PongGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
