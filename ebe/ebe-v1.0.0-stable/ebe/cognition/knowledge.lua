local Util = require("ebe.util")

local Knowledge = {}

function Knowledge.rebuild(beliefs, opts)
  opts = opts or {}
  local direct_threshold = tonumber(opts.direct_threshold) or 0.55
  local corroborated_threshold = tonumber(opts.corroborated_threshold) or 0.62
  local facts = {}

  for _, key in ipairs(Util.sorted_keys(beliefs or {})) do
    local b = beliefs[key]
    local direct = (b.direct_sources or 0) > 0
    local corroborated = (b.source_count or 0) >= 2

    if (direct and b.confidence >= direct_threshold) or
       (corroborated and b.confidence >= corroborated_threshold) then
      facts[key] = {
        key = key,
        value = Util.deepcopy(b.value),
        confidence = b.confidence,
        basis = direct and "direct_evidence" or "corroborated_reports",
        source_count = b.source_count,
        sources = Util.deepcopy(b.sources),
      }
    end
  end

  return facts
end

return Knowledge
