from PIL import Image
from .materials import MATERIALS
from .rng import SeededRNG
from .grammar import grow_branch, crack_path, cluster
from .constraints import require_int

def _px(img, x, y, c):
    w, h = img.size
    img.putpixel((x % w, y % h), c)

def _base_noise(img, rng, mid, light, density):
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r = rng.random()
            if r < density * 0.72:
                img.putpixel((x, y), mid)
            elif r < density:
                img.putpixel((x, y), light)

def _draw_points(img, pts, color):
    for x,y in pts:
        _px(img,x,y,color)

def _lock_tile_edges(img):
    """Guarantee exact opposite-edge equality for seamless repetition."""
    w,h=img.size
    # Lock right edge to left edge.
    for y in range(h):
        img.putpixel((w-1,y), img.getpixel((0,y)))
    # Lock bottom edge to top edge.
    for x in range(w):
        img.putpixel((x,h-1), img.getpixel((x,0)))
    # Canonical corner.
    c=img.getpixel((0,0))
    img.putpixel((w-1,0),c)
    img.putpixel((0,h-1),c)
    img.putpixel((w-1,h-1),c)
    return img

def _peat(img, rng, pal):
    if rng.chance(0.70):
        _draw_points(img, grow_branch(img.size[0], rng, length=rng.randint(5,11), bias=(0,1)), pal["peat_mid"])
    if rng.chance(0.35):
        _draw_points(img, cluster(img.size[0], rng, count=rng.randint(3,6), radius=2), pal["moss_dark"])
    # Mica remains deliberately subdued in the base floor layer.
    for _ in range(rng.randint(0,2)):
        _px(img, rng.randint(0,15), rng.randint(0,15), pal["peat_mid"])

def _pine(img, rng, pal):
    size=img.size[0]
    for _ in range(rng.randint(5,10)):
        x,y=rng.randint(0,size-1),rng.randint(0,size-1)
        c = pal["peat_light"] if rng.chance(0.65) else pal["peat_dark"]
        _px(img,x,y,c)
        if rng.chance(0.7):
            _px(img,x+1,y+rng.choice((-1,1)),c)
    if rng.chance(0.45):
        _draw_points(img, grow_branch(size,rng,length=rng.randint(4,8),bias=(1,0)), pal["moss_dark"])

def _chapel(img, rng, pal):
    size=img.size[0]
    dark=pal["basalt_dark"]
    # grid/slate seams
    for x in range(0,size,8):
        for y in range(size):
            if rng.chance(0.88): _px(img,x,y,dark)
    for y in range(0,size,8):
        for x in range(size):
            if rng.chance(0.88): _px(img,x,y,dark)
    if rng.chance(0.75):
        _draw_points(img,crack_path(size,rng,length=rng.randint(3,7)),dark)
    if rng.chance(0.28):
        for x,y in cluster(size,rng,count=rng.randint(2,4),radius=1):
            _px(img,x,y,pal["vellum"])

def _water(img, rng, pal):
    size=img.size[0]
    # short horizontal oil-film strokes
    for _ in range(rng.randint(2,4)):
        y=rng.randint(1,size-2)
        x=rng.randint(0,size-4)
        run=rng.randint(2,5)
        for i in range(run):
            _px(img,x+i,y,pal["silt_oil"])
        if rng.chance(0.45):
            _px(img,x+run//2,y-1,pal["silt_mid"])

def _ice(img, rng, pal):
    size=img.size[0]
    for _ in range(rng.randint(2,4)):
        pts=crack_path(size,rng,length=rng.randint(2,5))
        _draw_points(img,pts,pal["ice_light"] if rng.chance(0.55) else pal["basalt_dark"])

def generate_terrain(material, profile, seed=0, variant_index=0):
    seed=require_int("seed",seed)
    variant_index=require_int("variant_index",variant_index,0)
    if material not in MATERIALS:
        raise ValueError(f"Unknown material: {material}")
    size=int(profile.get("tile_size",16))
    pal=profile["palette_rgb"]
    rule=MATERIALS[material]
    rng=SeededRNG(seed+variant_index*104729)

    base=pal[rule["base"]]
    mid=pal[rule["mid"]]
    light=pal[rule["light"]]

    img=Image.new("RGB",(size,size),base)
    _base_noise(img,rng,mid,light,rule["density"])

    {"peat":_peat,"pine":_pine,"chapel":_chapel,"water":_water,"ice":_ice}[material](img,rng,pal)
    return _lock_tile_edges(img)
