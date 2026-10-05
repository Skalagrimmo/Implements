# FPE 0.12 public API freeze candidate

Browser dependency order:

```text
fpe_core.js → fpe_handoff.js → fpe_scheduler.js → fpe.js
```

0.12 adds no public method or error-code surface. It hardens the contracts underneath the 0.11 candidate.

## Top-level API

```js
FPE.version                  // "0.12.0"
FPE.create(projection, opts)
FPE.restore(snapshot)
FPE.describe()
FPE.FPEError
```

## Runtime methods

| Method | Contract |
|---|---|
| `accept(projection)` | Validate integrity and compatibility, accept a newer projection, preserve compatible view state, reset scheduler only on a genuinely new revision |
| `setView(view)` | Normalize/set viewer expansion state |
| `toggleCluster(id)` | Expand/collapse cluster; collapsing prunes descendant bud expansion |
| `toggleBud(id)` | Expand/collapse bud; parent cluster must already be expanded |
| `step(tick)` | Deterministic bounded scheduler update using monotonic host tick |
| `request(action, targetId, payload={})` | Detached `fpe.action_request/0.10.0` semantic-intent envelope; no writeback |
| `serialize()` | Detached `fpe.runtime_snapshot/0.11.0` checkpoint produced by runtime 0.12.0 |
| `getProjection()` | Detached accepted projection |
| `getView()` | Detached normalized view state |
| `getPlan()` | Detached hierarchy/render plan |

## Error codes

`INVALID_OPTIONS`, `INVALID_PROJECTION`, `FOREIGN_WORLD`, `STALE_REVISION`, `REVISION_CONFLICT`, `INVALID_VIEW`, `UNKNOWN_ID`, `PARENT_COLLAPSED`, `INVALID_TICK`, `INVALID_REQUEST`, `INVALID_SNAPSHOT`.

## Describe contract

```text
version              0.12.0
projectionSchema     fpe.pixelgen_hierarchy/0.6.0
actionRequestSchema  fpe.action_request/0.10.0
snapshotSchema       fpe.runtime_snapshot/0.11.0
writeback            false
```

## Snapshot compatibility in this RC

`FPE.restore()` accepts structurally valid snapshots of schema `fpe.runtime_snapshot/0.11.0` produced by runtime versions `0.11.0` and `0.12.0`. A restored 0.11 snapshot is migrated on serialization: the next `serialize()` emits `runtime_version: "0.12.0"` with the same schema.

## Integrity boundary

Public projection acceptance includes strict JSON-data validation, semantic contract validation and a full recomputation of `projection_fingerprint`. Internal caching is legal only for an already-validated recursively frozen projection owned by the runtime.

Returned projections, views, plans, requests, descriptions and snapshots remain detached from runtime ownership.
