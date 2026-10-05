# Changelog

## 1.0.0 — Stable

- Promoted PixelGen to the first stable public runtime/contract.
- Preserved all mature semantic payload schema versions.
- Promoted runtime API and contract manifest to 1.0.0.
- Contract status is now `stable`.
- Added metadata-only migration from 0.9.3 to the 1.0 contract.
- Preserved truthful source generator provenance during migration.
- Kept 0.9.3 contract manifests readable for compatibility verification.
- Preserved strict hostile-JSON validation and transactional bundle writes from 0.9.3.
- Added explicit 1.0 promotion/parity/bundle gate.
- No new world mechanic was introduced in the 1.0 promotion.

# Changelog

## 0.9.2 — Schema / Migration Freeze Candidate

- Added renderer-free public contract registry.
- Added deterministic contract fingerprint.
- Added machine-readable structural JSON Schemas for public artifacts.
- Added artifact type detection and strict public validation.
- Added conservative migration framework.
- Added metadata-only v0.9.0/v0.9.1 world migration.
- Preserved original generator provenance during migration.
- Added hard refusal to fabricate missing regional-corridor semantics for pre-0.9 worlds.
- Added deterministic contract bundle manifests.
- Added SHA-256 and canonical JSON hashes per artifact.
- Added cross-artifact world/state/events/EBE relationship verification.
- Added bundle tamper detection tests.
- Added renderer-free contract CLI commands.
- Added v0.9.1→v0.9.2 semantic parity verification.
- Added four-world 12×12 contract-bundle stress validation.
- Kept render API schema at 0.9.1 because the renderer contract did not change.
- Preserved canonical v0.9.1 world semantics.

## 0.9.1 — Runtime/Renderer Separation + Performance Hardening

- Added renderer-free `pixelgen.runtime_api`.
- Added renderer-free `runtime_cli.py`.
- Added optional lazy `pixelgen.render_api`.
- Added separate `render_cli.py`.
- Added deterministic fast preview asset cache.
- Preserved historical exact renderer mode.
- Added runtime/render API schema labels `0.9.1`.
- Kept regional corridor schema at `0.9.0`.
- Added Pillow-blocked runtime import/generation regression.
- Added runtime CLI blocked-renderer regression.
- Added fast-preview byte determinism regression.
- Added renderer-free world/state fuzz.
- Measured ~11.94× world-preview speedup on canonical 12×12 validation run.
- Preserved canonical v0.9.0 semantic fingerprint for seed 7301 / 6×5.

## 0.9.0 — Regional Corridors / Macro-to-Local Continuity

- Added deterministic world-scale regional corridor topology.
- Added `old_road`.
- Added `pilgrim_route`.
- Added `ridge_chain`.
- Added `silt_vein`.
- Added `drainage_channel`.
- Added one world-spine corridor for multi-sector geography worlds.
- Added deterministic regional-center connectors.
- Added regional/world landmark spurs.
- Added geography-field-weighted corridor path costs.
- Added sector corridor membership metadata.
- Added reciprocal physical-link corridor metadata.
- Added local scene corridor anchors.
- Added local walkable route realization without carving a second gameplay topology.
- Added `regional_corridors` world schema version `0.9.0`.
- Added corridor integrity validation.
- Added corridor-aware unified audit.
- Added corridor-aware `inspect` and `world-diff`.
- Added `corridor-demo` CLI command.
- Added `*.corridors.json` / `*.corridors.lua` exports.
- Added corridor overview renderer.
- Verified v0.8 semantic projection remains unchanged when the additive v0.9 layer is stripped.
- Preserved dynamic world-state and EBE bridge schema version `0.8.0`.

## 0.8.0 — Dynamic World State / PixelGen ↔ EBE Bridge

- Added deterministic mutable world-state overlay.
- Added territory/front runtime state, event replay, provenance and local observations.

## 0.7.5 — Territory Graph / Regional Event Seeds
## 0.7.4 — Influence Topology / Contested Zones
## 0.7.3.1 — Influence Hardening
## 0.7.3 — Regional Influence Fields / Landmark Ecology
## 0.7.2 — Subbiome / Ecotone Structural Variation
## 0.7.1 — Biome Structural Grammar
## 0.7.0 — Regional Geography / Biome Scale
