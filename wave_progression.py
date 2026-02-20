EARLY_END = 5
MID_END = 14

EARLY_BASE = 3
MID_BASE = 8
LATE_BASE = 20

MID_GROWTH = 1.4
LATE_GROWTH = 1.8


def get_wave_enemy_count(wave, target_wave):
    effective_wave = min(wave, target_wave)
    if effective_wave <= EARLY_END:
        return EARLY_BASE + effective_wave
    if effective_wave <= MID_END:
        return MID_BASE + int((effective_wave - EARLY_END) * MID_GROWTH)
    return LATE_BASE + int((effective_wave - MID_END) * LATE_GROWTH)
