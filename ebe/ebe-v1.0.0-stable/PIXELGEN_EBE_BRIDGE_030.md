# EBE v0.3.0 — PixelGen v0.8 Runtime Bridge

## Ownership boundary

PixelGen owns:

```text
static world semantics
dynamic territory/front state overlay
state mutation provenance
derived semantic events
local evidence availability
```

EBE owns:

```text
agent observation assignment
memory
belief
knowledge
interpretation
communication
distortion
reaction
```

## Input

The bridge consumes PixelGen v0.8 runtime bundles shaped like:

```text
version
source
contract
static_entities[]
dynamic_entities[]
events[]
observations[]
```

## Required contract

If present, these values must be:

```text
global_knowledge = forbidden

observation_semantics =
local evidence only
```

A bundle that claims global knowledge is rejected.

## Entity ingestion

Static and dynamic semantic entities are registered together without overwriting one another:

```text
runtime.entities[id]
├── static
└── dynamic
```

For example, a territory can retain static `center` / `sector_count` while its dynamic `control_strength` / `alert` / `stability` is refreshed by newer PixelGen revisions.

## Event ingestion

PixelGen derived events are stored in:

```text
runtime.external_events
```

and exposed on the EBE bus:

```text
pixelgen.event
```

They do not directly enter agent memory.

## Observation ingestion

PixelGen observations are normalized and staged under:

```text
runtime.available_observations
```

Bus notification:

```text
pixelgen.observation_available
```

Still no agent knows anything at this point.

## Local assignment

Calling:

```lua
runtime:assign_local_observations()
```

checks each staged observation against each current agent sector.

Only exact sector matches receive direct evidence.

Example:

```text
observation sector [0,2]

Mara  [0,2] → receives evidence
Levko [5,4] → receives nothing
```

This is deliberate because PixelGen already expanded the originating event into the allowed direct-observation sectors.

Expanding again inside EBE would double-count locality.

## Incremental bundles

PixelGen v0.8 supports:

```text
since_revision
```

EBE ingestion is idempotent by:

```text
entity id
event id
observation id
```

Re-importing the same bundle does not duplicate memory or event evidence.

## Canonical fixture

Included:

```text
demo/pixelgen_v080_runtime.lua
```

Contents:

```text
11 dynamic/static semantic entities
3 derived events
13 local observations
```

The fixture corresponds to the PixelGen dynamic-state demo around seed 7301 / 6×5.

## Example epistemic path

```text
PixelGen:
front_0 active → tense

↓ derived event

PixelGen:
observation available [0,2]

↓ local EBE assignment

Mara:
memory(obs)
belief(front_0.status = tense)
knowledge(direct evidence)

↓ explicit communication link
delay = 2
trust < 1
distortion chance > 0

Levko:
transmitted observation
belief(front_0.status ≈ tense)

↓ independent second report

Levko:
corroborated knowledge
```

## No write-back yet

v0.3.0 does not mutate PixelGen state.

The bridge is currently:

```text
PixelGen → EBE
```

A future version can define a controlled reaction/write-back contract such as:

```text
EBE reaction
↓
semantic action request
↓
PixelGen world-state event
↓
new PixelGen derived event
↓
new EBE observations
```

That feedback loop should remain explicit and provenance-preserving.
