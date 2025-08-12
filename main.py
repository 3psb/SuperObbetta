# SuperObbetta - main.py
import pygame, sys
from pathlib import Path
import math

# Config
WIDTH, HEIGHT = 900, 600
FPS = 60
GRAVITY = 0.5
PLAYER_SPEED = 4.5
JUMP_POWER = 11
TILE_SIZE = 64

ASSET_DIR = Path(__file__).parent / "assets"

# Helper
def load_image(name, fallback_size=None):
    p = ASSET_DIR / name
    try:
        img = pygame.image.load(str(p)).convert_alpha()
        return img
    except Exception as e:
        if fallback_size:
            s = pygame.Surface(fallback_size, pygame.SRCALPHA)
            s.fill((255,0,255,255))
            return s
        raise e

# Classes
class Camera:
    def __init__(self):
        self.x = 0
    def apply(self, rect):
        return rect.move(-self.x, 0)
    def update(self, target_rect):
        target_x = target_rect.centerx - WIDTH * 0.33
        if target_x > 0:
            self.x = target_x

class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = load_image("player.png")
        self.rect = self.image.get_rect(topleft=pos)
        self.vel = pygame.math.Vector2(0,0)
        self.on_ground = False
        self.coins = 0
        self.facing = 1
        self.shoot_cool = 0
        self.shot_toggle = 0  # alternate lipstick/smalto

    def update(self, platforms, keys, projectiles_group):
        # horizontal movement
        self.vel.x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel.x = -PLAYER_SPEED; self.facing = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel.x = PLAYER_SPEED; self.facing = 1

        # apply gravity
        self.vel.y += GRAVITY
        if self.vel.y > 18: self.vel.y = 18

        # jump
        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
            self.vel.y = -JUMP_POWER
            try:
                pygame.mixer.Sound(str(ASSET_DIR/"music"/"jump.wav")).play()
            except:
                pass
            self.on_ground = False

        # shoot (Z or LCTRL)
        if (keys[pygame.K_z] or keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]) and self.shoot_cool <= 0:
            self.shoot(projectiles_group)
            self.shoot_cool = 12  # frames cooldown
        if self.shoot_cool > 0:
            self.shoot_cool -= 1

        # move and collide
        self.rect.x += int(self.vel.x)
        self.collide(platforms, "x")
        self.rect.y += int(self.vel.y)
        self.on_ground = False
        self.collide(platforms, "y")

    def collide(self, platforms, dir):
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if dir == "x":
                    if self.vel.x > 0:
                        self.rect.right = p.rect.left
                    elif self.vel.x < 0:
                        self.rect.left = p.rect.right
                    self.vel.x = 0
                elif dir == "y":
                    if self.vel.y > 0:
                        self.rect.bottom = p.rect.top
                        self.on_ground = True
                        self.vel.y = 0
                    elif self.vel.y < 0:
                        self.rect.top = p.rect.bottom
                        self.vel.y = 0

    def shoot(self, projectiles_group):
        # alternate lipstick and smalto, unlimited ammo
        proj_type = "rossetto" if self.shot_toggle % 2 == 0 else "smalto"
        self.shot_toggle += 1
        px = self.rect.centerx + (20 * self.facing)
        py = self.rect.centery - 8
        p = Projectile(px, py, self.facing, proj_type)
        projectiles_group.add(p)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w=TILE_SIZE, h=TILE_SIZE//2):
        super().__init__()
        try:
            tile = load_image("tiles/ground.png")
            tile = pygame.transform.scale(tile, (w,h))
            self.image = tile
        except:
            self.image = pygame.Surface((w,h), pygame.SRCALPHA)
            self.image.fill((100,50,20))
        self.rect = self.image.get_rect(topleft=(x,y))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_width=150):
        super().__init__()
        try:
            self.image = load_image("enemy.png")
        except:
            self.image = pygame.Surface((40,40))
            self.image.fill((180,40,40))
        self.rect = self.image.get_rect(midbottom=(x,y))
        self.start_x = x
        self.patrol = patrol_width
        self.speed = 1.7

    def update(self):
        self.rect.x += self.speed
        if self.rect.x > self.start_x + self.patrol:
            self.speed = -abs(self.speed)
        if self.rect.x < self.start_x - self.patrol:
            self.speed = abs(self.speed)

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            self.image = load_image("coin.png")
        except:
            self.image = pygame.Surface((20,20), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (255,215,0), (10,10), 10)
        self.rect = self.image.get_rect(center=(x,y))

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, ptype="rossetto"):
        super().__init__()
        try:
            if ptype=="rossetto":
                self.image = load_image("rossetto.png")
            else:
                self.image = load_image("smalto.png")
        except:
            self.image = pygame.Surface((10,6), pygame.SRCALPHA)
            self.image.fill((255,0,255))
        self.rect = self.image.get_rect(center=(x,y))
        self.vx = 8 * direction
        self.vy = -1.2  # slight arc
        self.ptype = ptype

    def update(self):
        self.rect.x += int(self.vx)
        self.vy += 0.18  # gravity on projectile slightly
        self.rect.y += int(self.vy)
        # remove if off-screen (beyond a big range)
        if self.rect.x < -2000 or self.rect.x > 20000 or self.rect.y > 2000:
            self.kill()

# Levels builder
def build_level(index):
    plats = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    coins = pygame.sprite.Group()

    if index == 1:
        plats.add(Platform(0, HEIGHT-64, 3000, 64))
        plats.add(Platform(400, HEIGHT-160, 160))
        plats.add(Platform(700, HEIGHT-240, 160))
        plats.add(Platform(1100, HEIGHT-200, 220))
        enemies.add(Enemy(600, HEIGHT-64, 200))
        enemies.add(Enemy(1250, HEIGHT-200, 120))
        coins.add(Coin(420, HEIGHT-200 - 30))
        coins.add(Coin(720, HEIGHT-240 - 30))
        level_length = 1800
    elif index == 2:
        plats.add(Platform(0, HEIGHT-64, 3000, 64))
        plats.add(Platform(350, HEIGHT-220, 200))
        plats.add(Platform(620, HEIGHT-300, 200))
        plats.add(Platform(950, HEIGHT-220, 200))
        enemies.add(Enemy(500, HEIGHT-64, 300))
        enemies.add(Enemy(900, HEIGHT-220, 160))
        for i, x in enumerate([380, 660, 980, 1400, 1500]):
            coins.add(Coin(x, HEIGHT-220 - 30))
        level_length = 2200
    else:
        plats.add(Platform(0, HEIGHT-64, 4000, 64))
        plats.add(Platform(450, HEIGHT-200, 200))
        plats.add(Platform(800, HEIGHT-260, 200))
        enemies.add(Enemy(700, HEIGHT-64, 400))
        enemies.add(Enemy(1700, HEIGHT-64, 500))
        for i, x in enumerate(range(500, 1900, 200)):
            coins.add(Coin(x+40, HEIGHT-64 - 30))
        level_length = 3000

    return plats, enemies, coins, level_length

# Main
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("SuperObbetta")
    clock = pygame.time.Clock()

    # try load background music
    try:
        pygame.mixer.init()
        bg = pygame.mixer.Sound(str(ASSET_DIR/"music"/"bg1.wav"))
        bg.set_volume(0.4)
        bg.play(loops=-1)
    except:
        pass

    try:
        bg1 = load_image("tiles/bg_layer1.png")
    except:
        bg1 = None

    player = Player((50, HEIGHT-200))
    level = 1
    plats, enemies, coins, level_length = build_level(level)
    projectiles = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group(player)
    camera = Camera()

    font = pygame.font.SysFont(None, 28)
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        player.update(plats.sprites(), keys, projectiles)
        enemies.update()
        projectiles.update()

        # collisions: projectile vs enemy
        for p in projectiles:
            hit = pygame.sprite.spritecollideany(p, enemies)
            if hit:
                hit.kill()
                p.kill()

        # collisions: player vs enemies
        hits = pygame.sprite.spritecollide(player, enemies, False)
        for e in hits:
            if player.vel.y > 0:
                e.kill()
                player.vel.y = -6
            else:
                player.rect.topleft = (50, HEIGHT-200)
                player.vel = pygame.math.Vector2(0,0)
                player.coins = max(0, player.coins - 3)

        # player vs coins
        coin_hits = pygame.sprite.spritecollide(player, coins, dokill=True)
        for c in coin_hits:
            player.coins += 1

        camera.update(player.rect)

        # draw
        screen.fill((140,200,255))
        if bg1:
            bgw = bg1.get_width()
            start_x = -int(camera.x * 0.3) % bgw
            x = start_x - bgw
            while x < WIDTH + bgw:
                screen.blit(bg1, (x, 0))
                x += bgw

        for p in plats:
            screen.blit(p.image, camera.apply(p.rect))
        for c in coins:
            screen.blit(c.image, camera.apply(c.rect))
        for e in enemies:
            screen.blit(e.image, camera.apply(e.rect))
        for pr in projectiles:
            screen.blit(pr.image, camera.apply(pr.rect))
        screen.blit(player.image, camera.apply(player.rect))

        txt = font.render(f"Level: {level}   Coins: {player.coins}", True, (20,20,20))
        screen.blit(txt, (10,10))

        if player.rect.centerx > level_length - 50:
            level += 1
            if level > 3:
                win_txt = font.render("Hai completato SuperObbetta! Premi ESC per uscire.", True, (0,0,0))
                screen.blit(win_txt, (WIDTH//2 - 220, HEIGHT//2))
                pygame.display.flip()
                waiting = True
                while waiting:
                    for ev in pygame.event.get():
                        if ev.type == pygame.QUIT:
                            waiting = False
                            running = False
                        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                            waiting = False
                            running = False
                    clock.tick(30)
                break
            else:
                plats, enemies, coins, level_length = build_level(level)
                player.rect.topleft = (50, HEIGHT - 200)
                camera.x = 0

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
