# EBE v0.5.0 — PixelGen Network Synthesis Contract

## Input contract

The synthesizer consumes a PixelGen world table containing:

```text
cols / rows
sectors[].links
landmark_system.placements
geography.regions
gameplay.main_path
territory_graph.front_sites
influence_topology.boundary_edges
```

The compact converter can extract exactly these fields from a full `.world.json`.

## Pipeline

```text
PixelGen semantic anchors
↓
institution synthesis
↓
weighted sector graph
↓
all reachable institution-pair candidates
↓
minimum spanning forest
↓
local redundancy completion
↓
sector → nearest institution access index
↓
EBE InformationEcology subscriptions
```

## Institution identity

Every auto node records provenance in `metadata`:

```text
generated_by
source_kind
source ids / types
roles[]
sources[]
```

Region/front roles may merge into an already generated institution at the same sector.

## Public path policy

Default:

```text
open   allowed
gated  allowed with higher cost
secret disallowed
sealed disallowed
```

Optional:

```lua
allow_gated=false
allow_secret=true
```

No route may contain a world-link step forbidden by its plan policy.

## Main path preference

Edges belonging to `gameplay.main_path` are discounted:

```text
cost × 0.78
```

This is a preference, not a hard constraint.

## Backbone invariant

The synthesizer does not create an all-to-all institutional graph.

It chooses a deterministic minimum spanning forest over reachable candidates, then adds limited local redundancy.

If the public world graph is disconnected:

```text
components > 1
```

is valid and reported as a warning.

It is preferable to a fabricated connection through sealed terrain.

## Route semantics

Each route stores:

```text
id
a / b institutions
path[]
path_cost
delay
trust
distortion
risk
front_crossings
region_crossings
transition_sectors
main_path_steps
access_states
reason = backbone | redundancy
```

## Sector access

For every sector reachable from at least one institution:

```text
sector_access["x,y"]
```

stores its deterministic lowest-cost institutional access path.

Tie-break:

```text
lowest path cost
then lexicographically lowest institution id
```

## Runtime application

Applying a plan:

```text
creates missing synthesized institutions
adds bidirectional route subscriptions
stores network_plan
optionally attaches agents
```

Reapplying the identical plan is safe.

Applying a different plan to a runtime that already owns one is rejected.

## Agent movement

When an agent moves under an active plan:

```text
old institution subscription removed
↓
sector access recomputed from plan
↓
new institution subscription added
```

## Traffic / echo protection

Institution archives now index reports by:

```text
claim key
+
independent origin observation ids
```

Multiple route copies of one evidence root are suppressed from repeated rebroadcast.

A higher-confidence duplicate may upgrade the retained archive copy, but it does not become a new independent root.

## Determinism

Same:

```text
PixelGen world
synthesis options
EBE version
```

must produce the same plan and plan fingerprint.

Canonical seed 7301 / 6×5:

```text
fingerprint = 1314574499
```
