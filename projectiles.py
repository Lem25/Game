import math
import pygame

try:
    from assets import get as get_asset
except Exception:
    get_asset = None


class Projectile:
    def __init__(self, start_pos, target_enemy, dmg, dmg_type, tower_type, tower=None):
        self.pos = pygame.Vector2(start_pos)
        self.target = target_enemy
        self.dmg = dmg
        self.dmg_type = dmg_type
        self.tower_type = tower_type
        self.tower = tower
        self.speed = 300
        self.size = 4
        self.color = (0, 100, 255) if tower_type == 'physical' else (148, 0, 211)
        self.angle = 0
        self.bounces_left = 0
        self.hit_enemies = set()

        if tower and hasattr(tower, 'bounce_enabled') and tower.bounce_enabled:
            self.bounces_left = 1

        if tower and hasattr(tower, 'chain_enabled') and tower.chain_enabled:
            self.is_chain = True
        else:
            self.is_chain = False

        self.sprite = None
        if get_asset:
            if tower_type == 'physical':
                self.sprite = get_asset('arrow_proj', size=12)
            else:
                self.sprite = get_asset('missile_proj', size=12)

    def update(self, dt, enemies=None):
        if not self.target:
            return False

        direction = self.target.pos - self.pos
        distance = direction.length()

        if distance < self.speed * dt:
            self.hit_enemies.add(id(self.target))
            
            if self.tower_type == 'ice':
                self.target.add_slow(2)
            else:
                if self.tower and hasattr(self.tower, 'armor_pierce') and self.tower.armor_pierce > 0:
                    original_resist = self.target.resist_phys if self.dmg_type == 'physical' else self.target.resist_magic
                    effective_resist = max(0, original_resist - self.tower.armor_pierce)
                    self.target.take_damage(self.dmg, self.dmg_type, source='projectile', resist_override=effective_resist)
                else:
                    self.target.take_damage(self.dmg, self.dmg_type, source='projectile')

                if self.tower and hasattr(self.tower, 'shatter_bonus') and self.tower.shatter_bonus > 0:
                    if hasattr(self.target, 'slow_stacks') and self.target.slow_stacks >= 10:
                        self.target.take_damage(self.dmg * self.tower.shatter_bonus, self.dmg_type, source='projectile')

                if self.is_chain and self.tower and enemies:
                    chain_count = getattr(self.tower, 'chain_count', 0)
                    if chain_count > 0:
                        self._chain_to_nearby(enemies, chain_count)

                if self.tower and hasattr(self.tower, 'aoe_enabled') and self.tower.aoe_enabled and enemies:
                    aoe_radius = getattr(self.tower, 'aoe_radius', 80)
                    for enemy in enemies:
                        if enemy != self.target and self.target.pos.distance_to(enemy.pos) < aoe_radius:
                            enemy.take_damage(self.dmg * 0.5, self.dmg_type, source='projectile')

            if self.bounces_left > 0 and enemies:
                self.bounces_left -= 1
                nearest_new_target = None
                min_dist = float('inf')
                for enemy in enemies:
                    if id(enemy) not in self.hit_enemies and enemy.hp > 0:
                        dist = self.pos.distance_to(enemy.pos)
                        if dist < 150 and dist < min_dist:
                            min_dist = dist
                            nearest_new_target = enemy
                
                if nearest_new_target:
                    self.target = nearest_new_target
                    return True
            
            return False

        self.angle = math.degrees(math.atan2(direction.y, direction.x))
        direction.normalize_ip()
        self.pos += direction * self.speed * dt
        return True
    
    def _chain_to_nearby(self, enemies, count):
        chained = 0
        for enemy in enemies:
            if enemy != self.target and self.target.pos.distance_to(enemy.pos) < 100 and chained < count:
                enemy.take_damage(self.dmg * 0.7, self.dmg_type, source='projectile')

                if self.tower and hasattr(self.tower, 'status_spread') and self.tower.status_spread:
                    if hasattr(self.target, 'slow_stacks') and self.target.slow_stacks > 0:
                        enemy.add_slow(self.target.slow_stacks * 0.5)
                
                chained += 1

    def draw(self, screen):
        if self.sprite:
            rotated_sprite = pygame.transform.rotate(self.sprite, -self.angle)
            rect = rotated_sprite.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            screen.blit(rotated_sprite, rect.topleft)
        else:
            pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), self.size)


class ProjectilePool:
    def __init__(self):
        self._pool = []

    def acquire(self, start_pos, target_enemy, dmg, dmg_type, tower_type, tower=None):
        if self._pool:
            projectile = self._pool.pop()
            projectile.pos = pygame.Vector2(start_pos)
            projectile.target = target_enemy
            projectile.dmg = dmg
            projectile.dmg_type = dmg_type
            projectile.tower_type = tower_type
            projectile.tower = tower
            projectile.speed = 300
            projectile.size = 4
            projectile.color = (0, 100, 255) if tower_type == 'physical' else (148, 0, 211)
            projectile.angle = 0
            projectile.bounces_left = 1 if tower and hasattr(tower, 'bounce_enabled') and tower.bounce_enabled else 0
            projectile.hit_enemies = set()
            projectile.is_chain = bool(tower and hasattr(tower, 'chain_enabled') and tower.chain_enabled)
            projectile.sprite = None
            if get_asset:
                if tower_type == 'physical':
                    projectile.sprite = get_asset('arrow_proj', size=12)
                else:
                    projectile.sprite = get_asset('missile_proj', size=12)
            return projectile

        return Projectile(start_pos, target_enemy, dmg, dmg_type, tower_type, tower)

    def release(self, projectile):
        if projectile:
            self._pool.append(projectile)


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

    def update(self, dt, enemies=None):
        if not self.active:
            return False

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
