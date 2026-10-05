from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.territory_integrity import validate_territory_graph
from pixelgen.topology_integrity import validate_influence_topology
from pixelgen.gameplay_integrity import validate_gameplay_integrity
from pixelgen.progression import simulate_progression

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")
dims=[(1,1),(2,2),(3,3),(4,3),(6,5)]
cases=0
for seed in range(-15,25):
    for cols,rows in dims:
        w=generate_gameplay_world(profile,seed,cols,rows,4)
        assert validate_territory_graph(w)==[], (seed,cols,rows)
        assert validate_influence_topology(w)==[]
        assert validate_gameplay_integrity(w)==[]
        sim=simulate_progression(w)
        assert sim["final_sector_reachable"] and sim["all_sectors_reachable"]
        cases+=1

print(f"PixelGen v0.7.5 territory fuzz passed: {cases} worlds")
