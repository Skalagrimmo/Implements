# FPE 1.0 stable contract

FPE 1.0 is the stable promotion of the 0.12 freeze candidate. The promotion adds no new public runtime method, error code, schema identifier, writeback authority, or rendering semantics.

## Public API

Top level:

```text
FPE.version = 1.0.0
FPE.create(projection, options)
FPE.restore(snapshot)
FPE.describe()
FPE.FPEError
```

Runtime methods, frozen in order:

```text
accept
setView
toggleCluster
toggleBud
step
request
serialize
getProjection
getView
getPlan
```

Stable error codes:

```text
INVALID_OPTIONS
INVALID_PROJECTION
FOREIGN_WORLD
STALE_REVISION
REVISION_CONFLICT
INVALID_VIEW
UNKNOWN_ID
PARENT_COLLAPSED
INVALID_TICK
INVALID_REQUEST
INVALID_SNAPSHOT
```

## Frozen schemas

```text
projection             fpe.pixelgen_hierarchy/0.6.0
hierarchy/view         fpe.view_hierarchy/0.6.0
action request         fpe.action_request/0.10.0
runtime snapshot       fpe.runtime_snapshot/0.11.0
scheduler state        fpe.scheduler_state/0.11.0
```

Schema versions are intentionally independent of the runtime release. No serialized shape changed during 1.0 promotion.

## Snapshot compatibility

FPE 1.0 accepts structurally valid checkpoints whose `runtime_version` is:

```text
0.11.0
0.12.0
1.0.0
```

All accepted historical checkpoints are re-serialized with `runtime_version: 1.0.0` while retaining the same snapshot schema. Unknown older or future runtime versions are rejected until an explicit compatibility rule exists.

## Authority boundary

PixelGen remains authoritative for objective semantic world state. FPE is a deterministic read-only manifestation/view runtime. `request()` emits semantic intent but does not execute or commit it. `serialize()` stores FPE viewer/runtime state and an accepted projection copy; it does not transfer objective authority to FPE.

## Integrity boundary

Projection fingerprints are recomputed in JavaScript using the same canonical SHA-256 contract as the Python bridge. Public JSON boundaries reject cycles, accessors, symbols, hidden properties, sparse/extended arrays, non-plain objects and non-finite numbers where applicable. Accepted projections are detached, validated and deep-frozen internally.

This structural/integrity validation is not an authentication mechanism. If snapshots or projections cross an untrusted transport boundary, authenticity must be supplied by the surrounding application or transport.
