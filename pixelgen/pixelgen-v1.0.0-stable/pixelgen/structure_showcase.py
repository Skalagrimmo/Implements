from PIL import Image, ImageDraw

from .biomes import biome_names
from .scene_biome import generate_biome_scene
from .scene_render import render_scene
from .scene_structure import structural_signature


def _skeleton(scene, cell=10):
    w=scene["width"]*cell
    h=scene["height"]*cell
    img=Image.new("RGBA",(w,h),(18,18,22,255))
    draw=ImageDraw.Draw(img)
    path={(x,y) for y,row in enumerate(scene["ground"]) for x,v in enumerate(row) if v=="path"}
    for y in range(scene["height"]):
        for x in range(scene["width"]):
            x0=x*cell; y0=y*cell
            if (x,y) in path:
                draw.rectangle((x0+1,y0+1,x0+cell-2,y0+cell-2),fill=(205,205,195,255))
            else:
                draw.rectangle((x0+1,y0+1,x0+cell-2,y0+cell-2),fill=(40,42,47,255))
    sx=scene["spawn"]["x"]*cell+cell//2
    sy=scene["spawn"]["y"]*cell+cell//2
    draw.ellipse((sx-2,sy-2,sx+2,sy+2),fill=(242,227,198,255))
    return img


def build_structure_showcase(profile, seed=7100):
    entries=[]
    for i,biome in enumerate(biome_names()):
        scene=generate_biome_scene(
            profile,
            seed+i*101,
            biome,
            landmark_plan=[],
        )
        entries.append({
            "biome":biome,
            "scene":scene,
            "render":render_scene(scene,profile),
            "skeleton":_skeleton(scene),
            "signature":structural_signature(scene),
        })

    full_w=320
    full_h=240
    sk_w=200
    sk_h=150
    panel_w=max(full_w,sk_w)+18
    panel_h=36+full_h+10+sk_h+38
    cols=3
    rows=2
    W=cols*panel_w
    H=rows*panel_h
    canvas=Image.new("RGBA",(W,H),(14,14,18,255))
    draw=ImageDraw.Draw(canvas)

    for i,e in enumerate(entries):
        col=i%cols; row=i//cols
        x=col*panel_w+8
        y=row*panel_h+8
        sig=e["signature"]
        draw.text((x,y),e["biome"],fill=(242,227,198,255))
        draw.text((x,y+15),sig["grammar_id"],fill=(170,190,185,255))
        canvas.alpha_composite(e["render"],(x,y+36))
        canvas.alpha_composite(e["skeleton"],(x,y+36+full_h+10))
        info_y=y+36+full_h+10+sk_h+4
        draw.text(
            (x,info_y),
            f"J{sig['junctions']} E{sig['endpoints']} T{sig['turn_like_cells']} L{sig['loop_rank']}",
            fill=(180,180,185,255),
        )

    return canvas,entries
