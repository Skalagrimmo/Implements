from pathlib import Path
import sys, json

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.biomes import biome_names
from pixelgen.scene_biome import generate_biome_scene
from pixelgen.encounters import generate_encounters, generate_finds
from pixelgen.pockets import insert_hollow
from pixelgen.world import generate_world
from pixelgen.world_render import render_world
from pixelgen.world_export import export_world_json, export_world_lua

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

assert len(biome_names()) == 5

for idx,biome in enumerate(biome_names()):
    seed=5050+idx*1000
    scene=generate_biome_scene(profile,seed,biome)
    generate_encounters(scene,biome,seed)
    generate_finds(scene,biome,seed)
    insert_hollow(scene,seed,chance=1.0)
    assert scene["width"]==20 and scene["height"]==15
    assert len(scene["encounters"]) >= 1
    assert len(scene["finds"]) >= 2
    assert len(scene["hollows"]) == 1
    # encounters must spawn on walkable cells
    for e in scene["encounters"]:
        assert scene["collision"][e["y"]][e["x"]] == "walk"
    # deterministic
    scene2=generate_biome_scene(profile,seed,biome)
    generate_encounters(scene2,biome,seed)
    generate_finds(scene2,biome,seed)
    insert_hollow(scene2,seed,chance=1.0)
    assert json.dumps(scene["ground"],sort_keys=True)==json.dumps(scene2["ground"],sort_keys=True)
    assert json.dumps(scene["encounters"],sort_keys=True)==json.dumps(scene2["encounters"],sort_keys=True)

world=generate_world(profile,seed=5050,cols=3,rows=3)
assert len(world["sectors"]) == 9

# all reciprocal links exist
lookup={(s["sx"],s["sy"]):s for s in world["sectors"]}
for s in world["sectors"]:
    for edge,link in s["links"].items():
        tx,ty=link["to"]
        other=lookup[(tx,ty)]
        opposite={"N":"S","S":"N","E":"W","W":"E"}[edge]
        assert opposite in other["links"]
        assert other["links"][opposite]["to"] == [s["sx"],s["sy"]]
        assert other["links"][opposite]["coord"] == link["coord"]

img=render_world(world,profile,gap=4)
expected_w=3*(20*16)+2*4
expected_h=3*(15*16)+2*4
assert img.size==(expected_w,expected_h)

out=ROOT/"generated"/"_test_v05"
out.mkdir(parents=True,exist_ok=True)
assert export_world_json(world,out/"world.json").exists()
assert export_world_lua(world,out/"world.lua").exists()

print("PixelGen v0.5 tests passed")
