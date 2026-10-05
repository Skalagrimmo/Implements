from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.scene_biome import generate_biome_scene
from pixelgen.encounters import generate_encounters
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.structural_report import analyze_structural_grammar
from pixelgen.serialization import lua_serialize
from pixelgen.fingerprint import world_fingerprint
from pixelgen.region_influence import plan_influences, apply_influence_to_geography_context

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

def ctx(biome,subbiome,h=1.0,p=1.0,e=1.0):
    return {
        "region_id":0,
        "region_name":"Hardening Test",
        "primary_biome":biome,
        "subbiome":subbiome,
        "zone":"mid",
        "distance_to_region_center":1,
        "transition":False,
        "transition_to":None,
        "transition_edges":[],
        "fields":{"moisture":0.5,"elevation":0.5,"settlement":0.5},
        "modifiers":{
            "hazard_mult":h,
            "prop_mult":p,
            "encounter_mult":e,
        },
    }

def hazard_count(scene):
    return sum(v=="hazard" for row in scene["collision"] for v in row)

# Hazard density must be monotonic for the same seed.
for biome,sub in (
    ("ruined_settlement","broken_streets"),
    ("silt_marsh","reed_channels"),
    ("dark_forest","moss_grove"),
):
    for i in range(100):
        seed=31_000+i
        low=generate_biome_scene(profile,seed,biome,landmark_plan=[],geography_context=ctx(biome,sub,h=0.92))
        base=generate_biome_scene(profile,seed,biome,landmark_plan=[],geography_context=ctx(biome,sub,h=1.00))
        high=generate_biome_scene(profile,seed,biome,landmark_plan=[],geography_context=ctx(biome,sub,h=1.24))
        assert hazard_count(low) <= hazard_count(base) <= hazard_count(high)

# Fractional encounter multipliers must have real effect while staying monotonic.
inc=0
dec=0
for i in range(200):
    seed=32_000+i
    biome="dark_forest"
    sub="moss_grove"

    base=generate_biome_scene(profile,seed,biome,landmark_plan=[],geography_context=ctx(biome,sub,e=1.0))
    high=generate_biome_scene(profile,seed,biome,landmark_plan=[],geography_context=ctx(biome,sub,e=1.0432))
    low=generate_biome_scene(profile,seed,biome,landmark_plan=[],geography_context=ctx(biome,sub,e=0.94))

    generate_encounters(base,biome,seed)
    generate_encounters(high,biome,seed)
    generate_encounters(low,biome,seed)

    nb=len(base["encounters"])
    nh=len(high["encounters"])
    nl=len(low["encounters"])

    assert nl <= nb <= nh
    inc += nh > nb
    dec += nl < nb

assert inc > 0
assert dec > 0


# Printing Cathedral must not become more hazardous through its increased prop budget.
print_source=plan_influences(1,1,{
    "placements":[{
        "id":"cathedral",
        "kind":"printing_cathedral",
        "scope":"world",
        "sector":[0,0],
    }]
})["per_sector"][(0,0)]

base_ctx=ctx("ruined_settlement","broken_streets")
print_ctx=apply_influence_to_geography_context(base_ctx,print_source)

for i in range(50):
    seed=33_000+i
    base_scene=generate_biome_scene(
        profile,seed,"ruined_settlement",
        landmark_plan=[],geography_context=base_ctx
    )
    print_scene=generate_biome_scene(
        profile,seed,"ruined_settlement",
        landmark_plan=[],geography_context=print_ctx
    )
    assert hazard_count(print_scene) <= hazard_count(base_scene)
    assert all(
        getattr(o,"kind",o.get("kind") if isinstance(o,dict) else None)!="silt_growth"
        for o in print_scene["objects"]
    )

# Known Frozen Pass warning seed must be cleaned up by the grammar itself.
world=generate_gameplay_world(profile,7303,6,5,4)
report=analyze_structural_grammar(world)
assert report["status"]=="pass"
assert not any("frozen_pass" in w for w in report["warnings"])

# Lua dictionaries omit absent optional values.
lua=lua_serialize({
    "dominant_channel":None,
    "transition_to":None,
    "nested":{"missing":None,"value":2},
})
assert "nil" not in lua
assert "dominant_channel" not in lua
assert "transition_to" not in lua
assert "missing" not in lua
assert "value = 2" in lua

# Patch metadata and determinism.
w1=generate_gameplay_world(profile,7301,6,5,4)
w2=generate_gameplay_world(profile,7301,6,5,4)
assert w1["generator"]["version"].startswith(("0.7.","0.8.","0.9.","1.0."))
assert w1["schema_versions"]["hardening"]=="0.7.3.1"
assert world_fingerprint(w1)==world_fingerprint(w2)

print("PixelGen v0.7.3.1 influence hardening tests passed")
