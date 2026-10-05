package.path = "./?.lua;./?/init.lua;" .. package.path

local Renderer = require("render.renderer")

local seen = {}
local Impl = {}

function Impl:begin_frame(world)
  assert(self == Impl)
  assert(world.marker == "world")
  seen.begin_frame = true
end

function Impl:draw_tile(tile, x, y, size)
  assert(self == Impl)
  assert(tile == "grass")
  assert(x == 16)
  assert(y == 32)
  assert(size == 16)
  seen.draw_tile = true
end

function Impl:draw_entity(entity)
  assert(self == Impl)
  assert(entity.id == "npc")
  seen.draw_entity = true
end

function Impl:draw_event(event)
  assert(self == Impl)
  assert(event.type == "freeze")
  seen.draw_event = true
end

function Impl:draw_hud(info)
  assert(self == Impl)
  assert(info.hour == 3)
  seen.draw_hud = true
end

function Impl:end_frame(world)
  assert(self == Impl)
  assert(world.marker == "world")
  seen.end_frame = true
end

local renderer = Renderer.new(Impl)
local world = { marker = "world" }
renderer:begin_frame(world)
renderer:draw_tile("grass", 16, 32, 16)
renderer:draw_entity({ id = "npc" })
renderer:draw_event({ type = "freeze" })
renderer:draw_hud({ hour = 3 })
renderer:end_frame(world)

for _, key in ipairs({"begin_frame","draw_tile","draw_entity","draw_event","draw_hud","end_frame"}) do
  assert(seen[key], "missing forwarded call: " .. key)
end

print("Renderer forwarding regression test passed")
