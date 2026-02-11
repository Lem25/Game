import pygame

from projectiles import IceLaser, Projectile
try:
    from assets import get as get_asset
except Exception:
    get_asset = None

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
        self.lasers = {}

    def in_range(self, enemy):
        return self.pos.distance_to(enemy.pos) < self.range

    def update(self, enemies):
        self.cooldown = max(0, self.cooldown - 1)
        if self.type != 'ice' and self.cooldown > 0:
            return None
        if not enemies:
            if self.type == 'ice' and self.lasers:
                for laser in self.lasers.values():
                    laser.active = False
                self.lasers.clear()
            return None
        if self.type == 'ice':
            in_range_enemies = [e for e in enemies if self.in_range(e)]
            if not in_range_enemies:
                for laser in self.lasers.values():
                    laser.active = False
                self.lasers.clear()
                return None

            active_targets = {id(e) for e in in_range_enemies}
            for target_id, laser in list(self.lasers.items()):
                if target_id not in active_targets:
                    laser.active = False
                    del self.lasers[target_id]

            new_lasers = []
            for enemy in in_range_enemies:
                target_id = id(enemy)
                laser = self.lasers.get(target_id)
                if not laser or not laser.active or laser.target is not enemy:
                    laser = IceLaser(self, enemy)
                    self.lasers[target_id] = laser
                    new_lasers.append(laser)

            return new_lasers if new_lasers else None

        nearest_enemy = min(enemies, key=lambda e: self.pos.distance_to(e.pos), default=None)
        if not nearest_enemy or not self.in_range(nearest_enemy):
            return None

        projectile = Projectile(self.pos, nearest_enemy, self.dmg, self.dmg_type, self.type)
        self.cooldown = 60
        return projectile

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
