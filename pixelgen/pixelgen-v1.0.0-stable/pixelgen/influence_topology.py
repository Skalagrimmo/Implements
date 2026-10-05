from collections import defaultdict, deque

TOPOLOGY_VERSION="0.7.4"

NEUTRAL_THRESHOLD=0.28
CONTEST_MIN_SECONDARY=0.12
CONTEST_MARGIN=0.12

CHANNELS=("print_civic","silt_contamination","nano_signal")


def _rank_channels(channels):
    return sorted(
        ((str(k),float(v)) for k,v in channels.items()),
        key=lambda kv:(-kv[1],kv[0]),
    )


def classify_influence(channels):
    ranked=_rank_channels(channels)
    if not ranked:
        return {
            "status":"neutral",
            "alignment":None,
            "top_channel":None,
            "top_strength":0.0,
            "second_channel":None,
            "second_strength":0.0,
            "dominance_margin":0.0,
            "contest_pair":[],
        }

    top_channel,top_strength=ranked[0]
    second_channel,second_strength=ranked[1] if len(ranked)>1 else (None,0.0)
    margin=round(top_strength-second_strength,4)

    if top_strength < NEUTRAL_THRESHOLD:
        status="neutral"
        alignment=None
        contest_pair=[]
    elif (
        second_channel is not None
        and second_strength >= CONTEST_MIN_SECONDARY
        and margin <= CONTEST_MARGIN
    ):
        status="contested"
        alignment=top_channel
        contest_pair=sorted((top_channel,second_channel))
    else:
        status="dominated"
        alignment=top_channel
        contest_pair=[]

    return {
        "status":status,
        "alignment":alignment,
        "top_channel":top_channel,
        "top_strength":round(top_strength,4),
        "second_channel":second_channel,
        "second_strength":round(second_strength,4),
        "dominance_margin":margin,
        "contest_pair":contest_pair,
    }


def _edge_pressure(a,b,pair):
    # Pressure measures how strongly both opposing channels are represented
    # across the two sectors on this boundary.
    if len(pair)!=2:
        return 0.0
    p0,p1=pair
    a0=float(a.get("channels",{}).get(p0,0.0))
    a1=float(a.get("channels",{}).get(p1,0.0))
    b0=float(b.get("channels",{}).get(p0,0.0))
    b1=float(b.get("channels",{}).get(p1,0.0))
    cross=min(max(a0,b0),max(a1,b1))
    return round(max(0.0,min(1.75,cross)),4)


def _boundary_edges(per_sector,cols,rows):
    edges=[]
    for y in range(rows):
        for x in range(cols):
            a=per_sector[(x,y)]
            for dx,dy,edge_name in ((1,0,"E"),(0,1,"S")):
                q=(x+dx,y+dy)
                if q not in per_sector:
                    continue
                b=per_sector[q]
                aa=a["topology"]["alignment"]
                bb=b["topology"]["alignment"]
                if aa is None or bb is None or aa==bb:
                    continue
                pair=sorted((aa,bb))
                edges.append({
                    "a":[x,y],
                    "b":[q[0],q[1]],
                    "edge":edge_name,
                    "pair":pair,
                    "pressure":_edge_pressure(a,b,pair),
                })
    return edges


def _edge_components(edges):
    by_pair=defaultdict(list)
    for i,e in enumerate(edges):
        by_pair[tuple(e["pair"])].append((i,e))

    fronts=[]
    front_index=0

    for pair,items in sorted(by_pair.items()):
        edge_map={i:e for i,e in items}
        cell_to_edges=defaultdict(set)
        for i,e in items:
            cell_to_edges[tuple(e["a"])].add(i)
            cell_to_edges[tuple(e["b"])].add(i)

        unseen=set(edge_map)
        while unseen:
            start=min(unseen)
            unseen.remove(start)
            q=deque([start])
            component=[]

            while q:
                ei=q.popleft()
                e=edge_map[ei]
                component.append(e)
                cells=(tuple(e["a"]),tuple(e["b"]))
                neighbors=set()
                for c in cells:
                    neighbors |= cell_to_edges[c]
                for ni in sorted(neighbors):
                    if ni in unseen:
                        unseen.remove(ni)
                        q.append(ni)

            sectors=sorted({
                tuple(cell)
                for e in component
                for cell in (e["a"],e["b"])
            })
            pressures=[e["pressure"] for e in component]
            fronts.append({
                "id":f"front_{front_index}",
                "pair":list(pair),
                "edge_count":len(component),
                "sector_count":len(sectors),
                "sectors":[list(x) for x in sectors],
                "mean_pressure":round(sum(pressures)/len(pressures),4),
                "max_pressure":round(max(pressures),4),
                "edges":component,
            })
            front_index+=1

    return fronts


def build_influence_topology(influence_plan,cols,rows):
    per_sector={}
    for y in range(rows):
        for x in range(cols):
            raw=influence_plan["per_sector"][(x,y)]
            per_sector[(x,y)]={
                **raw,
                "topology":classify_influence(raw.get("channels",{})),
            }

    edges=_boundary_edges(per_sector,cols,rows)
    fronts=_edge_components(edges)

    front_ids_by_sector=defaultdict(list)
    front_pressure_by_sector=defaultdict(float)
    for front in fronts:
        for cell in front["sectors"]:
            pos=tuple(cell)
            front_ids_by_sector[pos].append(front["id"])
            front_pressure_by_sector[pos]=max(
                front_pressure_by_sector[pos],
                float(front["max_pressure"]),
            )

    for pos,item in per_sector.items():
        topo=item["topology"]
        topo["front_ids"]=sorted(front_ids_by_sector.get(pos,[]))
        topo["front_pressure"]=round(front_pressure_by_sector.get(pos,0.0),4)

    status_counts=defaultdict(int)
    for item in per_sector.values():
        status_counts[item["topology"]["status"]]+=1

    pair_counts=defaultdict(int)
    for front in fronts:
        pair_counts[" + ".join(front["pair"])]+=1

    return {
        "version":TOPOLOGY_VERSION,
        "policy":{
            "neutral_threshold":NEUTRAL_THRESHOLD,
            "contest_min_secondary":CONTEST_MIN_SECONDARY,
            "contest_margin":CONTEST_MARGIN,
            "front_rule":"4-neighbor boundary between non-neutral sectors with different alignments",
            "front_grouping":"connected boundary edges sharing the same unordered channel pair",
        },
        "per_sector":per_sector,
        "boundary_edges":edges,
        "fronts":fronts,
        "summary":{
            "status_counts":dict(sorted(status_counts.items())),
            "front_count":len(fronts),
            "front_pair_counts":dict(sorted(pair_counts.items())),
        },
    }


def public_topology(topology_plan,cols,rows):
    return {
        "version":topology_plan["version"],
        "policy":topology_plan["policy"],
        "summary":topology_plan["summary"],
        "sectors":[
            {
                "sx":x,
                "sy":y,
                **topology_plan["per_sector"][(x,y)]["topology"],
            }
            for y in range(rows)
            for x in range(cols)
        ],
        "boundary_edges":topology_plan["boundary_edges"],
        "fronts":topology_plan["fronts"],
    }


def apply_topology_to_influence(influence,topology):
    out=dict(influence or {})
    out["topology"]={
        "status":topology.get("status"),
        "alignment":topology.get("alignment"),
        "top_channel":topology.get("top_channel"),
        "top_strength":topology.get("top_strength"),
        "second_channel":topology.get("second_channel"),
        "second_strength":topology.get("second_strength"),
        "dominance_margin":topology.get("dominance_margin"),
        "contest_pair":list(topology.get("contest_pair",[])),
        "front_ids":list(topology.get("front_ids",[])),
        "front_pressure":topology.get("front_pressure",0.0),
    }
    return out
