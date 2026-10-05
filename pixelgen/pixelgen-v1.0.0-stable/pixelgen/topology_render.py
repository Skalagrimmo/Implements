from PIL import Image, ImageDraw

LABELS={
    "print_civic":"PRINT",
    "silt_contamination":"SILT",
    "nano_signal":"NANO",
}

def render_topology_map(world,profile,cell=58,pad=12):
    topo=world["influence_topology"]
    cols,rows=world["cols"],world["rows"]
    W=pad*2+cols*cell+190
    H=pad*2+rows*cell+24
    img=Image.new("RGBA",(W,H),(14,14,18,255))
    draw=ImageDraw.Draw(img)
    lookup={(s["sx"],s["sy"]):s for s in topo["sectors"]}

    for y in range(rows):
        for x in range(cols):
            item=lookup[(x,y)]
            x0=pad+x*cell
            y0=pad+y*cell
            status=item["status"]
            alignment=item.get("alignment")

            if status=="neutral":
                fill=(52,52,58,225)
            elif status=="contested":
                fill=(92,72,104,230)
            elif alignment=="silt_contamination":
                fill=(35,108,98,230)
            elif alignment=="print_civic":
                fill=(132,112,58,230)
            elif alignment=="nano_signal":
                fill=(54,92,128,230)
            else:
                fill=(54,54,62,225)

            draw.rectangle(
                (x0+1,y0+1,x0+cell-2,y0+cell-2),
                fill=fill,
                outline=(205,205,195,80),
            )

            if status=="neutral":
                title="NEUT"
            elif status=="contested":
                title="CONTEST"
            else:
                title=LABELS.get(alignment,"—")

            draw.text((x0+4,y0+4),title,fill=(242,232,212,255))
            draw.text(
                (x0+4,y0+cell-16),
                f"{item['top_strength']:.2f}/{item['dominance_margin']:.2f}",
                fill=(205,205,210,255),
            )

    # Draw front boundaries on top.
    for edge in topo.get("boundary_edges",[]):
        ax,ay=edge["a"]
        bx,by=edge["b"]
        x0=pad+ax*cell
        y0=pad+ay*cell
        pressure=float(edge.get("pressure",0.0))
        width=2 if pressure<0.35 else 3
        if bx>ax:
            x=x0+cell
            draw.line((x,y0+2,x,y0+cell-2),fill=(238,238,228,235),width=width)
        else:
            y=y0+cell
            draw.line((x0+2,y,x0+cell-2,y),fill=(238,238,228,235),width=width)

    lx=pad+cols*cell+12
    draw.text((lx,pad),"TOPOLOGY",fill=(240,230,210,255))
    ly=pad+18
    summary=topo.get("summary",{})
    for status,count in summary.get("status_counts",{}).items():
        draw.text((lx,ly),f"{status}: {count}",fill=(205,205,210,255))
        ly+=15
    ly+=5
    draw.text((lx,ly),f"fronts: {summary.get('front_count',0)}",fill=(205,205,210,255))
    ly+=18
    for front in topo.get("fronts",[])[:8]:
        pair="/".join(LABELS.get(x,x) for x in front["pair"])
        draw.text((lx,ly),f"{front['id']} {pair}",fill=(180,185,190,255))
        ly+=13
        draw.text(
            (lx+8,ly),
            f"edges={front['edge_count']} p={front['mean_pressure']:.2f}",
            fill=(145,150,155,255),
        )
        ly+=17

    return img
