import json
from pathlib import Path
from .constraints import validate_profile


def hex_to_rgb(value: str):
    if not isinstance(value, str):
        raise TypeError("palette color must be a #RRGGBB string")
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"invalid hex color length: {value!r}")
    try:
        return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))
    except ValueError as e:
        raise ValueError(f"invalid hex color: {value!r}") from e


def load_profile(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"profile not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid profile JSON: {e}") from e
    if not isinstance(data.get("palette"), dict):
        raise ValueError("profile.palette must be an object")
    data["palette_rgb"] = {k: hex_to_rgb(v) for k, v in data["palette"].items()}
    return validate_profile(data)
