local EventBus = {}
EventBus.__index = EventBus

function EventBus.new()
  return setmetatable({ _listeners = {} }, EventBus)
end

function EventBus:on(event_type, handler)
  assert(type(handler) == "function", "handler must be a function")
  local list = self._listeners[event_type]
  if not list then
    list = {}
    self._listeners[event_type] = list
  end
  list[#list + 1] = handler
  local active = true
  return function()
    if not active then return false end
    active = false
    for i = #list, 1, -1 do
      if list[i] == handler then
        table.remove(list, i)
        return true
      end
    end
    return false
  end
end

local function emit_list(list, event)
  if not list then return end
  local snapshot = {}
  for i = 1, #list do snapshot[i] = list[i] end
  for i = 1, #snapshot do snapshot[i](event) end
end

function EventBus:emit(event)
  emit_list(self._listeners[event.type], event)
  emit_list(self._listeners["*"], event)
end

function EventBus:clear()
  self._listeners = {}
end

return EventBus
