import random

from constants import GRID_W, GRID_H

MIN_STARTING_LANES = 3
MAX_STARTING_LANES = 4
MAX_TOTAL_LANES = 6
MIN_SPAWN_DISTANCE = 6

SPAWN_ZONES = [
    ("top_left", "top"),
    ("top_right", "top"),
    ("left_mid", "left"),
    ("right_mid", "right"),
    ("bottom_left", "bottom"),
    ("bottom_right", "bottom"),
]

def manhattan_distance(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def _clamp_range(start, end, low, high):
    start = max(low, min(high, start))
    end = max(low, min(high, end))
    if start > end:
        start, end = end, start
    return range(start, end + 1)


def _zone_candidates(zone_name):
    min_x = 1
    max_x = max(1, GRID_W - 2)
    min_y = 1
    max_y = max(1, GRID_H - 2)

    left_x_end = max(min_x, GRID_W // 3)
    right_x_start = max(min_x, (GRID_W * 2) // 3)
    mid_y_start = max(min_y, GRID_H // 3)
    mid_y_end = max(min_y, (GRID_H * 2) // 3)

    candidates = []
    if zone_name == "top_left":
        candidates = [(x, min_y) for x in _clamp_range(min_x, left_x_end, min_x, max_x)]
    elif zone_name == "top_right":
        candidates = [(x, min_y) for x in _clamp_range(right_x_start, max_x, min_x, max_x)]
    elif zone_name == "left_mid":
        candidates = [(min_x, y) for y in _clamp_range(mid_y_start, mid_y_end, min_y, max_y)]
    elif zone_name == "right_mid":
        candidates = [(max_x, y) for y in _clamp_range(mid_y_start, mid_y_end, min_y, max_y)]
    elif zone_name == "bottom_left":
        candidates = [(x, max_y) for x in _clamp_range(min_x, left_x_end, min_x, max_x)]
    elif zone_name == "bottom_right":
        candidates = [(x, max_y) for x in _clamp_range(right_x_start, max_x, min_x, max_x)]

    unique_candidates = []
    seen = set()
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            unique_candidates.append(candidate)
    return unique_candidates


def _spawn_is_spaced(spawn, spawn_points):
    return all(manhattan_distance(spawn, existing) >= MIN_SPAWN_DISTANCE for existing in spawn_points)


def _pick_spawn_for_zone(zone_name, spawn_points, retries=12):
    candidates = _zone_candidates(zone_name)
    if not candidates:
        return None

    for _ in range(retries):
        spawn = random.choice(candidates)
        if _spawn_is_spaced(spawn, spawn_points):
            return spawn

    random.shuffle(candidates)
    for spawn in candidates:
        if _spawn_is_spaced(spawn, spawn_points):
            return spawn
    return None


def _carve_path_to_goal(grid, spawn, goal):
    sx, sy = spawn
    gx, gy = goal
    grid[sy][sx] = 2

    if random.choice((True, False)):
        x_step = 1 if gx >= sx else -1
        for x in range(sx, gx + x_step, x_step):
            grid[sy][x] = 2
        y_step = 1 if gy >= sy else -1
        for y in range(sy, gy + y_step, y_step):
            grid[y][gx] = 2
    else:
        y_step = 1 if gy >= sy else -1
        for y in range(sy, gy + y_step, y_step):
            grid[y][sx] = 2
        x_step = 1 if gx >= sx else -1
        for x in range(sx, gx + x_step, x_step):
            grid[gy][x] = 2

def create_maze():
    grid = [[1] * GRID_W for _ in range(GRID_H)]
    
    for y in range(1, GRID_H - 1):
        for x in range(1, GRID_W - 1):
            grid[y][x] = 0
    
    goal = (GRID_W // 2, GRID_H // 2)
    spawn_points = []

    lane_count = random.randint(MIN_STARTING_LANES, MAX_STARTING_LANES)

    zone_pool = list(SPAWN_ZONES)
    random.shuffle(zone_pool)

    selected_zones = []
    used_sides = set()
    for zone in zone_pool:
        if len(selected_zones) >= lane_count:
            break
        zone_name, side = zone
        if side not in used_sides:
            selected_zones.append(zone_name)
            used_sides.add(side)
    for zone in zone_pool:
        if len(selected_zones) >= lane_count:
            break
        zone_name, _ = zone
        if zone_name not in selected_zones:
            selected_zones.append(zone_name)

    zone_names = [zone_name for zone_name, _ in zone_pool]
    for zone_name in selected_zones:
        spawn = _pick_spawn_for_zone(zone_name, spawn_points)
        if spawn is not None:
            spawn_points.append(spawn)

    for zone_name in zone_names:
        if len(spawn_points) >= lane_count:
            break
        if any(spawn in _zone_candidates(zone_name) for spawn in spawn_points):
            continue
        spawn = _pick_spawn_for_zone(zone_name, spawn_points)
        if spawn is not None:
            spawn_points.append(spawn)

    if not spawn_points:
        spawn_points.append((1, 1))

    for spawn in spawn_points:
        _carve_path_to_goal(grid, spawn, goal)

    grid[goal[1]][goal[0]] = 2
    
    return grid, spawn_points, goal

def expand_paths(grid, towers, spawn_points):
    from constants import TILE

    if len(spawn_points) >= MAX_TOTAL_LANES:
        return [], [], None
    
    edge_options = []
    
    for x in range(1, GRID_W - 1):
        edge_options.append((x, 1))
    
    for x in range(1, GRID_W - 1):
        edge_options.append((x, GRID_H - 2))
    
    for y in range(1, GRID_H - 1):
        edge_options.append((1, y))
    
    for y in range(1, GRID_H - 1):
        edge_options.append((GRID_W - 2, y))
    
    if not edge_options:
        return [], [], None
    
    new_spawn = random.choice(edge_options)
    
    closest_path = None
    min_distance = float('inf')
    
    for y in range(GRID_H):
        for x in range(GRID_W):
            if grid[y][x] == 2 and (x, y) not in spawn_points:
                is_adjacent_to_spawn = False
                for sx, sy in spawn_points:
                    if abs(x - sx) + abs(y - sy) <= 1:
                        is_adjacent_to_spawn = True
                        break
                
                if not is_adjacent_to_spawn:
                    distance = abs(new_spawn[0] - x) + abs(new_spawn[1] - y)
                    if distance < min_distance:
                        min_distance = distance
                        closest_path = (x, y)
    
    if not closest_path:
        return [], [], None
    
    grid[new_spawn[1]][new_spawn[0]] = 2
    
    path = [new_spawn]
    current = list(new_spawn)
    
    while (current[0], current[1]) != closest_path:
        x, y = current
        target_x, target_y = closest_path
        
        if x < target_x:
            current[0] += 1
        elif x > target_x:
            current[0] -= 1
        elif y < target_y:
            current[1] += 1
        elif y > target_y:
            current[1] -= 1
        
        if not (0 <= current[0] < GRID_W and 0 <= current[1] < GRID_H):
            break
        
        if grid[current[1]][current[0]] != 2:
            grid[current[1]][current[0]] = 2
        
        path.append((current[0], current[1]))
    
    towers_to_remove = []
    for x, y in path:
        for tower in towers:
            tower_grid_x = int(tower.pos.x // TILE)
            tower_grid_y = int(tower.pos.y // TILE)
            if tower_grid_x == x and tower_grid_y == y:
                towers_to_remove.append(tower)
    
    return path, towers_to_remove, new_spawn
