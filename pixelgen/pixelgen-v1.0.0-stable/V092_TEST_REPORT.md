# PixelGen v0.9.2 — Schema / Migration Freeze Candidate Test Report

## Release gate

```text
22 active regression scripts PASS
v0.9 corridor fuzz: 240 worlds PASS
v0.9.1 renderer-free fuzz: 40 worlds PASS
v0.9.2 contract fuzz: 60 worlds PASS
```

The retained historical `tests/test_v05.py` is intentionally excluded from the active gate because its old “exactly one hollow” assumption was already obsolete in v0.9.1. It is not reported as passing.

## Contract identity

```text
contract version: 0.9.2
contract fingerprint: ce2324e2c472162f39dbe0ee460e847dca97edfd0634215ea671da2b4f3b7bb9
canonical 7301 / 6×5 world: ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a
```

## v0.9.1 → v0.9.2 semantic parity

```text
seed 7301  6×5
ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a
ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a
equal = True
```

```text
seed 6060  4×3
1dda98af5f8512af698139cb3b70bbdba5a557863cd008bf8a5bd4965b105c50
1dda98af5f8512af698139cb3b70bbdba5a557863cd008bf8a5bd4965b105c50
equal = True
```

```text
seed 42  8×6
0b9cf5159c72b32f0d7509826471f32852b9938b05cad42712006124d7ed5ac1
0b9cf5159c72b32f0d7509826471f32852b9938b05cad42712006124d7ed5ac1
equal = True
```

```text
seed -777  1×1
926324556c14011b53b07292ffb9c791a4f9dab67fcb4c9fb11f5857e1e8283f
926324556c14011b53b07292ffb9c791a4f9dab67fcb4c9fb11f5857e1e8283f
equal = True
```

```text
seed 0  12×12
b0104c9f97b85aedcad1b1f0a0548f6d725e6e7510befb85174e83a11da35386
b0104c9f97b85aedcad1b1f0a0548f6d725e6e7510befb85174e83a11da35386
equal = True
```

```text
seed 7301  12×12
e4edb22d22f2fb2ca50bb7312e9415da3a0d6505134e2f75abcdfe90b80565c9
e4edb22d22f2fb2ca50bb7312e9415da3a0d6505134e2f75abcdfe90b80565c9
equal = True
```

All six fresh generation comparisons matched.

## Migration behavior

Real v0.9.1 canonical world export was migrated through the public CLI.

```text
before: ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a
after:  ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a
semantic identity preserved = True
```

v0.9.0/v0.9.1 worlds with existing corridor semantics use metadata-only migration. Pre-corridor worlds are rejected with a regeneration requirement rather than receiving fabricated semantic data.

## Contract bundle verification

The canonical 6×5 CLI flow produced and verified a four-artifact bundle:

```text
world.json
state.json
events.json
ebe-runtime.json
pixelgen_contract_manifest.json
```

Checks include file hashes, canonical JSON hashes, world/state fingerprints, event-log equality, state/world identity, and EBE revision/world identity. A deliberate event-file modification was detected as a verification failure.

## 12×12 stress

```text
seed 0
world = b0104c9f97b85aedcad1b1f0a0548f6d725e6e7510befb85174e83a11da35386
revision = 1
events = 1
observations = 4
bundle artifacts = 4
verify = pass
```

```text
seed 1
world = 6eabd15fddec60e484d3afc1104192bb8a47ee3eb6b0f87949c5fd803b916686
revision = 1
events = 1
observations = 4
bundle artifacts = 4
verify = pass
```

```text
seed 6060
world = 22e4aa35f52322bea5c0d980a79faa7b6526b89ac7ad7da78b5757e1c49e684d
revision = 1
events = 1
observations = 4
bundle artifacts = 4
verify = pass
```

```text
seed 7301
world = e4edb22d22f2fb2ca50bb7312e9415da3a0d6505134e2f75abcdfe90b80565c9
revision = 1
events = 1
observations = 4
bundle artifacts = 4
verify = pass
```

All four 144-sector bundles verified successfully. Timing values in the JSON report are validation-environment measurements, not device benchmarks.

## Renderer separation

The contract registry, migration code, runtime CLI, and bundle verifier remain renderer-free. The v0.9.2 test explicitly blocks `PIL` imports and successfully imports the contract/runtime surfaces.

## Machine-readable schemas

The release includes structural JSON Schema documents for world, state, runtime events, EBE runtime bundles, corridors, and the contract manifest. When the optional `jsonschema` package is present, the v0.9.2 test validates the canonical artifacts against those documents.

## Freeze assessment

v0.9.2 is suitable as the PixelGen 1.0 contract freeze candidate. From this point, changes should default to bug fixes, compatibility fixes, and release hardening rather than new world subsystems.
