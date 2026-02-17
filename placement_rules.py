import math


def can_place_tower(grid, gx, gy, towers, tile_size, grid_width, grid_height):
    if not (0 <= gx < grid_width and 0 <= gy < grid_height):
        return False
    if grid[gy][gx] != 0:
        return False
    tower_exists = any(
        math.hypot(t.pos.x - (gx * tile_size + tile_size // 2), t.pos.y - (gy * tile_size + tile_size // 2)) < tile_size
        for t in towers
    )
    return not tower_exists


def can_place_trap(grid, gx, gy, towers, traps, grid_width, grid_height, tile_size):
    if not (0 <= gx < grid_width and 0 <= gy < grid_height):
        return False
    if grid[gy][gx] != 2:
        return False
    for tower in towers:
        if int(tower.pos.x // tile_size) == gx and int(tower.pos.y // tile_size) == gy:
            return False
    for trap in traps:
        if trap.grid_pos == (gx, gy):
            return False
    return True
