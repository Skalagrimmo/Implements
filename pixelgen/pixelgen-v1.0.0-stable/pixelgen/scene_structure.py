from collections import deque

STRUCTURE_VERSION = "0.7.3.1"

STYLE_BY_BIOME = {
    "silt_marsh": {
        "id": "meandering_causeways",
        "path_visual": "peat",
        "description": "dry causeways, stepping islands, low-branch wetland traversal",
    },
    "dark_forest": {
        "id": "root_branch_network",
        "path_visual": "pine",
        "description": "organic root/stem branching with several irregular forks",
    },
    "frozen_pass": {
        "id": "ridge_zigzag",
        "path_visual": "ice",
        "description": "angular ridge traverse with long diagonal/zigzag runs and few forks",
    },
    "ruined_settlement": {
        "id": "street_grid",
        "path_visual": "chapel",
        "description": "orthogonal streets, blocks and plaza-like loops",
    },
    "reformed_chapel": {
        "id": "axial_cloister",
        "path_visual": "chapel",
        "description": "processional axis, transept and enclosed cloister loop",
    },
}

# v0.7.2 does not create a second independent grammar system.
# A subbiome applies small, semantic operators to its parent biome skeleton.
SUBBIOME_OPERATORS = {
    # Silt marsh
    "deep_bog": ("prune_leaves", "island_spur"),
    "blackwater_basin": ("island_chain",),
    "reed_channels": ("island_spur",),
    "peat_islands": ("island_spur", "island_chain"),
    "wet_meadow": ("prune_leaves", "edge_bias"),
    "fen_edge": ("edge_bias",),

    # Dark forest
    "redwood_core": ("large_platform", "prune_leaves"),
    "root_maze": ("extra_spurs", "extra_spurs"),
    "moss_grove": ("side_loop",),
    "wet_pine": ("extra_spurs", "widen"),
    "forest_edge": ("prune_leaves", "edge_bias"),
    "scrub_march": ("extra_spurs", "edge_bias"),

    # Frozen pass
    "ice_basin": (),
    "wind_scoured_ridge": ("prune_leaves",),
    "frost_scree": ("extra_spurs",),
    "chapel_snowfield": ("crossing",),
    "cold_foothill": ("widen",),
    "meltwater_edge": ("edge_bias",),

    # Ruined settlement
    "charred_blocks": ("side_loop",),
    "collapsed_market": ("large_platform", "crossing"),
    "broken_streets": ("prune_leaves", "prune_leaves"),
    "ash_courtyards": ("side_loop", "small_platform"),
    "outskirts": ("prune_leaves", "edge_bias"),
    "flooded_lane": ("edge_bias", "widen"),

    # Reformed chapel
    "print_cloister": ("side_loop",),
    "scriptorium_ruin": ("prune_leaves", "small_platform"),
    "wax_yard": ("large_platform",),
    "chapel_quarter": ("crossing",),
    "pilgrim_road": ("edge_bias", "crossing"),
    "printer_outskirts": ("prune_leaves", "edge_bias"),
}

ZONE_OPERATORS = {
    "core": ("intensify",),
    "mid": (),
    "margin": ("edge_bias",),
}


def _in(scene, x, y):
    return 0 <= x < scene["width"] and 0 <= y < scene["height"]


def _paint(scene, cells):
    painted=set()
    for x,y in cells:
        if not _in(scene,x,y):
            continue
        scene["ground"][y][x]="path"
        scene["overlay"][y][x]=None
        scene["collision"][y][x]="walk"
        painted.add((x,y))
    return painted


def _hline(x0,x1,y):
    if x1 < x0:
        x0,x1=x1,x0
    return {(x,y) for x in range(x0,x1+1)}


def _vline(x,y0,y1):
    if y1 < y0:
        y0,y1=y1,y0
    return {(x,y) for y in range(y0,y1+1)}


def _rect_loop(x0,y0,x1,y1):
    cells=set()
    cells |= _hline(x0,x1,y0)
    cells |= _hline(x0,x1,y1)
    cells |= _vline(x0,y0,y1)
    cells |= _vline(x1,y0,y1)
    return cells


def _platform(cx,cy,rx=1,ry=1):
    return {
        (x,y)
        for y in range(cy-ry,cy+ry+1)
        for x in range(cx-rx,cx+rx+1)
    }


def _step_path(start, target, rng, horizontal_bias=0.5):
    x,y=start
    tx,ty=target
    cells={(x,y)}
    guard=0
    while (x,y)!=(tx,ty) and guard<200:
        guard+=1
        dx=0 if x==tx else (1 if tx>x else -1)
        dy=0 if y==ty else (1 if ty>y else -1)
        choices=[]
        if dx:
            choices.extend([(dx,0)]*(3 if horizontal_bias>=0.5 else 1))
        if dy:
            choices.extend([(0,dy)]*(3 if horizontal_bias<0.5 else 1))
        if not choices:
            break
        sx,sy=rng.choice(choices)
        x+=sx; y+=sy
        cells.add((x,y))
    return cells


def _meander(scene, rng):
    cells=set()
    x=1
    y=11
    cells.add((x,y))
    turn_every=rng.randint(3,5)
    since=0
    while x < scene["width"]-2:
        x+=1
        cells.add((x,y))
        since+=1
        if since>=turn_every:
            since=0
            turn_every=rng.randint(3,5)
            if rng.chance(0.72):
                y=max(7,min(12,y+rng.choice((-1,1))))
                cells.add((x,y))

    # Stepping islands widen the route rather than branching it.
    for cx in (5,11,16):
        cy=min(range(7,13), key=lambda yy: min(abs(yy-y0) for x0,y0 in cells if x0==cx)) if any(x0==cx for x0,_ in cells) else 10
        cells |= _platform(cx,cy,1,0)

    # One short alternate wet crossing, deliberately not a large branch tree.
    if rng.chance(0.65):
        source=min(cells,key=lambda p:abs(p[0]-9)+abs(p[1]-10))
        target=(min(17,source[0]+4), max(7,min(12,source[1]+rng.choice((-2,2)))))
        cells |= _step_path(source,target,rng,horizontal_bias=0.72)
    return cells,(2,11)


def _forest_roots(scene, rng):
    hub=(9+rng.choice((-1,0,1)),8+rng.choice((-1,0,1)))
    entry=(2,11)
    cells=set()
    cells |= _step_path(entry,hub,rng,horizontal_bias=0.58)

    targets=[
        (17,rng.randint(3,5)),
        (17,rng.randint(9,12)),
        (rng.randint(6,10),2),
        (rng.randint(3,6),rng.randint(4,7)),
    ]
    for i,target in enumerate(targets):
        if i==3 and not rng.chance(0.70):
            continue
        cells |= _step_path(hub,target,rng,horizontal_bias=rng.choice((0.35,0.55,0.70)))
        # irregular root nub
        if rng.chance(0.55):
            near=min(cells,key=lambda p:abs(p[0]-target[0])+abs(p[1]-target[1]))
            nub=(max(1,min(18,near[0]+rng.choice((-1,1)))), max(1,min(13,near[1]+rng.choice((-1,1)))))
            cells |= _step_path(near,nub,rng,horizontal_bias=0.5)
    return cells,entry


def _frozen_ridge(scene, rng):
    anchors=[
        (2,11),
        (5,10),
        (7,8),
        (10,8),
        (12,6),
        (15,5),
        (17,3),
    ]
    # Perturb the ridge while preserving a strong angular direction.
    perturbed=[anchors[0]]
    for x,y in anchors[1:-1]:
        perturbed.append((x,max(2,min(12,y+rng.choice((-1,0,0,1))))))
    perturbed.append(anchors[-1])

    cells=set()
    for a,b in zip(perturbed,perturbed[1:]):
        # Alternate horizontal/vertical priority to make visible broken ridges.
        cells |= _step_path(a,b,rng,horizontal_bias=rng.choice((0.25,0.78)))

    # Sparse shelf rather than a tree of branches.
    if rng.chance(0.75):
        source=perturbed[rng.choice((2,3,4))]
        target=(min(18,source[0]+rng.randint(3,5)), min(12,source[1]+rng.randint(2,4)))
        cells |= _step_path(source,target,rng,horizontal_bias=0.72)
    return cells,(2,11)


def _settlement_grid(scene, rng):
    xs=[5,14]
    ys=[5,11]
    if rng.chance(0.5):
        xs[0]+=rng.choice((-1,1))
    if rng.chance(0.5):
        ys[0]+=rng.choice((-1,1))

    cells=set()
    for x in xs:
        cells |= _vline(x,2,13)
    for y in ys:
        cells |= _hline(1,18,y)

    # Plaza / block circulation gives loops rather than branching trunks.
    px=9+rng.choice((0,1))
    py=7+rng.choice((0,1))
    cells |= _rect_loop(px-2,py-1,px+3,py+2)
    # The plaza must belong to the street fabric, never become an isolated decorative island.
    cells |= _hline(xs[0],px-2,py)

    # One broken lane survives as a shorter orthogonal segment.
    if rng.chance(0.72):
        yy=rng.choice((3,8,13))
        cells |= _hline(rng.randint(2,5),rng.randint(10,17),yy)
    return cells,(2,11)


def _chapel_axis(scene, rng):
    cx=10
    cells=set()
    cells |= _vline(cx,1,13)
    cells |= _hline(4,16,7)
    cells |= _rect_loop(6,3,14,11)

    # Processional approach from player side into the cloister.
    cells |= _hline(2,6,11)

    # Small symmetric forecourt.
    if rng.chance(0.75):
        cells |= _rect_loop(8,10,12,13)
    return cells,(2,11)



def _neighbors4(cell):
    x,y=cell
    return ((x+1,y),(x-1,y),(x,y+1),(x,y-1))


def _nearest(cells, target):
    tx,ty=target
    return min(cells, key=lambda p:abs(p[0]-tx)+abs(p[1]-ty))


def _prune_leaves(cells, protected, count=2):
    cells=set(cells)
    protected=set(protected)
    for _ in range(count):
        leaves=[
            p for p in cells
            if p not in protected
            and sum(n in cells for n in _neighbors4(p)) <= 1
        ]
        if not leaves:
            break
        # Deterministic: prune the lexicographically last leaf.
        cells.remove(sorted(leaves)[-1])
    return cells


def _central_path_cell(scene, cells):
    cx=(scene["width"]-1)/2
    cy=(scene["height"]-1)/2
    return min(cells,key=lambda p:abs(p[0]-cx)+abs(p[1]-cy))


def _add_platform(scene, cells, large=False):
    center=_central_path_cell(scene,cells)
    return set(cells) | _platform(center[0],center[1],2 if large else 1,1 if large else 0)


def _add_side_loop(scene, cells, rng):
    center=_central_path_cell(scene,cells)
    x=max(2,min(scene["width"]-5,center[0]-1+rng.choice((-1,0,1))))
    y=max(2,min(scene["height"]-5,center[1]-1+rng.choice((-1,0,1))))
    loop=_rect_loop(x,y,x+3,y+3)
    # Explicit connector prevents decorative loop islands.
    connector=_step_path(_nearest(cells,(x,y)),(x,y),rng,horizontal_bias=0.5)
    return set(cells) | loop | connector


def _add_spur(scene, cells, rng):
    source=sorted(cells)[rng.randint(0,len(cells)-1)]
    dx,dy=rng.choice(((1,0),(-1,0),(0,1),(0,-1)))
    length=rng.randint(2,4)
    tx=max(1,min(scene["width"]-2,source[0]+dx*length))
    ty=max(1,min(scene["height"]-2,source[1]+dy*length))
    return set(cells) | _step_path(source,(tx,ty),rng,horizontal_bias=0.65 if dx else 0.35)



def _add_island_spur(scene, cells, rng, length=1):
    """Attach a narrow marsh island/causeway without creating a graph cycle."""
    cells=set(cells)
    if not cells:
        return cells

    ordered=sorted(cells)
    start_index=rng.randint(0,len(ordered)-1)
    ordered=ordered[start_index:]+ordered[:start_index]

    directions=((1,0),(-1,0),(0,1),(0,-1))
    for source in ordered:
        sx,sy=source
        # Deterministically rotate direction priority.
        shift=rng.randint(0,3)
        dirs=directions[shift:]+directions[:shift]
        for dx,dy in dirs:
            chain=[]
            ok=True
            for step in range(1,length+1):
                q=(sx+dx*step,sy+dy*step)
                if not _in(scene,*q) or q in cells:
                    ok=False
                    break

                # New cells may touch only their predecessor/source. This prevents
                # accidental loops against another part of the meandering causeway.
                existing=cells | set(chain)
                allowed_prev=source if step==1 else chain[-1]
                touching=[n for n in _neighbors4(q) if n in existing]
                if touching != [allowed_prev] and set(touching)!={allowed_prev}:
                    ok=False
                    break
                chain.append(q)
            if ok and chain:
                return cells | set(chain)
    return cells


def _widen(scene, cells, rng):
    out=set(cells)
    sample=sorted(cells)
    if not sample:
        return out
    stride=max(2,len(sample)//7)
    for i,p in enumerate(sample):
        if i%stride:
            continue
        x,y=p
        if rng.chance(0.5):
            q=(x,y+1 if y < scene["height"]-2 else y-1)
        else:
            q=(x+1 if x < scene["width"]-2 else x-1,y)
        if _in(scene,*q):
            out.add(q)
    return out


def _crossing(scene, cells, rng):
    center=_central_path_cell(scene,cells)
    if rng.chance(0.5):
        segment=_hline(max(1,center[0]-3),min(scene["width"]-2,center[0]+3),center[1])
    else:
        segment=_vline(center[0],max(1,center[1]-3),min(scene["height"]-2,center[1]+3))
    return set(cells) | segment


def _edge_target(scene, edge, salt=0):
    # Keep adapters away from corners and deterministic without relying on hash().
    if edge in ("N","S"):
        span=max(1,scene["width"]-8)
        x=4+(salt%span)
        return (x,0 if edge=="N" else scene["height"]-1)
    span=max(1,scene["height"]-8)
    y=4+(salt%span)
    return (0 if edge=="W" else scene["width"]-1,y)


def _preferred_world_edge(geography_context):
    transitions=geography_context.get("transition_edges",[])
    if transitions:
        return transitions[0].get("edge")
    # Margin sectors without a region transition still receive a mild outward tendency.
    dist=int(geography_context.get("distance_to_region_center",0))
    return ("N","E","S","W")[dist%4]


def _edge_bias(scene, cells, rng, geography_context):
    edge=_preferred_world_edge(geography_context)
    if not edge:
        return set(cells)
    target=_edge_target(scene,edge,rng.randint(0,9999))
    source=_nearest(cells,target)
    return set(cells) | _step_path(source,target,rng,horizontal_bias=0.68 if edge in ("E","W") else 0.32)


def _intensify(scene, biome_kind, cells, rng):
    if biome_kind=="dark_forest":
        return _add_spur(scene,_add_spur(scene,cells,rng),rng)
    if biome_kind in ("ruined_settlement","reformed_chapel"):
        return _add_side_loop(scene,cells,rng)
    if biome_kind=="silt_marsh":
        return _add_island_spur(scene,cells,rng,length=1)
    if biome_kind=="frozen_pass":
        # Ridge cores should become more emphatic through their parent zigzag,
        # not through 2D widening that creates urban-looking loops/junctions.
        return set(cells)
    return set(cells)


def _apply_operator(scene, biome_kind, cells, entry, operator, rng, geography_context):
    protected={entry}
    if operator=="prune_leaves":
        return _prune_leaves(cells,protected,count=2)
    if operator=="island_spur":
        return _add_island_spur(scene,cells,rng,length=1)
    if operator=="island_chain":
        return _add_island_spur(scene,cells,rng,length=2)
    if operator=="small_platform":
        return _add_platform(scene,cells,large=False)
    if operator=="large_platform":
        return _add_platform(scene,cells,large=True)
    if operator=="side_loop":
        return _add_side_loop(scene,cells,rng)
    if operator=="extra_spurs":
        return _add_spur(scene,cells,rng)
    if operator=="widen":
        return _widen(scene,cells,rng)
    if operator=="crossing":
        return _crossing(scene,cells,rng)
    if operator=="edge_bias":
        return _edge_bias(scene,cells,rng,geography_context)
    if operator=="intensify":
        return _intensify(scene,biome_kind,cells,rng)
    return set(cells)


def _apply_subbiome_variation(scene, biome_kind, cells, entry, rng, geography_context):
    subbiome=geography_context.get("subbiome")
    zone=geography_context.get("zone")
    operators=list(SUBBIOME_OPERATORS.get(subbiome,()))
    operators.extend(ZONE_OPERATORS.get(zone,()))
    out=set(cells)
    for operator in operators:
        out=_apply_operator(scene,biome_kind,out,entry,operator,rng,geography_context)
    variant={
        "operators":operators,
        "variant_id":f"{biome_kind}:{subbiome or 'standalone'}:{zone or 'none'}",
    }
    if subbiome is not None:
        variant["subbiome"]=subbiome
    if zone is not None:
        variant["zone"]=zone
    return out,variant


def _apply_ecotone_adapters(scene, cells, rng, geography_context):
    out=set(cells)
    adapters=[]
    transitions=list(geography_context.get("transition_edges",[]))
    for i,trans in enumerate(transitions):
        edge=trans.get("edge")
        if edge not in ("N","E","S","W"):
            continue
        target=_edge_target(scene,edge,731+i*97+rng.randint(0,997))
        source=_nearest(out,target)
        adapter=_step_path(
            source,target,rng,
            horizontal_bias=0.70 if edge in ("E","W") else 0.30
        )
        out |= adapter
        adapters.append({
            "edge":edge,
            "neighbor_biome":trans.get("biome"),
            "neighbor_region_id":trans.get("region_id"),
            "path_cells":[[x,y] for x,y in sorted(adapter)],
        })
    return out,adapters


def _metrics(cells):
    if not cells:
        return {
            "path_cells":0,
            "endpoints":0,
            "junctions":0,
            "turn_like_cells":0,
            "loop_rank":0,
            "components":0,
            "horizontal_edges":0,
            "vertical_edges":0,
        }

    neighbors={}
    h_edges=0
    v_edges=0
    edges=0
    for x,y in cells:
        ns=[]
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            q=(x+dx,y+dy)
            if q in cells:
                ns.append(q)
                if (dx,dy)==(1,0):
                    h_edges+=1
                elif (dx,dy)==(0,1):
                    v_edges+=1
        neighbors[(x,y)]=ns
    edges=h_edges+v_edges

    endpoints=sum(len(ns)==1 for ns in neighbors.values())
    junctions=sum(len(ns)>=3 for ns in neighbors.values())

    turn_like=0
    for (x,y),ns in neighbors.items():
        if len(ns)!=2:
            continue
        a,b=ns
        if a[0]!=b[0] and a[1]!=b[1]:
            turn_like+=1

    unseen=set(cells)
    components=0
    while unseen:
        components+=1
        start=unseen.pop()
        q=deque([start])
        while q:
            p=q.popleft()
            for n in neighbors[p]:
                if n in unseen:
                    unseen.remove(n)
                    q.append(n)

    loop_rank=max(0,edges-len(cells)+components)
    return {
        "path_cells":len(cells),
        "endpoints":endpoints,
        "junctions":junctions,
        "turn_like_cells":turn_like,
        "loop_rank":loop_rank,
        "components":components,
        "horizontal_edges":h_edges,
        "vertical_edges":v_edges,
    }


def apply_biome_structure(scene, biome_kind, rng, geography_context=None):
    if biome_kind not in STYLE_BY_BIOME:
        raise ValueError(f"no structural grammar for biome {biome_kind!r}")

    if biome_kind=="silt_marsh":
        cells,entry=_meander(scene,rng)
    elif biome_kind=="dark_forest":
        cells,entry=_forest_roots(scene,rng)
    elif biome_kind=="frozen_pass":
        cells,entry=_frozen_ridge(scene,rng)
    elif biome_kind=="ruined_settlement":
        cells,entry=_settlement_grid(scene,rng)
    else:
        cells,entry=_chapel_axis(scene,rng)

    geography_context=dict(geography_context or {})
    variant_rng=rng
    cells,variant=_apply_subbiome_variation(
        scene,biome_kind,cells,entry,variant_rng,geography_context
    )
    cells,ecotone_adapters=_apply_ecotone_adapters(
        scene,cells,variant_rng,geography_context
    )

    painted=_paint(scene,cells)
    scene["_structural_path_cells"]=set(painted)
    style=STYLE_BY_BIOME[biome_kind]
    metrics=_metrics(painted)
    scene["structural_grammar"]={
        "version":STRUCTURE_VERSION,
        "biome":biome_kind,
        "grammar_id":style["id"],
        "description":style["description"],
        "path_visual":style["path_visual"],
        "entry":{"x":entry[0],"y":entry[1]},
        "variant":variant,
        "ecotone_adapters":ecotone_adapters,
        "metrics":metrics,
    }
    return scene["structural_grammar"]


def structural_signature(scene):
    meta=scene.get("structural_grammar",{})
    m=meta.get("metrics",{})
    return {
        "grammar_id":meta.get("grammar_id"),
        "path_visual":meta.get("path_visual"),
        "path_cells":m.get("path_cells",0),
        "endpoints":m.get("endpoints",0),
        "junctions":m.get("junctions",0),
        "turn_like_cells":m.get("turn_like_cells",0),
        "loop_rank":m.get("loop_rank",0),
        "components":m.get("components",0),
        "variant_id":meta.get("variant",{}).get("variant_id"),
        "variant_operators":tuple(meta.get("variant",{}).get("operators",[])),
        "ecotone_adapters":len(meta.get("ecotone_adapters",[])),
    }
