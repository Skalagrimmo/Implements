"""Deterministic stress/fuzz matrix for PixelGen v0.5 Hardened.
Run manually: python tests/fuzz_hardening.py
"""
from pathlib import Path
import sys,time,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pixelgen.palette import load_profile
from pixelgen.biomes import biome_names
from pixelgen.scene import generate_scene
from pixelgen.scene_biome import generate_biome_scene
from pixelgen.pockets import insert_hollow
from pixelgen.encounters import generate_encounters,generate_finds
from pixelgen.integrity import validate_scene_integrity,validate_world_integrity
from pixelgen.world import generate_world

P=load_profile(ROOT/'profiles/techno_animist_gothic.json')
start=time.perf_counter(); scene_count=0
for biome in biome_names():
    for seed in range(-500,1500):
        s=generate_biome_scene(P,seed,biome)
        insert_hollow(s,seed,chance=(abs(seed)%5)/4)
        generate_encounters(s,biome,seed); generate_finds(s,biome,seed)
        errors=validate_scene_integrity(s)
        if errors: raise AssertionError((biome,seed,errors[:10]))
        scene_count+=1
for seed in range(-250,750):
    errors=validate_scene_integrity(generate_scene(P,seed))
    if errors: raise AssertionError(('legacy_scene',seed,errors[:10]))
    scene_count+=1
scene_time=time.perf_counter()-start

start=time.perf_counter(); world_count=0
matrix=((1,1),(1,6),(6,1),(2,2),(3,3),(4,4),(5,3))
for seed in range(-50,51):
    for dims in matrix:
        w=generate_world(P,seed,*dims)
        errors=validate_world_integrity(w)
        if errors: raise AssertionError((seed,dims,errors[:10]))
        world_count+=1
world_time=time.perf_counter()-start

# Maximum supported topology generation (no render here).
start=time.perf_counter(); maxworld=generate_world(P,123456,12,12); max_time=time.perf_counter()-start
assert len(maxworld['sectors'])==144
assert validate_world_integrity(maxworld)==[]

print(json.dumps({
    'scene_cases':scene_count,
    'scene_seconds':round(scene_time,3),
    'world_cases':world_count,
    'world_seconds':round(world_time,3),
    'max_world_sectors':len(maxworld['sectors']),
    'max_world_generation_seconds':round(max_time,3),
    'status':'PASS',
},indent=2))
