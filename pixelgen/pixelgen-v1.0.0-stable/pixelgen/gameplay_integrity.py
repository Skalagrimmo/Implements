from .abilities import ABILITY_ORDER
from .progression import simulate_progression, reachable_sectors, OPPOSITE
from .placement import occupied_cells

def validate_gameplay_integrity(world):
    errors = []
    gp = world.get("gameplay")
    if not isinstance(gp, dict):
        return ["missing gameplay metadata"]

    lookup = {(s["sx"],s["sy"]):s for s in world["sectors"]}
    known = set(ABILITY_ORDER)

    # Link metadata must be reciprocal and semantically valid.
    for s in world["sectors"]:
        src = (s["sx"],s["sy"])
        for edge, link in s["links"].items():
            meta = link.get("gameplay")
            if not meta:
                errors.append(f"{src} {edge}: missing gameplay metadata")
                continue
            if meta.get("state") not in ("open","sealed","gated","secret"):
                errors.append(f"{src} {edge}: invalid gameplay state")
            req = meta.get("requires")
            if req is not None and req not in known:
                errors.append(f"{src} {edge}: unknown required ability {req}")
            dst = tuple(link["to"])
            other = lookup.get(dst)
            if not other:
                continue
            rev = other["links"].get(OPPOSITE[edge])
            if not rev or rev.get("gameplay") != meta:
                errors.append(f"{src} {edge}: non-reciprocal gameplay link metadata")

    # Pickups/secrets must be on valid walkable cells and must not overlap objects.
    pickup_ids = set()
    pickup_abilities = set()
    for s in world["sectors"]:
        scene = s["scene"]
        occupied = occupied_cells(scene)
        w,h = scene["width"],scene["height"]
        for p in scene.get("ability_pickups", []):
            if p["id"] in pickup_ids:
                errors.append(f"duplicate ability pickup id {p['id']}")
            pickup_ids.add(p["id"])
            if p["ability"] not in known:
                errors.append(f"unknown pickup ability {p['ability']}")
            pickup_abilities.add(p["ability"])
            x,y = p["x"],p["y"]
            if not (0 <= x < w and 0 <= y < h):
                errors.append(f"pickup {p['id']} out of bounds")
            elif scene["collision"][y][x] != "walk":
                errors.append(f"pickup {p['id']} not on walkable cell")
            if (x,y) in occupied:
                errors.append(f"pickup {p['id']} overlaps object")
        for sec in scene.get("secrets", []):
            if sec.get("requires") not in known:
                errors.append(f"secret {sec.get('id')} has unknown requirement")
            x,y = sec["x"],sec["y"]
            if not (0 <= x < w and 0 <= y < h):
                errors.append(f"secret {sec.get('id')} out of bounds")
            elif scene["collision"][y][x] != "walk":
                errors.append(f"secret {sec.get('id')} not on walkable cell")

    declared = set(gp.get("ability_order", []))
    if declared != pickup_abilities:
        errors.append("declared ability_order does not match placed ability pickups")

    # Full simulation is the main anti-softlock check.
    try:
        sim = simulate_progression(world)
    except Exception as e:
        errors.append(f"progression simulation failed: {e}")
        return errors

    if not sim["final_sector_reachable"]:
        errors.append("final sector is not reachable after progression")
    if not sim["all_sectors_reachable"]:
        errors.append("not all sectors are reachable after collecting abilities")
    if set(sim["abilities"]) != declared:
        errors.append("not all declared abilities can be collected")

    # Each ability must be obtainable without already possessing itself.
    order = gp.get("ability_order", [])
    prior = set()
    pickup_locations = {}
    for s in world["sectors"]:
        key = (s["sx"],s["sy"])
        for p in s["scene"].get("ability_pickups", []):
            pickup_locations[p["ability"]] = key
    for ability in order:
        reach = reachable_sectors(world, prior)
        loc = pickup_locations.get(ability)
        if loc not in reach:
            errors.append(f"ability {ability} is softlocked behind itself or a later gate")
        prior.add(ability)

    return errors
