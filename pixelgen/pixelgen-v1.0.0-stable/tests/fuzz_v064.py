from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.fingerprint import world_fingerprint
from pixelgen.inspect_world import inspect_world
from pixelgen.audit import audit_world

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")
dims=[(1,1),(2,2),(3,2),(4,3),(5,4)]
seen=set()
cases=0
for seed in range(-10,30):
    for cols,rows in dims:
        w=generate_gameplay_world(profile,seed,cols,rows,4)
        a=audit_world(w)
        assert a["status"]!="fail"
        fp=world_fingerprint(w)
        assert len(fp)==64
        info=inspect_world(w)
        assert info["dimensions"]["sectors"]==cols*rows
        key=(seed,cols,rows,fp)
        assert key not in seen
        seen.add(key)
        cases+=1
print(f"PixelGen v0.6.4 fuzz passed: {cases} worlds")
