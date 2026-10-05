local Util = require("ebe.util")

local Interpretation = {}

local THREAT_VALUE = {
  quiet = 0.10,
  active = 0.38,
  tense = 0.72,
  volatile = 0.96,
  secure = 0.08,
  stable = 0.22,
  pressured = 0.68,
  fragile = 0.90,
}

function Interpretation.rebuild(beliefs, agent)
  local result = {}
  local sensitivity = tonumber(((agent or {}).biases or {}).threat_sensitivity) or 1.0
  local skepticism = tonumber(((agent or {}).biases or {}).skepticism) or 0.0

  for _, key in ipairs(Util.sorted_keys(beliefs or {})) do
    local b = beliefs[key]
    local base_threat = THREAT_VALUE[b.value] or 0
    local threat = Util.clamp(base_threat * sensitivity * (1 - skepticism * 0.25))
    local salience = Util.clamp((b.confidence or 0) * (0.45 + threat * 0.55))

    result[#result + 1] = {
      claim_key = key,
      value = Util.deepcopy(b.value),
      confidence = b.confidence,
      threat = Util.round(threat, 6),
      salience = Util.round(salience, 6),
      stance = threat >= 0.75 and "danger"
        or threat >= 0.45 and "caution"
        or "ordinary",
    }
  end

  table.sort(result, function(a, b)
    if a.salience == b.salience then return a.claim_key < b.claim_key end
    return a.salience > b.salience
  end)

  return result
end

return Interpretation
