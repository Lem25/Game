import os
import pygame

ASSET_DIR = os.path.join(os.path.dirname(__file__), 'assets')

_raw = {}

_FALLBACK_NAMES = {
    'tower_physical': 'physical_tower',
    'tower_magic': 'magic_tower',
    'tower_ice': 'ice_tower',
    'trap_fire': 'fire_trap',
    'trap_spikes': 'spike_trap',
    'tile_path': 'enemy_path',
    'tile_grass': 'standard_tile',
    'tile_wall': 'wall',
    'proj_arrow': 'arrow_proj',
    'proj_missile': 'missile_proj',
    'enemy_fighter': 'warrior_enemy',
    'enemy_mage': 'wizard_enemy',
    'enemy_assassin': 'assassin_enemy',
    'enemy_healer': 'healer_enemy',
    'enemy_tank': 'tank_enemy',
    'enemy_minotaur_boss': 'minotaur_boss',
    'enemy_demon_boss': 'demon_boss',
    'goal_gem': 'goal_treasure',
}

_EXTS = ['.png', '.jpg', '.jpeg']


def _try_candidates(name):
    seen = set()
    candidates = [name]
    if name in _FALLBACK_NAMES:
        candidates.append(_FALLBACK_NAMES[name])
    if '_' in name:
        parts = name.split('_')
        candidates.append('_'.join(reversed(parts)))
    if name.startswith('enemy_'):
        base = name.split('enemy_', 1)[1]
        candidates.append(f"{base}_enemy")
    if name.endswith('_enemy'):
        base = name.rsplit('_enemy', 1)[0]
        candidates.append(f"enemy_{base}")
    if name.startswith('proj_'):
        base = name.split('proj_', 1)[1]
        candidates.append(f"{base}_proj")
    out = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _load_raw(name):
    if name in _raw:
        return _raw[name]

    candidates = _try_candidates(name)
    for cand in candidates:
        for ext in _EXTS:
            path = os.path.join(ASSET_DIR, f"{cand}{ext}")
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    _raw[name] = img
                    return img
                except Exception:
                    continue

    _raw[name] = None
    return None


def get(name, size=None):
    raw = _load_raw(name)
    if raw is None:
        return None
    if size is None:
        return raw.copy()
    if isinstance(size, int):
        size = (size, size)
    try:
        return pygame.transform.smoothscale(raw, size)
    except Exception:
        return raw.copy()
