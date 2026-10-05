from PIL import Image, ImageDraw
from .rng import SeededRNG
from .structural import *
from .constraints import require_int

def _pal(profile):
    p=profile["palette_rgb"]
    return {
        "peat": rgba(p["peat_dark"]),
        "wood_dark": rgba(p["peat_dark"]),
        "wood_mid": rgba(p["peat_mid"]),
        "wood_light": rgba(p["peat_light"]),
        "moss": rgba(p["moss_dark"]),
        "basalt_dark": rgba(p["basalt_dark"]),
        "basalt_mid": rgba(p["basalt_mid"]),
        "basalt_light": rgba(p["basalt_light"]),
        "vellum": rgba(p["vellum"]),
        "wax": rgba(p["wax"]),
        "bone": rgba((217,200,169)),
        "iron": rgba((35,40,45)),
        "silt": rgba(p["silt_deep"]),
        "oil": rgba(p["silt_oil"]),
        "glow": rgba(p["nano_glow"]),
    }

def generate_cliff(profile, seed=0, variant="straight"):
    seed=require_int("seed",seed)
    if variant not in ("straight","corner_inner","corner_outer","broken","silt"):
        raise ValueError(f"Unknown cliff variant: {variant}")
    rng=SeededRNG(seed)
    p=_pal(profile)
    if variant=="straight":
        w,h=16,48
    elif variant in ("corner_inner","corner_outer","broken"):
        w,h=32,48
    else:
        w,h=16,48
    img=new_canvas(w,h)
    jagged_vertical_face(img,0,0,w,h,rng,p["basalt_dark"],p["basalt_mid"],p["basalt_light"])

    if variant=="corner_inner":
        rect(img,(0,0,7,h-1),p["basalt_dark"])
        rect(img,(8,0,w-1,3),p["basalt_light"])
    elif variant=="corner_outer":
        for y in range(h):
            cut=max(0,7-y//6)
            for x in range(cut):
                img.putpixel((x,y),(0,0,0,0))
    elif variant=="broken":
        gap_x=w//2
        for y in range(h//2,h):
            radius=max(1,(y-h//2)//6)
            for x in range(gap_x-radius,gap_x+radius+1):
                if 0<=x<w: img.putpixel((x,y),(0,0,0,0))
    elif variant=="silt":
        draw_silt_creep(img,rng,0,4,w,h-6,p["silt"],p["oil"],p["glow"],0.10)
    return img

def generate_timber_wall(profile, seed=0, variant="straight"):
    seed=require_int("seed",seed)
    if variant not in ("straight","corner_inner","corner_outer","broken","doorway"):
        raise ValueError(f"Unknown timber wall variant: {variant}")
    rng=SeededRNG(seed)
    p=_pal(profile)
    if variant=="doorway":
        w,h=48,48
    elif variant in ("corner_inner","corner_outer","broken"):
        w,h=32,48
    else:
        w,h=16,48
    img=new_canvas(w,h)
    timber_face(img,0,0,w,h,rng,p["wood_dark"],p["wood_mid"],p["wood_light"],p["iron"],p["wax"])

    if variant=="doorway":
        dx0,dx1=17,30
        for y in range(20,h):
            for x in range(dx0,dx1+1):
                img.putpixel((x,y),(0,0,0,0))
        rect(img,(dx0-2,18,dx1+2,20),p["iron"])
    elif variant=="broken":
        for y in range(16,h):
            center=w//2+rng.choice((-1,0,1))
            width=max(1,(y-16)//8)
            for x in range(center-width,center+width+1):
                if 0<=x<w:
                    img.putpixel((x,y),(0,0,0,0))
    elif variant=="corner_outer":
        for y in range(h):
            cut=max(0,5-y//8)
            for x in range(cut):
                img.putpixel((x,y),(0,0,0,0))
    elif variant=="corner_inner":
        rect(img,(0,0,5,h-1),p["wood_dark"])
    return img

def generate_nanolith_shrine(profile, seed=0):
    seed=require_int("seed",seed)
    rng=SeededRNG(seed)
    p=_pal(profile)
    w,h=48,64
    img=new_canvas(w,h)

    # base + timber frame
    rect(img,(6,46,41,61),p["wood_mid"])
    rect(img,(8,12,12,53),p["wood_mid"])
    rect(img,(35,12,39,53),p["wood_mid"])
    rect(img,(8,10,39,14),p["wood_light"])
    rect(img,(5,58,42,63),p["wood_dark"])

    # nanolith
    draw_nanolith(img,16,20,16,32,p["silt"],p["oil"],p["glow"])

    # ropes
    draw_rope(img,9,14,38,48,p["bone"])
    draw_rope(img,38,14,10,48,p["bone"])

    # papers/wax
    draw_paper(img,3,25,6,7,p["vellum"],p["silt"],p["wax"])
    draw_paper(img,39,31,6,7,p["vellum"],p["silt"],p["wax"])
    # skull hints
    draw_skull_hint(img,8,18,p["bone"],p["silt"])
    draw_skull_hint(img,40,18,p["bone"],p["silt"])
    return img

def generate_printing_press_altar(profile, seed=0):
    seed=require_int("seed",seed)
    rng=SeededRNG(seed)
    p=_pal(profile)
    w,h=64,64
    img=new_canvas(w,h)

    # platform
    rect(img,(6,48,57,61),p["wood_mid"])
    rect(img,(6,60,57,63),p["wood_dark"])

    # uprights
    rect(img,(11,18,17,50),p["iron"])
    rect(img,(46,18,52,50),p["iron"])

    # top beam
    rect(img,(9,14,54,21),p["iron"])

    # screw
    rect(img,(30,6,33,36),p["basalt_light"])
    rect(img,(24,8,39,11),p["iron"])
    rect(img,(18,10,45,12),p["iron"])

    # press plate
    rect(img,(20,32,43,37),p["iron"])
    rect(img,(18,40,45,47),p["wood_light"])

    # papers / wax
    draw_paper(img,8,51,10,6,p["vellum"],p["silt"],p["wax"])
    draw_paper(img,42,50,11,7,p["vellum"],p["silt"],p["wax"])
    draw_paper(img,24,54,12,5,p["vellum"],p["silt"],p["wax"])

    # ink tub
    rect(img,(54,45,61,54),p["iron"])
    rect(img,(55,46,60,49),p["silt"])
    return img

def generate_mask_cross(profile, seed=0):
    seed=require_int("seed",seed)
    rng=SeededRNG(seed)
    p=_pal(profile)
    w,h=32,64
    img=new_canvas(w,h)
    rect(img,(14,6,18,61),p["wood_mid"])
    rect(img,(5,18,27,22),p["wood_mid"])
    rect(img,(13,60,19,63),p["wood_dark"])

    # mask
    rect(img,(10,24,22,37),p["bone"])
    rect(img,(12,22,20,25),p["wood_light"])
    # eyeless slash
    rect(img,(11,29,21,30),p["wood_dark"])

    draw_paper(img,3,34,6,8,p["vellum"],p["silt"],p["wax"])
    draw_paper(img,24,27,6,8,p["vellum"],p["silt"],p["wax"])

    # fiber strands
    for x in (14,16,18):
        for y in range(39,53):
            if y%2==0:
                pixel(img,x,y,p["glow"])
    return img


def generate_printing_cathedral(profile, seed=0):
    seed=require_int("seed",seed)
    rng=SeededRNG(seed)
    p=_pal(profile)
    w,h=96,96
    img=new_canvas(w,h)

    # Wide stepped platform.
    rect(img,(8,76,87,91),p["wood_mid"])
    rect(img,(5,90,90,95),p["wood_dark"])

    # Twin print-towers form a strong minimap/silhouette identity.
    for x0 in (14,68):
        rect(img,(x0,28,x0+13,79),p["iron"])
        rect(img,(x0+3,16,x0+10,31),p["basalt_mid"])
        rect(img,(x0+5,8,x0+8,17),p["basalt_light"])
        rect(img,(x0-3,25,x0+16,29),p["wood_light"])

    # Central press nave.
    rect(img,(31,34,64,78),p["wood_mid"])
    rect(img,(36,28,59,36),p["iron"])
    rect(img,(45,13,50,58),p["basalt_light"])
    rect(img,(38,17,57,21),p["iron"])
    rect(img,(34,51,61,57),p["iron"])
    rect(img,(31,61,64,70),p["wood_light"])

    # Dark Silt "apse" behind the press.
    draw_nanolith(img,40,36,16,31,p["silt"],p["oil"],p["glow"])

    # Papers and ritual seals keep the Print identity visible.
    for x,y in ((10,80),(24,83),(58,82),(74,79),(43,72)):
        draw_paper(img,x,y,10,6,p["vellum"],p["silt"],p["wax"])
    return img

def generate_silt_spire(profile, seed=0):
    seed=require_int("seed",seed)
    rng=SeededRNG(seed)
    p=_pal(profile)
    w,h=64,96
    img=new_canvas(w,h)

    # Low ritual footing.
    rect(img,(9,79,54,91),p["wood_mid"])
    rect(img,(6,90,57,95),p["wood_dark"])

    # Irregular layered Silt monolith; broad bottom, narrow crown.
    layers=[
        (18,24,45,84),
        (22,14,41,72),
        (27,6,36,57),
    ]
    for x0,y0,x1,y1 in layers:
        rect(img,(x0,y0,x1,y1),p["silt"])
        rect(img,(x0+2,y0+3,x1-2,y1-2),p["oil"])

    # Sparse ideal geometry hints.
    for y in range(20,78,11):
        x=31 + rng.choice((-5,-3,0,3,5))
        pixel(img,x,y,p["glow"])
        if y % 22 == 0:
            line(img,(x-5,y,x+5,y),p["glow"])

    draw_rope(img,14,35,48,79,p["bone"])
    draw_rope(img,49,34,16,80,p["bone"])
    draw_paper(img,5,68,8,9,p["vellum"],p["silt"],p["wax"])
    draw_paper(img,52,59,8,9,p["vellum"],p["silt"],p["wax"])
    return img
