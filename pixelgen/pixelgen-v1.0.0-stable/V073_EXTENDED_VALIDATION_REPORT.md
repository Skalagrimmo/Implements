# PixelGen v0.7.3 — Extended Validation Report

This report is a **test-only addendum**. The v0.7.3 source was kept frozen during this pass; no release code was silently changed.

## Executive result

**Core generation / navigation / export integrity is strong.** No hard world-integrity or progression failure was found in the extended soak matrix.

However, the deeper causal tests found **one real semantic defect** and several softer design/hygiene issues:

1. **Printing Cathedral hazard inversion** — `hazard_mult=0.92` can increase final hazards because hazard generation uses a branch-dependent stateful RNG stream.
2. **Nanolith Shrine encounter dead-zone** — `encounter_mult=1.0432` often rounds to the same integer encounter target, producing no actual encounter-count change.
3. **Frozen Pass morphology warning** — seed 7303 / 6×5 is valid and reachable, but the structural analyzer reports too many branches/loops.
4. **Influence saturation on 6×5** — in 60 sampled 6×5 worlds, all 30 sectors were affected by at least one field because six sources with radii 3–5 cover the whole map.
5. **Lua export hygiene** — minimal whole-world / geography / influence Lua exports may contain explicit `nil` for absent optional values. Lua remains syntactically valid, but this is not the nil-free style used by some older scene-export contracts.

These are good candidates for a future **0.7.3.1 hardening patch** rather than a new subsystem.

---

## 1. Regression suite

Combined historical + v0.7.3 pytest gate:

```text
15 passed
```

Covered prior hardening, navigation, landmarks, reproducibility, geography, biome structural grammar, subbiome/ecotone variation, and regional influence fields.

---

## 2. Extended world soak

### Batch A — small / medium

- cases: **240**
- dimensions: 1×1, 2×2, 3×3, 4×3
- seeds: -30…29
- hard failures: **0**

### Batch B — medium

- cases: **120**
- dimensions: 5×4, 6×5
- seeds: -30…29
- hard failures: **0**

Influence source coverage observed:

```json
{
  "silt_spire": 65,
  "printing_press_altar": 291,
  "nanolith_shrine": 189,
  "printing_cathedral": 55
}
```

All four current source kinds appeared in the soak.

### Batch C — large

- cases: **24**
- dimensions: 8×6, 10×8, 12×10
- seeds: 0…7
- hard failures: **0**

### Batch D — 12×12

- cases: **4**
- dimensions: 12×12 / 144 sectors
- seeds: 0, 1, 6060, 7301
- hard failures: **0**

### Extended matrix total

- dedicated extended soak worlds: **388**
- hard failures: **0**

In addition, the normal v0.7.3 fuzz script completed **240 worlds PASS**.

---

## 3. Determinism

Repeated independent generation was checked for **10** cases including:

- negative seeds;
- 1×1;
- 4×3;
- 6×5;
- 8×6;
- 10×8;
- 12×12.

Fingerprint mismatches: **0**.

Canonical mixed influence seed 7301 / 6×5:

```text
af6352af84e4ec44e16b180a9888b309017b1b8acadce79a2d08777dac01afa4
```

---

## 4. Influence field mathematics

Direct field-math checks: **330**

Failures: **0**

Verified:

- monotonic non-increasing falloff;
- positive source-cell influence;
- positive influence through declared radius;
- zero influence after radius;
- finite non-negative channels;
- finite positive density multipliers;
- mixed-source order invariance.

Observed falloff examples:

```text
radius 5 world source:
1.0000
0.6944
0.4444
0.2500
0.1111
0.0278
0.0000

radius 3 regional source (strength 0.72):
0.7200
0.4050
0.1800
0.0450
0.0000
```

---

## 5. Causal scene effects — 500 matched seed pairs per source

This test generated a baseline scene and an influenced scene with the **same seed and same biome/subbiome**, changing only influence modifiers.

### Silt Spire

Modifiers:

```text
hazard ×1.24
props ×1.08
encounters ×1.14
```

500-seed averages:

```text
hazards     23.754 → 28.948   (+5.194)
objects     24.000 → 25.000   (+1)
encounters  12.000 → 13.000   (+1)
```

This behaves in the intended direction.

### Printing Cathedral

Modifiers:

```text
hazard ×0.92
props ×1.18
encounters ×0.94
```

500-seed averages:

```text
hazards     10.098 → 10.902   (+0.804)  ← opposite to intended direction
objects     36.000 → 42.000   (+6)
encounters  16.000 → 15.000   (-1)
```

Hazard pair distribution:

```text
hazards increased: 319 / 500
unchanged:         161 / 500
decreased:          20 / 500
```

### Root cause

Hazard generation uses one stateful RNG stream:

```text
chance to start pocket
↓
if pocket starts, consume extra RNG calls for radius/cells
↓
RNG state for later candidate cells changes
```

Changing the threshold therefore changes not only acceptance probability but the sequence of later random draws. A lower `hazard_mult` is not monotonic for the same seed and, in this sample, is statistically inverted.

**Recommended 0.7.3.1 fix:** make hazard candidate decisions coordinate-stable / branch-independent (for example separate deterministic per-cell draws or independent substreams).

### Nanolith Shrine

Modifiers:

```text
hazard ×1.072
props ×1.036
encounters ×1.0432
```

500-seed averages:

```text
hazards     12.576 → 13.578   (+1.002)
objects     30.000 → 31.000   (+1)
encounters  15.000 → 15.000   (0)
```

The encounter multiplier is currently too small to cross the integer target boundary for this tested scene scale.

**Recommended 0.7.3.1 fix:** stochastic/deterministic fractional rounding or an accumulated density budget, so small influence values are not inert.

---

## 6. Influence distribution across 60 real 6×5 worlds

Samples: **1800 sector-influence records**

Sources per 6×5 world:

```text
min 6
max 6
mean 6
```

Affected sectors:

```text
min 30/30
max 30/30
mean 30/30
```

Observed modifier range:

```text
hazard     0.9138 … 1.2663
props      1.0158 … 1.212
encounters 0.9358 … 1.1544
```

No explosive numeric stacking was observed. The stronger design question is **coverage saturation**: 6×5 currently has no uninfluenced sectors in this 60-world sample.

---

## 7. Structural / visual seed sweep

20 seeds, 6×5, starting at 7300:

- PASS: **19**
- WARN: **1**
- hard errors: **0**

Seed 7303 warning:

```text
frozen_pass: too branch-heavy even after ecotone allowance
frozen_pass: too many loops even after ecotone allowance
```

The world remains fully reachable. This is a morphology-quality warning, not a navigation failure.

---

## 8. Public toolchain

Verified successfully:

```text
doctor
fingerprint
inspect
world-diff self comparison
gameplay-check
seed-sweep
env-log quick --repeat 2
env-log stress
bundle-manifest
bundle-verify
bundle corruption detection
```

Bundle corruption test:

```text
baseline bundle → PASS
modified influence JSON → FAIL correctly detected
```

---

## 9. Stress benchmark

Harness stress suite:

| Case | Size | Generate ms | World render ms | Export I/O ms | Total ms | Render share |
|---|---:|---:|---:|---:|---:|---:|
| tiny | 2×2 | 43.5 | 343.1 | 42.5 | 455.8 | 75.3% |
| reference | 4×3 | 92.4 | 1122.0 | 64.3 | 1316.9 | 85.2% |
| medium | 6×5 | 259.9 | 2314.7 | 163.6 | 2836.4 | 81.6% |
| large | 8×6 | 299.0 | 4108.8 | 309.7 | 4873.1 | 84.3% |
| stress | 10×8 | 634.4 | 6652.0 | 767.6 | 8259.8 | 80.5% |

The main performance bottleneck is clearly **world rendering**, not generation.

### 12×12 full render

Without tracemalloc instrumentation:

```text
generation: 0.936s
world render: 11.148s
total: 12.084s
image: 3884×2924
```

With Python `tracemalloc` enabled:

```text
approx Python peak: 92.77 MB
```

The tracemalloc run substantially inflated timing, so use it only as a rough Python-allocation memory estimate.

---

## 10. Lua export hygiene edge case

A 1×1 seed -777 world with zero influence sources exports valid Lua, but whole-world / geography / influence Lua files include optional `nil` values such as:

```lua
dominant_channel = nil
transition_to = nil
```

This is **not a syntax failure**, and the historical nil-free scene export contract still passes. It is nevertheless worth normalizing in a hardening patch if the goal is consistent Lua tables without explicit absent-value assignments.

---

# Release assessment

### Strong / release-safe areas

```text
world generation
regional connectivity
structural integrity
progression reachability
semantic fingerprint determinism
influence falloff math
source-to-landmark linkage
JSON exports
bundle integrity
large-world generation up to 12×12
```

### Needs hardening

```text
1. hazard RNG causal monotonicity
2. small encounter multipliers lost to integer rounding
3. Frozen Pass rare over-branching warning
4. influence coverage saturation on 6×5
5. optional nil cleanup in whole-world Lua exports
6. render performance dominates at 10×8 / 12×12
```

## Recommendation

Keep **v0.7.3** frozen for the user's live visual testing.

If live testing does not reveal a more important defect, the next release should be:

```text
0.7.3.1 — Influence Hardening
```

focused on causal monotonicity, fractional encounter effects, export hygiene, and possibly influence-radius tuning — **not** a new feature subsystem.
