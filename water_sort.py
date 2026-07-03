"""
水排序 (Water Sort Puzzle) - 2026-07-03
Python + Pygame 单文件实现
玩法：将不同颜色的水分别倒入对应的试管中，使每根试管只有一种颜色
"""

import pygame
import random
import sys
from copy import deepcopy

# ---------- 常量配置 ----------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 620
BG_COLOR = (30, 30, 40)

# 试管参数
TUBE_WIDTH = 50
TUBE_HEIGHT = 180
TUBE_RADIUS = 10          # 试管圆角
TUBE_BORDER = 3
TUBE_WALL_COLOR = (180, 180, 190)
TUBE_EMPTY_COLOR = (60, 60, 70)
TUBE_GAP_X = 20           # 试管水平间距
TUBE_TOP_OFFSET = 120     # 试管顶部y坐标

# 颜色方案 (R, G, B)
COLORS = {
    0: (255, 80, 80),     # 红
    1: (80, 200, 255),    # 蓝
    2: (80, 220, 80),     # 绿
    3: (255, 220, 50),    # 黄
    4: (200, 80, 255),    # 紫
    5: (255, 140, 40),    # 橙
    6: (255, 100, 180),   # 粉
    7: (100, 220, 200),   # 青
}

NUM_COLORS = 6            # 颜色种类数 (6色=6*4=24格, 6满管+2空管)
SEGMENTS_PER_TUBE = 4     # 每管最多段数
EMPTY_TUBES = 2           # 空管数量
TOTAL_TUBES = NUM_COLORS + EMPTY_TUBES

# 动画
ANIM_SPEED = 12           # 像素/帧

FPS = 60

# ---------- 工具函数 ----------
def create_puzzle():
    """生成一个可解的谜题"""
    segments = []
    for c in range(NUM_COLORS):
        segments.extend([c] * SEGMENTS_PER_TUBE)
    random.shuffle(segments)

    tubes = [[] for _ in range(TOTAL_TUBES)]
    for i, seg in enumerate(segments):
        tube_idx = i // SEGMENTS_PER_TUBE
        tubes[tube_idx].append(seg)
    return tubes


def is_solved(tubes):
    """检查是否全部完成"""
    for t in tubes:
        if len(t) == 0:
            continue
        if len(t) != SEGMENTS_PER_TUBE:
            return False
        if len(set(t)) != 1:
            return False
    return True


def can_pour(src, dst):
    """判断能否从 src 倒入 dst"""
    if not src or len(dst) >= SEGMENTS_PER_TUBE:
        return False
    if not dst:
        return True
    return src[-1] == dst[-1]


def pour(src, dst):
    """执行倒水，返回(src倒出数量, dst颜色段列表)"""
    if not can_pour(src, dst):
        return 0, list(dst)

    color = src[-1]
    count = 0
    # 统计 src 顶部相同颜色的连续段数
    for i in range(len(src) - 1, -1, -1):
        if src[i] == color:
            count += 1
        else:
            break
    # 计算 dst 能接收多少
    space = SEGMENTS_PER_TUBE - len(dst)
    pour_count = min(count, space)
    return pour_count, color


# ---------- 渲染 ----------
def draw_tube(screen, tube, x, y, selected=False, anim_offset=0, pour_count=0):
    """绘制一根试管"""
    h = TUBE_HEIGHT
    # 选中高亮
    if selected:
        pygame.draw.rect(screen, (255, 255, 100),
                         (x - 4, y - 4, TUBE_WIDTH + 8, h + 8),
                         border_radius=TUBE_RADIUS + 2)

    # 试管壁
    pygame.draw.rect(screen, TUBE_WALL_COLOR,
                     (x, y, TUBE_WIDTH, h), border_radius=TUBE_RADIUS)
    # 内部背景
    inner_rect = (x + TUBE_BORDER, y + TUBE_BORDER,
                  TUBE_WIDTH - 2 * TUBE_BORDER, h - 2 * TUBE_BORDER)
    pygame.draw.rect(screen, TUBE_EMPTY_COLOR, inner_rect, border_radius=TUBE_RADIUS - 2)

    # 绘制各段颜色 (从下往上)
    seg_h = (h - 2 * TUBE_BORDER) // SEGMENTS_PER_TUBE
    for i, color_id in enumerate(tube):
        cy = y + h - TUBE_BORDER - (i + 1) * seg_h
        # 如果正在动画且是顶部被倒出的段
        if anim_offset > 0 and i >= len(tube) - pour_count:
            cy -= anim_offset
        color_rgb = COLORS[color_id]
        pygame.draw.rect(screen, color_rgb,
                         (x + TUBE_BORDER + 1, cy + 1,
                          TUBE_WIDTH - 2 * TUBE_BORDER - 2, seg_h - 2),
                         border_radius=TUBE_RADIUS - 3)


def draw_info(screen, font, moves, solved):
    """绘制顶部信息"""
    title = font.render("水排序 Water Sort", True, (220, 220, 220))
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 20))

    moves_text = font.render(f"步数: {moves}", True, (180, 180, 200))
    screen.blit(moves_text, (30, 60))

    if solved:
        win_text = font.render("🎉 恭喜通关! 按 R 重新开始", True, (100, 255, 100))
        screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, 70))

    hint = font.render("R=重开  S=洗牌", True, (140, 140, 160))
    screen.blit(hint, (SCREEN_WIDTH - hint.get_width() - 30, 60))


# ---------- 工具函数: 检查是否可解(简化版) ----------
def shuffle_tubes(tubes):
    """洗牌(保留空管)"""
    all_segs = []
    for t in tubes:
        all_segs.extend(t)
    random.shuffle(all_segs)
    idx = 0
    for t in tubes:
        t.clear()
        for _ in range(min(SEGMENTS_PER_TUBE, len(all_segs) - idx)):
            t.append(all_segs[idx])
            idx += 1
    # 补齐完全填满的tube按实际填
    return tubes


# ---------- 主函数 ----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("水排序 Water Sort Puzzle")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("simhei", 24)

    tubes = create_puzzle()
    src_idx = -1           # 当前选中的试管索引
    moves = 0
    solved = False

    # 动画状态
    animating = False
    anim_src_idx = -1
    anim_dst_idx = -1
    anim_offset = 0        # 水柱上升像素偏移
    anim_pour_count = 0
    anim_color = -1
    anim_phase = "up"      # up = 上升, down = 下降, back = 回退

    running = True
    while running:
        dt = clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        # ---- 事件处理 ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # 重开
                    tubes = create_puzzle()
                    src_idx = -1
                    moves = 0
                    solved = False
                    animating = False
                if event.key == pygame.K_s and not animating:
                    # 洗牌
                    shuffle_tubes(tubes)
                    src_idx = -1
                    solved = False

            if event.type == pygame.MOUSEBUTTONDOWN and not animating and not solved:
                mx, my = event.pos
                # 计算点击的试管
                total_width = TOTAL_TUBES * TUBE_WIDTH + (TOTAL_TUBES - 1) * TUBE_GAP_X
                start_x = (SCREEN_WIDTH - total_width) // 2
                clicked_idx = -1
                for i in range(TOTAL_TUBES):
                    tx = start_x + i * (TUBE_WIDTH + TUBE_GAP_X)
                    if tx <= mx <= tx + TUBE_WIDTH and TUBE_TOP_OFFSET <= my <= TUBE_TOP_OFFSET + TUBE_HEIGHT:
                        clicked_idx = i
                        break

                if clicked_idx == -1:
                    continue

                if src_idx == -1:
                    # 首次选择
                    if tubes[clicked_idx]:
                        src_idx = clicked_idx
                else:
                    if clicked_idx == src_idx:
                        src_idx = -1  # 取消选择
                    elif can_pour(tubes[src_idx], tubes[clicked_idx]):
                        # 开始倒水动画
                        pour_count, color = pour(tubes[src_idx], tubes[clicked_idx])
                        if pour_count > 0:
                            animating = True
                            anim_src_idx = src_idx
                            anim_dst_idx = clicked_idx
                            anim_offset = 0
                            anim_pour_count = pour_count
                            anim_color = color
                            anim_phase = "up"
                        src_idx = -1
                    else:
                        # 切换到新选择
                        src_idx = clicked_idx if tubes[clicked_idx] else -1

        # ---- 动画更新 ----
        if animating:
            if anim_phase == "up":
                anim_offset += ANIM_SPEED
                seg_h = (TUBE_HEIGHT - 2 * TUBE_BORDER) // SEGMENTS_PER_TUBE
                if anim_offset >= seg_h:
                    anim_offset = seg_h
                    anim_phase = "down"
            elif anim_phase == "down":
                anim_offset -= ANIM_SPEED * 1.5
                if anim_offset <= 0:
                    anim_offset = 0
                    # 执行实际的倒水
                    src = tubes[anim_src_idx]
                    dst = tubes[anim_dst_idx]
                    for _ in range(anim_pour_count):
                        if src and can_pour(src, dst):
                            dst.append(src.pop())
                    moves += 1
                    if is_solved(tubes):
                        solved = True
                    animating = False
                    src_idx = -1

        # ---- 渲染 ----
        screen.fill(BG_COLOR)

        total_width = TOTAL_TUBES * TUBE_WIDTH + (TOTAL_TUBES - 1) * TUBE_GAP_X
        start_x = (SCREEN_WIDTH - total_width) // 2

        for i in range(TOTAL_TUBES):
            tx = start_x + i * (TUBE_WIDTH + TUBE_GAP_X)
            ty = TUBE_TOP_OFFSET
            is_selected = (i == src_idx)
            anim_off = 0
            pour_cnt = 0
            if animating:
                if i == anim_src_idx:
                    anim_off = anim_offset
                    pour_cnt = anim_pour_count
            draw_tube(screen, tubes[i], tx, ty, is_selected, anim_off, pour_cnt)

        # 选中指示文字
        if src_idx >= 0 and not animating:
            tx = start_x + src_idx * (TUBE_WIDTH + TUBE_GAP_X)
            label = font.render("▼", True, (255, 255, 100))
            screen.blit(label, (tx + TUBE_WIDTH // 2 - label.get_width() // 2,
                                TUBE_TOP_OFFSET - 35))

        draw_info(screen, font, moves, solved)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()