from pathlib import Path
import sys, json, copy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pixelgen.palette import load_profile
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.visual_pattern import analyze_visual_patterns
from pixelgen.cognitive_map import render_cognitive_map
from pixelgen.landmark_integrity import validate_landmark_integrity
from pixelgen.gameplay_integrity import validate_gameplay_integrity
from pixelgen.progression import simulate_progression
profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")
w=generate_gameplay_world(profile,6060,4,3,4)
assert validate_landmark_integrity(w)==[]
assert validate_gameplay_integrity(w)==[]
assert simulate_progression(w)["all_sectors_reachable"]
quality=analyze_visual_patterns(w)
assert quality["metrics"]["visual_repetition_score"] >= 65
assert quality["metrics"]["dominant_quadrant_share"] < 0.90
assert quality["metrics"]["exact_position_repeat_share"] < 0.75
assert "visual_quality" in w
lms=[lm for s in w["sectors"] for lm in s["scene"].get("landmarks",{}).values()]
assert sum(x["scope"]=="world" for x in lms)==1
assert all("prominence" in x for x in lms)
assert max(x["prominence"] for x in lms if x["scope"]=="world")==100
m1=render_cognitive_map(w,profile)
w2=generate_gameplay_world(profile,6060,4,3,4)
m2=render_cognitive_map(w2,profile)
assert m1.size[0] > 4*78
assert m1.tobytes()==m2.tobytes()
bad=copy.deepcopy(w)
for s in bad["sectors"]:
    for lm in s["scene"].get("landmarks",{}).values(): lm["x"]=18; lm["y"]=1
qbad=analyze_visual_patterns(bad)
assert qbad["status"]=="warn"
assert qbad["metrics"]["visual_repetition_score"] < quality["metrics"]["visual_repetition_score"]
print("PixelGen v0.6.2 tests passed")
