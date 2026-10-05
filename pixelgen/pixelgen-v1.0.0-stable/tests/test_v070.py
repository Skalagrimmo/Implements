from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.world import generate_world
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.geography_integrity import validate_geography
from pixelgen.geography_render import render_geography_map
from pixelgen.cognitive_map import render_cognitive_map
from pixelgen.gameplay_integrity import validate_gameplay_integrity
from pixelgen.progression import simulate_progression
from pixelgen.fingerprint import world_fingerprint
from pixelgen.world_diff import compare_worlds
from pixelgen.biomes import get_biome

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

w=generate_gameplay_world(profile,7000,6,5,4)
assert w["generator"]["version"].startswith(("0.7.","0.8.","0.9.","1.0."))
assert w["schema_versions"]["world"]=="0.7"
assert w["schema_versions"]["geography"]=="0.7.0"
assert validate_geography(w)==[]
assert validate_gameplay_integrity(w)==[]

geo=w["geography"]
assert len(geo["regions"])==3
assert len(geo["sectors"])==30
assert all(r["sector_count"]>0 for r in geo["regions"])
assert sum(r["sector_count"] for r in geo["regions"])==30
assert any(r["sector_count"]>1 for r in geo["regions"])

# Every world sector inherits region/subbiome context into its local scene.
for s in w["sectors"]:
    assert isinstance(s["region_id"],int)
    assert s["subbiome"]
    assert s["geography_zone"] in ("core","mid","margin")
    sg=s["scene"]["geography"]
    assert sg["region_id"]==s["region_id"]
    assert sg["subbiome"]==s["subbiome"]
    assert sg["primary_biome"]==s["biome"]

# Regions create actual biome masses rather than a row-major one-cell cycle.
lookup={(s["sx"],s["sy"]):s for s in w["sectors"]}
same_biome_edges=0
cross_region_edges=0
for (x,y),s in lookup.items():
    for n in ((x+1,y),(x,y+1)):
        if n not in lookup:
            continue
        other=lookup[n]
        same_biome_edges += int(s["biome"]==other["biome"])
        cross_region_edges += int(s["region_id"]!=other["region_id"])
assert same_biome_edges>0
assert cross_region_edges>0

# Ecotone scenes should physically contain some neighboring biome material at a boundary.
transition_scenes=[s for s in w["sectors"] if s["transition"]]
assert transition_scenes
mixed=0
for s in transition_scenes:
    ctx=s["scene"]["geography"]
    for edge in ctx["transition_edges"]:
        neighbor_base=get_biome(edge["biome"])["base_ground"]
        if any(neighbor_base in row for row in s["scene"]["ground"]):
            mixed+=1
            break
assert mixed>0

sim=simulate_progression(w)
assert sim["final_sector_reachable"]
assert sim["all_sectors_reachable"]

# Geography and cognitive maps are deterministic.
m1=render_geography_map(w,profile)
c1=render_cognitive_map(w,profile)
w2=generate_gameplay_world(profile,7000,6,5,4)
m2=render_geography_map(w2,profile)
assert m1.tobytes()==m2.tobytes()
assert world_fingerprint(w)==world_fingerprint(w2)
assert m1.size[0]>6*54 and m1.size[1]>5*54
assert c1.size[0]>6*78

# Different seed changes semantic geography.
w3=generate_gameplay_world(profile,7001,6,5,4)
d=compare_worlds(w,w3)
assert not d["identical"]
assert d["geography"]["regions_a"]==3
assert d["geography"]["regions_b"]==3

# Explicit legacy mode remains available for regression/reference work.
legacy=generate_world(profile,7000,3,3,geography=False)
assert "geography" not in legacy

out=ROOT/"generated"/"_test_v070"
out.mkdir(parents=True,exist_ok=True)
m1.save(out/"geography.png")
c1.save(out/"cognitive.png")

print("PixelGen v0.7.0 regional geography tests passed")
