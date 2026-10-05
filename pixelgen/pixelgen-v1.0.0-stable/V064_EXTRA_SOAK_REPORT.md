# PixelGen v0.6.4 — Extra Soak / Reproducibility Pass

## Additional soak tests

### Batch A

- worlds requested: **250**
- worlds completed: **250**
- hard failures: **0**
- visual warnings: **13**
- elapsed: **11.563 s**
- dimensions: 1×1, 2×2, 3×2, 4×3, 5×4

### Batch B

- worlds requested: **250**
- worlds completed: **250**
- hard failures: **0**
- visual warnings: **11**
- elapsed: **49.039 s**
- dimensions: 4×3, 5×4, 6×5, 8×6, 10×8

## Combined result

- worlds generated: **500**
- hard failures: **0**
- visual warnings: **24**

Visual warnings are intentionally non-fatal composition warnings.

## Determinism checks

Five repeated-generation cases were tested:

- 1×1 / seed 0
- 4×3 / seed 6060
- 4×3 / seed 6401
- 6×5 / seed 999999
- 8×6 / seed -777

All produced identical semantic fingerprints on repeated generation.

## Semantic diff checks

- a world compared with itself → **identical**
- seed 6401 vs seed 6402 → **different**
- reversing A/B preserves the expected fingerprint relation → **PASS**

## Bundle integrity checks

- untouched bundle → **PASS**
- modified listed file → **FAIL detected**
- unlisted extra file → **FAIL detected**
- missing listed file → **FAIL detected**

## Conclusion

The extra pass found **no hard generation failures** in 500 additional worlds and no reproducibility or bundle-integrity regressions.
