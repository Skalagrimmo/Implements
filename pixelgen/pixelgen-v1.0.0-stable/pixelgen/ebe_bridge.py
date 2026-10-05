EBE_BRIDGE_VERSION="0.7.5"


def build_ebe_seed_bundle(world):
    graph=world.get("territory_graph",{})
    topo=world.get("influence_topology",{})

    entities=[]
    for t in graph.get("territories",[]):
        entities.append({
            "id":t["id"],
            "entity_type":"territory",
            "alignment":t.get("alignment"),
            "center":list(t.get("center",[])),
            "sector_count":t.get("sector_count",0),
            "mean_strength":t.get("mean_strength",0.0),
        })
    for f in topo.get("fronts",[]):
        entities.append({
            "id":f["id"],
            "entity_type":"influence_front",
            "pair":list(f.get("pair",[])),
            "sector_count":f.get("sector_count",0),
            "mean_pressure":f.get("mean_pressure",0.0),
        })

    events=[]
    for seed in graph.get("event_seeds",[]):
        payload={k:v for k,v in seed.items() if k not in ("id","kind")}
        events.append({
            "id":seed["id"],
            "event_type":seed["kind"],
            "payload":payload,
            "state":"seeded",
            "observability":"local_or_transmitted",
        })

    return {
        "version":EBE_BRIDGE_VERSION,
        "source":{
            "generator":world.get("generator",{}),
            "world_seed":world.get("seed"),
            "dimensions":[world.get("cols"),world.get("rows")],
        },
        "contract":{
            "pixelgen_role":"generate deterministic semantic entities and event seeds",
            "ebe_role":"observe, remember, interpret, propagate and react at runtime",
            "runtime_mutation":"not performed by PixelGen",
        },
        "entities":entities,
        "events":events,
    }
