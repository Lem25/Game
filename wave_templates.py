import random


_EARLY_POOL = ['fighter', 'fighter', 'fighter', 'mage', 'fighter', 'assassin']
_MID_POOL = ['fighter', 'fighter', 'mage', 'assassin', 'tank', 'swarm']
_LATE_POOL = ['fighter', 'tank', 'mage', 'assassin', 'healer', 'swarm']
_BOSS_TYPES = {'minotaur_boss', 'demon_boss'}
_FALLBACK_TYPE = 'fighter'


def _get_phase_config(wave: int):
    if wave <= 5:
        return list(_EARLY_POOL), (0.0 if wave < 5 else 0.08)
    if wave <= 14:
        pool = list(_MID_POOL)
        if wave >= 12:
            pool.append('healer')
        return pool, 0.12

    pool = list(_LATE_POOL)
    if wave >= 20:
        pool.append('tank')
    return pool, 0.18


def get_wave_template(wave: int):
    base_pool, swarm_chance = _get_phase_config(wave)

    return {
        'pool': base_pool,
        'has_boss': wave % 5 == 0,
        'swarm_chance': swarm_chance,
    }


def choose_enemy_type(wave: int, enemies_alive, wave_enemies_left=None):
    template = get_wave_template(wave)
    can_spawn_swarm = wave_enemies_left is None or wave_enemies_left >= 10

    if can_spawn_swarm and random.random() < template['swarm_chance']:
        return 'swarm'

    pool = [enemy_type for enemy_type in template['pool'] if enemy_type not in _BOSS_TYPES]
    if not can_spawn_swarm:
        pool = [enemy_type for enemy_type in pool if enemy_type != 'swarm']
    if not pool:
        return _FALLBACK_TYPE

    choice = random.choice(pool)
    if choice == 'healer' and not enemies_alive:
        non_healer = [enemy_type for enemy_type in pool if enemy_type != 'healer']
        return random.choice(non_healer) if non_healer else _FALLBACK_TYPE

    return choice


def get_spawn_interval(wave: int):
    if wave <= 5:
        return 1.8
    if wave <= 14:
        return 1.5
    return 1.25
