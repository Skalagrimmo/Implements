# FPE 0.9 public API candidate

Package entry point: `require('./web/fpe.js')` in Node; global `FPE` in browser.
Browser script order: `fpe_core.js`, `fpe_handoff.js`, `fpe_scheduler.js`, `fpe.js`.
No npm dependencies are required by the core API. Three.js belongs to the demo only.

```js
const FPE = require('./web/fpe.js');
const runtime = FPE.create(projection, {budget: 8});
runtime.toggleCluster('sector_0_0');
runtime.toggleBud('sector_0_0_bud_0');
const plan = runtime.getPlan();
const batch = runtime.step(0);
runtime.accept(newerProjection);
const intent = runtime.request('inspect', 'sector_0_0', {mode:'deep'});
```

| Method | Result and behavior |
| --- | --- |
| `FPE.describe()` | Detached version, schema, methods and error-code description |
| `FPE.create(projection, {budget:8})` | Runtime with detached accepted data; positive integer descriptor budget |
| `accept(projection)` | `{changed, revision}`; preserves view, resets scheduler only for a new revision |
| `setView({expandedClusters, expandedBuds})` | Normalized view copy; unknown and orphan IDs removed |
| `toggleCluster(id)` | Updated view copy; collapse removes descendant expansion |
| `toggleBud(id)` | Updated view copy; parent must already be expanded |
| `getProjection()` | Detached projection copy |
| `getView()` | Detached view copy |
| `getPlan()` | Detached hierarchy/geometry plan |
| `step(tick)` | `{tick, updates, deferred, repeated}` from the scheduler |
| `request(action, targetId, payload={})` | Detached `fpe.action_request/0.10.0` intent envelope; never mutates world state |

Runtime methods and exports are frozen; returned data is mutable but detached. Getter copies cost time and memory; retain a plan between explicit view/revision changes rather than calling it every frame.

## Stable error codes

All documented input failures use `FPE.FPEError`, with `name`, `code`, and a diagnostic `message`. Match the code, not message text.

| Code | Meaning |
| --- | --- |
| INVALID_OPTIONS | Invalid options or budget |
| INVALID_PROJECTION | Projection failed structural validation/preflight |
| FOREIGN_WORLD | Different world identity; create a new runtime |
| STALE_REVISION | Revision or source tick moved backward |
| REVISION_CONFLICT | Different content at the same revision |
| INVALID_VIEW | Missing view arrays or non-string IDs |
| UNKNOWN_ID | Unknown cluster or bud toggle target |
| PARENT_COLLAPSED | Bud toggle requires expanded parent |
| INVALID_TICK | Negative, backward, unsafe or non-integer host tick |
| INVALID_REQUEST | Malformed semantic request or non-JSON-safe payload |

Ticks are host view ticks, not PixelGen time. The monotonic guard survives accepted revisions. A new revision resets scheduled work, so one update at the same host tick is allowed after handoff; an identical duplicate does not reset it. Values above `Number.MAX_SAFE_INTEGER - 16` are rejected.

## Compatibility and limits

Projection schema remains `fpe.pixelgen_hierarchy/0.6.0`; canonical fingerprints are unchanged. Earlier modules remain available, but new integrations should use `FPE`. The 0.9 runtime core remains the freeze candidate toward 1.0. Version 0.10 adds semantic action request envelopes while retaining the same authority boundary.

PixelGen owns objective state. API writeback is disabled. Semantic requests are emitted as intent envelopes only; the authoritative host must validate/apply them and feed resulting projections back through `accept()`. Browser checksum verification, persistence of runtime/scheduler state, GPU rollback and spatial streaming are not provided. Python CLI still checks SHA-256. Version 0.9 visual changes require a fresh manual browser check; the user's earlier successful check covered 0.8.
