# PixelGen v0.9.0 — Regional Corridors Test Report

## Release gate

```text
17 regression scripts through v0.9.0: PASS
corridor fuzz: 240 worlds PASS
corridors exercised in fuzz: 982
local corridor segments exercised: 3440
12×12 stress: 4/4 PASS
canonical corridor-demo: PASS
unified audit: PASS
v0.8 additive semantic parity: 4/4 PASS
```

## Canonical seed 7301 / 6×5

```text
corridors: 7
covered sectors: 19 / 30
local segments: 25
old_road: 3
pilgrim_route: 1
silt_vein: 3
world fingerprint: ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a
```

The canonical unified audit reports:

```text
AUDIT: PASS
Sectors: 30
Landmarks: 8
Regional corridors: 7
Visual repetition score: 100/100 (A)
Structural grammar score: 100/100
Progression final reachable: True
Progression all sectors reachable: True
```

## Macro-to-local integrity

The dedicated validator checks:

```text
corridor IDs are unique
every macro path step is orthogonally adjacent
every macro step corresponds to a real reciprocal world link
source / target / sector_count match the path
sector membership matches corridor paths
local anchor cells match actual link coordinates
local route cells are walkable
internal corridor anchors are connected inside the scene
summary counts match the realized data
```

## Gameplay separation

Corridors are geographic/semantic continuity, while gameplay gates remain a separate layer.

```text
corridor exists physically
+
gameplay link may later be open / gated / secret / sealed
```

The 240-world fuzz re-runs gameplay integrity and full progression simulation after corridor generation.

## v0.8 → v0.9 additive parity

For each comparison world, the v0.9-only corridor metadata and release labels were stripped before canonical hashing.

```text
seed  7301  6×5  equal=True  351d2f345756b2e517cfec5a6848d1c6b2b7353a0f5e24e1529d67f6c461f0d0
seed  6060  4×3  equal=True  171fea2682fb792b5e45b651b64f06fc3d42496c024a242a375893b46dc59df6
seed    42  8×6  equal=True  09f4563e08bac8a65ef4dae9fbd9b54d16c7a243e6c425871246697c5cb8bc85
seed  -777  1×1  equal=True  867667147bcfc30cbc2c856a8b05c7901db771787a923d6859edd353e8ed9b06
```

This verifies that v0.9.0 does not silently alter the established v0.8 biome, scene, encounter, progression, influence, territory, or dynamic-state semantics.

## Actual 12×12 / 144-sector stress

### seed 0

```text
corridors: 10
covered sectors: 47 / 144
local segments: 61
kinds: {'drainage_channel': 2, 'old_road': 3, 'pilgrim_route': 3, 'ridge_chain': 1, 'silt_vein': 1}
fingerprint: b0104c9f97b85aedcad1b1f0a0548f6d725e6e7510befb85174e83a11da35386
generation time in validation environment: 0.662 s
```

### seed 1

```text
corridors: 12
covered sectors: 52 / 144
local segments: 67
kinds: {'drainage_channel': 2, 'old_road': 3, 'pilgrim_route': 3, 'ridge_chain': 1, 'silt_vein': 3}
fingerprint: 6eabd15fddec60e484d3afc1104192bb8a47ee3eb6b0f87949c5fd803b916686
generation time in validation environment: 0.65 s
```

### seed 6060

```text
corridors: 9
covered sectors: 48 / 144
local segments: 56
kinds: {'drainage_channel': 2, 'old_road': 3, 'pilgrim_route': 1, 'ridge_chain': 1, 'silt_vein': 2}
fingerprint: 22e4aa35f52322bea5c0d980a79faa7b6526b89ac7ad7da78b5757e1c49e684d
generation time in validation environment: 0.641 s
```

### seed 7301

```text
corridors: 11
covered sectors: 53 / 144
local segments: 63
kinds: {'drainage_channel': 2, 'old_road': 3, 'pilgrim_route': 4, 'ridge_chain': 1, 'silt_vein': 1}
fingerprint: e4edb22d22f2fb2ca50bb7312e9415da3a0d6505134e2f75abcdfe90b80565c9
generation time in validation environment: 0.601 s
```

Timing values are environment-specific validation measurements, not device benchmarks.

## Current 0.9 boundary

v0.9.0 provides deterministic geographic corridors and local realization metadata. It intentionally does not yet make corridors autonomous simulation entities or dynamic-state owners.

The next 0.9.x work toward 1.0 is primarily performance/renderer separation, schema migration/freeze, and release hardening rather than adding another major world subsystem.
