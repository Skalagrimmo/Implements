local M = {}

function M.clamp01(v)
  if v < 0 then return 0 end
  if v > 1 then return 1 end
  return v
end

function M.is_finite(v)
  return type(v) == "number" and v == v and v ~= math.huge and v ~= -math.huge
end

function M.shallow_copy(t)
  local out = {}
  if t then for k, v in pairs(t) do out[k] = v end end
  return out
end

function M.deep_copy(value, seen)
  if type(value) ~= "table" then return value end
  seen = seen or {}
  if seen[value] then return seen[value] end
  local out = {}
  seen[value] = out
  for k, v in pairs(value) do
    out[M.deep_copy(k, seen)] = M.deep_copy(v, seen)
  end
  return out
end

function M.array_copy(a)
  local out = {}
  if a then for i = 1, #a do out[i] = a[i] end end
  return out
end

function M.round(v)
  return math.floor(v + 0.5)
end

return M
