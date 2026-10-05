# EBE Migration — v0.4.0 → v0.5.0

## Existing manual institutional networks

No migration is required.

These APIs still work:

```lua
rt:add_institution(...)
rt:subscribe_institution(...)
rt:report_to_institution(...)
```

## Optional auto-synthesis

Instead of writing the institutional graph manually:

```lua
local world=EBE.PixelGenNetworkSynth.load_world("world.lua")
rt:synthesize_pixelgen_network(world,{attach_existing_agents=true})
```

## Local report convenience

v0.4:

```lua
rt:report_to_institution("mara","press_01",claim)
```

v0.5 can use:

```lua
rt:report_to_local_network("mara",claim)
```

The runtime resolves Mara's current network access automatically.

## Movement

Under an active synthesized plan:

```lua
rt:move_agent("mara",{x,y})
```

also updates institutional access.

## Snapshot migration

v0.4 and v0.3 snapshots remain accepted.

Missing fields initialize as:

```text
network_plan = nil
agent_institution_access = {}
```

## Institution snapshot extension

Institutions now also preserve:

```text
metadata
lineage_index
duplicate_lineage_count
```

Old snapshots without those fields remain valid.

## Important semantic change

Generated route options now matter to information transport:

```text
delay
trust
distortion exposure
route provenance
```

The underlying v0.4 institution policy still controls its own acceptance, archive, rebroadcast and content distortion behavior.
