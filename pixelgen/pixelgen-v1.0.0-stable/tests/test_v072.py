from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.biomes import biome_names
from pixelgen.geography import SUBBIOMES
from pixelgen.scene_biome import generate_biome_scene
from pixelgen.scene_structure import structural_signature
from pixelgen.structural_integrity import validate_structural_grammar
from pixelgen.structural_report import analyze_structural_grammar
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.progression import simulate_progression
from pixelgen.fingerprint import world_fingerprint

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

# Each ordinary subbiome gets a stable variant identity and at least some
# structural diversity exists within every parent biome.
for bi,biome in enumerate(biome_names()):
    signatures=[]
    variants=[]
    for zone in ("core","mid","margin"):
        for i,sub in enumerate(SUBBIOMES[biome][zone]):
            ctx={
                "region_id":0,
                "region_name":"Test",
                "primary_biome":biome,
                "subbiome":sub,
                "zone":zone,
                "distance_to_region_center":i,
                "transition":False,
                "transition_to":None,
                "transition_edges":[],
                "fields":{"moisture":0.5,"elevation":0.5,"settlement":0.5},
                "modifiers":{"hazard_mult":1.0,"prop_mult":1.0,"encounter_mult":1.0},
            }
            scene=generate_biome_scene(
                profile,7200+bi*100+i+len(signatures)*7,
                biome,landmark_plan=[],geography_context=ctx
            )
            sig=structural_signature(scene)
            signatures.append(
                (sig["path_cells"],sig["junctions"],sig["turn_like_cells"],sig["loop_rank"])
            )
            variants.append(sig["variant_id"])
            assert sig["components"]==1
            assert sig["variant_id"].endswith(f":{sub}:{zone}")
            assert sig["ecotone_adapters"]==0

    assert len(set(variants))==6
    assert len(set(signatures))>=3, (biome,signatures)

# An ecotone receives a real adapter that reaches the declared world edge.
ctx={
    "region_id":0,
    "region_name":"Test",
    "primary_biome":"dark_forest",
    "subbiome":"wet_forest_ecotone",
    "zone":"margin",
    "distance_to_region_center":4,
    "transition":True,
    "transition_to":"silt_marsh",
    "transition_edges":[{"edge":"E","region_id":1,"biome":"silt_marsh"}],
    "fields":{"moisture":0.7,"elevation":0.4,"settlement":0.2},
    "modifiers":{"hazard_mult":1.0,"prop_mult":1.0,"encounter_mult":1.0},
}
scene=generate_biome_scene(
    profile,7299,"dark_forest",landmark_plan=[],geography_context=ctx
)
meta=scene["structural_grammar"]
assert len(meta["ecotone_adapters"])==1
adapter=meta["ecotone_adapters"][0]
assert adapter["edge"]=="E"
assert adapter["neighbor_biome"]=="silt_marsh"
assert any(cell[0]==scene["width"]-1 for cell in adapter["path_cells"])
assert all(scene["ground"][y][x]=="path" for x,y in adapter["path_cells"])

# Full regional world contract.
world=generate_gameplay_world(profile,7000,6,5,4)
assert world["generator"]["version"].startswith(("0.7.","0.8.","0.9.","1.0."))
assert world["schema_versions"]["structural_grammar"].startswith("0.7.")
assert validate_structural_grammar(world)==[]

report=analyze_structural_grammar(world)
assert report["status"]=="pass"
assert report["score"]==100
assert report["distinct_variant_ids"]>=6
assert report["ecotone_adapters"]>0

# Every declared transition edge has one structural adapter.
for sector in world["sectors"]:
    geo=sector["scene"]["geography"]
    meta=sector["scene"]["structural_grammar"]
    assert len(meta["ecotone_adapters"])==len(geo.get("transition_edges",[]))

sim=simulate_progression(world)
assert sim["final_sector_reachable"]
assert sim["all_sectors_reachable"]

world2=generate_gameplay_world(profile,7000,6,5,4)
assert world_fingerprint(world)==world_fingerprint(world2)

print("PixelGen v0.7.2 subbiome/ecotone structural variation tests passed")
