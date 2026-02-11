from PIL import Image
import os
p='c:/Abra/assets'
files=sorted([f for f in os.listdir(p) if f.lower().endswith(('.png','.webp'))])
print('Found', len(files), 'files')
for f in files:
    path=os.path.join(p,f)
    im=Image.open(path).convert('RGBA')
    w,h=im.size
    # compute bbox of non-transparent
    bbox=im.getbbox()
    px=list(im.getdata())
    r=sum(c[0] for c in px)//len(px)
    g=sum(c[1] for c in px)//len(px)
    b=sum(c[2] for c in px)//len(px)
    a=sum(c[3] for c in px)//len(px)
    print(f, 'size=',(w,h), 'bbox=',bbox, 'avgRGBA=',(r,g,b,a))
