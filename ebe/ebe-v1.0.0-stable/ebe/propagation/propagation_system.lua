local util = require("ebe.core.util")
local PropagationSystem = {}
PropagationSystem.__index = PropagationSystem

function PropagationSystem.new(opts)
  opts = opts or {}
  assert(type(opts.get_observers) == "function", "get_observers is required")
  assert(opts.knowledge, "knowledge store is required")
  assert(opts.interpreter, "interpreter is required")
  assert(type(opts.transmission_factor) == "function", "transmission_factor is required")
  return setmetatable({
    get_observers = opts.get_observers,
    knowledge = opts.knowledge,
    interpreter = opts.interpreter,
    transmission_factor = opts.transmission_factor,
    min_source_confidence = opts.min_source_confidence or 0.5,
    min_received_confidence = opts.min_received_confidence or 0.2,
    get_candidates = opts.get_candidates,
    random = opts.random or math.random,
  }, PropagationSystem)
end

function PropagationSystem:propagate(event, time, observers_override)
  time = time or 0
  local observers = observers_override or self.get_observers()
  local transmissions = {}

  for i = 1, #observers do
    local source = observers[i]
    local source_knowledge = self.knowledge:get(source.id, event.id)
    if source_knowledge and source_knowledge.confidence >= self.min_source_confidence then
      local candidates = self.get_candidates and self.get_candidates(source, observers) or observers
      for j = 1, #candidates do
        local target = candidates[j]
        if target.id ~= source.id then
          local factor = self.transmission_factor(event, source, target, source_knowledge)
          if util.is_finite(factor) and factor > 0 then
            local current = self.knowledge:confidence(target.id, event.id)
            local received = math.min(0.99, source_knowledge.confidence * factor)
            if received >= self.min_received_confidence and received > current + 0.01 then
              local interpretation = self.interpreter:interpret(event, target)
              local inherited_spin = source_knowledge.spin
              local spin = (inherited_spin and self.random() < 0.7) and inherited_spin or interpretation.label
              local record = self.knowledge:set(target.id, event.id, received, {
                source = source.id,
                spin = spin,
                time = time,
              })
              transmissions[#transmissions + 1] = {
                event_id = event.id,
                source = source.id,
                target = target.id,
                confidence = record.confidence,
                spin = spin,
              }
            end
          end
        end
      end
    end
  end
  return transmissions
end

return PropagationSystem
