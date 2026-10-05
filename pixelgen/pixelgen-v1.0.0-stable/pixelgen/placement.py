import math
from .metadata import STRUCTURE_META, PROP_META


def _meta(kind):
    if kind in STRUCTURE_META:
        return STRUCTURE_META[kind]
    return PROP_META.get(kind)


def footprint_tiles(kind, tile_size=16):
    meta = _meta(kind)
    if not meta:
        return (1, 1)
    fw, fh = meta.get("footprint", meta.get("size", [tile_size, tile_size]))
    if fw <= 0 or fh <= 0:
        return (0, 0)
    return (max(1, math.ceil(fw / tile_size)), max(1, math.ceil(fh / tile_size)))


def collision_role(kind):
    meta = _meta(kind) or {}
    return meta.get("collision", "none")


def object_cells(kind, x, y, tile_size=16):
    tw, th = footprint_tiles(kind, tile_size)
    return {(x + dx, y + dy) for dy in range(th) for dx in range(tw)}


def cells_in_bounds(scene, cells):
    return all(0 <= x < scene["width"] and 0 <= y < scene["height"] for x, y in cells)


def reserved_cells(scene):
    r = scene.setdefault("_reserved", set())
    if not isinstance(r, set):
        r = set(map(tuple, r))
        scene["_reserved"] = r
    return r


def occupied_cells(scene):
    result = set()
    ts = scene.get("tile_size", 16)
    for o in scene.get("objects", []):
        kind = o.kind if hasattr(o, "kind") else o["kind"]
        x = o.x if hasattr(o, "x") else o["x"]
        y = o.y if hasattr(o, "y") else o["y"]
        result |= object_cells(kind, x, y, ts)
    return result


def can_place(scene, kind, x, y, allow_reserved=False):
    cells = object_cells(kind, x, y, scene.get("tile_size", 16))
    if not cells_in_bounds(scene, cells):
        return False
    if not allow_reserved and cells & reserved_cells(scene):
        return False
    role = collision_role(kind)
    if role in ("full", "low", "hazard"):
        for cx, cy in cells:
            if scene["collision"][cy][cx] != "walk":
                return False
    return not bool(cells & occupied_cells(scene))


def apply_object_collision(scene, kind, x, y):
    role = collision_role(kind)
    if role in ("overlay", "wall_decor", "none", "portal"):
        return
    target = "hazard" if role == "hazard" else "solid"
    for cx, cy in object_cells(kind, x, y, scene.get("tile_size", 16)):
        if 0 <= cx < scene["width"] and 0 <= cy < scene["height"]:
            scene["collision"][cy][cx] = target


def reserve(scene, cells):
    reserved_cells(scene).update(cells)


def reserve_path_tiles(scene):
    cells = set()
    for y, row in enumerate(scene["ground"]):
        for x, value in enumerate(row):
            if value == "path":
                cells.add((x, y))
    reserve(scene, cells)
    return cells
