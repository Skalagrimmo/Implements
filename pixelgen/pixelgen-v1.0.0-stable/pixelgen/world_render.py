from PIL import Image, ImageDraw
from .scene_render import render_scene, RenderAssetCache
from .constraints import require_int, MAX_RENDER_PIXELS


def render_world(world, profile, gap=4, quality="exact", variants=8):
    gap=require_int("gap",gap,0,256)
    ts=int(profile.get("tile_size",16))
    sw=world["sector_width"]*ts
    sh=world["sector_height"]*ts
    W=world["cols"]*sw+(world["cols"]-1)*gap
    H=world["rows"]*sh+(world["rows"]-1)*gap
    if W <= 0 or H <= 0:
        raise ValueError("render dimensions must be positive")
    if W*H > MAX_RENDER_PIXELS:
        raise ValueError(f"world preview would contain {W*H:,} pixels; safety limit is {MAX_RENDER_PIXELS:,}")
    if quality not in ("exact","fast"):
        raise ValueError("quality must be 'exact' or 'fast'")
    cache = RenderAssetCache(profile, variants=variants) if quality == "fast" else None
    out=Image.new("RGBA",(W,H),(15,15,18,255))
    draw=ImageDraw.Draw(out)
    for s in world["sectors"]:
        img=render_scene(s["scene"],profile,cache=cache)
        x=s["sx"]*(sw+gap); y=s["sy"]*(sh+gap)
        out.alpha_composite(img,(x,y))
        draw.rectangle((x,y,x+sw-1,y+sh-1),outline=(242,227,198,120))
    return out
