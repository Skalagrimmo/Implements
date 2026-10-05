import math
from .rng import SeededRNG
from .biomes import get_biome, weighted_choice
from .placement import occupied_cells, reserved_cells
from .constraints import require_int


def _walkable(scene, x, y):
    return 0 <= x < scene["width"] and 0 <= y < scene["height"] and scene["collision"][y][x] == "walk"


def _entity_cells(scene):
    cells = set()
    for e in scene.get("encounters", []):
        cells.add((e["x"],e["y"]))
    for f in scene.get("finds", []):
        cells.add((f["x"],f["y"]))
    return cells


def _candidate_cells(scene, spawn_margin=0):
    blocked = occupied_cells(scene) | reserved_cells(scene) | _entity_cells(scene)
    sx,sy = scene["spawn"]["x"],scene["spawn"]["y"]
    out=[]
    for y in range(scene["height"]):
        for x in range(scene["width"]):
            if (x,y) in blocked or not _walkable(scene,x,y):
                continue
            if spawn_margin and abs(x-sx)+abs(y-sy) < spawn_margin:
                continue
            out.append((x,y))
    return out



def _stable_fractional_target(raw_target, seed):
    """Deterministic stochastic rounding.

    floor(raw + u) is monotonic in raw for a fixed u, so a larger multiplier
    cannot produce a smaller integer target for the same seed.
    """
    rng=SeededRNG(int(seed)+510_731)
    return int(math.floor(float(raw_target)+rng.random()))


def generate_encounters(scene, biome_kind, seed=0):
    seed = require_int("seed", seed)
    biome = get_biome(biome_kind)
    rng = SeededRNG(seed + 500_000)
    geo_mult=float(scene.get("geography",{}).get("modifiers",{}).get("encounter_mult",1.0))
    raw_target=scene["width"]*scene["height"]*biome["encounter_density"]*geo_mult
    target=max(1,_stable_fractional_target(raw_target,seed))
    candidates = _candidate_cells(scene, spawn_margin=4)
    target = min(target, len(candidates))
    chosen = rng.sample(candidates, target) if target else []
    encounters=[]
    for x,y in chosen:
        encounters.append({
            "kind": weighted_choice(rng, biome["enemy_weights"]),
            "x": x, "y": y,
            "tier": 1 + (1 if rng.chance(0.18) else 0),
            "group": f"{biome_kind}:{len(encounters)+1}",
        })
    scene["encounters"] = encounters
    return encounters


def generate_finds(scene, biome_kind, seed=0):
    seed = require_int("seed", seed)
    biome = get_biome(biome_kind)
    rng = SeededRNG(seed + 700_000)
    target = max(2, int(scene["width"] * scene["height"] * 0.018))
    candidates = _candidate_cells(scene, spawn_margin=1)
    target = min(target, len(candidates))
    chosen = rng.sample(candidates, target) if target else []
    finds=[]
    for x,y in chosen:
        finds.append({
            "kind": weighted_choice(rng, biome["loot_weights"]),
            "x": x, "y": y,
            "rarity": "rare" if rng.chance(0.12) else "common",
        })
    scene["finds"] = finds
    return finds
