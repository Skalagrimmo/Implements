from PIL import Image, ImageDraw
from .rng import SeededRNG
from .structural import *
from .constraints import require_int

def _p(profile):
    p=profile["palette_rgb"]
    return {
        "wood_dark":rgba(p["peat_dark"]),
        "wood":rgba(p["peat_mid"]),
        "wood_light":rgba(p["peat_light"]),
        "iron":rgba(p["basalt_dark"]),
        "iron2":rgba(p["basalt_mid"]),
        "paper":rgba(p["vellum"]),
        "wax":rgba(p["wax"]),
        "bone":rgba((217,200,169)),
        "silt":rgba(p["silt_deep"]),
        "oil":rgba(p["silt_oil"]),
        "glow":rgba(p["nano_glow"]),
        "amber":rgba((220,145,58)),
        "amber2":rgba((255,196,92)),
        "glass":rgba((122,158,158),190),
    }

def generate_prop(profile, seed=0, kind="brazier_lit"):
    seed=require_int("seed",seed)
    sizes={
        "brazier_lit":(16,32),
        "brazier_off":(16,32),
        "paper_stack":(16,16),
        "chest":(32,32),
        "nano_capsule_broken":(32,32),
        "skull_stake_a":(16,32),
        "skull_stake_b":(16,32),
        "biogel_barrel":(16,32),
        "biogel_barrel_leaking":(32,32),
        "ritual_mask":(16,16),
        "warning_board":(32,32),
        "silt_growth":(16,16),
    }
    if kind not in sizes:
        raise ValueError(f"Unknown prop kind: {kind}")
    rng=SeededRNG(seed)
    p=_p(profile)
    w,h=sizes[kind]
    img=new_canvas(w,h)

    if kind.startswith("brazier"):
        # tripod + bowl
        rect(img,(3,16,12,21),p["iron"])
        rect(img,(5,21,10,23),p["iron2"])
        line(img,[(5,23),(2,31)],p["iron"])
        line(img,[(10,23),(13,31)],p["iron"])
        line(img,[(8,23),(8,31)],p["iron"])
        if kind=="brazier_lit":
            # warm flame, stylized and non-realistic
            rect(img,(6,9,9,15),p["amber"])
            pixel(img,7,7,p["amber2"]); pixel(img,8,8,p["amber2"])
            pixel(img,5,12,p["amber"])
            pixel(img,10,11,p["amber"])

    elif kind=="paper_stack":
        for off in range(3):
            draw_paper(img,2+off,5-off,11,7,p["paper"],p["silt"],p["wax"] if off==2 else None)

    elif kind=="chest":
        rect(img,(4,12,27,27),p["wood"])
        rect(img,(4,10,27,15),p["wood_light"])
        rect(img,(4,14,27,16),p["iron"])
        rect(img,(7,10,8,27),p["iron"])
        rect(img,(23,10,24,27),p["iron"])
        rect(img,(14,16,17,20),p["wax"])

    elif kind=="nano_capsule_broken":
        # broken capsule base
        rect(img,(6,8,25,26),p["glass"])
        for y in range(10,24):
            if rng.chance(0.5): pixel(img,7,y,p["iron2"])
            if rng.chance(0.5): pixel(img,24,y,p["iron2"])
        # broken top opening
        for x in range(10,22):
            img.putpixel((x,8),(0,0,0,0))
        draw_silt_creep(img,rng,9,16,14,10,p["silt"],p["oil"],p["glow"],0.18)

    elif kind.startswith("skull_stake"):
        rect(img,(7,15,8,31),p["wood"])
        draw_skull_hint(img,8,11,p["bone"],p["silt"])
        if kind.endswith("_b"):
            for y in range(16,25,2):
                pixel(img,9,y,p["glow"])

    elif kind.startswith("biogel_barrel"):
        rect(img,(4,8,11,29),p["wood"])
        rect(img,(3,10,12,12),p["iron"])
        rect(img,(3,23,12,25),p["iron"])
        rect(img,(5,14,10,21),p["oil"])
        pixel(img,7,16,p["glow"])
        if kind.endswith("leaking"):
            # puddle in larger canvas
            for x in range(10,27):
                if rng.chance(0.65): pixel(img,x,27+rng.randint(-1,2),p["oil"])
            for x in (18,21,24):
                if rng.chance(0.7): pixel(img,x,28,p["glow"])

    elif kind=="ritual_mask":
        rect(img,(3,3,12,13),p["bone"])
        rect(img,(4,2,11,4),p["wood_light"])
        rect(img,(4,7,11,8),p["wood_dark"])

    elif kind=="warning_board":
        rect(img,(5,9,26,24),p["wood"])
        rect(img,(14,24,17,31),p["wood_dark"])
        for i in range(3):
            draw_paper(img,7+i*6,11+(i%2),5,8,p["paper"],p["silt"],p["wax"] if i==1 else None)

    elif kind=="silt_growth":
        draw_silt_creep(img,rng,1,5,14,10,p["silt"],p["oil"],p["glow"],0.30)

    return img
