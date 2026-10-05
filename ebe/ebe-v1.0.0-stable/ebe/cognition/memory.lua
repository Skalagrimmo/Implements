local Util = require("ebe.util")

local Memory = {}
Memory.__index = Memory

function Memory.new(opts)
  opts = opts or {}
  return setmetatable({
    entries = {},
    order = {},
    capacity = tonumber(opts.capacity) or 128,
    decay_per_hour = tonumber(opts.decay_per_hour) or 0.985,
    min_confidence = tonumber(opts.min_confidence) or 0.08,
  }, Memory)
end

function Memory:has(id)
  return self.entries[id] ~= nil
end

function Memory:add(observation, tick)
  if self.entries[observation.id] then return false end

  local entry = {
    id = observation.id,
    observation = Util.deepcopy(observation),
    confidence = Util.clamp(observation.confidence or 0.5),
    encoded_at = tonumber(tick) or 0,
    last_updated = tonumber(tick) or 0,
  }
  self.entries[entry.id] = entry
  self.order[#self.order + 1] = entry.id
  self:_trim()
  return true
end

function Memory:_trim()
  while #self.order > self.capacity do
    local weakest_i = 1
    local weakest_score = math.huge
    for i, id in ipairs(self.order) do
      local e = self.entries[id]
      local score = (e and e.confidence or 0) + i * 1e-9
      if score < weakest_score then
        weakest_score = score
        weakest_i = i
      end
    end
    local id = table.remove(self.order, weakest_i)
    self.entries[id] = nil
  end
end

function Memory:advance(hours, tick)
  hours = math.max(0, tonumber(hours) or 0)
  local factor = self.decay_per_hour ^ hours
  local new_order = {}
  for _, id in ipairs(self.order) do
    local e = self.entries[id]
    if e then
      e.confidence = Util.clamp(e.confidence * factor)
      e.last_updated = tonumber(tick) or e.last_updated
      if e.confidence >= self.min_confidence then
        new_order[#new_order + 1] = id
      else
        self.entries[id] = nil
      end
    end
  end
  self.order = new_order
end

function Memory:all()
  local out = {}
  for _, id in ipairs(self.order) do
    if self.entries[id] then out[#out + 1] = Util.deepcopy(self.entries[id]) end
  end
  return out
end

function Memory:snapshot()
  return {
    entries = Util.deepcopy(self.entries),
    order = Util.deepcopy(self.order),
    capacity = self.capacity,
    decay_per_hour = self.decay_per_hour,
    min_confidence = self.min_confidence,
  }
end

function Memory.restore(data)
  local m = Memory.new(data or {})
  m.entries = Util.deepcopy((data or {}).entries or {})
  m.order = Util.deepcopy((data or {}).order or {})
  return m
end

return Memory
