from .integrity import validate_world_integrity
from .landmark_integrity import validate_landmark_integrity
from .visual_pattern import analyze_visual_patterns
from .progression import simulate_progression
from .gameplay_integrity import validate_gameplay_integrity
from .geography_integrity import validate_geography
from .structural_integrity import validate_structural_grammar
from .structural_report import analyze_structural_grammar
from .influence_integrity import validate_influence_fields
from .topology_integrity import validate_influence_topology
from .territory_integrity import validate_territory_graph
from .corridor_integrity import validate_regional_corridors

AUDIT_VERSION = "1.0.0"

def audit_world(world, strict_visual=False):
    errors=[]
    warnings=[]

    errors.extend(validate_world_integrity(world))
    errors.extend(validate_landmark_integrity(world))
    errors.extend(validate_structural_grammar(world))
    if isinstance(world.get("regional_influence"),dict):
        errors.extend(validate_influence_fields(world))
    if isinstance(world.get("influence_topology"),dict):
        errors.extend(validate_influence_topology(world))
    if isinstance(world.get("territory_graph"),dict):
        errors.extend(validate_territory_graph(world))
    if isinstance(world.get("regional_corridors"),dict):
        errors.extend(validate_regional_corridors(world))
    if isinstance(world.get("geography"),dict):
        errors.extend(validate_geography(world))

    structural=analyze_structural_grammar(world)
    warnings.extend(structural.get("warnings",[]))

    gameplay_present=isinstance(world.get("gameplay"),dict)
    progression=None
    if gameplay_present:
        errors.extend(validate_gameplay_integrity(world))
        if not errors:
            try:
                progression=simulate_progression(world)
            except Exception as e:
                errors.append(f"progression audit failed: {e}")

    visual=analyze_visual_patterns(world)
    warnings.extend(visual.get("warnings",[]))
    if strict_visual and warnings:
        errors.extend(f"visual: {w}" for w in warnings)

    status="fail" if errors else ("warn" if warnings else "pass")
    return {
        "audit_version":AUDIT_VERSION,
        "status":status,
        "strict_visual":bool(strict_visual),
        "errors":errors,
        "warnings":warnings,
        "counts":{
            "sectors":len(world.get("sectors",[])),
            "landmarks":visual.get("metrics",{}).get("landmark_count",0),
            "gameplay_present":gameplay_present,
            "corridors":len((world.get("regional_corridors") or {}).get("corridors",[])),
        },
        "visual":visual,
        "structural":structural,
        "progression":progression,
    }

def audit_summary(result):
    lines=[
        f"AUDIT: {result['status'].upper()}",
        f"Sectors: {result['counts']['sectors']}",
        f"Landmarks: {result['counts']['landmarks']}",
        f"Regional corridors: {result['counts'].get('corridors',0)}",
    ]
    score=result.get("visual",{}).get("metrics",{}).get("visual_repetition_score")
    grade=result.get("visual",{}).get("metrics",{}).get("visual_grade")
    if score is not None:
        lines.append(f"Visual repetition score: {score}/100" + (f" ({grade})" if grade else ""))
    structural=result.get("structural",{})
    if structural:
        lines.append(f"Structural grammar score: {structural.get('score')}/100")
    if result.get("progression") is not None:
        p=result["progression"]
        lines.append(f"Progression final reachable: {p['final_sector_reachable']}")
        lines.append(f"Progression all sectors reachable: {p['all_sectors_reachable']}")
    for e in result["errors"]:
        lines.append(f"ERROR: {e}")
    for w in result["warnings"]:
        lines.append(f"WARNING: {w}")
    return "\n".join(lines)
