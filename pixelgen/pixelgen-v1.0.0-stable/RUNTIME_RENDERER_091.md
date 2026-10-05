# PixelGen v0.9.1 — Runtime / Renderer Separation Contract

## Purpose

PixelGen now exposes two explicit public surfaces:

```text
SEMANTIC RUNTIME
pixelgen.runtime_api
runtime_cli.py

OPTIONAL RENDERER
pixelgen.render_api
render_cli.py
```

The semantic runtime owns world generation, progression, dynamic state, replay,
fingerprints, and EBE handoff. It does **not** require Pillow.

The renderer consumes an already-generated semantic world and produces visual
artifacts. It may be absent entirely on a headless/server/Termux runtime.

## Renderer-free runtime

```python
from pixelgen.runtime_api import (
    load_runtime_profile,
    generate_semantic_world,
    initialize_state,
    apply_event,
    replay_events,
)
```

A dedicated regression test removes any preloaded `PIL*` modules, installs an
import blocker that raises on every Pillow import, then imports the runtime API
and generates a real 4×3 world successfully.

This is the core v0.9.1 invariant:

```text
world semantics
!=
PNG availability
```

## Renderer facade

```python
from pixelgen.render_api import render_world_preview

img = render_world_preview(
    world,
    profile,
    quality="fast",
)
```

Two quality modes are available:

```text
exact
  historical per-cell/per-object seeded rendering

fast
  deterministic bounded asset-variant pool
```

Both modes render the same semantic world and the same canvas geometry.
`fast` changes only cosmetic PNG realization; it does not mutate or rewrite
world data.

## Fast preview cache

The fast path uses `RenderAssetCache` and reuses a small deterministic pool for:

```text
terrain/path tiles
structure sprites
prop sprites
```

A semantic cell seed is mapped deterministically to one pooled variant.
No runtime world field is changed.

## CLI split

Renderer-free:

```bash
python runtime_cli.py world --cols 6 --rows 5 --seed 7301 --out generated/runtime
python runtime_cli.py state-demo --cols 6 --rows 5 --seed 7301
python runtime_cli.py benchmark --cols 12 --rows 12 --seed 7301 --runs 3
```

Renderer process:

```bash
python render_cli.py world \
  --world generated/runtime/gameplay_6x5_seed7301.json \
  --out generated/runtime/gameplay.fast.png \
  --quality fast
```

Diagnostic render bundle:

```bash
python render_cli.py bundle \
  --world world.json \
  --out generated/diagnostic/world \
  --quality fast
```

The historical all-in-one `cli.py` remains available for compatibility.

## Performance result

Validation environment, 12×12 / 144 sectors, seed 7301:

```text
semantic generation mean (3 runs): ~0.627 s
exact world preview:              ~6.377 s
fast world preview:               ~0.534 s
measured preview speedup:         ~11.94×
```

These are environment-specific validation measurements, not device benchmarks.

## Version boundary

The following schemas remain unchanged:

```text
regional_corridors = 0.9.0
dynamic_world_state = 0.8.0
territory_graph = 0.7.5
```

New API contracts:

```text
runtime_api = 0.9.1
render_api  = 0.9.1
```

The canonical 7301 / 6×5 semantic world fingerprint remains:

```text
ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a
```

So v0.9.1 is a runtime/rendering hardening release, not a new world-generation
mechanic.
