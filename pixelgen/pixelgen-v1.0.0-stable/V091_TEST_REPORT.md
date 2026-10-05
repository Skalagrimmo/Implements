# PixelGen v0.9.1 — Runtime/Renderer Separation Test Report

## Release gate

A fresh current-tree run completed:

```text
21 curated regression scripts PASS
runtime/renderer separation test PASS
renderer-free PIL-blocked generation PASS
renderer-free runtime_cli import PASS
fast-render determinism PASS
v0.9.1 renderer-free fuzz: 40 worlds PASS
```

The curated suite includes the active regression line from v0.2–v0.4,
hardening, v0.6–v0.9.1. The old standalone `test_v05.py` is intentionally not
counted because it already fails unchanged in the v0.9.0 baseline: its
historical assertion requires exactly one optional hollow after later scene
reservation systems were added. v0.9.1 does not introduce that baseline issue.

## Runtime without Pillow

The dedicated test:

1. removes any environment-preloaded `PIL*` modules;
2. installs an import hook that raises on `PIL` / `PIL.*`;
3. imports `pixelgen.runtime_api`;
4. generates a real 4×3 gameplay world;
5. verifies no Pillow module was loaded by PixelGen.

Result:

```text
PASS
```

`runtime_cli.py` is tested under the same blocked-renderer import policy.

## Canonical semantic parity

Seed 7301 / 6×5:

```text
world fingerprint:
ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a
```

This is the same v0.9.0 canonical semantic fingerprint. Renderer changes do
not alter world semantics.

## Dynamic runtime

`runtime_cli.py state-demo` successfully performs:

```text
semantic world generation
→ initial dynamic state
→ 3 runtime events
→ mutations / derived events / local observations
→ EBE runtime bundle
→ exact replay
```

Observed result:

```text
Replay deterministic: True
```

## Render performance

Actual validation run, seed 7301, 12×12 / 144 sectors:

```text
semantic generation runs:
0.6588 s
0.6111 s
0.6106 s
mean = 0.6268 s
```

World preview:

```text
exact = 6.3767 s
fast  = 0.5340 s
speedup = 11.94×
canvas = 3884 × 2924 in both modes
```

The v0.9.1 test also compares two independent `fast` renders byte-for-byte and
requires equality.

Timing numbers are specific to the validation environment.

## Renderer-free fuzz

```text
40 worlds
22 worlds with a front mutation
all deterministic regeneration checks PASS
all mutated-state replay checks PASS
```

Dimensions exercised:

```text
1×1
2×2
4×3
6×5
8×6
```

## Preserved contracts

The active regression gate still passes:

```text
v0.9 regional corridors
v0.8 dynamic world state / EBE bridge
v0.7.5 territory graph
v0.7.4 influence topology
v0.7.3.1 influence hardening
v0.7.2 subbiome/ecotone structure
v0.7.1 biome structural grammar
v0.7.0 regional geography
v0.6.x reproducibility / interop / landmarks / gameplay
legacy v0.2–v0.4 scripts
```

## Remaining road to 1.0

v0.9.1 deliberately does not freeze schemas yet. The next stabilization step
should focus on:

```text
versioned schema manifest
migration rules
strict compatibility validator
public JSON contract freeze candidate
release packaging / CLI surface freeze
```
