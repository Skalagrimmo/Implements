-- Renderer contract used by the demo/game layer.
-- EBE never requires this module and never knows about LÖVE.
--
-- IMPORTANT: renderer implementations use Lua method syntax (`:`), so the
-- adapter must forward the implementation object as `self`. Calling
-- `self.impl.draw_tile(...)` would shift every argument by one position and
-- eventually pass nil as the tile size to love.graphics.rectangle().
local Renderer = {}
Renderer.__index = Renderer

function Renderer.new(impl)
  assert(type(impl) == "table", "renderer implementation table is required")
  return setmetatable({ impl = impl }, Renderer)
end

function Renderer:begin_frame(world)
  if self.impl.begin_frame then self.impl:begin_frame(world) end
end

function Renderer:draw_tile(...)
  if self.impl.draw_tile then self.impl:draw_tile(...) end
end

function Renderer:draw_entity(...)
  if self.impl.draw_entity then self.impl:draw_entity(...) end
end

function Renderer:draw_event(...)
  if self.impl.draw_event then self.impl:draw_event(...) end
end

function Renderer:draw_hud(...)
  if self.impl.draw_hud then self.impl:draw_hud(...) end
end

function Renderer:end_frame(world)
  if self.impl.end_frame then self.impl:end_frame(world) end
end

return Renderer
