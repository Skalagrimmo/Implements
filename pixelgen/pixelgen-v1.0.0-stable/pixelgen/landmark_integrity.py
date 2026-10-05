from .landmarks import LANDMARK_CATALOG
from .placement import object_cells

def validate_landmark_integrity(world):
    errors=[]
    placements=world.get("landmark_system",{}).get("placements",[])
    ids=set()
    world_count=0
    regional_sectors=[]
    scene_records={}

    for s in world["sectors"]:
        key=(s["sx"],s["sy"])
        scene_records[key]=s["scene"].get("landmarks",{})
        for lid,item in scene_records[key].items():
            if lid in ids:
                errors.append(f"duplicate landmark id {lid}")
            ids.add(lid)
            if item.get("kind") not in LANDMARK_CATALOG:
                errors.append(f"unknown landmark kind {item.get('kind')}")
            if item.get("scope") not in ("local","regional","world"):
                errors.append(f"invalid landmark scope {item.get('scope')}")
            if item.get("scope")=="world":
                world_count += 1
            if item.get("scope")=="regional":
                regional_sectors.append(key)

            # Landmark object and metadata must agree.
            matching=[]
            for raw in s["scene"].get("objects",[]):
                o=raw.to_dict() if hasattr(raw,"to_dict") else raw
                if o["kind"]==item["kind"] and o["x"]==item["x"] and o["y"]==item["y"]:
                    matching.append(o)
            if not matching:
                errors.append(f"landmark {lid} has no matching scene object")

    if world["cols"]*world["rows"] >= 4 and world_count != 1:
        errors.append(f"expected exactly one world landmark, got {world_count}")
    if world["cols"]*world["rows"] < 4 and world_count > 0:
        errors.append("tiny world should not have a world landmark")

    # Planned placements must have actual placed records.
    for p in placements:
        key=tuple(p["sector"])
        recs=scene_records.get(key,{})
        if p["id"] not in recs:
            errors.append(f"planned landmark {p['id']} was not placed")

    # Regional anchors should not all collapse into the same sector.
    if len(regional_sectors) != len(set(regional_sectors)):
        errors.append("multiple regional landmarks share a sector")

    return errors
