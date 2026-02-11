from constants import GRID_W, GRID_H

def manhattan_distance(p1, p2):
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def create_maze():
    grid = [[1] * GRID_W for _ in range(GRID_H)]
    
    for y in range(1, GRID_H - 1):
        for x in range(1, GRID_W - 1):
            grid[y][x] = 0
    
    goal = (GRID_W // 2, GRID_H // 2)
    spawn_points = []
    
    spawn1 = (3, 10)
    spawn_points.append(spawn1)
    for x in range(3, goal[0] + 1):
        grid[10][x] = 2
    for y in range(10, goal[1] + 1):
        grid[y][goal[0]] = 2
    
    spawn2 = (20, 3)
    spawn_points.append(spawn2)
    for y in range(3, goal[1] + 1):
        grid[y][20] = 2
    for x in range(20, goal[0] - 1, -1):
        grid[goal[1]][x] = 2
    
    spawn3 = (37, 30)
    spawn_points.append(spawn3)
    for x in range(37, goal[0] - 1, -1):
        grid[30][x] = 2
    for y in range(30, goal[1] - 1, -1):
        grid[y][goal[0]] = 2
    
    grid[goal[1]][goal[0]] = 2
    
    return grid, spawn_points, goal

def expand_paths(grid, towers, goal, spawn_points):
    import random
    from constants import TILE
    
    edge_options = []
    
    for x in range(1, GRID_W - 1):
        edge_options.append((x, 1))
    
    for x in range(1, GRID_W - 1):
        edge_options.append((x, GRID_H - 2))
    
    for y in range(1, GRID_H - 1):
        edge_options.append((1, y))
    
    for y in range(1, GRID_W - 1):
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

GOAL_GRID = (GRID_W // 2, GRID_H // 2)
