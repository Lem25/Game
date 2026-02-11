"""
Simple asset processor:
- Converts near-white background to transparency for .jpg/.jpeg/.png files in assets/
- Skips trap images (fire/spike) as requested
- Creates rotated wall variants 'wall_left.png' and 'wall_right.png'

Usage:
    python scripts/process_assets.py

Requires Pillow: pip install Pillow
"""
import os
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
SKIP_NAMES = {'fire_trap', 'spike_trap', 'trap_fire', 'trap_spikes'}
WHITE_THRESH = 240

def make_transparent(im):
    im = im.convert('RGBA')
    datas = im.getdata()
    new_data = []
    for item in datas:
        r, g, b, a = item
        if r >= WHITE_THRESH and g >= WHITE_THRESH and b >= WHITE_THRESH:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append((r, g, b, a))
    im.putdata(new_data)
    return im


def process():
    files = [f for f in os.listdir(ROOT) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    for fn in files:
        name, ext = os.path.splitext(fn)
        if name in SKIP_NAMES:
            print('Skipping trap asset', fn)
            continue
        path = os.path.join(ROOT, fn)
        try:
            im = Image.open(path)
        except Exception as e:
            print('Failed to open', fn, e)
            continue
        print('Processing', fn)
        im2 = make_transparent(im)
        out_path = os.path.join(ROOT, f"{name}.png")
        try:
            im2.save(out_path)
        except Exception as e:
            print('Failed to save', out_path, e)

    # Create rotated wall variants if wall.png exists (or wall.jpg)
    for cand in ('wall.png', 'wall.jpg', 'wall.jpeg'):
        p = os.path.join(ROOT, cand)
        if os.path.exists(p):
            try:
                w = Image.open(p).convert('RGBA')
                left = w.rotate(90, expand=True)
                right = w.rotate(-90, expand=True)
                left.save(os.path.join(ROOT, 'wall_left.png'))
                right.save(os.path.join(ROOT, 'wall_right.png'))
                print('Saved wall_left.png and wall_right.png')
            except Exception as e:
                print('Failed to create rotated walls', e)
            break

if __name__ == '__main__':
    process()
