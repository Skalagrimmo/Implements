local ManualClock = {}
ManualClock.__index = ManualClock

function ManualClock.new(initial_time)
  local self = setmetatable({}, ManualClock)
  self._time = initial_time or 0
  return self
end

function ManualClock:now()
  return self._time
end

function ManualClock:advance(delta)
  delta = delta or 1
  assert(type(delta) == "number" and delta == delta and delta ~= math.huge and delta ~= -math.huge, "delta must be finite")
  self._time = self._time + delta
  return self._time
end

function ManualClock:set(value)
  assert(type(value) == "number" and value == value and value ~= math.huge and value ~= -math.huge, "time must be finite")
  self._time = value
end

return ManualClock
