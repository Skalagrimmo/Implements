from pathlib import Path

MAX_BATCH_COUNT = 10_000
MAX_PREVIEW_SCALE = 64
MAX_ATLAS_COLUMNS = 256
MAX_WORLD_DIM = 12
MAX_WORLD_SECTORS = 144
MAX_RENDER_PIXELS = 32_000_000


def require_int(name, value, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be <= {maximum}")
    return value


def require_probability(name, value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise TypeError(f"{name} must be a number in [0, 1]")
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be in [0, 1]")
    return value


def validate_world_dimensions(cols, rows):
    cols = require_int("cols", cols, 1, MAX_WORLD_DIM)
    rows = require_int("rows", rows, 1, MAX_WORLD_DIM)
    if cols * rows > MAX_WORLD_SECTORS:
        raise ValueError(f"world has {cols*rows} sectors; maximum is {MAX_WORLD_SECTORS}")
    return cols, rows


def validate_profile(profile):
    if not isinstance(profile, dict):
        raise TypeError("profile must be a dict")
    tile_size = profile.get("tile_size")
    require_int("profile.tile_size", tile_size, 16, 16)
    palette = profile.get("palette_rgb")
    if not isinstance(palette, dict) or not palette:
        raise ValueError("profile.palette_rgb must be a non-empty dict")
    required = {
        "peat_dark","peat_mid","peat_light","moss_dark","moss_mid","moss_light",
        "basalt_dark","basalt_mid","basalt_light","vellum","wax","silt_deep",
        "silt_oil","silt_mid","nano_glow","ice_dark","ice_mid","ice_light"
    }
    missing = sorted(required - set(palette))
    if missing:
        raise ValueError("profile palette is missing: " + ", ".join(missing))
    for key, rgb in palette.items():
        if not (isinstance(rgb, tuple) and len(rgb) == 3 and all(isinstance(c, int) and 0 <= c <= 255 for c in rgb)):
            raise ValueError(f"profile.palette_rgb[{key!r}] must be an RGB tuple")
    return profile


def safe_output_parent(path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
