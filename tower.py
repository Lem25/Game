import pygame

from projectiles import IceLaser, Projectile
try:
    from assets import get as get_asset
except Exception:
    get_asset = None

class Tower:
    TARGETING_MODES = ['first', 'last', 'strongest', 'weakest', 'closest_goal']

    def __init__(self, pos, ttype):
        self.pos = pos
        self.type = ttype
        self.dmg_type = ttype
        if ttype == 'physical':
            self.dmg = 20
            self.color = (0, 100, 255)
            self.name = "Archer Tower"
        elif ttype == 'magic':
            self.dmg = 18
            self.color = (148, 0, 211)
            self.name = "Magic Tower"
        else:
            self.dmg = 0
            self.color = (100, 200, 255)
            self.name = "Ice Tower"
        self.range = 130
        self.cooldown = 0
        self.size = 8
        self.stun_timer = 0.0
        self.lasers = {}

        self.path1_level = 0
        self.path2_level = 0
        self.armor_pierce = 0.0
        self.projectile_count = 1
        self.bounce_enabled = False
        self.chain_enabled = False
        self.chain_count = 0
        self.status_spread = False
        self.aoe_enabled = False
        self.aoe_radius = 0
        self.pull_enabled = False
        self.freeze_duration = 0.8
        self.shatter_bonus = 0.0
        self.slow_aoe = False
        self.absolute_zero = False
        self.targeting_mode = 'first'
        self.attack_interval = 0.8

    def cycle_targeting_mode(self):
        idx = self.TARGETING_MODES.index(self.targeting_mode)
        self.targeting_mode = self.TARGETING_MODES[(idx + 1) % len(self.TARGETING_MODES)]

    def _targeting_key(self, enemy):
        if self.targeting_mode == 'strongest':
            return enemy.max_hp
        if self.targeting_mode == 'weakest':
            return -enemy.hp
        if self.targeting_mode == 'closest_goal':
            goal_distance = abs(enemy.grid_pos()[0] - enemy.goal[0]) + abs(enemy.grid_pos()[1] - enemy.goal[1])
            return -goal_distance

        path_length = max(1, len(getattr(enemy, 'path', [])))
        progress = getattr(enemy, 'path_idx', 0) / path_length
        if self.targeting_mode == 'last':
            return -progress
        return progress

    def _select_target(self, enemies):
        if not enemies:
            return None
        return max(enemies, key=self._targeting_key)

    def get_upgrade_info(self, path):
        if path == 1:
            if self.type == 'physical':
                if self.path1_level == 0:
                    return ("Sniper", 120)
                elif self.path1_level == 1:
                    return ("Elite", 240)
            elif self.type == 'magic':
                if self.path1_level == 0:
                    return ("Bolt", 140)
                elif self.path1_level == 1:
                    return ("Arc", 280)
            elif self.type == 'ice':
                if self.path1_level == 0:
                    return ("Glacial", 130)
                elif self.path1_level == 1:
                    return ("Shatter", 260)
        elif path == 2:
            if self.type == 'physical':
                if self.path2_level == 0:
                    return ("Volley", 110)
                elif self.path2_level == 1:
                    return ("Bounce", 220)
            elif self.type == 'magic':
                if self.path2_level == 0:
                    return ("Nova", 160)
                elif self.path2_level == 1:
                    return ("Vortex", 320)
            elif self.type == 'ice':
                if self.path2_level == 0:
                    return ("Blizzard", 150)
                elif self.path2_level == 1:
                    return ("Absolute Zero", 300)
        return (None, 0)

    def can_upgrade(self, path):
        if path == 1:
            return self.path1_level < 2 and self.path2_level == 0
        elif path == 2:
            return self.path2_level < 2 and self.path1_level == 0
        return False

    def upgrade(self, path):
        if not self.can_upgrade(path):
            return False
        
        if path == 1:
            self.path1_level += 1
            if self.type == 'physical':
                if self.path1_level == 1:
                    self.range = 220
                    self.dmg = 24
                elif self.path1_level == 2:
                    self.armor_pierce = 0.6
                    self.dmg = 32
            elif self.type == 'magic':
                if self.path1_level == 1:
                    self.chain_enabled = True
                    self.chain_count = 3
                elif self.path1_level == 2:
                    self.chain_count = 4
                    self.status_spread = True
            elif self.type == 'ice':
                if self.path1_level == 1:
                    self.freeze_duration = 0.45
                elif self.path1_level == 2:
                    self.shatter_bonus = 0.7
                    
        elif path == 2:
            self.path2_level += 1
            if self.type == 'physical':
                if self.path2_level == 1:
                    self.projectile_count = 4
                elif self.path2_level == 2:
                    self.bounce_enabled = True
            elif self.type == 'magic':
                if self.path2_level == 1:
                    self.aoe_enabled = True
                    self.aoe_radius = 90
                elif self.path2_level == 2:
                    self.pull_enabled = True
                    self.aoe_radius = 120
            elif self.type == 'ice':
                if self.path2_level == 1:
                    self.slow_aoe = True
                elif self.path2_level == 2:
                    self.slow_aoe = False
                    self.absolute_zero = True
        return True

    def in_range(self, enemy):
        return self.pos.distance_to(enemy.pos) < self.range

    def update(self, enemies, dt=1.0 / 60.0, spatial_index=None, projectile_pool=None):
        self.cooldown = max(0.0, self.cooldown - dt)
        if self.type != 'ice' and self.cooldown > 0:
            return None
        if not enemies:
            if self.type == 'ice' and self.lasers:
                for laser in self.lasers.values():
                    laser.active = False
                self.lasers.clear()
            return None
        
        if self.type == 'ice':
            if spatial_index:
                in_range_enemies = [e for e in spatial_index.query_radius(self.pos, self.range) if self.in_range(e) and e.hp > 0]
            else:
                in_range_enemies = [e for e in enemies if self.in_range(e) and e.hp > 0]
            if not in_range_enemies:
                for laser in self.lasers.values():
                    laser.active = False
                self.lasers.clear()
                return None

            if self.slow_aoe:
                for enemy in in_range_enemies:
                    enemy.add_slow(0.5)

            max_targets = len(in_range_enemies) if self.slow_aoe else 1
            target_enemies = sorted(in_range_enemies, key=self._targeting_key, reverse=True)[:max_targets]

            if self.absolute_zero:
                for enemy in target_enemies:
                    enemy.add_slow(10)
            
            active_targets = {id(e) for e in target_enemies}
            for target_id, laser in list(self.lasers.items()):
                if target_id not in active_targets:
                    laser.active = False
                    del self.lasers[target_id]

            new_lasers = []
            for enemy in target_enemies:
                target_id = id(enemy)
                laser = self.lasers.get(target_id)
                if not laser or not laser.active or laser.target is not enemy:
                    laser = IceLaser(self, enemy, freeze_delay=self.freeze_duration)
                    self.lasers[target_id] = laser
                    new_lasers.append(laser)

            return new_lasers if new_lasers else None

        if self.type == 'magic' and self.pull_enabled:
            if spatial_index:
                in_range_enemies = [e for e in spatial_index.query_radius(self.pos, self.range) if self.in_range(e) and e.hp > 0]
            else:
                in_range_enemies = [e for e in enemies if self.in_range(e) and e.hp > 0]
            for enemy in in_range_enemies:
                direction = self.pos - enemy.pos
                if direction.length() > 20:
                    direction.normalize_ip()
                    enemy.pos += direction * 0.5

        if self.type == 'magic' and self.aoe_enabled:
            if spatial_index:
                in_range = [e for e in spatial_index.query_radius(self.pos, self.range) if self.in_range(e) and e.hp > 0]
            else:
                in_range = [e for e in enemies if self.in_range(e) and e.hp > 0]
            target_enemy = self._select_target(in_range)
            if target_enemy:
                if projectile_pool:
                    projectile = projectile_pool.acquire(self.pos, target_enemy, self.dmg, self.dmg_type, self.type, self)
                else:
                    projectile = Projectile(self.pos, target_enemy, self.dmg, self.dmg_type, self.type, self)
                self.cooldown = self.attack_interval
                return projectile
            return None

        if spatial_index:
            in_range = [e for e in spatial_index.query_radius(self.pos, self.range) if self.in_range(e) and e.hp > 0]
        else:
            in_range = [e for e in enemies if self.in_range(e) and e.hp > 0]

        nearest_enemy = self._select_target(in_range)
        if not nearest_enemy:
            return None

        if self.projectile_count > 1:
            projectiles = []
            targets = sorted(in_range, key=self._targeting_key, reverse=True)[:self.projectile_count]
            for target in targets:
                if projectile_pool:
                    projectile = projectile_pool.acquire(self.pos, target, self.dmg, self.dmg_type, self.type, self)
                else:
                    projectile = Projectile(self.pos, target, self.dmg, self.dmg_type, self.type, self)
                projectiles.append(projectile)
            self.cooldown = self.attack_interval
            return projectiles if projectiles else None
        
        if projectile_pool:
            projectile = projectile_pool.acquire(self.pos, nearest_enemy, self.dmg, self.dmg_type, self.type, self)
        else:
            projectile = Projectile(self.pos, nearest_enemy, self.dmg, self.dmg_type, self.type, self)
        self.cooldown = self.attack_interval
        return projectile

    def draw(self, screen, selected=False):
        sprite = None
        if get_asset:
            key = 'tower_physical' if self.type == 'physical' else ('tower_magic' if self.type == 'magic' else 'tower_ice')
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
