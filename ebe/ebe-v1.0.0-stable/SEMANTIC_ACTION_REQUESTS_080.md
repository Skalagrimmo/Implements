# EBE v0.8.0 — Semantic Action Request Contract

## Ownership rule

EBE may decide that an agent **wants to act**, but EBE does not directly mutate PixelGen reality.

```text
belief / interpretation
↓
reaction
↓
semantic action request
↓
external authority boundary
↓
PixelGen accepts or rejects
↓
derived event + local observations
↓
EBE ingest
```

This keeps one authority for objective world state.

## Domains

### `agent_intent`

Local/gameplay intent for another consumer, for example:

```text
avoid_front
prepare_exit
wait
```

It is not automatically a PixelGen event.

### `pixelgen_world_event`

Strict adapter for the stable PixelGen 1.0 dynamic-world contract:

```text
front_escalation
front_deescalation
territory_strengthen
territory_weaken
territory_alert
```

Target type and amount are validated before export.

## Lifecycle

```text
pending
  ↓ export_pixelgen_action()
exported
  ↓ authority result
applied | rejected
```

Export is idempotent. Terminal resolution is idempotent only when the same terminal status is repeated.

## Causal provenance

Every request can retain:

```text
actor_id
source_reaction_id
source_rule_id
claim_key
believed_value
confidence
origin_observation_ids[]
source_count
```

The evidence roots are inherited from the belief. Creating or relaying an action does not create new evidence roots.

## PixelGen handoff

A PixelGen request exports as:

```text
id          = EBE action request id
event_type  = action_type
target_type
target_id
amount
sector
source      = ebe_v080_action_request
actor_id
cause_id
```

The request ID is preserved as the PixelGen runtime-event ID. Therefore a later PixelGen derived event can be correlated through:

```text
derived_event.cause_event_id == action_request.id
```

EBE then marks the request `applied`.

## No implicit mutation

Calling:

```lua
rt:request_action(...)
rt:export_pixelgen_action(id)
```

never changes PixelGen state. A host/bridge must explicitly submit the exported event to PixelGen.

## Reaction adapters

Adapters are declarative and snapshot-safe:

```lua
rt:register_reaction_action_adapter("request_front_deescalation", {
  domain="pixelgen_world_event",
  action_type="front_deescalation",
  target_from_claim=true,
  amount=.12,
})
```

`target_from_claim=true` resolves `front:front_0:status` to `front / front_0`.

The default EBE reactions create only harmless `agent_intent` requests. They do not become world mutations unless the application explicitly installs a PixelGen adapter.

## Snapshot migration

v0.7 snapshots restore into v0.8 with an empty action history. v0.8 snapshots preserve:

```text
sequence
requests
order
adapters
bounded action log
```

## PixelGen feedback

`Runtime:ingest_pixelgen(bundle)` checks derived events. If a derived event has:

```text
cause_event_id = exported EBE request id
```

the request transitions to `applied` and records the authoritative derived-event/revision result.
