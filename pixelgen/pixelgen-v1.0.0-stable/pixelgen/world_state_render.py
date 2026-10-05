from PIL import Image, ImageDraw

LABELS={
    "print_civic":"PRINT",
    "silt_contamination":"SILT",
    "nano_signal":"NANO",
}


def _territory_sector_map(world):
    result={}
    for t in world.get("territory_graph",{}).get("territories",[]):
        for cell in t.get("sectors",[]):
            result[tuple(cell)]=t["id"]
    return result


def render_world_state_map(world,state,cell=62,pad=12):
    cols,rows=world["cols"],world["rows"]
    W=pad*2+cols*cell+250
    H=pad*2+rows*cell+24
    img=Image.new("RGBA",(W,H),(14,14,18,255))
    draw=ImageDraw.Draw(img)

    territory_by_sector=_territory_sector_map(world)
    topology={(s["sx"],s["sy"]):s for s in world.get("influence_topology",{}).get("sectors",[])}
    latest_observed={
        tuple(o["sector"])
        for o in state.get("observations",[])
        if o.get("sector")
    }

    for y in range(rows):
        for x in range(cols):
            x0=pad+x*cell
            y0=pad+y*cell
            tid=territory_by_sector.get((x,y))
            topo=topology.get((x,y),{})

            if tid is None:
                if topo.get("status")=="contested":
                    fill=(80,67,92,230)
                    label="CONTEST"
                else:
                    fill=(47,47,53,225)
                    label="NEUT"
                alert=0.0
            else:
                ts=state["territories"][tid]
                alignment=ts["alignment"]
                control=float(ts["control_strength"])
                alert=float(ts["alert"])
                brightness=max(0.45,min(1.0,0.52+control*0.35))

                if alignment=="silt_contamination":
                    base=(35,108,98)
                elif alignment=="print_civic":
                    base=(132,112,58)
                elif alignment=="nano_signal":
                    base=(54,92,128)
                else:
                    base=(70,70,76)

                fill=tuple(int(c*brightness) for c in base)+(230,)
                label=tid.replace("territory_","T")

            draw.rectangle(
                (x0+1,y0+1,x0+cell-2,y0+cell-2),
                fill=fill,
                outline=(205,205,195,75),
            )
            draw.text((x0+4,y0+4),label,fill=(242,232,212,255))

            if tid is not None:
                ts=state["territories"][tid]
                draw.text(
                    (x0+4,y0+cell-28),
                    f"C{ts['control_strength']:.2f}",
                    fill=(205,205,210,255),
                )
                draw.text(
                    (x0+4,y0+cell-15),
                    f"A{ts['alert']:.2f}",
                    fill=(205,205,210,255),
                )

            # local observation availability is marked without implying that
            # any particular NPC has learned it.
            if (x,y) in latest_observed:
                draw.ellipse(
                    (x0+cell-13,y0+4,x0+cell-5,y0+12),
                    fill=(242,232,212,255),
                )

    # Dynamic front site symbols.
    for site in world.get("territory_graph",{}).get("front_sites",[]):
        fid=site["front_id"]
        fs=state.get("fronts",{}).get(fid)
        if not fs:
            continue
        sx,sy=site["sector"]
        cx=pad+sx*cell+cell//2
        cy=pad+sy*cell+cell//2
        width=1
        if fs["status"]=="tense":
            width=2
        elif fs["status"]=="volatile":
            width=3
        draw.rectangle(
            (cx-7,cy-7,cx+7,cy+7),
            outline=(245,245,235,255),
            width=width,
        )
        draw.line((cx-9,cy,cx+9,cy),fill=(245,245,235,220),width=width)
        draw.line((cx,cy-9,cx,cy+9),fill=(245,245,235,220),width=width)

    lx=pad+cols*cell+12
    draw.text((lx,pad),"DYNAMIC WORLD STATE",fill=(240,230,210,255))
    ly=pad+18
    draw.text((lx,ly),f"revision: {state['clock']['revision']}",fill=(205,205,210,255)); ly+=14
    draw.text((lx,ly),f"tick: {state['clock']['tick']}",fill=(205,205,210,255)); ly+=18

    draw.text((lx,ly),"FRONTS",fill=(220,215,200,255)); ly+=15
    for fid,fs in list(sorted(state.get("fronts",{}).items()))[:8]:
        draw.text(
            (lx,ly),
            f"{fid}: {fs['status']} T{fs['tension']:.2f}",
            fill=(175,180,185,255),
        )
        ly+=14

    ly+=4
    draw.text((lx,ly),"TERRITORIES",fill=(220,215,200,255)); ly+=15
    for tid,ts in list(sorted(state.get("territories",{}).items()))[:8]:
        draw.text(
            (lx,ly),
            f"{tid}: {ts['status']}",
            fill=(175,180,185,255),
        )
        ly+=13
        draw.text(
            (lx+8,ly),
            f"C{ts['control_strength']:.2f} S{ts['stability']:.2f} A{ts['alert']:.2f}",
            fill=(145,150,155,255),
        )
        ly+=16

    ly+=4
    draw.text(
        (lx,ly),
        f"derived events: {len(state.get('derived_events',[]))}",
        fill=(205,205,210,255),
    ); ly+=14
    draw.text(
        (lx,ly),
        f"local observations: {len(state.get('observations',[]))}",
        fill=(205,205,210,255),
    )

    return img
