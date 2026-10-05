from collections import Counter
from .fingerprint import world_fingerprint
from .structural_report import analyze_structural_grammar

def inspect_world(world):
    sectors=world.get("sectors",[])
    biomes=Counter()
    objects=Counter()
    scopes=Counter()
    encounters=Counter()
    finds=Counter()
    gates=Counter()
    abilities=Counter()

    for s in sectors:
        biomes[s.get("biome","?")] += 1
        scene=s.get("scene",{})
        for raw in scene.get("objects",[]):
            o=raw.to_dict() if hasattr(raw,"to_dict") else raw
            objects[o.get("kind","?")] += 1
        for lm in scene.get("landmarks",{}).values():
            scopes[lm.get("scope","?")] += 1
        for e in scene.get("encounters",[]):
            encounters[e.get("kind",e.get("enemy","?"))] += 1
        for f in scene.get("finds",[]):
            finds[f.get("kind",f.get("item","?"))] += 1
        for g in scene.get("gates",[]):
            gates[g.get("state","?")] += 1
        for a in scene.get("ability_pickups",[]):
            abilities[a.get("ability","?")] += 1

    gameplay=world.get("gameplay") or {}
    geography=world.get("geography") or {}
    subbiomes=Counter(
        s.get("subbiome","?")
        for s in geography.get("sectors",[])
        if s.get("subbiome")
    )
    zones=Counter(
        s.get("zone","?")
        for s in geography.get("sectors",[])
        if s.get("zone")
    )
    visual=world.get("visual_quality") or {}
    vm=visual.get("metrics",{})
    structural=analyze_structural_grammar(world)
    influence=world.get("regional_influence") or {}
    influence_sectors=influence.get("sectors",[])
    topology=world.get("influence_topology") or {}
    topology_sectors=topology.get("sectors",[])
    topology_status=Counter(
        s.get("status","?")
        for s in topology_sectors
    )
    topology_pairs=Counter(
        " + ".join(f.get("pair",[]))
        for f in topology.get("fronts",[])
        if f.get("pair")
    )
    territory_graph=world.get("territory_graph") or {}
    corridors=world.get("regional_corridors") or {}
    corridor_kinds=Counter(
        c.get("kind","?") for c in corridors.get("corridors",[])
    )
    territory_alignments=Counter(
        t.get("alignment","?")
        for t in territory_graph.get("territories",[])
    )
    event_kinds=Counter(
        e.get("kind","?")
        for e in territory_graph.get("event_seeds",[])
    )
    dominant_counts=Counter(
        s.get("dominant_channel") or "none"
        for s in influence_sectors
    )
    grammar_counts=Counter(
        s.get("scene",{}).get("structural_grammar",{}).get("grammar_id","?")
        for s in sectors
    )

    return {
        "name":world.get("name"),
        "generator":world.get("generator"),
        "fingerprint":world_fingerprint(world),
        "dimensions":{
            "cols":world.get("cols"),
            "rows":world.get("rows"),
            "sectors":len(sectors),
            "sector_width":world.get("sector_width"),
            "sector_height":world.get("sector_height"),
        },
        "biomes":dict(sorted(biomes.items())),
        "geography":{
            "version":geography.get("version"),
            "regions":len(geography.get("regions",[])),
            "transitions":len(geography.get("transitions",[])),
            "subbiomes":dict(sorted(subbiomes.items())),
            "zones":dict(sorted(zones.items())),
        },
        "objects":{
            "total":sum(objects.values()),
            "by_kind":dict(sorted(objects.items())),
        },
        "landmarks":{
            "total":sum(scopes.values()),
            "by_scope":dict(sorted(scopes.items())),
        },
        "encounters":{
            "total":sum(encounters.values()),
            "by_kind":dict(sorted(encounters.items())),
        },
        "finds":{
            "total":sum(finds.values()),
            "by_kind":dict(sorted(finds.items())),
        },
        "navigation":{
            "gates_by_state":dict(sorted(gates.items())),
            "abilities":dict(sorted(abilities.items())),
            "main_path_nodes":len(gameplay.get("main_path",[])),
            "final_sector":gameplay.get("final_sector"),
        },
        "visual":{
            "score":vm.get("visual_repetition_score"),
            "grade":vm.get("visual_grade"),
            "quadrant_entropy":vm.get("quadrant_entropy"),
        },
        "influence":{
            "version":influence.get("version"),
            "sources":len(influence.get("sources",[])),
            "dominant_channels":dict(sorted(dominant_counts.items())),
            "affected_sectors":sum(
                1 for s in influence_sectors
                if s.get("dominant_channel") is not None
            ),
        },
        "topology":{
            "version":topology.get("version"),
            "status_counts":dict(sorted(topology_status.items())),
            "front_count":len(topology.get("fronts",[])),
            "front_pair_counts":dict(sorted(topology_pairs.items())),
            "boundary_edges":len(topology.get("boundary_edges",[])),
            "neutral_sectors":topology_status.get("neutral",0),
            "contested_sectors":topology_status.get("contested",0),
            "dominated_sectors":topology_status.get("dominated",0),
        },
        "regional_corridors":{
            "version":corridors.get("version"),
            "count":len(corridors.get("corridors",[])),
            "covered_sectors":corridors.get("summary",{}).get("covered_sector_count",0),
            "local_segments":corridors.get("summary",{}).get("local_segment_count",0),
            "by_kind":dict(sorted(corridor_kinds.items())),
        },
        "territory_graph":{
            "version":territory_graph.get("version"),
            "territories":len(territory_graph.get("territories",[])),
            "by_alignment":dict(sorted(territory_alignments.items())),
            "front_sites":len(territory_graph.get("front_sites",[])),
            "event_seeds":len(territory_graph.get("event_seeds",[])),
            "event_kinds":dict(sorted(event_kinds.items())),
        },
        "structural":{
            "version":structural.get("version"),
            "status":structural.get("status"),
            "score":structural.get("score"),
            "distinct_grammar_ids":structural.get("distinct_grammar_ids"),
            "distinct_path_visuals":structural.get("distinct_path_visuals"),
            "grammar_counts":dict(sorted(grammar_counts.items())),
            "distinct_variant_ids":structural.get("distinct_variant_ids"),
            "ecotone_adapters":structural.get("ecotone_adapters"),
            "biomes":structural.get("biomes",{}),
        },
    }

def inspection_text(info):
    d=info["dimensions"]
    lines=[
        f"World: {info.get('name') or '(unnamed)'}",
        f"Fingerprint: {info['fingerprint']}",
        f"Size: {d.get('cols')}x{d.get('rows')} sectors ({d.get('sectors')} total)",
        "Biomes: " + ", ".join(f"{k}={v}" for k,v in info["biomes"].items()),
        f"Regions: {info['geography']['regions']}  transitions: {info['geography']['transitions']}",
        "Zones: " + ", ".join(f"{k}={v}" for k,v in info["geography"]["zones"].items()),
        f"Objects: {info['objects']['total']}",
        f"Landmarks: {info['landmarks']['total']} " +
            ", ".join(f"{k}={v}" for k,v in info["landmarks"]["by_scope"].items()),
        f"Encounters: {info['encounters']['total']}",
        f"Finds: {info['finds']['total']}",
        f"Main path nodes: {info['navigation']['main_path_nodes']}",
        f"Structural grammars: {info['structural']['distinct_grammar_ids']}  score: {info['structural']['score']}/100",
        f"Subbiome variants: {info['structural']['distinct_variant_ids']}  ecotone adapters: {info['structural']['ecotone_adapters']}",
        f"Influence sources: {info['influence']['sources']}  affected sectors: {info['influence']['affected_sectors']}",
        "Influence: " + ", ".join(f"{k}={v}" for k,v in info["influence"]["dominant_channels"].items()),
        f"Topology: neutral={info['topology']['neutral_sectors']} contested={info['topology']['contested_sectors']} dominated={info['topology']['dominated_sectors']}",
        f"Influence fronts: {info['topology']['front_count']}  boundary edges: {info['topology']['boundary_edges']}",
        f"Territories: {info['territory_graph']['territories']}  front sites: {info['territory_graph']['front_sites']}",
        f"Event seeds: {info['territory_graph']['event_seeds']}  " + ", ".join(f"{k}={v}" for k,v in info["territory_graph"]["event_kinds"].items()),
        f"Regional corridors: {info['regional_corridors']['count']}  coverage: {info['regional_corridors']['covered_sectors']}/{d.get('sectors')}",
        "Corridor kinds: " + ", ".join(f"{k}={v}" for k,v in info["regional_corridors"]["by_kind"].items()),
        "Grammar counts: " + ", ".join(f"{k}={v}" for k,v in info["structural"]["grammar_counts"].items()),
    ]
    if info["visual"]["score"] is not None:
        lines.append(f"Visual: {info['visual']['score']}/100 ({info['visual']['grade']})")
    return "\n".join(lines)
