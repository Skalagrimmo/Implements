from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.corridor_integrity import validate_regional_corridors
from pixelgen.gameplay_integrity import validate_gameplay_integrity
from pixelgen.progression import simulate_progression

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")
dims=[(1,1),(2,2),(3,3),(4,3),(6,5),(8,6)]
cases=0
corridors=0
segments=0

for seed in range(-15,25):
    for cols,rows in dims:
        world=generate_gameplay_world(profile,seed,cols,rows,4)
        errors=validate_regional_corridors(world)
        assert errors==[], (seed,cols,rows,errors[:5])
        assert validate_gameplay_integrity(world)==[]
        sim=simulate_progression(world)
        assert sim["final_sector_reachable"] and sim["all_sectors_reachable"]

        data=world["regional_corridors"]
        corridors += data["summary"]["corridor_count"]
        segments += data["summary"]["local_segment_count"]
        cases+=1

print(
    f"PixelGen v0.9.0 corridor fuzz passed: {cases} worlds, "
    f"{corridors} corridors, {segments} local segments"
)
