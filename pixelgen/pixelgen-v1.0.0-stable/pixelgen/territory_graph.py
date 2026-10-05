from collections import defaultdict, deque

TERRITORY_VERSION="0.7.5"


def _neighbors4(pos,cols,rows):
    x,y=pos
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
        q=(x+dx,y+dy)
        if 0 <= q[0] < cols and 0 <= q[1] < rows:
            yield q


def _sector_lookup(topology):
    return {(s["sx"],s["sy"]):s for s in topology.get("sectors",[])}


def _build_territories(topology,cols,rows):
    lookup=_sector_lookup(topology)
    unseen={
        pos for pos,s in lookup.items()
        if s.get("status")=="dominated" and s.get("alignment") is not None
    }
    territories=[]
    tid=0

    while unseen:
        start=min(unseen)
        alignment=lookup[start]["alignment"]
        q=deque([start])
        unseen.remove(start)
        cells=[]
        strengths=[]
        front_ids=set()

        while q:
            pos=q.popleft()
            s=lookup[pos]
            cells.append(pos)
            strengths.append(float(s.get("top_strength",0.0)))
            front_ids.update(s.get("front_ids",[]))
            for n in _neighbors4(pos,cols,rows):
                if n in unseen and lookup[n].get("alignment")==alignment and lookup[n].get("status")=="dominated":
                    unseen.remove(n)
                    q.append(n)

        cx=sum(x for x,y in cells)/len(cells)
        cy=sum(y for x,y in cells)/len(cells)
        center=min(cells,key=lambda p:(abs(p[0]-cx)+abs(p[1]-cy),p[1],p[0]))
        territories.append({
            "id":f"territory_{tid}",
            "alignment":alignment,
            "sector_count":len(cells),
            "sectors":[list(p) for p in sorted(cells)],
            "center":[center[0],center[1]],
            "mean_strength":round(sum(strengths)/len(strengths),4),
            "max_strength":round(max(strengths),4),
            "front_ids":sorted(front_ids),
        })
        tid+=1

    return territories


def _territory_index(territories):
    out={}
    for t in territories:
        for cell in t["sectors"]:
            out[tuple(cell)]=t["id"]
    return out


def _front_links(topology,territories):
    tindex=_territory_index(territories)
    links=[]
    for front in topology.get("fronts",[]):
        ids=set()
        for edge in front.get("edges",[]):
            for pos in (tuple(edge["a"]),tuple(edge["b"])):
                tid=tindex.get(pos)
                if tid:
                    ids.add(tid)
        links.append({
            "front_id":front["id"],
            "pair":list(front.get("pair",[])),
            "territory_ids":sorted(ids),
            "mean_pressure":front.get("mean_pressure",0.0),
            "max_pressure":front.get("max_pressure",0.0),
            "edge_count":front.get("edge_count",0),
        })
    return links


def _front_sites(topology):
    sites=[]
    for sid,front in enumerate(topology.get("fronts",[])):
        edges=list(front.get("edges",[]))
        if not edges:
            continue
        edge=sorted(
            edges,
            key=lambda e:(
                -float(e.get("pressure",0.0)),
                tuple(e.get("a",[])),
                tuple(e.get("b",[])),
            )
        )[0]
        a=tuple(edge["a"]); b=tuple(edge["b"])
        site=min(a,b)
        other=b if site==a else a
        sites.append({
            "id":f"front_site_{sid}",
            "front_id":front["id"],
            "sector":[site[0],site[1]],
            "neighbor_sector":[other[0],other[1]],
            "pair":list(front.get("pair",[])),
            "pressure":edge.get("pressure",0.0),
            "front_edge_count":front.get("edge_count",0),
        })
    return sites


def _event_seeds(topology,territories,front_sites):
    events=[]
    eid=0

    for site in front_sites:
        pressure=float(site.get("pressure",0.0))
        severity="high" if pressure>=0.60 else "medium" if pressure>=0.35 else "low"
        base={
            "sector":list(site["sector"]),
            "front_id":site["front_id"],
            "pair":list(site.get("pair",[])),
            "pressure":round(pressure,4),
            "severity":severity,
        }
        for kind in ("front_observation","front_rumor","border_encounter"):
            events.append({"id":f"event_seed_{eid}","kind":kind,**base})
            eid+=1

    for territory in territories:
        if territory["sector_count"] < 2:
            continue
        strength=float(territory["mean_strength"])
        severity="high" if strength>=0.75 else "medium" if strength>=0.45 else "low"
        events.append({
            "id":f"event_seed_{eid}",
            "kind":"territory_presence",
            "territory_id":territory["id"],
            "alignment":territory["alignment"],
            "sector":list(territory["center"]),
            "strength":round(strength,4),
            "severity":severity,
        })
        eid+=1

    for s in topology.get("sectors",[]):
        if s.get("status")!="contested":
            continue
        events.append({
            "id":f"event_seed_{eid}",
            "kind":"contested_observation",
            "sector":[s["sx"],s["sy"]],
            "pair":list(s.get("contest_pair",[])),
            "top_strength":s.get("top_strength",0.0),
            "dominance_margin":s.get("dominance_margin",0.0),
            "severity":"medium",
        })
        eid+=1

    return events


def build_territory_graph(topology,cols,rows):
    territories=_build_territories(topology,cols,rows)
    front_links=_front_links(topology,territories)
    front_sites=_front_sites(topology)
    event_seeds=_event_seeds(topology,territories,front_sites)

    alignment_counts=defaultdict(int)
    for t in territories:
        alignment_counts[t["alignment"]]+=1

    event_kind_counts=defaultdict(int)
    for e in event_seeds:
        event_kind_counts[e["kind"]]+=1

    return {
        "version":TERRITORY_VERSION,
        "policy":{
            "territory_rule":"4-neighbor connected component of dominated sectors sharing alignment",
            "front_site_rule":"highest-pressure edge representative per front",
            "event_seed_rule":"deterministic semantic hooks; no runtime mutation is applied by PixelGen",
        },
        "territories":territories,
        "front_links":front_links,
        "front_sites":front_sites,
        "event_seeds":event_seeds,
        "summary":{
            "territory_count":len(territories),
            "alignment_territory_counts":dict(sorted(alignment_counts.items())),
            "front_site_count":len(front_sites),
            "event_seed_count":len(event_seeds),
            "event_kind_counts":dict(sorted(event_kind_counts.items())),
        },
    }


def territory_context_for_sector(graph,pos):
    pos=tuple(pos)
    territory_id=None
    alignment=None
    for t in graph.get("territories",[]):
        if list(pos) in t.get("sectors",[]):
            territory_id=t["id"]
            alignment=t.get("alignment")
            break

    front_site_ids=[
        s["id"] for s in graph.get("front_sites",[])
        if tuple(s.get("sector",[]))==pos or tuple(s.get("neighbor_sector",[]))==pos
    ]
    event_seed_ids=[
        e["id"] for e in graph.get("event_seeds",[])
        if tuple(e.get("sector",[]))==pos
    ]
    return {
        "territory_id":territory_id,
        "alignment":alignment,
        "front_site_ids":sorted(front_site_ids),
        "event_seed_ids":sorted(event_seed_ids),
    }
