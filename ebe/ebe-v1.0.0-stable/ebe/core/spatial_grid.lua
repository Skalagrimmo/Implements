local SpatialGrid = {}
SpatialGrid.__index = SpatialGrid

local function default_position(item)
  return item.x, item.y
end

function SpatialGrid.new(opts)
  opts = opts or {}
  local cell_size = opts.cell_size or opts.cellSize or 100
  assert(type(cell_size) == "number" and cell_size > 0, "cell_size must be a positive number")
  return setmetatable({
    _cell_size = cell_size,
    _get_position = opts.get_position or opts.getPosition or default_position,
    _cells = {},
    _item_cell = setmetatable({}, { __mode = "k" }),
    _item_count = 0,
  }, SpatialGrid)
end

function SpatialGrid:_coords(x, y)
  return math.floor(x / self._cell_size), math.floor(y / self._cell_size)
end

function SpatialGrid:_key(cx, cy)
  return tostring(cx) .. "," .. tostring(cy)
end

function SpatialGrid:insert(item)
  local x, y = self._get_position(item)
  assert(type(x) == "number" and type(y) == "number", "item position must contain numeric x/y")
  if self._item_cell[item] then self:remove(item) end
  local cx, cy = self:_coords(x, y)
  local key = self:_key(cx, cy)
  local bucket = self._cells[key]
  if not bucket then bucket = {}; self._cells[key] = bucket end
  bucket[item] = true
  self._item_cell[item] = key
  self._item_count = self._item_count + 1
end

function SpatialGrid:remove(item)
  local key = self._item_cell[item]
  if not key then return false end
  local bucket = self._cells[key]
  if bucket then
    bucket[item] = nil
    if next(bucket) == nil then self._cells[key] = nil end
  end
  self._item_cell[item] = nil
  self._item_count = math.max(0, self._item_count - 1)
  return true
end

function SpatialGrid:update(item)
  self:remove(item)
  self:insert(item)
end

function SpatialGrid:clear()
  self._cells = {}
  self._item_cell = setmetatable({}, { __mode = "k" })
  self._item_count = 0
end

function SpatialGrid:rebuild(items)
  self:clear()
  for i = 1, #(items or {}) do self:insert(items[i]) end
  return self
end

function SpatialGrid:query_radius(x, y, radius)
  local min_cx, min_cy = self:_coords(x - radius, y - radius)
  local max_cx, max_cy = self:_coords(x + radius, y + radius)
  local result = {}
  for cx = min_cx, max_cx do
    for cy = min_cy, max_cy do
      local bucket = self._cells[self:_key(cx, cy)]
      if bucket then
        for item in pairs(bucket) do result[#result + 1] = item end
      end
    end
  end
  return result
end

function SpatialGrid:cell_count()
  local n = 0
  for _ in pairs(self._cells) do n = n + 1 end
  return n
end

function SpatialGrid:item_count()
  return self._item_count
end

return SpatialGrid
