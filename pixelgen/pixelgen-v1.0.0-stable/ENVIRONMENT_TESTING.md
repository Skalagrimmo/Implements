# PixelGen v0.6.4.2 — cross-environment test plan

Recommended matrix:

```text
PC
Termux
UserLAnd
Pydroid
another Python IDE/runtime
```

## Stage 1 — quick repeated benchmark

In every environment:

```bash
python cli.py doctor
python cli.py env-log --label NAME --suite quick --repeat 3
```

## Stage 2 — collect and compare

Copy every `*.envlog.json` into one folder and run:

```bash
python compare_env_logs.py logs   --baseline PC   --json-out comparison.json   --md-out comparison.md   --csv-out comparison.csv
```

### Interpretation

- `PASS`: shared cases pass and semantic fingerprints match.
- `WARN`: no semantic mismatch, but some shared benchmark case is missing.
- `FAIL`: benchmark failure or semantic fingerprint mismatch.
- Performance index: geometric mean relative to the chosen baseline.
- Stability CV: timing noise across repeated runs.
- Stability is informational and never substitutes for semantic correctness.

## Stage 3 — standard

```bash
python cli.py env-log --label NAME --suite standard --repeat 3
```

## Stage 4 — stress

```bash
python cli.py env-log --label NAME --suite stress --repeat 2
```

Stress includes 8×6 and 10×8 worlds and may be slow on phones.
