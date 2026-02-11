"""
Simple sprite sheet slicer.

Usage:
    python scripts/slice_sprites.py path/to/spritesheet.png cols rows out_dir

Example:
    python scripts/slice_sprites.py assets/spritesheet.png 5 5 assets/

This will split the sheet into a cols x rows grid and save tiles as out_dir/sprite_r{row}_c{col}.png

If you prefer, run with no args and the script will prompt for inputs.
"""
import sys
import os
from PIL import Image


def slice_sheet(path, cols, rows, out_dir):
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
            out_path = os.path.join(out_dir, f"sprite_r{r}_c{c}.png")
            tile.save(out_path)
            saved.append(out_path)
    return saved


def main():
    if len(sys.argv) >= 5:
        path = sys.argv[1]
        cols = int(sys.argv[2])
        rows = int(sys.argv[3])
        out_dir = sys.argv[4]
    else:
        path = input('C:\Abra\task_01kh162qygfqbtgjv7adht6f87_1770640286_img_1.webp ').strip()
        cols = int(input('Columns: ').strip() or 5)
        rows = int(input('Rows: ').strip() or 5)
        out_dir = input('Output directory (e.g. assets): ').strip() or 'assets'

    if not os.path.exists(path):
        print('Spritesheet not found:', path)
        sys.exit(1)

    saved = slice_sheet(path, cols, rows, out_dir)
    print('Saved', len(saved), 'tiles to', out_dir)

if __name__ == '__main__':
    main()
