local Util = require("ebe.util")

local Lineage = {}

local function unique_sorted(list)
  local seen, out = {}, {}
  for _, v in ipairs(list or {}) do
    if v ~= nil and not seen[v] then
      seen[v] = true
      out[#out + 1] = v
    end
  end
  table.sort(out, function(a,b) return tostring(a) < tostring(b) end)
  return out
end

function Lineage.from_observation(obs)
  local provenance = obs.provenance or {}
  local roots = provenance.origin_observation_ids
  if type(roots) ~= "table" or #roots == 0 then
    roots = { obs.id }
  end
  return {
    origin_observation_ids = unique_sorted(roots),
    route = Util.deepcopy(provenance.route or {}),
    hop_count = tonumber(provenance.hop_count) or 0,
  }
end

function Lineage.from_belief(belief)
  local roots = belief.origin_observation_ids or belief.sources or {}
  return {
    origin_observation_ids = unique_sorted(roots),
    route = {},
    hop_count = 0,
  }
end

function Lineage.extend(lineage, hop)
  lineage = lineage or {}
  local out = {
    origin_observation_ids = unique_sorted(lineage.origin_observation_ids or {}),
    route = Util.deepcopy(lineage.route or {}),
    hop_count = (tonumber(lineage.hop_count) or 0) + 1,
  }
  out.route[#out.route + 1] = Util.deepcopy(hop or {})
  return out
end

function Lineage.merge(...)
  local roots, route, hop_count = {}, {}, 0
  for i = 1, select("#", ...) do
    local lin = select(i, ...)
    if lin then
      for _, id in ipairs(lin.origin_observation_ids or {}) do roots[#roots+1] = id end
      for _, hop in ipairs(lin.route or {}) do route[#route+1] = Util.deepcopy(hop) end
      hop_count = math.max(hop_count, tonumber(lin.hop_count) or 0)
    end
  end
  return {
    origin_observation_ids = unique_sorted(roots),
    route = route,
    hop_count = hop_count,
  }
end

return Lineage
