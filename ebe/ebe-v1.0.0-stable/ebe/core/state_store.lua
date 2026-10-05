local util = require("ebe.core.util")
local StateStore = {}
StateStore.__index = StateStore

function StateStore.new()
  return setmetatable({ _values = {} }, StateStore)
end

function StateStore:get(key, fallback)
  local value = self._values[key]
  if value == nil then return fallback end
  return value
end

function StateStore:has(key)
  return self._values[key] ~= nil
end

function StateStore:set(key, value)
  local previous = self._values[key]
  self._values[key] = value
  return { target = key, previous = previous, value = value }
end

function StateStore:update(key, updater, fallback)
  local previous = self:get(key, fallback)
  local value = updater(previous)
  self._values[key] = value
  return { target = key, previous = previous, value = value }
end

function StateStore:entries()
  local out = {}
  for k, v in pairs(self._values) do out[#out + 1] = { k, v } end
  return out
end

function StateStore:snapshot()
  return util.deep_copy(self._values)
end

function StateStore:restore(data)
  self._values = util.deep_copy(data or {})
end

function StateStore:clear()
  self._values = {}
end

return StateStore
