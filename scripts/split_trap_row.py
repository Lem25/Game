from PIL import Image
import os
p='c:/Abra/assets/trap_row.png'
if not os.path.exists(p):
    print('trap_row.png not found at',p)
    raise SystemExit(1)
im=Image.open(p).convert('RGBA')
w,h=im.size
# compute alpha per column
alpha_cols=[sum(im.getpixel((x,y))[3] for y in range(h)) for x in range(w)]
# find lowest-alpha column as separator
min_index=min(range(w), key=lambda x: alpha_cols[x])
# try to find a region of low alpha (gap)
start=None
for x in range(w):
    if alpha_cols[x] < 10 and start is None:
        start=x
    if alpha_cols[x] >= 10 and start is not None:
        end=x
        break
if start is None:
    # fallback: split center
    mid=w//2
    left=im.crop((0,0,mid,h))
    right=im.crop((mid,0,w,h))
else:
    # choose split at midpoint of gap
    gap_start=start
    gap_end=end if 'end' in locals() else w
    split=(gap_start+gap_end)//2
    left=im.crop((0,0,split,h))
    right=im.crop((split,0,w,h))
# trim whitespace around each
def trim(im):
    bbox=im.getbbox()
    return im.crop(bbox) if bbox else im
left=trim(left)
right=trim(right)
out_dir='c:/Abra/assets'
left.save(os.path.join(out_dir,'trap_fire.png'))
right.save(os.path.join(out_dir,'trap_spikes.png'))
print('Saved trap_fire.png and trap_spikes.png')