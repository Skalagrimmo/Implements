package.path = "./?.lua;./?/init.lua;" .. package.path
local A = require("tests.assertions")
local EBE = require("ebe")
local RingBuffer = require("ebe.core.ring_buffer")
local SpatialGrid = require("ebe.core.spatial_grid")
local ObserverRegistry = require("ebe.perception.observer_registry")
local Interpreter = require("ebe.interpretation.interpreter")

local log = RingBuffer.new(3)
log:push(1); log:push(2); log:push(3); log:push(4)
local arr = log:to_array()
A.eq(log:length(), 3); A.eq(arr[1], 2); A.eq(arr[3], 4)

local unlimited = RingBuffer.new(0)
for i = 1, 20000 do unlimited:push(i) end
A.ok(unlimited:unlimited()); A.eq(unlimited:length(), 20000)

local a = { id = "a", x = -5, y = -5 }
local b = { id = "b", x = 15, y = 5 }
local c = { id = "c", x = 300, y = 300 }
local grid = SpatialGrid.new({ cell_size = 20 })
grid:rebuild({ a, b, c })
A.eq(grid:item_count(), 3)
c.x, c.y = 8, 8; grid:update(c)
local nearby = grid:query_radius(0, 0, 25)
local ids = {}; for i = 1, #nearby do ids[nearby[i].id] = true end
A.ok(ids.a and ids.b and ids.c, "spatial grid query")

local reg = ObserverRegistry.new({ { id = "a" }, { id = "b" } })
A.eq(reg:size(), 2); A.eq(reg:get("b").id, "b")

local obs = { { id = "a", values = { nature = 1 } }, { id = "b", values = { nature = 1 } } }
local reads = 0
local engine = EBE.create({
  interpreter = Interpreter.new(),
  get_observers = function() reads = reads + 1; return obs end,
  observe = function(e, o) return o.id == "a" and 1 or 0 end,
  transmission_factor = function(e, s, t) return (s.id == "a" and t.id == "b") and 0.8 or 0 end,
  max_log_size = 0,
  decay_rate = 1,
})
for i = 1, 25 do engine.emit({ type = "grow", metadata = { semantics = { nature = 1 } } }) end
local before = reads
engine.advance(1)
A.eq(reads - before, 1, "one observer snapshot per advance")
A.ok(engine.transmission_log:unlimited())
A.eq(engine.transmission_log:length(), 25)
print("EBE Lua v0.2.1 hardening tests passed")
