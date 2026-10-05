from PIL import Image, ImageDraw

CHANNEL_LABELS={
    "print_civic":"PRINT",
    "silt_contamination":"SILT",
    "nano_signal":"NANO",
}

def render_influence_map(world,profile,cell=54,pad=12):
    inf=world["regional_influence"]
    cols,rows=world["cols"],world["rows"]
    W=pad*2+cols*cell+170
    H=pad*2+rows*cell+24
    img=Image.new("RGBA",(W,H),(14,14,18,255))
    draw=ImageDraw.Draw(img)
    p=profile["palette_rgb"]
    lookup={(s["sx"],s["sy"]):s for s in inf["sectors"]}

    for y in range(rows):
        for x in range(cols):
            item=lookup[(x,y)]
            x0=pad+x*cell; y0=pad+y*cell
            channels=item["channels"]
            dom=item.get("dominant_channel")
            strength=max(channels.values()) if channels else 0
            base=32+int(min(1.0,strength)*105)
            if dom=="silt_contamination":
                fill=(24,base,base-10,220)
            elif dom=="print_civic":
                fill=(base+35,base+20,70,220)
            elif dom=="nano_signal":
                fill=(55,base,115,220)
            else:
                fill=(38,38,44,220)
            draw.rectangle((x0+1,y0+1,x0+cell-2,y0+cell-2),fill=fill,outline=(200,200,195,70))
            label=CHANNEL_LABELS.get(dom,"—")
            draw.text((x0+4,y0+4),label,fill=(238,230,210,255))
            draw.text((x0+4,y0+cell-15),f"{strength:.2f}",fill=(210,210,215,255))

    # source markers
    for src in inf.get("sources",[]):
        sx,sy=src["sector"]
        cx=pad+sx*cell+cell//2
        cy=pad+sy*cell+cell//2
        draw.ellipse((cx-6,cy-6,cx+6,cy+6),outline=(245,245,235,255),width=2)

    lx=pad+cols*cell+12
    draw.text((lx,pad),"INFLUENCE SOURCES",fill=(240,230,210,255))
    ly=pad+18
    for src in inf.get("sources",[]):
        draw.text((lx,ly),f"{src['kind']}",fill=(205,205,210,255))
        ly+=13
        draw.text((lx+8,ly),f"{src['channel']} r{src['radius']}",fill=(155,160,165,255))
        ly+=18
    return img
