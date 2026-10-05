from .fingerprint import world_fingerprint
from .inspect_world import inspect_world

def _dict_delta(a,b):
    keys=sorted(set(a)|set(b))
    out={}
    for k in keys:
        av=a.get(k,0); bv=b.get(k,0)
        if av != bv:
            out[k]={"a":av,"b":bv,"delta":bv-av if isinstance(av,(int,float)) and isinstance(bv,(int,float)) else None}
    return out

def compare_worlds(a,b):
    ia=inspect_world(a)
    ib=inspect_world(b)
    same=ia["fingerprint"]==ib["fingerprint"]

    ga=a.get("gameplay") or {}
    gb=b.get("gameplay") or {}

    return {
        "identical":same,
        "fingerprints":{"a":ia["fingerprint"],"b":ib["fingerprint"]},
        "dimensions":{
            "a":ia["dimensions"],
            "b":ib["dimensions"],
            "same":ia["dimensions"]==ib["dimensions"],
        },
        "biome_delta":_dict_delta(ia["biomes"],ib["biomes"]),
        "geography":{
            "regions_a":ia["geography"]["regions"],
            "regions_b":ib["geography"]["regions"],
            "transitions_a":ia["geography"]["transitions"],
            "transitions_b":ib["geography"]["transitions"],
            "subbiome_delta":_dict_delta(ia["geography"]["subbiomes"],ib["geography"]["subbiomes"]),
            "zone_delta":_dict_delta(ia["geography"]["zones"],ib["geography"]["zones"]),
        },
        "influence":{
            "sources_a":ia["influence"]["sources"],
            "sources_b":ib["influence"]["sources"],
            "affected_a":ia["influence"]["affected_sectors"],
            "affected_b":ib["influence"]["affected_sectors"],
            "dominant_delta":_dict_delta(
                ia["influence"]["dominant_channels"],
                ib["influence"]["dominant_channels"],
            ),
        },
        "topology":{
            "fronts_a":ia["topology"]["front_count"],
            "fronts_b":ib["topology"]["front_count"],
            "edges_a":ia["topology"]["boundary_edges"],
            "edges_b":ib["topology"]["boundary_edges"],
            "status_delta":_dict_delta(
                ia["topology"]["status_counts"],
                ib["topology"]["status_counts"],
            ),
            "pair_delta":_dict_delta(
                ia["topology"]["front_pair_counts"],
                ib["topology"]["front_pair_counts"],
            ),
        },
        "regional_corridors":{
            "count_a":ia["regional_corridors"]["count"],
            "count_b":ib["regional_corridors"]["count"],
            "covered_a":ia["regional_corridors"]["covered_sectors"],
            "covered_b":ib["regional_corridors"]["covered_sectors"],
            "kind_delta":_dict_delta(
                ia["regional_corridors"]["by_kind"],
                ib["regional_corridors"]["by_kind"],
            ),
        },
        "territory_graph":{
            "territories_a":ia["territory_graph"]["territories"],
            "territories_b":ib["territory_graph"]["territories"],
            "front_sites_a":ia["territory_graph"]["front_sites"],
            "front_sites_b":ib["territory_graph"]["front_sites"],
            "event_seeds_a":ia["territory_graph"]["event_seeds"],
            "event_seeds_b":ib["territory_graph"]["event_seeds"],
            "alignment_delta":_dict_delta(
                ia["territory_graph"]["by_alignment"],
                ib["territory_graph"]["by_alignment"],
            ),
            "event_kind_delta":_dict_delta(
                ia["territory_graph"]["event_kinds"],
                ib["territory_graph"]["event_kinds"],
            ),
        },
        "structural":{
            "score_a":ia["structural"]["score"],
            "score_b":ib["structural"]["score"],
            "grammar_delta":_dict_delta(
                ia["structural"]["grammar_counts"],
                ib["structural"]["grammar_counts"],
            ),
        },
        "object_delta":_dict_delta(ia["objects"]["by_kind"],ib["objects"]["by_kind"]),
        "landmark_scope_delta":_dict_delta(ia["landmarks"]["by_scope"],ib["landmarks"]["by_scope"]),
        "encounter_delta":_dict_delta(ia["encounters"]["by_kind"],ib["encounters"]["by_kind"]),
        "find_delta":_dict_delta(ia["finds"]["by_kind"],ib["finds"]["by_kind"]),
        "ability_delta":_dict_delta(ia["navigation"]["abilities"],ib["navigation"]["abilities"]),
        "main_path":{
            "same":ga.get("main_path")==gb.get("main_path"),
            "a_nodes":len(ga.get("main_path",[])),
            "b_nodes":len(gb.get("main_path",[])),
        },
        "visual":{
            "a":ia["visual"],
            "b":ib["visual"],
        },
    }

def diff_text(result):
    lines=[
        f"Identical semantic world: {result['identical']}",
        f"A: {result['fingerprints']['a']}",
        f"B: {result['fingerprints']['b']}",
        f"Dimensions equal: {result['dimensions']['same']}",
        f"Main path equal: {result['main_path']['same']}",
        f"Regions: {result['geography']['regions_a']}→{result['geography']['regions_b']}",
        f"Region transitions: {result['geography']['transitions_a']}→{result['geography']['transitions_b']}",
        f"Structural score: {result['structural']['score_a']}→{result['structural']['score_b']}",
        f"Influence sources: {result['influence']['sources_a']}→{result['influence']['sources_b']}",
        f"Affected sectors: {result['influence']['affected_a']}→{result['influence']['affected_b']}",
        f"Influence fronts: {result['topology']['fronts_a']}→{result['topology']['fronts_b']}",
        f"Influence boundary edges: {result['topology']['edges_a']}→{result['topology']['edges_b']}",
        f"Territories: {result['territory_graph']['territories_a']}→{result['territory_graph']['territories_b']}",
        f"Front sites: {result['territory_graph']['front_sites_a']}→{result['territory_graph']['front_sites_b']}",
        f"Event seeds: {result['territory_graph']['event_seeds_a']}→{result['territory_graph']['event_seeds_b']}",
        f"Regional corridors: {result['regional_corridors']['count_a']}→{result['regional_corridors']['count_b']}",
        f"Corridor coverage: {result['regional_corridors']['covered_a']}→{result['regional_corridors']['covered_b']}",
    ]
    for label,key in (
        ("Biomes","biome_delta"),
        ("Objects","object_delta"),
        ("Landmarks","landmark_scope_delta"),
        ("Encounters","encounter_delta"),
        ("Finds","find_delta"),
        ("Abilities","ability_delta"),
        ("Subbiomes","geography.subbiome_delta"),
        ("Geography zones","geography.zone_delta"),
        ("Structural grammars","structural.grammar_delta"),
        ("Influence dominance","influence.dominant_delta"),
        ("Influence topology","topology.status_delta"),
        ("Influence front pairs","topology.pair_delta"),
        ("Territory alignments","territory_graph.alignment_delta"),
        ("Event seed kinds","territory_graph.event_kind_delta"),
        ("Corridor kinds","regional_corridors.kind_delta"),
    ):
        if "." in key:
            a,b=key.split(".",1)
            delta=result[a][b]
        else:
            delta=result[key]
        if delta:
            lines.append(label + ": " + ", ".join(
                f"{k} {v['a']}→{v['b']}" for k,v in delta.items()
            ))
    return "\n".join(lines)
