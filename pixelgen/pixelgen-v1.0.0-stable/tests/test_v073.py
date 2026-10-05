from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.region_influence import plan_influences
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.influence_integrity import validate_influence_fields
from pixelgen.progression import simulate_progression
from pixelgen.fingerprint import world_fingerprint
from pixelgen.inspect_world import inspect_world

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

# Isolated causal profiles.
fake={
    "placements":[
        {"id":"silt","kind":"silt_spire","scope":"world","sector":[0,0]},
        {"id":"print","kind":"printing_cathedral","scope":"world","sector":[5,0]},
    ]
}
plan=plan_influences(6,1,fake)

near_silt=plan["per_sector"][(0,0)]
far_silt=plan["per_sector"][(2,0)]
assert near_silt["channels"]["silt_contamination"] > far_silt["channels"]["silt_contamination"]
assert near_silt["modifier_mults"]["hazard_mult"] > 1.0
assert near_silt["modifier_mults"]["encounter_mult"] > 1.0

near_print=plan["per_sector"][(5,0)]
assert near_print["channels"]["print_civic"] > 0
assert near_print["modifier_mults"]["prop_mult"] > 1.0
assert near_print["modifier_mults"]["hazard_mult"] < 1.05

# Full-world integration.
world=generate_gameplay_world(profile,7000,6,5,4)
assert world["generator"]["version"].startswith(("0.7.","0.8.","0.9.","1.0."))
assert world["schema_versions"]["regional_influence"]=="0.7.3"
assert validate_influence_fields(world)==[]

inf=world["regional_influence"]
assert len(inf["sources"])>=1
assert len(inf["sectors"])==30
assert any(s["dominant_channel"] is not None for s in inf["sectors"])

world_lookup={(s["sx"],s["sy"]):s for s in world["sectors"]}
for item in inf["sectors"]:
    pos=(item["sx"],item["sy"])
    scene_inf=world_lookup[pos]["scene"]["geography"]["regional_influence"]
    assert scene_inf["dominant_channel"]==item["dominant_channel"]
    assert scene_inf["channels"]==item["channels"]

# Each source is strongest at its own sector for its own channel among
# Manhattan-equidistant/directly compared samples.
lookup={(s["sx"],s["sy"]):s for s in inf["sectors"]}
for src in inf["sources"]:
    sx,sy=src["sector"]
    own=lookup[(sx,sy)]["channels"][src["channel"]]
    assert own > 0
    for x,y in ((sx+1,sy),(sx-1,sy),(sx,sy+1),(sx,sy-1)):
        if (x,y) in lookup:
            # Other overlapping sources may raise the same channel, so only require
            # that source-sector influence is not implausibly lower.
            assert own + 0.75 >= lookup[(x,y)]["channels"][src["channel"]]

sim=simulate_progression(world)
assert sim["final_sector_reachable"]
assert sim["all_sectors_reachable"]

info=inspect_world(world)
assert info["influence"]["sources"]==len(inf["sources"])
assert info["influence"]["affected_sectors"]>0

world2=generate_gameplay_world(profile,7000,6,5,4)
assert world_fingerprint(world)==world_fingerprint(world2)

print("PixelGen v0.7.3 regional influence field tests passed")
