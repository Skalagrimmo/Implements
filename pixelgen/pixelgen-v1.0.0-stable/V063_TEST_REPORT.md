# PixelGen v0.6.3 — Release Hardening Test Report

## Release gate

- Combined v0.5 Hardened + v0.6.0 + v0.6.1 + v0.6.2 + v0.6.3 pytest suite: **15 PASS**
- Legacy v0.2 regression script: **PASS**
- Legacy v0.3 regression script: **PASS**
- Legacy v0.4 regression script: **PASS**
- Legacy v0.5 regression script: **PASS**
- v0.6.3 fuzz matrix: **250 worlds**
  - hard failures: **0**
  - visual warnings: **10**
- `doctor`: **PASS**
- public `audit`: **PASS**
- public `visual-check`: **PASS**
- public `seed-sweep`: **PASS**

## Canonical seed 6060

- audit status: **PASS**
- sectors: **12**
- landmarks: **6**
- visual repetition score: **83/100**
- grade: **B**
- quadrant entropy: **0.0**
- final sector reachable: **True**
- all sectors reachable: **True**

## Seed-sweep sample

```bash
python cli.py seed-sweep --start-seed 6300 --count 12 --cols 4 --rows 3
```

Best seed: **6301**  
Best visual score: **100/100**

Seed 6301 is bundled as a reference example and passes the unified audit with grade **A**.

## New hardening tools

- `doctor` — runtime/Pillow/profile/tiny-world/progression sanity check.
- `audit` — world + landmarks + gameplay + anti-softlock + visual-pattern checks.
- `seed-sweep` — ranks candidate seeds without expensive PNG rendering.
- `--strict-visual` — optionally upgrades visual warnings to audit failures.

## Export metadata

World exports now include explicit generator identity:

```json
"generator": {
  "name": "PixelGen",
  "version": "0.6.3"
}
```
