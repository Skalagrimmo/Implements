from pathlib import Path
import sys, json

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.world import generate_world
from pixelgen.landmark_integrity import validate_landmark_integrity
from pixelgen.gameplay_integrity import validate_gameplay_integrity
from pixelgen.progression import simulate_progression
from pixelgen.cognitive_map import render_cognitive_map
from pixelgen.structures import generate_printing_cathedral, generate_silt_spire

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

world=generate_gameplay_world(profile,6060,4,3,4)
assert validate_landmark_integrity(world)==[]
assert validate_gameplay_integrity(world)==[]
assert simulate_progression(world)["all_sectors_reachable"]

landmarks=[]
for s in world["sectors"]:
    landmarks.extend(s["scene"].get("landmarks",{}).values())

assert sum(1 for x in landmarks if x["scope"]=="world")==1
assert sum(1 for x in landmarks if x["scope"]=="regional")==2
assert len(landmarks) < len(world["sectors"])  # sparse by design: not one compulsory landmark per sector

# World anchor is unique and is one of the deliberately larger silhouettes.
world_lm=[x for x in landmarks if x["scope"]=="world"][0]
assert world_lm["kind"] in ("printing_cathedral","silt_spire")

# No old fixed "every landmark at top-right" pattern.
positions={(x["x"],x["y"]) for x in landmarks}
assert len(positions) >= min(3,len(landmarks))

# Deterministic global landmark plan.
world2=generate_gameplay_world(profile,6060,4,3,4)
assert json.dumps(world["landmark_system"],sort_keys=True)==json.dumps(world2["landmark_system"],sort_keys=True)

# Tiny worlds don't force a fake world-scale anchor.
tiny=generate_world(profile,7,1,1)
assert validate_landmark_integrity(tiny)==[]
assert not any(x["scope"]=="world" for s in tiny["sectors"] for x in s["scene"]["landmarks"].values())

# New silhouettes and cognitive map render.
assert generate_printing_cathedral(profile,1).size==(96,96)
assert generate_silt_spire(profile,1).size==(64,96)
m=render_cognitive_map(world,profile)
assert m.size[0] > 200 and m.size[1] > 150

out=ROOT/"generated"/"_test_v061"
out.mkdir(parents=True,exist_ok=True)
m.save(out/"cognitive_map.png")
print("PixelGen v0.6.1 landmark tests passed")
