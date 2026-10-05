# EBE Lua v0.2.1 + LÖVE2D thin renderer

A Lua/LÖVE2D port of the EBE v0.2.1 hardening prototype. The goal is architectural separation:

```text
Game / rules
    ↓
EBE (pure Lua)
    ↓        (no renderer dependency)
Game adapter/state
    ↓
Renderer contract
    ↓
LÖVE2D now / FPE later
```

## Key rule

Nothing under `ebe/` calls or requires `love.*`. The core can be tested with a normal Lua 5.1/LuaJIT interpreter.

## Run the LÖVE demo

From the project directory:

```bash
love .
```

Controls:

- `1` — freeze event
- `2` — burn event
- `3` — craft event
- `Space` — advance one simulation hour and propagate knowledge
- `R` — clear EBE state/history
- `Esc` — quit

The graphics intentionally use only tiny tiles, rectangles, circles and a warm restrained palette. The visual layer is deliberately thin; the interesting part is the event → observation → interpretation → propagation → reaction chain.

## Run pure Lua tests

With Lua/LuaJIT installed:

```bash
lua tests/smoke.lua
lua tests/hardening.lua
```

or:

```bash
luajit tests/smoke.lua
luajit tests/hardening.lua
```

## Modules

```text
ebe/
  core/
    clock.lua
    event.lua
    event_bus.lua
    ring_buffer.lua
    spatial_grid.lua
    state_store.lua
    util.lua
  memory/
    memory_store.lua
  perception/
    knowledge_store.lua
    observation_system.lua
    observer_registry.lua
  interpretation/
    interpreter.lua
  propagation/
    propagation_system.lua
  reaction/
    reaction_system.lua
  ebe.lua
  init.lua

render/
  renderer.lua          thin contract
  love_renderer.lua     LÖVE2D implementation
  palette.lua

demo/
  world.lua
  game.lua

main.lua
conf.lua
```

## v0.2.1 parity

Ported concepts from the JS hardening branch:

- bounded/unlimited `RingBuffer`
- `SpatialGrid` candidate filtering
- O(1) `ObserverRegistry`
- one observer snapshot per `advance()`
- `propagation_history_window`
- event bus and nested reaction events
- memory, knowledge, interpretation, propagation and decay
- snapshot/restore

## Intentional Lua differences

- JavaScript `Map`/`Set` become Lua tables.
- `Infinity` becomes `math.huge`; `max_log_size = 0` is also accepted as unlimited.
- names use snake_case idiomatic Lua (`get_observers`, `interpret_for`, `parent_id`).
- event immutability cannot be enforced like `Object.freeze`; callers should treat emitted events as immutable records.
