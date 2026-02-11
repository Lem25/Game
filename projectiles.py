import math
import pygame

try:
    from assets import get as get_asset
except Exception:
    get_asset = None


class Projectile:
    def __init__(self, start_pos, target_enemy, dmg, dmg_type, tower_type):
        self.pos = pygame.Vector2(start_pos)
        self.target = target_enemy
        self.dmg = dmg
        self.dmg_type = dmg_type
        self.tower_type = tower_type
        self.speed = 300
        self.size = 4
        self.color = (0, 100, 255) if tower_type == 'physical' else (148, 0, 211)
        self.angle = 0

        self.sprite = None
        if get_asset:
            if tower_type == 'physical':
                self.sprite = get_asset('arrow_proj', size=12)
            else:
                self.sprite = get_asset('missile_proj', size=12)

    def update(self, dt):
        if not self.target:
            return False

        direction = self.target.pos - self.pos
        distance = direction.length()

        if distance < self.speed * dt:
            if self.tower_type == 'ice':
                self.target.add_slow(2)
            else:
                self.target.take_damage(self.dmg, self.dmg_type)
            return False

        self.angle = math.degrees(math.atan2(direction.y, direction.x))
        direction.normalize_ip()
        self.pos += direction * self.speed * dt
        return True

    def draw(self, screen):
        if self.sprite:
            rotated_sprite = pygame.transform.rotate(self.sprite, -self.angle)
            rect = rotated_sprite.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            screen.blit(rotated_sprite, rect.topleft)
        else:
            pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), self.size)


class IceLaser:
    def __init__(self, tower, target_enemy, freeze_delay=1.0):
        self.tower = tower
        self.target = target_enemy
        self.freeze_delay = freeze_delay
        self.time_on_target = 0.0
        self.active = True
        self.initial_slow_applied = False
        self.color = (120, 220, 255)
        self.width = 3

    def update(self, dt):
        if not self.target or self.target.hp <= 0:
            self.active = False
            return False

        if not self.tower.in_range(self.target):
            self.active = False
            return False

        if not self.initial_slow_applied:
            self.target.add_slow(2)
            self.initial_slow_applied = True

        self.time_on_target += dt
        if self.time_on_target >= self.freeze_delay:
            self.target.add_slow(10)
            self.time_on_target = 0.0

        return True

    def draw(self, screen):
        if not self.target:
            return
        start = (int(self.tower.pos.x), int(self.tower.pos.y))
        end = (int(self.target.pos.x), int(self.target.pos.y))
        pygame.draw.line(screen, self.color, start, end, self.width)
        pygame.draw.circle(screen, self.color, end, 4)
