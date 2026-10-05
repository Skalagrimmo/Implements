# FPE 0.12 API/schema freeze candidate

The following names are candidates to carry unchanged into FPE 1.0 unless a release-blocking defect is found.

## Public names

Top level: `version`, `create`, `restore`, `describe`, `FPEError`.

Runtime: `accept`, `setView`, `toggleCluster`, `toggleBud`, `step`, `request`, `serialize`, `getProjection`, `getView`, `getPlan`.

Error codes: the 11 codes listed in `PUBLIC_API_012.md`.

## Schema identifiers

- projection: `fpe.pixelgen_hierarchy/0.6.0`
- hierarchy: `fpe.view_hierarchy/0.6.0`
- action request: `fpe.action_request/0.10.0`
- runtime snapshot: `fpe.runtime_snapshot/0.11.0`
- scheduler persisted state: `fpe.scheduler_state/0.11.0`

Runtime version and schema version are intentionally separate. 0.12 hardening did not alter the serialized shape, so it does not rename the 0.11 snapshot/scheduler schemas.

## Authority freeze

PixelGen remains the sole owner of objective semantic world state. FPE remains read-only with respect to that state. `request()` describes intent; it never executes or commits it. A snapshot is viewer/runtime state, not authoritative PixelGen state.

## Compatibility candidate

0.12 accepts 0.11 and 0.12 runtime snapshots under the 0.11 snapshot schema. The final 1.0 release should explicitly choose whether to keep this migration window and which pre-1.0 snapshots, if any, remain supported after 1.0.
