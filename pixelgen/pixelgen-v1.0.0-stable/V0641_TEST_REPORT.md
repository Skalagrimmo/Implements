# PixelGen v0.6.4.1 — Cross-Environment Journal Test Report

## Release gate

- combined regression suite through v0.6.4.1: **15 PASS**
- public `env-log`: **PASS**
- public `env-compare`: **PASS**
- standalone `compare_env_logs.py`: **PASS**
- deliberate fingerprint mismatch: **FAIL correctly detected**
- CLI help surface: **PASS**

## Reference harness log

The bundled `Harness-PC` log was generated in the current desktop Python test environment.

- schema: **0.6.4.1**
- detected runtime: **desktop-python**
- Python: **CPython 3.13.5**
- Pillow: **12.3.0**
- suite: **quick**
- cases passed: **2/2**

Reference fingerprints:

- 2×2 seed 6401: `80dcae0ddc7aa18d4c31aa62250d2af17358035de5d2fe1e0ff6b5396bc90b25`
- 4×3 seed 6401: `9ca5ee610374c75406390c054887d9aa6752e92f60456748d15782c39db54197`

## Comparator harness

A second **simulated** environment log was made by keeping the same fingerprints and scaling timing values to 1.75×. This validates that performance differences alone do not fail compatibility.

Result:

- overall comparison: **PASS**
- fingerprint mismatches: **0**
- missing case groups: **0**
- environment case failures: **0**

A deliberately corrupted 4×3 fingerprint was then compared against the reference log. The standalone script returned exit code **2** and reported exactly **1 fingerprint mismatch**.

## Intended real-world use

The simulated second runtime is only a test fixture. Real portability evidence should be collected separately on:

```text
PC
Termux
UserLAnd
Pydroid
another Python IDE/runtime
```

using the same suite and then compared with `compare_env_logs.py`.
