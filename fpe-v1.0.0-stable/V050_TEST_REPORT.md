# FPE v0.5.0 — Test Report

## Canonical PixelGen 1.0 fixture

Source: fresh PixelGen 1.0.0 `state-demo`, seed `7301`, dimensions `6×5`.

```text
PixelGen semantic world fingerprint
ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a

initial state revision 0
after state revision   3
runtime events         3
derived events         3
local observations     13
```

Initial FPE projection:

```text
clusters                30
buds                    120
territory clusters      25
front clusters          20
STRAIGHT buds           53
CURVED buds             67
projection fingerprint  5587f1abd8cc883465fdfce5d2ac8ebe84531461a827b51a10d70ba123996b2c
```

After PixelGen revision 3:

```text
clusters                30
buds                    120
STRAIGHT buds           57
CURVED buds             63
projection fingerprint  2d0c7d000b00416e5f727a3d84f43e559f467ce97ea8550c53cae91d051dce63
changed cluster records 25
```

The PixelGen world fingerprint is unchanged; only the dynamic projection changes.

## Regression

`tests/test_bridge.py` validates:

- exact source seed/dimensions/fingerprint identity;
- 30 sectors → 30 clusters → 120 buds;
- exact topology `front_ids` preservation;
- deterministic repeated projection;
- dynamic revision mapping;
- rejection of wrong seed, dimensions, world fingerprint, and incomplete sector sets;
- projection self-fingerprint and range validation.

Result: **PASS**.

## Browser/core determinism

`tests/test_web_core.js` validates the renderer-independent JavaScript geometry planner.

Canonical geometry plan:

```text
clusters  30
buds      120
nodes     1362
edges     2110
straight  53
curved    67
```

Two independent geometry-plan builds are byte-equivalent. `web/fpe_core.js` and `web/index.html` contain no executable `Math.random()` calls.

Result: **PASS**.

## Cross-engine PixelGen 1.0 fuzz

A direct 48-world monolithic rerun exceeded the interactive wall-clock limit and is **not** relabeled as PASS.

The exact deterministic case range was then run in four 12-world shards, preserving the same seed stream and dimension cycle:

```text
4×3
6×5
8×6
12×12
```

Aggregate fresh result:

```text
worlds             48
PixelGen mutations 48
FPE clusters       2808
FPE buds           11232
hard failures      0
```

Every mutation was performed through PixelGen 1.0 `apply_event()` before rebuilding the FPE projection. PixelGen remained the state authority.

Result: **PASS (4 exact-case shards)**.

## Python/package checks

```text
python compileall       PASS
bridge_cli build        PASS
bridge_cli validate     PASS
projection determinism  PASS
```

## Scope

v0.5 proves the read-only `PixelGen sector → FPE local cluster` contract. It does not yet claim hierarchical FPE expansion/collapse, multi-rate scheduler behavior, or bidirectional semantic action requests; those remain later milestones.
