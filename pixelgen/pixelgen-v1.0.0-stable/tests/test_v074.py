from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.influence_topology import classify_influence
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.topology_integrity import validate_influence_topology
from pixelgen.progression import simulate_progression
from pixelgen.fingerprint import world_fingerprint
from pixelgen.topology_render import render_topology_map

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

# Classification contract.
neutral=classify_influence({
    "print_civic":0.10,
    "silt_contamination":0.18,
    "nano_signal":0.05,
})
assert neutral["status"]=="neutral"
assert neutral["alignment"] is None

contested=classify_influence({
    "print_civic":0.42,
    "silt_contamination":0.39,
    "nano_signal":0.10,
})
assert contested["status"]=="contested"
assert contested["contest_pair"]==["print_civic","silt_contamination"]

dominated=classify_influence({
    "print_civic":0.68,
    "silt_contamination":0.24,
    "nano_signal":0.11,
})
assert dominated["status"]=="dominated"
assert dominated["alignment"]=="print_civic"

# Canonical mixed field.
world=generate_gameplay_world(profile,7301,6,5,4)
assert world["generator"]["version"].startswith(("0.7.","0.8.","0.9.","1.0."))
assert world["schema_versions"]["influence_topology"]=="0.7.4"
assert validate_influence_topology(world)==[]

topo=world["influence_topology"]
counts=topo["summary"]["status_counts"]
assert sum(counts.values())==30
assert counts.get("neutral",0)>=1
assert counts.get("contested",0)>=1
assert counts.get("dominated",0)>=1
assert topo["summary"]["front_count"]>=1
assert len(topo["boundary_edges"])>=topo["summary"]["front_count"]

# Raw influence can cover the whole map while topology still distinguishes weak
# and contested sectors.
affected=sum(
    s["dominant_channel"] is not None
    for s in world["regional_influence"]["sectors"]
)
assert affected==30
assert counts.get("neutral",0)+counts.get("contested",0)>0

# Every local scene receives the derived topology.
world_lookup={(s["sx"],s["sy"]):s for s in world["sectors"]}
for item in topo["sectors"]:
    pos=(item["sx"],item["sy"])
    local=world_lookup[pos]["scene"]["geography"]["regional_influence"]["topology"]
    assert local["status"]==item["status"]
    assert local["front_ids"]==item["front_ids"]

# Fronts are true adjacency boundaries between different non-neutral alignments.
lookup={(s["sx"],s["sy"]):s for s in topo["sectors"]}
for front in topo["fronts"]:
    assert front["edge_count"]==len(front["edges"])
    assert front["sector_count"]==len(front["sectors"])
    assert front["mean_pressure"]>=0
    for edge in front["edges"]:
        a=tuple(edge["a"]); b=tuple(edge["b"])
        assert abs(a[0]-b[0])+abs(a[1]-b[1])==1
        aa=lookup[a]["alignment"]
        bb=lookup[b]["alignment"]
        assert aa is not None and bb is not None and aa!=bb
        assert sorted((aa,bb))==front["pair"]

# Zero-source/minimal world is a neutral topology with no fronts.
tiny=generate_gameplay_world(profile,-777,1,1,0)
tt=tiny["influence_topology"]
assert tt["summary"]["status_counts"]=={"neutral":1}
assert tt["summary"]["front_count"]==0
assert tt["boundary_edges"]==[]

# Topology is fingerprinted and rendered deterministically.
world2=generate_gameplay_world(profile,7301,6,5,4)
assert world_fingerprint(world)==world_fingerprint(world2)
a=render_topology_map(world,profile)
b=render_topology_map(world2,profile)
assert a.tobytes()==b.tobytes()

sim=simulate_progression(world)
assert sim["final_sector_reachable"]
assert sim["all_sectors_reachable"]

print("PixelGen v0.7.4 influence topology tests passed")
