import pygame
import random
import sys

# 初始化 pygame
pygame.init()

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_BLUE = (173, 216, 230)
DARK_GRAY = (169, 169, 169)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# 游戏配置
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRID_SIZE = 4  # 4x4 网格
CARD_WIDTH = 120
CARD_HEIGHT = 120
MARGIN = 20
FPS = 30

# 创建窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('记忆卡片')

# 时钟
clock = pygame.time.Clock()

# 字体
font = pygame.font.SysFont('arial', 40)
small_font = pygame.font.SysFont('arial', 24)

# 卡片颜色（8 种不同颜色，每种两张）
CARD_COLORS = [
    (255, 0, 0),    # 红
    (0, 255, 0),    # 绿
    (0, 0, 255),    # 蓝
    (255, 255, 0),  # 黄
    (255, 0, 255),  # 紫
    (0, 255, 255),  # 青
    (255, 165, 0),  # 橙
    (128, 0, 128)   # 深紫
]

class Card:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.revealed = False
        self.matched = False

    def draw(self, surface):
        rect = pygame.Rect(self.x, self.y, CARD_WIDTH, CARD_HEIGHT)
        if self.revealed or self.matched:
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.rect(surface, WHITE, rect, 3)
        else:
            pygame.draw.rect(surface, DARK_GRAY, rect)
            pygame.draw.rect(surface, WHITE, rect, 3)
            # 画一个问号
            text = font.render('?', True, WHITE)
            text_rect = text.get_rect(center=rect.center)
            surface.blit(text, text_rect)

    def is_clicked(self, mouse_pos):
        rect = pygame.Rect(self.x, self.y, CARD_WIDTH, CARD_HEIGHT)
        return rect.collidepoint(mouse_pos) and not self.revealed and not self.matched

def create_cards():
    # 创建卡片列表（每种颜色两张）
    colors = CARD_COLORS * 2
    random.shuffle(colors)
    
    cards = []
    start_x = (WINDOW_WIDTH - (GRID_SIZE * CARD_WIDTH + (GRID_SIZE - 1) * MARGIN)) // 2
    start_y = (WINDOW_HEIGHT - (GRID_SIZE * CARD_HEIGHT + (GRID_SIZE - 1) * MARGIN)) // 2
    
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x = start_x + col * (CARD_WIDTH + MARGIN)
            y = start_y + row * (CARD_HEIGHT + MARGIN)
            color = colors.pop()
            cards.append(Card(x, y, color))
    return cards

def draw_game(screen, cards, moves, matches):
    screen.fill(LIGHT_BLUE)
    
    for card in cards:
        card.draw(screen)
    
    # 显示步数和匹配数
    moves_text = small_font.render(f'步数: {moves}', True, BLACK)
    matches_text = small_font.render(f'匹配: {matches}/8', True, BLACK)
    screen.blit(moves_text, (20, 20))
    screen.blit(matches_text, (20, 50))
    
    pygame.display.flip()

def show_win_screen(screen, moves):
    screen.fill(LIGHT_BLUE)
    win_text = font.render('恭喜获胜!', True, GREEN)
    moves_text = small_font.render(f'总步数: {moves}', True, BLACK)
    restart_text = small_font.render('点击任意键重新开始', True, BLACK)
    
    win_rect = win_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
    moves_rect = moves_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
    restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
    
    screen.blit(win_text, win_rect)
    screen.blit(moves_text, moves_rect)
    screen.blit(restart_text, restart_rect)
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                waiting = False

def main():
    while True:
        cards = create_cards()
        first_card = None
        second_card = None
        moves = 0
        matches = 0
        waiting = False
        waiting_start = 0
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN and not waiting:
                    pos = pygame.mouse.get_pos()
                    for card in cards:
                        if card.is_clicked(pos):
                            card.revealed = True
                            if first_card is None:
                                first_card = card
                            elif second_card is None:
                                second_card = card
                                moves += 1
                                if first_card.color == second_card.color:
                                    first_card.matched = True
                                    second_card.matched = True
                                    matches += 1
                                    first_card = None
                                    second_card = None
                                    if matches == 8:
                                        running = False
                                else:
                                    waiting = True
                                    waiting_start = pygame.time.get_ticks()
            
            # 处理等待状态，翻回不匹配的卡片
            if waiting and pygame.time.get_ticks() - waiting_start > 1000:
                first_card.revealed = False
                second_card.revealed = False
                first_card = None
                second_card = None
                waiting = False
            
            draw_game(screen, cards, moves, matches)
            clock.tick(FPS)
        
        show_win_screen(screen, moves)

if __name__ == '__main__':
    main()

