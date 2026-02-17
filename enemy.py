import pygame
import random
import math
from constants import TILE, ENEMY_STATS, FPS
from colors import ENEMY_COLORS
from pathfinding import astar
from status_effects import StatusEffect
try:
    from assets import get as get_asset
except Exception:
    get_asset = None

ENEMY_SIZE_SCALE = {
    'tank': 6,
    'fighter': 4,
    'swarm': 2.5,
    'mage': 3.5,
    'assassin': 3,
    'healer': 3.5,
    'minotaur_boss': 9,
    'demon_boss': 12,
}

_PATH_CACHE = {}
_PATH_CACHE_VERSION = 0


def invalidate_path_cache():
    global _PATH_CACHE_VERSION
    _PATH_CACHE_VERSION += 1
    _PATH_CACHE.clear()

class Enemy:
    def __init__(self, grid, spawn, goal, enemy_type, scale=1.0):
        self.grid = grid
        self.type = enemy_type
        stats = ENEMY_STATS[enemy_type]
        self.max_hp = int(stats['max_hp'] * scale)
        self.hp = self.max_hp
        self.base_speed = (stats['speed'] * scale) / 1.5
        self.speed = self.base_speed
        self.base_resist_phys = stats.get('resist_phys', 0)
        self.base_resist_magic = stats.get('resist_magic', 0)
        self.resist_phys = self.base_resist_phys
        self.resist_magic = self.base_resist_magic
        base_size = stats.get('size', ENEMY_SIZE_SCALE.get(enemy_type, 6))
        self.size = base_size * 0.9 * (1.0 if scale <= 1.0 else (1.0 + (scale - 1.0) * 0.5))
        self.color = ENEMY_COLORS[enemy_type]
        self.reward = stats['reward']
        self.reward = int(self.reward * scale)
        self.spawn_tile = spawn
        self.lane_id = spawn
        self.pos = pygame.Vector2(spawn[0] * TILE + TILE // 2, spawn[1] * TILE + TILE // 2)
        self.goal = goal
        self.path = []
        self.path_idx = 0
        self.dodge_chance = 0.20 if enemy_type == 'assassin' else 0.0
        self.dodge_streak = 0
        self.healer_chain_timer = 0.0
        self.healer_chain_interval = 1.2
        self.healer_chain_amount = 0.13 * self.max_hp
        self.fighter_shield_used = False
        self.shield_hp = 0.0
        self.mage_blocks_left = 3 if enemy_type == 'mage' else 0
        self.assassin_emergency_used = False
        self.tank_bulwark_active = False
        self.minotaur_phase2 = False
        self.minotaur_stun_cooldown = 1.5
        self.demon_phase1_done = False
        self.demon_phase2_done = False
        self.demon_phase3_done = False
        self.slow_stacks = 0.0
        self.slow_decay_rate = 0.3
        self.frozen_time = 0.0
        self.freeze_immunity_timer = 0.0
        self.burning = False
        self.status_effects = {}
        self.impaled_time = 0.0
        self.is_boss = enemy_type in ('minotaur_boss', 'demon_boss')
        self.freeze_resist = 0.0
        
        self.repath()

    def _set_status(self, effect_type, duration, strength=0.0, stack_strength=True):
        existing = self.status_effects.get(effect_type)
        if existing and existing.active:
            existing.duration = max(existing.duration, duration)
            if stack_strength:
                existing.strength += strength
            else:
                existing.strength = max(existing.strength, strength)
        else:
            self.status_effects[effect_type] = StatusEffect(effect_type, duration, strength)

    def add_status(self, effect_type, duration, strength=0.0):
        if self.type == 'minotaur_boss' and self.minotaur_phase2 and effect_type in ('slow', 'frozen', 'impale'):
            return
        self._set_status(effect_type, duration, strength, stack_strength=True)

    def has_status(self, effect_type):
        effect = self.status_effects.get(effect_type)
        return bool(effect and effect.active)

    def _update_status_effects(self, dt):
        for effect in list(self.status_effects.values()):
            effect.tick(dt)
            if effect.type == 'slow' and effect.strength > 0:
                effect.strength = max(0.0, effect.strength - self.slow_decay_rate * dt)
            if not effect.active:
                del self.status_effects[effect.type]

        slow_effect = self.status_effects.get('slow')
        self.slow_stacks = slow_effect.strength if slow_effect else 0.0

        impale = self.status_effects.get('impale')
        self.impaled_time = impale.duration if impale and impale.active else 0.0

        burn = self.status_effects.get('burn')
        self.burning = bool(burn and burn.active)

        mark = self.status_effects.get('mark')
        self.damage_taken_mult = (1.0 + mark.strength) if mark and mark.active else 1.0

        bleed = self.status_effects.get('bleed')
        bleeding = bool(bleed and bleed.active)

        if self.burning:
            self.take_damage(3.5 * dt, 'magic', source='trap')

        if bleeding:
            bleed_dps = 5.0 + (bleed.strength * 0.5)
            self.take_damage(bleed_dps * dt, 'physical', source='trap')

    def repath(self):
        start = self.grid_pos()
        cache_key = (_PATH_CACHE_VERSION, id(self.grid), start, self.goal)
        cached = _PATH_CACHE.get(cache_key)
        if cached is None:
            cached = astar(self.grid, start, self.goal)
            _PATH_CACHE[cache_key] = list(cached)
        self.path = list(cached)
        if self.path and len(self.path) > 1:
            self.path = self.path[1:]
        self.path_idx = 0

    def grid_pos(self):
        return (int(self.pos.x // TILE), int(self.pos.y // TILE))

    def logic(self, enemies, dt, towers=None, spawn_points=None, goal_grid=None):
        if self.freeze_immunity_timer > 0:
            self.freeze_immunity_timer = max(0.0, self.freeze_immunity_timer - dt)

        self._update_status_effects(dt)

        self._apply_health_behaviors(enemies)
        self._apply_boss_behaviors(enemies, towers or [], spawn_points or [], goal_grid or self.goal, dt)

        movement_impairment_immune = self.type == 'minotaur_boss' and self.minotaur_phase2
        if movement_impairment_immune:
            self.status_effects.pop('slow', None)
            self.status_effects.pop('frozen', None)
            self.status_effects.pop('impale', None)
            self.slow_stacks = 0.0
            self.impaled_time = 0.0

        if self.impaled_time > 0 and not movement_impairment_immune:
            return
        
        if not self.path or self.path_idx >= len(self.path):
            self.repath()
            if not self.path:
                self.hp = 0
                return

        if self.has_status('frozen') and not movement_impairment_immune:
            return

        if self.slow_stacks >= 10 and self.freeze_immunity_timer <= 0 and not movement_impairment_immune:
            base_duration = 1.5
            resist = max(0.0, min(0.99, getattr(self, 'freeze_resist', 0.0)))
            final_duration = max(base_duration * 0.2, base_duration * (1.0 - resist))
            self.status_effects['frozen'] = StatusEffect('frozen', final_duration, 1.0)
            self.freeze_immunity_timer = 2.0
            if 'slow' in self.status_effects:
                del self.status_effects['slow']
            self.slow_stacks = 0.0
            return

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
        step = self.speed * slow_multiplier * dt * FPS
        self.pos += direction * step

        if self.type == 'healer':
            self.healer_chain_timer += dt
            if self.healer_chain_timer >= self.healer_chain_interval:
                self.healer_chain_timer = 0.0
                self._chain_heal_lane(enemies)

    def take_damage(self, incoming_dmg, dmg_type, source='generic', resist_override=None):
        if self.type == 'mage' and source == 'projectile' and self.mage_blocks_left > 0:
            self.mage_blocks_left -= 1
            return False

        if self.type == 'assassin' and random.random() < self.dodge_chance:
            self.dodge_streak += 1
            self.dodge_chance = max(0.05, self.dodge_chance - 0.02)
            return False

        resist = resist_override
        if resist is None:
            resist = self.resist_phys if dmg_type == 'physical' else self.resist_magic

        actual_dmg = max(0.0, incoming_dmg * (1 - resist))
        actual_dmg *= getattr(self, 'damage_taken_mult', 1.0)

        if self.shield_hp > 0 and actual_dmg > 0:
            absorbed = min(self.shield_hp, actual_dmg)
            self.shield_hp -= absorbed
            actual_dmg -= absorbed

        self.hp -= actual_dmg
        return True

    def _apply_health_behaviors(self, enemies):
        if self.type == 'fighter' and not self.fighter_shield_used and self.hp <= self.max_hp * 0.5:
            self.fighter_shield_used = True
            self.shield_hp = self.max_hp * 0.30

        if self.type == 'assassin' and not self.assassin_emergency_used and self.hp <= self.max_hp * 0.3:
            self.assassin_emergency_used = True
            healers = [e for e in enemies if e.type == 'healer' and e.hp > 0 and e is not self]
            if healers:
                nearest_healer = min(healers, key=lambda h: self.pos.distance_to(h.pos))
                self.pos = nearest_healer.pos.copy()
                self.repath()
            else:
                self.dodge_chance = max(self.dodge_chance, 0.50)
                self.speed *= 1.2

        if self.type == 'tank' and not self.tank_bulwark_active and self.hp <= self.max_hp * 0.3:
            self.tank_bulwark_active = True
            self.resist_phys = min(0.95, self.base_resist_phys * 2)
            self.resist_magic = min(0.95, self.base_resist_magic * 2)

        if self.type == 'minotaur_boss' and not self.minotaur_phase2 and self.hp <= self.max_hp * 0.3:
            self.minotaur_phase2 = True
            self.resist_phys = 0.0
            self.resist_magic = 0.0
            self.speed = self.base_speed * 3.5
            self.status_effects.pop('slow', None)
            self.status_effects.pop('frozen', None)
            self.status_effects.pop('impale', None)
            self.slow_stacks = 0.0
            self.impaled_time = 0.0

    def _apply_boss_behaviors(self, enemies, towers, spawn_points, goal_grid, dt):
        if self.type == 'minotaur_boss' and not self.minotaur_phase2:
            self.minotaur_stun_cooldown -= dt
            if self.minotaur_stun_cooldown <= 0 and towers:
                nearest_tower = min(towers, key=lambda t: self.pos.distance_to(t.pos))
                if self.pos.distance_to(nearest_tower.pos) <= 170:
                    current_stun = getattr(nearest_tower, 'stun_timer', 0.0)
                    nearest_tower.stun_timer = max(current_stun, 2.5)
                self.minotaur_stun_cooldown = 3.5

        if self.type != 'demon_boss':
            return

        if not self.demon_phase1_done and len(spawn_points) >= 2 and towers:
            self.demon_phase1_done = self._swap_lane_towers(towers, spawn_points)

        if not self.demon_phase2_done and self.hp <= self.max_hp * 0.5:
            self.demon_phase2_done = True
            self._spawn_demon_minions(enemies)

        if not self.demon_phase3_done and self.hp <= self.max_hp * 0.25:
            if self._teleport_to_beneficial_point(goal_grid):
                self.demon_phase3_done = True

    def _chain_heal_lane(self, enemies):
        lane_allies = [
            e for e in enemies
            if e is not self and e.hp > 0 and e.lane_id == self.lane_id and e.hp < e.max_hp
        ]
        lane_allies.sort(key=lambda e: (e.hp / max(1, e.max_hp), self.pos.distance_to(e.pos)))

        for ally in lane_allies[:3]:
            ally.hp = min(ally.max_hp, ally.hp + self.healer_chain_amount)

    def _swap_lane_towers(self, towers, spawn_points):
        lane_a, lane_b = random.sample(spawn_points, 2)

        def lane_center(tile):
            return pygame.Vector2(tile[0] * TILE + TILE // 2, tile[1] * TILE + TILE // 2)

        center_a = lane_center(lane_a)
        center_b = lane_center(lane_b)

        def nearest_lane(tower):
            dist_a = tower.pos.distance_to(center_a)
            dist_b = tower.pos.distance_to(center_b)
            return 'a' if dist_a <= dist_b else 'b'

        towers_a = [t for t in towers if nearest_lane(t) == 'a']
        towers_b = [t for t in towers if nearest_lane(t) == 'b']
        if not towers_a or not towers_b:
            return False

        towers_a.sort(key=lambda t: t.pos.distance_to(center_a))
        towers_b.sort(key=lambda t: t.pos.distance_to(center_b))
        pairs = min(len(towers_a), len(towers_b))

        for idx in range(pairs):
            tower_a = towers_a[idx]
            tower_b = towers_b[idx]
            pos_a = tower_a.pos.copy()
            tower_a.pos = tower_b.pos.copy()
            tower_b.pos = pos_a
            if hasattr(tower_a, 'grid_pos'):
                tower_a.grid_pos = (int(tower_a.pos.x // TILE), int(tower_a.pos.y // TILE))
            if hasattr(tower_b, 'grid_pos'):
                tower_b.grid_pos = (int(tower_b.pos.x // TILE), int(tower_b.pos.y // TILE))
        return True

    def _spawn_demon_minions(self, enemies):
        minion_types = ['fighter', 'fighter', 'assassin', 'mage']
        summon_tile = self.grid_pos()
        for minion_type in minion_types:
            minion = Enemy(self.grid, summon_tile, self.goal, minion_type, scale=0.9)
            minion.lane_id = self.lane_id
            enemies.append(minion)

    def _teleport_to_beneficial_point(self, goal_grid):
        if not self.path or self.path_idx >= len(self.path):
            self.repath()
            if not self.path:
                return False

        current_remaining = len(self.path) - self.path_idx
        candidates = []
        for idx in range(self.path_idx + 3, len(self.path)):
            tile = self.path[idx]
            goal_dist = abs(tile[0] - goal_grid[0]) + abs(tile[1] - goal_grid[1])
            remaining = len(self.path) - idx
            if goal_dist >= 5 and remaining < current_remaining:
                candidates.append((idx, tile))

        if not candidates:
            return False

        teleport_idx, teleport_tile = random.choice(candidates[-max(1, len(candidates) // 2):])
        self.pos = pygame.Vector2(teleport_tile[0] * TILE + TILE // 2, teleport_tile[1] * TILE + TILE // 2)
        self.path_idx = teleport_idx
        return True

    def add_slow(self, amount):
        if self.type == 'minotaur_boss' and self.minotaur_phase2:
            return
        if self.freeze_immunity_timer > 0:
            return
        self._set_status('slow', 5.0, amount, stack_strength=True)
        slow_effect = self.status_effects.get('slow')
        if slow_effect:
            slow_effect.strength = min(12.0, slow_effect.strength)

    def apply_impale(self, duration):
        if self.type == 'minotaur_boss' and self.minotaur_phase2:
            return
        self._set_status('impale', duration, 0.0, stack_strength=False)

    def apply_burn(self, duration=2.5, strength=1.0):
        self._set_status('burn', duration, strength, stack_strength=False)

    def apply_bleed(self, duration=3.0, strength=1.0):
        self._set_status('bleed', duration, strength, stack_strength=False)

    def apply_mark(self, duration=4.0, strength=0.2):
        self._set_status('mark', duration, strength, stack_strength=False)

    def draw(self, screen):
        sprite = None
        if get_asset:
            sprite = get_asset(f"enemy_{self.type}", size=int(self.size * 1.6))
        if sprite:
            rect = sprite.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            screen.blit(sprite, rect.topleft)
        else:
            pygame.draw.circle(screen, self.color, (int(self.pos.x), int(self.pos.y)), int(self.size))

        is_frozen = self.has_status('frozen')

        if is_frozen or self.slow_stacks >= 10:
            outline_color = (100, 200, 255)
            outline_width = 3
            pygame.draw.circle(screen, outline_color, (int(self.pos.x), int(self.pos.y)), int(self.size) + outline_width, outline_width)
            tint = pygame.Surface((int(self.size * 2.4), int(self.size * 2.4)), pygame.SRCALPHA)
            pygame.draw.circle(tint, (120, 210, 255, 80), (tint.get_width() // 2, tint.get_height() // 2), int(self.size * 1.1))
            screen.blit(tint, (self.pos.x - tint.get_width() / 2, self.pos.y - tint.get_height() / 2))

            crack_len = int(self.size)
            center = (int(self.pos.x), int(self.pos.y))
            pygame.draw.line(screen, (220, 245, 255), (center[0] - crack_len, center[1]), (center[0] + crack_len, center[1]), 1)
            pygame.draw.line(screen, (220, 245, 255), (center[0], center[1] - crack_len), (center[0], center[1] + crack_len), 1)
            pygame.draw.line(screen, (180, 230, 255), (center[0] - crack_len // 2, center[1] - crack_len // 2), (center[0] + crack_len // 2, center[1] + crack_len // 2), 1)
        elif self.slow_stacks > 0:
            slow_intensity = int(100 + (self.slow_stacks / 10) * 70)
            outline_color = (100, slow_intensity, 255)
            outline_width = max(1, int(self.slow_stacks / 5))
            pygame.draw.circle(screen, outline_color, (int(self.pos.x), int(self.pos.y)), int(self.size) + outline_width, outline_width)

            particle_count = min(6, int(self.slow_stacks // 2) + 1)
            for idx in range(particle_count):
                angle = (idx / max(1, particle_count)) * 6.283
                offset_x = int((self.size + 4) * 0.8 * math.cos(angle))
                offset_y = int((self.size + 4) * 0.8 * math.sin(angle))
                pygame.draw.circle(screen, (140, 220, 255), (int(self.pos.x) + offset_x, int(self.pos.y) + offset_y), 2)

        bar_w, bar_h = 12, 2
        fill_w = max(0, (self.hp / self.max_hp) * bar_w)
        bar_x = int(self.pos.x - 6)
        bar_y = int(self.pos.y - 10)
        pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(screen, (255, 50, 50), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(screen, (50, 255, 50), (bar_x, bar_y, fill_w, bar_h))

        if self.shield_hp > 0:
            max_shield_hp = max(1.0, self.max_hp * 0.30)
            shield_ratio = max(0.0, min(1.0, self.shield_hp / max_shield_hp))
            shield_w = max(1, int(bar_w * shield_ratio))
            shield_overlay = pygame.Surface((shield_w, bar_h), pygame.SRCALPHA)
            shield_overlay.fill((255, 230, 80, 160))
            screen.blit(shield_overlay, (bar_x, bar_y))

        if self.slow_stacks > 0 or is_frozen:
            meter_w, meter_h = 12, 2
            meter_fill = meter_w if is_frozen else max(0, min(meter_w, (self.slow_stacks / 10.0) * meter_w))
            meter_x = int(self.pos.x - 6)
            meter_y = int(self.pos.y - 14)
            pygame.draw.rect(screen, (20, 30, 45), (meter_x, meter_y, meter_w, meter_h))
            pygame.draw.rect(screen, (120, 210, 255), (meter_x, meter_y, meter_fill, meter_h))
            if is_frozen or self.slow_stacks >= 10:
                pygame.draw.circle(screen, (190, 240, 255), (meter_x - 3, meter_y + 1), 2)
