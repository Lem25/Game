import pygame
import random
from constants import TILE, ENEMY_STATS, FPS
from colors import ENEMY_COLORS
from pathfinding import astar
try:
    from assets import get as get_asset
except Exception:
    get_asset = None

ENEMY_SIZE_SCALE = {
    'tank': 6,
    'fighter': 4,
    'mage': 3.5,
    'assassin': 3,
    'healer': 3.5,
    'mini_boss': 8,
    'boss': 12,
    'minotaur_boss': 9,
    'demon_boss': 12,
}

class Enemy:
    def __init__(self, grid, spawn, goal, enemy_type, scale=1.0):
        self.grid = grid
        self.type = enemy_type
        stats = ENEMY_STATS[enemy_type]
        self.max_hp = int(stats['max_hp'] * scale)
        self.hp = self.max_hp
        self.speed = (stats['speed'] * scale) / 1.5
        self.resist_phys = stats.get('resist_phys', 0)
        self.resist_magic = stats.get('resist_magic', 0)
        base_size = stats.get('size', ENEMY_SIZE_SCALE.get(enemy_type, 6))
        self.size = base_size * 0.9 * (1.0 if scale <= 1.0 else (1.0 + (scale - 1.0) * 0.5))
        self.color = ENEMY_COLORS[enemy_type]
        self.reward = stats['reward']
        self.reward = int(self.reward * scale)
        self.pos = pygame.Vector2(spawn[0] * TILE + TILE // 2, spawn[1] * TILE + TILE // 2)
        self.goal = goal
        self.path = []
        self.path_idx = 0
        self.dodge_chance = 0.10 if enemy_type == 'assassin' else 0.0
        self.dodge_streak = 0
        self.heal_per_update = (0.05 * self.max_hp / FPS) if enemy_type == 'healer' else 0
        self.slow_stacks = 0
        self.slow_decay_rate = 0.3
        self.frozen_time = 0.0
        self.freeze_immunity_timer = 0.0
        
        self.repath()

    def repath(self):
        self.path = astar(self.grid, self.grid_pos(), self.goal)
        if self.path and len(self.path) > 1:
            self.path = self.path[1:]
        self.path_idx = 0

    def grid_pos(self):
        return (int(self.pos.x // TILE), int(self.pos.y // TILE))

    def logic(self, enemies, dt):
        if self.freeze_immunity_timer > 0:
            self.freeze_immunity_timer = max(0.0, self.freeze_immunity_timer - dt)

        self.slow_stacks = max(0.0, self.slow_stacks - self.slow_decay_rate * dt)
        
        if not self.path or self.path_idx >= len(self.path):
            self.repath()
            if not self.path:
                self.hp = 0
                return

        if self.slow_stacks >= 10:
            if self.freeze_immunity_timer <= 0:
                self.frozen_time += dt
                if self.frozen_time >= 3.0:
                    self.freeze_immunity_timer = 2.0
                    self.frozen_time = 0.0
                    self.slow_stacks = 0.0
            return
        else:
            self.frozen_time = 0.0

        target = pygame.Vector2(
            self.path[self.path_idx][0] * TILE + TILE // 2,
            self.path[self.path_idx][1] * TILE + TILE // 2
        )

        diff = target - self.pos
        distance = diff.length()

        if distance < self.speed * 1.5:
            self.path_idx += 1
            return

        direction = diff.normalize()
        slow_multiplier = max(0.1, 1.0 - (self.slow_stacks * 0.08))

        self.pos += direction * self.speed * slow_multiplier

        if self.heal_per_update > 0:
            heal_radius = 120
            for other in enemies:
                if other is not self and self.pos.distance_to(other.pos) < heal_radius:
                    other.hp = min(other.max_hp, other.hp + self.heal_per_update)

    def take_damage(self, incoming_dmg, dmg_type):
        resist = self.resist_phys if dmg_type == 'physical' else self.resist_magic
        actual_dmg = incoming_dmg * (1 - resist)
        if random.random() < self.dodge_chance and self.type == 'assassin':
            self.dodge_streak += 1
            self.dodge_chance = max(0.01, 0.10 - 0.01 * self.dodge_streak)
            return False
        self.hp -= actual_dmg
        return True

    def add_slow(self, amount):
        if self.freeze_immunity_timer > 0:
            return
        self.slow_stacks = min(12, self.slow_stacks + amount)

    def draw(self, screen):
        sprite = None
        if get_asset:
            sprite = get_asset(f"enemy_{self.type}", size=int(self.size * 1.6))
        if sprite:
            rect = sprite.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            screen.blit(sprite, rect.topleft)
        else:
            pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), int(self.size))

        if self.slow_stacks >= 10:
            outline_color = (100, 200, 255)
            outline_width = 3
            pygame.draw.circle(screen, outline_color, (int(self.pos.x), int(self.pos.y)), int(self.size) + outline_width, outline_width)
        elif self.slow_stacks > 0:
            slow_intensity = int(100 + (self.slow_stacks / 10) * 70)
            outline_color = (100, slow_intensity, 255)
            outline_width = max(1, int(self.slow_stacks / 5))
            pygame.draw.circle(screen, outline_color, (int(self.pos.x), int(self.pos.y)), int(self.size) + outline_width, outline_width)

        bar_w, bar_h = 12, 2
        fill_w = max(0, (self.hp / self.max_hp) * bar_w)
        pygame.draw.rect(screen, (0, 0, 0), (int(self.pos.x - 6), int(self.pos.y - 10), bar_w, bar_h))
        pygame.draw.rect(screen, (255, 50, 50), (int(self.pos.x - 6), int(self.pos.y - 10), bar_w, bar_h))
        pygame.draw.rect(screen, (50, 255, 50), (int(self.pos.x - 6), int(self.pos.y - 10), fill_w, bar_h))
