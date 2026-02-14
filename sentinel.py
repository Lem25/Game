import pygame
from constants import TILE, FPS
from colors import BLACK

class Sentinel:
    """Tower that creates barriers when enemies approach"""
    def __init__(self, pos):
        self.pos = pos
        self.grid_pos = (int(pos.x // TILE), int(pos.y // TILE))
        self.hp = 100
        self.max_hp = 100
        self.duration = 5.0
        self.timer = 0.0
        self.barrier_active = False
        self.name = "Sentinel"
        self.range = 100
        self.cooldown = 0.0
        self.cooldown_duration = 10.0
        self.size = 8
        
        self.path1_level = 0
        self.path2_level = 0
        self.reflect_damage = 0.0
        self.pulse_enabled = False
        self.overload_enabled = False
        self.pulse_timer = 0.0
        self.pulse_interval = 2.0
    
    def get_upgrade_info(self, path):
        """Get upgrade name and cost for the specified path"""
        if path == 1:
            if self.path1_level == 0:
                return ("Barrier", 100)
            elif self.path1_level == 1:
                return ("Reflect", 200)
        elif path == 2:
            if self.path2_level == 0:
                return ("Pulse", 110)
            elif self.path2_level == 1:
                return ("Overload", 220)
        return (None, 0)
    
    def can_upgrade(self, path):
        """Check if sentinel can be upgraded on specified path"""
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
            if self.path1_level == 1:
                self.duration = 8.0
                self.range = 130
            elif self.path1_level == 2:
                self.reflect_damage = 3.0
                    
        elif path == 2:
            self.path2_level += 1
            if self.path2_level == 1:
                self.pulse_enabled = True
                self.cooldown_duration = 8.0
            elif self.path2_level == 2:
                self.overload_enabled = True
        return True

    def _apply_damage(self, enemy, amount, dmg_type):
        if hasattr(enemy, 'take_damage'):
            enemy.take_damage(amount, dmg_type, source='sentinel')
        else:
            shield_hp = getattr(enemy, 'shield_hp', 0.0)
            remaining = max(0.0, amount)
            if shield_hp > 0 and remaining > 0:
                absorbed = min(shield_hp, remaining)
                enemy.shield_hp = shield_hp - absorbed
                remaining -= absorbed
            enemy.hp -= remaining

    def _deactivate_barrier(self):
        self.barrier_active = False
        self.cooldown = self.cooldown_duration
        self.timer = 0.0

    def _handle_barrier_expire(self, enemies):
        if self.overload_enabled:
            for enemy in enemies:
                if self.pos.distance_to(enemy.pos) < 100:
                    self._apply_damage(enemy, 100, 'magic')
        self._deactivate_barrier()

    def _handle_barrier_block(self, enemies, dt):
        for enemy in enemies:
            if enemy.grid_pos() != self.grid_pos:
                continue

            direction = enemy.pos - self.pos
            if direction.length() > 0:
                direction.normalize_ip()
                enemy.pos -= direction * 2

            if self.reflect_damage > 0:
                self._apply_damage(enemy, self.reflect_damage * dt, 'physical')

    def _handle_pulse(self, enemies):
        if not self.pulse_enabled or self.pulse_timer < self.pulse_interval:
            return

        for enemy in enemies:
            if self.pos.distance_to(enemy.pos) < 80:
                direction = enemy.pos - self.pos
                if direction.length() > 0:
                    direction.normalize_ip()
                    enemy.pos += direction * 30
        self.pulse_timer = 0.0

    def _try_activate_barrier(self, enemies):
        if self.cooldown != 0:
            return

        for enemy in enemies:
            if self.pos.distance_to(enemy.pos) < self.range:
                self.barrier_active = True
                self.timer = 0.0
                self.pulse_timer = 0.0
                break
    
    def update(self, enemies, dt):
        """Update sentinel state"""
        if self.cooldown > 0:
            self.cooldown = max(0, self.cooldown - dt)

        if self.barrier_active:
            self.timer += dt
            self.pulse_timer += dt

            if self.timer >= self.duration:
                self._handle_barrier_expire(enemies)
                return

            self._handle_barrier_block(enemies, dt)
            self._handle_pulse(enemies)
            return

        self._try_activate_barrier(enemies)
    
    def draw(self, screen, selected=False):
        """Draw the sentinel tower"""
        tower_color = (80, 180, 240)
        pygame.draw.circle(screen, tower_color, (int(self.pos.x), int(self.pos.y)), self.size)
        pygame.draw.circle(screen, (50, 150, 200), (int(self.pos.x), int(self.pos.y)), self.size, 2)

        if selected:
            range_surf = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
            circle_color = (100, 200, 255, 50)
            pygame.draw.circle(range_surf, circle_color, (self.range, self.range), self.range)
            screen.blit(range_surf, (self.pos.x - self.range, self.pos.y - self.range))

        if self.barrier_active:
            gx, gy = self.grid_pos
            barrier_rect = pygame.Rect(gx * TILE, gy * TILE, TILE, TILE)
            barrier_color = (100, 200, 255, 180)
            barrier_surf = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
            pygame.draw.rect(barrier_surf, barrier_color, (0, 0, TILE, TILE))
            pygame.draw.rect(barrier_surf, (50, 150, 255), (0, 0, TILE, TILE), 3)
            screen.blit(barrier_surf, (gx * TILE, gy * TILE))

            if self.pulse_enabled and self.pulse_timer < 0.3:
                pulse_surf = pygame.Surface((160, 160), pygame.SRCALPHA)
                pulse_alpha = int(100 * (1 - self.pulse_timer / 0.3))
                pygame.draw.circle(pulse_surf, (100, 200, 255, pulse_alpha), (80, 80), 80, 3)
                screen.blit(pulse_surf, (self.pos.x - 80, self.pos.y - 80))

            time_left = max(0, self.duration - self.timer)
            time_text = f"{time_left:.1f}s"
            try:
                font = pygame.font.SysFont("arial", 10)
                text_surf = font.render(time_text, True, (255, 255, 255))
                text_rect = text_surf.get_rect(center=(self.pos.x, self.pos.y - 15))
                screen.blit(text_surf, text_rect)
            except Exception:
                pass

        elif self.cooldown > 0:
            cooldown_text = f"CD: {self.cooldown:.1f}s"
            try:
                font = pygame.font.SysFont("arial", 9)
                text_surf = font.render(cooldown_text, True, (255, 100, 100))
                text_rect = text_surf.get_rect(center=(self.pos.x, self.pos.y - 15))
                screen.blit(text_surf, text_rect)
            except Exception:
                pass
