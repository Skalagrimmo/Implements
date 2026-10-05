from math import ceil
from .rng import SeededRNG
from .metadata import STRUCTURE_META
from .placement import object_cells, occupied_cells, reserved_cells
from .biomes import get_biome, weighted_choice

LANDMARK_CATALOG = {
    "mask_cross": {
        "scope": "local",
        "semantic": "roadside",
        "map_label": "Mask Cross",
        "silhouette": "cross",
    },
    "nanolith_shrine": {
        "scope": "regional",
        "semantic": "remote_silt",
        "map_label": "Nanolith Shrine",
        "silhouette": "spire",
    },
    "printing_press_altar": {
        "scope": "regional",
        "semantic": "civic_path",
        "map_label": "Press Altar",
        "silhouette": "press",
    },
    "printing_cathedral": {
        "scope": "world",
        "semantic": "civic_center",
        "map_label": "Printing Cathedral",
        "silhouette": "cathedral",
    },
    "silt_spire": {
        "scope": "world",
        "semantic": "remote_silt",
        "map_label": "Silt Spire",
        "silhouette": "spire",
    },
}

LOCAL_CHANCE = {
    "silt_marsh": 0.24,
    "dark_forest": 0.36,
    "frozen_pass": 0.26,
    "ruined_settlement": 0.18,
    "reformed_chapel": 0.20,
}

WORLD_KIND_WEIGHTS = {
    "silt_marsh": [("silt_spire", 4), ("printing_cathedral", 1)],
    "dark_forest": [("silt_spire", 4), ("printing_cathedral", 1)],
    "frozen_pass": [("printing_cathedral", 3), ("silt_spire", 2)],
    "ruined_settlement": [("printing_cathedral", 5), ("silt_spire", 1)],
    "reformed_chapel": [("printing_cathedral", 6), ("silt_spire", 1)],
}

PROMINENCE = {"local": 25, "regional": 60, "world": 100}
PLACEMENT_ZONES = ("NW","SE","SW","NE","C")

def _zone_for(index, seed):
    return PLACEMENT_ZONES[(index + abs(int(seed))) % len(PLACEMENT_ZONES)]

def _zone_bonus(scene, x, y, zone):
    if not zone:
        return 0.0
    nx=(x+0.5)/max(1,scene["width"])
    ny=(y+0.5)/max(1,scene["height"])
    targets={"NW":(0.28,0.28),"NE":(0.72,0.28),"SW":(0.28,0.72),"SE":(0.72,0.72),"C":(0.50,0.50)}
    tx,ty=targets.get(zone,(0.5,0.5))
    return -((abs(nx-tx)+abs(ny-ty))*2.0)

def landmark_info(kind):
    if kind not in LANDMARK_CATALOG:
        raise ValueError(f"unknown landmark kind {kind!r}")
    return LANDMARK_CATALOG[kind]

def _manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def _sector_biome_map(cols, rows, cycle):
    return {
        (sx, sy): cycle[(sx + sy*cols) % len(cycle)]
        for sy in range(rows)
        for sx in range(cols)
    }

def _choose_world_sector(rng, cols, rows, biomes):
    if cols*rows < 4:
        return None
    center = ((cols-1)/2.0, (rows-1)/2.0)
    start = (0, 0)
    candidates = [(sx,sy) for sy in range(rows) for sx in range(cols) if (sx,sy) != start]
    best = None
    best_score = None
    for pos in candidates:
        central = -(abs(pos[0]-center[0]) + abs(pos[1]-center[1]))
        from_start = _manhattan(pos, start)
        # Slight seeded jitter prevents the same coordinate from becoming canonical.
        score = central * 1.8 + from_start * 0.9 + rng.random() * 2.4
        if best_score is None or score > best_score:
            best_score, best = score, pos
    return best

def _choose_spaced_sector(rng, candidates, selected):
    if not candidates:
        return None
    best = None
    best_score = None
    for pos in candidates:
        spacing = min((_manhattan(pos, s) for s in selected), default=99)
        edge_penalty = 0.25 if (pos[0] in (0, max(x for x,_ in candidates)) or pos[1] in (0, max(y for _,y in candidates))) else 0
        score = spacing * 4.0 - edge_penalty + rng.random() * 2.0
        if best_score is None or score > best_score:
            best_score, best = score, pos
    return best

def plan_world_landmarks(seed, cols, rows, cycle=None, biome_map=None):
    rng = SeededRNG(int(seed) + 6_101_000)
    if biome_map is not None:
        biomes = dict(biome_map)
    else:
        if not cycle:
            raise ValueError("cycle or biome_map is required")
        biomes = _sector_biome_map(cols, rows, cycle)
    per_sector = {(sx,sy): [] for sy in range(rows) for sx in range(cols)}
    placements = []
    selected = []

    # One unique world-scale anchor in worlds large enough to support one.
    world_sector = _choose_world_sector(rng, cols, rows, biomes)
    if world_sector is not None:
        biome = biomes[world_sector]
        kind = weighted_choice(rng, WORLD_KIND_WEIGHTS[biome])
        info = landmark_info(kind)
        item = {
            "id": f"world_01_{kind}",
            "kind": kind,
            "scope": "world",
            "semantic": info["semantic"],
            "map_label": info["map_label"],
            "sector": list(world_sector),
            "preferred_zone": _zone_for(0, seed),
        }
        per_sector[world_sector].append(dict(item))
        placements.append(dict(item))
        selected.append(world_sector)

    # Roughly one regional landmark per ~6 sectors, capped so they remain memorable.
    sector_count = cols * rows
    regional_count = 0 if sector_count < 3 else max(1, min(6, round(sector_count / 6)))
    all_positions = [(sx,sy) for sy in range(rows) for sx in range(cols)]
    for i in range(regional_count):
        candidates = [p for p in all_positions if p not in selected and p != (0,0)]
        if not candidates:
            break
        spaced = [p for p in candidates if all(_manhattan(p,s) >= 2 for s in selected)]
        pos = _choose_spaced_sector(rng, spaced or candidates, selected)
        biome = biomes[pos]
        regional_weights = [
            (kind, weight)
            for kind, weight in get_biome(biome)["landmark_weights"]
            if kind in ("nanolith_shrine", "printing_press_altar")
        ]
        if not regional_weights:
            regional_weights = [("nanolith_shrine",1),("printing_press_altar",1)]
        kind = weighted_choice(rng, regional_weights)
        info = landmark_info(kind)
        item = {
            "id": f"regional_{i+1:02d}_{kind}",
            "kind": kind,
            "scope": "regional",
            "semantic": info["semantic"],
            "map_label": info["map_label"],
            "sector": list(pos),
            "preferred_zone": _zone_for(i+1, seed),
        }
        per_sector[pos].append(dict(item))
        placements.append(dict(item))
        selected.append(pos)

    # Local landmarks are optional. Most sectors deliberately have none.
    local_index = 0
    for pos in all_positions:
        biome = biomes[pos]
        chance = LOCAL_CHANCE.get(biome, 0.25)
        if per_sector[pos]:
            chance *= 0.28  # avoid landmark clutter in already-important sectors
        near_anchor = any(_manhattan(pos,s) <= 1 for s in selected)
        if near_anchor:
            chance *= 0.55
        if rng.chance(chance):
            local_index += 1
            kind = "mask_cross"
            info = landmark_info(kind)
            item = {
                "id": f"local_{local_index:02d}_{kind}",
                "kind": kind,
                "scope": "local",
                "semantic": info["semantic"],
                "map_label": info["map_label"],
                "sector": list(pos),
                "preferred_zone": _zone_for(local_index+7, seed),
            }
            per_sector[pos].append(dict(item))
            placements.append(dict(item))

    return {
        "version": "0.6.2",
        "policy": {
            "local": "optional / scene-scale orientation",
            "regional": "sparse / multi-sector orientation",
            "world": "unique large-scale cognitive anchor",
            "spacing": "regional anchors prefer >=2 sector Manhattan separation",
            "composition": "preferred zones vary to suppress repeated corner placement",
        },
        "per_sector": per_sector,
        "placements": placements,
    }

def _visual_top_margin(kind, tile_size):
    meta = STRUCTURE_META.get(kind, {})
    size_h = meta.get("size", [tile_size,tile_size])[1]
    footprint_h = meta.get("footprint", [tile_size,tile_size])[1]
    return max(0, ceil(max(0, size_h-footprint_h) / tile_size))

def _distance_to_path(scene, x, y):
    path = []
    for yy,row in enumerate(scene["ground"]):
        for xx,value in enumerate(row):
            if value == "path":
                path.append((xx,yy))
    if not path:
        return scene["width"] + scene["height"]
    return min(abs(x-px)+abs(y-py) for px,py in path)

def _near_material(scene, cells, materials, radius=3):
    if not materials:
        return 0
    w,h=scene["width"],scene["height"]
    score=0
    for cx,cy in cells:
        for yy in range(max(0,cy-radius),min(h,cy+radius+1)):
            for xx in range(max(0,cx-radius),min(w,cx+radius+1)):
                if scene["ground"][yy][xx] in materials or scene["overlay"][yy][xx] in materials:
                    score += 1
    return score

def _candidate_free(scene, kind, x, y, allow_structural_overlap=False):
    cells = object_cells(kind, x, y, scene.get("tile_size",16))
    if not cells:
        return False
    if any(not (0 <= cx < scene["width"] and 0 <= cy < scene["height"]) for cx,cy in cells):
        return False

    overlap = cells & reserved_cells(scene)
    if overlap:
        if not allow_structural_overlap:
            return False
        structural = set(scene.get("_structural_path_cells", set()))
        critical = set(scene.get("_critical_reserved", set()))
        # Civic structures may consume visual street/courtyard paving, but never
        # spawn safety cells or other non-structural protected reservations.
        if not overlap <= structural:
            return False
        if overlap & critical:
            return False

    if cells & occupied_cells(scene):
        return False
    return True

def _score_candidate(scene, kind, semantic, x, y, rng, preferred_zone=None):
    cells = object_cells(kind, x, y, scene.get("tile_size",16))
    sx,sy = scene["spawn"]["x"],scene["spawn"]["y"]
    center = ((scene["width"]-1)/2.0, (scene["height"]-1)/2.0)
    cx = sum(px for px,_ in cells)/len(cells)
    cy = sum(py for _,py in cells)/len(cells)
    path_d = _distance_to_path(scene, round(cx), round(cy))
    spawn_d = abs(cx-sx)+abs(cy-sy)
    center_d = abs(cx-center[0])+abs(cy-center[1])
    chapel_near = _near_material(scene,cells,{"chapel"},radius=2)
    silt_near = _near_material(scene,cells,{"water","silt"},radius=3)

    if semantic == "roadside":
        score = -abs(path_d-1)*7.0 + spawn_d*0.15 - center_d*0.05
    elif semantic == "civic_path":
        score = -abs(path_d-2)*3.0 + chapel_near*0.55 - center_d*0.12 + spawn_d*0.08
    elif semantic == "civic_center":
        score = -abs(path_d-2)*2.5 + chapel_near*0.65 - center_d*0.50 + spawn_d*0.05
    elif semantic == "remote_silt":
        score = path_d*0.55 + spawn_d*0.35 + silt_near*0.48 - center_d*0.05
    else:
        score = -center_d*0.2 + spawn_d*0.1
    score += _zone_bonus(scene, cx, cy, preferred_zone) * 1.7
    return score + rng.random()*2.5

def place_landmark(scene, rng, spec):
    kind = spec["kind"]
    semantic = spec.get("semantic", landmark_info(kind)["semantic"])
    ts = scene.get("tile_size",16)
    top_margin = _visual_top_margin(kind, ts)
    # Keep large silhouettes away from world boundaries/exits.
    edge_margin = 2 if spec.get("scope") != "world" else 3

    candidates = []
    for y in range(max(top_margin,edge_margin), scene["height"]-edge_margin):
        for x in range(edge_margin, scene["width"]-edge_margin):
            allow_structural_overlap = (
                semantic in ("civic_center","civic_path")
                and spec.get("scope") in ("regional","world")
            )
            if not _candidate_free(
                scene,kind,x,y,
                allow_structural_overlap=allow_structural_overlap
            ):
                continue
            score = _score_candidate(scene,kind,semantic,x,y,rng,spec.get("preferred_zone"))
            candidates.append((score,x,y))
    candidates.sort(reverse=True)
    if not candidates:
        return None

    _,x,y = candidates[0]
    cells = object_cells(kind,x,y,ts)

    # Hazard under the footprint is converted to stable local ground; the landmark
    # itself remains solid and never occupies protected navigation cells.
    for cx,cy in cells:
        scene["collision"][cy][cx] = "walk"
        scene["overlay"][cy][cx] = None
        if scene["ground"][cy][cx] == "water":
            scene["ground"][cy][cx] = scene.get("_base_ground","peat")

    from .scene import SceneObject
    from .placement import apply_object_collision
    note = f"{spec.get('scope','local')} landmark: {semantic}"
    scene["objects"].append(SceneObject(kind=kind,x=x,y=y,note=note))
    apply_object_collision(scene,kind,x,y)

    record = {
        "id": spec["id"],
        "kind": kind,
        "scope": spec.get("scope","local"),
        "semantic": semantic,
        "map_label": spec.get("map_label", landmark_info(kind)["map_label"]),
        "prominence": PROMINENCE.get(spec.get("scope","local"),25),
        "x": x, "y": y,
    }
    if spec.get("preferred_zone") is not None:
        record["preferred_zone"] = spec["preferred_zone"]
    scene.setdefault("landmarks", {})[spec["id"]] = record
    return record

def standalone_landmark_plan(seed, biome_kind):
    # Standalone biome previews use the same rarity rule instead of forcing a landmark.
    rng=SeededRNG(int(seed)+6_102_000)
    specs=[]
    chance=LOCAL_CHANCE.get(biome_kind,0.25)
    if rng.chance(chance):
        info=landmark_info("mask_cross")
        specs.append({
            "id":"local_preview_mask_cross",
            "kind":"mask_cross","scope":"local",
            "semantic":info["semantic"],"map_label":info["map_label"],
        })
    # A regional preview is intentionally uncommon.
    if rng.chance(0.22):
        weights=[(k,w) for k,w in get_biome(biome_kind)["landmark_weights"] if k in ("nanolith_shrine","printing_press_altar")]
        if weights:
            kind=weighted_choice(rng,weights)
            info=landmark_info(kind)
            specs.append({
                "id":f"regional_preview_{kind}",
                "kind":kind,"scope":"regional",
                "semantic":info["semantic"],"map_label":info["map_label"],
            })
    return specs
