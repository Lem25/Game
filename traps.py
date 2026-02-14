import pygame
from constants import TILE, FPS, TRAP_STATS
from colors import BLACK

class Trap:
    def __init__(self, grid_pos, trap_type):
        self.grid_pos = grid_pos
        self.trap_type = trap_type
        self.pos = pygame.Vector2(grid_pos[0] * TILE + TILE // 2, grid_pos[1] * TILE + TILE // 2)
        self.timer = 0.0
        stats = TRAP_STATS.get(trap_type, {})
        self.dps = stats.get('dps', 0)
        self.damage = stats.get('damage', 0)
        self.interval = stats.get('interval', 1.0)
        self.name = "Fire Trap" if trap_type == 'fire' else "Spike Trap"
        
        self.path1_level = 0
        self.path2_level = 0
        self.aura_radius = 2
        self.revive_available = False
        self.has_revived = False
        self.burn_spread = False
        self.explode_on_kill = False
        self.bleed_enabled = False
        self.impale_enabled = False
        self.cluster_enabled = False
        self.quake_enabled = False
    
    def get_upgrade_info(self, path):
        """Get upgrade name and cost for the specified path"""
        if path == 1:
            if self.trap_type == 'fire':
                if self.path1_level == 0:
                    return ("Inferno", 80)
                elif self.path1_level == 1:
                    return ("Phoenix", 180)
            elif self.trap_type == 'spikes':
                if self.path1_level == 0:
                    return ("Barbed", 70)
                elif self.path1_level == 1:
                    return ("Impale", 160)
        elif path == 2:
            if self.trap_type == 'fire':
                if self.path2_level == 0:
                    return ("Oil Slick", 90)
                elif self.path2_level == 1:
                    return ("Detonate", 200)
            elif self.trap_type == 'spikes':
                if self.path2_level == 0:
                    return ("Cluster", 80)
                elif self.path2_level == 1:
                    return ("Quake", 170)
        return (None, 0)
    
    def can_upgrade(self, path):
        """Check if trap can be upgraded on specified path"""
        if path == 1:
            return self.path1_level < 2 and self.path2_level == 0
        elif path == 2:
            return self.path2_level < 2 and self.path1_level == 0
        return False
    
    def upgrade(self, path):
        """Apply upgrade to the specified path"""
        if not self.can_upgrade(path):
            return False
        
        if path == 1:
            self.path1_level += 1
            if self.trap_type == 'fire':
                if self.path1_level == 1:
                    self.aura_radius = 3
                    self.dps = 45
                elif self.path1_level == 2:
                    self.revive_available = True
            elif self.trap_type == 'spikes':
                if self.path1_level == 1:
                    self.bleed_enabled = True
                    self.damage = 65
                elif self.path1_level == 2:
                    self.impale_enabled = True
                    
        elif path == 2:
            self.path2_level += 1
            if self.trap_type == 'fire':
                if self.path2_level == 1:
                    self.burn_spread = True
                elif self.path2_level == 2:
                    self.explode_on_kill = True
            elif self.trap_type == 'spikes':
                if self.path2_level == 1:
                    self.cluster_enabled = True
                elif self.path2_level == 2:
                    self.quake_enabled = True
        return True

    def _apply_damage(self, enemy, amount, dmg_type, source):
        if hasattr(enemy, 'take_damage'):
            enemy.take_damage(amount, dmg_type, source=source)
        else:
            shield_hp = getattr(enemy, 'shield_hp', 0.0)
            remaining = max(0.0, amount)
            if shield_hp > 0 and remaining > 0:
                absorbed = min(shield_hp, remaining)
                enemy.shield_hp = shield_hp - absorbed
                remaining -= absorbed
            enemy.hp -= remaining

    def _update_fire(self, enemies, dt):
        trap_x, trap_y = self.grid_pos
        per_tick = self.dps * dt

        for enemy in enemies:
            ex, ey = enemy.grid_pos()
            distance = max(abs(ex - trap_x), abs(ey - trap_y))

            if distance == 0:
                self._apply_damage(enemy, per_tick, 'magic', 'trap')
                if self.burn_spread and hasattr(enemy, 'apply_burn'):
                    enemy.apply_burn(2.5, 1.0)
            elif distance == 1:
                self._apply_damage(enemy, per_tick * 0.5, 'magic', 'trap')
                if self.burn_spread and hasattr(enemy, 'apply_burn'):
                    enemy.apply_burn(2.0, 0.7)
            elif distance == 2:
                self._apply_damage(enemy, per_tick * 0.25, 'magic', 'trap')
            elif distance <= self.aura_radius:
                self._apply_damage(enemy, per_tick * 0.15, 'magic', 'trap')

            if self.burn_spread and getattr(enemy, 'burning', False):
                for other in enemies:
                    if other != enemy and enemy.pos.distance_to(other.pos) < 40:
                        self._apply_damage(other, per_tick * 0.2, 'magic', 'trap')
                        if hasattr(other, 'apply_burn'):
                            other.apply_burn(1.5, 0.5)

    def _update_spikes_trigger(self, enemies, affected):
        for enemy in affected:
            initial_hp = enemy.hp
            self._apply_damage(enemy, self.damage, 'physical', 'trap')

            if self.bleed_enabled:
                if hasattr(enemy, 'apply_bleed'):
                    enemy.apply_bleed(duration=3.0, strength=1.0)

            if self.impale_enabled:
                if hasattr(enemy, 'apply_impale'):
                    enemy.apply_impale(2.0)
                elif hasattr(enemy, 'impaled_time'):
                    enemy.impaled_time = 2.0

            if enemy.hp <= 0 and initial_hp > 0 and self.explode_on_kill:
                for other in enemies:
                    if other != enemy and enemy.pos.distance_to(other.pos) < 60:
                        self._apply_damage(other, 40, 'magic', 'trap')

        if self.quake_enabled:
            trap_x, trap_y = self.grid_pos
            for enemy in enemies:
                ex, ey = enemy.grid_pos()
                distance = max(abs(ex - trap_x), abs(ey - trap_y))
                if distance <= 2 and enemy not in affected:
                    self._apply_damage(enemy, self.damage * 0.5, 'physical', 'trap')

        if self.cluster_enabled:
            trap_x, trap_y = self.grid_pos
            for enemy in enemies:
                ex, ey = enemy.grid_pos()
                distance = max(abs(ex - trap_x), abs(ey - trap_y))
                if distance == 1:
                    self._apply_damage(enemy, self.damage * 0.3, 'physical', 'trap')

    def update(self, enemies, dt=1.0 / FPS):
        self.timer += dt

        if self.trap_type == 'fire':
            self._update_fire(enemies, dt)
        
        elif self.trap_type == 'spikes':
            affected = [enemy for enemy in enemies if enemy.grid_pos() == self.grid_pos]

            if not affected:
                return

            if self.timer >= self.interval:
                self._update_spikes_trigger(enemies, affected)
                self.timer = 0.0

    def draw(self, screen):
        gx, gy = self.grid_pos
        try:
            from assets import get as get_asset
        except Exception:
            get_asset = None

        sprite = None
        if get_asset:
            key = 'trap_fire' if self.trap_type == 'fire' else 'trap_spikes'
            sprite = get_asset(key, size=TILE - 8)
        if sprite:
            rect = sprite.get_rect(center=(gx * TILE + TILE // 2, gy * TILE + TILE // 2))
            screen.blit(sprite, rect.topleft)
        else:
            rect = pygame.Rect(gx * TILE + 4, gy * TILE + 4, TILE - 8, TILE - 8)
            if self.trap_type == 'fire':
                color = (255, 100, 0)
            else:
                color = (150, 150, 150)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, BLACK, rect, 1)
