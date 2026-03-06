import pygame
import random
import sys
import math

pygame.init()

# ── Constants ─────────────────────────────────────────────────────────────────
WINDOW_WIDTH  = 700
WINDOW_HEIGHT = 700
CELL_SIZE     = 28
GRID_W        = WINDOW_WIDTH  // CELL_SIZE
GRID_H        = WINDOW_HEIGHT // CELL_SIZE
FPS           = 10

UP    = (0, -1)
DOWN  = (0,  1)
LEFT  = (-1, 0)
RIGHT = (1,  0)

# ── Palette ───────────────────────────────────────────────────────────────────
BG_DARK         = (34,  85,  34)
BG_LIGHT        = (40,  100, 40)
SNAKE_BODY_A    = (60,  179,  60)
SNAKE_BODY_B    = (45,  140,  45)
SNAKE_HEAD      = (30,  160,  50)
SNAKE_BELLY     = (200, 230, 170)
SCALE_COLOR     = (35,  120,  35)
EYE_WHITE       = (240, 240, 240)
EYE_PUPIL       = (20,   20,  20)
EYE_SHINE       = (255, 255, 255)
TONGUE_COLOR    = (200,  30,  30)
FOOD_RED        = (220,  40,  40)
FOOD_SHINE      = (255, 160, 160)
FOOD_STEM       = (80,  160,  60)
FOOD_LEAF       = (60,  200,  60)
SHADOW_COLOR    = (0,    0,    0,  80)
TEXT_COLOR      = (255, 255, 255)
SCORE_GLOW      = (100, 255, 100)
PANEL_COLOR     = (10,   30,  10, 200)
PARTICLE_COLORS = [(255,80,80),(255,160,80),(255,220,80),(255,255,150)]


# ── Particle ──────────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y):
        angle  = random.uniform(0, 2 * math.pi)
        speed  = random.uniform(2, 7)
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life     = random.randint(18, 35)
        self.max_life = self.life
        self.radius   = random.randint(3, 7)
        self.color    = random.choice(PARTICLE_COLORS)

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.2          # gravity
        self.life -= 1

    def draw(self, surface):
        alpha  = int(255 * self.life / self.max_life)
        radius = max(1, int(self.radius * self.life / self.max_life))
        surf   = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha), (radius, radius), radius)
        surface.blit(surf, (int(self.x) - radius, int(self.y) - radius))


# ── Food ──────────────────────────────────────────────────────────────────────
class Food:
    def __init__(self, snake_body):
        self.pos    = self._spawn(snake_body)
        self.wobble = 0.0          # animation timer

    def _spawn(self, snake_body):
        while True:
            p = (random.randint(1, GRID_W - 2),
                 random.randint(1, GRID_H - 2))
            if p not in snake_body:
                return p

    def respawn(self, snake_body):
        self.pos    = self._spawn(snake_body)
        self.wobble = 0.0

    def update(self):
        self.wobble += 0.15

    def draw(self, surface):
        x, y = self.pos
        cx   = x * CELL_SIZE + CELL_SIZE // 2
        cy   = y * CELL_SIZE + CELL_SIZE // 2

        bob  = math.sin(self.wobble) * 2          # gentle float
        r    = CELL_SIZE // 2 - 2

        # shadow
        shadow_surf = pygame.Surface((r * 2 + 4, r // 2 + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 60),
                            (0, 0, r * 2 + 4, r // 2 + 4))
        surface.blit(shadow_surf, (cx - r - 2, cy + r - 2))

        # body
        pygame.draw.circle(surface, FOOD_RED,   (cx, int(cy + bob)), r)
        pygame.draw.circle(surface, (180, 20, 20), (cx, int(cy + bob)), r, 2)

        # shine
        pygame.draw.circle(surface, FOOD_SHINE, (cx - r // 3, int(cy + bob) - r // 3), r // 3)

        # stem
        stem_x = cx
        stem_y = int(cy + bob) - r
        pygame.draw.line(surface, FOOD_STEM,
                         (stem_x, stem_y), (stem_x + 3, stem_y - 7), 3)

        # leaf
        leaf_pts = [
            (stem_x + 3, stem_y - 5),
            (stem_x + 10, stem_y - 9),
            (stem_x + 6,  stem_y - 2),
        ]
        pygame.draw.polygon(surface, FOOD_LEAF, leaf_pts)


# ── Snake ─────────────────────────────────────────────────────────────────────
class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        sx, sy         = GRID_W // 2, GRID_H // 2
        self.body      = [(sx, sy), (sx-1, sy), (sx-2, sy), (sx-3, sy)]
        self.direction  = RIGHT
        self.next_dir   = RIGHT
        self.grew       = False
        # tongue animation
        self.tongue_out    = False
        self.tongue_timer  = 0
        self.tongue_length = 0
        self.alive         = True

    def change_direction(self, d):
        if d != (-self.direction[0], -self.direction[1]):
            self.next_dir = d

    def move(self):
        self.direction = self.next_dir
        hx, hy   = self.body[0]
        dx, dy   = self.direction
        new_head = (hx + dx, hy + dy)
        self.body.insert(0, new_head)
        if not self.grew:
            self.body.pop()
        self.grew = False

        # tongue flick
        self.tongue_timer += 1
        if self.tongue_timer > random.randint(8, 16):
            self.tongue_out   = True
            self.tongue_timer = 0
        else:
            self.tongue_out = (self.tongue_timer < 3)

    def grow(self):
        self.grew = True

    def wall_hit(self):
        hx, hy = self.body[0]
        return hx < 0 or hx >= GRID_W or hy < 0 or hy >= GRID_H

    def self_hit(self):
        return self.body[0] in self.body[1:]

    # ── Drawing helpers ───────────────────────────────────────────
    def _cell_center(self, idx):
        x, y = self.body[idx]
        return (x * CELL_SIZE + CELL_SIZE // 2,
                y * CELL_SIZE + CELL_SIZE // 2)

    def _lerp_color(self, c1, c2, t):
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

    def draw(self, surface):
        n = len(self.body)

        # ── 1. Curved body segments (draw tail → head) ────────────
        for i in range(n - 1, -1, -1):
            cx, cy = self._cell_center(i)
            t      = i / max(n - 1, 1)

            # gradient green along body
            body_col = self._lerp_color(SNAKE_BODY_A, SNAKE_BODY_B, t)
            r        = max(5, CELL_SIZE // 2 - int(t * 4))

            # shadow
            pygame.draw.circle(surface, (0, 0, 0, 40), (cx + 2, cy + 3), r)
            # main body
            pygame.draw.circle(surface, body_col, (cx, cy), r)

            # belly stripe (lighter underside)
            belly_r = max(2, r - 5)
            pygame.draw.circle(surface, SNAKE_BELLY, (cx, cy), belly_r)
            pygame.draw.circle(surface, body_col, (cx, cy), belly_r - 3)

            # scale pattern
            if i % 2 == 0 and i != 0:
                scale_r = max(2, r // 3)
                pygame.draw.circle(surface, SCALE_COLOR,
                                   (cx, cy), scale_r, 1)

            # connector between segments
            if i < n - 1:
                nx, ny = self._cell_center(i + 1)
                pygame.draw.line(surface, body_col,
                                 (cx, cy), (nx, ny),
                                 max(4, (r * 2) - 2))

        # ── 2. Head ───────────────────────────────────────────────
        hcx, hcy = self._cell_center(0)
        hr       = CELL_SIZE // 2 + 2

        # head shadow
        pygame.draw.circle(surface, (0, 0, 0, 60), (hcx + 2, hcy + 3), hr)
        # head fill
        pygame.draw.circle(surface, SNAKE_HEAD, (hcx, hcy), hr)
        # head outline
        pygame.draw.circle(surface, (20, 120, 30), (hcx, hcy), hr, 2)
        # belly patch on head
        pygame.draw.ellipse(surface, SNAKE_BELLY,
                            (hcx - hr // 2, hcy - hr // 3,
                             hr, hr // 2 + 4))

        # ── 3. Eyes ───────────────────────────────────────────────
        dx, dy = self.direction
        # perpendicular offsets for two eyes
        perp = (-dy, dx)

        for side in (+1, -1):
            ex = hcx + dx * (hr // 2) + perp[0] * side * (hr // 2)
            ey = hcy + dy * (hr // 2) + perp[1] * side * (hr // 2)

            pygame.draw.circle(surface, EYE_WHITE,  (ex, ey), 5)
            pygame.draw.circle(surface, EYE_PUPIL,
                               (ex + dx, ey + dy), 3)
            pygame.draw.circle(surface, EYE_SHINE,
                               (ex + dx - 1, ey + dy - 1), 1)

        # ── 4. Tongue ─────────────────────────────────────────────
        if self.tongue_out:
            tx_start = hcx + dx * hr
            ty_start = hcy + dy * hr
            tongue_len = CELL_SIZE - 4
            tx_end = tx_start + dx * tongue_len
            ty_end = ty_start + dy * tongue_len
            # base
            pygame.draw.line(surface, TONGUE_COLOR,
                             (tx_start, ty_start),
                             (tx_end, ty_end), 2)
            # forked tips
            fork = 5
            perp_v = (-dy * fork, dx * fork)
            pygame.draw.line(surface, TONGUE_COLOR,
                             (tx_end, ty_end),
                             (tx_end + dx * fork + perp_v[0],
                              ty_end + dy * fork + perp_v[1]), 2)
            pygame.draw.line(surface, TONGUE_COLOR,
                             (tx_end, ty_end),
                             (tx_end + dx * fork - perp_v[0],
                              ty_end + dy * fork - perp_v[1]), 2)


# ── Background ────────────────────────────────────────────────────────────────
def build_grass(seed=42):
    """Pre-render a tiled grass background."""
    rng  = random.Random(seed)
    surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    for gy in range(GRID_H):
        for gx in range(GRID_W):
            checker = (gx + gy) % 2
            base    = BG_DARK if checker else BG_LIGHT
            # tiny random variation per tile
            noise   = rng.randint(-6, 6)
            color   = tuple(max(0, min(255, c + noise)) for c in base)
            rect    = pygame.Rect(gx * CELL_SIZE, gy * CELL_SIZE,
                                  CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surf, color, rect)

    # random grass blades
    for _ in range(300):
        bx = rng.randint(0, WINDOW_WIDTH - 1)
        by = rng.randint(0, WINDOW_HEIGHT - 1)
        blen = rng.randint(4, 10)
        bcol = (rng.randint(30, 60), rng.randint(110, 160), rng.randint(30, 60))
        pygame.draw.line(surf, bcol,
                         (bx, by), (bx + rng.randint(-3,3), by - blen), 1)
    return surf


# ── HUD ───────────────────────────────────────────────────────────────────────
def draw_hud(surface, score, high_score, font_lg, font_sm):
    # Panel
    panel = pygame.Surface((200, 64), pygame.SRCALPHA)
    panel.fill((10, 30, 10, 180))
    pygame.draw.rect(panel, (80, 180, 80), panel.get_rect(), 2, border_radius=8)
    surface.blit(panel, (8, 8))

    s_text  = font_lg.render(f"SCORE  {score:04d}", True, SCORE_GLOW)
    hs_text = font_sm.render(f"BEST   {high_score:04d}", True, TEXT_COLOR)
    surface.blit(s_text,  (18, 14))
    surface.blit(hs_text, (18, 42))


# ── Overlay Screen ────────────────────────────────────────────────────────────
def draw_overlay(surface, title, lines, big_font, med_font, sm_font):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 20, 0, 200))
    surface.blit(overlay, (0, 0))

    # glowing title
    for glow_r in range(6, 0, -2):
        glow_col = (0, 180, 0, 40)
        glow_surf = big_font.render(title, True, (0, min(255, 60 * glow_r), 0))
        gx = WINDOW_WIDTH  // 2 - glow_surf.get_width()  // 2
        gy = WINDOW_HEIGHT // 2 - 130
        surface.blit(glow_surf, (gx + glow_r, gy + glow_r))

    title_surf = big_font.render(title, True, SCORE_GLOW)
    surface.blit(title_surf,
                 (WINDOW_WIDTH  // 2 - title_surf.get_width()  // 2,
                  WINDOW_HEIGHT // 2 - 130))

    for i, (text, font, color) in enumerate(lines):
        t = font.render(text, True, color)
        surface.blit(t,
                     (WINDOW_WIDTH  // 2 - t.get_width()  // 2,
                      WINDOW_HEIGHT // 2 - 50 + i * 44))

    pygame.display.flip()


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("🐍 Realistic Snake")
    clock = pygame.time.Clock()

    big_font = pygame.font.SysFont("Arial", 56, bold=True)
    med_font = pygame.font.SysFont("Arial", 30, bold=True)
    sm_font  = pygame.font.SysFont("Arial", 22)
    hud_lg   = pygame.font.SysFont("Consolas", 20, bold=True)
    hud_sm   = pygame.font.SysFont("Consolas", 16)

    grass    = build_grass()
    high_score = 0
    particles  = []

    # ── Start screen ──────────────────────────────────────────────
    screen.blit(grass, (0, 0))
    draw_overlay(screen, "SNAKE",
                 [("A Realistic Experience",    med_font, (180, 255, 180)),
                  ("Use Arrow Keys or WASD",    sm_font,  TEXT_COLOR),
                  ("Press ANY KEY to begin",    sm_font,  SCORE_GLOW)],
                 big_font, med_font, sm_font)

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN: waiting = False
        clock.tick(30)

    # ── Game loop ─────────────────────────────────────────────────
    while True:
        snake      = Snake()
        food       = Food(snake.body)
        score      = 0
        particles  = []
        running    = True
        flash      = 0           # screen flash on eating

        while running:
            clock.tick(FPS)

            # events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if   event.key in (pygame.K_UP,    pygame.K_w): snake.change_direction(UP)
                    elif event.key in (pygame.K_DOWN,  pygame.K_s): snake.change_direction(DOWN)
                    elif event.key in (pygame.K_LEFT,  pygame.K_a): snake.change_direction(LEFT)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d): snake.change_direction(RIGHT)
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()

            # update
            snake.move()
            food.update()

            if snake.wall_hit() or snake.self_hit():
                running = False
                break

            # eat
            if snake.body[0] == food.pos:
                snake.grow()
                score += 10
                high_score = max(high_score, score)
                # spawn burst of particles at food location
                fx = food.pos[0] * CELL_SIZE + CELL_SIZE // 2
                fy = food.pos[1] * CELL_SIZE + CELL_SIZE // 2
                for _ in range(28):
                    particles.append(Particle(fx, fy))
                food.respawn(snake.body)
                flash = 8

            # update particles
            particles = [p for p in particles if p.life > 0]
            for p in particles:
                p.update()

            # ── Draw ──────────────────────────────────────────────
            screen.blit(grass, (0, 0))

            # flash overlay on eating
            if flash > 0:
                fl_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                fl_surf.fill((255, 255, 200, flash * 12))
                screen.blit(fl_surf, (0, 0))
                flash -= 1

            food.draw(screen)

            for p in particles:
                p.draw(screen)

            snake.draw(screen)
            draw_hud(screen, score, high_score, hud_lg, hud_sm)

            pygame.display.flip()

        # ── Death animation (brief) ────────────────────────────────
        for _ in range(20):
            clock.tick(30)
            red_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            red_surf.fill((180, 0, 0, 60))
            screen.blit(red_surf, (0, 0))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()

        # ── Game over screen ───────────────────────────────────────
        screen.blit(grass, (0, 0))
        snake.draw(screen)
        draw_overlay(screen, "GAME OVER",
                     [( f"Score: {score}  |  Best: {high_score}", med_font, SCORE_GLOW),
                      (  "Press R to Play Again",                 sm_font,  TEXT_COLOR),
                      (  "Press ESC to Quit",                     sm_font,  (180,180,180))],
                     big_font, med_font, sm_font)

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if   event.key == pygame.K_r:      waiting = False
                    elif event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
            clock.tick(30)


if __name__ == "__main__":
    main()
    