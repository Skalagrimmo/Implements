# PixelGen 0.8.0 — Dynamic World State Contract

## 1. Static source world

Every dynamic state stores:

```text
source_world.fingerprint
source_world.seed
source_world.dimensions
```

A state may only be applied to the exact semantic world it came from.

## 2. State clock

```text
tick
revision
```

In 0.8.0 one accepted semantic runtime event advances both by one.

No wall-clock simulation is implied yet.

## 3. Territory state

```text
alignment
control_strength  0.0 .. 1.75
stability         0.0 .. 1.0
alert             0.0 .. 1.0
status
revision
```

Territory status can be:

```text
secure
stable
pressured
fragile
```

## 4. Front state

```text
pair
tension   0.0 .. 1.0
activity  0.0 .. 1.0
status
revision
```

Front status:

```text
quiet
active
tense
volatile
```

## 5. Event application

Supported events:

```text
front_escalation
front_deescalation
territory_strengthen
territory_weaken
territory_alert
```

An input event records:

```text
id
event_type
target_type
target_id
amount
sector
source
actor_id
cause_id
```

## 6. Mutation provenance

Every event produces exactly one primary mutation:

```text
mutation_id
revision
tick
cause_event_id
target_type
target_id
before
after
secondary_mutations[]
provenance
```

`front_escalation` may also alter alert/stability in territories adjacent to the front. Those changes are stored under `secondary_mutations`.

## 7. Derived events

Mutation:

```text
front state changes
```

becomes semantic event:

```text
front_state_changed
```

Mutation:

```text
territory state changes
```

becomes:

```text
territory_state_changed
```

The derived event stores its runtime cause.

## 8. Observation locality

For direct observations:

```text
Manhattan radius = 1 sector
```

Observation records:

```text
source_event_id
sector
subject_type
subject_id
fact
evidence
delivery_state
knowledge_state
```

Crucially:

```text
observation != memory
observation != knowledge
observation != belief
```

0.8.0 never claims that an NPC knows an event merely because it happened.

## 9. EBE runtime bundle

`build_dynamic_ebe_bundle()` exports:

```text
static_entities
dynamic_entities
events
observations
```

It can export only changes after a chosen revision:

```text
since_revision = N
```

This supports incremental runtime handoff.

## 10. Replay invariant

Given:

```text
same static world
+
same ordered runtime event log
```

PixelGen must reconstruct exactly the same dynamic state.

## 11. Immutability invariant

Applying or replaying events may not alter the static world or its semantic fingerprint.

## 12. Current non-goals

0.8.0 deliberately does not yet implement:

```text
NPC memory stores
belief divergence
rumor decay
agent-to-agent transmission
territory ownership flips
front geometry movement
time-based autonomous simulation
```

The purpose of 0.8.0 is to make the state mutation and information-locality foundation correct before those systems consume it.
