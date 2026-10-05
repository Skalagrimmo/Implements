# EBE migration — v0.6.0 → v0.7.0

## Compatibility

v0.6 snapshots remain accepted by `Runtime.restore()`.

If an institution snapshot has no `editorial` field, v0.7 creates a pass-through policy:

```text
publish
priority 0
no extra delay
confidence multiplier 1
```

No archived report, subscriber, route, source lineage, collective, belief, or knowledge record is invented.

## Semantic change

v0.7 introduces a new optional institutional decision layer between:

```text
institution archive
↓
broadcast queue
```

The old default behavior is preserved when no editorial policy is configured.

## New APIs

```lua
rt:set_institution_editorial_policy(institution_id, spec)
rt:institution_policy_view(institution_id)
```

New module:

```lua
local Policy=require("ebe.social.institution_policy")
```

## Snapshot additions

Institution snapshots now include:

```text
editorial
policy_log
```

## Source-lineage rule

Editorial decisions never create new `origin_observation_ids`.

Censorship changes distribution, not evidence identity.
