local Util = require("ebe.util")

local EventBus = {}
EventBus.__index = EventBus

function EventBus.new(opts)
  opts = opts or {}
  return setmetatable({
    subscribers = {},
    history = {},
    history_limit = tonumber(opts.history_limit) or 512,
    sequence = 0,
  }, EventBus)
end

function EventBus:subscribe(topic, fn, priority)
  assert(type(topic) == "string", "topic must be a string")
  assert(type(fn) == "function", "subscriber must be a function")
  self.sequence = self.sequence + 1
  local item = {
    fn = fn,
    priority = tonumber(priority) or 0,
    sequence = self.sequence,
  }
  local list = self.subscribers[topic] or {}
  list[#list + 1] = item
  table.sort(list, function(a, b)
    if a.priority == b.priority then return a.sequence < b.sequence end
    return a.priority > b.priority
  end)
  self.subscribers[topic] = list

  return function()
    local current = self.subscribers[topic] or {}
    for i = #current, 1, -1 do
      if current[i] == item then table.remove(current, i) end
    end
  end
end

function EventBus:_dispatch(topic, event)
  for _, item in ipairs(self.subscribers[topic] or {}) do
    item.fn(event, topic)
  end
end

function EventBus:emit(topic, event)
  assert(type(topic) == "string", "topic must be a string")
  local record = {
    topic = topic,
    event = Util.deepcopy(event),
  }
  self.history[#self.history + 1] = record
  while #self.history > self.history_limit do table.remove(self.history, 1) end

  self:_dispatch(topic, event)
  if topic ~= "*" then self:_dispatch("*", event) end
end

function EventBus:snapshot()
  return Util.deepcopy(self.history)
end

return EventBus
