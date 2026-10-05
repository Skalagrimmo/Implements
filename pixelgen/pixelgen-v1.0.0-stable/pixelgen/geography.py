from collections import Counter, defaultdict
import heapq

from .biomes import get_biome
from .constraints import require_int, validate_world_dimensions
from .rng import SeededRNG

GEOGRAPHY_VERSION = "0.7.0"

SUBBIOMES = {
    "silt_marsh": {
        "core": ("deep_bog", "blackwater_basin"),
        "mid": ("reed_channels", "peat_islands"),
        "margin": ("wet_meadow", "fen_edge"),
    },
    "dark_forest": {
        "core": ("redwood_core", "root_maze"),
        "mid": ("moss_grove", "wet_pine"),
        "margin": ("forest_edge", "scrub_march"),
    },
    "frozen_pass": {
        "core": ("ice_basin", "wind_scoured_ridge"),
        "mid": ("frost_scree", "chapel_snowfield"),
        "margin": ("cold_foothill", "meltwater_edge"),
    },
    "ruined_settlement": {
        "core": ("charred_blocks", "collapsed_market"),
        "mid": ("broken_streets", "ash_courtyards"),
        "margin": ("outskirts", "flooded_lane"),
    },
    "reformed_chapel": {
        "core": ("print_cloister", "scriptorium_ruin"),
        "mid": ("wax_yard", "chapel_quarter"),
        "margin": ("pilgrim_road", "printer_outskirts"),
    },
}

TRANSITION_NAMES = {
    frozenset(("silt_marsh","dark_forest")): "wet_forest_ecotone",
    frozenset(("silt_marsh","ruined_settlement")): "drowned_outskirts",
    frozenset(("silt_marsh","reformed_chapel")): "flooded_cloister_edge",
    frozenset(("silt_marsh","frozen_pass")): "meltwater_fen",
    frozenset(("dark_forest","ruined_settlement")): "overgrown_ruins",
    frozenset(("dark_forest","reformed_chapel")): "chapel_wood",
    frozenset(("dark_forest","frozen_pass")): "frostwood_edge",
    frozenset(("ruined_settlement","reformed_chapel")): "print_district_ruins",
    frozenset(("ruined_settlement","frozen_pass")): "ash_scree",
    frozenset(("reformed_chapel","frozen_pass")): "frozen_cloister_march",
}

REGION_SUFFIX = {
    "silt_marsh": ("Basin","Fen","Blackwater"),
    "dark_forest": ("March","Wood","Rootlands"),
    "frozen_pass": ("Ridge","Pale Heights","Pass"),
    "ruined_settlement": ("Ashlands","Sloboda Belt","Burnt Quarter"),
    "reformed_chapel": ("Print March","Cloister Belt","Chapelry"),
}

BASE_FIELDS = {
    "silt_marsh": {"moisture":0.90,"elevation":0.18,"settlement":0.18},
    "dark_forest": {"moisture":0.67,"elevation":0.40,"settlement":0.14},
    "frozen_pass": {"moisture":0.34,"elevation":0.86,"settlement":0.08},
    "ruined_settlement": {"moisture":0.42,"elevation":0.37,"settlement":0.78},
    "reformed_chapel": {"moisture":0.38,"elevation":0.48,"settlement":0.88},
}

DIRS = {
    "N":(0,-1),
    "E":(1,0),
    "S":(0,1),
    "W":(-1,0),
}

def _stable01(seed, x, y, salt=0):
    # Integer-only deterministic hash → [0,1). Cross-runtime stable.
    n=(int(seed)*1103515245 + x*374761393 + y*668265263 + salt*2246822519) & 0xFFFFFFFF
    n ^= (n >> 13)
    n=(n*1274126177) & 0xFFFFFFFF
    n ^= (n >> 16)
    return n / 4294967296.0

def _clamp(v, lo=0.0, hi=1.0):
    return max(lo,min(hi,v))

def _manhattan(a,b):
    return abs(a[0]-b[0])+abs(a[1]-b[1])

def _region_count(sectors):
    if sectors <= 4: return 1
    if sectors <= 12: return 2
    if sectors <= 30: return 3
    if sectors <= 64: return 4
    if sectors <= 100: return 5
    return 6

def _choose_centers(rng, cols, rows, count):
    positions=[(x,y) for y in range(rows) for x in range(cols)]
    first=(rng.randint(0,cols-1),rng.randint(0,rows-1))
    centers=[first]
    while len(centers)<count:
        best=None
        best_score=None
        for p in positions:
            if p in centers:
                continue
            spacing=min(_manhattan(p,c) for c in centers)
            edge_bonus=0.25 if p[0] in (0,cols-1) or p[1] in (0,rows-1) else 0.0
            score=spacing*5.0 + edge_bonus + rng.random()
            if best_score is None or score>best_score:
                best_score,best=score,p
        centers.append(best)
    return centers

def _region_name(biome, index, seed):
    base=get_biome(biome)["name"]
    suffixes=REGION_SUFFIX[biome]
    suffix=suffixes[(abs(int(seed))+index) % len(suffixes)]
    return f"{base} — {suffix} {index+1}"

def _pick_region_biomes(rng, allowed, count):
    allowed=list(allowed)
    if not allowed:
        raise ValueError("allowed biomes cannot be empty")
    for b in allowed:
        get_biome(b)
    if len(allowed)>=count:
        return rng.sample(allowed,count)
    out=[]
    while len(out)<count:
        out.append(allowed[len(out)%len(allowed)])
    return out

def _assignment_score(pos, region, seed):
    cx,cy=region["center"]
    dx=abs(pos[0]-cx)
    dy=abs(pos[1]-cy)
    # Different region shapes without noisy one-cell islands.
    wx=region["shape"]["x_weight"]
    wy=region["shape"]["y_weight"]
    diagonal=abs((pos[0]-cx)+(pos[1]-cy))*region["shape"]["diag_weight"]
    jitter=(_stable01(seed,pos[0],pos[1],region["id"]+17)-0.5)*0.28
    return dx*wx + dy*wy + diagonal + jitter

def _assign_connected_regions(regions, seed, cols, rows):
    """Multi-source region growth.

    A cell can only be claimed from an already-claimed predecessor of the same
    region, so every final region is 4-neighbor connected to its seed center.
    """
    heap=[]
    assignment={}
    for r in regions:
        x,y=r["center"]
        heapq.heappush(heap,(0.0,r["id"],x,y))

    while heap:
        cost,rid,x,y=heapq.heappop(heap)
        pos=(x,y)
        if pos in assignment:
            continue
        assignment[pos]=rid
        r=regions[rid]

        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            n=(nx,ny)
            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
            if n in assignment:
                continue

            axis_weight=r["shape"]["x_weight"] if dx else r["shape"]["y_weight"]
            # Small positive deterministic terrain resistance bends boundaries
            # without allowing detached one-cell islands.
            terrain=0.86 + _stable01(seed,nx,ny,700+rid)*0.32
            diag=r["shape"]["diag_weight"] * abs((nx-r["center"][0])+(ny-r["center"][1])) * 0.035
            step=max(0.05,axis_weight*terrain+diag)
            heapq.heappush(heap,(cost+step,rid,nx,ny))

    return assignment

def _zone(distance, max_distance):
    if max_distance <= 0:
        return "core"
    q=distance/max_distance
    if q <= 0.34: return "core"
    if q <= 0.70: return "mid"
    return "margin"

def _subbiome(seed, x, y, biome, zone, transition_to=None):
    if transition_to and transition_to != biome:
        return TRANSITION_NAMES.get(
            frozenset((biome,transition_to)),
            f"{biome}_to_{transition_to}_ecotone",
        )
    choices=SUBBIOMES[biome][zone]
    idx=int(_stable01(seed,x,y,911)*len(choices)) % len(choices)
    return choices[idx]

def _environment_fields(seed, x, y, biome, transition, cols, rows):
    base=BASE_FIELDS[biome]
    xnorm=0.0 if cols<=1 else x/(cols-1)
    ynorm=0.0 if rows<=1 else y/(rows-1)
    moisture=base["moisture"] + (0.5-xnorm)*0.06 + (_stable01(seed,x,y,101)-0.5)*0.12
    elevation=base["elevation"] + (0.5-ynorm)*0.08 + (_stable01(seed,x,y,202)-0.5)*0.12
    settlement=base["settlement"] + (_stable01(seed,x,y,303)-0.5)*0.14
    if transition:
        # Ecotones are somewhat more structurally varied.
        moisture += (_stable01(seed,x,y,404)-0.5)*0.06
    return {
        "moisture":round(_clamp(moisture),3),
        "elevation":round(_clamp(elevation),3),
        "settlement":round(_clamp(settlement),3),
    }

def _modifiers(fields, zone, transition):
    hazard=0.82 + fields["moisture"]*0.45
    props=0.82 + fields["settlement"]*0.42
    encounters=0.92 + (1.0-fields["settlement"])*0.18
    if zone=="core":
        encounters *= 1.05
    if transition:
        props *= 1.05
        hazard *= 1.03
    return {
        "hazard_mult":round(hazard,3),
        "prop_mult":round(props,3),
        "encounter_mult":round(encounters,3),
    }

def plan_geography(seed, cols, rows, allowed_biomes):
    seed=require_int("seed",seed)
    cols,rows=validate_world_dimensions(cols,rows)
    rng=SeededRNG(seed+7_000_000)
    region_count=_region_count(cols*rows)
    centers=_choose_centers(rng,cols,rows,region_count)
    primaries=_pick_region_biomes(rng,allowed_biomes,region_count)

    regions=[]
    for i,(center,biome) in enumerate(zip(centers,primaries)):
        regions.append({
            "id":i,
            "name":_region_name(biome,i,seed),
            "primary_biome":biome,
            "center":list(center),
            "shape":{
                "x_weight":round(0.82+rng.random()*0.42,3),
                "y_weight":round(0.82+rng.random()*0.42,3),
                "diag_weight":round(rng.random()*0.13,3),
            },
        })

    assignment=_assign_connected_regions(regions,seed,cols,rows)

    # Sector membership and region extent.
    members=defaultdict(list)
    for pos,rid in assignment.items():
        members[rid].append(pos)

    # Some unusual tiny Voronoi layouts may lose a non-center cell, never the center.
    for r in regions:
        cells=members[r["id"]]
        maxd=max((_manhattan(tuple(r["center"]),p) for p in cells),default=0)
        r["sector_count"]=len(cells)
        r["max_center_distance"]=maxd
        r["bounds"]={
            "min_x":min(p[0] for p in cells),"max_x":max(p[0] for p in cells),
            "min_y":min(p[1] for p in cells),"max_y":max(p[1] for p in cells),
        }

    adjacency=defaultdict(set)
    per_sector={}
    for y in range(rows):
        for x in range(cols):
            pos=(x,y)
            rid=assignment[pos]
            region=regions[rid]
            edge_neighbors=[]
            neighbor_regions=[]
            neighbor_biomes=[]
            transition_edges=[]
            for edge,(dx,dy) in DIRS.items():
                q=(x+dx,y+dy)
                if q not in assignment:
                    continue
                qrid=assignment[q]
                if qrid!=rid:
                    qregion=regions[qrid]
                    adjacency[rid].add(qrid)
                    adjacency[qrid].add(rid)
                    neighbor_regions.append(qrid)
                    neighbor_biomes.append(qregion["primary_biome"])
                    transition_edges.append({
                        "edge":edge,
                        "region_id":qrid,
                        "biome":qregion["primary_biome"],
                    })

            transition_to=None
            if neighbor_biomes:
                transition_to=Counter(neighbor_biomes).most_common(1)[0][0]
            distance=_manhattan(pos,tuple(region["center"]))
            zone=_zone(distance,region["max_center_distance"])
            fields=_environment_fields(seed,x,y,region["primary_biome"],bool(transition_edges),cols,rows)
            sub=_subbiome(seed,x,y,region["primary_biome"],zone,transition_to)

            per_sector[pos]={
                "region_id":rid,
                "region_name":region["name"],
                "primary_biome":region["primary_biome"],
                "subbiome":sub,
                "zone":zone,
                "distance_to_region_center":distance,
                "transition":bool(transition_edges),
                "transition_to":transition_to,
                "transition_edges":transition_edges,
                "fields":fields,
                "modifiers":_modifiers(fields,zone,bool(transition_edges)),
            }

    for r in regions:
        r["adjacent_regions"]=sorted(adjacency[r["id"]])
        r.pop("shape",None)  # generation-only detail, not useful in public export

    transitions=[]
    seen=set()
    for rid,others in adjacency.items():
        for other in others:
            pair=tuple(sorted((rid,other)))
            if pair in seen:
                continue
            seen.add(pair)
            transitions.append({
                "regions":list(pair),
                "biomes":[regions[pair[0]]["primary_biome"],regions[pair[1]]["primary_biome"]],
            })

    return {
        "version":GEOGRAPHY_VERSION,
        "policy":{
            "region_assignment":"multi-source weighted flood growth / guaranteed connected masses",
            "biome_scale":"primary biome is stable across each region",
            "transition_belts":"sector edges touching another region become ecotones",
            "subbiomes":"core/mid/margin + pair-specific transition subbiomes",
            "local_fields":"moisture/elevation/settlement modulate scene density",
        },
        "regions":regions,
        "transitions":transitions,
        "per_sector":per_sector,
    }

def public_geography(plan, cols, rows):
    sectors=[]
    for y in range(rows):
        for x in range(cols):
            sectors.append({"sx":x,"sy":y,**plan["per_sector"][(x,y)]})
    return {
        "version":plan["version"],
        "policy":plan["policy"],
        "regions":plan["regions"],
        "transitions":plan["transitions"],
        "sectors":sectors,
    }
