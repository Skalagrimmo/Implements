from pathlib import Path
import sys, argparse

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.gameplay_integrity import validate_gameplay_integrity
from pixelgen.progression import simulate_progression

parser=argparse.ArgumentParser()
parser.add_argument("--extended", action="store_true", help="Run the larger desktop fuzz matrix")
args=parser.parse_args()

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")
dims=[(1,1),(1,4),(4,1),(2,2),(3,3),(4,3),(5,4),(6,5)]
seeds=range(-25,25) if not args.extended else range(-100,100)

cases=0
for seed in seeds:
    for cols,rows in dims:
        world=generate_gameplay_world(profile,seed=seed,cols=cols,rows=rows,ability_count=4)
        errors=validate_gameplay_integrity(world)
        assert not errors, (seed,cols,rows,errors[:5])
        sim=simulate_progression(world)
        assert sim["final_sector_reachable"]
        assert sim["all_sectors_reachable"]
        cases += 1

print(f"PixelGen v0.6 fuzz passed: {cases} gameplay worlds")
