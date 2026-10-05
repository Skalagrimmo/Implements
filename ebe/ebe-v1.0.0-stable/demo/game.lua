local EBE = require("ebe")
local Interpreter = require("ebe.interpretation.interpreter")
local SpatialGrid = require("ebe.core.spatial_grid")
local World = require("demo.world")

local Game = {}
Game.__index = Game

local function dist(a, b)
  local dx, dy = a.x - b.x, a.y - b.y
  return math.sqrt(dx * dx + dy * dy)
end

function Game.new()
  local self = setmetatable({}, Game)
  self.world = World
  self.grid = SpatialGrid.new({ cell_size = 72 })
  self.grid:rebuild(World.observers)
  self.message = "A quiet village remembers what happens."

  local interpreter = Interpreter.new()
  local reaction_rules = {
    {
      matches = function(ctx)
        return ctx.knowledge.confidence >= 0.55 and ctx.interpretation.label ~= "meh"
      end,
      apply = function(ctx)
        local delta = ctx.interpretation.label == "good" and 1 or -1
        return {
          type = "mutation",
          target = "attitude:" .. ctx.observer.id,
          mode = "add",
          value = delta,
        }
      end,
    },
  }

  self.engine = EBE.create({
    interpreter = interpreter,
    get_observers = function() return World.observers end,
    observe = function(event, observer)
      if not event.location then return 0 end
      local d = dist(event.location, observer)
      if d <= 54 then return 1 end
      if d <= 86 then return 0.65 end
      return 0
    end,
    transmission_factor = function(event, source, target, source_knowledge)
      local d = dist(source, target)
      if d > 118 then return 0 end
      local same = source.group == target.group and 1.05 or 0.82
      return math.min(0.95, same * (1 - d / 180))
    end,
    get_candidates = function(source, all)
      return self.grid:query_radius(source.x, source.y, 118)
    end,
    reaction_rules = reaction_rules,
    propagation_history_window = 128,
    max_log_size = 512,
    decay_rate = 0.96,
    decay_minimum = 0.08,
  })

  self.engine.on("*", function(event)
    self.message = string.format("event: %s — %s", event.type, (event.metadata and event.metadata.description) or "")
  end)
  return self
end

function Game:emit_freeze()
  self.engine.emit({
    type = "freeze", actor = "hero", subject = "channel", location = { x = 72, y = 88 },
    metadata = { semantics = { nature = 1.0, cunning = 0.35, lore = 0.2 }, description = "The channel freezes into a bridge." },
  })
end

function Game:emit_burn()
  self.engine.emit({
    type = "burn", actor = "hero", subject = "lichen", location = { x = 274, y = 96 },
    metadata = { semantics = { harm = 1.5, nature = -1.0, cunning = 0.15 }, description = "Living lichen burns near the hunters." },
  })
end

function Game:emit_craft()
  self.engine.emit({
    type = "craft", actor = "hero", subject = "charm", location = { x = 158, y = 92 },
    metadata = { semantics = { trade = 0.7, lore = 0.8, cunning = 0.25 }, description = "A shard charm is crafted at the workbench." },
  })
end

function Game:advance_hour()
  local tx = self.engine.advance(1)
  self.message = string.format("hour advanced; %d transmissions", #tx)
end

function Game:reset()
  self.engine.clear()
  self.message = "World memory cleared."
end

function Game:knowledge_summary(observer)
  local parts = {}
  for i = 1, #self.engine.history do
    local event = self.engine.history[i]
    local k = self.engine.knowledge:get(observer.id, event.id)
    if k then
      parts[#parts + 1] = string.format("%s %d%% %s", event.type, math.floor(k.confidence * 100 + 0.5), k.spin or "?")
    end
  end
  return table.concat(parts, " | ")
end

return Game
