from pathlib import Path
import sys, json

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.structures import (
    generate_cliff, generate_timber_wall,
    generate_nanolith_shrine, generate_printing_press_altar, generate_mask_cross
)
from pixelgen.props import generate_prop
from pixelgen.metadata import combined_manifest

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

# Structural dimensions.
assert generate_cliff(profile,1,"straight").size == (16,48)
assert generate_cliff(profile,1,"corner_inner").size == (32,48)
assert generate_timber_wall(profile,1,"doorway").size == (48,48)
assert generate_nanolith_shrine(profile,1).size == (48,64)
assert generate_printing_press_altar(profile,1).size == (64,64)
assert generate_mask_cross(profile,1).size == (32,64)

# Determinism.
a=generate_nanolith_shrine(profile,777)
b=generate_nanolith_shrine(profile,777)
assert list(a.get_flattened_data()) == list(b.get_flattened_data())

# Props and expected sizes.
expected = {
    "brazier_lit":(16,32),
    "brazier_off":(16,32),
    "paper_stack":(16,16),
    "chest":(32,32),
    "nano_capsule_broken":(32,32),
    "skull_stake_a":(16,32),
    "skull_stake_b":(16,32),
    "biogel_barrel":(16,32),
    "biogel_barrel_leaking":(32,32),
    "ritual_mask":(16,16),
    "warning_board":(32,32),
    "silt_growth":(16,16),
}
for kind,size in expected.items():
    assert generate_prop(profile,123,kind).size == size, kind

manifest=combined_manifest()
assert "structures" in manifest and "props" in manifest
assert manifest["structures"]["nanolith_shrine"]["footprint"] == [48,32]
assert manifest["structures"]["wall_doorway"]["collision"] == "portal"
assert manifest["props"]["silt_growth"]["collision"] == "hazard"

print("PixelGen v0.3 tests passed")
