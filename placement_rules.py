import math


def _in_bounds(gx, gy, grid_width, grid_height):
    return 0 <= gx < grid_width and 0 <= gy < grid_height


def _tile_center(gx, gy, tile_size):
    return gx * tile_size + tile_size // 2, gy * tile_size + tile_size // 2


def _tower_occupies_tile(tower, gx, gy, tile_size):
    return int(tower.pos.x // tile_size) == gx and int(tower.pos.y // tile_size) == gy


def _tower_too_close(tower, gx, gy, tile_size):
    center_x, center_y = _tile_center(gx, gy, tile_size)
    return math.hypot(tower.pos.x - center_x, tower.pos.y - center_y) < tile_size


def can_place_tower(grid, gx, gy, towers, tile_size, grid_width, grid_height):
    if not _in_bounds(gx, gy, grid_width, grid_height):
        return False
    if grid[gy][gx] != 0:
        return False
    tower_exists = any(_tower_too_close(tower, gx, gy, tile_size) for tower in towers)
    return not tower_exists


def can_place_trap(grid, gx, gy, towers, traps, grid_width, grid_height, tile_size):
    if not _in_bounds(gx, gy, grid_width, grid_height):
        return False
    if grid[gy][gx] != 2:
        return False
    for tower in towers:
        if _tower_occupies_tile(tower, gx, gy, tile_size):
            return False
    for trap in traps:
        if trap.grid_pos == (gx, gy):
            return False
    return True
