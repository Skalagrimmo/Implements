local Util = require("ebe.util")

local Reaction = {}
Reaction.__index = Reaction

local function default_rules()
  return {
    {
      id = "avoid_volatile_front",
      match = function(agent, belief)
        return string.find(belief.key, "^front:")
          and string.find(belief.key, ":status$")
          and (belief.value == "tense" or belief.value == "volatile")
          and belief.confidence >= 0.58
      end,
      build = function(agent, belief, tick)
        return {
          kind = "avoid_front",
          agent_id = agent.id,
          tick = tick,
          claim_key = belief.key,
          believed_value = belief.value,
          confidence = belief.confidence,
        }
      end,
    },
    {
      id = "prepare_for_fragile_territory",
      match = function(agent, belief)
        return string.find(belief.key, "^territory:")
          and string.find(belief.key, ":status$")
          and (belief.value == "pressured" or belief.value == "fragile")
          and belief.confidence >= 0.58
      end,
      build = function(agent, belief, tick)
        return {
          kind = "prepare_exit",
          agent_id = agent.id,
          tick = tick,
          claim_key = belief.key,
          believed_value = belief.value,
          confidence = belief.confidence,
        }
      end,
    },
  }
end

function Reaction.new(opts)
  opts = opts or {}
  local self = setmetatable({
    rules = {},
    fired = {},
  }, Reaction)
  if opts.defaults ~= false then
    for _, rule in ipairs(default_rules()) do self:register(rule) end
  end
  return self
end

function Reaction:register(rule)
  assert(type(rule) == "table" and rule.id, "reaction rule id is required")
  assert(type(rule.match) == "function", "reaction rule match() is required")
  assert(type(rule.build) == "function", "reaction rule build() is required")
  self.rules[#self.rules + 1] = rule
end

function Reaction:evaluate(runtime, agent)
  local emitted = {}
  for _, rule in ipairs(self.rules) do
    for _, key in ipairs(Util.sorted_keys(agent.beliefs or {})) do
      local belief = agent.beliefs[key]
      if rule.match(agent, belief, runtime) then
        local fire_key = table.concat({
          tostring(agent.id),
          tostring(rule.id),
          tostring(key),
          Util.value_key(belief.value),
        }, "|")
        if not self.fired[fire_key] then
          self.fired[fire_key] = runtime.tick
          local reaction = rule.build(agent, belief, runtime.tick, runtime)
          reaction.rule_id = rule.id
          reaction.id = "reaction_" .. tostring(#runtime.reaction_log + 1)
          runtime.reaction_log[#runtime.reaction_log + 1] = Util.deepcopy(reaction)
          runtime.bus:emit("reaction.emitted", Util.deepcopy(reaction))
          if runtime._handle_reaction_action then
            runtime:_handle_reaction_action(reaction, agent, belief)
          end
          emitted[#emitted + 1] = reaction
        end
      end
    end
  end
  return emitted
end

function Reaction:snapshot()
  return { fired = Util.deepcopy(self.fired) }
end

function Reaction:restore(data)
  self.fired = Util.deepcopy((data or {}).fired or {})
end

return Reaction
