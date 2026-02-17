def compute_freeze_resist(wave: int) -> float:
    if wave <= 5:
        return 0.0
    if wave <= 15:
        return min(0.4, (wave - 5) * 0.03)
    return min(0.65, 0.4 + (wave - 15) * 0.02)


def compute_swarm_reward(base_reward: int, swarm_spawn_index: int) -> int:
    if swarm_spawn_index <= 6:
        return base_reward
    extra_swarm_count = swarm_spawn_index - 6
    multiplier = max(0.6, 0.9 ** extra_swarm_count)
    return max(1, int(base_reward * multiplier))


def apply_spawn_scaling(enemy, wave_number: int, swarm_spawn_index: int | None = None):
    freeze_resist = compute_freeze_resist(wave_number)
    if getattr(enemy, 'is_boss', False):
        freeze_resist = min(0.85, freeze_resist + 0.15)
    enemy.freeze_resist = freeze_resist

    if enemy.type == 'swarm' and swarm_spawn_index is not None:
        base_reward = enemy.reward
        enemy.reward = compute_swarm_reward(base_reward, swarm_spawn_index)
