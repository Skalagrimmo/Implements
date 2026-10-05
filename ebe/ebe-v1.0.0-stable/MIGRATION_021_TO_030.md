# EBE Migration — v0.2.1 → v0.3.0

## Compatibility strategy

v0.3.0 does not delete the v0.2.1 runtime.

The recovered 0.2.1 source tree is included and its old public constructor remains:

```lua
local EBE=require("ebe")

local engine=EBE.create({
  get_observers=...,
  observe=...,
  transmission_factor=...,
})
```

Historical tests continue to run unchanged.

## New API

New information-locality projects should prefer:

```lua
local EBE=require("ebe")

local rt=EBE.Runtime.new({
  seed=3030,
})
```

## Namespace split

Historical API:

```text
EBE.create
EBE.LegacyEvent
EBE.LegacyEventBus
EBE.ManualClock
EBE.StateStore
EBE.RingBuffer
EBE.SpatialGrid
EBE.MemoryStore
EBE.KnowledgeStore
EBE.ObservationSystem
EBE.ObserverRegistry
EBE.LegacyInterpreter
EBE.PropagationSystem
EBE.ReactionSystem
```

New API:

```text
EBE.Runtime
EBE.Event
EBE.EventBus
EBE.Observation
EBE.Memory
EBE.Belief
EBE.Knowledge
EBE.Interpretation
EBE.Propagation
EBE.Reaction
EBE.PixelGenV080
EBE.Snapshot
```

The explicit `Legacy*` aliases avoid ambiguous use of the old and new event/bus/interpreter models.

## Why not replace the old stores in place?

v0.2.1 has a useful optimized event-level model:

```text
event
→ witness confidence
→ knowledge store
→ propagation
```

v0.3 adds a more detailed agent epistemic model:

```text
observation
→ memory
→ belief
→ knowledge
```

Replacing the old store classes in place would silently change old game behavior.

Keeping both allows gradual migration.

## Renderer

The corrected 0.2.1 renderer adapter is preserved unchanged.

The renderer remains outside EBE core, so either runtime can coexist with:

```text
LÖVE2D now
FPE later
```

## Suggested migration path

1. Keep existing game mechanics on `EBE.create`.
2. Add `EBE.Runtime` only for NPC information and rumor systems.
3. Feed important old EBE events into the new runtime as observations.
4. Move reactions to belief-driven rules gradually.
5. Retire old knowledge propagation only when game behavior is verified.
