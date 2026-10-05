from PIL import Image

def composite(base, *overlays):
    out=base.convert("RGBA")
    for ov in overlays:
        out.alpha_composite(ov.convert("RGBA"))
    return out
