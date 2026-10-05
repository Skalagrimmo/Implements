from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from .rng import SeededRNG

TILE_IDS = {
    "peat": 1,
    "pine": 2,
    "chapel": 3,
    "water": 4,
    "ice": 5,
    "path": 6,
    "moss": 7,
    "silt": 8,
}

@dataclass
class SceneObject:
    kind: str
    x: int
    y: int
    layer: str = "objects"
    note: str = ""

    def to_dict(self):
        return asdict(self)

def _blank_grid(w, h, fill="peat"):
    return [[fill for _ in range(w)] for _ in range(h)]

def _set(grid, x, y, value):
    h=len(grid); w=len(grid[0])
    if 0 <= x < w and 0 <= y < h:
        grid[y][x] = value

def _rect(grid, x0, y0, w, h, value):
    for y in range(y0, y0+h):
        for x in range(x0, x0+w):
            _set(grid, x, y, value)

def _can_place_rect(scene, x0, y0, w, h):
    return 0 <= x0 and 0 <= y0 and x0 + w <= scene["width"] and y0 + h <= scene["height"]

def _draw_meandering_path(scene, rng, x0, y0, x1, y1, width=2):
    x, y = x0, y0
    while x != x1:
        for dy in range(width):
            _set(scene["ground"], x, min(scene["height"]-1, y+dy), "path")
        x += 1 if x < x1 else -1
        if rng.chance(0.18):
            y = max(0, min(scene["height"]-2, y + rng.choice((-1,1))))
    while y != y1:
        for dx in range(width):
            _set(scene["ground"], min(scene["width"]-1, x+dx), y, "path")
        y += 1 if y < y1 else -1

def _carve_bog(scene, rng, x0, y0, w, h):
    for y in range(y0, min(scene["height"], y0+h)):
        for x in range(x0, min(scene["width"], x0+w)):
            if rng.chance(0.82):
                scene["ground"][y][x] = "water"
                if rng.chance(0.18):
                    scene["overlay"][y][x] = "silt"
    # small ice patch
    ix = max(x0, min(scene["width"]-2, x0 + w//2 - 1))
    iy = max(y0, min(scene["height"]-2, y0 + h//2))
    for y in range(iy, min(scene["height"], iy+2)):
        for x in range(ix, min(scene["width"], ix+2)):
            scene["ground"][y][x] = "ice"

def _moss_border(scene, rng, x0, y0, w, h):
    for y in range(y0, min(scene["height"], y0+h)):
        for x in range(x0, min(scene["width"], x0+w)):
            is_edge = x in (x0, x0+w-1) or y in (y0, y0+h-1)
            if is_edge and rng.chance(0.75):
                scene["overlay"][y][x] = "moss"

def _mark_collision(scene, x0, y0, w, h, kind="solid"):
    for y in range(y0, min(scene["height"], y0+h)):
        for x in range(x0, min(scene["width"], x0+w)):
            scene["collision"][y][x] = kind

def _add_object(scene, kind, x, y, layer="objects", note=""):
    scene["objects"].append(SceneObject(kind=kind, x=x, y=y, layer=layer, note=note))

def _prop_spots(scene, rng):
    # Emphasize readable clusters rather than noise everywhere.
    spots = []
    bands = [(1, scene["height"]-3), (scene["height"]-4, scene["height"]-2)]
    for _ in range(24):
        x = rng.randint(0, scene["width"]-1)
        y = rng.randint(0, scene["height"]-1)
        if scene["ground"][y][x] in ("peat", "pine", "path", "chapel"):
            spots.append((x, y))
    return spots

def generate_scene(profile, seed=0, kind="silt_marsh"):
    from .constraints import require_int
    from .placement import can_place, apply_object_collision, reserve, reserve_path_tiles
    from .navigation import ensure_route

    seed=require_int("seed",seed)
    if kind != "silt_marsh":
        raise ValueError(f"Unknown scene kind: {kind}")
    rng=SeededRNG(seed)
    w,h=20,15
    scene={
        "name":"Smoliani Bolota","kind":kind,"seed":seed,
        "tile_size":int(profile.get("tile_size",16)),"width":w,"height":h,
        "ground":_blank_grid(w,h,"peat"),"overlay":_blank_grid(w,h,None),
        "collision":_blank_grid(w,h,"walk"),"objects":[],
        "spawn":{"x":2,"y":12},"landmarks":{},"_reserved":set(),
    }

    def add(kind,x,y,layer="objects",note="",force=False):
        if not force and not can_place(scene,kind,x,y): return False
        scene["objects"].append(SceneObject(kind=kind,x=x,y=y,layer=layer,note=note))
        apply_object_collision(scene,kind,x,y)
        return True

    # Background chapel precinct.
    _rect(scene["ground"],0,0,w,5,"chapel")
    _moss_border(scene,rng,0,0,w,5)
    for x in range(0,w,2): add("cliff_straight",x,0,layer="backdrop",force=True)
    _mark_collision(scene,0,0,w,1,"solid")

    # Printing chapel mass and altar.
    chapel_x=5+rng.randint(-1,1); chapel_y=1; chapel_w,chapel_h=6,3
    _rect(scene["ground"],chapel_x,chapel_y,chapel_w,chapel_h,"chapel")
    _mark_collision(scene,chapel_x,chapel_y,chapel_w,chapel_h,"solid")
    scene["landmarks"]["printing_chapel"]={"x":chapel_x,"y":chapel_y,"w":chapel_w,"h":chapel_h}
    add("printing_press_altar",chapel_x+1,chapel_y+1,note="courtyard focal machine-altar",force=True)

    shrine_x=13+rng.randint(-1,1); shrine_y=1
    scene["landmarks"]["nanolith_shrine"]={"x":shrine_x,"y":shrine_y}
    add("nanolith_shrine",shrine_x,shrine_y,note="sacred landmark",force=True)
    add("mask_cross",1,2,note="roadside warning marker",force=True)
    _mark_collision(scene,1,2,2,1,"solid")

    # Mid terrain and bog first; navigation is carved after hazards exist.
    for y in range(5,10):
        for x in range(w): scene["ground"][y][x]="peat" if rng.chance(0.42) else "pine"
    bog_x,bog_y,bog_w,bog_h=11,8,7,5
    _carve_bog(scene,rng,bog_x,bog_y,bog_w,bog_h)
    scene["landmarks"]["bog"]={"x":bog_x,"y":bog_y,"w":bog_w,"h":bog_h}
    for y in range(h):
        for x in range(w):
            if scene["ground"][y][x]=="water": scene["collision"][y][x]="hazard"
            elif scene["ground"][y][x]=="ice": scene["collision"][y][x]="walk"

    # Foreground material variation.
    for y in range(10,h):
        for x in range(w):
            if scene["ground"][y][x]=="peat" and rng.chance(0.35): scene["ground"][y][x]="pine"

    # Protected traversal spine and bridge.
    for x in range(2,14):
        scene["ground"][7][x]="path"; scene["overlay"][7][x]=None; scene["collision"][7][x]="walk"
    ensure_route(scene,(2,12),(2,11))
    ensure_route(scene,(2,11),(10,7))
    reserve_path_tiles(scene)
    for yy in range(11,14):
        for xx in range(1,4):
            scene["collision"][yy][xx]="walk"; scene["overlay"][yy][xx]=None; reserve(scene,{(xx,yy)})
            if scene["ground"][yy][xx]=="water": scene["ground"][yy][xx]="path"

    # Random props, all footprint-aware.
    spots=_prop_spots(scene,rng)
    for x,y in spots:
        g=scene["ground"][y][x]
        choices=[]
        if g=="path" and rng.chance(0.10): choices=["paper_stack"]
        elif g in ("peat","pine") and rng.chance(0.08): choices=["skull_stake_a","skull_stake_b","silt_growth"]
        elif g=="chapel" and rng.chance(0.06): choices=["paper_stack","brazier_lit","brazier_off"]
        elif g in ("peat","pine") and rng.chance(0.05): choices=["biogel_barrel","biogel_barrel_leaking","chest"]
        if choices: add(rng.choice(choices),x,y)

    # Iconic props with deterministic fallback positions.
    requested=[
        ("brazier_lit",[(4,4),(3,5),(5,5)]),
        ("warning_board",[(6,9),(5,9),(7,9)]),
        ("skull_stake_a",[(3,12),(4,12),(2,10)]),
        ("biogel_barrel_leaking",[(15,13),(17,13),(18,12)]),
        ("silt_growth",[(16,10),(17,10),(18,10)]),
    ]
    for obj,candidates in requested:
        for x,y in candidates:
            if add(obj,x,y,note="iconic prop"):
                break

    # Enemy marker must be walkable and clear.
    candidates=[(12,9),(11,9),(10,10),(9,10),(12,11)]
    ex,ey=next(((x,y) for x,y in candidates if 0<=x<w and 0<=y<h and scene["collision"][y][x]=="walk"), (2,11))
    scene["enemy_spawn"]={"kind":"striga","x":ex,"y":ey}
    return scene

def tile_id_grid(scene, which="ground"):
    grid = scene[which]
    return [[0 if v is None else TILE_IDS.get(v, 0) for v in row] for row in grid]

def flatten_grid(grid):
    out = []
    for row in grid:
        out.extend(row)
    return out

def scene_summary(scene):
    collision_counts = {}
    for row in scene.get("collision", []):
        for value in row:
            collision_counts[value] = collision_counts.get(value, 0) + 1
    return {
        "name": scene["name"],
        "kind": scene["kind"],
        "seed": scene["seed"],
        "size_tiles": [scene["width"], scene["height"]],
        "tile_size": scene["tile_size"],
        "object_count": len(scene.get("objects", [])),
        "encounter_count": len(scene.get("encounters", [])),
        "find_count": len(scene.get("finds", [])),
        "hollow_count": len(scene.get("hollows", [])),
        "collision_counts": collision_counts,
        "spawn": scene["spawn"],
        "enemy_spawn": scene.get("enemy_spawn"),
        "landmarks": scene.get("landmarks", {}),
    }
