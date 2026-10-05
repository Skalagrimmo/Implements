def validate_territory_graph(world):
    graph=world.get("territory_graph")
    topo=world.get("influence_topology")
    if not isinstance(graph,dict):
        return ["missing territory_graph"]
    if not isinstance(topo,dict):
        return ["missing influence_topology"]

    errors=[]
    topo_lookup={(s["sx"],s["sy"]):s for s in topo.get("sectors",[])}
    territories=graph.get("territories",[])
    territory_ids={t.get("id") for t in territories}
    front_ids={f.get("id") for f in topo.get("fronts",[])}

    occupied={}
    for t in territories:
        tid=t.get("id")
        alignment=t.get("alignment")
        cells=[tuple(x) for x in t.get("sectors",[])]
        if t.get("sector_count")!=len(cells):
            errors.append(f"{tid} sector_count mismatch")
        for pos in cells:
            if pos in occupied:
                errors.append(f"sector {pos} belongs to multiple territories")
            occupied[pos]=tid
            s=topo_lookup.get(pos)
            if not s:
                errors.append(f"{tid} references missing sector {pos}")
                continue
            if s.get("status")!="dominated":
                errors.append(f"{tid} includes non-dominated sector {pos}")
            if s.get("alignment")!=alignment:
                errors.append(f"{tid} alignment mismatch at {pos}")

    expected={pos for pos,s in topo_lookup.items() if s.get("status")=="dominated"}
    if set(occupied)!=expected:
        errors.append("territories do not partition all dominated sectors exactly")

    site_ids=set()
    for site in graph.get("front_sites",[]):
        sid=site.get("id")
        if sid in site_ids:
            errors.append(f"duplicate front site id {sid}")
        site_ids.add(sid)
        if site.get("front_id") not in front_ids:
            errors.append(f"{sid} references unknown front")
        a=tuple(site.get("sector",[])); b=tuple(site.get("neighbor_sector",[]))
        if len(a)!=2 or len(b)!=2 or abs(a[0]-b[0])+abs(a[1]-b[1])!=1:
            errors.append(f"{sid} endpoints are not adjacent")

    event_ids=set()
    for e in graph.get("event_seeds",[]):
        eid=e.get("id")
        if eid in event_ids:
            errors.append(f"duplicate event seed id {eid}")
        event_ids.add(eid)
        if "front_id" in e and e["front_id"] not in front_ids:
            errors.append(f"{eid} references unknown front")
        if "territory_id" in e and e["territory_id"] not in territory_ids:
            errors.append(f"{eid} references unknown territory")

    return errors
