local Util = require("ebe.util")

local Observation = {}

local BASE_CONFIDENCE = {
  direct_local = 0.96,
  transmitted = 0.72,
  rumor = 0.62,
  inferred = 0.52,
}

function Observation.normalize(raw, opts)
  opts = opts or {}
  assert(type(raw) == "table", "observation must be a table")
  assert(raw.id or opts.id, "observation id is required")

  local evidence = raw.evidence or opts.evidence or "direct_local"
  local confidence = tonumber(raw.confidence or opts.confidence)
    or BASE_CONFIDENCE[evidence]
    or 0.50

  return {
    id = raw.id or opts.id,
    source_event_id = raw.source_event_id or opts.source_event_id,
    subject_type = raw.subject_type or opts.subject_type,
    subject_id = raw.subject_id or opts.subject_id,
    sector = Util.deepcopy(raw.sector or opts.sector),
    fact = Util.deepcopy(raw.fact or opts.fact or {}),
    evidence = evidence,
    confidence = Util.clamp(confidence),
    observed_at = tonumber(raw.observed_at or opts.observed_at) or 0,
    observer_id = raw.observer_id or opts.observer_id,
    source_agent_id = raw.source_agent_id or opts.source_agent_id,
    provenance = Util.deepcopy(raw.provenance or opts.provenance or {}),
    delivery_state = raw.delivery_state or opts.delivery_state or "delivered",
    knowledge_state = raw.knowledge_state or opts.knowledge_state or "unprocessed",
    revision = raw.revision or opts.revision,
  }
end

function Observation.claims(obs)
  local claims = {}
  local fact = obs.fact or {}

  if type(fact.claims) == "table" then
    for _, claim in ipairs(fact.claims) do
      claims[#claims + 1] = {
        key = claim.key,
        value = Util.deepcopy(claim.value),
        prior = Util.deepcopy(claim.prior),
        confidence = Util.clamp((claim.confidence or 1) * (obs.confidence or 1)),
      }
    end
    return claims
  end

  if type(fact.changes) == "table" then
    for _, field in ipairs(Util.sorted_keys(fact.changes)) do
      local change = fact.changes[field]
      claims[#claims + 1] = {
        key = table.concat({
          tostring(obs.subject_type or "subject"),
          tostring(obs.subject_id or "unknown"),
          tostring(field),
        }, ":"),
        value = Util.deepcopy(change.after),
        prior = Util.deepcopy(change.before),
        confidence = obs.confidence,
      }
    end
    return claims
  end

  claims[#claims + 1] = {
    key = table.concat({
      tostring(obs.subject_type or "event"),
      tostring(obs.subject_id or obs.source_event_id or "unknown"),
      tostring(fact.event_type or "observed"),
    }, ":"),
    value = Util.deepcopy(fact.value ~= nil and fact.value or true),
    prior = nil,
    confidence = obs.confidence,
  }
  return claims
end

function Observation.from_claim(id, claim, opts)
  opts = opts or {}
  return Observation.normalize({
    id = id,
    source_event_id = opts.source_event_id,
    subject_type = opts.subject_type or "claim",
    subject_id = opts.subject_id or claim.key,
    sector = opts.sector,
    evidence = opts.evidence or "transmitted",
    confidence = opts.confidence,
    observed_at = opts.observed_at,
    observer_id = opts.observer_id,
    source_agent_id = opts.source_agent_id,
    provenance = opts.provenance,
    fact = {
      claims = {
        {
          key = claim.key,
          value = Util.deepcopy(claim.value),
          prior = Util.deepcopy(claim.prior),
          confidence = claim.confidence or 1,
        }
      }
    }
  })
end

return Observation
