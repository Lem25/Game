"""
Slice a spritesheet into tiles and save mapped filenames for common game assets.

Usage:
    python scripts/slice_and_map.py assets/spritesheet.png cols rows assets

Defaults: cols=3, rows=5, out_dir=assets

The script will save raw tiles as sprite_r{r}_c{c}.png and also attempt to save mapped files
with suggested names (e.g., tile_path.png, tower_physical.png, enemy_tank.png, trap_fire.png).
If the sheet dimensions or layout differ, re-run with correct cols/rows.
"""
import sys
import os
from PIL import Image

DEFAULT_COLS = 3
DEFAULT_ROWS = 5

# Suggested mapping for a 3x5 layout (row, col) -> filename
SUGGESTED_MAPPING = {
    (0,0): 'tile_path.png',
    (0,1): 'tile_grass.png',
    (0,2): 'tile_wall.png',
    (1,0): 'tower_physical.png',
    (1,1): 'tower_magic.png',
    (1,2): 'proj_arrow.png',
    (2,0): 'enemy_tank.png',
    (2,1): 'proj_magic.png',
    (2,2): 'proj_magic2.png',
    (3,0): 'enemy_fighter.png',
    (3,1): 'enemy_mage.png',
    (3,2): 'enemy_assassin.png',
    (4,0): 'enemy_knight.png',
    (4,1): 'enemy_healer.png',
    (4,2): 'trap_row.png',  # may contain both traps; keep raw slices too
}


def slice_and_map(path, cols, rows, out_dir):
    im = Image.open(path)
    w, h = im.size
    tile_w = w // cols
    tile_h = h // rows
    os.makedirs(out_dir, exist_ok=True)
    saved = []
    for r in range(rows):
        for c in range(cols):
            box = (c * tile_w, r * tile_h, (c + 1) * tile_w, (r + 1) * tile_h)
            tile = im.crop(box)
            raw_name = os.path.join(out_dir, f"sprite_r{r}_c{c}.png")
            tile.save(raw_name)
            saved.append(raw_name)
            # Also save suggested mapped name if exists
            mapped = SUGGESTED_MAPPING.get((r,c))
            if mapped:
                tile.save(os.path.join(out_dir, mapped))
    return saved


def main():
    if len(sys.argv) >= 5:
        path = sys.argv[1]
        cols = int(sys.argv[2])
        rows = int(sys.argv[3])
        out_dir = sys.argv[4]
    else:
        path = input('Path to spritesheet (e.g. assets/spritesheet.png): ').strip()
        cols = int(input(f'Columns [{DEFAULT_COLS}]: ').strip() or DEFAULT_COLS)
        rows = int(input(f'Rows [{DEFAULT_ROWS}]: ').strip() or DEFAULT_ROWS)
        out_dir = input('Output directory (e.g. assets) [assets]: ').strip() or 'assets'

    if not os.path.exists(path):
        print('Spritesheet not found:', path)
        sys.exit(1)

    saved = slice_and_map(path, cols, rows, out_dir)
    print('Saved', len(saved), 'raw tiles to', out_dir)
    print('Also saved suggested mapped filenames for common assets where possible.')

if __name__ == '__main__':
    main()
