from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.biomes import biome_names
from pixelgen.scene_biome import generate_biome_scene
from pixelgen.scene_structure import STYLE_BY_BIOME, structural_signature
from pixelgen.structural_integrity import validate_structural_grammar
from pixelgen.structural_report import analyze_structural_grammar
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.progression import simulate_progression
from pixelgen.scene_render import render_scene
from pixelgen.fingerprint import world_fingerprint

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

expected_ids={
    "silt_marsh":"meandering_causeways",
    "dark_forest":"root_branch_network",
    "frozen_pass":"ridge_zigzag",
    "ruined_settlement":"street_grid",
    "reformed_chapel":"axial_cloister",
}
expected_visuals={
    "silt_marsh":"peat",
    "dark_forest":"pine",
    "frozen_pass":"ice",
    "ruined_settlement":"chapel",
    "reformed_chapel":"chapel",
}

signatures={}
renders={}
for i,biome in enumerate(biome_names()):
    scene=generate_biome_scene(profile,7100+i,biome,landmark_plan=[])
    sig=structural_signature(scene)
    signatures[biome]=sig
    renders[biome]=render_scene(scene,profile)
    assert sig["grammar_id"]==expected_ids[biome]
    assert sig["path_visual"]==expected_visuals[biome]
    assert sig["components"]==1
    assert sig["path_cells"]>=8

# Explicit morphology contracts.
assert signatures["silt_marsh"]["junctions"] <= 4
assert signatures["silt_marsh"]["loop_rank"] <= 1
assert signatures["dark_forest"]["junctions"] >= 4
assert signatures["dark_forest"]["endpoints"] >= 3
assert signatures["frozen_pass"]["junctions"] <= 4
assert signatures["frozen_pass"]["turn_like_cells"] >= 4
assert signatures["ruined_settlement"]["loop_rank"] >= 2
assert signatures["ruined_settlement"]["junctions"] >= 6
assert signatures["reformed_chapel"]["loop_rank"] >= 1

# Different biome skeletons/renderings should not collapse to the same output.
assert len({tuple(sorted(s.items())) for s in signatures.values()})==5
assert renders["dark_forest"].tobytes()!=renders["ruined_settlement"].tobytes()
assert renders["frozen_pass"].tobytes()!=renders["reformed_chapel"].tobytes()

world=generate_gameplay_world(profile,7000,6,5,4)
assert world["generator"]["version"].startswith(("0.7.","0.8.","0.9.","1.0."))
assert world["schema_versions"]["structural_grammar"].startswith("0.7.")
assert validate_structural_grammar(world)==[]
report=analyze_structural_grammar(world)
assert report["status"]=="pass"
assert report["score"]==100

sim=simulate_progression(world)
assert sim["final_sector_reachable"]
assert sim["all_sectors_reachable"]

# Same seed remains deterministic with structural grammar included in fingerprint.
world2=generate_gameplay_world(profile,7000,6,5,4)
assert world_fingerprint(world)==world_fingerprint(world2)

print("PixelGen v0.7.1 biome structural grammar tests passed")
