from collections import defaultdict
import heapq

from .constraints import require_int, validate_world_dimensions
from .navigation import exit_cell

CORRIDOR_VERSION = "0.9.0"

DIRS = ((1,0),(-1,0),(0,1),(0,-1))
OPPOSITE = {"N":"S","S":"N","E":"W","W":"E"}

BIOME_CORRIDOR = {
    "silt_marsh": "drainage_channel",
    "dark_forest": "old_road",
    "frozen_pass": "ridge_chain",
    "ruined_settlement": "old_road",
    "reformed_chapel": "pilgrim_route",
}

LANDMARK_CORRIDOR = {
    "printing_cathedral": "pilgrim_route",
    "printing_press_altar": "pilgrim_route",
    "silt_spire": "silt_vein",
    "nanolith_shrine": "silt_vein",
    "mask_cross": "old_road",
}

VISUAL_MATERIAL = {
    "old_road": "road",
    "pilgrim_route": "pilgrim_paving",
    "ridge_chain": "ridge_track",
    "silt_vein": "silt_trace",
    "drainage_channel": "drainage_trace",
}


def _manhattan(a,b):
    return abs(a[0]-b[0])+abs(a[1]-b[1])


def _neighbors(pos, cols, rows):
    x,y=pos
    for dx,dy in DIRS:
        q=(x+dx,y+dy)
        if 0 <= q[0] < cols and 0 <= q[1] < rows:
            yield q


def _sector_cost(ctx, corridor_type):
    fields=ctx.get("fields",{})
    moisture=float(fields.get("moisture",0.5))
    elevation=float(fields.get("elevation",0.5))
    settlement=float(fields.get("settlement",0.5))
    biome=ctx.get("primary_biome")
    transition=bool(ctx.get("transition"))

    if corridor_type=="old_road":
        cost=1.55 - settlement*0.75 + abs(elevation-0.45)*0.45 + moisture*0.10
    elif corridor_type=="pilgrim_route":
        civic=0.0 if biome in ("reformed_chapel","ruined_settlement") else 0.28
        cost=1.35 - settlement*0.55 + civic + abs(elevation-0.48)*0.25
    elif corridor_type=="ridge_chain":
        cost=1.55 - elevation*0.75 + moisture*0.15
        if biome=="frozen_pass": cost-=0.22
    elif corridor_type=="silt_vein":
        cost=1.55 - moisture*0.55 - (0.22 if biome=="silt_marsh" else 0.0) + elevation*0.10
    elif corridor_type=="drainage_channel":
        cost=1.60 - moisture*0.45 + elevation*0.60
        if biome=="silt_marsh": cost-=0.18
    else:
        cost=1.0
    if transition:
        cost += 0.08
    return max(0.12,round(cost,6))


def _shortest_path(start, goal, cols, rows, per_sector, corridor_type):
    if start==goal:
        return [start]
    heap=[(0.0,start[1],start[0],start)]
    cost={start:0.0}
    prev={}
    while heap:
        cur_cost,_,_,cur=heapq.heappop(heap)
        if cur==goal:
            break
        if cur_cost != cost.get(cur):
            continue
        for nxt in _neighbors(cur,cols,rows):
            step=_sector_cost(per_sector[nxt],corridor_type)
            nc=cur_cost+step
            old=cost.get(nxt)
            if old is None or nc < old-1e-12:
                cost[nxt]=nc
                prev[nxt]=cur
                heapq.heappush(heap,(nc,nxt[1],nxt[0],nxt))
            elif old is not None and abs(nc-old)<=1e-12:
                # Stable lexicographic predecessor tie-break.
                old_prev=prev.get(nxt)
                if old_prev is None or (cur[1],cur[0]) < (old_prev[1],old_prev[0]):
                    prev[nxt]=cur
    if goal not in cost:
        raise RuntimeError(f"no corridor path from {start} to {goal}")
    path=[goal]
    while path[-1]!=start:
        path.append(prev[path[-1]])
    path.reverse()
    return path


def _nearest(target, candidates):
    return min(candidates,key=lambda p:(_manhattan(target,p),p[1],p[0]))


def _farthest(target, candidates):
    return max(candidates,key=lambda p:(_manhattan(target,p),p[1],p[0]))


def _corridor_record(cid,kind,purpose,path,source,target,metadata=None):
    return {
        "id":cid,
        "kind":kind,
        "purpose":purpose,
        "source":list(source),
        "target":list(target),
        "sector_count":len(path),
        "path":[list(p) for p in path],
        "visual_material":VISUAL_MATERIAL[kind],
        "metadata":dict(metadata or {}),
    }


def plan_regional_corridors(seed, cols, rows, geography_plan, landmark_plan):
    seed=require_int("seed",seed)
    cols,rows=validate_world_dimensions(cols,rows)
    if geography_plan is None:
        return {
            "version":CORRIDOR_VERSION,
            "policy":{"enabled":False,"reason":"legacy geography disabled"},
            "corridors":[],
            "per_sector":{(x,y):[] for y in range(rows) for x in range(cols)},
        }

    per=geography_plan["per_sector"]
    regions=geography_plan["regions"]
    corridors=[]
    network=set()
    signatures=set()

    def add(kind,purpose,start,target,metadata=None):
        nonlocal corridors,network
        path=_shortest_path(start,target,cols,rows,per,kind)
        sig=(kind,tuple(path))
        rsig=(kind,tuple(reversed(path)))
        if len(path)<2 or sig in signatures or rsig in signatures:
            network.update(path)
            return None
        cid=f"corridor_{len(corridors)+1:02d}_{kind}"
        rec=_corridor_record(cid,kind,purpose,path,start,target,metadata)
        corridors.append(rec)
        signatures.add(sig)
        network.update(path)
        return rec

    start=(0,0)
    world_landmarks=[
        p for p in landmark_plan.get("placements",[])
        if p.get("scope")=="world"
    ]
    if world_landmarks:
        target=tuple(world_landmarks[0]["sector"])
    else:
        target=(cols-1,rows-1)
    if target==start and cols*rows>1:
        target=(cols-1,rows-1)
    add("old_road","world_spine",start,target,{"tier":"world"})

    # Every region gets a deterministic macro-to-network connector.
    members=defaultdict(list)
    for pos,ctx in per.items():
        members[int(ctx["region_id"])].append(pos)

    for region in sorted(regions,key=lambda r:int(r["id"])):
        rid=int(region["id"])
        center=tuple(region["center"])
        kind=BIOME_CORRIDOR.get(region["primary_biome"],"old_road")
        if network:
            target=_nearest(center,network)
        else:
            target=start
        if target==center:
            target=_farthest(center,members[rid])
        add(kind,"region_connector",center,target,{
            "tier":"regional",
            "region_id":rid,
            "primary_biome":region["primary_biome"],
        })

    # Regional/world landmarks that remain away from the corridor network get spurs.
    important=[
        p for p in landmark_plan.get("placements",[])
        if p.get("scope") in ("regional","world")
    ]
    for lm in sorted(important,key=lambda p:p["id"]):
        pos=tuple(lm["sector"])
        if pos in network:
            continue
        target=_nearest(pos,network) if network else start
        kind=LANDMARK_CORRIDOR.get(lm["kind"],"old_road")
        add(kind,"landmark_spur",pos,target,{
            "tier":lm.get("scope"),
            "landmark_id":lm["id"],
            "landmark_kind":lm["kind"],
        })

    per_sector={(x,y):[] for y in range(rows) for x in range(cols)}
    for corridor in corridors:
        path=[tuple(p) for p in corridor["path"]]
        for i,pos in enumerate(path):
            role="through"
            if i==0: role="source"
            if i==len(path)-1: role="target" if i else "source_target"
            per_sector[pos].append({
                "id":corridor["id"],
                "kind":corridor["kind"],
                "purpose":corridor["purpose"],
                "role":role,
                "index":i,
                "length":len(path),
                "visual_material":corridor["visual_material"],
            })

    return {
        "version":CORRIDOR_VERSION,
        "policy":{
            "enabled":True,
            "topology":"deterministic weighted 4-neighbor sector paths",
            "world_spine":"start sector to world landmark or opposite corner",
            "regional_connectors":"each region center connects to existing macro network",
            "landmark_spurs":"uncovered regional/world landmarks connect to macro network",
            "local_realization":"actual world link anchors joined by walkable local scene routes",
            "invariant":"global corridor topology fixed first; local scene realizes it without changing sector order",
        },
        "corridors":corridors,
        "per_sector":per_sector,
    }




def _walk_path(scene,start,goal):
    if start==goal:
        return [start]
    from collections import deque
    q=deque([start])
    prev={start:None}
    while q:
        cur=q.popleft()
        x,y=cur
        for dx,dy in DIRS:
            nxt=(x+dx,y+dy)
            if nxt in prev:
                continue
            nx,ny=nxt
            if not (0 <= nx < scene["width"] and 0 <= ny < scene["height"]):
                continue
            if scene["collision"][ny][nx] != "walk":
                continue
            prev[nxt]=cur
            if nxt==goal:
                q.clear()
                break
            q.append(nxt)
    if goal not in prev:
        return None
    path=[goal]
    while path[-1]!=start:
        path.append(prev[path[-1]])
    path.reverse()
    return path

def _edge_between(lookup,a,b):
    sec=lookup[a]
    for edge,link in sec["links"].items():
        if tuple(link["to"])==b:
            return edge,link
    raise KeyError(f"no world link between {a} and {b}")


def realize_regional_corridors(world, plan):
    lookup={(s["sx"],s["sy"]):s for s in world["sectors"]}
    local_records=[]

    for sec in world["sectors"]:
        sec["scene"]["regional_corridors"]=[]
        sec["corridors"]=list(plan["per_sector"].get((sec["sx"],sec["sy"]),[]))
        for link in sec["links"].values():
            link.setdefault("corridors",[])

    for corridor in plan["corridors"]:
        path=[tuple(p) for p in corridor["path"]]
        for i,pos in enumerate(path):
            sec=lookup[pos]
            scene=sec["scene"]
            anchors=[]
            neighbors=[]
            if i>0: neighbors.append(path[i-1])
            if i+1<len(path): neighbors.append(path[i+1])

            for neighbor in neighbors:
                edge,link=_edge_between(lookup,pos,neighbor)
                cell=exit_cell(scene,edge,link["coord"])
                anchors.append({
                    "edge":edge,
                    "coord":link["coord"],
                    "x":cell[0],"y":cell[1],
                    "to":list(neighbor),
                })
                tag={"id":corridor["id"],"kind":corridor["kind"]}
                if tag not in link["corridors"]:
                    link["corridors"].append(tag)

            if len(anchors)>=2:
                a=(anchors[0]["x"],anchors[0]["y"])
                b=(anchors[1]["x"],anchors[1]["y"])
            elif len(anchors)==1:
                a=(anchors[0]["x"],anchors[0]["y"])
                b=(scene["spawn"]["x"],scene["spawn"]["y"])
            else:
                a=b=(scene["spawn"]["x"],scene["spawn"]["y"])

            route=[] if a==b else _walk_path(scene,a,b)
            if route is None:
                raise RuntimeError(
                    f"could not realize {corridor['id']} inside sector {pos}"
                )

            record={
                "corridor_id":corridor["id"],
                "kind":corridor["kind"],
                "purpose":corridor["purpose"],
                "visual_material":corridor["visual_material"],
                "path_index":i,
                "anchors":anchors,
                "route_cells":[list(p) for p in route],
            }
            scene["regional_corridors"].append(record)
            local_records.append({"sector":list(pos),**record})

    public={
        "version":plan["version"],
        "policy":dict(plan["policy"]),
        "corridors":[dict(c) for c in plan["corridors"]],
        "local_realization":local_records,
        "summary":{
            "corridor_count":len(plan["corridors"]),
            "covered_sector_count":sum(1 for v in plan["per_sector"].values() if v),
            "local_segment_count":len(local_records),
            "kind_counts":dict(sorted(_kind_counts(plan["corridors"]).items())),
        },
    }
    world["regional_corridors"]=public
    return public


def _kind_counts(corridors):
    out=defaultdict(int)
    for c in corridors:
        out[c["kind"]]+=1
    return out
