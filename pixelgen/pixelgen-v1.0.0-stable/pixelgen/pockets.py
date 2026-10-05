from .rng import SeededRNG
from .constraints import require_probability, require_int
from .placement import reserved_cells, occupied_cells, reserve


def insert_hollow(scene, seed=0, chance=0.50):
    seed = require_int("seed", seed)
    chance = require_probability("hollow chance", chance)
    rng = SeededRNG(seed + 900_000)
    if not rng.chance(chance):
        scene["hollows"] = []
        return []

    occupied = occupied_cells(scene)
    reserved = reserved_cells(scene)
    sx,sy = scene["spawn"]["x"],scene["spawn"]["y"]

    candidate = None
    for _ in range(120):
        w = rng.randint(3, 5)
        h = rng.randint(2, 4)
        max_x = scene["width"] - w - 1
        max_y = scene["height"] - h - 1
        if max_x < 1 or max_y < 1:
            break
        x0 = rng.randint(1, max_x)
        y0 = rng.randint(1, max_y)
        cells = {(x,y) for y in range(y0,y0+h) for x in range(x0,x0+w)}
        if cells & occupied or cells & reserved:
            continue
        if min(abs(x-sx)+abs(y-sy) for x,y in cells) < 5:
            continue
        candidate = (x0,y0,w,h,cells)
        break

    if candidate is None:
        scene["hollows"] = []
        return []

    x0,y0,w,h,cells = candidate
    for y in range(y0, y0+h):
        for x in range(x0, x0+w):
            scene["ground"][y][x] = "chapel"
            scene["collision"][y][x] = "walk"
            scene["overlay"][y][x] = None

    # Silt perimeter is visual, not collision.
    for x in range(x0, x0+w):
        scene["overlay"][y0][x] = "silt"
        scene["overlay"][y0+h-1][x] = "silt"
    for y in range(y0, y0+h):
        scene["overlay"][y][x0] = "silt"
        scene["overlay"][y][x0+w-1] = "silt"

    entrance = {"x": x0 + w//2, "y": y0 + h - 1}
    hollow = {
        "kind": "silt_hollow",
        "x": x0, "y": y0, "w": w, "h": h,
        "entrance": entrance,
        "secret": True,
    }
    scene["hollows"] = [hollow]
    reserve(scene,cells)
    return [hollow]
