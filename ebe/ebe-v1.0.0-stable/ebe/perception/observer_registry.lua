local ObserverRegistry = {}
ObserverRegistry.__index = ObserverRegistry

function ObserverRegistry.new(observers)
  local self = setmetatable({ _by_id = {}, _size = 0 }, ObserverRegistry)
  self:rebuild(observers or {})
  return self
end

function ObserverRegistry:rebuild(observers)
  self._by_id = {}
  self._size = 0
  for i = 1, #(observers or {}) do
    local observer = observers[i]
    if observer and observer.id ~= nil then
      if self._by_id[observer.id] == nil then self._size = self._size + 1 end
      self._by_id[observer.id] = observer
    end
  end
  return self
end

function ObserverRegistry:get(id)
  return self._by_id[id]
end

function ObserverRegistry:has(id)
  return self._by_id[id] ~= nil
end

function ObserverRegistry:clear()
  self._by_id = {}
  self._size = 0
end

function ObserverRegistry:size()
  return self._size
end

return ObserverRegistry
