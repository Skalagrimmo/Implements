local util = require("ebe.core.util")
local ObservationSystem = {}
ObservationSystem.__index = ObservationSystem

function ObservationSystem.new(opts)
  opts = opts or {}
  assert(type(opts.get_observers) == "function", "get_observers is required")
  assert(type(opts.observe) == "function", "observe rule is required")
  return setmetatable({
    get_observers = opts.get_observers,
    observe = opts.observe,
  }, ObservationSystem)
end

function ObservationSystem:observers_of(event)
  local result = {}
  local observers = self.get_observers()
  for i = 1, #observers do
    local observer = observers[i]
    local confidence = self.observe(event, observer)
    if util.is_finite(confidence) and confidence > 0 then
      result[#result + 1] = { observer = observer, confidence = math.min(1, confidence) }
    end
  end
  return result
end

return ObservationSystem
