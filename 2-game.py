import pygame
import random
 
pygame.init()
W, H = 400, 600
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()
 
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
SKY = (30, 30, 60)
HELI_COLOR = (0, 200, 100)
HELI_DARK = (0, 150, 70)
CAVE_COLOR = (80, 60, 40)
CAVE_EDGE = (120, 90, 60)
PILLAR_COLOR = (180, 60, 60)
PILLAR_EDGE = (140, 40, 40)
 
# Helicopter
heli_x = 80
heli_y = H // 2
heli_vy = 0.0
GRAVITY = 0.4
LIFT = -0.7
HELI_W = 40
HELI_H = 20
 
# Cave
CAVE_SEG_W = 4
cave_top = []
cave_bot = []
cave_gap = 320
cave_center = H // 2
MIN_GAP = 180
scroll_speed = 2.5
 
# Pillars
pillars = []
PILLAR_W = 40
pillar_timer = 0
PILLAR_INTERVAL = 80
 
# Game state
score = 0
best_score = 0
game_over = False
started = False
holding = False
frame = 0
rotor_frame = 0
 
def init_cave():
    global cave_top, cave_bot, cave_gap, cave_center
    cave_top.clear()
    cave_bot.clear()
    cave_gap = 320
    cave_center = H // 2
    for i in range(W // CAVE_SEG_W + 2):
        cave_top.append(cave_center - cave_gap // 2)
        cave_bot.append(cave_center + cave_gap // 2)
 
def add_cave_segment():
    global cave_center, cave_gap
    cave_center += random.randint(-8, 8)
    cave_gap += random.choice([-1, -1, 0, 0, 1])
    cave_gap = max(MIN_GAP, min(380, cave_gap))
    cave_center = max(cave_gap // 2 + 10, min(H - cave_gap // 2 - 10, cave_center))
    cave_top.append(cave_center - cave_gap // 2)
    cave_bot.append(cave_center + cave_gap // 2)
 
init_cave()
 
def reset_game():
    global heli_y, heli_vy, score, game_over, started, holding
    global pillars, pillar_timer, frame, scroll_speed
    heli_y = H // 2
    heli_vy = 0.0
    score = 0
    game_over = False
    started = False
    holding = False
    pillars.clear()
    pillar_timer = 0
    frame = 0
    scroll_speed = 2.5
    init_cave()
 
def draw_helicopter(x, y):
    # Body
    body = pygame.Rect(x - HELI_W // 2, int(y) - HELI_H // 2, HELI_W, HELI_H)
    pygame.draw.ellipse(screen, HELI_COLOR, body)
    pygame.draw.ellipse(screen, HELI_DARK, body, 2)
    # Cockpit window
    pygame.draw.ellipse(screen, (180, 230, 255),
        (x - HELI_W // 2 + 22, int(y) - 6, 14, 12))
    # Tail
    pygame.draw.line(screen, HELI_DARK,
        (x - HELI_W // 2, int(y)),
        (x - HELI_W // 2 - 18, int(y) - 6), 3)
    # Tail rotor
    pygame.draw.circle(screen, WHITE,
        (x - HELI_W // 2 - 18, int(y) - 6), 5, 1)
    # Main rotor (animated)
    rotor_w = HELI_W + 16
    if rotor_frame % 2 == 0:
        pygame.draw.line(screen, WHITE,
            (x - rotor_w // 2, int(y) - HELI_H // 2 - 3),
            (x + rotor_w // 2, int(y) - HELI_H // 2 - 3), 2)
    else:
        pygame.draw.line(screen, WHITE,
            (x - rotor_w // 4, int(y) - HELI_H // 2 - 3),
            (x + rotor_w // 4, int(y) - HELI_H // 2 - 3), 2)
    # Skids
    pygame.draw.line(screen, GRAY,
        (x - 14, int(y) + HELI_H // 2),
        (x - 14, int(y) + HELI_H // 2 + 4), 2)
    pygame.draw.line(screen, GRAY,
        (x + 10, int(y) + HELI_H // 2),
        (x + 10, int(y) + HELI_H // 2 + 4), 2)
    pygame.draw.line(screen, GRAY,
        (x - 18, int(y) + HELI_H // 2 + 4),
        (x + 14, int(y) + HELI_H // 2 + 4), 2)
 
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if game_over:
                reset_game()
            else:
                started = True
                holding = True
        elif event.type == pygame.MOUSEBUTTONUP:
            holding = False
 
    if started and not game_over:
        frame += 1
        rotor_frame += 1
 
        # Physics
        if holding:
            heli_vy += LIFT
        heli_vy += GRAVITY
        heli_vy = max(-6, min(6, heli_vy))
        heli_y += heli_vy
 
        # Scroll cave
        if len(cave_top) > 0:
            cave_top.pop(0)
            cave_bot.pop(0)
        add_cave_segment()
 
        # Speed up gradually
        if frame % 200 == 0 and scroll_speed < 4.5:
            scroll_speed += 0.2
 
        # Pillar logic
        pillar_timer += 1
        if pillar_timer >= PILLAR_INTERVAL:
            pillar_timer = 0
            # Get cave bounds at right edge
            ct = cave_top[-1]
            cb = cave_bot[-1]
            gap_h = cb - ct
            if gap_h > MIN_GAP + 40:
                # Place pillar from top or bottom
                if random.random() < 0.5:
                    ph = random.randint(30, gap_h // 2 - 30)
                    pillars.append([float(W + 10), ct, PILLAR_W, ph, "top"])
                else:
                    ph = random.randint(30, gap_h // 2 - 30)
                    pillars.append([float(W + 10), cb - ph, PILLAR_W, ph, "bot"])
 
        # Move pillars
        for p in pillars:
            p[0] -= scroll_speed
        pillars = [p for p in pillars if p[0] + p[2] > -10]
 
        # Score
        score = frame // 10
 
        # Collision with cave
        seg_idx = heli_x // CAVE_SEG_W
        if 0 <= seg_idx < len(cave_top):
            ct = cave_top[seg_idx]
            cb = cave_bot[seg_idx]
            if heli_y - HELI_H // 2 < ct or heli_y + HELI_H // 2 > cb:
                game_over = True
                if score > best_score:
                    best_score = score
 
        # Collision with pillars
        heli_rect = pygame.Rect(heli_x - HELI_W // 2 + 4, int(heli_y) - HELI_H // 2 + 2,
                                HELI_W - 8, HELI_H - 4)
        for p in pillars:
            pr = pygame.Rect(int(p[0]), int(p[1]), p[2], p[3])
            if heli_rect.colliderect(pr):
                game_over = True
                if score > best_score:
                    best_score = score
 
        # Off screen
        if heli_y < 0 or heli_y > H:
            game_over = True
            if score > best_score:
                best_score = score
    else:
        rotor_frame += 1
 
    # Draw
    screen.fill(SKY)
 
    # Background stars
    random.seed(77)
    for _ in range(30):
        sx = random.randint(0, W)
        sy = random.randint(0, H)
        pygame.draw.circle(screen, (60, 60, 80), (sx, sy), 1)
    random.seed()
 
    # Draw cave
    for i in range(len(cave_top) - 1):
        x = i * CAVE_SEG_W
        # Top wall
        pygame.draw.rect(screen, CAVE_COLOR, (x, 0, CAVE_SEG_W + 1, cave_top[i]))
        pygame.draw.line(screen, CAVE_EDGE, (x, cave_top[i]), (x + CAVE_SEG_W, cave_top[i + 1] if i + 1 < len(cave_top) else cave_top[i]), 2)
        # Bottom wall
        pygame.draw.rect(screen, CAVE_COLOR, (x, cave_bot[i], CAVE_SEG_W + 1, H - cave_bot[i]))
        pygame.draw.line(screen, CAVE_EDGE, (x, cave_bot[i]), (x + CAVE_SEG_W, cave_bot[i + 1] if i + 1 < len(cave_bot) else cave_bot[i]), 2)
 
    # Draw pillars
    for p in pillars:
        pr = pygame.Rect(int(p[0]), int(p[1]), p[2], p[3])
        pygame.draw.rect(screen, PILLAR_COLOR, pr, border_radius=3)
        pygame.draw.rect(screen, PILLAR_EDGE, pr, 2, border_radius=3)
 
    # Draw helicopter
    if not game_over:
        draw_helicopter(heli_x, heli_y)
 
    # HUD
    font = pygame.font.Font(None, 32)
    st = font.render(f"Score: {score}", True, WHITE)
    screen.blit(st, (10, 10))
    bt = font.render(f"Best: {best_score}", True, (200, 200, 160))
    screen.blit(bt, (W - 130, 10))
 
    if game_over:
        overlay = pygame.Surface((W, H))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        screen.blit(overlay, (0, 0))
        bf = pygame.font.Font(None, 52)
        gt = bf.render("GAME OVER", True, (255, 60, 60))
        gr = gt.get_rect(center=(W // 2, H // 2 - 40))
        screen.blit(gt, gr)
        sf = pygame.font.Font(None, 34)
        st2 = sf.render(f"Score: {score}", True, WHITE)
        sr = st2.get_rect(center=(W // 2, H // 2))
        screen.blit(st2, sr)
        if score >= best_score and score > 0:
            nf = pygame.font.Font(None, 28)
            nt = nf.render("New Best!", True, (255, 255, 80))
            nr = nt.get_rect(center=(W // 2, H // 2 + 30))
            screen.blit(nt, nr)
        hf = pygame.font.Font(None, 26)
        ht = hf.render("Tap to restart", True, GRAY)
        hr = ht.get_rect(center=(W // 2, H // 2 + 65))
        screen.blit(ht, hr)
    elif not started:
        hf = pygame.font.Font(None, 30)
        ht = hf.render("Hold to fly up!", True, WHITE)
        hr = ht.get_rect(center=(W // 2, H // 2 + 80))
        screen.blit(ht, hr)
        sf = pygame.font.Font(None, 24)
        st3 = sf.render("Release to fall", True, GRAY)
        sr3 = st3.get_rect(center=(W // 2, H // 2 + 110))
        screen.blit(st3, sr3)
        draw_helicopter(heli_x, heli_y)
 
    pygame.display.flip()
    clock.tick(30)
 
pygame.quit()