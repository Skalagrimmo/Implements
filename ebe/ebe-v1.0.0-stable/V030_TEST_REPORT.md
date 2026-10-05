# EBE v0.3.0 — Information Locality Test Report

## Release identity

```text
release: EBE v0.3.0
base: ebe-lua-v0.2.1-love-hotfix1
language: pure Lua core
optional renderer: LÖVE2D
PixelGen bridge: v0.8 runtime bundle
```

The upgrade was merged over the recovered full v0.2.1 hotfix source tree rather than replacing it with a clean-room rewrite.

## Release gate

```text
Lua source syntax checked: 51 files
syntax failures: 0

historical v0.2.1 regression tests: 3 PASS
new v0.3.0 regression tests: 4 PASS

information-locality fuzz:
200 simulations PASS
400 received rumor memories
44 deterministic distorted transmissions
```

Validation interpreter:

```text
texlua
```

A standalone `lua`, `luajit`, and `love` executable was not installed in the build environment.

Therefore:

```text
pure Lua runtime execution: TESTED
LÖVE2D visual execution: NOT TESTED IN THIS ENVIRONMENT
```

The LÖVE sources were syntax-checked with `texluac`.

---

## Historical compatibility

The following original v0.2.1 tests run unchanged:

```text
tests/smoke.lua
→ PASS

tests/hardening.lua
→ PASS

tests/renderer_forwarding.lua
→ PASS
```

This verifies continued behavior for:

```text
EBE.create(...)
event emission
witness knowledge
legacy propagation
legacy snapshot/restore
RingBuffer
SpatialGrid
ObserverRegistry
one-observer-snapshot-per-advance optimization
unlimited logs
renderer method forwarding
```

The old constructor remains:

```lua
local EBE=require("ebe")
local engine=EBE.create({...})
```

The new runtime is additive:

```lua
local runtime=EBE.Runtime.new({...})
```

---

## PixelGen v0.8 canonical fixture

The bundled fixture contains:

```text
semantic entities: 11
derived events: 3
local observations: 13
```

Entity registry contract:

```text
entity
├── static
└── dynamic
```

Verified for `territory_0`:

```text
static.center retained
static.sector_count retained

dynamic.control_strength retained
dynamic.stability retained
dynamic.alert retained
```

So dynamic state refresh does not destroy static identity.

---

## Information locality

Canonical agents:

```text
Mara   [0,2]
Iva    [0,3]
Levko  [5,4]
```

Immediately after PixelGen ingestion:

```text
Mara memory: 0
Iva memory: 0
Levko memory: 0
```

This is intentional.

Ingestion stages observations but does not assign them to agents.

After:

```lua
runtime:assign_local_observations()
```

only exact-sector agents receive direct evidence.

Canonical result:

```text
Mara:
belief = tense
confidence = 0.960
knowledge = tense / direct_evidence

Iva:
belief = tense
confidence = 0.960
knowledge = tense / direct_evidence

Levko:
no belief
no knowledge
no direct memory
```

So the far agent does not acquire omniscient state.

---

## Delayed propagation

Mara tells Levko:

```text
created t=0
delivery t=2
```

At:

```text
t=1
```

Levko still has:

```text
no belief
no knowledge
```

At:

```text
t=2
```

after one transmitted report:

```text
belief = tense
confidence ≈ 0.757
distinct reporting sources = 1

knowledge = no
```

This proves:

```text
rumor != knowledge
```

---

## Corroboration

Iva independently reports the same front state.

After the second report:

```text
belief = tense
distinct reporting sources = 2

knowledge = tense
basis = corroborated_reports
```

A dedicated regression additionally verifies:

```text
same sender repeats same claim twice
→ source_count remains 1
→ does not become corroborated knowledge
```

This prevents one repeatedly echoed voice from becoming artificial consensus.

---

## Contradictory evidence

The cognition test supplies:

```text
strong direct evidence:
front_0 = tense

weak transmitted contradiction:
front_0 = quiet
```

Result:

```text
chosen belief = tense
contradictory alternative remains stored
```

Evidence is not destructively overwritten.

---

## Memory decay

Memory confidence is time-dependent.

The test verifies:

```text
confidence after advance
<
confidence before advance
```

and fuzz advances agents for 72 hours without producing out-of-range confidence.

Current defaults:

```text
decay/hour = 0.985
forget below = 0.08
```

---

## Rumor distortion

Distortion is deterministic for fixed runtime history.

Fuzz:

```text
200 simulations
400 rumor memories delivered
44 transmissions distorted
```

The distortion test verifies that a 100% distortion policy eventually changes a supported status while remaining inside the valid status ladder:

```text
quiet
active
tense
volatile
```

No arbitrary impossible status is invented.

---

## Provenance

Every transmitted observation preserves:

```text
transmission_id
source_agent_id
distortion_applied
inherited provenance
```

The PixelGen bridge also retains integration revision provenance.

This gives future debugging/social simulation a path from belief back toward evidence.

---

## Reactions

Default reaction rules were exercised by the canonical demo.

Direct witnesses produce:

```text
front tense
→ avoid_front
```

A remote agent may also react after forming a sufficiently strong transmitted belief even before the claim qualifies as knowledge.

This is intentional:

```text
agents may act on uncertain information
```

---

## Snapshot / restore

Canonical runtime snapshot is serialized as deterministic Lua data.

Verified:

```text
snapshot
→ Lua source
→ dofile()
→ Runtime.restore()
→ snapshot

semantic equality = true
```

Canonical demo snapshot hash:

```text
1558191294
```

The snapshot contains no functions and does not depend on renderer state.

---

## Renderer separation

Search across all files under:

```text
ebe/
```

found:

```text
love.* dependency hits = 0
```

The renderer remains an outer adapter.

The historical renderer-forwarding regression passes, preserving the `:` method-call fix.

---

## Fuzz matrix

For each of 200 runtime seeds:

```text
2 direct witnesses
1 remote agent
2 explicit communication links
variable delay
variable trust
variable distortion
```

Checks include:

```text
remote agent starts with no direct memory
remote agent starts with no belief
rumors do not arrive before deliver_at
delivered remote evidence is transmitted, not direct
transmission provenance exists
belief confidence remains 0..1
long-term memory confidence remains 0..1
```

Result:

```text
200 / 200 PASS
```

---

## Known scope limits

These are not release failures:

```text
1. LÖVE2D executable was unavailable, so visual demo execution was not tested here.
2. v0.3.0 has no autonomous NPC schedule simulator.
3. Rumor source-lineage/echo-chamber analysis is not yet a full social graph theorem.
4. EBE currently consumes PixelGen runtime state but does not write reactions back into PixelGen.
5. Belief-driven dialogue generation is not included.
6. Group/faction memory is not yet a first-class cognition store.
```

## Assessment

v0.3.0 establishes a tested bridge from:

```text
PixelGen:
event exists locally
```

to:

```text
EBE:
specific agents observe it
→ remember it
→ believe something about it
→ may know it
→ interpret it
→ tell somebody else later
→ possibly distort it
→ provoke reactions
```

without turning world state into global NPC knowledge.
