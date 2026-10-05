# PixelGen v0.6.2 Test Report

## Release gate

- v0.5 Hardened + v0.6 + v0.6.1 + v0.6.2 pytest gate: **15 PASS**
- Legacy v0.2 regression: **PASS**
- Legacy v0.3 regression: **PASS**
- Legacy v0.4 regression: **PASS**
- Legacy v0.5 regression: **PASS**
- v0.6.2 fuzz: **250 worlds PASS**
- Fuzz worlds with artistic warnings (non-fatal): **12 / 250**
- Canonical gameplay validation: **PASS**
- Final sector reachable: **True**
- All sectors reachable: **True**
- Deterministic PNG/JSON/Lua/progression/cognitive/quality outputs: **PASS**

## Canonical 4×3 seed 6060

- local landmarks: **3**
- regional landmarks: **2**
- world landmarks: **1**
- visual-quality status: **PASS**
- visual repetition score: **83 / 100**
- dominant landmark quadrant share: **67%**
- exact repeated local-coordinate share: **17%**
- minimum regional sector distance: **5**

## Cognitive navigation grammar

```text
open    = pale solid link
gated   = wax link + filled diamond
secret  = dashed nano link + hollow diamond
sealed  = muted link + X
```

Landmark hierarchy:

```text
local    = small cross, prominence 25
regional = diamond + collision-aware label, prominence 60
world    = unique silhouette + priority label, prominence 100
```

## Visual-pattern validator

`visual-check` is intentionally an artistic warning system rather than a structural-failure system. It flags suspicious patterns such as:

- too many landmarks in the same quadrant;
- too many identical local coordinates;
- regional anchors packed too closely;
- landmark density high enough to reduce salience.

Warnings do **not** mean the generated world is unplayable. Gameplay/topology validation remains separate.
