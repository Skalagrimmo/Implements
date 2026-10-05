from pathlib import Path
import copy
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.environment_journal import run_environment_log
from pixelgen.environment_compare import compare_logs, comparison_csv

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

log=run_environment_log(profile,suite="quick",label="fast",repeat=2)
assert log["schema_version"]=="0.6.4.2"
assert log["repeat"]==2
assert log["summary"]["status"]=="pass"

for c in log["cases"]:
    assert c["repeat"]==2
    assert len(c["runs"])==2
    assert c["fingerprint_consistent"]
    assert c["timing_stats"]["total"]["median"]>0
    assert 0 <= c["timing_stats"]["total"]["cv"]

slow=copy.deepcopy(log)
slow["environment"]["label"]="slow"

# Scale median timing view + underlying statistics by 2x while preserving fingerprints.
for c in slow["cases"]:
    for k,v in list(c["timings_ms"].items()):
        if isinstance(v,(int,float)):
            c["timings_ms"][k]=v*2
    for stats in c["timing_stats"].values():
        for sk in ("mean","median","min","max","stdev"):
            if isinstance(stats.get(sk),(int,float)):
                stats[sk]*=2

cmp=compare_logs([log,slow],baseline_label="fast")
assert cmp["status"]=="pass"
summary={x["label"]:x for x in cmp["environment_summary"]}
assert summary["fast"]["performance_index"]==1.0
assert 1.9 <= summary["slow"]["performance_index"] <= 2.1
assert cmp["summary"]["fingerprint_mismatches"]==0

csv_text=comparison_csv(cmp)
assert "relative_to_baseline" in csv_text
assert "stability_cv" in csv_text
assert "fast" in csv_text and "slow" in csv_text

print("PixelGen v0.6.4.2 tests passed")
