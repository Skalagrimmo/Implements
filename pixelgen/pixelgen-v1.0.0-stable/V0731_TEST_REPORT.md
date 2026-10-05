# PixelGen v0.7.3.1 — Influence Hardening Test Report

## Release gate

- combined regression tests: **15 PASS**
- causal hazard monotonicity triplets: **1500**
- hazard monotonicity violations: **0**
- causal encounter monotonicity triplets: **1500**
- encounter monotonicity violations: **0**
- final world/audit soak: **120 worlds**
- hard world failures: **0**
- remaining audit warnings: **3**
- 12×12 hardening samples: **4 PASS**
- Lua optional-value `nil` hits: **0**

## 1. Causal monotonicity

Across all five primary biomes:

```text
hazard ×0.92 <= hazard ×1.00 <= hazard ×1.24
```

was checked for **300 seeds per biome**.

Violations:

```text
0 / 1500
```

Encounter targets were checked with:

```text
×0.94
×1.00
×1.0432
```

Violations:

```text
0 / 1500
```

The small `×1.0432` multiplier produced actual higher encounter counts in:

- `silt_marsh`: **155 / 300** seeds
- `dark_forest`: **196 / 300** seeds
- `frozen_pass`: **168 / 300** seeds
- `ruined_settlement`: **211 / 300** seeds
- `reformed_chapel`: **138 / 300** seeds

## 2. Full source effects — 500 matched seed pairs

### Printing Cathedral

```text
hazards:    -6.620
objects:    +6.000
encounters: -0.992
```

Hazards were lower in:

```text
500/500
```

and higher in:

```text
0/500
```

### Silt Spire

```text
hazards:    +10.134
objects:    +1.000
encounters: +1.660
```

### Nanolith Shrine

```text
hazards:    +0.630
objects:    +1.000
encounters: +0.628
```

The Nanolith encounter effect is no longer truncated to zero.

## 3. Morphology soak

Final 120-world audit soak:

```text
2×2
4×3
6×5
8×6
seeds 0…29
```

Hard failures:

```text
0
```

Structural morphology warnings:

```text
0
```

Remaining warnings were only landmark quadrant-concentration heuristics:

```json
{
  "landmark quadrant concentration is high (77%)": 1,
  "landmark quadrant concentration is high (75%)": 1,
  "landmark quadrant concentration is high (83%)": 1
}
```

The previous known Frozen Pass seed:

```text
7303 / 6×5
```

now passes the 20-seed canonical sweep with score 100/A and zero warnings.

## 4. Large worlds

12×12 / 144-sector samples:

- seed `0` — **PASS** — 1.292 s generation — `943f0871a43951c84d6443709ec377bab560a507cf3ba781bfb29475e7e7458b`
- seed `1` — **PASS** — 1.125 s generation — `25688e907b849d48fdb4bcb8437e0eaf1169f81a8541425d4f5aefdb9d049242`
- seed `6060` — **PASS** — 1.159 s generation — `1fc29ba23e38fa4e999d85519b5c906cabb605d42d8ffe8c0c433067ac38ccf4`
- seed `7301` — **PASS** — 1.55 s generation — `6a3ba8bda6e2afceb8af120749395c671e85930d96a7c52a609259cc42687cb4`

## 5. Canonical hardening demo

Seed 7301 / 6×5:

```text
fingerprint: 18908b906a1056e538dbe2d566801bbd11356579b9f61b0ba5c28d1bfad6669c
regions: 3
structural score: 100/100
visual score: 100/100
influence sources: 6
affected sectors: 30
```

Influence coverage remains 30/30 by design in this patch.

## 6. Lua export

A minimal 1×1 world with zero influence sources was exported through the public CLI.

Checked Lua files:

```text
world
geography
influence
progression
```

Explicit `nil` hits:

```text
0
```

## Assessment

0.7.3.1 closes the correctness defects found in the extended 0.7.3 validation pass.

The main intentionally unresolved design question is **influence coverage saturation on small/medium worlds**. It should be judged from live play/visual testing before changing radii.
