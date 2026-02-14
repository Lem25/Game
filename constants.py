WIDTH, HEIGHT = 800, 950
TILE = 20
GRID_W, GRID_H = 40, 40
GAME_HEIGHT = 800
FPS = 60

TOWER_COSTS = {'physical': 60, 'magic': 70, 'ice': 80}

TRAP_COSTS = {'fire': 45, 'spikes': 35}

SENTINEL_COST = 90

ENEMY_STATS = {
    'tank': {'max_hp': 200, 'speed': 0.58, 'resist_phys': 0.24, 'resist_magic': 0.24, 'size': 20, 'reward': 24},
    'fighter': {'max_hp': 82, 'speed': 1.18, 'resist_phys': 0.22, 'resist_magic': 0.00, 'size': 14, 'reward': 10},
    'swarm': {'max_hp': 22, 'speed': 2.4, 'resist_phys': 0.00, 'resist_magic': 0.00, 'size': 8, 'reward': 4},
    'mage': {'max_hp': 62, 'speed': 0.95, 'resist_phys': 0.00, 'resist_magic': 0.42, 'size': 12, 'reward': 12},
    'disruptor': {'max_hp': 74, 'speed': 1.0, 'resist_phys': 0.08, 'resist_magic': 0.25, 'size': 13, 'reward': 18},
    'assassin': {'max_hp': 48, 'speed': 2.0, 'resist_phys': 0.00, 'resist_magic': 0.00, 'size': 10, 'reward': 14},
    'healer': {'max_hp': 72, 'speed': 0.85, 'resist_phys': 0.10, 'resist_magic': 0.10, 'size': 13, 'reward': 16},
    'minotaur_boss': {'max_hp': 440, 'speed': 0.52, 'resist_phys': 0.62, 'resist_magic': 0.18, 'size': 28, 'reward': 220},
    'demon_boss': {'max_hp': 760, 'speed': 0.48, 'resist_phys': 0.12, 'resist_magic': 0.65, 'size': 40, 'reward': 380},
}

TRAP_STATS = {
    'fire': {'dps': 30.0},
    'spikes': {'damage': 50, 'interval': 1},
}

ENEMY_SCALE_WAVE_INTERVAL = 5
ENEMY_SCALE_INCREMENT = 0.07
