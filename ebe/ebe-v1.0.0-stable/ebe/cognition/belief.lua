local Util = require("ebe.util")
local Observation = require("ebe.cognition.observation")

local Belief = {}

local function source_trust(agent, obs)
  if obs.evidence == "direct_local" then return 1.0 end
  local source = obs.source_agent_id
  if source and agent and agent.trust and agent.trust[source] ~= nil then
    return Util.clamp(agent.trust[source])
  end
  return 0.72
end

function Belief.rebuild(memory, agent)
  local grouped = {}

  for _, entry in ipairs(memory:all()) do
    local obs = entry.observation
    local trust = source_trust(agent, obs)

    for _, claim in ipairs(Observation.claims(obs)) do
      local bucket = grouped[claim.key]
      if not bucket then
        bucket = { key = claim.key, options = {}, evidence_count = 0 }
        grouped[claim.key] = bucket
      end

      local vk = Util.value_key(claim.value)
      local option = bucket.options[vk]
      if not option then
        option = {
          value = Util.deepcopy(claim.value),
          score = 0,
          sources = {},
          source_agents = {},
          _source_agent_set = {},
          origin_observation_ids = {},
          _origin_set = {},
          direct_sources = 0,
        }
        bucket.options[vk] = option
      end

      local weight = Util.clamp(entry.confidence) * trust
      option.score = option.score + weight
      option.sources[#option.sources + 1] = obs.id

      local source_identity = obs.source_agent_id
      if source_identity == nil and obs.evidence == "direct_local" then
        source_identity = obs.observer_id or ("direct:" .. tostring(obs.id))
      end
      if source_identity ~= nil and not option._source_agent_set[source_identity] then
        option._source_agent_set[source_identity] = true
        option.source_agents[#option.source_agents + 1] = source_identity
      end

      local provenance = obs.provenance or {}
      local roots = provenance.origin_observation_ids
      if type(roots) ~= "table" or #roots == 0 then
        if obs.evidence ~= "direct_local" and obs.source_agent_id ~= nil then
          -- Legacy v0.3 observations may not carry explicit lineage.
          -- Repeated reports from the same sender must still count as one
          -- corroboration source rather than inventing new roots per message id.
          roots = { "legacy-source:" .. tostring(obs.source_agent_id) }
        else
          roots = { obs.id }
        end
      end
      for _, root_id in ipairs(roots) do
        if not option._origin_set[root_id] then
          option._origin_set[root_id] = true
          option.origin_observation_ids[#option.origin_observation_ids + 1] = root_id
        end
      end
      table.sort(option.origin_observation_ids, function(a,b)
        return tostring(a) < tostring(b)
      end)

      if obs.evidence == "direct_local" then
        option.direct_sources = option.direct_sources + 1
      end
      bucket.evidence_count = bucket.evidence_count + 1
    end
  end

  local beliefs = {}
  for _, key in ipairs(Util.sorted_keys(grouped)) do
    local bucket = grouped[key]
    local total = 0
    local best_key = nil
    local best_score = -1

    for vk, option in pairs(bucket.options) do
      total = total + option.score
      if option.score > best_score or
         (option.score == best_score and tostring(vk) < tostring(best_key)) then
        best_key = vk
        best_score = option.score
      end
    end

    local best = bucket.options[best_key]
    local agreement = total > 0 and (best_score / total) or 0
    local support = Util.clamp(best_score)
    local confidence = Util.clamp(agreement * support)

    for _, option in pairs(bucket.options) do
      option._source_agent_set = nil
      option._origin_set = nil
    end

    beliefs[key] = {
      key = key,
      value = Util.deepcopy(best.value),
      confidence = Util.round(confidence, 6),
      agreement = Util.round(agreement, 6),
      support = Util.round(best_score, 6),
      evidence_count = bucket.evidence_count,
      source_count = #best.origin_observation_ids,
      reporter_count = #best.source_agents,
      direct_sources = best.direct_sources,
      sources = Util.deepcopy(best.sources),
      source_agents = Util.deepcopy(best.source_agents),
      origin_observation_ids = Util.deepcopy(best.origin_observation_ids),
      alternatives = Util.deepcopy(bucket.options),
    }
  end

  return beliefs
end

return Belief
