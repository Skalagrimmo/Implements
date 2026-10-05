# PixelGen v0.7.0 — Regional Geography Test Report

## Regression gate

- v0.5 Hardened + v0.6.0–v0.6.4.2 + v0.7.0 combined pytest gate: **15 PASS**
- legacy world/navigation/progression contracts: **PASS**
- `doctor`: **PASS**
- `gameplay-demo`: **PASS**
- `gameplay-check`: **PASS**
- `inspect` on geography-aware export: **PASS**
- `geography-demo`: **PASS**

## Geography fuzz

Two release batches were completed:

```text
200 worlds
dimensions:
1×1
2×2
3×3
4×3
6×5

40 larger worlds
dimensions:
8×6
10×8
```

Total v0.7 geography fuzz worlds: **240**  
Hard geography failures: **0**  
Gameplay/progression failures: **0**

## Canonical 6×5 seed 7000

- sectors: **30**
- regions: **3**
- region-transition pairs: **3**
- transition/ecotone sectors: **14**
- distinct subbiomes: **12**

Regions:

- R0 — `frozen_pass` — **16 sectors** — Zblidli Perevaly — Pale Heights 1
- R1 — `ruined_settlement` — **10 sectors** — Pospaleni Slobody — Burnt Quarter 2
- R2 — `dark_forest` — **4 sectors** — Chervonolis — March 3

## Connectivity bug caught during development

The first 0.7 regional prototype used noisy weighted Voronoi assignment.

The old hardening matrix found a seed in which one region was split into disconnected islands.

Release fix:

```text
weighted Voronoi
→ removed

multi-source weighted flood growth
→ adopted
```

The final geography validator explicitly checks 4-neighbor connectivity for every region.

## Canonical semantic identity

The canonical v0.7 world export has generator metadata:

```json
"generator": {
  "name": "PixelGen",
  "version": "0.7.0"
}
```

Its geography is included in semantic fingerprinting, so changing region shape, subbiomes or transition structure changes world identity.
