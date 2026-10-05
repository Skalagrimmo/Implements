from PIL import Image
from .rng import SeededRNG
from .grammar import cluster
from .constraints import require_int, require_probability

def paper_wax_overlay(profile, seed=0, variant_index=0, wax_chance=0.45):
    seed=require_int("seed",seed)
    variant_index=require_int("variant_index",variant_index,0)
    wax_chance=require_probability("wax_chance",wax_chance)
    size = int(profile.get("tile_size",16))
    pal = profile["palette_rgb"]
    rng = SeededRNG(seed + variant_index * 9187)
    vellum = pal["vellum"] + (235,)
    wax = pal["wax"] + (245,)
    ink = pal["silt_deep"] + (220,)

    img = Image.new("RGBA",(size,size),(0,0,0,0))
    # one or two tiny paper scraps
    for _ in range(rng.randint(1,2)):
        w,h = rng.randint(3,5), rng.randint(2,4)
        x,y = rng.randint(0,size-w), rng.randint(0,size-h)
        for py in range(y,y+h):
            for px in range(x,x+w):
                if rng.chance(0.9):
                    img.putpixel((px,py), vellum)
        # short ink mark
        if h >= 2:
            iy = y + rng.randint(0,h-1)
            for ix in range(x+1,min(x+w-1,size)):
                if rng.chance(0.6):
                    img.putpixel((ix,iy), ink)
        if rng.chance(wax_chance):
            wx = min(size-1, x+w-1)
            wy = min(size-1, y+h-1)
            img.putpixel((wx,wy), wax)
            if wx > 0 and rng.chance(0.5):
                img.putpixel((wx-1,wy), wax)
    return img

def moss_overlay(profile, seed=0, variant_index=0, density=0.14):
    seed=require_int("seed",seed)
    variant_index=require_int("variant_index",variant_index,0)
    density=require_probability("density",density)
    size = int(profile.get("tile_size",16))
    pal = profile["palette_rgb"]
    rng = SeededRNG(seed + variant_index * 12289)
    dark = pal["moss_dark"] + (220,)
    mid = pal["moss_mid"] + (220,)
    light = pal["moss_light"] + (200,)
    img = Image.new("RGBA",(size,size),(0,0,0,0))
    count = max(2, int(size*size*density/3))
    for x,y in cluster(size,rng,count=count,radius=max(1,size//5)):
        c = dark if rng.chance(0.55) else (mid if rng.chance(0.8) else light)
        img.putpixel((x,y),c)
    return img
