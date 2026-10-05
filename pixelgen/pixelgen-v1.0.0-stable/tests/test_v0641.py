from pathlib import Path
import copy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.environment_journal import run_environment_log
from pixelgen.environment_compare import compare_logs
from pixelgen.fingerprint import world_fingerprint
from pixelgen.gameplay_world import generate_gameplay_world

profile = load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

log = run_environment_log(profile, suite="quick", label="test-A")
assert log["schema_version"].startswith("0.6.4.")
assert log["summary"]["status"] == "pass"
assert len(log["cases"]) == 2
assert all(c["fingerprint"] and len(c["fingerprint"]) == 64 for c in log["cases"])
assert all(c["timings_ms"]["total"] > 0 for c in log["cases"])

clone = copy.deepcopy(log)
clone["environment"]["label"] = "test-B"
for c in clone["cases"]:
    c["timings_ms"]["total"] *= 2

result = compare_logs([log, clone])
assert result["status"] == "pass"
assert result["summary"]["fingerprint_mismatches"] == 0
assert all(c["deterministic"] for c in result["cases"])

bad = copy.deepcopy(clone)
bad["environment"]["label"] = "test-C"
bad["cases"][0]["fingerprint"] = "f" * 64
bad_result = compare_logs([log, bad])
assert bad_result["status"] == "fail"
assert bad_result["summary"]["fingerprint_mismatches"] == 1

world = generate_gameplay_world(profile, 6401, 4, 3, 4)
assert world["generator"]["name"]=="PixelGen"
assert world["gameplay"]["version"]=="0.6"

print("PixelGen v0.6.4.1 tests passed")
