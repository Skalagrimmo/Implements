from pathlib import Path
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.terrain import generate_terrain
from pixelgen.autotile47 import canonical_masks_47, generate_transition47
from pixelgen.silt import generate_silt_overlay
from pixelgen.validate import validate_tile

profile = load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

# 1) canonical 47-mask topology
masks = canonical_masks_47()
assert len(masks) == 47
assert len(set(masks)) == 47

# 2) deterministic pixels
a = generate_terrain("peat", profile, seed=777, variant_index=3)
b = generate_terrain("peat", profile, seed=777, variant_index=3)
assert list(a.get_flattened_data()) == list(b.get_flattened_data())

# 3) seamless opposite edges for base terrain
for material in ("peat","pine","chapel","water","ice"):
    img = generate_terrain(material, profile, seed=100, variant_index=1)
    w,h=img.size
    assert [img.getpixel((0,y)) for y in range(h)] == [img.getpixel((w-1,y)) for y in range(h)]
    assert [img.getpixel((x,0)) for x in range(w)] == [img.getpixel((x,h-1)) for x in range(w)]

# 4) floor contrast
peat = generate_terrain("peat", profile, seed=42, variant_index=0)
result = validate_tile(peat, profile, floor=True)
assert result["ok"], result

# 5) Silt glow cap
for i in range(32):
    s = generate_silt_overlay(profile, seed=52, variant_index=i, density=0.30)
    result = validate_tile(s, profile, floor=False)
    assert result["nano_glow_coverage"] <= profile["rules"]["nano_glow_max_coverage"]

# 6) all 47 transitions are generated at proper size
for mask in masks:
    img = generate_transition47("peat","water",profile,seed=60,mask=mask)
    assert img.size == (16,16)

print("PixelGen v0.2 tests passed")
