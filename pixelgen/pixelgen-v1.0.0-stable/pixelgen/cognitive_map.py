from PIL import Image, ImageDraw

BIOME_KEYS={
    "silt_marsh":"peat_mid","dark_forest":"moss_dark","frozen_pass":"basalt_light",
    "ruined_settlement":"basalt_mid","reformed_chapel":"peat_light",
}

def _rgba(rgb,a=255): return tuple(rgb)+(a,)
def _sector_center(sx,sy,cw,ch,pad): return (pad+sx*cw+cw//2,pad+sy*ch+ch//2)
def _mid(a,b): return ((a[0]+b[0])//2,(a[1]+b[1])//2)

def _dashed_line(draw,a,b,fill,width=2,dash=5,gap=4):
    x1,y1=a; x2,y2=b; dx=x2-x1; dy=y2-y1
    length=max(abs(dx),abs(dy))
    if length<=0: return
    for start in range(0,length+1,dash+gap):
        end=min(length,start+dash); t1=start/length; t2=end/length
        draw.line((round(x1+dx*t1),round(y1+dy*t1),round(x1+dx*t2),round(y1+dy*t2)),fill=fill,width=width)

def _draw_link(draw,a,b,state,p):
    vellum=_rgba(p["vellum"],175); wax=_rgba(p["wax"],210); glow=_rgba(p["nano_glow"],205); grey=(112,112,120,165)
    x,y=_mid(a,b)
    if state=="open":
        draw.line((*a,*b),fill=vellum,width=2)
    elif state=="gated":
        draw.line((*a,*b),fill=wax,width=2)
        draw.polygon([(x,y-4),(x+4,y),(x,y+4),(x-4,y)],fill=wax)
    elif state=="secret":
        _dashed_line(draw,a,b,glow,2,5,4)
        draw.polygon([(x,y-4),(x+4,y),(x,y+4),(x-4,y)],outline=glow)
    else:
        draw.line((*a,*b),fill=grey,width=1)
        draw.line((x-4,y-4,x+4,y+4),fill=grey,width=2); draw.line((x+4,y-4,x-4,y+4),fill=grey,width=2)

def _draw_landmark(draw,x,y,item,p):
    scope=item.get("scope","local"); kind=item.get("kind"); glow=_rgba(p["nano_glow"]); vellum=_rgba(p["vellum"]); dark=(18,18,22,255)
    if scope=="local":
        draw.line((x-3,y,x+3,y),fill=vellum,width=1); draw.line((x,y-4,x,y+4),fill=vellum,width=1)
        return (x-4,y-5,x+4,y+5)
    if scope=="regional":
        draw.polygon([(x,y-6),(x+6,y),(x,y+6),(x-6,y)],outline=glow,fill=dark)
        return (x-7,y-7,x+7,y+7)
    if kind=="printing_cathedral":
        draw.rectangle((x-8,y-3,x+8,y+6),fill=dark,outline=vellum); draw.rectangle((x-7,y-11,x-3,y+2),fill=dark,outline=vellum); draw.rectangle((x+3,y-11,x+7,y+2),fill=dark,outline=vellum); draw.line((x,y-7,x,y+5),fill=glow,width=2)
        return (x-9,y-12,x+9,y+7)
    draw.polygon([(x,y-13),(x+7,y+7),(x,y+10),(x-7,y+7)],fill=dark,outline=glow); draw.line((x,y-9,x,y+5),fill=glow,width=2)
    return (x-8,y-14,x+8,y+11)

def _intersects(a,b,pad=2):
    return not (a[2]+pad<b[0] or b[2]+pad<a[0] or a[3]+pad<b[1] or b[3]+pad<a[1])

def _place_label(draw,text,anchor,occupied,bounds,fill):
    ax,ay=anchor
    for side,dx,dy in ((1,10,-8),(1,10,3),(-1,-10,-8),(-1,-10,3),(1,-2,-20),(1,-2,14)):
        x=ax+dx; y=ay+dy
        box=draw.textbbox((x,y),text)
        if side<0:
            w=box[2]-box[0]; x-=w; box=draw.textbbox((x,y),text)
        if box[0]<bounds[0] or box[1]<bounds[1] or box[2]>bounds[2] or box[3]>bounds[3]: continue
        if any(_intersects(box,o,2) for o in occupied): continue
        draw.rectangle((box[0]-2,box[1]-1,box[2]+2,box[3]+1),fill=(12,12,15,190)); draw.text((x,y),text,fill=fill); occupied.append(box); return box
    return None

def _draw_legend(draw,x,y,p):
    vellum=_rgba(p["vellum"]); wax=_rgba(p["wax"]); glow=_rgba(p["nano_glow"]); muted=(155,155,160,255)
    draw.text((x,y),"Links:",fill=vellum); y+=15
    draw.line((x,y+5,x+20,y+5),fill=vellum,width=2); draw.text((x+27,y),"open",fill=muted); y+=15
    draw.line((x,y+5,x+20,y+5),fill=wax,width=2); draw.polygon([(x+10,y+1),(x+14,y+5),(x+10,y+9),(x+6,y+5)],fill=wax); draw.text((x+27,y),"gated",fill=muted); y+=15
    _dashed_line(draw,(x,y+5),(x+20,y+5),glow,2,4,3); draw.text((x+27,y),"secret",fill=muted); y+=15
    draw.line((x,y+5,x+20,y+5),fill=(110,110,118,180),width=1); draw.line((x+7,y+1,x+13,y+9),fill=(110,110,118,220),width=1); draw.line((x+13,y+1,x+7,y+9),fill=(110,110,118,220),width=1); draw.text((x+27,y),"sealed",fill=muted); y+=18
    draw.text((x,y),"Landmarks:",fill=vellum); y+=15
    draw.line((x+10,y+1,x+10,y+9),fill=vellum,width=1); draw.line((x+6,y+5,x+14,y+5),fill=vellum,width=1); draw.text((x+27,y),"local",fill=muted); y+=15
    draw.polygon([(x+10,y),(x+16,y+5),(x+10,y+10),(x+4,y+5)],outline=glow); draw.text((x+27,y),"regional",fill=muted); y+=15
    draw.polygon([(x+10,y-1),(x+16,y+8),(x+10,y+11),(x+4,y+8)],outline=glow); draw.text((x+27,y),"world",fill=muted)

def render_cognitive_map(world,profile,cell_w=78,cell_h=58,pad=12):
    p=profile["palette_rgb"]; cols,rows=world["cols"],world["rows"]; map_w=cols*cell_w; legend_w=118; footer_h=28
    W=pad*2+map_w+legend_w; H=pad*2+rows*cell_h+footer_h
    img=Image.new("RGBA",(W,H),(15,15,18,255)); draw=ImageDraw.Draw(img)
    for s in world["sectors"]:
        x0=pad+s["sx"]*cell_w; y0=pad+s["sy"]*cell_h; key=BIOME_KEYS.get(s["biome"],"basalt_mid")
        draw.rectangle((x0+1,y0+1,x0+cell_w-2,y0+cell_h-2),fill=_rgba(p[key],215),outline=(210,210,205,80))

    # v0.7 regional borders: thick dark seams between geographic masses.
    sector_lookup={(s["sx"],s["sy"]):s for s in world["sectors"]}
    for (sx0,sy0),s in sector_lookup.items():
        rid=s.get("region_id")
        if rid is None:
            continue
        x0=pad+sx0*cell_w; y0=pad+sy0*cell_h
        east=sector_lookup.get((sx0+1,sy0))
        south=sector_lookup.get((sx0,sy0+1))
        if east is not None and east.get("region_id")!=rid:
            draw.line((x0+cell_w,y0,x0+cell_w,y0+cell_h),fill=(25,25,30,235),width=4)
        if south is not None and south.get("region_id")!=rid:
            draw.line((x0,y0+cell_h,x0+cell_w,y0+cell_h),fill=(25,25,30,235),width=4)

    handled=set()
    for s in world["sectors"]:
        a=(s["sx"],s["sy"]); ca=_sector_center(*a,cell_w,cell_h,pad)
        for edge,link in s["links"].items():
            b=tuple(link["to"]); pair=tuple(sorted((a,b)))
            if pair in handled: continue
            handled.add(pair); cb=_sector_center(*b,cell_w,cell_h,pad); state=link.get("gameplay",{}).get("state","open"); _draw_link(draw,ca,cb,state,p)
    gp=world.get("gameplay",{}); start=tuple(gp.get("start_sector",[0,0])); final=tuple(gp.get("final_sector",[cols-1,rows-1])); sx,sy=_sector_center(*start,cell_w,cell_h,pad); fx,fy=_sector_center(*final,cell_w,cell_h,pad)
    draw.ellipse((sx-5,sy-5,sx+5,sy+5),fill=_rgba(p["vellum"]),outline=(20,20,20,255)); draw.rectangle((fx-5,fy-5,fx+5,fy+5),outline=_rgba(p["nano_glow"]),width=2)
    occupied=[]; labels=[]
    for s in world["sectors"]:
        x0=pad+s["sx"]*cell_w; y0=pad+s["sy"]*cell_h
        for item in s["scene"].get("landmarks",{}).values():
            px=x0+int((item["x"]+0.5)/s["scene"]["width"]*cell_w); py=y0+int((item["y"]+0.5)/s["scene"]["height"]*cell_h); occupied.append(_draw_landmark(draw,px,py,item,p))
            if item.get("scope") in ("regional","world"): labels.append((item.get("prominence",0),item,(px,py)))
    labels.sort(reverse=True,key=lambda z:z[0]); bounds=(pad,pad,pad+map_w-2,pad+rows*cell_h-2)
    for _,item,anchor in labels: _place_label(draw,item.get("map_label",item["kind"]),anchor,occupied,bounds,_rgba(p["vellum"]))
    _draw_legend(draw,pad+map_w+12,pad,p); draw.text((pad,pad+rows*cell_h+7),"● start   □ final   thick seams = geographic region borders",fill=(180,180,185,255))
    return img
