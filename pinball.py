"""
pinball.py - 弹珠台 (Pinball)
经典弹珠台游戏，控制挡板反弹小球撞击弹珠得分。
操作：
  ← → 控制左右挡板
  空格 蓄力发射小球
  R 重新开始

Date: 2026-06-12
"""

import pygame
import math

# Initialize
pygame.init()
WIDTH, HEIGHT = 480, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pinball - 弹珠台")
clock = pygame.time.Clock()
FPS = 60

# Colors
BLACK = (10, 10, 20)
WHITE = (230, 230, 240)
DARK = (30, 30, 50)
GRAY = (100, 100, 120)
RED = (255, 60, 60)
GREEN = (60, 220, 60)
BLUE = (60, 100, 255)
YELLOW = (255, 220, 60)
PURPLE = (200, 60, 255)
ORANGE = (255, 160, 40)
CYAN = (60, 220, 255)
PINK = (255, 80, 150)

# Physics constants
GRAVITY = 0.15
BALL_RADIUS = 7
MAX_LIVES = 3

# Fonts
FONT_S = pygame.font.Font(None, 22)
FONT_M = pygame.font.Font(None, 32)
FONT_L = pygame.font.Font(None, 52)


class Ball:
    """Main game ball with position, velocity, and physics."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.x = WIDTH - 50
        self.y = HEIGHT - 90
        self.vx = 0.0
        self.vy = 0.0
        self.radius = BALL_RADIUS
        self.active = False  # Whether ball has been launched

    def update(self):
        if not self.active:
            return
        # Gravity
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy
        # Friction
        self.vx *= 0.995
        self.vy *= 0.995

        # Wall collisions (with energy loss)
        if self.x - self.radius < 15:
            self.x = 15 + self.radius
            self.vx = abs(self.vx) * 0.8
        if self.x + self.radius > WIDTH - 15:
            self.x = WIDTH - 15 - self.radius
            self.vx = -abs(self.vx) * 0.8
        if self.y - self.radius < 15:
            self.y = 15 + self.radius
            self.vy = abs(self.vy) * 0.8

    def draw(self):
        if not self.active:
            return
        # Main ball
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius)
        # Highlight for 3D effect
        pygame.draw.circle(screen, (180, 180, 200), (int(self.x) - 2, int(self.y) - 2), self.radius - 3)


class Flipper:
    """Pinball flipper that rotates around a pivot point."""

    def __init__(self, pivot_x, pivot_y, is_left):
        self.pivot_x = pivot_x
        self.pivot_y = pivot_y
        self.is_left = is_left
        self.rest_angle = math.radians(65) if is_left else math.radians(115)
        self.act_angle = math.radians(20) if is_left else math.radians(160)
        self.angle = self.rest_angle
        self.length = 70
        self.width = 12
        self.active = False

    def activate(self, pressed):
        self.active = pressed

    def update(self):
        target = self.act_angle if self.active else self.rest_angle
        self.angle += (target - self.angle) * 0.25

    def get_endpoint(self):
        ex = self.pivot_x + math.cos(self.angle) * self.length
        ey = self.pivot_y - math.sin(self.angle) * self.length
        return ex, ey

    def draw(self):
        ex, ey = self.get_endpoint()
        color = CYAN if self.active else (40, 80, 120)
        pygame.draw.line(screen, color, (self.pivot_x, self.pivot_y), (ex, ey), self.width)
        pygame.draw.line(screen, WHITE, (self.pivot_x, self.pivot_y), (ex, ey), self.width // 3)
        pygame.draw.circle(screen, WHITE, (int(self.pivot_x), int(self.pivot_y)), 4)

    def check_collision(self, ball):
        """Collision between ball (circle) and flipper (line segment)."""
        ex, ey = self.get_endpoint()
        dx = ex - self.pivot_x
        dy = ey - self.pivot_y
        length_sq = dx * dx + dy * dy
        if length_sq == 0:
            return False

        # Project ball center onto the flipper line segment
        t = ((ball.x - self.pivot_x) * dx + (ball.y - self.pivot_y) * dy) / length_sq
        t = max(0.0, min(1.0, t))
        closest_x = self.pivot_x + t * dx
        closest_y = self.pivot_y + t * dy

        dist = math.hypot(ball.x - closest_x, ball.y - closest_y)
        if dist >= ball.radius + self.width / 2:
            return False

        # Normal direction from flipper to ball
        if dist > 0:
            nx = (ball.x - closest_x) / dist
            ny = (ball.y - closest_y) / dist
        else:
            nx, ny = 0, -1

        # Push ball out of overlap
        overlap = ball.radius + self.width / 2 - dist
        ball.x += nx * overlap
        ball.y += ny * overlap

        # Reflect velocity and add flipper energy
        dot = ball.vx * nx + ball.vy * ny
        if dot < 0:  # Only reflect when moving toward flipper
            bonus = 4.0 if self.active else 1.5
            ball.vx = (ball.vx - 2 * dot * nx) * 0.9 + nx * bonus
            ball.vy = (ball.vy - 2 * dot * ny) * 0.9 - abs(ny) * bonus

        return True


class Bumper:
    """Circular bumper that bounces the ball and awards points."""

    def __init__(self, x, y, radius, color, points):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.points = points
        self.flash = 0  # Flash timer on hit

    def update(self):
        if self.flash > 0:
            self.flash -= 1

    def check_collision(self, ball):
        dx = ball.x - self.x
        dy = ball.y - self.y
        dist = math.hypot(dx, dy)
        if dist >= ball.radius + self.radius:
            return False

        if dist > 0:
            nx = dx / dist
            ny = dy / dist
        else:
            nx, ny = 0, -1

        # Push ball out
        overlap = ball.radius + self.radius - dist
        ball.x += nx * overlap
        ball.y += ny * overlap

        # Bounce with extra speed
        speed = max(3.0, math.hypot(ball.vx, ball.vy))
        ball.vx = nx * speed * 1.4
        ball.vy = ny * speed * 1.4

        self.flash = 12
        return True

    def draw(self):
        color = WHITE if self.flash > 0 else self.color
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius, 2)
        if self.points > 0:
            txt = FONT_S.render(str(self.points), True, BLACK)
            r = txt.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(txt, r)


class ArcGuide:
    """Semi-circular guide wall at the top of the table."""

    def __init__(self, cx, cy, radius):
        self.cx = cx
        self.cy = cy
        self.radius = radius

    def check_collision(self, ball):
        dx = ball.x - self.cx
        dy = ball.y - self.cy
        dist = math.hypot(dx, dy)
        # Only check ball near the arc (top half)
        if dist >= self.radius - ball.radius and dist <= self.radius + ball.radius and ball.y < self.cy + 30:
            if dist > 0:
                nx = dx / dist
                ny = dy / dist
            else:
                nx, ny = 0, -1
            # Push to surface and reflect
            ball.x = self.cx + nx * (self.radius - ball.radius)
            ball.y = self.cy + ny * (self.radius - ball.radius)
            dot = ball.vx * nx + ball.vy * ny
            if dot < 0:
                ball.vx -= 2 * dot * nx
                ball.vy -= 2 * dot * ny
            return True
        return False

    def draw(self):
        # Draw the arc as connected line segments
        for i in range(0, 181, 6):
            a1 = math.radians(i)
            a2 = math.radians(i + 6)
            p1 = (int(self.cx + self.radius * math.cos(a1)),
                  int(self.cy - self.radius * math.sin(a1)))
            p2 = (int(self.cx + self.radius * math.cos(a2)),
                  int(self.cy - self.radius * math.sin(a2)))
            pygame.draw.line(screen, GRAY, p1, p2, 3)
        # Inner glow line
        inner_r = self.radius - 4
        for i in range(0, 181, 10):
            a = math.radians(i)
            px = int(self.cx + inner_r * math.cos(a))
            py = int(self.cy - inner_r * math.sin(a))
            pygame.draw.circle(screen, DARK, (px, py), 2)


class Game:
    """Main game controller."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.ball = Ball()
        self.score = 0
        self.lives = MAX_LIVES
        self.game_over = False
        self.launch_power = 0.0
        self.charging = False

        # Flippers
        self.left_flipper = Flipper(150, HEIGHT - 70, True)
        self.right_flipper = Flipper(WIDTH - 150, HEIGHT - 70, False)

        # Bumpers — arranged in a diamond pattern
        self.bumpers = [
            Bumper(WIDTH // 2, 240, 22, RED, 100),
            Bumper(160, 320, 20, GREEN, 150),
            Bumper(WIDTH - 160, 320, 20, BLUE, 150),
            Bumper(WIDTH // 2, 370, 18, YELLOW, 200),
            Bumper(120, 420, 16, PURPLE, 250),
            Bumper(WIDTH - 120, 420, 16, ORANGE, 250),
            Bumper(WIDTH // 2, 460, 22, PINK, 300),
        ]

        # Top arc
        self.arc = ArcGuide(WIDTH // 2, 130, 200)

        # Angled guide walls near bottom
        self.guide_walls = [
            ((15, 130), (50, HEIGHT - 150)),
            ((WIDTH - 15, 130), (WIDTH - 50, HEIGHT - 150)),
            ((50, HEIGHT - 150), (100, HEIGHT - 100)),
            ((WIDTH - 50, HEIGHT - 150), (WIDTH - 100, HEIGHT - 100)),
        ]

    def launch_charge(self):
        """Hold space to charge launcher power."""
        if not self.ball.active and not self.game_over:
            self.charging = True
            self.launch_power = min(10.0, self.launch_power + 0.25)

    def launch_release(self):
        """Release space to fire the ball."""
        if not self.ball.active and self.charging and self.launch_power > 0.5:
            power = self.launch_power
            self.ball.vx = math.cos(math.radians(-15)) * power * 0.5
            self.ball.vy = -math.sin(math.radians(-15)) * power * 1.0
            self.ball.active = True
            self.ball.x = WIDTH - 50
            self.ball.y = HEIGHT - 100
            self.charging = False
            self.launch_power = 0.0
        else:
            self.charging = False
            self.launch_power = 0.0

    def update(self, keys):
        if self.game_over:
            return

        # Flippers
        self.left_flipper.activate(keys[pygame.K_LEFT])
        self.right_flipper.activate(keys[pygame.K_RIGHT])
        self.left_flipper.update()
        self.right_flipper.update()

        # Launcher
        if keys[pygame.K_SPACE]:
            self.launch_charge()
        else:
            self.launch_release()

        self.ball.update()
        if not self.ball.active:
            return

        # Collisions
        self.arc.check_collision(self.ball)
        for (x1, y1), (x2, y2) in self.guide_walls:
            self._line_collision(self.ball, x1, y1, x2, y2)
        self.left_flipper.check_collision(self.ball)
        self.right_flipper.check_collision(self.ball)

        for bumper in self.bumpers:
            bumper.update()
            if bumper.check_collision(self.ball):
                self.score += bumper.points

        # Ball lost at bottom
        if self.ball.y > HEIGHT + 30:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
            else:
                self.ball = Ball()

    def _line_collision(self, ball, x1, y1, x2, y2):
        """Collision between ball and an infinite wall segment."""
        dx, dy = x2 - x1, y2 - y1
        length_sq = dx * dx + dy * dy
        if length_sq == 0:
            return
        t = ((ball.x - x1) * dx + (ball.y - y1) * dy) / length_sq
        t = max(0.0, min(1.0, t))
        cx = x1 + t * dx
        cy = y1 + t * dy
        dist = math.hypot(ball.x - cx, ball.y - cy)
        if dist < ball.radius:
            if dist > 0:
                nx = (ball.x - cx) / dist
                ny = (ball.y - cy) / dist
            else:
                nx, ny = 0, -1
            ball.x = cx + nx * ball.radius
            ball.y = cy + ny * ball.radius
            dot = ball.vx * nx + ball.vy * ny
            if dot < 0:
                ball.vx -= 2 * dot * nx
                ball.vy -= 2 * dot * ny
                ball.vx *= 0.8
                ball.vy *= 0.8

    def draw(self):
        screen.fill(BLACK)

        # Table border
        pygame.draw.rect(screen, DARK, (10, 10, WIDTH - 20, HEIGHT - 20), 4)
        pygame.draw.rect(screen, GRAY, (12, 12, WIDTH - 24, HEIGHT - 24), 1)

        # Arc guide
        self.arc.draw()

        # Guide walls
        for (x1, y1), (x2, y2) in self.guide_walls:
            pygame.draw.line(screen, DARK, (int(x1), int(y1)), (int(x2), int(y2)), 4)

        # Launcher track
        pygame.draw.rect(screen, DARK, (WIDTH - 60, HEIGHT - 450, 20, 350))
        pygame.draw.rect(screen, GRAY, (WIDTH - 58, HEIGHT - 450, 16, 350), 1)

        # Bumpers
        for bumper in self.bumpers:
            bumper.draw()

        # Flippers
        self.left_flipper.draw()
        self.right_flipper.draw()

        # Ball
        self.ball.draw()

        # Launch power bar
        if not self.ball.active and self.launch_power > 0:
            h = int(self.launch_power / 10 * 340)
            pygame.draw.rect(screen, YELLOW, (WIDTH - 56, HEIGHT - 100 - h, 12, h))
            pygame.draw.rect(screen, WHITE, (WIDTH - 56, HEIGHT - 100 - h, 12, h), 1)

        # Ball in launcher position
        if not self.ball.active:
            pygame.draw.circle(screen, WHITE, (WIDTH - 50, HEIGHT - 90), BALL_RADIUS)
            pygame.draw.circle(screen, (180, 180, 200), (WIDTH - 52, HEIGHT - 92), BALL_RADIUS - 3)

        # Score
        score_text = FONT_M.render(f"SCORE: {self.score}", True, WHITE)
        screen.blit(score_text, (20, 15))

        # Lives
        for i in range(self.lives):
            pygame.draw.circle(screen, RED, (WIDTH - 30 - i * 25, 28), 6)
            pygame.draw.circle(screen, WHITE, (WIDTH - 30 - i * 25, 28), 6, 1)

        # Hint text
        if not self.ball.active:
            hint = FONT_S.render("Hold SPACE to charge launcher, release to fire!", True, YELLOW)
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 35))

        # Control hints
        ctrl = FONT_S.render("LEFT / RIGHT — Flippers", True, GRAY)
        screen.blit(ctrl, (20, HEIGHT - 30))

        # Game over overlay
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))

            go = FONT_L.render("GAME OVER", True, RED)
            screen.blit(go, (WIDTH // 2 - go.get_width() // 2, HEIGHT // 2 - 80))

            fs = FONT_L.render(f"Final Score: {self.score}", True, WHITE)
            screen.blit(fs, (WIDTH // 2 - fs.get_width() // 2, HEIGHT // 2))

            restart = FONT_M.render("Press R to Restart", True, YELLOW)
            screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT // 2 + 60))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and self.game_over:
            self.reset()


def main():
    """Main game loop."""
    game = Game()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_event(event)

        keys = pygame.key.get_pressed()
        game.update(keys)
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()