import pygame
import math
import random

pygame.init()

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 700
COLS = 10
ROWS = 12
BUBBLE_RADIUS = 22
BUBBLE_DIAMETER = BUBBLE_RADIUS * 2
BOARD_LEFT = 40
BOARD_TOP = 60
BOARD_WIDTH = COLS * BUBBLE_DIAMETER + BUBBLE_RADIUS
BOARD_HEIGHT = ROWS * int(BUBBLE_DIAMETER * 0.85)

COLORS = [
    (255, 60, 60),
    (60, 180, 255),
    (60, 220, 80),
    (255, 220, 40),
    (200, 100, 255),
]

COLOR_NAMES = ["RED", "BLUE", "GREEN", "YELLOW", "PURPLE"]

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("泡泡龙 Bubble Shooter")
clock = pygame.time.Clock()
font = pygame.font.SysFont("dejavusans", 28, bold=True)
small_font = pygame.font.SysFont("dejavusans", 20)

shooter_angle = 90
current_bubble_color = 0
next_bubble_color = 0
score = 0
game_state = "aiming"
state_timer = 0
move_down_counter = 0
move_down_delay = 600

grid = [[None for _ in range(COLS)] for _ in range(ROWS)]

def get_bubble_pos(row, col):
    offset_x = BUBBLE_RADIUS if row % 2 == 1 else 0
    x = BOARD_LEFT + col * BUBBLE_DIAMETER + BUBBLE_RADIUS + offset_x
    y = BOARD_TOP + row * int(BUBBLE_DIAMETER * 0.85) + BUBBLE_RADIUS
    return x, y

def init_grid():
    global grid
    grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
    fill_rows = 5
    for row in range(fill_rows):
        cols_in_row = COLS - (1 if row % 2 == 1 else 0)
        offset = 1 if row % 2 == 1 else 0
        for col in range(cols_in_row):
            grid[row][col + offset] = random.randint(0, len(COLORS) - 1)

def grid_col_count(row):
    return COLS - (1 if row % 2 == 1 else 0)

def grid_col_offset(row):
    return 1 if row % 2 == 1 else 0

def get_neighbors(row, col):
    neighbors = []
    offsets = [
        (-1, -1) if row % 2 == 1 else (-1, 0),
        (-1, 0) if row % 2 == 1 else (-1, 1),
        (0, -1), (0, 1),
        (1, -1) if row % 2 == 1 else (1, 0),
        (1, 0) if row % 2 == 1 else (1, 1),
    ]
    for dr, dc in offsets:
        nr, nc = row + dr, col + dc
        if 0 <= nr < ROWS and 0 <= nc < COLS:
            if nc < grid_col_count(nr) + grid_col_offset(nr):
                if grid[nr][nc] is not None:
                    neighbors.append((nr, nc))
    return neighbors

def find_matches(row, col, color):
    visited = set()
    to_visit = [(row, col)]
    matched = []
    while to_visit:
        r, c = to_visit.pop()
        if (r, c) in visited:
            continue
        visited.add((r, c))
        if grid[r][c] == color:
            matched.append((r, c))
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in visited and grid[nr][nc] == color:
                    to_visit.append((nr, nc))
    return matched

def find_connected_to_top():
    connected = set()
    for c in range(COLS):
        if grid[0][c] is not None:
            to_visit = [(0, c)]
            while to_visit:
                r, cc = to_visit.pop()
                if (r, cc) in connected:
                    continue
                connected.add((r, cc))
                for nr, nc in get_neighbors(r, cc):
                    if (nr, nc) not in connected and grid[nr][nc] is not None:
                        to_visit.append((nr, nc))
    return connected

def remove_floating():
    connected = find_connected_to_top()
    floating = []
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] is not None and (r, c) not in connected:
                floating.append((r, c))
    for r, c in floating:
        grid[r][c] = None
    return len(floating)

def remove_bubbles(matched):
    for r, c in matched:
        grid[r][c] = None

def drop_all_grid():
    for r in range(ROWS - 2, -1, -1):
        for c in range(COLS):
            if grid[r][c] is not None:
                nr = r + 1
                while nr < ROWS and grid[nr][c] is None:
                    nr += 1
                if nr - 1 != r:
                    grid[nr - 1][c] = grid[r][c]
                    grid[r][c] = None

def find_insert_position(row, col, color):
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] is not None:
                continue
            px, py = get_bubble_pos(r, c)
            bx, by = get_bubble_pos(row, col)
            dist = math.hypot(px - bx, py - by)
            if dist < BUBBLE_DIAMETER * 0.9:
                return r, c
    return row, col

def find_closest_grid(x, y):
    best_dist = float("inf")
    best_pos = None
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] is not None:
                continue
            gx, gy = get_bubble_pos(r, c)
            dist = math.hypot(x - gx, y - gy)
            if dist < best_dist:
                best_dist = dist
                best_pos = (r, c)
    return best_pos

init_grid()
current_bubble_color = random.randint(0, len(COLORS) - 1)
next_bubble_color = random.randint(0, len(COLORS) - 1)

shooter_x = SCREEN_WIDTH // 2
shooter_y = SCREEN_HEIGHT - 50
bullet = None
aim_direction = (0, -1)

def reset_shooter():
    global current_bubble_color, next_bubble_color
    current_bubble_color = next_bubble_color
    next_bubble_color = random.randint(0, len(COLORS) - 1)

def shoot():
    global bullet, game_state
    angle_rad = math.radians(shooter_angle)
    dx = -math.cos(angle_rad)
    dy = -math.sin(angle_rad)
    speed = 12
    bullet = {
        "x": shooter_x,
        "y": shooter_y - BUBBLE_RADIUS,
        "dx": dx * speed,
        "dy": dy * speed,
        "color": current_bubble_color,
    }
    game_state = "shooting"

def draw_grid():
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] is not None:
                x, y = get_bubble_pos(r, c)
                color = COLORS[grid[r][c]]
                pygame.draw.circle(screen, (30, 30, 30), (int(x) + 2, int(y) + 2), BUBBLE_RADIUS)
                pygame.draw.circle(screen, color, (int(x), int(y)), BUBBLE_RADIUS)
                highlight = tuple(min(255, c + 60) for c in color)
                pygame.draw.circle(screen, highlight, (int(x) - 4, int(y) - 4), BUBBLE_RADIUS - 8, 2)

def draw_shooter():
    angle_rad = math.radians(shooter_angle)
    tip_x = shooter_x - math.cos(angle_rad) * 50
    tip_y = shooter_y - math.sin(angle_rad) * 50
    pygame.draw.line(screen, (100, 100, 100), (shooter_x, shooter_y), (tip_x, tip_y), 5)
    color = COLORS[current_bubble_color]
    pygame.draw.circle(screen, (30, 30, 30), (shooter_x + 2, shooter_y + 2), BUBBLE_RADIUS)
    pygame.draw.circle(screen, color, (shooter_x, shooter_y), BUBBLE_RADIUS)
    highlight = tuple(min(255, c + 60) for c in color)
    pygame.draw.circle(screen, highlight, (shooter_x - 3, shooter_y - 3), BUBBLE_RADIUS - 6, 2)

def draw_next():
    label = small_font.render("Next", True, (200, 200, 200))
    screen.blit(label, (SCREEN_WIDTH - 80, 100))
    color = COLORS[next_bubble_color]
    nx, ny = SCREEN_WIDTH - 70, 140
    pygame.draw.circle(screen, (30, 30, 30), (nx + 2, ny + 2), BUBBLE_RADIUS - 4)
    pygame.draw.circle(screen, color, (nx, ny), BUBBLE_RADIUS - 4)

def draw_bullet():
    if bullet:
        x, y, color_idx = bullet["x"], bullet["y"], bullet["color"]
        color = COLORS[color_idx]
        pygame.draw.circle(screen, (30, 30, 30), (int(x) + 2, int(y) + 2), BUBBLE_RADIUS - 2)
        pygame.draw.circle(screen, color, (int(x), int(y)), BUBBLE_RADIUS - 2)

def draw_aim_line():
    angle_rad = math.radians(shooter_angle)
    for dist in range(30, 600, 30):
        px = shooter_x - math.cos(angle_rad) * dist
        py = shooter_y - math.sin(angle_rad) * dist
        alpha = max(0, 255 - dist * 0.6)
        if alpha < 20:
            break
        for r in range(ROWS):
            for c in range(COLS):
                if grid[r][c] is not None:
                    gx, gy = get_bubble_pos(r, c)
                    if math.hypot(px - gx, py - gy) < BUBBLE_RADIUS + 5:
                        return
        pygame.draw.circle(screen, (255, 255, 255, int(alpha)), (int(px), int(py)), 3)

def draw_ui():
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (20, 10))
    if game_state == "game_over":
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        go_text = font.render("GAME OVER", True, (255, 60, 60))
        go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        screen.blit(go_text, go_rect)
        restart_text = small_font.render("Press R to restart", True, (200, 200, 200))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        screen.blit(restart_text, restart_rect)

def check_game_over():
    for c in range(COLS):
        x, y = get_bubble_pos(ROWS - 1, c)
        if y > SCREEN_HEIGHT - 100:
            return True
    return False

def restart():
    global score, game_state, bullet, current_bubble_color, next_bubble_color, move_down_counter
    score = 0
    game_state = "aiming"
    bullet = None
    move_down_counter = 0
    init_grid()
    current_bubble_color = random.randint(0, len(COLORS) - 1)
    next_bubble_color = random.randint(0, len(COLORS) - 1)

running = True
while running:
    dt = clock.get_time()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_state == "game_over":
                restart()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state == "aiming":
                shoot()

    mx, my = pygame.mouse.get_pos()
    dx = mx - shooter_x
    dy = my - shooter_y
    if dy < 0:
        angle = math.degrees(math.atan2(-dy, dx))
        shooter_angle = max(10, min(170, angle))

    if game_state == "shooting" and bullet:
        bullet["x"] += bullet["dx"]
        bullet["y"] += bullet["dy"]
        bx, by = bullet["x"], bullet["y"]
        if bx < BUBBLE_RADIUS or bx > SCREEN_WIDTH - BUBBLE_RADIUS:
            bullet["dx"] = -bullet["dx"]
            bx = max(BUBBLE_RADIUS, min(SCREEN_WIDTH - BUBBLE_RADIUS, bx))
            bullet["x"] = bx
        if by < BOARD_TOP:
            result = find_closest_grid(bx, by)
            if result:
                row, col = result
                grid[row][col] = bullet["color"]
                matched = find_matches(row, col, bullet["color"])
                if len(matched) >= 3:
                    remove_bubbles(matched)
                    score += len(matched) * 10
                    removed = remove_floating()
                    score += removed * 20
                    drop_all_grid()
                bullet = None
                game_state = "aiming"
                reset_shooter()
                if check_game_over():
                    game_state = "game_over"
            else:
                bullet = None
                game_state = "aiming"
                reset_shooter()

        for r in range(ROWS):
            for c in range(COLS):
                if grid[r][c] is not None:
                    gx, gy = get_bubble_pos(r, c)
                    dist = math.hypot(bx - gx, by - gy)
                    if dist < BUBBLE_DIAMETER - 2:
                        result = find_closest_grid(bx, by)
                        if result:
                            row, col = result
                            grid[row][col] = bullet["color"]
                            matched = find_matches(row, col, bullet["color"])
                            if len(matched) >= 3:
                                remove_bubbles(matched)
                                score += len(matched) * 10
                                removed = remove_floating()
                                score += removed * 20
                                drop_all_grid()
                            else:
                                pass
                        bullet = None
                        game_state = "aiming"
                        reset_shooter()
                        if check_game_over():
                            game_state = "game_over"
                        break
            if bullet is None:
                break

        if bullet and bullet["y"] < BOARD_TOP - BUBBLE_RADIUS * 2:
            bullet = None
            game_state = "aiming"
            reset_shooter()

    move_down_counter += dt
    if move_down_counter >= move_down_delay:
        move_down_counter = 0
        new_grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
        for r in range(ROWS - 1):
            for c in range(COLS):
                new_grid[r + 1][c] = grid[r][c]
        grid = new_grid
        if check_game_over():
            game_state = "game_over"

    screen.fill((20, 20, 40))
    board_rect = pygame.Rect(BOARD_LEFT - 10, BOARD_TOP - 10, BOARD_WIDTH + 20, BOARD_HEIGHT + 20)
    pygame.draw.rect(screen, (30, 30, 60), board_rect, border_radius=8)
    draw_grid()
    draw_aim_line()
    draw_shooter()
    draw_next()
    draw_bullet()
    draw_ui()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()