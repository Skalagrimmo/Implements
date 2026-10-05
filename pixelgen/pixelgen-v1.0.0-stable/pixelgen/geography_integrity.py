from collections import defaultdict, deque

def validate_geography(world):
    errors=[]
    geo=world.get("geography")
    if not isinstance(geo,dict):
        return ["missing geography"]
    regions=geo.get("regions",[])
    if not regions:
        return ["geography has no regions"]

    sectors={(s["sx"],s["sy"]):s for s in world.get("sectors",[])}
    gsectors={(s["sx"],s["sy"]):s for s in geo.get("sectors",[])}
    if set(sectors)!=set(gsectors):
        errors.append("geography sector map does not match world sectors")

    ids={r["id"] for r in regions}
    members=defaultdict(set)
    for pos,g in gsectors.items():
        rid=g.get("region_id")
        if rid not in ids:
            errors.append(f"sector {pos} references unknown region {rid}")
            continue
        members[rid].add(pos)
        if sectors.get(pos,{}).get("biome") != g.get("primary_biome"):
            errors.append(f"sector {pos} biome disagrees with geography")
        scene_geo=sectors.get(pos,{}).get("scene",{}).get("geography")
        if scene_geo and scene_geo.get("subbiome") != g.get("subbiome"):
            errors.append(f"sector {pos} scene geography disagrees with world geography")

    # Every region must form one 4-neighbor connected mass.
    for r in regions:
        cells=members[r["id"]]
        if not cells:
            errors.append(f"region {r['id']} is empty")
            continue
        start=next(iter(cells))
        seen={start}
        q=deque([start])
        while q:
            x,y=q.popleft()
            for n in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if n in cells and n not in seen:
                    seen.add(n); q.append(n)
        if seen != cells:
            errors.append(f"region {r['id']} is geographically fragmented")
        if tuple(r["center"]) not in cells:
            errors.append(f"region {r['id']} does not own its center")

    # Transition flags must correspond to an actual cross-region edge.
    for pos,g in gsectors.items():
        rid=g["region_id"]
        actual=[]
        x,y=pos
        for edge,(dx,dy) in {"N":(0,-1),"E":(1,0),"S":(0,1),"W":(-1,0)}.items():
            n=(x+dx,y+dy)
            if n in gsectors and gsectors[n]["region_id"]!=rid:
                actual.append(edge)
        declared=sorted(e["edge"] for e in g.get("transition_edges",[]))
        if sorted(actual)!=declared:
            errors.append(f"sector {pos} transition edges disagree with neighbors")

    return errors
