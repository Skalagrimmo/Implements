from collections import defaultdict, Counter

EXPECTATIONS = {
    "silt_marsh": {
        "max_junctions": 4.0,
        "max_loop_rank": 1.5,
        "min_turns": 2.0,
    },
    "dark_forest": {
        "min_junctions": 4.0,
        "min_endpoints": 3.0,
    },
    "frozen_pass": {
        "max_junctions": 4.0,
        "min_turns": 4.0,
        "max_loop_rank": 1.5,
    },
    "ruined_settlement": {
        "min_junctions": 6.0,
        "min_loop_rank": 2.0,
    },
    "reformed_chapel": {
        "min_junctions": 3.0,
        "min_loop_rank": 1.0,
    },
}


def _avg(values):
    return 0.0 if not values else sum(values)/len(values)


def analyze_structural_grammar(world):
    groups=defaultdict(list)
    warnings=[]

    for s in world.get("sectors",[]):
        meta=s.get("scene",{}).get("structural_grammar")
        if not isinstance(meta,dict):
            warnings.append(f"sector {(s.get('sx'),s.get('sy'))} has no structural grammar")
            continue
        groups[s.get("biome","?")].append(meta)

    biomes={}
    for biome,items in sorted(groups.items()):
        metrics=[x.get("metrics",{}) for x in items]
        variants=[
            x.get("variant",{}).get("variant_id")
            for x in items if x.get("variant",{}).get("variant_id")
        ]
        subbiomes=[
            x.get("variant",{}).get("subbiome")
            for x in items if x.get("variant",{}).get("subbiome")
        ]
        zones=[
            x.get("variant",{}).get("zone")
            for x in items if x.get("variant",{}).get("zone")
        ]
        ecotone_adapters=sum(len(x.get("ecotone_adapters",[])) for x in items)
        operator_counts=Counter(
            op
            for x in items
            for op in x.get("variant",{}).get("operators",[])
        )
        summary={
            "sectors":len(items),
            "grammar_ids":sorted({x.get("grammar_id") for x in items}),
            "path_visuals":sorted({x.get("path_visual") for x in items}),
            "variant_ids":sorted(set(variants)),
            "subbiomes":sorted(set(subbiomes)),
            "zones":sorted(set(zones)),
            "ecotone_adapters":ecotone_adapters,
            "ecotone_pressure":round(ecotone_adapters/max(1,len(items)),3),
            "operator_counts":dict(sorted(operator_counts.items())),
            "morphology_sample_reliable":len(items)>=5,
            "avg_path_cells":round(_avg([m.get("path_cells",0) for m in metrics]),2),
            "avg_endpoints":round(_avg([m.get("endpoints",0) for m in metrics]),2),
            "avg_junctions":round(_avg([m.get("junctions",0) for m in metrics]),2),
            "avg_turn_like_cells":round(_avg([m.get("turn_like_cells",0) for m in metrics]),2),
            "avg_loop_rank":round(_avg([m.get("loop_rank",0) for m in metrics]),2),
        }
        biomes[biome]=summary

        exp=EXPECTATIONS.get(biome,{})
        # v0.7.2 ecotone adapters deliberately add edgeward connectors.
        # They may create extra junctions/loops without changing the parent biome grammar.
        pressure=summary["ecotone_pressure"]
        ops=summary["operator_counts"]
        n=max(1,summary["sectors"])

        # Intentional variant operators are part of the requested morphology,
        # so the old 0.7.1 ceilings are expanded only by the operators that can
        # structurally create intersections/loops.
        junction_allowance=(
            pressure*5.0
            + ops.get("extra_spurs",0)*2.0/n
            + ops.get("side_loop",0)*2.5/n
            + ops.get("crossing",0)*2.0/n
            + ops.get("widen",0)*1.2/n
            + ops.get("large_platform",0)*1.6/n
            + ops.get("small_platform",0)*0.8/n
            + ops.get("island_spur",0)*1.0/n
            + ops.get("island_chain",0)*1.0/n
            + ops.get("intensify",0)*1.0/n
        )
        loop_allowance=(
            pressure*3.0
            + ops.get("side_loop",0)*2.0/n
            + ops.get("crossing",0)*1.5/n
            + ops.get("large_platform",0)*1.0/n
            + ops.get("small_platform",0)*0.5/n
            + ops.get("intensify",0)*1.5/n
        )

        max_junctions=exp.get("max_junctions")
        max_loops=exp.get("max_loop_rank")
        if max_junctions is not None:
            max_junctions += junction_allowance
        if max_loops is not None:
            max_loops += loop_allowance

        if summary["morphology_sample_reliable"]:
            if max_junctions is not None and summary["avg_junctions"]>max_junctions:
                warnings.append(f"{biome}: too branch-heavy even after ecotone allowance")
            if "min_junctions" in exp and summary["avg_junctions"]<exp["min_junctions"]:
                warnings.append(f"{biome}: not structurally branched/intersected enough")
            if "min_endpoints" in exp and summary["avg_endpoints"]<exp["min_endpoints"]:
                warnings.append(f"{biome}: too few structural endpoints")
            if "min_turns" in exp and summary["avg_turn_like_cells"]<exp["min_turns"]:
                warnings.append(f"{biome}: too straight for intended morphology")
            if max_loops is not None and summary["avg_loop_rank"]>max_loops:
                warnings.append(f"{biome}: too many loops even after ecotone allowance")
            if "min_loop_rank" in exp and summary["avg_loop_rank"]<exp["min_loop_rank"]:
                warnings.append(f"{biome}: lacks expected loops/courtyard blocks")

    grammar_ids={
        g
        for summary in biomes.values()
        for g in summary["grammar_ids"]
        if g is not None
    }
    visuals={
        g
        for summary in biomes.values()
        for g in summary["path_visuals"]
        if g is not None
    }

    variant_ids={
        v
        for summary in biomes.values()
        for v in summary.get("variant_ids",[])
        if v is not None
    }
    total_ecotone_adapters=sum(
        summary.get("ecotone_adapters",0)
        for summary in biomes.values()
    )

    if len(biomes)>=3 and len(grammar_ids)<len(biomes):
        warnings.append("multiple biomes share a structural grammar id")
    if len(biomes)>=3 and len(visuals)<2:
        warnings.append("all biome route skeletons use the same visible material")

    score=max(0,100-len(warnings)*12)
    return {
        "version":"0.7.2",
        "status":"pass" if not warnings else "warn",
        "score":score,
        "biomes":biomes,
        "distinct_grammar_ids":len(grammar_ids),
        "distinct_path_visuals":len(visuals),
        "distinct_variant_ids":len(variant_ids),
        "ecotone_adapters":total_ecotone_adapters,
        "warnings":warnings,
    }


def structural_report_text(result):
    lines=[
        f"STRUCTURAL GRAMMAR: {result['status'].upper()}",
        f"Score: {result['score']}/100",
        f"Distinct grammar IDs: {result['distinct_grammar_ids']}",
        f"Distinct path visuals: {result['distinct_path_visuals']}",
        f"Distinct subbiome variants: {result.get('distinct_variant_ids',0)}",
        f"Ecotone adapters: {result.get('ecotone_adapters',0)}",
        "",
    ]
    for biome,s in result["biomes"].items():
        lines.append(
            f"{biome}: grammar={','.join(s['grammar_ids'])} "
            f"paths={s['avg_path_cells']} endpoints={s['avg_endpoints']} "
            f"junctions={s['avg_junctions']} turns={s['avg_turn_like_cells']} "
            f"loops={s['avg_loop_rank']} "
            f"variants={len(s.get('variant_ids',[]))} "
            f"ecotones={s.get('ecotone_adapters',0)} "
            f"pressure={s.get('ecotone_pressure',0)}"
        )
    for w in result["warnings"]:
        lines.append(f"WARNING: {w}")
    return "\n".join(lines)
