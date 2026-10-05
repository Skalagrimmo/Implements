from .rng import SeededRNG
from .scene import SceneObject
from .biomes import get_biome, weighted_choice
from .placement import can_place, apply_object_collision, reserve, reserve_path_tiles
from .navigation import ensure_route
from .constraints import require_int
from .landmarks import place_landmark, standalone_landmark_plan
from .scene_structure import apply_biome_structure


def _blank(w, h, value):
    return [[value for _ in range(w)] for _ in range(h)]


def _set(grid, x, y, value):
    if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
        grid[y][x] = value


def _add_object(scene, kind, x, y, note="", force=False):
    if not force and not can_place(scene, kind, x, y):
        return False
    scene["objects"].append(SceneObject(kind=kind, x=x, y=y, note=note))
    apply_object_collision(scene, kind, x, y)
    return True



def _hazard_rng(seed, x, y):
    # Per-candidate deterministic substream. A hazard decision at one coordinate
    # can no longer shift RNG state for later coordinates or unrelated systems.
    return SeededRNG(
        int(seed)
        + 1_731_000
        + int(x) * 73_856_093
        + int(y) * 19_349_663
    )


def _clear_safe_zone(scene, cx, cy, radius=1):
    for y in range(max(0, cy-radius), min(scene["height"], cy+radius+1)):
        for x in range(max(0, cx-radius), min(scene["width"], cx+radius+1)):
            scene["collision"][y][x] = "walk"
            scene["overlay"][y][x] = None
            if scene["ground"][y][x] == "water":
                scene["ground"][y][x] = "peat"
            reserve(scene, {(x, y)})
            scene.setdefault("_critical_reserved", set()).add((x,y))




def _prop_pool(geography_context):
    base=[
        "warning_board",
        "paper_stack",
        "skull_stake_a",
        "skull_stake_b",
        "biogel_barrel",
        "silt_growth",
    ]
    dominant=(geography_context or {}).get("regional_influence",{}).get("dominant_channel")

    if dominant=="print_civic":
        # Civic influence may increase prop density, but it must not do so by
        # multiplying hazardous Silt growth. Keep the increased budget thematic.
        return [
            "warning_board",
            "paper_stack",
            "paper_stack",
            "biogel_barrel",
            "warning_board",
        ]

    if dominant=="silt_contamination":
        # Preserve the existing contamination identity without changing the
        # overall prop-count contract.
        return base+["silt_growth","silt_growth"]

    return base


def generate_biome_scene(profile, seed=0, biome_kind="silt_marsh", landmark_plan=None, geography_context=None):
    seed = require_int("seed", seed)
    biome = get_biome(biome_kind)
    rng = SeededRNG(seed)
    geography_context = dict(geography_context or {})
    modifiers = geography_context.get("modifiers", {})
    hazard_density = biome["hazard_density"] * float(modifiers.get("hazard_mult", 1.0))
    prop_density = biome["prop_density"] * float(modifiers.get("prop_mult", 1.0))
    w, h = 20, 15
    scene = {
        "name": biome["name"],
        "kind": biome_kind,
        "seed": int(seed),
        "tile_size": int(profile.get("tile_size",16)),
        "width": w,
        "height": h,
        "ground": _blank(w,h,biome["base_ground"]),
        "overlay": _blank(w,h,None),
        "collision": _blank(w,h,"walk"),
        "objects": [],
        "spawn": {"x":2,"y":12},
        "landmarks": {},
        "_reserved": set(),
        "_base_ground": biome["base_ground"],
        "geography": geography_context,
    }

    # Secondary-material swaths.
    for y in range(h):
        for x in range(w):
            band = (x + 2*y + seed) % 7
            if band in (0,1) and rng.chance(0.55):
                scene["ground"][y][x] = biome["secondary_ground"]

    # Hazard pockets use coordinate-stable RNG substreams.
    #
    # Hardening invariant:
    # lowering hazard_density for the same seed must remove candidate pockets,
    # not reshuffle the RNG sequence for all later cells and systems.
    hazard_probability=min(0.95,hazard_density)/12.0
    for y in range(4,h-2):
        for x in range(3,w-2):
            hrng=_hazard_rng(seed,x,y)
            if hrng.chance(hazard_probability):
                radius=1 if hrng.chance(0.75) else 2
                for yy in range(max(0,y-radius),min(h,y+radius+1)):
                    for xx in range(max(0,x-radius),min(w,x+radius+1)):
                        if hrng.chance(0.72):
                            scene["ground"][yy][xx]=biome["hazard_ground"]
                            scene["collision"][yy][xx]="hazard"

    # v0.7 transition belts: bring a neighboring biome's material into the
    # local scene specifically from the sector edge that touches that region.
    for trans in geography_context.get("transition_edges", []):
        neighbor_kind = trans.get("biome")
        if not neighbor_kind:
            continue
        neighbor = get_biome(neighbor_kind)
        material = neighbor["base_ground"]
        edge = trans.get("edge")
        depth = 3
        if edge == "N":
            cells = ((x,y) for y in range(0,depth) for x in range(w))
        elif edge == "S":
            cells = ((x,y) for y in range(h-depth,h) for x in range(w))
        elif edge == "W":
            cells = ((x,y) for y in range(h) for x in range(0,depth))
        elif edge == "E":
            cells = ((x,y) for y in range(h) for x in range(w-depth,w))
        else:
            cells = ()
        for tx,ty in cells:
            if rng.chance(0.42):
                scene["ground"][ty][tx] = material

    # v0.7.1: biome-specific structural skeleton.
    # A dedicated RNG keeps the morphology stable even if hazard/prop grammar changes.
    structure_rng = SeededRNG(seed + 7_101_000)
    structural = apply_biome_structure(
        scene, biome_kind, structure_rng, geography_context=geography_context
    )
    reserve_path_tiles(scene)

    # Protected player start and explicit connection into that biome's network.
    sx, sy = scene["spawn"]["x"], scene["spawn"]["y"]
    _clear_safe_zone(scene, sx, sy, radius=1)
    entry = (structural["entry"]["x"], structural["entry"]["y"])
    ensure_route(scene, (sx,sy), entry)

    # v0.6.1: landmarks are sparse cognitive anchors, not a mandatory per-sector decoration.
    specs = standalone_landmark_plan(seed, biome_kind) if landmark_plan is None else list(landmark_plan)
    scene["landmark_plan"] = [dict(s) for s in specs]
    for spec in specs:
        placed = place_landmark(scene, rng, spec)
        if placed is None:
            # World/regional anchors are contractual; local marks may be omitted if geometry is too tight.
            if spec.get("scope") in ("regional","world"):
                raise RuntimeError(f"could not place {spec.get('scope')} landmark {spec.get('kind')!r} in biome {biome_kind!r}")

    # Supporting props. Solid/low props cannot block protected routes or overlap one another.
    desired = max(3, int(w*h*prop_density))
    attempts = desired * 30
    placed = 0
    prop_kinds=_prop_pool(geography_context)
    while placed < desired and attempts > 0:
        attempts -= 1
        px = rng.randint(1,w-2)
        py = rng.randint(1,h-2)
        if scene["collision"][py][px] != "walk":
            continue
        if abs(px-sx) + abs(py-sy) < 3:
            continue
        kind = rng.choice(prop_kinds)
        if _add_object(scene, kind, px, py):
            placed += 1

    # Overlay accents are visual only and never change navigation.
    for yy in range(h):
        for xx in range(w):
            if scene["ground"][yy][xx] == biome["base_ground"] and rng.chance(0.035):
                scene["overlay"][yy][xx] = "moss"
            if scene["ground"][yy][xx] == biome["hazard_ground"] and rng.chance(0.18):
                scene["overlay"][yy][xx] = "silt"

    # Reassert protected cells after all visual overlays/objects.
    _clear_safe_zone(scene, sx, sy, radius=1)
    for px,py in list(scene["_reserved"]):
        if 0 <= px < w and 0 <= py < h and scene["collision"][py][px] != "solid":
            scene["collision"][py][px] = "walk"
            if scene["ground"][py][px] == biome["hazard_ground"]:
                scene["ground"][py][px] = "path"
            scene["overlay"][py][px] = None

    scene["enemy_spawn"] = {"kind": weighted_choice(rng, biome["enemy_weights"]), "x":12, "y":10}
    return scene
