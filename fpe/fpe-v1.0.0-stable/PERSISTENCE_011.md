# FPE 0.11 runtime persistence

## Goal

FPE 0.11 can checkpoint and restore **viewer/runtime state** without turning FPE into an authoritative world-state owner.

```js
const snapshot = runtime.serialize();
const restored = FPE.restore(snapshot);
```

The public snapshot schema is:

```text
fpe.runtime_snapshot/0.11.0
```

## Snapshot contents

A snapshot contains:

- the complete accepted FPE projection;
- normalized expanded-cluster / expanded-bud view state;
- runtime options currently limited to scheduler `budget`;
- the monotonic host runtime clock;
- exact scheduler internal state for every cluster;
- request source-context matching the accepted PixelGen world/revision/tick;
- explicit projection, request and snapshot schema identifiers.

The scheduler state records each cluster's update rate, next due tick, last serviced tick and current detail class. This is required for exact continuation: reconstructing a new scheduler only from projection + view would produce a valid but different schedule.

## Split clock rule

The host runtime clock and scheduler clock are intentionally separate.

After a successful `accept(newerProjection)`:

- the host runtime clock remains monotonic across revisions;
- the scheduler is freshly created for the new revision and begins internally at `-1` until stepped.

A snapshot may therefore legitimately contain, for example:

```text
runtime clock   = 29
scheduler clock = -1
```

`FPE.restore()` preserves this state exactly. The scheduler clock may never be ahead of the runtime clock.

## Request context

`request()` has no pending queue or hidden mutable request history. Its context is the accepted projection source identity. Persistence therefore stores and validates the source context used for future request envelopes:

- seed;
- PixelGen world fingerprint;
- dimensions;
- state revision;
- source state tick.

After restore, a new `request()` produces the same source binding as it would have before serialization.

## Validation

`FPE.restore(snapshot)` rejects malformed data with `INVALID_SNAPSHOT`, including:

- unsupported snapshot/runtime contract versions;
- invalid or modified projection structure;
- non-canonical/unknown view IDs;
- invalid runtime or scheduler clocks;
- scheduler budget, projection fingerprint or source-clock mismatch;
- missing/duplicate/foreign scheduler entries;
- modified scheduler rates or invalid detail classes;
- request context inconsistent with the accepted projection;
- cycles, non-finite numbers, `undefined`, functions, non-plain objects or excessive nesting.

Restore never silently normalizes a damaged snapshot into a different valid state.

## Ownership and isolation

`serialize()` returns detached data. Mutating the returned snapshot cannot mutate the live runtime. `FPE.restore()` also detaches from its input; mutating the input object after restore cannot change the restored runtime.

## Security / trust boundary

Snapshots are validation-checked but are not digitally signed or cryptographically authenticated. They are not evidence that PixelGen authorized any semantic change.

Treat snapshots as local runtime/viewer checkpoints. If they come from an untrusted source, validate application-level trust separately. Authoritative game/world changes still have to pass through the host/PixelGen layer and return as a new projection through `accept()`.

## Compatibility

0.11 is the first FPE runtime snapshot format. There is no earlier snapshot migration path because 0.10 and earlier did not expose runtime persistence. Future cross-version migration policy remains to be frozen before/at 1.0.

## 0.12 hardening note

FPE runtime 0.12 keeps this serialized schema unchanged. It accepts valid snapshots produced by runtime 0.11.0 or 0.12.0, applies stricter integrity/scheduler invariants during restore, and emits `runtime_version: 0.12.0` on the next serialization. The schema identifier remains `fpe.runtime_snapshot/0.11.0` because no field-shape change was required.
