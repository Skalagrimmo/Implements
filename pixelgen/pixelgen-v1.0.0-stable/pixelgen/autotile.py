from PIL import Image
from .terrain import generate_terrain
from .constraints import require_int

# Bits: N=1 E=2 S=4 W=8
def generate_transition(from_material, to_material, profile, seed=0, mask=0):
    seed=require_int("seed",seed)
    mask=require_int("mask",mask,0,15)
    size = int(profile.get("tile_size", 16))
    a = generate_terrain(from_material, profile, seed=seed, variant_index=mask)
    b = generate_terrain(to_material, profile, seed=seed+99991, variant_index=mask)
    out = a.copy()

    edge = max(3, size // 4)

    for y in range(size):
        for x in range(size):
            use_b = False
            if mask & 1 and y < edge:       # North
                use_b = True
            if mask & 2 and x >= size-edge: # East
                use_b = True
            if mask & 4 and y >= size-edge: # South
                use_b = True
            if mask & 8 and x < edge:       # West
                use_b = True
            if use_b:
                out.putpixel((x,y), b.getpixel((x,y)))
    return out
