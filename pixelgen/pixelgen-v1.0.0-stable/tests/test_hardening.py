import json
from pathlib import Path
import tempfile
import pytest
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

from pixelgen.palette import load_profile
from pixelgen.terrain import generate_terrain
from pixelgen.silt import generate_silt_overlay
from pixelgen.decals import moss_overlay, paper_wax_overlay
from pixelgen.autotile import generate_transition
from pixelgen.autotile47 import canonical_masks_47, generate_transition47
from pixelgen.structures import generate_cliff, generate_timber_wall
from pixelgen.props import generate_prop
from pixelgen.scene import generate_scene
from pixelgen.scene_biome import generate_biome_scene
from pixelgen.biomes import biome_names, weighted_choice
from pixelgen.pockets import insert_hollow
from pixelgen.encounters import generate_encounters, generate_finds
from pixelgen.world import generate_world
from pixelgen.world_render import render_world
from pixelgen.scene_export import export_scene_json, export_scene_lua, export_scene_tiled_like
from pixelgen.world_export import export_world_json, export_world_lua
from pixelgen.export import make_atlas, make_preview
from pixelgen.integrity import validate_scene_integrity, validate_world_integrity
from pixelgen.serialization import lua_quote, lua_serialize
from pixelgen.rng import SeededRNG

PROFILE=load_profile(ROOT/'profiles/techno_animist_gothic.json')


def test_profile_contract_is_explicitly_16px():
    assert PROFILE['tile_size']==16
    bad=json.loads((ROOT/'profiles/techno_animist_gothic.json').read_text())
    bad['tile_size']=8
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'bad.json'; p.write_text(json.dumps(bad))
        with pytest.raises(ValueError): load_profile(p)


def test_public_generation_rejects_bad_parameters():
    with pytest.raises(TypeError): generate_terrain('peat',PROFILE,seed=1.5)
    with pytest.raises(ValueError): generate_silt_overlay(PROFILE,density=1.01)
    with pytest.raises(ValueError): moss_overlay(PROFILE,density=-0.01)
    with pytest.raises(ValueError): generate_transition('peat','water',PROFILE,mask=16)
    with pytest.raises(ValueError): generate_transition47('peat','water',PROFILE,mask=2)  # diagonal without cardinals is noncanonical
    with pytest.raises(ValueError): generate_cliff(PROFILE,variant='wat')
    with pytest.raises(ValueError): generate_timber_wall(PROFILE,variant='wat')
    with pytest.raises(ValueError): generate_prop(PROFILE,kind='wat')
    with pytest.raises(ValueError): generate_scene(PROFILE,kind='wat')
    with pytest.raises(ValueError): insert_hollow(generate_biome_scene(PROFILE,1,'silt_marsh'),1,chance=1.2)


def test_weighted_choice_rejects_broken_tables():
    rng=SeededRNG(1)
    with pytest.raises(ValueError): weighted_choice(rng,[])
    with pytest.raises(ValueError): weighted_choice(rng,[('x',-1)])
    with pytest.raises(ValueError): weighted_choice(rng,[('x',0),('y',0)])


def test_47_mask_contract():
    masks=canonical_masks_47()
    assert len(masks)==47 and len(set(masks))==47
    for mask in masks:
        assert generate_transition47('peat','water',PROFILE,seed=-123,mask=mask).size==(16,16)


def test_determinism_extreme_seeds():
    for seed in (-10**12,-1,0,1,10**12):
        a=generate_terrain('peat',PROFILE,seed=seed,variant_index=7)
        b=generate_terrain('peat',PROFILE,seed=seed,variant_index=7)
        assert a.tobytes()==b.tobytes()
        a=generate_silt_overlay(PROFILE,seed=seed,variant_index=7,density=0.3)
        b=generate_silt_overlay(PROFILE,seed=seed,variant_index=7,density=0.3)
        assert a.tobytes()==b.tobytes()


def test_preview_atlas_are_idempotent_and_ignore_themselves(tmp_path):
    for i in range(5): generate_terrain('peat',PROFILE,seed=i).save(tmp_path/f't{i}.png')
    a1=make_atlas(tmp_path,columns=3); size1=Image.open(a1).size
    p1=make_preview(tmp_path,scale=2,columns=3); psize1=Image.open(p1).size
    a2=make_atlas(tmp_path,columns=3); size2=Image.open(a2).size
    p2=make_preview(tmp_path,scale=2,columns=3); psize2=Image.open(p2).size
    assert size1==size2 and psize1==psize2


def test_lua_serializer_escapes_and_preserves_array_length_semantics():
    quoted=lua_quote('a"b\\c\nline')
    assert quoted=='"a\\"b\\\\c\\nline"'
    text=lua_serialize([1,None,3])
    assert 'nil' not in text and '0' in text


def _complete_biome(seed,biome,chance=1.0):
    scene=generate_biome_scene(PROFILE,seed,biome)
    insert_hollow(scene,seed,chance=chance)
    generate_encounters(scene,biome,seed)
    generate_finds(scene,biome,seed)
    return scene


def test_all_biomes_integrity_across_seed_sample():
    for biome in biome_names():
        for seed in list(range(-20,30))+[999999999]:
            scene=_complete_biome(seed,biome,chance=(abs(seed)%5)/4)
            assert validate_scene_integrity(scene)==[]
            sx,sy=scene['spawn']['x'],scene['spawn']['y']
            assert scene['collision'][sy][sx]=='walk'


def test_legacy_scene_integrity_sample():
    for seed in range(-25,75):
        assert validate_scene_integrity(generate_scene(PROFILE,seed))==[]


def test_hollow_never_accidentally_overlaps_entities():
    for seed in range(100):
        scene=_complete_biome(seed,'silt_marsh',chance=1.0)
        entity={(e['x'],e['y']) for e in scene['encounters']}|{(f['x'],f['y']) for f in scene['finds']}
        for h in scene['hollows']:
            cells={(x,y) for y in range(h['y'],h['y']+h['h']) for x in range(h['x'],h['x']+h['w'])}
            assert not cells & entity


def test_scene_exports_are_complete_and_roundtrip_json(tmp_path):
    scene=_complete_biome(5050,'silt_marsh',1.0)
    # exercise escaping in a real object note
    scene['objects'][0].note='quote " slash \\ newline\n'
    jp=export_scene_json(scene,tmp_path/'deep'/'scene.json')
    lp=export_scene_lua(scene,tmp_path/'deep'/'scene.lua')
    tp=export_scene_tiled_like(scene,tmp_path/'deep'/'scene.tiled.json')
    data=json.loads(jp.read_text())
    assert all(k in data for k in ('encounters','finds','hollows','collision','objects','tile_ids'))
    assert len(data['encounters'])==len(scene['encounters'])
    tiled=json.loads(tp.read_text())
    assert [x['name'] for x in tiled['layers']]==['ground','overlay','collision','entities']
    lua=lp.read_text()
    assert 'encounters' in lua and 'hollows' in lua and '\\n' in lua and 'nil' not in lua


def test_world_dimensions_and_cycles_are_defensive():
    for dims in ((0,1),(1,0),(-1,2),(13,1),(1,13)):
        with pytest.raises((ValueError,TypeError)): generate_world(PROFILE,1,*dims)
    with pytest.raises(ValueError): generate_world(PROFILE,1,2,2,biome_cycle=[])
    with pytest.raises(ValueError): generate_world(PROFILE,1,2,2,biome_cycle=['not_a_biome'])
    w=generate_world(PROFILE,-5,2,2,biome_cycle=['dark_forest'])
    assert {s['biome'] for s in w['sectors']}=={'dark_forest'}


def test_world_integrity_and_reachability_matrix():
    for seed in (-50,-1,0,1,37,44,53,110,144,999999):
        for cols,rows in ((1,1),(1,5),(5,1),(2,2),(3,3),(4,3)):
            world=generate_world(PROFILE,seed,cols,rows)
            assert validate_world_integrity(world)==[]


def test_world_exports_are_full_not_metadata_only(tmp_path):
    world=generate_world(PROFILE,5050,2,2)
    jp=export_world_json(world,tmp_path/'w.json'); lp=export_world_lua(world,tmp_path/'w.lua')
    data=json.loads(jp.read_text())
    scene=data['sectors'][0]['scene']
    assert all(k in scene for k in ('ground','collision','encounters','finds','hollows','objects'))
    lua=lp.read_text()
    assert 'ground' in lua and 'encounters' in lua and 'finds' in lua and 'links' in lua


def test_world_render_safety_limit():
    fake={'sector_width':10000,'sector_height':10000,'cols':1,'rows':1,'sectors':[]}
    with pytest.raises(ValueError): render_world(fake,PROFILE,gap=0)
