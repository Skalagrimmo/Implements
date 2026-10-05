"""Optional rendering facade.

Importing this module itself does not import Pillow.  Pillow-backed modules are
loaded only when a render function is actually called.
"""
from pathlib import Path

RENDER_API_VERSION = "0.9.1"


def renderer_status():
    try:
        import PIL  # noqa: F401
        return {"available": True, "backend": "Pillow", "version": RENDER_API_VERSION}
    except Exception as exc:
        return {"available": False, "backend": "Pillow", "version": RENDER_API_VERSION, "error": str(exc)}


def _require_renderer():
    status = renderer_status()
    if not status["available"]:
        raise RuntimeError(
            "PixelGen renderer is optional and Pillow is unavailable. "
            "Use runtime_cli.py for renderer-free generation or install Pillow."
        )


def render_world_preview(world, profile, gap=4, quality="fast"):
    _require_renderer()
    from .world_render import render_world
    return render_world(world, profile, gap=gap, quality=quality)


def render_diagnostic_bundle(world, profile, base, quality="fast", include_world=True):
    _require_renderer()
    base = Path(base)
    base.parent.mkdir(parents=True, exist_ok=True)
    outputs = {}

    if include_world:
        img = render_world_preview(world, profile, gap=4, quality=quality)
        path = Path(str(base) + ".png")
        img.save(path)
        outputs["world"] = str(path)

    from .geography_render import render_geography_map
    from .influence_render import render_influence_map
    from .topology_render import render_topology_map
    from .territory_render import render_territory_map
    from .corridor_render import render_corridor_map

    maps = {
        "geography": render_geography_map,
        "influence": render_influence_map,
        "topology": render_topology_map,
        "territory": render_territory_map,
        "corridors": render_corridor_map,
    }
    for suffix, fn in maps.items():
        path = Path(str(base) + f".{suffix}.png")
        fn(world, profile).save(path)
        outputs[suffix] = str(path)
    return outputs


__all__ = [
    "RENDER_API_VERSION",
    "renderer_status",
    "render_world_preview",
    "render_diagnostic_bundle",
]
