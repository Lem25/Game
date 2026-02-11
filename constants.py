WIDTH, HEIGHT = 800, 950
TILE = 20
GRID_W, GRID_H = 40, 40
GAME_HEIGHT = 800
FPS = 60

TOWER_COSTS = {'physical': 50, 'magic': 60, 'ice': 70}

ENEMY_STATS = {
    'tank': {'max_hp': 210, 'speed': 0.7, 'resist_phys': 0.12, 'resist_magic': 0.12, 'size': 20, 'reward': 18},
    'fighter': {'max_hp': 80, 'speed': 1.4, 'resist_phys': 0.1, 'resist_magic': 0.0, 'size': 14, 'reward': 6},
    'mage': {'max_hp': 60, 'speed': 1.1, 'resist_phys': 0.0, 'resist_magic': 0.1, 'size': 12, 'reward': 8},
    'assassin': {'max_hp': 40, 'speed': 2.2, 'resist_phys': 0.0, 'resist_magic': 0.0, 'size': 10, 'reward': 10},
    'healer': {'max_hp': 70, 'speed': 1.0, 'resist_phys': 0.05, 'resist_magic': 0.05, 'size': 13, 'reward': 12},
    'minotaur_boss': {'max_hp': 420, 'speed': 0.7, 'resist_phys': 0.22, 'resist_magic': 0.12, 'size': 28, 'reward': 130},
    'demon_boss': {'max_hp': 820, 'speed': 0.5, 'resist_phys': 0.26, 'resist_magic': 0.3, 'size': 40, 'reward': 260},
}
TRAP_COSTS = {'fire': 40, 'spikes': 30}

TRAP_STATS = {
    'fire': {'dps': 30.0},
    'spikes': {'damage': 50, 'interval': 1},
}

ENEMY_SCALE_WAVE_INTERVAL = 5
ENEMY_SCALE_INCREMENT = 0.10
