# JS → Lua porting notes

This is not a mechanical syntax translation. The architecture is preserved while using Lua 5.1/LuaJIT-friendly idioms for LÖVE2D.

## Preserved boundaries

- `ebe/` has zero dependency on LÖVE2D.
- `demo/game.lua` is the adapter between domain data and EBE.
- `render/renderer.lua` is a thin rendering contract.
- `render/love_renderer.lua` owns all `love.graphics` calls.

## Why this matters for FPE

The current dependency direction is:

```text
EBE <- Game adapter -> Renderer contract -> LÖVE2D
```

A future FPE backend can replace only the final implementation:

```text
Renderer contract -> FPE renderer/backend
```

without changing event, memory, knowledge, belief/interpretation or propagation logic.

## Hotfix 1 — Renderer method forwarding

Fixed the renderer adapter to forward implementation methods with `:` rather
than `.`. The previous adapter dropped the implementation `self`, shifting
arguments and causing `LoveRenderer:draw_tile()` to receive `size == nil`.
All renderer methods are fixed (`begin_frame`, `draw_tile`, `draw_entity`,
`draw_event`, `draw_hud`, `end_frame`). Added `tests/renderer_forwarding.lua`.
