import pygame
import math
from constants import TILE
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

class Tower:
    def __init__(self, pos, ttype):
        self.pos = pos
        self.type = ttype
        self.dmg_type = ttype
        if ttype == 'physical':
            self.dmg = 18
            self.color = (0, 100, 255)
        elif ttype == 'magic':
            self.dmg = 15
            self.color = (148, 0, 211)
        else:
            self.dmg = 0
            self.color = (100, 200, 255)
        self.range = 120
        self.cooldown = 0
        self.size = 8
        self.ice_shots = 0

    def in_range(self, enemy):
        return self.pos.distance_to(enemy.pos) < self.range

    def update(self, enemies):
        self.cooldown = max(0, self.cooldown - 1)
        if self.cooldown > 0:
            return None
        if not enemies:
            return None
        nearest_enemy = min(enemies, key=lambda e: self.pos.distance_to(e.pos), default=None)
        if nearest_enemy and self.in_range(nearest_enemy):
            if self.type == 'ice':
                self.ice_shots += 1
                if self.ice_shots % 2 == 0:
                    projectile = Projectile(self.pos, nearest_enemy, 0, 'ice', self.type)
                    self.cooldown = 60
                    return projectile
            else:
                projectile = Projectile(self.pos, nearest_enemy, self.dmg, self.dmg_type, self.type)
                self.cooldown = 60
                return projectile
        return None

    def draw(self, screen, selected=False):
        sprite = None
        if get_asset:
            key = 'tower_physical' if self.type == 'physical' else ('tower_magic' if self.type == 'magic' else 'towe_ice')
            sprite = get_asset(key, size=int(self.size * 3))
        if sprite:
            rect = sprite.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            screen.blit(sprite, rect.topleft)
        else:
            pygame.draw.circle(screen, self.color, self.pos, self.size)
        if selected:
            range_surf = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
            circle_color = self.color + (50,)
            pygame.draw.circle(range_surf, circle_color, (self.range, self.range), self.range)
            screen.blit(range_surf, (self.pos.x - self.range, self.pos.y - self.range))
