from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.world import generate_world
from pixelgen.corridor_integrity import validate_regional_corridors
from pixelgen.progression import simulate_progression
from pixelgen.fingerprint import world_fingerprint

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

world=generate_gameplay_world(profile,7301,6,5,4)
assert world["generator"]["version"].startswith(("0.9.","1.0."))
assert world["schema_versions"]["regional_corridors"]=="0.9.0"
assert validate_regional_corridors(world)==[]

corr=world["regional_corridors"]
assert corr["version"]=="0.9.0"
assert corr["summary"]["corridor_count"]>=1
assert corr["summary"]["covered_sector_count"]>=1
assert corr["summary"]["local_segment_count"]==sum(
    c["sector_count"] for c in corr["corridors"]
)

# World spine is guaranteed and starts at the gameplay/world origin.
spines=[c for c in corr["corridors"] if c["purpose"]=="world_spine"]
assert len(spines)==1
assert spines[0]["source"]==[0,0]

# Every geography region center is represented by the macro corridor network.
covered={tuple(p) for c in corr["corridors"] for p in c["path"]}
for region in world["geography"]["regions"]:
    assert tuple(region["center"]) in covered

# Every regional/world landmark is connected to corridor topology.
for lm in world["landmark_system"]["placements"]:
    if lm["scope"] in ("regional","world"):
        assert tuple(lm["sector"]) in covered

# Links on corridor paths know which macro corridor crosses them.
lookup={(s["sx"],s["sy"]):s for s in world["sectors"]}
for c in corr["corridors"]:
    path=[tuple(p) for p in c["path"]]
    for a,b in zip(path,path[1:]):
        matching=[l for l in lookup[a]["links"].values() if tuple(l["to"])==b]
        assert len(matching)==1
        assert any(tag["id"]==c["id"] for tag in matching[0].get("corridors",[]))

# Local realization survives gameplay grammar and progression remains valid.
sim=simulate_progression(world)
assert sim["final_sector_reachable"] and sim["all_sectors_reachable"]
for s in world["sectors"]:
    for local in s["scene"].get("regional_corridors",[]):
        for x,y in local["route_cells"]:
            assert s["scene"]["collision"][y][x]=="walk"

# Deterministic world/corridor fingerprint.
world2=generate_gameplay_world(profile,7301,6,5,4)
assert world_fingerprint(world)==world_fingerprint(world2)
assert world["regional_corridors"]==world2["regional_corridors"]

# Minimal world is valid: there is simply no multi-sector corridor to realize.
tiny=generate_gameplay_world(profile,-777,1,1,0)
assert validate_regional_corridors(tiny)==[]
assert tiny["regional_corridors"]["summary"]["corridor_count"]==0

# Legacy no-geography mode gets an explicit disabled/empty corridor contract.
legacy=generate_world(profile,9,2,2,geography=False)
assert validate_regional_corridors(legacy)==[]
assert legacy["regional_corridors"]["policy"]["enabled"] is False
assert legacy["regional_corridors"]["corridors"]==[]

print("PixelGen v0.9.0 regional corridor / macro-to-local continuity tests passed")
