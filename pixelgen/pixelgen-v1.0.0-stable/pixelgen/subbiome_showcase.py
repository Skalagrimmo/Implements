from PIL import Image, ImageDraw

from .geography import SUBBIOMES, TRANSITION_NAMES
from .scene_biome import generate_biome_scene
from .scene_render import render_scene
from .scene_structure import structural_signature, STYLE_BY_BIOME


def _skeleton(scene, cell=8):
    w=scene["width"]*cell
    h=scene["height"]*cell
    img=Image.new("RGBA",(w,h),(18,18,22,255))
    draw=ImageDraw.Draw(img)

    adapter_cells=set()
    for a in scene.get("structural_grammar",{}).get("ecotone_adapters",[]):
        for c in a.get("path_cells",[]):
            if isinstance(c,(list,tuple)) and len(c)==2:
                adapter_cells.add((int(c[0]),int(c[1])))

    for y in range(scene["height"]):
        for x in range(scene["width"]):
            x0=x*cell; y0=y*cell
            if scene["ground"][y][x]=="path":
                fill=(205,205,195,255)
                if (x,y) in adapter_cells:
                    fill=(82,229,197,255)
            else:
                fill=(40,42,47,255)
            draw.rectangle((x0+1,y0+1,x0+cell-2,y0+cell-2),fill=fill)
    return img


def _zone_for_subbiome(biome, subbiome):
    for zone, names in SUBBIOMES[biome].items():
        if subbiome in names:
            return zone
    return "mid"


def _neighbor_for(biome):
    names=list(STYLE_BY_BIOME)
    i=names.index(biome)
    return names[(i+1)%len(names)]


def build_subbiome_showcase(profile, biome, seed=7200):
    if biome not in SUBBIOMES:
        raise ValueError(f"unknown biome {biome!r}")

    samples=[]
    flat=[]
    for zone in ("core","mid","margin"):
        for sub in SUBBIOMES[biome][zone]:
            flat.append((zone,sub,[]))

    neighbor=_neighbor_for(biome)
    trans_name=TRANSITION_NAMES.get(
        frozenset((biome,neighbor)),
        f"{biome}_to_{neighbor}_ecotone",
    )
    flat.append((
        "margin",
        trans_name,
        [{"edge":"E","region_id":99,"biome":neighbor}],
    ))

    for i,(zone,sub,transition_edges) in enumerate(flat):
        ctx={
            "region_id":0,
            "region_name":"Showcase Region",
            "primary_biome":biome,
            "subbiome":sub,
            "zone":zone,
            "distance_to_region_center":i,
            "transition":bool(transition_edges),
            "transition_to":neighbor if transition_edges else None,
            "transition_edges":transition_edges,
            "fields":{"moisture":0.5,"elevation":0.5,"settlement":0.5},
            "modifiers":{"hazard_mult":1.0,"prop_mult":1.0,"encounter_mult":1.0},
        }
        scene=generate_biome_scene(
            profile,
            seed+i*131,
            biome,
            landmark_plan=[],
            geography_context=ctx,
        )
        samples.append({
            "zone":zone,
            "subbiome":sub,
            "transition":bool(transition_edges),
            "scene":scene,
            "render":render_scene(scene,profile),
            "skeleton":_skeleton(scene),
            "signature":structural_signature(scene),
        })

    panel_w=338
    panel_h=430
    cols=3
    rows=(len(samples)+cols-1)//cols
    W=panel_w*cols
    H=panel_h*rows
    canvas=Image.new("RGBA",(W,H),(14,14,18,255))
    draw=ImageDraw.Draw(canvas)

    for i,s in enumerate(samples):
        col=i%cols; row=i//cols
        x=col*panel_w+8
        y=row*panel_h+8
        sig=s["signature"]
        title=f"{s['zone']} / {s['subbiome']}"
        draw.text((x,y),title,fill=(242,227,198,255))
        draw.text(
            (x,y+15),
            f"{sig['grammar_id']}  adapters={sig['ecotone_adapters']}",
            fill=(170,190,185,255),
        )
        canvas.alpha_composite(s["render"],(x,y+34))
        canvas.alpha_composite(s["skeleton"],(x,y+34+240+8))
        draw.text(
            (x,y+34+240+8+120+5),
            f"J{sig['junctions']} E{sig['endpoints']} "
            f"T{sig['turn_like_cells']} L{sig['loop_rank']}",
            fill=(180,180,185,255),
        )
        ops=", ".join(sig.get("variant_operators",())) or "base"
        draw.text((x,y+34+240+8+120+20),ops[:48],fill=(150,155,160,255))

    return canvas,samples
