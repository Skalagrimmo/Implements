# EBE v1.0.0 — Stable Epistemic Runtime

EBE 1.0.0 is the stable promotion of the v0.9 contract-freeze candidate. No new cognition subsystem was added during promotion; the release freezes the public API and persistence boundary, closes final hostile-input gaps, and proves semantic parity with v0.9. See `EBE_1_0_CONTRACT.md`, `MIGRATION_090_TO_100.md`, and `V100_TEST_REPORT.md`.

Stable contract fingerprints:

```text
public API   ebe-stablehash-v1:251571066
persistence  ebe-stablehash-v1:254293849
```

PixelGen remains objective world authority; the PixelGen EBE bundle schema remains `0.8.0`.

## v0.8 public action API

```lua
rt:register_reaction_action_adapter(reaction_kind, spec)
rt:request_action(spec)
rt:action_request(id)
rt:action_requests(status, domain)
rt:export_pixelgen_action(id)
rt:resolve_action_request(id, "applied" | "rejected", result)
```

PixelGen feedback is also correlated automatically during `rt:ingest_pixelgen(bundle)` when a derived event carries `cause_event_id` equal to an exported EBE action request ID.


EBE is the epistemic/event layer of the engine stack.

It does not define objective world truth. PixelGen does that.

EBE answers:

```text
who observed what?
what did they remember?
what do they believe?
what counts as knowledge?
how does information travel?
what does an institution retain?
what does a bounded group collectively accept?
what does an institution choose to publish, delay, or suppress?
```

The core remains pure Lua and renderer-independent.

## Architecture

```text
PIXELGEN 1.0
objective semantic reality
+ local evidence availability
        ↓

EBE LOCAL COGNITION
observation
↓
memory
↓
belief
↓
knowledge
↓
interpretation
↓
reaction

        +

EBE INFORMATION ECOLOGY
agent
↓
institution
↓
route / delay / trust / distortion
↓
agent

        +

EBE COLLECTIVE EPISTEMICS
agent belief
↓
explicit report
↓
bounded group ledger
↓
source-lineage aggregation
↓
tentative / corroborated / consensus
↓
explicit publication
↓
agent or institution
```


        +

EBE INSTITUTIONAL POLICY
institution archive
↓
agenda / audience rules
↓
publish / hold / suppress
↓
priority scheduling
↓
explicit subscriber
```

## Historical compatibility

The original v0.2.1 API remains available:

```lua
local EBE=require("ebe")
local legacy=EBE.create({...})
```

The current runtime:

```lua
local EBE=require("ebe")
local rt=EBE.Runtime.new({seed=6060})
```

## PixelGen 1.0

PixelGen 1.0 keeps its EBE handoff schema at `0.8.0`.

Therefore the bridge remains named:

```lua
EBE.PixelGenV080
```

because the name describes the bundle schema, not the current PixelGen package number.

A real PixelGen 1.0 canonical runtime bundle is included:

```text
demo/pixelgen_v100_runtime.lua
```

and the compact full-world network view:

```text
demo/pixelgen_v100_network.lua
```

v0.6 tests both.

See:

```text
PIXELGEN_1_0_COMPATIBILITY_060.md
```

## Local cognition

PixelGen evidence is staged as sector-local evidence.

EBE deliberately does not expand its radius a second time.

```text
PixelGen observation at sector [x,y]
↓
only an agent currently in [x,y]
receives that direct evidence
```

Then:

```text
Observation
≠ Memory
≠ Belief
≠ Knowledge
```

remain distinct objects/stages.

## Source lineage

The important invariant from v0.4 remains:

```text
message copies
!=
independent evidence
```

Beliefs distinguish:

```text
reporter_count
source_count
```

where:

```text
reporter_count
= immediate reporting identities

source_count
= independent observation roots
```

Echo loops therefore cannot manufacture corroboration.

## Automatic PixelGen information infrastructure

The v0.5 subsystem remains available:

```lua
local world=EBE.PixelGenNetworkSynth.load_world(
  "demo/pixelgen_v100_network.lua"
)

local plan=rt:synthesize_pixelgen_network(world,{
  allow_gated=true,
  allow_secret=false,
  attach_existing_agents=true,
})
```

It derives:

```text
landmarks / regional centers / front sites / main path
↓
institutions
↓
weighted routes
↓
sector access
```

Current institution kinds include:

```text
printing_house
shrine_circle
caravan_exchange
military_post
settlement_square
roadside_relay
front_watch
```

Routes retain geographic provenance:

```text
path
path_cost
front_crossings
region_crossings
transition_sectors
delay
trust
distortion
risk
```

## New in v0.6 — Collectives

Create a bounded group:

```lua
rt:add_collective({
  id="watch_council",
  kind="faction_council",
  faction="watch",
  members={"mara","iva","levko"},
})
```

Membership does not share knowledge.

A member submits an existing belief explicitly:

```lua
rt:submit_to_collective(
  "mara",
  "watch_council",
  "front:front_0:status"
)
```

Inspect the aggregate:

```lua
local c=rt:get_collective_consensus(
  "watch_council",
  "front:front_0:status"
)
```

A collective aggregate records:

```text
selected value
confidence
agreement

winning independent roots
all independent roots
conflicting roots

reporter count
total reporter count
alternatives
```

Current states:

```text
tentative
corroborated
consensus
```

## Echo protection at group level

Example:

```text
Mara sees root_A
Mara → Oles
Mara reports root_A
Oles reports root_A
```

Result:

```text
reporters = 2
roots = 1
state = tentative
```

Then Iva observes the same fact independently:

```text
root_B
```

Result:

```text
reporters = 3
roots = 2
state = consensus
```

The group never treats repetition as independent evidence.

## Explicit publication

Even after a collective reaches consensus, members do not automatically know it.

Subscribe a target:

```lua
rt:subscribe_collective(
  "watch_council",
  "levko",
  {trust=0.95}
)
```

Publish:

```lua
rt:publish_collective(
  "watch_council",
  "front:front_0:status"
)
```

Levko receives ordinary transmitted evidence with the original independent roots preserved.

## Collective → institution

A collective can also publish into the existing information network:

```lua
rt:subscribe_collective(
  "watch_council",
  "print_house",
  {trust=0.95}
)
```

Then:

```text
watch_council
↓
printing house
↓
caravan
↓
agent
```

still preserves root lineage.

## Faction auto-enrollment

Optional:

```lua
rt:add_collective({
  id="watch_archive",
  faction="watch",
  metadata={
    auto_enroll_faction=true
  }
})
```

Matching agents become members.

They do not automatically receive any group belief.

## Demos

Pure Lua collective demo:

```bash
lua demo/collective_epistemics_demo.lua .
```

Canonical behavior:

```text
Mara report
→ roots=1 reporters=1 tentative

Oles repeats Mara
→ roots=1 reporters=2 tentative

Iva independent report
→ roots=2 reporters=3 consensus

explicit publication
→ Levko receives belief / corroborated knowledge
```

LÖVE demo:

```text
main.lua
```

Controls:

```text
M / I   agent → local institution report
G / H   Mara / Iva → watch council
P       publish council → Levko
A       advance 0.5h
F       advance 5h
R       reset
```

## Tests

Historical:

```bash
lua tests/smoke.lua
lua tests/hardening.lua
lua tests/renderer_forwarding.lua
lua tests/run_all.lua .
```

Fuzz:

```bash
lua tests/fuzz_v030.lua .
lua tests/fuzz_v040.lua .
lua tests/fuzz_v050.lua .
lua tests/fuzz_v060.lua .
```

Extended collective soak:

```bash
lua tests/soak_v060.lua .
```

## Snapshot compatibility

v0.6 restores runtime snapshots from:

```text
0.6.0
0.5.0
0.4.0
0.3.0
```

Pre-v0.6 snapshots acquire an empty collective layer.

No collective state is inferred or invented during migration.

## Ownership boundary

```text
PixelGen
= objective semantic world state

EBE agent cognition
= individual models of that world

EBE institutions
= bounded information-processing routes/archives

EBE collectives
= bounded explicit group aggregation
```

A collective aggregate is not global truth and is not automatically installed in any agent.

## Current non-goals

v0.6 does not yet implement:

```text
institutional censorship / agendas
propaganda policy
collective memory decay
ranked voting / authority
collective-to-collective routing
autonomous faction decisions
semantic write-back to PixelGen
physical documents
network capacity economics
```

Those can be built later without changing the v0.6 source-lineage foundation.

## Road to 1.0

Current planned direction:

```text
0.6  collective epistemics
↓
0.7  institution policies / censorship / priorities
↓
0.8  reaction → explicit semantic action requests
↓
0.9  persistence / hostile-input / API hardening
↓
1.0  stable epistemic runtime
```


## v0.7 institutional policy example

```lua
rt:add_institution({
  id="press",
  kind="printing_house",
  editorial={
    agenda={["front:"]=0.40},
    rules={
      {
        id="restricted_front",
        match={target_id="outsider",key_prefix="front:"},
        action="suppress",
      },
      {
        id="front_priority",
        match={target_id="levko",key_prefix="front:"},
        action="publish",
        priority=0.40,
      },
    },
  },
})
```

The source report is still retained in the institutional archive. The policy only controls publication behavior.

See `INSTITUTIONAL_POLICY_070.md`.
