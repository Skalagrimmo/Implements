from PIL import Image
from .terrain import generate_terrain
from .constraints import require_int

# 8 neighbors: N,NE,E,SE,S,SW,W,NW
BITS = {"N":1,"NE":2,"E":4,"SE":8,"S":16,"SW":32,"W":64,"NW":128}

def canonical_masks_47():
    """
    Build the common 47 useful 8-neighbor masks where a diagonal is only
    meaningful when both adjacent cardinals are present.
    """
    masks=[]
    for mask in range(256):
        n=bool(mask&BITS["N"]); e=bool(mask&BITS["E"])
        s=bool(mask&BITS["S"]); w=bool(mask&BITS["W"])
        ne=bool(mask&BITS["NE"]); se=bool(mask&BITS["SE"])
        sw=bool(mask&BITS["SW"]); nw=bool(mask&BITS["NW"])
        valid = True
        if ne and not (n and e): valid=False
        if se and not (s and e): valid=False
        if sw and not (s and w): valid=False
        if nw and not (n and w): valid=False
        if valid:
            masks.append(mask)
    # For this diagonal-validity convention there are exactly 47 canonical masks.
    return masks

def _neighbor_selector(x,y,size,mask):
    edge=max(3,size//4)
    use=False
    if mask & BITS["N"] and y < edge: use=True
    if mask & BITS["S"] and y >= size-edge: use=True
    if mask & BITS["W"] and x < edge: use=True
    if mask & BITS["E"] and x >= size-edge: use=True

    # Diagonals carve/fill corner wedges.
    if mask & BITS["NE"] and x >= size-edge and y < edge: use=True
    if mask & BITS["SE"] and x >= size-edge and y >= size-edge: use=True
    if mask & BITS["SW"] and x < edge and y >= size-edge: use=True
    if mask & BITS["NW"] and x < edge and y < edge: use=True
    return use

def generate_transition47(from_material,to_material,profile,seed=0,mask=0):
    seed=require_int("seed",seed)
    mask=require_int("mask",mask,0,255)
    if mask not in canonical_masks_47():
        raise ValueError(f"mask {mask} is not one of the 47 canonical masks")
    size=int(profile.get("tile_size",16))
    a=generate_terrain(from_material,profile,seed=seed,variant_index=mask)
    b=generate_terrain(to_material,profile,seed=seed+424242,variant_index=mask)
    out=a.copy()
    for y in range(size):
        for x in range(size):
            if _neighbor_selector(x,y,size,mask):
                out.putpixel((x,y),b.getpixel((x,y)))
    return out
