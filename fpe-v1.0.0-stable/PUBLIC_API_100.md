# FPE 1.0 public API

The stable public surface is the 0.12 freeze candidate promoted unchanged.

```js
const runtime = FPE.create(projection, { budget: 8 });
const restored = FPE.restore(snapshot);
FPE.version;     // "1.0.0"
FPE.describe();
```

Runtime methods:

```text
accept(projection)
setView(view)
toggleCluster(id)
toggleBud(id)
step(tick)
request(action, targetId, payload)
serialize()
getProjection()
getView()
getPlan()
```

Error codes:

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

All public returned structures are detached copies. PixelGen objective state remains external and authoritative. `request()` is an intent envelope, not writeback.

Stable schema IDs and compatibility policy are defined in `FPE_1_0_CONTRACT.md`.
