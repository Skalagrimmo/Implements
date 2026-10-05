from PIL import Image, ImageDraw

LABELS={
    "print_civic":"PRINT",
    "silt_contamination":"SILT",
    "nano_signal":"NANO",
}


def render_territory_map(world,profile,cell=60,pad=12):
    graph=world["territory_graph"]
    topo=world["influence_topology"]
    cols,rows=world["cols"],world["rows"]
    W=pad*2+cols*cell+210
    H=pad*2+rows*cell+24
    img=Image.new("RGBA",(W,H),(14,14,18,255))
    draw=ImageDraw.Draw(img)

    territory_by_sector={}
    territory_by_id={t["id"]:t for t in graph.get("territories",[])}
    for t in graph.get("territories",[]):
        for c in t.get("sectors",[]):
            territory_by_sector[tuple(c)]=t

    topo_lookup={(s["sx"],s["sy"]):s for s in topo.get("sectors",[])}

    for y in range(rows):
        for x in range(cols):
            x0=pad+x*cell; y0=pad+y*cell
            t=territory_by_sector.get((x,y))
            ts=topo_lookup.get((x,y),{})
            if t is None:
                if ts.get("status")=="contested":
                    fill=(92,72,104,230)
                    label="CONTEST"
                else:
                    fill=(50,50,56,225)
                    label="NEUT"
            else:
                a=t.get("alignment")
                if a=="silt_contamination": fill=(35,108,98,230)
                elif a=="print_civic": fill=(132,112,58,230)
                elif a=="nano_signal": fill=(54,92,128,230)
                else: fill=(60,60,66,225)
                label=t["id"].replace("territory_","T")

            draw.rectangle((x0+1,y0+1,x0+cell-2,y0+cell-2),fill=fill,outline=(205,205,195,75))
            draw.text((x0+4,y0+4),label,fill=(242,232,212,255))
            if t is not None:
                draw.text((x0+4,y0+cell-16),LABELS.get(t.get("alignment"),"?"),fill=(205,205,210,255))

    # Front sites are explicit event anchors.
    for site in graph.get("front_sites",[]):
        sx,sy=site["sector"]
        cx=pad+sx*cell+cell//2
        cy=pad+sy*cell+cell//2
        draw.rectangle((cx-5,cy-5,cx+5,cy+5),outline=(245,245,235,255),width=2)
        draw.line((cx-7,cy,cx+7,cy),fill=(245,245,235,210),width=1)
        draw.line((cx,cy-7,cx,cy+7),fill=(245,245,235,210),width=1)

    lx=pad+cols*cell+12
    draw.text((lx,pad),"TERRITORY GRAPH",fill=(240,230,210,255))
    ly=pad+18
    for t in graph.get("territories",[])[:10]:
        draw.text((lx,ly),f"{t['id']} {LABELS.get(t['alignment'],t['alignment'])}",fill=(205,205,210,255))
        ly+=13
        draw.text((lx+8,ly),f"sectors={t['sector_count']} mean={t['mean_strength']:.2f}",fill=(150,155,160,255))
        ly+=18

    ly+=4
    draw.text((lx,ly),f"front sites: {graph['summary']['front_site_count']}",fill=(205,205,210,255)); ly+=15
    draw.text((lx,ly),f"event seeds: {graph['summary']['event_seed_count']}",fill=(205,205,210,255)); ly+=18
    for kind,count in graph["summary"].get("event_kind_counts",{}).items():
        draw.text((lx,ly),f"{kind}: {count}",fill=(165,170,175,255)); ly+=13

    return img
