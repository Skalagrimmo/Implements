package.path = "./?.lua;./?/init.lua;" .. package.path
local A = require("tests.assertions")
local EBE = require("ebe")
local Interpreter = require("ebe.interpretation.interpreter")

local observers = {
  { id = "a", x = 0, y = 0, values = { nature = 1 } },
  { id = "b", x = 10, y = 0, values = { nature = -1 } },
}
local ebe = EBE.create({
  interpreter = Interpreter.new(),
  get_observers = function() return observers end,
  observe = function(event, observer) return observer.id == "a" and 1 or 0 end,
  transmission_factor = function() return 0.8 end,
  reaction_rules = {},
  decay_rate = 1,
})
local event = ebe.emit({ type = "grow", location = { x = 0, y = 0 }, metadata = { semantics = { nature = 1 } } })
A.eq(ebe.knowledge:confidence("a", event.id), 1, "witness knowledge")
A.eq(ebe.knowledge:confidence("b", event.id), 0, "initial knowledge")
ebe.advance(1)
A.ok(ebe.knowledge:confidence("b", event.id) > 0, "propagation")
local snap = ebe.snapshot()
ebe.clear()
ebe.restore(snap)
A.eq(#ebe.history, 1, "restore history")
print("EBE Lua smoke test passed")
