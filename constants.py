WIDTH, HEIGHT = 800, 950
TILE = 20
GRID_W, GRID_H = 40, 40
GAME_HEIGHT = 800
FPS = 60

TOWER_COSTS = {'physical': 60, 'magic': 70, 'ice': 80}

TRAP_COSTS = {'fire': 45, 'spikes': 35}

SENTINEL_COST = 90

ENEMY_STATS = {
    'tank': {'max_hp': 230, 'speed': 0.65, 'resist_phys': 0.30, 'resist_magic': 0.30, 'size': 20, 'reward': 24},
    'fighter': {'max_hp': 95, 'speed': 1.35, 'resist_phys': 0.35, 'resist_magic': 0.00, 'size': 14, 'reward': 10},
    'mage': {'max_hp': 70, 'speed': 1.05, 'resist_phys': 0.00, 'resist_magic': 0.55, 'size': 12, 'reward': 12},
    'assassin': {'max_hp': 55, 'speed': 2.3, 'resist_phys': 0.00, 'resist_magic': 0.00, 'size': 10, 'reward': 14},
    'healer': {'max_hp': 85, 'speed': 0.95, 'resist_phys': 0.15, 'resist_magic': 0.15, 'size': 13, 'reward': 16},
    'minotaur_boss': {'max_hp': 520, 'speed': 0.6, 'resist_phys': 0.75, 'resist_magic': 0.25, 'size': 28, 'reward': 220},
    'demon_boss': {'max_hp': 920, 'speed': 0.55, 'resist_phys': 0.16, 'resist_magic': 0.80, 'size': 40, 'reward': 380},
}
TRAP_COSTS = {'fire': 40, 'spikes': 30}

TRAP_STATS = {
    'fire': {'dps': 30.0},
    'spikes': {'damage': 50, 'interval': 1},
}

ENEMY_SCALE_WAVE_INTERVAL = 5
ENEMY_SCALE_INCREMENT = 0.10
