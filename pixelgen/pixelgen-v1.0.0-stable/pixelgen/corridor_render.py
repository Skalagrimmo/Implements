from PIL import Image, ImageDraw
from .geography_render import BIOME_KEYS

KIND_LABEL={
    "old_road":"ROAD",
    "pilgrim_route":"PILG",
    "ridge_chain":"RIDG",
    "silt_vein":"SILT",
    "drainage_channel":"DRAN",
}


def _rgba(rgb,a=255):
    return tuple(rgb)+(a,)


def render_corridor_map(world, profile, cell=58, pad=12):
    data=world["regional_corridors"]
    cols,rows=world["cols"],world["rows"]
    palette=profile["palette_rgb"]
    W=pad*2+cols*cell+220
    H=pad*2+rows*cell+28
    img=Image.new("RGBA",(W,H),(15,15,18,255))
    draw=ImageDraw.Draw(img)

    geo={(s["sx"],s["sy"]):s for s in world.get("geography",{}).get("sectors",[])}
    for y in range(rows):
        for x in range(cols):
            g=geo.get((x,y),{})
            biome=g.get("primary_biome")
            fill=_rgba(palette[BIOME_KEYS[biome]],205) if biome in BIOME_KEYS else (55,55,60,220)
            x0=pad+x*cell; y0=pad+y*cell
            draw.rectangle((x0+1,y0+1,x0+cell-2,y0+cell-2),fill=fill,outline=(220,215,205,75))
            draw.text((x0+4,y0+4),f"{x},{y}",fill=(230,225,215,220))

    # Draw macro corridor paths through sector centers.
    for corridor in data.get("corridors",[]):
        pts=[]
        for sx,sy in corridor["path"]:
            pts.append((pad+sx*cell+cell//2,pad+sy*cell+cell//2))
        if len(pts)>=2:
            draw.line(pts,fill=_rgba(palette["vellum"],230),width=3)
        for px,py in pts:
            draw.ellipse((px-4,py-4,px+4,py+4),fill=_rgba(palette["nano_glow"],220))

    # Junction count / compact membership markers.
    membership={(s["sx"],s["sy"]):s.get("corridors",[]) for s in world["sectors"]}
    for (x,y),items in membership.items():
        if not items: continue
        x0=pad+x*cell; y0=pad+y*cell
        text="/".join(KIND_LABEL.get(i["kind"],i["kind"][:4].upper()) for i in items[:2])
        if len(items)>2: text+="+"
        draw.text((x0+4,y0+cell-14),text,fill=(242,232,212,255))

    lx=pad+cols*cell+12
    draw.text((lx,pad),"REGIONAL CORRIDORS",fill=_rgba(palette["vellum"]))
    ly=pad+18
    summary=data.get("summary",{})
    draw.text((lx,ly),f"corridors: {summary.get('corridor_count',0)}",fill=(205,205,210,255)); ly+=14
    draw.text((lx,ly),f"coverage: {summary.get('covered_sector_count',0)}/{cols*rows}",fill=(205,205,210,255)); ly+=20

    for c in data.get("corridors",[])[:10]:
        draw.text((lx,ly),f"{c['id']}",fill=(190,190,195,255)); ly+=13
        draw.text((lx+7,ly),f"{c['purpose']} / {c['sector_count']} sectors",fill=(145,150,155,255)); ly+=17

    footer=pad+rows*cell+7
    draw.text((pad,footer),"PixelGen 0.9 — global corridor topology → local sector realization",fill=(185,185,190,255))
    return img
