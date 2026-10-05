local Util = require("ebe.util")

local Policy = {}

local VALID_ACTION = {
  publish=true,
  hold=true,
  suppress=true,
}

local DEFAULT = {
  default_action = "publish",
  default_priority = 0.0,
  default_delay_add = 0.0,
  default_delay_multiplier = 1.0,
  default_confidence_multiplier = 1.0,
  policy_log_capacity = 256,
  agenda = {},
  rules = {},
}

local function clamp_priority(v)
  return Util.clamp(tonumber(v) or 0, -1, 1)
end

local function normalize_action(v)
  if VALID_ACTION[v] then return v end
  return "publish"
end

local function normalize_match(m)
  m = Util.deepcopy(m or {})
  if m.min_confidence ~= nil then m.min_confidence = Util.clamp(tonumber(m.min_confidence) or 0) end
  if m.max_confidence ~= nil then m.max_confidence = Util.clamp(tonumber(m.max_confidence) or 1) end
  if m.min_roots ~= nil then m.min_roots = math.max(0, math.floor(tonumber(m.min_roots) or 0)) end
  if m.max_roots ~= nil then m.max_roots = math.max(0, math.floor(tonumber(m.max_roots) or 0)) end
  return m
end

local function normalize_rule(raw, i)
  raw = raw or {}
  return {
    id = tostring(raw.id or ("rule_"..tostring(i))),
    match = normalize_match(raw.match),
    action = normalize_action(raw.action or ((raw.effect or {}).action)),
    priority = clamp_priority(raw.priority or ((raw.effect or {}).priority)),
    delay_add = math.max(0, tonumber(raw.delay_add or ((raw.effect or {}).delay_add)) or 0),
    delay_multiplier = math.max(0, tonumber(raw.delay_multiplier or ((raw.effect or {}).delay_multiplier)) or 1),
    hold_delay = math.max(0, tonumber(raw.hold_delay or ((raw.effect or {}).hold_delay)) or 0),
    confidence_multiplier = Util.clamp(
      tonumber(raw.confidence_multiplier or ((raw.effect or {}).confidence_multiplier)) or 1,
      0, 1
    ),
    tag = raw.tag or ((raw.effect or {}).tag),
  }
end

local function normalize_agenda(src)
  local out = {}
  if type(src) ~= "table" then return out end
  if #src > 0 then
    for _,entry in ipairs(src) do
      if type(entry)=="table" and type(entry.prefix)=="string" and entry.prefix~="" then
        out[#out+1] = {
          prefix=entry.prefix,
          priority=clamp_priority(entry.priority),
        }
      end
    end
  else
    for _,prefix in ipairs(Util.sorted_keys(src)) do
      if type(prefix)=="string" and prefix~="" then
        out[#out+1] = {
          prefix=prefix,
          priority=clamp_priority(src[prefix]),
        }
      end
    end
  end
  table.sort(out,function(a,b)
    if #a.prefix ~= #b.prefix then return #a.prefix > #b.prefix end
    return a.prefix < b.prefix
  end)
  return out
end

function Policy.normalize(spec)
  spec = spec or {}
  local out = Util.deepcopy(DEFAULT)
  out.default_action = normalize_action(spec.default_action or DEFAULT.default_action)
  out.default_priority = clamp_priority(spec.default_priority or DEFAULT.default_priority)
  out.default_delay_add = math.max(0, tonumber(spec.default_delay_add) or DEFAULT.default_delay_add)
  out.default_delay_multiplier = math.max(0, tonumber(spec.default_delay_multiplier) or DEFAULT.default_delay_multiplier)
  out.default_confidence_multiplier = Util.clamp(
    tonumber(spec.default_confidence_multiplier) or DEFAULT.default_confidence_multiplier,
    0, 1
  )
  out.policy_log_capacity = math.max(1, math.floor(
    tonumber(spec.policy_log_capacity) or DEFAULT.policy_log_capacity
  ))
  out.agenda = normalize_agenda(spec.agenda)
  out.rules = {}
  for i,raw in ipairs(spec.rules or {}) do
    out.rules[#out.rules+1] = normalize_rule(raw,i)
  end
  return out
end

local function roots_count(report)
  local lineage = (report or {}).lineage or {}
  local roots = lineage.origin_observation_ids or
    (((report or {}).provenance or {}).origin_observation_ids) or {}
  return type(roots)=="table" and #roots or 0
end

local function starts_with(s,prefix)
  return type(s)=="string" and type(prefix)=="string" and s:sub(1,#prefix)==prefix
end

local function match_value(actual, expected)
  if expected == nil then return true end
  if type(expected)=="table" and #expected>0 then
    for _,v in ipairs(expected) do
      if Util.value_key(actual)==Util.value_key(v) then return true end
    end
    return false
  end
  return Util.value_key(actual)==Util.value_key(expected)
end

local function matches(m, report, context)
  local claim = (report or {}).claim or {}
  context = context or {}

  if m.key ~= nil and claim.key ~= m.key then return false end
  if m.key_prefix ~= nil and not starts_with(claim.key,m.key_prefix) then return false end
  if m.value ~= nil and not match_value(claim.value,m.value) then return false end
  if m.sender_type ~= nil and report.sender_type ~= m.sender_type then return false end
  if m.sender_id ~= nil and report.sender_id ~= m.sender_id then return false end
  if m.target_type ~= nil and context.target_type ~= m.target_type then return false end
  if m.target_id ~= nil and context.target_id ~= m.target_id then return false end

  local confidence = tonumber(report.confidence) or tonumber(report.source_confidence) or 0
  if m.min_confidence ~= nil and confidence < m.min_confidence then return false end
  if m.max_confidence ~= nil and confidence > m.max_confidence then return false end

  local roots = roots_count(report)
  if m.min_roots ~= nil and roots < m.min_roots then return false end
  if m.max_roots ~= nil and roots > m.max_roots then return false end

  return true
end

local function agenda_priority(policy, claim_key)
  for _,entry in ipairs(policy.agenda or {}) do
    if starts_with(claim_key or "",entry.prefix) then
      return entry.priority, entry.prefix
    end
  end
  return 0,nil
end

function Policy.evaluate(policy, report, context)
  policy = Policy.normalize(policy)
  context = context or {}
  local claim = (report or {}).claim or {}

  local agenda_delta,agenda_prefix = agenda_priority(policy,claim.key)
  local result = {
    action = policy.default_action,
    priority = clamp_priority(policy.default_priority + agenda_delta),
    delay_add = policy.default_delay_add,
    delay_multiplier = policy.default_delay_multiplier,
    confidence_multiplier = policy.default_confidence_multiplier,
    matched_rule_id = nil,
    agenda_prefix = agenda_prefix,
    tag = nil,
  }

  for _,rule in ipairs(policy.rules or {}) do
    if matches(rule.match,report,context) then
      result.action = rule.action
      result.priority = clamp_priority(result.priority + rule.priority)
      result.delay_add = result.delay_add + rule.delay_add
      result.delay_multiplier = result.delay_multiplier * rule.delay_multiplier
      result.confidence_multiplier = Util.clamp(
        result.confidence_multiplier * rule.confidence_multiplier, 0, 1
      )
      if rule.action=="hold" then
        result.delay_add = result.delay_add + rule.hold_delay
      end
      result.matched_rule_id = rule.id
      result.tag = rule.tag
      break
    end
  end

  -- Priority is scheduling preference only. It never changes evidence roots.
  -- +1 priority halves normal delay; -1 increases it by 50%.
  result.priority_delay_multiplier = 1 - (0.5 * result.priority)
  result.effective_delay_multiplier = result.delay_multiplier * result.priority_delay_multiplier
  return result
end

function Policy.defaults()
  return Policy.normalize({})
end

return Policy
