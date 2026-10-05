# PixelGen v0.6.4.2 — Compatibility Matrix / Benchmark Analytics Test Report

## Release gate

- combined regression suite through v0.6.4.2: **15 PASS**
- repeated `env-log --repeat 3`: **PASS**
- repeated-run fingerprint consistency: **PASS**
- standalone `compare_env_logs.py`: **PASS**
- CLI `env-compare --baseline ... --csv-out ...`: **PASS**
- old v0.6.4.1 single-run log compatibility: **PASS**
- duplicate environment labels: **clean error detected**
- semantic mismatch detection: **PASS**

## Reference repeated run

Harness environment:

- suite: **quick**
- repeats per case: **3**
- runtime: **desktop-python**
- Python: **CPython 3.13.5**
- Pillow: **12.3.0**

Reference cases:

| Case | Size | Median total ms | Total CV | Fingerprint |
|---|---:|---:|---:|---|
| tiny | 2×2 | 227.8 | 0.0204 | `80dcae0ddc7aa18d4c31aa62250d2af17358035de5d2fe1e0ff6b5396bc90b25` |
| reference | 4×3 | 671.963 | 0.0352 | `9ca5ee610374c75406390c054887d9aa6752e92f60456748d15782c39db54197` |

## Compatibility analytics fixture

The bundled comparison matrix contains:

- `Harness-PC` — **real current harness measurement**
- `Sim-Termux` — **synthetic timing fixture**
- `Sim-Pydroid` — **synthetic timing fixture**
- `Sim-UserLAnd` — **synthetic timing fixture**

The simulated entries exist only to verify the comparison/reporting code. They are **not measurements of real Android runtimes**.

Fixture result:

- overall status: **PASS**
- fingerprint mismatches: **0**
- missing cases: **0**
- case failures: **0**

## New metrics

Each repeated benchmark now records:

```text
mean
median
minimum
maximum
population standard deviation
coefficient of variation
```

The top-level `timings_ms` field remains backward-compatible and represents the median.

Cross-environment output adds:

```text
performance index
stability mean CV
stability grade
baseline-relative timing
CSV compatibility matrix
```

## Stability grades

```text
A  CV <= 0.03
B  CV <= 0.06
C  CV <= 0.10
D  CV >  0.10
```

These grades measure timing consistency only, not semantic compatibility.
