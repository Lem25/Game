"""
Process new boss and goal treasure images for sprite-ready use:
- goal_treasure (final objective)
- minotaur_boss (wave 5 boss)
- demon_boss (wave 10 boss)

Removes backgrounds, crops excess borders, and ensures consistent sizing.
Usage:
    python scripts/process_boss_assets.py
"""
import os
from PIL import Image, ImageOps

ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets')
WHITE_THRESH = 240

def remove_background(im):
    """Convert near-white background to transparent."""
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

def crop_to_content(im):
    """Crop image to remove empty transparent borders."""
    im = im.convert('RGBA')
    # Find bounding box of non-transparent pixels
    bbox = im.getbbox()
    if bbox:
        return im.crop(bbox)
    return im

def process_single_image(filename, output_name=None):
    """Process a single image file."""
    if output_name is None:
        output_name = os.path.splitext(filename)[0]
    
    path = os.path.join(ROOT, filename)
    if not os.path.exists(path):
        print(f"Skipping {filename} - not found")
        return
    
    try:
        print(f"Processing {filename}...")
        im = Image.open(path)
        
        # Remove background
        im = remove_background(im)
        
        # Crop to content
        im = crop_to_content(im)
        
        # Save as PNG
        out_path = os.path.join(ROOT, f"{output_name}.png")
        im.save(out_path)
        print(f"  Saved {output_name}.png ({im.size[0]}x{im.size[1]})")
    except Exception as e:
        print(f"Error processing {filename}: {e}")

def process():
    """Process boss and goal asset images."""
    # Try common filename variations
    boss_images = [
        ('goal_treasure', 'goal_treasure'),
        ('goal_treasure.png', 'goal_treasure'),
        ('goal_treasure.jpg', 'goal_treasure'),
        ('minotaur_boss', 'minotaur_boss'),
        ('minotaur_boss.png', 'minotaur_boss'),
        ('minotaur_boss.jpg', 'minotaur_boss'),
        ('demon_boss', 'demon_boss'),
        ('demon_boss.png', 'demon_boss'),
        ('demon_boss.jpg', 'demon_boss'),
    ]
    
    for src, out in boss_images:
        process_single_image(src, out)

if __name__ == '__main__':
    process()
