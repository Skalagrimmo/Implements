def luminance(rgb):
    r,g,b=rgb[:3]
    return 0.2126*r+0.7152*g+0.0722*b


def _pixels(img):
    getter=getattr(img,"get_flattened_data",None)
    return getter() if getter else img.getdata()


def _opaque_rgb_pixels(img):
    rgba=img.convert("RGBA")
    return [(r,g,b) for r,g,b,a in _pixels(rgba) if a > 0]


def contrast_delta(img):
    vals=[luminance(px) for px in _opaque_rgb_pixels(img)]
    if not vals: return 0.0
    return (max(vals)-min(vals))/255.0


def palette_usage(img,profile):
    pal=set(profile["palette_rgb"].values())
    pixels=_opaque_rgb_pixels(img)
    if not pixels: return 1.0
    return sum(1 for px in pixels if px in pal)/len(pixels)


def nano_glow_coverage(img,profile):
    glow=profile["palette_rgb"]["nano_glow"]
    pixels=_opaque_rgb_pixels(img)
    if not pixels: return 0.0
    return sum(1 for px in pixels if px==glow)/len(pixels)


def validate_tile(img,profile,floor=False):
    rules=profile.get("rules",{})
    result={
        "palette_usage":round(palette_usage(img,profile),4),
        "contrast_delta":round(contrast_delta(img),4),
        "nano_glow_coverage":round(nano_glow_coverage(img,profile),4),
        "ok":True,"warnings":[],
    }
    if floor:
        lim=float(rules.get("floor_max_contrast",0.22))
        if result["contrast_delta"]>lim:
            result["warnings"].append(f"floor contrast {result['contrast_delta']:.3f} > {lim:.3f}")
    glow_lim=float(rules.get("nano_glow_max_coverage",0.10))
    if result["nano_glow_coverage"]>glow_lim:
        result["warnings"].append(f"nano glow {result['nano_glow_coverage']:.3f} > {glow_lim:.3f}")
    if result["palette_usage"] < 0.999:
        result["warnings"].append(f"palette usage {result['palette_usage']:.3f} < 0.999")
    result["ok"]=not result["warnings"]
    return result
