from collections import deque
from .navigation import exit_cell


def _lookup(world):
    return {(s["sx"],s["sy"]):s for s in world.get("sectors",[])}


def _adjacent(a,b):
    return abs(a[0]-b[0])+abs(a[1]-b[1])==1


def _walk_connected(scene,start,goal):
    if start==goal:
        return True
    q=deque([start]); seen={start}
    while q:
        x,y=q.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            n=(x+dx,y+dy)
            if n in seen: continue
            nx,ny=n
            if not (0<=nx<scene["width"] and 0<=ny<scene["height"]):
                continue
            if scene["collision"][ny][nx] != "walk":
                continue
            if n==goal: return True
            seen.add(n); q.append(n)
    return False


def validate_regional_corridors(world):
    data=world.get("regional_corridors")
    if not isinstance(data,dict):
        return ["missing regional_corridors"]
    errors=[]
    lookup=_lookup(world)
    ids=set()
    expected_local=0
    sector_membership={k:set() for k in lookup}

    for corridor in data.get("corridors",[]):
        cid=corridor.get("id")
        if not cid or cid in ids:
            errors.append(f"duplicate/invalid corridor id {cid}")
            continue
        ids.add(cid)
        path=[tuple(p) for p in corridor.get("path",[])]
        if len(path)<2:
            errors.append(f"{cid}: corridor path shorter than two sectors")
            continue
        if corridor.get("sector_count")!=len(path):
            errors.append(f"{cid}: sector_count mismatch")
        if tuple(corridor.get("source",[]))!=path[0]:
            errors.append(f"{cid}: source mismatch")
        if tuple(corridor.get("target",[]))!=path[-1]:
            errors.append(f"{cid}: target mismatch")
        if len(set(path))!=len(path):
            errors.append(f"{cid}: corridor path self-intersects/repeats sector")
        for a,b in zip(path,path[1:]):
            if not _adjacent(a,b):
                errors.append(f"{cid}: non-adjacent step {a}->{b}")
                continue
            if a not in lookup or b not in lookup:
                errors.append(f"{cid}: path outside world")
                continue
            if not any(tuple(l["to"])==b for l in lookup[a]["links"].values()):
                errors.append(f"{cid}: no physical world link {a}->{b}")
        for pos in path:
            if pos in sector_membership:
                sector_membership[pos].add(cid)
        expected_local += len(path)

    local=data.get("local_realization",[])
    if len(local)!=expected_local:
        errors.append("local corridor realization count mismatch")

    local_keys=set()
    for rec in local:
        pos=tuple(rec.get("sector",[])); cid=rec.get("corridor_id")
        key=(pos,cid)
        if key in local_keys:
            errors.append(f"duplicate local corridor segment {key}")
        local_keys.add(key)
        sec=lookup.get(pos)
        if not sec:
            errors.append(f"local corridor {cid} references missing sector {pos}")
            continue
        scene=sec["scene"]
        anchors=rec.get("anchors",[])
        for anchor in anchors:
            edge=anchor.get("edge")
            link=sec["links"].get(edge)
            if not link:
                errors.append(f"{cid} {pos}: missing link for anchor {edge}")
                continue
            expected=exit_cell(scene,edge,link["coord"])
            actual=(anchor.get("x"),anchor.get("y"))
            if actual!=expected:
                errors.append(f"{cid} {pos}: anchor cell mismatch")
        route=[tuple(p) for p in rec.get("route_cells",[])]
        for x,y in route:
            if not (0<=x<scene["width"] and 0<=y<scene["height"]):
                errors.append(f"{cid} {pos}: local route out of bounds")
                break
            if scene["collision"][y][x] != "walk":
                errors.append(f"{cid} {pos}: local route not walkable")
                break
        if len(anchors)>=2:
            a=(anchors[0]["x"],anchors[0]["y"])
            b=(anchors[1]["x"],anchors[1]["y"])
            if not _walk_connected(scene,a,b):
                errors.append(f"{cid} {pos}: local anchors not connected")

    for pos,sec in lookup.items():
        declared={c.get("id") for c in sec.get("corridors",[])}
        if declared != sector_membership[pos]:
            errors.append(f"{pos}: sector corridor membership mismatch")

    summary=data.get("summary",{})
    if summary.get("corridor_count")!=len(data.get("corridors",[])):
        errors.append("corridor summary count mismatch")
    covered=sum(1 for ids_here in sector_membership.values() if ids_here)
    if summary.get("covered_sector_count")!=covered:
        errors.append("corridor covered-sector summary mismatch")
    return errors
