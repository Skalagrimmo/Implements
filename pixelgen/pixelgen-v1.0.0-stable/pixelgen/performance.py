from time import perf_counter
from .gameplay_world import generate_gameplay_world

PERFORMANCE_CONTRACT_VERSION = "0.9.1"


def benchmark_pipeline(profile, seed=7301, cols=6, rows=5, ability_count=4, render_quality="fast"):
    t0 = perf_counter()
    world = generate_gameplay_world(profile, seed, cols, rows, ability_count)
    generation = perf_counter() - t0

    render_seconds = None
    render_size = None
    try:
        from .world_render import render_world
        t1 = perf_counter()
        img = render_world(world, profile, gap=4, quality=render_quality)
        render_seconds = perf_counter() - t1
        render_size = list(img.size)
    except ImportError:
        pass

    return {
        "version": PERFORMANCE_CONTRACT_VERSION,
        "seed": seed,
        "dimensions": [cols, rows],
        "sectors": cols * rows,
        "generation_seconds": generation,
        "render_quality": render_quality,
        "render_seconds": render_seconds,
        "render_size": render_size,
        "renderer_optional": True,
    }
