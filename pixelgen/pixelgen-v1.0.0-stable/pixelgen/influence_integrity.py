import math

def validate_influence_fields(world):
    inf=world.get("regional_influence")
    if not isinstance(inf,dict):
        return ["missing regional_influence"]
    errors=[]
    sectors={(s["sx"],s["sy"]):s for s in world.get("sectors",[])}
    isectors={(s["sx"],s["sy"]):s for s in inf.get("sectors",[])}
    if set(sectors)!=set(isectors):
        errors.append("influence sector map does not match world sectors")

    source_ids={s.get("id") for s in inf.get("sources",[])}
    for pos,item in isectors.items():
        for ch,val in item.get("channels",{}).items():
            if not isinstance(val,(int,float)) or not math.isfinite(val) or val<0:
                errors.append(f"sector {pos} invalid influence value {ch}={val}")
        for c in item.get("contributions",[]):
            if c.get("source_id") not in source_ids:
                errors.append(f"sector {pos} references unknown influence source")
            w=c.get("weight")
            if not isinstance(w,(int,float)) or not (0 <= w <= 2):
                errors.append(f"sector {pos} invalid contribution weight")
        scene_inf=sectors.get(pos,{}).get("scene",{}).get("geography",{}).get("regional_influence")
        if scene_inf is not None:
            if scene_inf.get("dominant_channel") != item.get("dominant_channel"):
                errors.append(f"sector {pos} scene influence disagrees with world influence")
    return errors
