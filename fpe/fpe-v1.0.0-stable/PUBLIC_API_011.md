# FPE 0.11 public API candidate

Browser dependency order:

```text
fpe_core.js → fpe_handoff.js → fpe_scheduler.js → fpe.js
```

No npm dependencies are required by the core runtime API. Three.js belongs only to the demo.

## Top-level API

```js
FPE.version                  // "0.11.0"
FPE.create(projection, opts) // new runtime
FPE.restore(snapshot)        // restore exact runtime checkpoint
FPE.describe()               // detached contract description
FPE.FPEError                 // typed API error
```

## Runtime methods

| Method | Contract |
|---|---|
| `accept(projection)` | Validate and accept a compatible newer projection; preserve compatible view state; reset scheduler only on new revision |
| `setView(view)` | Normalize/set viewer expansion state |
| `toggleCluster(id)` | Expand/collapse cluster and prune descendant bud expansion when collapsed |
| `toggleBud(id)` | Expand/collapse bud; parent cluster must be expanded |
| `step(tick)` | Deterministic bounded scheduler update using monotonic host tick |
| `request(action, targetId, payload={})` | Detached `fpe.action_request/0.10.0` semantic-intent envelope; no writeback |
| `serialize()` | Detached `fpe.runtime_snapshot/0.11.0` checkpoint |
| `getProjection()` | Detached accepted projection |
| `getView()` | Detached normalized view state |
| `getPlan()` | Detached current hierarchy/render plan |

## Error codes

| Code | Meaning |
|---|---|
| `INVALID_OPTIONS` | Invalid runtime creation options |
| `INVALID_PROJECTION` | Projection failed structural/contract validation |
| `FOREIGN_WORLD` | Incoming projection belongs to another world identity |
| `STALE_REVISION` | Incoming revision/source tick moved backward |
| `REVISION_CONFLICT` | Same revision carries different projection content |
| `INVALID_VIEW` | Malformed public view state |
| `UNKNOWN_ID` | Cluster/bud/request target does not exist |
| `PARENT_COLLAPSED` | Bud expansion requested while its cluster is collapsed |
| `INVALID_TICK` | Host tick is invalid, unsafe or moves backward |
| `INVALID_REQUEST` | Malformed semantic request/payload |
| `INVALID_SNAPSHOT` | Runtime snapshot is malformed, incompatible or internally inconsistent |

## Describe contract

`FPE.describe()` reports:

```text
version              0.11.0
projectionSchema     fpe.pixelgen_hierarchy/0.6.0
actionRequestSchema  fpe.action_request/0.10.0
snapshotSchema       fpe.runtime_snapshot/0.11.0
writeback            false
```

Returned contract objects, projections, views, plans, requests and snapshots are detached from runtime ownership.

## Authority boundary

PixelGen owns objective state. FPE owns deterministic manifestation/view mechanics and local scheduling. `request()` describes intent but does not execute it. `serialize()` checkpoints FPE runtime/viewer state but does not convert that checkpoint into authoritative PixelGen state.
