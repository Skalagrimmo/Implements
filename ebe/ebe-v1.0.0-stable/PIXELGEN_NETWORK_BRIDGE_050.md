# PixelGen v0.8 → EBE v0.5 Information Infrastructure Bridge

PixelGen and EBE now exchange two different kinds of context.

## Dynamic handoff

Existing v0.3 bridge:

```text
PixelGen dynamic EBE bundle
→ events
→ local observations
→ EBE agents
```

This answers:

```text
What happened?
Where can it be observed?
```

## Static world topology handoff

New v0.5 synthesis:

```text
PixelGen world geography
→ institutions
→ communication routes
→ access network
```

This answers:

```text
Through what social/infrastructural channels can information travel?
```

## Why two inputs?

The compact dynamic EBE bundle intentionally does not contain the full world road/link/landmark graph.

Therefore auto-synthesis uses the richer PixelGen world table.

A typical runtime can load both:

```lua
rt:ingest_pixelgen_file("runtime_bundle.lua")
rt:synthesize_pixelgen_network_file("world_network.lua",{
  attach_existing_agents=true,
})
```

## JSON workflow

For PixelGen `state-demo`:

```text
dynamic_state_6x5_seed7301.world.json
```

convert it:

```bash
python tools/pixelgen_world_json_to_lua.py \
  dynamic_state_6x5_seed7301.world.json \
  world_network.lua
```

Then load `world_network.lua` in EBE.

## Provenance chain

A report can now retain:

```text
PixelGen event root
↓
local direct observation
↓
agent belief
↓
agent access route
↓
local institution
↓
world-derived route edge(s)
↓
receiving institution
↓
receiving agent access route
↓
agent memory
```

This gives future debugging and narrative systems a concrete answer to:

```text
Why does this NPC believe this?
How did the information physically/socially reach them?
```
