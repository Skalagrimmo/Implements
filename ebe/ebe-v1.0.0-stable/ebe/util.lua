local Util = {}

function Util.clamp(v, lo, hi)
  lo = lo or 0
  hi = hi or 1
  if v < lo then return lo end
  if v > hi then return hi end
  return v
end

function Util.round(v, digits)
  digits = digits or 6
  local p = 10 ^ digits
  if v >= 0 then
    return math.floor(v * p + 0.5) / p
  end
  return math.ceil(v * p - 0.5) / p
end

function Util.deepcopy(value, seen)
  if type(value) ~= "table" then return value end
  seen = seen or {}
  if seen[value] then return seen[value] end
  local out = {}
  seen[value] = out
  for k, v in pairs(value) do
    out[Util.deepcopy(k, seen)] = Util.deepcopy(v, seen)
  end
  return out
end

function Util.sorted_keys(t)
  local keys = {}
  for k in pairs(t or {}) do keys[#keys + 1] = k end
  table.sort(keys, function(a, b)
    local ta, tb = type(a), type(b)
    if ta == tb then return tostring(a) < tostring(b) end
    return ta < tb
  end)
  return keys
end

local function stable_scalar(v)
  local tv = type(v)
  if tv == "nil" then return "nil" end
  if tv == "boolean" then return v and "true" or "false" end
  if tv == "number" then return string.format("%.12g", v) end
  if tv == "string" then return string.format("%q", v) end
  return "<" .. tv .. ":" .. tostring(v) .. ">"
end

function Util.canonical(value, seen)
  if type(value) ~= "table" then return stable_scalar(value) end
  seen = seen or {}
  if seen[value] then return "<cycle>" end
  seen[value] = true

  local n = #value
  local is_array = true
  local count = 0
  for k in pairs(value) do
    count = count + 1
    if type(k) ~= "number" or k < 1 or k % 1 ~= 0 then
      is_array = false
      break
    end
  end
  if is_array and count ~= n then is_array = false end

  local parts = {}
  if is_array then
    for i = 1, n do
      parts[#parts + 1] = Util.canonical(value[i], seen)
    end
    seen[value] = nil
    return "[" .. table.concat(parts, ",") .. "]"
  end

  for _, k in ipairs(Util.sorted_keys(value)) do
    parts[#parts + 1] = stable_scalar(k) .. ":" .. Util.canonical(value[k], seen)
  end
  seen[value] = nil
  return "{" .. table.concat(parts, ",") .. "}"
end

-- Portable deterministic rolling hash; no bit library required.
function Util.stable_hash(value)
  local s = type(value) == "string" and value or Util.canonical(value)
  local mod = 2147483647
  local h = 146959
  for i = 1, #s do
    h = (h * 131 + string.byte(s, i)) % mod
  end
  return h
end

function Util.roll01(...)
  local parts = {}
  for i = 1, select("#", ...) do
    parts[i] = tostring(select(i, ...))
  end
  return (Util.stable_hash(table.concat(parts, "|")) % 1000000) / 1000000
end

function Util.value_key(v)
  return Util.canonical(v)
end

function Util.same_sector(a, b)
  if type(a) ~= "table" or type(b) ~= "table" then return false end
  return a[1] == b[1] and a[2] == b[2]
end

function Util.manhattan(a, b)
  if type(a) ~= "table" or type(b) ~= "table" then return math.huge end
  return math.abs((a[1] or 0) - (b[1] or 0)) + math.abs((a[2] or 0) - (b[2] or 0))
end

function Util.list_contains(list, value)
  for _, v in ipairs(list or {}) do
    if v == value then return true end
  end
  return false
end

return Util
