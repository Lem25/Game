import pygame
from constants import TILE, FPS, TRAP_STATS
from colors import BLACK, WHITE

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

    def update(self, enemies):
        dt = 1.0 / FPS
        self.timer += dt

        if self.trap_type == 'fire':
            trap_x, trap_y = self.grid_pos
            per_tick = self.dps * dt
            
            for e in enemies:
                ex, ey = e.grid_pos()
                distance = max(abs(ex - trap_x), abs(ey - trap_y))
                
                if distance == 0:
                    e.hp -= per_tick
                elif distance == 1:
                    e.hp -= per_tick * 0.5
                elif distance == 2:
                    e.hp -= per_tick * 0.25
        
        elif self.trap_type == 'spikes':
            affected = [e for e in enemies if e.grid_pos() == self.grid_pos]
            if not affected:
                return
            if self.timer >= self.interval:
                for e in affected:
                    e.hp -= self.damage
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
