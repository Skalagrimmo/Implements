# PixelGen v0.6.1 Test Report

## Release status

- v0.5 Hardened + v0.6 + v0.6.1 pytest gate: **15 PASS**
- Legacy v0.2 regression: **PASS**
- Legacy v0.3 regression: **PASS**
- Legacy v0.4 regression: **PASS**
- Legacy v0.5 regression: **PASS**
- v0.6.1 landmark/progression fuzz: **250 worlds PASS**
- Landmark plan determinism: **PASS**
- Cognitive-map determinism: **PASS**
- Gameplay final sector reachable: **True**
- All sectors reachable after progression: **True**

## Canonical 4×3 seed 6060

- local landmarks: **1**
- regional landmarks: **2**
- world landmarks: **1**
- total landmarks: **4 / 12 sectors**
- distinct local placement coordinates: **4**
- unique world anchor: **silt_spire**
- world-anchor sector: **[2, 1]**

The old v0.5/v0.6 pattern of one compulsory large landmark per sector is gone.

## Contract

```text
PROP
→ decoration

LOCAL LANDMARK
→ scene orientation

REGIONAL LANDMARK
→ multi-sector orientation

WORLD LANDMARK
→ unique large-scale cognitive anchor
```

Worlds with at least 4 sectors receive exactly one world-scale anchor.
Regional anchors are sparse and globally spaced.
Local markers are optional and biome-dependent.

## Semantic placement

- `mask_cross` → roadside / near traversal paths
- `printing_press_altar` → civic/path/chapel-adjacent
- `nanolith_shrine` → remote / Silt- or hazard-adjacent
- `printing_cathedral` → prominent civic center
- `silt_spire` → prominent remote Silt anchor

## Cognitive map

World and gameplay commands export an additional `*.cognitive.png`.
It is intentionally schematic and emphasizes cognitive navigation rather than tile-perfect geography.
