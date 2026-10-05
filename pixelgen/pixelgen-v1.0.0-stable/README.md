# PixelGen v1.0.0 — Stable

PixelGen 1.0 is the first stable release of the deterministic semantic world generator and runtime-authority layer.

The 1.0 promotion intentionally changes **contract/package metadata, not world semantics**. Mature payload schemas remain frozen:

```text
world                    0.7
territory graph          0.7.5
dynamic world state      0.8.0
runtime events           0.8.0
PixelGen → EBE runtime   0.8.0
regional corridors       0.9.0
render API               0.9.1
runtime API              1.0.0
contract manifest        1.0.0
```

## Stable ownership boundary

PixelGen owns objective semantic reality: static world generation, territories/fronts, dynamic mutation provenance, derived events, local evidence availability, deterministic replay, fingerprints and public bundles. NPC cognition remains outside PixelGen.

## Core invariants

- same seed/profile/dimensions → same semantic fingerprint
- generator/schema labels are excluded from semantic world identity
- dynamic state never rewrites static world semantics
- same world + ordered event log → exact replayed state
- public JSON is strict UTF-8 JSON: duplicate keys and NaN/Infinity are rejected
- public bundles are transactional: validate → stage → self-verify → commit/rollback
- unknown future generators are never silently metadata-migrated
- 0.9.3 worlds can migrate to the 1.0 contract without changing semantic identity
- EBE handoff remains local-evidence-only; observations are not agent knowledge

## Runtime-only use

```bash
python runtime_cli.py capabilities
python runtime_cli.py contract
python runtime_cli.py world --cols 6 --rows 5 --seed 7301 --out generated/world
python runtime_cli.py state-demo --cols 6 --rows 5 --seed 7301 --out generated/state_demo
```

Renderer is optional. Pillow is not required for the semantic runtime.

## Frozen public bundle

```bash
python runtime_cli.py freeze-bundle \
  --world world.json \
  --state state.json \
  --events events.json \
  --ebe-runtime ebe-runtime.json \
  --out frozen_bundle

python runtime_cli.py verify-bundle --bundle frozen_bundle
```

## Compatibility

- current 1.0 worlds: direct use
- 0.9.0–0.9.3 worlds with required mature features: metadata-only migration
- pre-corridor worlds: regeneration required; migration never invents geography
- unknown future generator versions: explicit rejection until compatibility is defined
- 0.9.3 contract manifests remain readable for verification

See `PIXELGEN_1_0_CONTRACT.md` and `V100_TEST_REPORT.md` for the release contract and promotion evidence.

## Stable contract fingerprint

```text
eb2deceb5913231addf4d9ddb323843c0832f25ee1f0b737378f53cbc892727c
```

The canonical `7301 / 6×5` semantic world fingerprint remains:

```text
ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a
```
