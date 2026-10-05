local util = require("ebe.core.util")
local Interpreter = {}
Interpreter.__index = Interpreter

local function default_semantics(event)
  return (event.metadata and event.metadata.semantics) or {}
end

local function default_values(observer)
  return observer.values or {}
end

local function default_labeler(score)
  if score > 0.5 then return "good" end
  if score < -0.4 then return "bad" end
  return "meh"
end

function Interpreter.dot_product(a, b)
  a, b = a or {}, b or {}
  local total = 0
  local seen = {}
  for k in pairs(a) do seen[k] = true end
  for k in pairs(b) do seen[k] = true end
  for k in pairs(seen) do total = total + (a[k] or 0) * (b[k] or 0) end
  return total
end

function Interpreter.new(opts)
  opts = opts or {}
  return setmetatable({
    semantic_resolver = opts.semantic_resolver or default_semantics,
    value_resolver = opts.value_resolver or default_values,
    labeler = opts.labeler or default_labeler,
  }, Interpreter)
end

function Interpreter:interpret(event, observer)
  local semantics = self.semantic_resolver(event, observer) or {}
  local values = self.value_resolver(observer, event) or {}
  local score = Interpreter.dot_product(semantics, values)
  return {
    observer_id = observer.id,
    event_id = event.id,
    score = score,
    label = self.labeler(score, event, observer),
    semantics = util.shallow_copy(semantics),
  }
end

return Interpreter
