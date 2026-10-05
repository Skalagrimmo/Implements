# EBE v0.6.0 — Collective Epistemics Contract

## 1. Purpose

v0.6 adds bounded collective information without introducing telepathy.

A collective is an explicit epistemic ledger used by:

```text
faction councils
settlement assemblies
military cells
guilds
archives
ritual circles
other bounded groups
```

It is **not** a shared mind.

Core invariant:

```text
membership
!=
shared memory
!=
shared belief
!=
shared knowledge
```

Agents must report explicitly, and a collective must publish explicitly before any member or outside subscriber receives its aggregate view.

## 2. Flow

```text
agent observation
↓
agent memory / belief
↓
explicit report
↓
COLLECTIVE LEDGER
├─ bounded archive
├─ source-lineage deduplication
├─ alternatives
├─ reporter diversity
└─ independent-root aggregation
↓
collective aggregate state
↓
explicit publication
├─ agent
└─ institution
↓
ordinary EBE evidence processing
```

## 3. Collective state

A collective contains:

```text
id
kind
faction
metadata
policy
members{}
subscribers{}
reports{}
report_order[]
consensus{}
```

Default policy:

```text
acceptance_min          0.30
consensus_min           0.62
confidence_min          0.55
min_independent_roots   2
archive_capacity        256
publication_trust       0.90
members_only_submit     true
```

Policies are per-collective and can be overridden.

## 4. Members are not omniscient

Adding:

```lua
rt:add_collective_member("watch_council","levko")
```

changes membership only.

It does not copy:

```text
collective reports
collective aggregate state
other members' memories
other members' knowledge
```

into Levko.

The same applies to automatic faction enrollment.

## 5. Explicit reporting

An agent can submit an existing belief:

```lua
rt:submit_to_collective(
  "mara",
  "watch_council",
  "front:front_0:status"
)
```

The report carries:

```text
reporter identity
claim
confidence
origin_observation_ids[]
provenance
```

With `members_only_submit=true`, non-members are rejected.

## 6. Root lineage and echo protection

The central invariant remains:

```text
message copies
!=
independent evidence
```

Example:

```text
Mara observes root_A
Mara → Oles
Mara reports root_A
Oles reports root_A
```

The collective sees:

```text
reporters = 2
independent roots = 1
```

So repetition can increase reporter diversity, but it cannot manufacture corroboration.

## 7. One root, one vote per claim

For each claim key the collective selects at most one best contribution per independent root.

If the same root arrives repeatedly:

```text
root_A → direct
root_A → relay
root_A → institution
```

the root is still counted once.

If the same root arrives with contradictory transformed values, the highest-confidence version wins for that root; equal-confidence ties are deterministic.

This avoids echo-amplification while still retaining all reports in the bounded archive.

## 8. Alternatives and conflicts

Collective state does not erase disagreement.

For each claim it stores:

```text
value
confidence
agreement
support
state

source_count
independent_root_count
total_independent_root_count
conflicting_root_count

reporter_count
total_reporter_count
report_count

origin_observation_ids[]
alternatives{}
```

`source_count` refers to independent roots supporting the currently selected value.

`total_independent_root_count` includes independent roots across all alternatives.

Example:

```text
root_A → tense
root_B → active
```

can yield:

```text
selected roots = 1
total roots = 2
conflicting roots = 1
state = tentative
```

No false consensus is created.

## 9. Aggregate states

Current states:

```text
tentative
corroborated
consensus
```

Meaning:

```text
tentative
→ insufficient independent support for the selected alternative

corroborated
→ enough independent roots, but agreement/confidence is below consensus thresholds

consensus
→ enough independent roots and policy thresholds are satisfied
```

A collective aggregate is still not ontological truth. It is a bounded group-level information state.

## 10. Explicit publication

A collective publishes only to explicit targets.

```lua
rt:subscribe_collective(
  "watch_council",
  "levko",
  { trust = 0.95 }
)

rt:publish_collective(
  "watch_council",
  "front:front_0:status"
)
```

Publication to an agent creates normal transmitted evidence.

The original independent roots are preserved:

```text
collective publication
→ agent observation
→ memory
→ belief
→ knowledge rules
```

The collective does not bypass the ordinary cognition pipeline.

## 11. Publication into institutions

A collective may explicitly publish into the institutional information ecology:

```text
Collective
↓
Printing House
↓
Caravan Exchange
↓
Agent
```

The institutional route preserves the collective publication's original evidence roots.

Therefore a group digest cannot turn one source into many sources merely by traversing multiple institutions.

## 12. Faction auto-enrollment

A collective may use:

```lua
metadata = {
  auto_enroll_faction = true
}
```

When its `faction` matches an agent, the agent is enrolled automatically.

This changes membership only.

It does **not** create belief or knowledge.

## 13. Snapshot persistence

v0.6 snapshots include:

```text
collectives
collective_log
```

Each collective persists:

```text
members
subscribers
reports
archive order
policy
aggregate state
sequence counters
```

On restore, derived collective consensus is rebuilt from retained reports instead of blindly trusting stale derived data.

## 14. Migration

Snapshots from:

```text
0.5.0
0.4.0
0.3.0
```

remain accepted.

A pre-v0.6 snapshot restores with:

```text
collectives = {}
collective_log = {}
```

No collective state is invented.

## 15. PixelGen ownership boundary

PixelGen remains the authority for objective world reality.

Collectives consume agent beliefs that ultimately derive from evidence.

They do not mutate PixelGen and do not reinterpret PixelGen observations as global knowledge.

The boundary remains:

```text
PixelGen
objective semantic reality / local evidence availability

EBE agents
memory / belief / knowledge

EBE collectives
explicit group aggregation / publication
```

## 16. Non-goals of v0.6

Not yet implemented:

```text
institutional censorship agendas
collective propaganda policy
collective memory decay
formal voting procedures
rank-weighted faction authority
automatic faction action requests
collective-to-collective routing
physical documents
capacity/congestion economics
PixelGen write-back
```

Those are later layers. v0.6 establishes the source-lineage-correct collective epistemic foundation first.
