from pathlib import Path
import sys, json, hashlib, tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.scene import generate_scene, scene_summary, tile_id_grid
from pixelgen.scene_render import render_scene
from pixelgen.scene_export import export_scene_json, export_scene_lua, export_scene_tiled_like

profile = load_profile(ROOT / "profiles" / "techno_animist_gothic.json")

scene = generate_scene(profile, seed=4040, kind="silt_marsh")
assert scene["width"] == 20 and scene["height"] == 15
assert scene["tile_size"] == 16
assert scene["spawn"]["x"] == 2 and scene["spawn"]["y"] == 12
assert scene["enemy_spawn"]["kind"] == "striga"
assert "bog" in scene["landmarks"]
assert "nanolith_shrine" in scene["landmarks"]
assert any((o.kind if hasattr(o,"kind") else o["kind"]) == "printing_press_altar" for o in scene["objects"])

# Water and path both present
tiles = [v for row in scene["ground"] for v in row]
assert "water" in tiles
assert "path" in tiles

# Determinism
scene2 = generate_scene(profile, seed=4040, kind="silt_marsh")
assert json.dumps(scene_summary(scene), sort_keys=True) == json.dumps(scene_summary(scene2), sort_keys=True)
assert json.dumps(scene["ground"], sort_keys=True) == json.dumps(scene2["ground"], sort_keys=True)

# Rendering
img = render_scene(scene, profile)
assert img.size == (20 * 16, 15 * 16)

# Exports
tmp = ROOT / "generated" / "_test_exports"
tmp.mkdir(parents=True, exist_ok=True)
jp = export_scene_json(scene, tmp / "scene.json")
lp = export_scene_lua(scene, tmp / "scene.lua")
tp = export_scene_tiled_like(scene, tmp / "scene.tiled.json")
assert jp.exists() and lp.exists() and tp.exists()

# Tile-id grids same dimensions
g = tile_id_grid(scene, "ground")
assert len(g) == 15 and len(g[0]) == 20

print("PixelGen v0.4 tests passed")
