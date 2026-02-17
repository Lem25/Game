import random


_EARLY_POOL = ['fighter', 'fighter', 'fighter', 'mage', 'fighter', 'assassin']
_MID_POOL = ['fighter', 'fighter', 'mage', 'assassin', 'tank', 'swarm']
_LATE_POOL = ['fighter', 'tank', 'mage', 'assassin', 'healer', 'swarm']


def get_wave_template(wave: int):
    if wave <= 5:
        base_pool = list(_EARLY_POOL)
        swarm_chance = 0.0 if wave < 5 else 0.08
    elif wave <= 14:
        base_pool = list(_MID_POOL)
        swarm_chance = 0.12
        if wave >= 12:
            base_pool.append('healer')
    else:
        base_pool = list(_LATE_POOL)
        swarm_chance = 0.18
        if wave >= 20:
            base_pool.append('tank')

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

    pool = [enemy_type for enemy_type in template['pool'] if enemy_type not in ['minotaur_boss', 'demon_boss']]
    if not can_spawn_swarm:
        pool = [enemy_type for enemy_type in pool if enemy_type != 'swarm']
    if not pool:
        return 'fighter'

    choice = random.choice(pool)
    if choice == 'healer' and not enemies_alive:
        non_healer = [enemy_type for enemy_type in pool if enemy_type != 'healer']
        return random.choice(non_healer) if non_healer else 'fighter'

    return choice


def get_spawn_interval(wave: int):
    if wave <= 5:
        return 1.8
    if wave <= 14:
        return 1.5
    return 1.25
