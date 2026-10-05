from pathlib import Path
import sys, json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.gameplay_integrity import validate_gameplay_integrity
from pixelgen.progression import simulate_progression
from pixelgen.gameplay_export import export_gameplay_json, export_gameplay_lua, export_progression_json, export_progression_dot
from pixelgen.world_render import render_world

profile = load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

world = generate_gameplay_world(profile, seed=6060, cols=4, rows=3, ability_count=4)
assert world["gameplay"]["version"] == "0.6"
assert validate_gameplay_integrity(world) == []

sim = simulate_progression(world)
assert sim["final_sector_reachable"]
assert sim["all_sectors_reachable"]
assert set(sim["abilities"]) == set(world["gameplay"]["ability_order"])

# Every public ability is placed at most once.
pickups = []
for s in world["sectors"]:
    pickups.extend(s["scene"].get("ability_pickups",[]))
ids = [p["ability"] for p in pickups]
assert len(ids) == len(set(ids))

# Reciprocal gameplay metadata.
lookup={(s["sx"],s["sy"]):s for s in world["sectors"]}
opp={"N":"S","S":"N","E":"W","W":"E"}
for s in world["sectors"]:
    for edge, link in s["links"].items():
        dst=tuple(link["to"])
        assert lookup[dst]["links"][opp[edge]]["gameplay"] == link["gameplay"]

# Determinism.
world2 = generate_gameplay_world(profile, seed=6060, cols=4, rows=3, ability_count=4)
assert json.dumps(world["gameplay"], sort_keys=True) == json.dumps(world2["gameplay"], sort_keys=True)

# Small worlds degrade ability count safely instead of softlocking.
tiny = generate_gameplay_world(profile, seed=7, cols=1, rows=1, ability_count=4)
assert tiny["gameplay"]["effective_ability_count"] == 0
assert validate_gameplay_integrity(tiny) == []

# Rendering and exports.
img = render_world(world,profile,gap=4)
assert img.size[0] > 0 and img.size[1] > 0

out = ROOT/"generated"/"_test_v06"
out.mkdir(parents=True,exist_ok=True)
assert export_gameplay_json(world,out/"world.json").exists()
assert export_gameplay_lua(world,out/"world.lua").exists()
assert export_progression_json(world,out/"progression.json").exists()
assert export_progression_dot(world,out/"progression.dot").exists()

print("PixelGen v0.6 tests passed")
