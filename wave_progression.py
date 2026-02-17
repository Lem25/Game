def get_wave_enemy_count(wave, target_wave):
    effective_wave = min(wave, target_wave)
    if effective_wave <= 5:
        return 3 + effective_wave
    if effective_wave <= 14:
        return 8 + int((effective_wave - 5) * 1.4)
    return 20 + int((effective_wave - 14) * 1.8)
