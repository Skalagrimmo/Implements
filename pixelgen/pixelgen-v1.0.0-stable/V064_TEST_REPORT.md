# PixelGen v0.6.4 — Reproducibility / Interop Test Report

## Release gate

- Combined v0.5 Hardened + v0.6.0–v0.6.4 pytest gate: **15 PASS**
- Legacy v0.2 regression: **PASS**
- Legacy v0.3 regression: **PASS**
- Legacy v0.4 regression: **PASS**
- Legacy v0.5 regression: **PASS**
- v0.6.4 fuzz: **200 worlds PASS**
- `doctor`: **PASS**
- `inspect`: **PASS**
- `fingerprint`: **PASS**
- `world-diff`: **PASS**
- `bundle-manifest`: **PASS**
- `bundle-verify`: **PASS**

## Reference seed 6401

- semantic fingerprint: `9ca5ee610374c75406390c054887d9aa6752e92f60456748d15782c39db54197`
- world size: **4×3 / 12 sectors**
- objects: **312**
- landmarks: **6**
- encounters: **159**
- finds: **60**
- main path nodes: **11**
- visual score: **95/100 (A)**

## Different-seed comparison

Seed 6401:

`9ca5ee610374c75406390c054887d9aa6752e92f60456748d15782c39db54197`

Seed 6402:

`ef1ae41abb8e33d4984174854e1ad594266254e5df105d1bb20d2cc4677c78f9`

Semantic identity result: **False**

The diff correctly detected changes in progression path, object composition, landmarks, encounters, and finds.

## Bundle verification

Reference output folder manifest:

- files: **9**
- total bytes: **1121197**
- embedded world fingerprint: `9ca5ee610374c75406390c054887d9aa6752e92f60456748d15782c39db54197`
- SHA-256 verification: **PASS**

## Fingerprint contract

The semantic fingerprint intentionally ignores:

- PixelGen version labels
- schema-version labels
- derived `visual_quality`
- embedded `progression_simulation`
- private runtime-only scene fields

Therefore a compatible later tool can recognize the same semantic generated world without changing its identity merely because the reader/exporter version changed.
