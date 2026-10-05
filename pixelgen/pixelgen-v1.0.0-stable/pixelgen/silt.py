from PIL import Image
from .rng import SeededRNG
from .primitives import blob_mask
from .grammar import hex_fragment, grow_branch
from .constraints import require_int, require_probability

def generate_silt_overlay(profile, seed=0, variant_index=0, density=0.34):
    seed=require_int("seed",seed)
    variant_index=require_int("variant_index",variant_index,0)
    density=require_probability("density",density)
    size=int(profile.get("tile_size",16))
    pal=profile["palette_rgb"]
    rng=SeededRNG(seed+variant_index*65537)

    deep=pal["silt_deep"]+(235,)
    oil=pal["silt_oil"]+(210,)
    mid=pal["silt_mid"]+(215,)
    glow=pal["nano_glow"]+(235,)

    img=Image.new("RGBA",(size,size),(0,0,0,0))
    mask=blob_mask(size,size,rng,fill=density,steps=2)

    for y in range(size):
        for x in range(size):
            if mask[y][x]:
                r=rng.random()
                img.putpixel((x,y), deep if r<0.70 else (oil if r<0.94 else mid))

    # Subtle buried machine geometry.
    for _ in range(rng.randint(1,2)):
        for x,y in hex_fragment(size,rng):
            if mask[y][x]:
                img.putpixel((x,y),oil)

    # Filament grammar: a restrained organic path, capped by profile max coverage.
    max_cov=float(profile.get("rules",{}).get("nano_glow_max_coverage",0.10))
    max_glow=max(1,int(size*size*max_cov))
    glow_count=0
    for x,y in grow_branch(size,rng,length=rng.randint(4,9),bias=(0,1),branch_chance=0.10):
        if glow_count>=max_glow:
            break
        if mask[y][x]:
            img.putpixel((x,y),glow)
            glow_count += 1

    return img
