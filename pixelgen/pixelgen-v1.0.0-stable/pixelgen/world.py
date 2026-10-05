from .biomes import biome_names, get_biome
from .scene_biome import generate_biome_scene
from .encounters import generate_encounters, generate_finds
from .pockets import insert_hollow
from .constraints import validate_world_dimensions, require_int
from .navigation import ensure_route
from .placement import reserve
from .integrity import validate_world_integrity
from .landmarks import plan_world_landmarks
from .landmark_integrity import validate_landmark_integrity
from .visual_pattern import analyze_visual_patterns
from .geography import plan_geography, public_geography
from .geography_integrity import validate_geography
from .structural_integrity import validate_structural_grammar
from .region_influence import plan_influences, public_influences, apply_influence_to_geography_context
from .influence_integrity import validate_influence_fields
from .influence_topology import build_influence_topology, public_topology, apply_topology_to_influence
from .topology_integrity import validate_influence_topology
from .territory_graph import build_territory_graph, territory_context_for_sector
from .territory_integrity import validate_territory_graph
from .regional_corridors import plan_regional_corridors, realize_regional_corridors
from .corridor_integrity import validate_regional_corridors


def _force_corridor(scene, edge, coord):
    w,h=scene["width"],scene["height"]
    if edge in ("N","S"):
        if not 0 <= coord < w:
            raise ValueError(f"corridor coordinate {coord} out of range for {edge}")
        y=0 if edge=="N" else h-1
        cells=[(coord,y)]
        if coord+1 < w:
            cells.append((coord+1,y))
    elif edge in ("W","E"):
        if not 0 <= coord < h:
            raise ValueError(f"corridor coordinate {coord} out of range for {edge}")
        x=0 if edge=="W" else w-1
        cells=[(x,coord)]
        if coord+1 < h:
            cells.append((x,coord+1))
    else:
        raise ValueError(f"unknown edge {edge!r}")
    for x,y in cells:
        scene["ground"][y][x]="path"
        scene["overlay"][y][x]=None
        scene["collision"][y][x]="walk"
    reserve(scene,cells)
    return cells[0]


def _connect_exit(scene, edge, coord):
    target=_force_corridor(scene,edge,coord)
    start=(scene["spawn"]["x"],scene["spawn"]["y"])
    path=ensure_route(scene,start,target)
    if path is None:
        raise RuntimeError(f"could not connect {edge} exit at {coord} to spawn")
    return target


def _legacy_biome_map(cols, rows, cycle):
    return {
        (sx,sy):cycle[(sx+sy*cols)%len(cycle)]
        for sy in range(rows)
        for sx in range(cols)
    }


def generate_world(profile, seed=0, cols=3, rows=3, biome_cycle=None, geography=True):
    seed=require_int("seed",seed)
    cols,rows=validate_world_dimensions(cols,rows)
    allowed=list(biome_cycle) if biome_cycle is not None else biome_names()
    if not allowed:
        raise ValueError("biome_cycle cannot be empty")
    for biome in allowed:
        get_biome(biome)

    if geography:
        geography_plan=plan_geography(seed,cols,rows,allowed)
        biome_map={
            pos:ctx["primary_biome"]
            for pos,ctx in geography_plan["per_sector"].items()
        }
    else:
        geography_plan=None
        biome_map=_legacy_biome_map(cols,rows,allowed)

    landmark_plan=plan_world_landmarks(
        seed,cols,rows,
        cycle=allowed,
        biome_map=biome_map,
    )
    influence_plan=plan_influences(cols,rows,landmark_plan)
    topology_plan=build_influence_topology(influence_plan,cols,rows)
    corridor_plan=plan_regional_corridors(
        seed,cols,rows,geography_plan,landmark_plan
    )
    territory_graph=build_territory_graph(
        public_topology(topology_plan,cols,rows),cols,rows
    )

    sectors=[]
    lookup={}
    for sy in range(rows):
        for sx in range(cols):
            pos=(sx,sy)
            biome=biome_map[pos]
            sector_seed=seed+sy*10000+sx*997
            scene_plan=landmark_plan["per_sector"].get(pos,[])
            geo_context=(
                dict(geography_plan["per_sector"][pos])
                if geography_plan is not None else {}
            )
            if geography_plan is not None:
                geo_context=apply_influence_to_geography_context(
                    geo_context,
                    influence_plan["per_sector"][pos],
                )
                geo_context["regional_influence"]=apply_topology_to_influence(
                    geo_context.get("regional_influence",{}),
                    topology_plan["per_sector"][pos]["topology"],
                )
                geo_context["territory"]=territory_context_for_sector(
                    territory_graph,pos
                )
                geo_context["regional_corridors"]=list(
                    corridor_plan["per_sector"].get(pos,[])
                )
            scene=generate_biome_scene(
                profile,sector_seed,biome,
                landmark_plan=scene_plan,
                geography_context=geo_context,
            )
            sector={
                "sx":sx,"sy":sy,
                "biome":biome,
                "seed":sector_seed,
                "scene":scene,
                "links":{},
            }
            if geography_plan is not None:
                sector["region_id"]=geo_context["region_id"]
                sector["subbiome"]=geo_context["subbiome"]
                sector["geography_zone"]=geo_context["zone"]
                sector["transition"]=geo_context["transition"]
            sectors.append(sector)
            lookup[pos]=sector

    # Physical inter-sector topology remains independent from the biome grammar.
    for sy in range(rows):
        for sx in range(cols):
            sec=lookup[(sx,sy)]
            if sx+1 < cols:
                other=lookup[(sx+1,sy)]
                y=6+((seed+sx*7+sy*13)%max(1,sec["scene"]["height"]-8))
                _connect_exit(sec["scene"],"E",y)
                _connect_exit(other["scene"],"W",y)
                sec["links"]["E"]={"to":[sx+1,sy],"coord":y}
                other["links"]["W"]={"to":[sx,sy],"coord":y}
            if sy+1 < rows:
                other=lookup[(sx,sy+1)]
                x=4+((seed+sx*11+sy*17)%max(1,sec["scene"]["width"]-8))
                _connect_exit(sec["scene"],"S",x)
                _connect_exit(other["scene"],"N",x)
                sec["links"]["S"]={"to":[sx,sy+1],"coord":x}
                other["links"]["N"]={"to":[sx,sy],"coord":x}

    # v0.9 macro corridor topology is planned at world scale first, then
    # realized through the actual reciprocal sector exits and local walk graph.
    realized_corridors=realize_regional_corridors({"sectors":sectors},corridor_plan)

    # Content comes after topology so it cannot block required routes.
    for sec in sectors:
        insert_hollow(sec["scene"],sec["seed"],chance=0.45)
        generate_encounters(sec["scene"],sec["biome"],sec["seed"])
        generate_finds(sec["scene"],sec["biome"],sec["seed"])

    world={
        "name":"Techno-Animist Regional World" if geography else "Techno-Animist Legacy Micro World",
        "generator":{"name":"PixelGen","version":"1.0.0"},
        "schema_versions":{
            "world":"0.7",
            "geography":"0.7.0",
            "structural_grammar":"0.7.3.1",
            "regional_influence":"0.7.3",
            "hardening":"0.7.3.1",
            "influence_topology":"0.7.4",
            "territory_graph":"0.7.5",
            "dynamic_world_state":"0.8.0",
            "regional_corridors":"0.9.0",
            "runtime_api":"1.0.0",
            "contract_manifest":"1.0.0",
            "render_api":"0.9.1",
            "landmarks":"0.6.2",
            "visual_quality":"0.6.3",
            "interop":"0.6.4",
            "environment_journal":"0.6.4.2",
        },
        "seed":seed,
        "cols":cols,"rows":rows,
        "sector_width":20,"sector_height":15,
        "sectors":sectors,
        "landmark_system":{
            "version":"0.6.2",
            "policy":landmark_plan["policy"],
            "placements":landmark_plan["placements"],
        },
    }
    if geography_plan is not None:
        world["geography"]=public_geography(geography_plan,cols,rows)
    world["regional_influence"]=public_influences(influence_plan,cols,rows)
    world["influence_topology"]=public_topology(topology_plan,cols,rows)
    world["territory_graph"]=territory_graph
    world["regional_corridors"]=realized_corridors

    errors=validate_world_integrity(world)+validate_landmark_integrity(world)
    errors += validate_structural_grammar(world)
    errors += validate_influence_fields(world)
    errors += validate_influence_topology(world)
    errors += validate_territory_graph(world)
    errors += validate_regional_corridors(world)
    if geography_plan is not None:
        errors += validate_geography(world)
    if errors:
        raise RuntimeError(
            "generated world failed integrity validation: "+"; ".join(errors[:12])
        )
    world["visual_quality"]=analyze_visual_patterns(world)
    return world
