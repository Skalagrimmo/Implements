from collections import Counter
from .navigation import reachable, exit_cell
from .placement import object_cells


def _obj_dict(o):
    return o.to_dict() if hasattr(o,"to_dict") else o


def validate_scene_integrity(scene, links=None):
    errors=[]
    w,h=scene["width"],scene["height"]
    if len(scene["ground"]) != h or any(len(r)!=w for r in scene["ground"]): errors.append("ground dimensions mismatch")
    if len(scene["overlay"]) != h or any(len(r)!=w for r in scene["overlay"]): errors.append("overlay dimensions mismatch")
    if len(scene["collision"]) != h or any(len(r)!=w for r in scene["collision"]): errors.append("collision dimensions mismatch")
    sx,sy=scene["spawn"]["x"],scene["spawn"]["y"]
    if not (0<=sx<w and 0<=sy<h): errors.append("spawn out of bounds")
    elif scene["collision"][sy][sx] != "walk": errors.append("spawn is not walkable")

    occupied=set()
    for raw in scene.get("objects",[]):
        o=_obj_dict(raw); x,y=o["x"],o["y"]
        cells=object_cells(o["kind"],x,y,scene.get("tile_size",16))
        if any(not (0<=cx<w and 0<=cy<h) for cx,cy in cells): errors.append(f"object {o['kind']} out of bounds")
        overlap=cells & occupied
        if overlap: errors.append(f"object overlap: {o['kind']} at {sorted(overlap)}")
        occupied |= cells

    seen_entities=set()
    for bucket in ("encounters","finds"):
        for e in scene.get(bucket,[]):
            x,y=e["x"],e["y"]
            if not (0<=x<w and 0<=y<h): errors.append(f"{bucket} out of bounds")
            elif scene["collision"][y][x] != "walk": errors.append(f"{bucket} on non-walkable cell")
            if (x,y) in seen_entities: errors.append(f"entity overlap at {(x,y)}")
            seen_entities.add((x,y))
            if (x,y) in occupied: errors.append(f"{bucket} overlaps object at {(x,y)}")

    reach=reachable(scene,(sx,sy))
    if links:
        for edge,link in links.items():
            target=exit_cell(scene,edge,link["coord"])
            if target not in reach: errors.append(f"exit {edge} unreachable from spawn")
    return errors


def validate_world_integrity(world):
    errors=[]
    lookup={(s["sx"],s["sy"]):s for s in world["sectors"]}
    if len(lookup) != world["cols"]*world["rows"]:
        errors.append("sector count/grid mismatch")
    opposite={"N":"S","S":"N","E":"W","W":"E"}
    for s in world["sectors"]:
        errors += [f"sector {s['sx']},{s['sy']}: {e}" for e in validate_scene_integrity(s["scene"],s["links"])]
        for edge,link in s["links"].items():
            dst=tuple(link["to"])
            if dst not in lookup:
                errors.append(f"sector link {s['sx']},{s['sy']} {edge} points outside world")
                continue
            other=lookup[dst]
            rev=other["links"].get(opposite[edge])
            if not rev or rev["to"] != [s["sx"],s["sy"]] or rev["coord"] != link["coord"]:
                errors.append(f"non-reciprocal link at {s['sx']},{s['sy']} {edge}")
    return errors
