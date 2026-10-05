from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.territory_integrity import validate_territory_graph
from pixelgen.ebe_bridge import build_ebe_seed_bundle
from pixelgen.progression import simulate_progression
from pixelgen.fingerprint import world_fingerprint
from pixelgen.territory_render import render_territory_map

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

world=generate_gameplay_world(profile,7301,6,5,4)
assert world["generator"]["version"].startswith(("0.7.","0.8.","0.9.","1.0."))
assert world["schema_versions"]["territory_graph"]=="0.7.5"
assert validate_territory_graph(world)==[]

graph=world["territory_graph"]
topo=world["influence_topology"]

# Dominated sectors are partitioned exactly into connected same-alignment territories.
dominated={
    (s["sx"],s["sy"])
    for s in topo["sectors"]
    if s["status"]=="dominated"
}
covered={
    tuple(c)
    for t in graph["territories"]
    for c in t["sectors"]
}
assert covered==dominated
assert len(graph["territories"])>=3
assert len(graph["front_sites"])==topo["summary"]["front_count"]

# Event seed accounting is deterministic and structurally meaningful.
large_territories=sum(t["sector_count"]>=2 for t in graph["territories"])
contested=topo["summary"]["status_counts"].get("contested",0)
expected=3*len(graph["front_sites"])+large_territories+contested
assert len(graph["event_seeds"])==expected

kinds=graph["summary"]["event_kind_counts"]
assert kinds["front_observation"]==len(graph["front_sites"])
assert kinds["front_rumor"]==len(graph["front_sites"])
assert kinds["border_encounter"]==len(graph["front_sites"])
assert kinds["contested_observation"]==contested
assert kinds["territory_presence"]==large_territories

# Local scenes get lookup-ready context without needing global scans at runtime.
for sector in world["sectors"]:
    pos=(sector["sx"],sector["sy"])
    local=sector["scene"]["geography"]["territory"]
    if pos in dominated:
        assert local["territory_id"] is not None
        assert local["alignment"] is not None
    else:
        assert local["territory_id"] is None

# EBE bridge is a deterministic semantic handoff, not a runtime mutation engine.
bridge=build_ebe_seed_bundle(world)
assert bridge["version"]=="0.7.5"
assert bridge["contract"]["runtime_mutation"]=="not performed by PixelGen"
assert len(bridge["events"])==len(graph["event_seeds"])
assert len(bridge["entities"])==len(graph["territories"])+len(topo["fronts"])
assert all(e["state"]=="seeded" for e in bridge["events"])
assert all(e["observability"]=="local_or_transmitted" for e in bridge["events"])

# Minimal zero-source world has no false territories/events.
tiny=generate_gameplay_world(profile,-777,1,1,0)
assert tiny["territory_graph"]["summary"]["territory_count"]==0
assert tiny["territory_graph"]["summary"]["front_site_count"]==0
assert tiny["territory_graph"]["summary"]["event_seed_count"]==0
assert build_ebe_seed_bundle(tiny)["events"]==[]

# Deterministic identity and visualization.
world2=generate_gameplay_world(profile,7301,6,5,4)
assert world_fingerprint(world)==world_fingerprint(world2)
a=render_territory_map(world,profile)
b=render_territory_map(world2,profile)
assert a.tobytes()==b.tobytes()

sim=simulate_progression(world)
assert sim["final_sector_reachable"]
assert sim["all_sectors_reachable"]

print("PixelGen v0.7.5 territory graph / event seed tests passed")
