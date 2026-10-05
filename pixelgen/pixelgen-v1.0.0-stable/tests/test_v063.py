from pathlib import Path
import sys, json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.audit import audit_world
from pixelgen.seed_sweep import sweep_seeds
from pixelgen.doctor import run_doctor
from pixelgen.serialization import to_plain

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

world=generate_gameplay_world(profile,6303,4,3,4)
assert world["generator"]["name"]=="PixelGen"
assert world["gameplay"]["version"]=="0.6"
assert world["schema_versions"]["visual_quality"]=="0.6.3"

audit=audit_world(world)
assert audit["status"] in ("pass","warn")
assert not audit["errors"]
assert audit["progression"]["final_sector_reachable"]
assert audit["progression"]["all_sectors_reachable"]
assert audit["visual"]["metrics"]["visual_grade"] in ("A","B","C","D","E")
assert 0 <= audit["visual"]["metrics"]["quadrant_entropy"] <= 1

sweep=sweep_seeds(profile,start_seed=6300,count=8,cols=4,rows=3,ability_count=4)
assert len(sweep["results"])==8
assert sweep["best_seed"] is not None
scores=[r["score"] for r in sweep["results"] if r["status"]!="fail"]
assert sweep["best_score"]==max(scores)

doctor=run_doctor(ROOT/"profiles"/"techno_animist_gothic.json")
assert doctor["status"]=="pass"
assert all(c["ok"] for c in doctor["checks"])

# Tampering with progression must be caught by unified audit.
bad=to_plain(world)
bad["gameplay"]["final_sector"]=[999,999]
bad_audit=audit_world(bad)
assert bad_audit["status"]=="fail"
assert bad_audit["errors"]

print("PixelGen v0.6.3 tests passed")
