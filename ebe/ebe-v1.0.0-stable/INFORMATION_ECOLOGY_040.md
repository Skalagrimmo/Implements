# EBE v0.4.0 — Information Ecology Contract

## 1. Institutional node

An institution is a semantic information-processing node:

```text
id
kind
sector
faction
policy
subscribers
archive
```

Institutional kinds are presets, not hard-coded behavior walls. Policies can be overridden per instance.

## 2. Report flow

```text
agent belief
↓
report
↓
institution receive delay
↓
acceptance threshold
↓
archive
↓
rebroadcast threshold
↓
institution transform
↓
broadcast delay
↓
subscriber
```

## 3. Explicit routing

No institution broadcasts globally.

Every target must be an explicit subscriber.

```text
institution
→ agent
```

or:

```text
institution
→ institution
```

## 4. Source lineage

Every report can carry:

```text
origin_observation_ids[]
route[]
hop_count
```

An observation root represents independent evidence.

Relaying a report does not create a new root.

## 5. Echo protection

If the same evidence travels:

```text
A → B → C → A
```

its root IDs remain unchanged.

Therefore:

```text
repetition != independent corroboration
```

## 6. Reporter count vs root count

Beliefs now distinguish:

```text
reporter_count
source_count
```

where:

```text
reporter_count
= distinct immediate reporting identities

source_count
= distinct independent evidence roots
```

Knowledge corroboration uses independent roots.

## 7. Institutional memory

Institutions keep bounded archives.

This archive is not agent knowledge.

It represents retained institutional reports.

## 8. Distortion

Institutional transforms are deterministic for a fixed runtime history.

Presets can define different distortion rates.

## 9. Cycle protection

Institution-to-institution routing checks lineage.

If a target institution is already present in the route, that hop is not queued.

A global `max_hops` cap provides an additional bound.

## 10. Persistence

Institution state is included in runtime snapshots:

```text
institutions
queue
routing_log
sequence
max_hops
```

## 11. Compatibility

v0.3 snapshots without ecology are valid migration inputs.

They restore into v0.4 with:

```text
ecology.institutions = {}
ecology.queue = {}
```

## 12. Non-goals

v0.4 does not yet implement:

```text
institutional censorship agendas
faction-wide collective belief
printing physical documents as game items
route capacity / congestion
caravan movement through world sectors
automatic settlement network synthesis from PixelGen
EBE → PixelGen write-back
```
