local RingBuffer = {}
RingBuffer.__index = RingBuffer

function RingBuffer.new(capacity)
  if capacity == nil then capacity = 2000 end
  local unlimited = capacity == math.huge or capacity == 0
  if not unlimited then
    assert(type(capacity) == "number" and capacity > 0 and math.floor(capacity) == capacity,
      "capacity must be a positive integer, 0, or math.huge")
  end
  return setmetatable({
    _capacity = unlimited and math.huge or capacity,
    _buffer = {},
    _start = 1,
    _length = 0,
  }, RingBuffer)
end

function RingBuffer:push(item)
  if self._capacity == math.huge then
    self._buffer[#self._buffer + 1] = item
    self._length = #self._buffer
    return item
  end
  local index = ((self._start - 1 + self._length) % self._capacity) + 1
  self._buffer[index] = item
  if self._length < self._capacity then
    self._length = self._length + 1
  else
    self._start = (self._start % self._capacity) + 1
  end
  return item
end

function RingBuffer:length()
  return self._length
end

function RingBuffer:capacity()
  return self._capacity
end

function RingBuffer:unlimited()
  return self._capacity == math.huge
end

function RingBuffer:to_array()
  if self._capacity == math.huge then
    local out = {}
    for i = 1, #self._buffer do out[i] = self._buffer[i] end
    return out
  end
  local out = {}
  for i = 0, self._length - 1 do
    out[#out + 1] = self._buffer[((self._start - 1 + i) % self._capacity) + 1]
  end
  return out
end

function RingBuffer:clear()
  self._buffer = {}
  self._start = 1
  self._length = 0
end

function RingBuffer:restore(items)
  self:clear()
  items = items or {}
  for i = 1, #items do self:push(items[i]) end
end

return RingBuffer
