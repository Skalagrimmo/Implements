from .influence_topology import classify_influence

def validate_influence_topology(world):
    topo=world.get("influence_topology")
    inf=world.get("regional_influence")
    if not isinstance(topo,dict):
        return ["missing influence_topology"]
    if not isinstance(inf,dict):
        return ["missing regional_influence"]

    errors=[]
    sectors={(s["sx"],s["sy"]):s for s in topo.get("sectors",[])}
    inf_sectors={(s["sx"],s["sy"]):s for s in inf.get("sectors",[])}
    world_sectors={(s["sx"],s["sy"]):s for s in world.get("sectors",[])}

    if set(sectors)!=set(inf_sectors):
        errors.append("topology sector map does not match influence sector map")
    if set(sectors)!=set(world_sectors):
        errors.append("topology sector map does not match world sector map")

    front_ids={f.get("id") for f in topo.get("fronts",[])}
    seen_front_ids=set()

    for pos,item in sectors.items():
        raw=inf_sectors.get(pos,{})
        expected=classify_influence(raw.get("channels",{}))
        for key in (
            "status","alignment","top_channel","top_strength",
            "second_channel","second_strength","dominance_margin","contest_pair",
        ):
            if item.get(key)!=expected.get(key):
                errors.append(f"sector {pos} topology classification mismatch for {key}")

        for fid in item.get("front_ids",[]):
            if fid not in front_ids:
                errors.append(f"sector {pos} references unknown front {fid}")

        scene_topo=(
            world_sectors.get(pos,{})
            .get("scene",{})
            .get("geography",{})
            .get("regional_influence",{})
            .get("topology")
        )
        if scene_topo is not None:
            if scene_topo.get("status")!=item.get("status"):
                errors.append(f"sector {pos} scene topology status mismatch")
            if scene_topo.get("front_ids")!=item.get("front_ids"):
                errors.append(f"sector {pos} scene topology front ids mismatch")

    for front in topo.get("fronts",[]):
        fid=front.get("id")
        if fid in seen_front_ids:
            errors.append(f"duplicate front id {fid}")
        seen_front_ids.add(fid)

        pair=front.get("pair",[])
        if len(pair)!=2 or pair[0]==pair[1]:
            errors.append(f"front {fid} has invalid channel pair")
        if front.get("edge_count")!=len(front.get("edges",[])):
            errors.append(f"front {fid} edge_count mismatch")
        sectors_set={tuple(x) for x in front.get("sectors",[])}
        for edge in front.get("edges",[]):
            a=tuple(edge.get("a",[]))
            b=tuple(edge.get("b",[]))
            if abs(a[0]-b[0])+abs(a[1]-b[1])!=1:
                errors.append(f"front {fid} has non-adjacent boundary edge")
            if a not in sectors_set or b not in sectors_set:
                errors.append(f"front {fid} edge references sector outside front")
            aa=sectors.get(a,{}).get("alignment")
            bb=sectors.get(b,{}).get("alignment")
            if sorted((aa,bb))!=sorted(pair):
                errors.append(f"front {fid} edge alignment mismatch")

    return errors
