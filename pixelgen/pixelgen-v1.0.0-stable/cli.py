#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from pixelgen.palette import load_profile
from pixelgen.terrain import generate_terrain
from pixelgen.silt import generate_silt_overlay
from pixelgen.autotile import generate_transition
from pixelgen.autotile47 import canonical_masks_47, generate_transition47
from pixelgen.decals import paper_wax_overlay, moss_overlay
from pixelgen.validate import validate_tile
from pixelgen.compose import composite
from pixelgen.structures import generate_cliff, generate_timber_wall, generate_nanolith_shrine, generate_printing_press_altar, generate_mask_cross, generate_printing_cathedral, generate_silt_spire
from pixelgen.props import generate_prop
from pixelgen.metadata import combined_manifest
from pixelgen.scene import generate_scene, scene_summary
from pixelgen.scene_render import render_scene
from pixelgen.scene_export import export_scene_json, export_scene_lua, export_scene_tiled_like
from pixelgen.biomes import biome_names
from pixelgen.scene_biome import generate_biome_scene
from pixelgen.encounters import generate_encounters, generate_finds
from pixelgen.pockets import insert_hollow
from pixelgen.world import generate_world
from pixelgen.world_render import render_world
from pixelgen.world_export import export_world_json, export_world_lua
from pixelgen.export import save_numbered, make_preview, make_atlas, ensure_dir
from pixelgen.constraints import MAX_BATCH_COUNT, MAX_PREVIEW_SCALE, MAX_ATLAS_COLUMNS, MAX_WORLD_DIM
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.gameplay_integrity import validate_gameplay_integrity
from pixelgen.progression import simulate_progression
from pixelgen.gameplay_export import export_gameplay_json, export_gameplay_lua, export_progression_json, export_progression_dot
from pixelgen.abilities import ABILITY_ORDER
from pixelgen.cognitive_map import render_cognitive_map
from pixelgen.geography_render import render_geography_map
from pixelgen.influence_render import render_influence_map
from pixelgen.topology_render import render_topology_map
from pixelgen.territory_render import render_territory_map
from pixelgen.corridor_render import render_corridor_map
from pixelgen.corridor_integrity import validate_regional_corridors
from pixelgen.territory_integrity import validate_territory_graph
from pixelgen.ebe_bridge import build_ebe_seed_bundle
from pixelgen.world_state import initialize_world_state, apply_world_event, replay_world_events, state_summary
from pixelgen.world_state_integrity import validate_world_state
from pixelgen.dynamic_ebe_bridge import build_dynamic_ebe_bundle
from pixelgen.world_state_render import render_world_state_map
from pixelgen.topology_integrity import validate_influence_topology
from pixelgen.influence_integrity import validate_influence_fields
from pixelgen.geography_integrity import validate_geography
from pixelgen.serialization import to_plain, write_lua_return
from pixelgen.landmark_integrity import validate_landmark_integrity
from pixelgen.visual_pattern import analyze_visual_patterns
from pixelgen.audit import audit_world, audit_summary
from pixelgen.seed_sweep import sweep_seeds
from pixelgen.doctor import run_doctor
from pixelgen.fingerprint import world_fingerprint
from pixelgen.inspect_world import inspect_world, inspection_text
from pixelgen.world_diff import compare_worlds, diff_text
from pixelgen.bundle_manifest import write_manifest, verify_manifest
from pixelgen.environment_journal import (
    SUITES as ENV_SUITES,
    default_log_filename,
    run_environment_log,
    write_environment_log,
    write_markdown_companion,
)
from pixelgen.structural_integrity import validate_structural_grammar
from pixelgen.structural_report import analyze_structural_grammar, structural_report_text
from pixelgen.structure_showcase import build_structure_showcase
from pixelgen.subbiome_showcase import build_subbiome_showcase
from pixelgen.environment_compare import (
    compare_logs as compare_environment_logs,
    comparison_markdown as environment_comparison_markdown,
    comparison_text as environment_comparison_text,
    comparison_csv as environment_comparison_csv,
    load_environment_log,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_PROFILE = ROOT / "profiles" / "techno_animist_gothic.json"

def _bounded_int(name, minimum, maximum):
    def parse(value):
        try:
            iv=int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} must be an integer")
        if not minimum <= iv <= maximum:
            raise argparse.ArgumentTypeError(f"{name} must be between {minimum} and {maximum}")
        return iv
    return parse

def _probability(value):
    try:
        fv=float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("value must be a number in [0, 1]")
    if not 0.0 <= fv <= 1.0:
        raise argparse.ArgumentTypeError("value must be in [0, 1]")
    return fv

COUNT = _bounded_int("count", 1, MAX_BATCH_COUNT)
POSITIVE = _bounded_int("value", 1, MAX_BATCH_COUNT)
SCALE = _bounded_int("scale", 1, MAX_PREVIEW_SCALE)
COLUMNS = _bounded_int("columns", 1, MAX_ATLAS_COLUMNS)
PADDING = _bounded_int("padding", 0, 1024)
WORLD_DIM = _bounded_int("world dimension", 1, MAX_WORLD_DIM)
GAP = _bounded_int("gap", 0, 256)
ABILITY_COUNT = _bounded_int("ability count", 0, len(ABILITY_ORDER))


def profile_from(args):
    return load_profile(args.profile)

def cmd_terrain(args):
    profile = profile_from(args)
    images = [generate_terrain(args.material, profile, args.seed, i) for i in range(args.count)]
    out = Path(args.out) if args.out else ROOT/"generated"/"terrain"/args.material
    save_numbered(images, out, f"tile_{args.material}")
    print(f"Generated {len(images)} {args.material} tiles -> {out}")

def cmd_silt(args):
    profile = profile_from(args)
    images = [generate_silt_overlay(profile, args.seed, i, args.density) for i in range(args.count)]
    out = Path(args.out) if args.out else ROOT/"generated"/"silt"
    save_numbered(images, out, "silt_overlay")
    print(f"Generated {len(images)} Silt overlays -> {out}")

def cmd_autotile(args):
    profile = profile_from(args)
    out = Path(args.out) if args.out else ROOT/"generated"/"autotile"/f"{args.from_material}_to_{args.to_material}"
    ensure_dir(out)
    for mask in range(16):
        img = generate_transition(args.from_material, args.to_material, profile, args.seed, mask)
        img.save(out/f"trans_{args.from_material}_to_{args.to_material}_{mask:02d}.png")
    print(f"Generated 16 transition masks -> {out}")

def cmd_preview(args):
    out = make_preview(args.folder, args.output, args.scale, args.columns)
    print(f"Preview -> {out}")

def cmd_atlas(args):
    out = make_atlas(args.folder, args.output, args.columns, args.padding)
    print(f"Atlas -> {out}")

def cmd_demo(args):
    profile = load_profile(args.profile)
    seed = args.seed
    for offset, material in enumerate(("peat","pine","chapel","water","ice")):
        out = ROOT/"generated"/"terrain"/material
        imgs = [generate_terrain(material, profile, seed+offset*1000, i) for i in range(16)]
        save_numbered(imgs, out, f"tile_{material}")
        make_preview(out, scale=8, columns=8)
        make_atlas(out, columns=8)
    out = ROOT/"generated"/"silt"
    imgs = [generate_silt_overlay(profile, seed+9000, i) for i in range(16)]
    save_numbered(imgs, out, "silt_overlay")
    make_preview(out, scale=8, columns=8)
    make_atlas(out, columns=8)
    auto = ROOT/"generated"/"autotile"/"peat_to_water"
    ensure_dir(auto)
    for mask in range(16):
        generate_transition("peat","water",profile,seed+12000,mask).save(auto/f"trans_peat_to_water_{mask:02d}.png")
    make_preview(auto, scale=8, columns=8)
    make_atlas(auto, columns=8)
    print(f"Demo generated under {ROOT/'generated'}")


def cmd_autotile47(args):
    profile = profile_from(args)
    out = Path(args.out) if args.out else ROOT/"generated"/"autotile47"/f"{args.from_material}_to_{args.to_material}"
    ensure_dir(out)
    masks = canonical_masks_47()
    for idx, mask in enumerate(masks):
        img = generate_transition47(args.from_material,args.to_material,profile,args.seed,mask)
        img.save(out/f"trans47_{idx:02d}_mask{mask:03d}.png")
    print(f"Generated {len(masks)} canonical 8-neighbor transition masks -> {out}")

def cmd_decals(args):
    profile = profile_from(args)
    out = Path(args.out) if args.out else ROOT/"generated"/"decals"/args.kind
    ensure_dir(out)
    images=[]
    for i in range(args.count):
        if args.kind=="paper":
            img=paper_wax_overlay(profile,args.seed,i)
        else:
            img=moss_overlay(profile,args.seed,i,args.density)
        images.append(img)
    save_numbered(images,out,f"decal_{args.kind}")
    print(f"Generated {len(images)} {args.kind} decals -> {out}")

def cmd_validate(args):
    profile = profile_from(args)
    from PIL import Image
    files = sorted(Path(args.folder).glob("*.png"))
    files = [p for p in files if p.name not in ("preview.png","atlas.png")]
    if not files:
        raise SystemExit(f"No PNG files in {args.folder}")
    failed=0
    for p in files:
        result=validate_tile(Image.open(p),profile,floor=args.floor)
        status="OK" if result["ok"] else "WARN"
        if not result["ok"]: failed+=1
        print(f"{status:4} {p.name:32} contrast={result['contrast_delta']:.3f} glow={result['nano_glow_coverage']:.3f} palette={result['palette_usage']:.3f}")
        for w in result["warnings"]:
            print(f"      - {w}")
    print(f"Validated {len(files)} files; warnings on {failed}")

def cmd_material_demo(args):
    profile = profile_from(args)
    out = ROOT/"generated"/"material_grammar"
    ensure_dir(out)
    materials=("peat","pine","chapel","water","ice")
    for mi,m in enumerate(materials):
        base=generate_terrain(m,profile,args.seed+mi*1000,0)
        if m in ("peat","pine"):
            ov=moss_overlay(profile,args.seed+mi*1000,0,0.16)
        elif m=="chapel":
            ov=paper_wax_overlay(profile,args.seed+mi*1000,0)
        else:
            ov=generate_silt_overlay(profile,args.seed+mi*1000,0,0.22)
        composite(base,ov).save(out/f"grammar_{m}.png")
    make_preview(out,scale=10,columns=5)
    print(f"Material grammar demo -> {out}")



def cmd_structure(args):
    profile = profile_from(args)
    out = Path(args.out) if args.out else ROOT/"generated"/"structures"/args.kind
    ensure_dir(out)
    images=[]
    for i in range(args.count):
        seed=args.seed+i*101
        if args.kind.startswith("cliff_"):
            variant=args.kind.replace("cliff_","")
            img=generate_cliff(profile,seed,variant)
        elif args.kind.startswith("wall_"):
            variant=args.kind.replace("wall_","")
            img=generate_timber_wall(profile,seed,variant)
        elif args.kind=="nanolith_shrine":
            img=generate_nanolith_shrine(profile,seed)
        elif args.kind=="printing_press_altar":
            img=generate_printing_press_altar(profile,seed)
        elif args.kind=="mask_cross":
            img=generate_mask_cross(profile,seed)
        elif args.kind=="printing_cathedral":
            img=generate_printing_cathedral(profile,seed)
        elif args.kind=="silt_spire":
            img=generate_silt_spire(profile,seed)
        else:
            raise SystemExit(f"Unknown structure kind: {args.kind}")
        images.append(img)
    save_numbered(images,out,f"struct_{args.kind}")
    print(f"Generated {len(images)} {args.kind} structure variants -> {out}")

def cmd_prop(args):
    profile = profile_from(args)
    out = Path(args.out) if args.out else ROOT/"generated"/"props"/args.kind
    images=[generate_prop(profile,args.seed+i*97,args.kind) for i in range(args.count)]
    save_numbered(images,out,f"prop_{args.kind}")
    print(f"Generated {len(images)} {args.kind} prop variants -> {out}")

def cmd_manifest(args):
    out = Path(args.out) if args.out else ROOT/"generated"/"asset_manifest.json"
    ensure_dir(out.parent)
    out.write_text(json.dumps(combined_manifest(),indent=2),encoding="utf-8")
    print(f"Manifest -> {out}")

def cmd_structure_demo(args):
    profile = profile_from(args)
    kinds=[
        "cliff_straight","cliff_corner_inner","cliff_corner_outer","cliff_broken","cliff_silt",
        "wall_straight","wall_corner_inner","wall_corner_outer","wall_broken","wall_doorway",
        "nanolith_shrine","printing_press_altar","mask_cross","printing_cathedral","silt_spire"
    ]
    for idx,kind in enumerate(kinds):
        class A: pass
        a=A(); a.profile=args.profile; a.kind=kind; a.count=3; a.seed=args.seed+idx*100; a.out=None
        cmd_structure(a)

    prop_kinds=[
        "brazier_lit","brazier_off","paper_stack","chest","nano_capsule_broken",
        "skull_stake_a","skull_stake_b","biogel_barrel","biogel_barrel_leaking",
        "ritual_mask","warning_board","silt_growth"
    ]
    for idx,kind in enumerate(prop_kinds):
        class A: pass
        a=A(); a.profile=args.profile; a.kind=kind; a.count=3; a.seed=args.seed+2000+idx*100; a.out=None
        cmd_prop(a)

    out=ROOT/"generated"/"asset_manifest.json"
    out.write_text(json.dumps(combined_manifest(),indent=2),encoding="utf-8")
    print(f"Structural demo generated under {ROOT/'generated'}")



def cmd_scene(args):
    profile = profile_from(args)
    out = Path(args.out) if args.out else ROOT/"generated"/"scenes"/args.kind
    ensure_dir(out)
    scene = generate_scene(profile, seed=args.seed, kind=args.kind)
    img = render_scene(scene, profile)
    img_path = out / f"scene_{args.kind}_seed{args.seed}.png"
    img.save(img_path)
    export_scene_json(scene, out / f"scene_{args.kind}_seed{args.seed}.json")
    export_scene_lua(scene, out / f"scene_{args.kind}_seed{args.seed}.lua")
    export_scene_tiled_like(scene, out / f"scene_{args.kind}_seed{args.seed}.tiled.json")
    (out / f"scene_{args.kind}_seed{args.seed}.summary.json").write_text(json.dumps(scene_summary(scene), indent=2), encoding="utf-8")
    print(f"Scene generated -> {img_path}")

def cmd_scene_batch(args):
    profile = profile_from(args)
    out = Path(args.out) if args.out else ROOT/"generated"/"scene_batch"/args.kind
    ensure_dir(out)
    for i in range(args.count):
        seed = args.seed + i * 97
        scene = generate_scene(profile, seed=seed, kind=args.kind)
        img = render_scene(scene, profile)
        img_path = out / f"scene_{args.kind}_{i+1:02d}_seed{seed}.png"
        img.save(img_path)
        export_scene_json(scene, out / f"scene_{args.kind}_{i+1:02d}_seed{seed}.json")
    print(f"Generated {args.count} scenes -> {out}")

def cmd_scene_demo(args):
    profile = profile_from(args)
    out = ROOT/"generated"/"scene_demo"
    ensure_dir(out)
    scene = generate_scene(profile, seed=args.seed, kind="silt_marsh")
    img = render_scene(scene, profile)
    img_path = out / "silt_marsh_vertical_slice.png"
    img.save(img_path)
    export_scene_json(scene, out / "silt_marsh_vertical_slice.json")
    export_scene_lua(scene, out / "silt_marsh_vertical_slice.lua")
    export_scene_tiled_like(scene, out / "silt_marsh_vertical_slice.tiled.json")
    (out / "silt_marsh_vertical_slice.summary.json").write_text(json.dumps(scene_summary(scene), indent=2), encoding="utf-8")
    print(f"Scene demo -> {img_path}")



def cmd_biome_scene(args):
    profile = profile_from(args)
    out = Path(args.out) if args.out else ROOT/"generated"/"biomes"/args.biome
    ensure_dir(out)
    scene = generate_biome_scene(profile,args.seed,args.biome)
    insert_hollow(scene,args.seed,chance=args.hollow_chance)
    generate_encounters(scene,args.biome,args.seed)
    generate_finds(scene,args.biome,args.seed)
    img = render_scene(scene,profile)
    base = out/f"{args.biome}_seed{args.seed}"
    img.save(str(base)+".png")
    export_scene_json(scene,str(base)+".json")
    export_scene_lua(scene,str(base)+".lua")
    export_scene_tiled_like(scene,str(base)+".tiled.json")
    print(f"Biome scene -> {base}.png")

def cmd_biome_demo(args):
    profile = profile_from(args)
    for i, biome in enumerate(biome_names()):
        out = ROOT/"generated"/"biome_demo"/biome
        ensure_dir(out)
        seed = args.seed + i*1000
        scene = generate_biome_scene(profile,seed,biome)
        insert_hollow(scene,seed,chance=0.65)
        generate_encounters(scene,biome,seed)
        generate_finds(scene,biome,seed)
        img=render_scene(scene,profile)
        img.save(out/f"{biome}.png")
        export_scene_json(scene,out/f"{biome}.json")
        export_scene_lua(scene,out/f"{biome}.lua")
    print(f"Biome demo generated under {ROOT/'generated'/'biome_demo'}")




def _export_corridors(world, base):
    if "regional_corridors" not in world:
        return
    base=Path(base)
    payload=to_plain(world["regional_corridors"])
    Path(str(base)+".corridors.json").write_text(
        json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True),
        encoding="utf-8",
    )
    write_lua_return(payload,str(base)+".corridors.lua")


def _export_territory(world, base):
    if "territory_graph" not in world:
        return
    base=Path(base)
    payload=to_plain(world["territory_graph"])
    Path(str(base)+".territory.json").write_text(
        json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True),
        encoding="utf-8",
    )
    write_lua_return(payload,str(base)+".territory.lua")



def _export_world_state(state, path_base):
    base=Path(path_base)
    base.parent.mkdir(parents=True,exist_ok=True)
    payload=to_plain(state)
    Path(str(base)+".json").write_text(
        json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True),
        encoding="utf-8",
    )
    write_lua_return(payload,str(base)+".lua")


def _export_dynamic_ebe(world, state, path_base, since_revision=0):
    base=Path(path_base)
    base.parent.mkdir(parents=True,exist_ok=True)
    payload=to_plain(build_dynamic_ebe_bundle(world,state,since_revision=since_revision))
    Path(str(base)+".json").write_text(
        json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True),
        encoding="utf-8",
    )
    write_lua_return(payload,str(base)+".lua")


def _export_ebe_seeds(world, base):
    base=Path(base)
    payload=to_plain(build_ebe_seed_bundle(world))
    Path(str(base)+".ebe-seeds.json").write_text(
        json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True),
        encoding="utf-8",
    )
    write_lua_return(payload,str(base)+".ebe-seeds.lua")


def _export_topology(world, base):
    if "influence_topology" not in world:
        return
    base=Path(base)
    payload=to_plain(world["influence_topology"])
    Path(str(base)+".topology.json").write_text(
        json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True),
        encoding="utf-8",
    )
    write_lua_return(payload,str(base)+".topology.lua")

def _export_influence(world, base):
    if "regional_influence" not in world:
        return
    base=Path(base)
    payload=to_plain(world["regional_influence"])
    Path(str(base)+".influence.json").write_text(
        json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True),
        encoding="utf-8",
    )
    write_lua_return(payload,str(base)+".influence.lua")

def _export_geography(world, base):
    if "geography" not in world:
        return
    base=Path(base)
    payload=to_plain(world["geography"])
    Path(str(base)+".geography.json").write_text(
        json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True),
        encoding="utf-8",
    )
    write_lua_return(payload,str(base)+".geography.lua")

def cmd_world(args):
    profile = profile_from(args)
    out = Path(args.out) if args.out else ROOT/"generated"/"worlds"
    ensure_dir(out)
    world = generate_world(profile,args.seed,args.cols,args.rows)
    img = render_world(world,profile,gap=args.gap)
    base = out/f"world_{args.cols}x{args.rows}_seed{args.seed}"
    img.save(str(base)+".png")
    export_world_json(world,str(base)+".json")
    export_world_lua(world,str(base)+".lua")
    render_cognitive_map(world,profile).save(str(base)+".cognitive.png")
    render_geography_map(world,profile).save(str(base)+".geography.png")
    render_influence_map(world,profile).save(str(base)+".influence.png")
    render_topology_map(world,profile).save(str(base)+".topology.png")
    render_territory_map(world,profile).save(str(base)+".territory.png")
    _export_geography(world,base)
    _export_influence(world,base)
    _export_topology(world,base)
    _export_territory(world,base)
    _export_ebe_seeds(world,base)
    _write_visual_quality(world,str(base)+".visual-quality.json")
    print(f"World -> {base}.png")
    print(f"Cognitive map -> {base}.cognitive.png")
    print(f"Geography map -> {base}.geography.png")

def cmd_world_demo(args):
    profile = profile_from(args)
    out = ROOT/"generated"/"world_demo"
    ensure_dir(out)
    world = generate_world(profile,args.seed,3,3)
    img = render_world(world,profile,gap=4)
    img.save(out/"micro_world_3x3.png")
    export_world_json(world,out/"micro_world_3x3.json")
    export_world_lua(world,out/"micro_world_3x3.lua")
    render_cognitive_map(world,profile).save(out/"micro_world_3x3.cognitive.png")
    render_geography_map(world,profile).save(out/"micro_world_3x3.geography.png")
    render_influence_map(world,profile).save(out/"micro_world_3x3.influence.png")
    render_topology_map(world,profile).save(out/"micro_world_3x3.topology.png")
    render_territory_map(world,profile).save(out/"micro_world_3x3.territory.png")
    _export_geography(world,out/"micro_world_3x3")
    _export_influence(world,out/"micro_world_3x3")
    _export_topology(world,out/"micro_world_3x3")
    _export_territory(world,out/"micro_world_3x3")
    _export_ebe_seeds(world,out/"micro_world_3x3")
    _write_visual_quality(world,out/"micro_world_3x3.visual-quality.json")
    print(f"World demo -> {out/'micro_world_3x3.png'}")
    print(f"Geography map -> {out/'micro_world_3x3.geography.png'}")



def cmd_gameplay_world(args):
    profile = profile_from(args)
    out = Path(args.out) if args.out else ROOT/"generated"/"gameplay_worlds"
    ensure_dir(out)
    world = generate_gameplay_world(profile,args.seed,args.cols,args.rows,args.ability_count)
    img = render_world(world,profile,gap=args.gap)
    base = out/f"gameplay_{args.cols}x{args.rows}_seed{args.seed}"
    img.save(str(base)+".png")
    export_gameplay_json(world,str(base)+".json")
    export_gameplay_lua(world,str(base)+".lua")
    export_progression_json(world,str(base)+".progression.json")
    export_progression_dot(world,str(base)+".progression.dot")
    render_cognitive_map(world,profile).save(str(base)+".cognitive.png")
    render_geography_map(world,profile).save(str(base)+".geography.png")
    render_influence_map(world,profile).save(str(base)+".influence.png")
    render_topology_map(world,profile).save(str(base)+".topology.png")
    render_territory_map(world,profile).save(str(base)+".territory.png")
    _export_geography(world,base)
    _export_influence(world,base)
    _export_topology(world,base)
    _export_territory(world,base)
    _export_ebe_seeds(world,base)
    _write_visual_quality(world,str(base)+".visual-quality.json")
    sim = simulate_progression(world)
    print(f"Gameplay world -> {base}.png")
    print(f"Abilities: {', '.join(world['gameplay']['ability_order']) or 'none'}")
    print(f"Progression: final={sim['final_sector_reachable']} all_sectors={sim['all_sectors_reachable']}")

def cmd_gameplay_demo(args):
    profile = profile_from(args)
    out = ROOT/"generated"/"gameplay_demo"
    ensure_dir(out)
    world = generate_gameplay_world(profile,args.seed,4,3,4)
    img = render_world(world,profile,gap=4)
    img.save(out/"navigation_gameplay_4x3.png")
    export_gameplay_json(world,out/"navigation_gameplay_4x3.json")
    export_gameplay_lua(world,out/"navigation_gameplay_4x3.lua")
    export_progression_json(world,out/"navigation_gameplay_4x3.progression.json")
    export_progression_dot(world,out/"navigation_gameplay_4x3.progression.dot")
    render_cognitive_map(world,profile).save(out/"navigation_gameplay_4x3.cognitive.png")
    render_geography_map(world,profile).save(out/"navigation_gameplay_4x3.geography.png")
    render_influence_map(world,profile).save(out/"navigation_gameplay_4x3.influence.png")
    render_topology_map(world,profile).save(out/"navigation_gameplay_4x3.topology.png")
    render_territory_map(world,profile).save(out/"navigation_gameplay_4x3.territory.png")
    _export_geography(world,out/"navigation_gameplay_4x3")
    _export_influence(world,out/"navigation_gameplay_4x3")
    _export_topology(world,out/"navigation_gameplay_4x3")
    _export_territory(world,out/"navigation_gameplay_4x3")
    _export_ebe_seeds(world,out/"navigation_gameplay_4x3")
    _write_visual_quality(world,out/"navigation_gameplay_4x3.visual-quality.json")
    print(f"Gameplay demo -> {out/'navigation_gameplay_4x3.png'}")
    print(f"Cognitive map -> {out/'navigation_gameplay_4x3.cognitive.png'}")
    print(f"Geography map -> {out/'navigation_gameplay_4x3.geography.png'}")


def cmd_geography_demo(args):
    profile=profile_from(args)
    out=Path(args.out) if args.out else ROOT/"generated"/"geography_demo"
    ensure_dir(out)
    world=generate_gameplay_world(
        profile,args.seed,args.cols,args.rows,args.ability_count
    )
    base=out/f"regional_geography_{args.cols}x{args.rows}_seed{args.seed}"
    render_world(world,profile,gap=4).save(str(base)+".png")
    render_cognitive_map(world,profile).save(str(base)+".cognitive.png")
    render_geography_map(world,profile).save(str(base)+".geography.png")
    render_influence_map(world,profile).save(str(base)+".influence.png")
    render_topology_map(world,profile).save(str(base)+".topology.png")
    render_territory_map(world,profile).save(str(base)+".territory.png")
    export_gameplay_json(world,str(base)+".json")
    export_gameplay_lua(world,str(base)+".lua")
    export_progression_json(world,str(base)+".progression.json")
    export_progression_dot(world,str(base)+".progression.dot")
    _export_geography(world,base)
    _export_influence(world,base)
    _export_topology(world,base)
    _export_territory(world,base)
    _export_ebe_seeds(world,base)

    geo=world["geography"]
    transition_sectors=sum(1 for s in geo["sectors"] if s["transition"])
    subbiomes=len({s["subbiome"] for s in geo["sectors"]})
    print(f"Geography demo -> {base}.png")
    print(f"Macro geography -> {base}.geography.png")
    print(f"Regions: {len(geo['regions'])}")
    print(f"Transition sectors: {transition_sectors}")
    print(f"Distinct subbiomes: {subbiomes}")
    for r in geo["regions"]:
        print(
            f"  R{r['id']} {r['primary_biome']}: "
            f"{r['sector_count']} sectors / {r['name']}"
        )


def cmd_influence_demo(args):
    profile=profile_from(args)
    out=Path(args.out) if args.out else ROOT/"generated"/"influence_demo"
    ensure_dir(out)
    world=generate_gameplay_world(profile,args.seed,args.cols,args.rows,args.ability_count)
    base=out/f"regional_influence_{args.cols}x{args.rows}_seed{args.seed}"
    render_world(world,profile,gap=4).save(str(base)+".png")
    render_geography_map(world,profile).save(str(base)+".geography.png")
    render_influence_map(world,profile).save(str(base)+".influence.png")
    render_topology_map(world,profile).save(str(base)+".topology.png")
    export_gameplay_json(world,str(base)+".json")
    _export_geography(world,base)
    _export_influence(world,base)
    _export_topology(world,base)
    _export_territory(world,base)
    _export_ebe_seeds(world,base)

    inf=world["regional_influence"]
    print(f"Influence demo -> {base}.influence.png")
    print(f"Sources: {len(inf['sources'])}")
    for src in inf["sources"]:
        print(
            f"  {src['kind']} / {src['channel']} "
            f"sector={src['sector']} radius={src['radius']}"
        )
    affected=sum(1 for s in inf["sectors"] if s["dominant_channel"] is not None)
    print(f"Affected sectors: {affected}/{len(inf['sectors'])}")


def cmd_topology_demo(args):
    profile=profile_from(args)
    out=Path(args.out) if args.out else ROOT/"generated"/"topology_demo"
    ensure_dir(out)
    world=generate_gameplay_world(
        profile,args.seed,args.cols,args.rows,args.ability_count
    )
    base=out/f"influence_topology_{args.cols}x{args.rows}_seed{args.seed}"
    render_world(world,profile,gap=4).save(str(base)+".png")
    render_influence_map(world,profile).save(str(base)+".influence.png")
    render_topology_map(world,profile).save(str(base)+".topology.png")
    render_territory_map(world,profile).save(str(base)+".territory.png")
    export_gameplay_json(world,str(base)+".json")
    _export_influence(world,base)
    _export_topology(world,base)
    _export_territory(world,base)
    _export_ebe_seeds(world,base)

    topo=world["influence_topology"]
    print(f"Topology demo -> {base}.topology.png")
    print("Statuses:", topo["summary"]["status_counts"])
    print(f"Fronts: {topo['summary']['front_count']}")
    for front in topo["fronts"]:
        print(
            f"  {front['id']} pair={front['pair']} "
            f"edges={front['edge_count']} "
            f"mean_pressure={front['mean_pressure']}"
        )

def cmd_territory_demo(args):
    profile=profile_from(args)
    out=Path(args.out) if args.out else ROOT/"generated"/"territory_demo"
    ensure_dir(out)
    world=generate_gameplay_world(profile,args.seed,args.cols,args.rows,args.ability_count)
    base=out/f"territory_graph_{args.cols}x{args.rows}_seed{args.seed}"
    render_world(world,profile,gap=4).save(str(base)+".png")
    render_topology_map(world,profile).save(str(base)+".topology.png")
    render_territory_map(world,profile).save(str(base)+".territory.png")
    export_gameplay_json(world,str(base)+".json")
    _export_topology(world,base)
    _export_territory(world,base)
    _export_ebe_seeds(world,base)

    graph=world["territory_graph"]
    print(f"Territory demo -> {base}.territory.png")
    print(f"Territories: {graph['summary']['territory_count']}")
    print(f"Front sites: {graph['summary']['front_site_count']}")
    print(f"Event seeds: {graph['summary']['event_seed_count']}")
    for t in graph["territories"]:
        print(f"  {t['id']} {t['alignment']} sectors={t['sector_count']} mean={t['mean_strength']}")
    print("Event kinds:", graph["summary"]["event_kind_counts"])



def cmd_corridor_demo(args):
    profile=profile_from(args)
    out=Path(args.out) if args.out else ROOT/"generated"/"corridor_demo"
    ensure_dir(out)
    world=generate_gameplay_world(
        profile,args.seed,args.cols,args.rows,args.ability_count
    )
    errors=validate_regional_corridors(world)
    if errors:
        raise RuntimeError("corridor validation failed: "+"; ".join(errors[:20]))
    base=out/f"regional_corridors_{args.cols}x{args.rows}_seed{args.seed}"
    render_world(world,profile,gap=4).save(str(base)+".png")
    render_geography_map(world,profile).save(str(base)+".geography.png")
    render_corridor_map(world,profile).save(str(base)+".corridors.png")
    export_gameplay_json(world,str(base)+".json")
    export_gameplay_lua(world,str(base)+".lua")
    _export_geography(world,base)
    _export_corridors(world,base)

    data=world["regional_corridors"]
    print(f"Corridor demo -> {base}.corridors.png")
    print(f"Corridors: {data['summary']['corridor_count']}")
    print(f"Coverage: {data['summary']['covered_sector_count']}/{args.cols*args.rows}")
    print("Kinds:",data['summary']['kind_counts'])
    for c in data["corridors"]:
        print(
            f"  {c['id']} {c['purpose']} {c['source']} -> {c['target']} "
            f"sectors={c['sector_count']}"
        )


def cmd_state_demo(args):
    profile=profile_from(args)
    out=Path(args.out) if args.out else ROOT/"generated"/"state_demo"
    ensure_dir(out)

    world=generate_gameplay_world(
        profile,args.seed,args.cols,args.rows,args.ability_count
    )
    base=out/f"dynamic_state_{args.cols}x{args.rows}_seed{args.seed}"

    # Keep the static world beside the dynamic overlay for reproducible replay.
    export_gameplay_json(world,str(base)+".world.json")

    initial=initialize_world_state(world)
    _export_world_state(initial,str(base)+".initial-state")
    render_world_state_map(world,initial).save(str(base)+".initial-state.png")

    events=[]

    # Canonical demo prefers a front because it exercises secondary territory mutation.
    front_ids=sorted(initial.get("fronts",{}))
    territory_ids=sorted(initial.get("territories",{}))

    if front_ids:
        events.append({
            "event_type":"front_escalation",
            "target_id":front_ids[0],
            "amount":args.escalation,
            "source":"state_demo",
        })

    if territory_ids:
        events.append({
            "event_type":"territory_weaken",
            "target_id":territory_ids[0],
            "amount":args.territory_delta,
            "source":"state_demo",
            "cause_id":events[0]["target_id"] if events else None,
        })

    if len(front_ids)>1:
        events.append({
            "event_type":"front_deescalation",
            "target_id":front_ids[1],
            "amount":max(0.05,args.escalation*0.45),
            "source":"state_demo",
        })

    state=initial
    for event in events:
        state=apply_world_event(world,state,event)

    errors=validate_world_state(world,state)
    if errors:
        raise RuntimeError("dynamic state failed validation: "+"; ".join(errors[:20]))

    replayed=replay_world_events(world,state["event_log"])
    if replayed != state:
        raise RuntimeError("dynamic state replay is not deterministic")

    _export_world_state(state,str(base)+".after-state")
    _export_dynamic_ebe(world,state,str(base)+".ebe-runtime")
    render_world_state_map(world,state).save(str(base)+".after-state.png")

    Path(str(base)+".events.json").write_text(
        json.dumps(state["event_log"],indent=2,ensure_ascii=False,sort_keys=True),
        encoding="utf-8",
    )
    Path(str(base)+".observations.json").write_text(
        json.dumps(state["observations"],indent=2,ensure_ascii=False,sort_keys=True),
        encoding="utf-8",
    )

    before=state_summary(initial)
    after=state_summary(state)
    print(f"Dynamic state demo -> {base}.after-state.png")
    print(f"World fingerprint: {initial['source_world']['fingerprint']}")
    print(f"Initial state: {before['fingerprint']}")
    print(f"Final state:   {after['fingerprint']}")
    print(f"Applied events: {after['events']}")
    print(f"Derived events: {after['derived_events']}")
    print(f"Local observations: {after['observations']}")
    print("Replay deterministic: True")


def cmd_state_check(args):
    world=json.loads(Path(args.world).read_text(encoding="utf-8"))
    world.pop("progression_simulation",None)
    state=json.loads(Path(args.state).read_text(encoding="utf-8"))
    errors=validate_world_state(world,state)
    if errors:
        raise RuntimeError("world-state validation failed: "+"; ".join(errors[:20]))

    print("World-state validation: PASS")
    summary=state_summary(state)
    print(f"Revision: {summary['revision']}  tick: {summary['tick']}")
    print(f"Events: {summary['events']}  mutations: {summary['mutations']}")
    print(f"Derived events: {summary['derived_events']}")
    print(f"Observations: {summary['observations']}")
    print(f"State fingerprint: {summary['fingerprint']}")


def cmd_state_replay(args):
    world=json.loads(Path(args.world).read_text(encoding="utf-8"))
    world.pop("progression_simulation",None)
    events=json.loads(Path(args.events).read_text(encoding="utf-8"))
    if not isinstance(events,list):
        raise ValueError("events JSON must contain a list")

    state=replay_world_events(world,events)
    errors=validate_world_state(world,state)
    if errors:
        raise RuntimeError("replayed world-state failed validation: "+"; ".join(errors[:20]))

    _export_world_state(state,args.out)
    print(f"Replayed {len(events)} events")
    print(f"State -> {args.out}.json")
    print(f"Fingerprint: {state_summary(state)['fingerprint']}")


def cmd_gameplay_check(args):
    data = json.loads(Path(args.file).read_text(encoding="utf-8"))
    # A gameplay export contains the world at top-level plus progression_simulation.
    data.pop("progression_simulation", None)
    errors = validate_gameplay_integrity(data) + validate_landmark_integrity(data)
    if isinstance(data.get("geography"),dict):
        errors += validate_geography(data)
    if isinstance(data.get("regional_influence"),dict):
        errors += validate_influence_fields(data)
    if isinstance(data.get("influence_topology"),dict):
        errors += validate_influence_topology(data)
    if isinstance(data.get("territory_graph"),dict):
        errors += validate_territory_graph(data)
    if errors:
        raise RuntimeError("gameplay validation failed: " + "; ".join(errors[:20]))
    sim = simulate_progression(data)
    print("Gameplay validation: PASS")
    print(f"Final sector reachable: {sim['final_sector_reachable']}")
    print(f"All sectors reachable: {sim['all_sectors_reachable']}")
    print(f"Abilities collected: {', '.join(sim['abilities']) or 'none'}")


def cmd_landmark_demo(args):
    profile = profile_from(args)
    out = ROOT/"generated"/"landmark_demo"
    ensure_dir(out)
    world = generate_gameplay_world(profile,args.seed,4,3,4)
    render_world(world,profile,gap=4).save(out/"landmark_world_4x3.png")
    render_cognitive_map(world,profile).save(out/"landmark_cognitive_map.png")
    _write_visual_quality(world,out/"landmark_visual_quality.json")
    export_gameplay_json(world,out/"landmark_world_4x3.json")
    counts={"local":0,"regional":0,"world":0}
    for s in world["sectors"]:
        for lm in s["scene"].get("landmarks",{}).values():
            counts[lm["scope"]]+=1
    print(f"Landmark demo -> {out/'landmark_world_4x3.png'}")
    print(f"Cognitive map -> {out/'landmark_cognitive_map.png'}")
    print(f"Landmarks: local={counts['local']} regional={counts['regional']} world={counts['world']}")



def _write_visual_quality(world, out_path):
    result=analyze_visual_patterns(world)
    Path(out_path).write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    return result

def cmd_visual_check(args):
    data=json.loads(Path(args.file).read_text(encoding="utf-8"))
    data.pop("progression_simulation",None)
    result=analyze_visual_patterns(data)
    print(f"Visual quality: {result['status'].upper()}")
    print(f"Repetition score: {result['metrics']['visual_repetition_score']}/100")
    if result["warnings"]:
        for w in result["warnings"]:
            print(f"WARNING: {w}")
    else:
        print("No suspicious landmark repetition patterns detected.")



def cmd_audit(args):
    data=json.loads(Path(args.file).read_text(encoding="utf-8"))
    data.pop("progression_simulation",None)
    result=audit_world(data,strict_visual=args.strict_visual)
    print(audit_summary(result))
    if args.out:
        Path(args.out).write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    if result["status"]=="fail":
        raise SystemExit(2)

def cmd_seed_sweep(args):
    profile=profile_from(args)
    result=sweep_seeds(
        profile,
        start_seed=args.start_seed,
        count=args.count,
        cols=args.cols,
        rows=args.rows,
        ability_count=args.ability_count,
        strict_visual=args.strict_visual,
    )
    out=Path(args.out) if args.out else ROOT/"generated"/"seed_sweep.json"
    ensure_dir(out.parent)
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"Seed sweep -> {out}")
    print(f"Best seed: {result['best_seed']} score={result['best_score']}")
    for row in result["results"][:min(5,len(result["results"]))]:
        print(f"  seed={row['seed']} status={row['status']} score={row['score']} grade={row['grade']} warnings={row['warnings']}")

def cmd_doctor(args):
    result=run_doctor(args.profile)
    print(f"PixelGen doctor: {result['status'].upper()}")
    for c in result["checks"]:
        print(f"{'OK' if c['ok'] else 'FAIL':4} {c['name']}: {c['detail']}")
    if result["status"]!="pass":
        raise SystemExit(2)



def _read_world_json(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    data.pop("progression_simulation",None)
    return data

def cmd_inspect(args):
    data=_read_world_json(args.file)
    info=inspect_world(data)
    print(inspection_text(info))
    if args.out:
        Path(args.out).write_text(json.dumps(info,indent=2,ensure_ascii=False),encoding="utf-8")

def cmd_fingerprint(args):
    data=_read_world_json(args.file)
    print(world_fingerprint(data))

def cmd_world_diff(args):
    a=_read_world_json(args.a)
    b=_read_world_json(args.b)
    result=compare_worlds(a,b)
    print(diff_text(result))
    if args.out:
        Path(args.out).write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")

def cmd_bundle_manifest(args):
    world_fp=None
    if args.world:
        world_fp=world_fingerprint(_read_world_json(args.world))
    out,manifest=write_manifest(args.folder,world_fingerprint=world_fp)
    print(f"Manifest -> {out}")
    print(f"Files: {manifest['file_count']}  bytes: {manifest['total_bytes']}")
    if world_fp:
        print(f"World fingerprint: {world_fp}")

def cmd_bundle_verify(args):
    result=verify_manifest(args.folder,args.manifest)
    print(f"Bundle verify: {result['status'].upper()}")
    print(f"Checked: {result['checked']}/{result.get('expected',0)}")
    for e in result["errors"]:
        print(f"ERROR: {e}")
    if result["status"]!="pass":
        raise SystemExit(2)



def cmd_env_log(args):
    profile = profile_from(args)
    log = run_environment_log(
        profile,
        suite=args.suite,
        label=args.label,
        device=args.device,
        notes=args.notes,
        repeat=args.repeat,
    )
    out = Path(args.out) if args.out else ROOT/"environment_logs"/default_log_filename(log)
    write_environment_log(log, out)
    md = write_markdown_companion(log, out)
    print(f"Environment log: {out}")
    print(f"Markdown log: {md}")
    print(f"Status: {log['summary']['status'].upper()}")
    for c in log["cases"]:
        fp = (c.get("fingerprint") or "—")[:16]
        print(
            f"  {c['name']} {c['cols']}x{c['rows']} "
            f"status={c['status']} total={c['timings_ms'].get('total')} ms fp={fp}"
        )
    if log["summary"]["status"] != "pass":
        raise SystemExit(2)

def cmd_env_compare(args):
    logs = [load_environment_log(Path(p)) for p in args.logs]
    try:
        result = compare_environment_logs(logs, baseline_label=args.baseline)
    except ValueError as e:
        print(f"Environment comparison error: {e}")
        raise SystemExit(2)
    print(environment_comparison_text(result), end="")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.md_out:
        Path(args.md_out).write_text(environment_comparison_markdown(result), encoding="utf-8")
    if args.csv_out:
        Path(args.csv_out).write_text(environment_comparison_csv(result), encoding="utf-8")
    if result["status"] == "fail":
        raise SystemExit(2)




def cmd_subbiome_structure_demo(args):
    profile=profile_from(args)
    out=Path(args.out) if args.out else ROOT/"generated"/"subbiome_structure_demo"/args.biome
    ensure_dir(out)
    atlas,samples=build_subbiome_showcase(profile,args.biome,args.seed)
    atlas_path=out/f"{args.biome}_subbiome_structure_atlas.png"
    atlas.save(atlas_path)

    payload={
        "version":"0.7.2",
        "biome":args.biome,
        "seed":args.seed,
        "samples":[
            {
                "zone":s["zone"],
                "subbiome":s["subbiome"],
                "transition":s["transition"],
                "signature":s["signature"],
            }
            for s in samples
        ],
    }
    json_path=out/f"{args.biome}_subbiome_structure_signatures.json"
    json_path.write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding="utf-8")

    print(f"Subbiome structural atlas -> {atlas_path}")
    print(f"Signatures -> {json_path}")
    for s in samples:
        sig=s["signature"]
        print(
            f"  {s['zone']}/{s['subbiome']}: "
            f"J={sig['junctions']} E={sig['endpoints']} "
            f"T={sig['turn_like_cells']} L={sig['loop_rank']} "
            f"adapters={sig['ecotone_adapters']}"
        )

def cmd_structural_check(args):
    data=_read_world_json(args.file)
    errors=validate_structural_grammar(data)
    result=analyze_structural_grammar(data)
    print(structural_report_text(result))
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
    if args.out:
        payload={"integrity_errors":errors,"analysis":result}
        Path(args.out).write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding="utf-8")
    if errors:
        raise SystemExit(2)

def cmd_biome_structure_demo(args):
    profile=profile_from(args)
    out=Path(args.out) if args.out else ROOT/"generated"/"biome_structure_demo"
    ensure_dir(out)
    atlas,entries=build_structure_showcase(profile,args.seed)
    atlas_path=out/"biome_structural_grammar_atlas.png"
    atlas.save(atlas_path)

    payload={
        "version":"0.7.1",
        "seed":args.seed,
        "entries":[
            {
                "biome":e["biome"],
                "signature":e["signature"],
            }
            for e in entries
        ],
    }
    json_path=out/"biome_structural_signatures.json"
    json_path.write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding="utf-8")

    print(f"Biome structural atlas -> {atlas_path}")
    print(f"Signatures -> {json_path}")
    for e in entries:
        s=e["signature"]
        print(
            f"  {e['biome']}: {s['grammar_id']} "
            f"J={s['junctions']} E={s['endpoints']} "
            f"T={s['turn_like_cells']} L={s['loop_rank']} "
            f"visual={s['path_visual']}"
        )


def build_parser():
    p = argparse.ArgumentParser(description="PixelGen v1.0.0 — Stable")
    p.add_argument("--profile", default=str(DEFAULT_PROFILE), help="JSON style profile")
    sub = p.add_subparsers(dest="command", required=True)

    t = sub.add_parser("terrain", help="Generate terrain tiles")
    t.add_argument("material", choices=["peat","pine","chapel","water","ice"])
    t.add_argument("--count", type=COUNT, default=16)
    t.add_argument("--seed", type=int, default=1)
    t.add_argument("--out")
    t.set_defaults(func=cmd_terrain)

    s = sub.add_parser("silt", help="Generate Silt overlays")
    s.add_argument("--count", type=COUNT, default=16)
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--density", type=_probability, default=0.34)
    s.add_argument("--out")
    s.set_defaults(func=cmd_silt)

    a = sub.add_parser("autotile", help="Generate simple N/E/S/W transition masks")
    a.add_argument("from_material", choices=["peat","pine","chapel","water","ice"])
    a.add_argument("to_material", choices=["peat","pine","chapel","water","ice"])
    a.add_argument("--seed", type=int, default=1)
    a.add_argument("--out")
    a.set_defaults(func=cmd_autotile)

    pv = sub.add_parser("preview", help="Build enlarged contact sheet")
    pv.add_argument("folder")
    pv.add_argument("--output")
    pv.add_argument("--scale", type=SCALE, default=8)
    pv.add_argument("--columns", type=COLUMNS, default=8)
    pv.set_defaults(func=cmd_preview)

    at = sub.add_parser("atlas", help="Pack PNG files into simple atlas")
    at.add_argument("folder")
    at.add_argument("--output")
    at.add_argument("--columns", type=COLUMNS, default=8)
    at.add_argument("--padding", type=PADDING, default=0)
    at.set_defaults(func=cmd_atlas)


    a47 = sub.add_parser("autotile47", help="Generate canonical 47-mask 8-neighbor transitions")
    a47.add_argument("from_material", choices=["peat","pine","chapel","water","ice"])
    a47.add_argument("to_material", choices=["peat","pine","chapel","water","ice"])
    a47.add_argument("--seed", type=int, default=1)
    a47.add_argument("--out")
    a47.set_defaults(func=cmd_autotile47)

    dc = sub.add_parser("decals", help="Generate modular paper/wax or moss decals")
    dc.add_argument("kind", choices=["paper","moss"])
    dc.add_argument("--count", type=COUNT, default=16)
    dc.add_argument("--seed", type=int, default=1)
    dc.add_argument("--density", type=_probability, default=0.14)
    dc.add_argument("--out")
    dc.set_defaults(func=cmd_decals)

    vl = sub.add_parser("validate", help="Validate palette/contrast/glow rules")
    vl.add_argument("folder")
    vl.add_argument("--floor", action="store_true")
    vl.set_defaults(func=cmd_validate)

    md = sub.add_parser("material-demo", help="Generate composed material grammar samples")
    md.add_argument("--seed", type=int, default=2026)
    md.set_defaults(func=cmd_material_demo)


    st = sub.add_parser("structure", help="Generate structural assets")
    st.add_argument("kind", choices=[
        "cliff_straight","cliff_corner_inner","cliff_corner_outer","cliff_broken","cliff_silt",
        "wall_straight","wall_corner_inner","wall_corner_outer","wall_broken","wall_doorway",
        "nanolith_shrine","printing_press_altar","mask_cross","printing_cathedral","silt_spire"
    ])
    st.add_argument("--count", type=COUNT, default=4)
    st.add_argument("--seed", type=int, default=1)
    st.add_argument("--out")
    st.set_defaults(func=cmd_structure)

    pp = sub.add_parser("prop", help="Generate prop assets")
    pp.add_argument("kind", choices=[
        "brazier_lit","brazier_off","paper_stack","chest","nano_capsule_broken",
        "skull_stake_a","skull_stake_b","biogel_barrel","biogel_barrel_leaking",
        "ritual_mask","warning_board","silt_growth"
    ])
    pp.add_argument("--count", type=COUNT, default=4)
    pp.add_argument("--seed", type=int, default=1)
    pp.add_argument("--out")
    pp.set_defaults(func=cmd_prop)

    mf = sub.add_parser("manifest", help="Export collision/footprint metadata")
    mf.add_argument("--out")
    mf.set_defaults(func=cmd_manifest)

    sd = sub.add_parser("structure-demo", help="Generate all v0.3 structure/prop samples")
    sd.add_argument("--seed", type=int, default=3030)
    sd.set_defaults(func=cmd_structure_demo)


    sc = sub.add_parser("scene", help="Generate one micro-map scene with preview + exports")
    sc.add_argument("kind", choices=["silt_marsh"])
    sc.add_argument("--seed", type=int, default=4040)
    sc.add_argument("--out")
    sc.set_defaults(func=cmd_scene)

    sb = sub.add_parser("scene-batch", help="Generate a batch of scenes")
    sb.add_argument("kind", choices=["silt_marsh"])
    sb.add_argument("--count", type=COUNT, default=4)
    sb.add_argument("--seed", type=int, default=4040)
    sb.add_argument("--out")
    sb.set_defaults(func=cmd_scene_batch)

    sd4 = sub.add_parser("scene-demo", help="Generate the v0.4 vertical-slice demo")
    sd4.add_argument("--seed", type=int, default=4040)
    sd4.set_defaults(func=cmd_scene_demo)


    bs = sub.add_parser("biome-scene", help="Generate one biome scene with encounters/finds")
    bs.add_argument("biome", choices=biome_names())
    bs.add_argument("--seed", type=int, default=5050)
    bs.add_argument("--hollow-chance", type=_probability, default=0.50)
    bs.add_argument("--out")
    bs.set_defaults(func=cmd_biome_scene)

    bd = sub.add_parser("biome-demo", help="Generate one scene for every v0.5 biome")
    bd.add_argument("--seed", type=int, default=5050)
    bd.set_defaults(func=cmd_biome_demo)

    wd = sub.add_parser("world", help="Generate v0.7 regional-geography multi-sector world")
    wd.add_argument("--cols", type=WORLD_DIM, default=3)
    wd.add_argument("--rows", type=WORLD_DIM, default=3)
    wd.add_argument("--seed", type=int, default=5050)
    wd.add_argument("--gap", type=GAP, default=4)
    wd.add_argument("--out")
    wd.set_defaults(func=cmd_world)

    wdemo = sub.add_parser("world-demo", help="Generate the canonical 3x3 stitched world")
    wdemo.add_argument("--seed", type=int, default=5050)
    wdemo.set_defaults(func=cmd_world_demo)


    gw6 = sub.add_parser("gameplay-world", help="Generate v0.7 regional geography + navigation/progression world")
    gw6.add_argument("--cols", type=WORLD_DIM, default=4)
    gw6.add_argument("--rows", type=WORLD_DIM, default=3)
    gw6.add_argument("--seed", type=int, default=6060)
    gw6.add_argument("--ability-count", type=ABILITY_COUNT, default=4)
    gw6.add_argument("--gap", type=GAP, default=4)
    gw6.add_argument("--out")
    gw6.set_defaults(func=cmd_gameplay_world)

    gd6 = sub.add_parser("gameplay-demo", help="Generate canonical 4x3 geography + metroidvania demo")
    gd6.add_argument("--seed", type=int, default=6060)
    gd6.set_defaults(func=cmd_gameplay_demo)

    geo7 = sub.add_parser("geography-demo", help="Generate canonical v0.7 regional geography showcase")
    geo7.add_argument("--cols", type=WORLD_DIM, default=6)
    geo7.add_argument("--rows", type=WORLD_DIM, default=5)
    geo7.add_argument("--seed", type=int, default=7000)
    geo7.add_argument("--ability-count", type=ABILITY_COUNT, default=4)
    geo7.add_argument("--out")
    geo7.set_defaults(func=cmd_geography_demo)

    inf73 = sub.add_parser("influence-demo", help="Render landmark-driven regional influence fields (v0.7.3.1 hardening)")
    inf73.add_argument("--cols", type=WORLD_DIM, default=6)
    inf73.add_argument("--rows", type=WORLD_DIM, default=5)
    inf73.add_argument("--seed", type=int, default=7300)
    inf73.add_argument("--ability-count", type=ABILITY_COUNT, default=4)
    inf73.add_argument("--out")
    inf73.set_defaults(func=cmd_influence_demo)

    topo74 = sub.add_parser("topology-demo", help="Render neutral/dominated/contested influence topology and front graph")
    topo74.add_argument("--cols", type=WORLD_DIM, default=6)
    topo74.add_argument("--rows", type=WORLD_DIM, default=5)
    topo74.add_argument("--seed", type=int, default=7301)
    topo74.add_argument("--ability-count", type=ABILITY_COUNT, default=4)
    topo74.add_argument("--out")
    topo74.set_defaults(func=cmd_topology_demo)

    terr75 = sub.add_parser("territory-demo", help="Render dominated territories, front event sites and EBE seed hooks")
    terr75.add_argument("--cols", type=WORLD_DIM, default=6)
    terr75.add_argument("--rows", type=WORLD_DIM, default=5)
    terr75.add_argument("--seed", type=int, default=7301)
    terr75.add_argument("--ability-count", type=ABILITY_COUNT, default=4)
    terr75.add_argument("--out")
    terr75.set_defaults(func=cmd_territory_demo)

    cor90 = sub.add_parser("corridor-demo", help="Render v0.9 regional corridors and macro-to-local realization")
    cor90.add_argument("--cols", type=WORLD_DIM, default=6)
    cor90.add_argument("--rows", type=WORLD_DIM, default=5)
    cor90.add_argument("--seed", type=int, default=7301)
    cor90.add_argument("--ability-count", type=ABILITY_COUNT, default=4)
    cor90.add_argument("--out")
    cor90.set_defaults(func=cmd_corridor_demo)

    state80 = sub.add_parser("state-demo", help="Apply deterministic dynamic world-state mutations and emit local EBE observations")
    state80.add_argument("--cols", type=WORLD_DIM, default=6)
    state80.add_argument("--rows", type=WORLD_DIM, default=5)
    state80.add_argument("--seed", type=int, default=7301)
    state80.add_argument("--ability-count", type=ABILITY_COUNT, default=4)
    state80.add_argument("--escalation", type=float, default=0.20)
    state80.add_argument("--territory-delta", type=float, default=0.12)
    state80.add_argument("--out")
    state80.set_defaults(func=cmd_state_demo)

    statecheck80 = sub.add_parser("state-check", help="Validate a dynamic state JSON against its static world JSON")
    statecheck80.add_argument("--world", required=True)
    statecheck80.add_argument("--state", required=True)
    statecheck80.set_defaults(func=cmd_state_check)

    replay80 = sub.add_parser("state-replay", help="Replay a runtime event log against a static world")
    replay80.add_argument("--world", required=True)
    replay80.add_argument("--events", required=True)
    replay80.add_argument("--out", required=True, help="Output path base without extension")
    replay80.set_defaults(func=cmd_state_replay)

    bsg71 = sub.add_parser("biome-structure-demo", help="Render one v0.7.1 structural grammar sample for every biome")
    bsg71.add_argument("--seed", type=int, default=7100)
    bsg71.add_argument("--out")
    bsg71.set_defaults(func=cmd_biome_structure_demo)

    sbg72 = sub.add_parser("subbiome-structure-demo", help="Render core/mid/margin/ecotone structural variants for one biome")
    sbg72.add_argument("--biome", choices=biome_names(), default="dark_forest")
    sbg72.add_argument("--seed", type=int, default=7200)
    sbg72.add_argument("--out")
    sbg72.set_defaults(func=cmd_subbiome_structure_demo)

    sch71 = sub.add_parser("structural-check", help="Analyze biome-specific structural morphology in a generated world JSON")
    sch71.add_argument("file")
    sch71.add_argument("--out")
    sch71.set_defaults(func=cmd_structural_check)





    el641 = sub.add_parser("env-log", help="Run portable benchmark suite and write an environment journal JSON + Markdown")
    el641.add_argument("--suite", choices=sorted(ENV_SUITES), default="standard")
    el641.add_argument("--label", help="Human label, e.g. PC, Termux, UserLAnd, Pydroid")
    el641.add_argument("--device", help="Optional device/model note")
    el641.add_argument("--notes", help="Optional free-form note")
    el641.add_argument("--repeat", type=COUNT, default=1, help="Repeat every benchmark case N times and aggregate medians/stability")
    el641.add_argument("--out", help="Output *.envlog.json path")
    el641.set_defaults(func=cmd_env_log)

    ec641 = sub.add_parser("env-compare", help="Compare two or more environment log JSON files")
    ec641.add_argument("logs", nargs="+")
    ec641.add_argument("--json-out")
    ec641.add_argument("--md-out")
    ec641.add_argument("--csv-out")
    ec641.add_argument("--baseline", help="Environment label used as performance baseline")
    ec641.set_defaults(func=cmd_env_compare)

    in64 = sub.add_parser("inspect", help="Print a compact semantic summary of a generated world JSON")
    in64.add_argument("file")
    in64.add_argument("--out")
    in64.set_defaults(func=cmd_inspect)

    fp64 = sub.add_parser("fingerprint", help="Print stable semantic SHA-256 fingerprint of a world JSON")
    fp64.add_argument("file")
    fp64.set_defaults(func=cmd_fingerprint)

    df64 = sub.add_parser("world-diff", help="Compare two generated world/gameplay JSON files semantically")
    df64.add_argument("a")
    df64.add_argument("b")
    df64.add_argument("--out")
    df64.set_defaults(func=cmd_world_diff)

    bm64 = sub.add_parser("bundle-manifest", help="Create SHA-256 manifest for an output folder")
    bm64.add_argument("folder")
    bm64.add_argument("--world", help="Optional world JSON used to embed semantic fingerprint")
    bm64.set_defaults(func=cmd_bundle_manifest)

    bv64 = sub.add_parser("bundle-verify", help="Verify a folder against pixelgen_bundle_manifest.json")
    bv64.add_argument("folder")
    bv64.add_argument("--manifest")
    bv64.set_defaults(func=cmd_bundle_verify)

    au63 = sub.add_parser("audit", help="Run unified structural/gameplay/landmark/visual audit on world JSON")
    au63.add_argument("file")
    au63.add_argument("--strict-visual", action="store_true", help="Treat visual warnings as audit failures")
    au63.add_argument("--out", help="Optional audit JSON output")
    au63.set_defaults(func=cmd_audit)

    sw63 = sub.add_parser("seed-sweep", help="Generate and rank a range of seeds without rendering PNG previews")
    sw63.add_argument("--start-seed", type=int, default=6300)
    sw63.add_argument("--count", type=COUNT, default=20)
    sw63.add_argument("--cols", type=WORLD_DIM, default=4)
    sw63.add_argument("--rows", type=WORLD_DIM, default=3)
    sw63.add_argument("--ability-count", type=ABILITY_COUNT, default=4)
    sw63.add_argument("--strict-visual", action="store_true")
    sw63.add_argument("--out")
    sw63.set_defaults(func=cmd_seed_sweep)

    dr63 = sub.add_parser("doctor", help="Check Python/Pillow/profile and run a tiny integrated generation test")
    dr63.set_defaults(func=cmd_doctor)

    vc62 = sub.add_parser("visual-check", help="Analyze landmark repetition/composition in a generated world JSON")
    vc62.add_argument("file")
    vc62.set_defaults(func=cmd_visual_check)

    lm61 = sub.add_parser("landmark-demo", help="Generate v0.6.1 landmark world + cognitive minimap")
    lm61.add_argument("--seed", type=int, default=6161)
    lm61.set_defaults(func=cmd_landmark_demo)

    gc6 = sub.add_parser("gameplay-check", help="Validate a generated v0.6 gameplay JSON")
    gc6.add_argument("file")
    gc6.set_defaults(func=cmd_gameplay_check)

    d = sub.add_parser("demo", help="Generate the full v0.1 sample set")
    d.add_argument("--seed", type=int, default=1337)
    d.set_defaults(func=cmd_demo)

    return p

def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except (ValueError, TypeError, FileNotFoundError, RuntimeError) as e:
        parser.exit(2, f"error: {e}\n")

if __name__ == "__main__":
    main()
