from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.audit import audit_world

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")
dims=[(1,1),(2,2),(3,2),(4,3),(5,4)]
cases=0
fails=0
warns=0
for seed in range(-15,35):
    for cols,rows in dims:
        w=generate_gameplay_world(profile,seed,cols,rows,4)
        a=audit_world(w)
        fails += int(a["status"]=="fail")
        warns += int(a["status"]=="warn")
        assert a["status"]!="fail", (seed,cols,rows,a["errors"][:5])
        cases += 1
print(f"PixelGen v0.6.3 fuzz passed: {cases} worlds; warn={warns}; fail={fails}")
