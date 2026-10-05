from PIL import Image, ImageDraw

BIOME_KEYS={
    "silt_marsh":"peat_mid",
    "dark_forest":"moss_dark",
    "frozen_pass":"ice_mid",
    "ruined_settlement":"basalt_mid",
    "reformed_chapel":"peat_light",
}

def _rgba(rgb,a=255):
    return tuple(rgb)+(a,)

def render_geography_map(world, profile, cell=54, pad=12):
    geo=world["geography"]
    cols,rows=world["cols"],world["rows"]
    palette=profile["palette_rgb"]
    W=pad*2+cols*cell+150
    H=pad*2+rows*cell+24
    img=Image.new("RGBA",(W,H),(15,15,18,255))
    draw=ImageDraw.Draw(img)
    gmap={(s["sx"],s["sy"]):s for s in geo["sectors"]}

    for y in range(rows):
        for x in range(cols):
            g=gmap[(x,y)]
            x0=pad+x*cell; y0=pad+y*cell
            fill=_rgba(palette[BIOME_KEYS[g["primary_biome"]]],225)
            draw.rectangle((x0+1,y0+1,x0+cell-2,y0+cell-2),fill=fill,outline=(225,220,205,100))
            # Transition belt marker: inner frame.
            if g["transition"]:
                draw.rectangle((x0+5,y0+5,x0+cell-6,y0+cell-6),outline=_rgba(palette["nano_glow"],150))
            # Region identity is the large readable number.
            draw.text((x0+5,y0+4),f"R{g['region_id']}",fill=_rgba(palette["vellum"]))
            # Core/mid/margin indicator.
            z={"core":"C","mid":"M","margin":"E"}[g["zone"]]
            draw.text((x0+cell-13,y0+4),z,fill=(210,210,210,210))
            # Subbiome abbreviated to first 8 chars.
            draw.text((x0+4,y0+cell-14),g["subbiome"][:8],fill=(220,220,215,210))

    lx=pad+cols*cell+12
    draw.text((lx,pad),"REGIONS",fill=_rgba(palette["vellum"]))
    ly=pad+18
    for r in geo["regions"]:
        draw.text((lx,ly),f"R{r['id']}  {r['primary_biome']}",fill=(205,205,205,255))
        ly+=14
        draw.text((lx+8,ly),f"{r['sector_count']} sectors",fill=(155,155,160,255))
        ly+=18

    ly=max(ly,pad+rows*cell-48)
    draw.text((lx,ly),"C core",fill=(180,180,185,255)); ly+=14
    draw.text((lx,ly),"M mid",fill=(180,180,185,255)); ly+=14
    draw.text((lx,ly),"E edge/margin",fill=(180,180,185,255)); ly+=14
    draw.text((lx,ly),"inner frame = ecotone",fill=(180,180,185,255))

    footer=pad+rows*cell+5
    draw.text((pad,footer),"Regional Geography 0.7 — biome masses → ecotones → subbiomes",fill=(185,185,190,255))
    return img
