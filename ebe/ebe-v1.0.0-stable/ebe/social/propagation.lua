local Util = require("ebe.util")
local Observation = require("ebe.cognition.observation")
local Lineage = require("ebe.social.source_lineage")

local Propagation = {}
Propagation.__index = Propagation

local STATUS_LADDERS = {
  front = { "quiet", "active", "tense", "volatile" },
  territory = { "secure", "stable", "pressured", "fragile" },
}

local function distorted_status(key, value, roll)
  if type(value) ~= "string" then return value end
  local ladder = nil
  if string.find(key, "^front:") and string.find(key, ":status$") then
    ladder = STATUS_LADDERS.front
  elseif string.find(key, "^territory:") and string.find(key, ":status$") then
    ladder = STATUS_LADDERS.territory
  end
  if not ladder then return value end

  local index = nil
  for i, v in ipairs(ladder) do
    if v == value then index = i break end
  end
  if not index then return value end

  local delta = roll < 0.5 and -1 or 1
  local new_index = math.max(1, math.min(#ladder, index + delta))
  return ladder[new_index]
end

local function distort_claim(claim, probability, token)
  local roll = Util.roll01("distort", token, claim.key, Util.value_key(claim.value))
  local out = Util.deepcopy(claim)
  out.distorted = false

  if roll >= probability then return out end

  local value = out.value
  if type(value) == "number" then
    local sign = Util.roll01("sign", token, claim.key) < 0.5 and -1 or 1
    out.value = Util.round(value * (1 + sign * 0.10), 4)
    out.distorted = true
  elseif type(value) == "string" then
    local shifted = distorted_status(claim.key, value, Util.roll01("status", token))
    if shifted ~= value then
      out.value = shifted
      out.distorted = true
    end
  end

  return out
end

function Propagation.new(opts)
  opts = opts or {}
  return setmetatable({
    links = {},
    queue = {},
    sequence = 0,
    default_delay = tonumber(opts.default_delay) or 1,
    default_trust = tonumber(opts.default_trust) or 0.72,
    default_distortion = tonumber(opts.default_distortion) or 0.08,
  }, Propagation)
end

function Propagation:_key(a, b)
  return tostring(a) .. "->" .. tostring(b)
end

function Propagation:connect(a, b, opts)
  opts = opts or {}
  local link = {
    from = a,
    to = b,
    delay = tonumber(opts.delay) or self.default_delay,
    trust = Util.clamp(tonumber(opts.trust) or self.default_trust),
    distortion = Util.clamp(tonumber(opts.distortion) or self.default_distortion),
  }
  self.links[self:_key(a, b)] = link

  if opts.bidirectional then
    self:connect(b, a, {
      delay = opts.delay,
      trust = opts.reverse_trust or opts.trust,
      distortion = opts.reverse_distortion or opts.distortion,
      bidirectional = false,
    })
  end
end

function Propagation:get_link(a, b)
  return self.links[self:_key(a, b)]
end

function Propagation:queue_claim(runtime, sender_id, receiver_id, claim, opts)
  opts = opts or {}
  local link = self:get_link(sender_id, receiver_id)
  assert(link, "no propagation link from " .. tostring(sender_id) .. " to " .. tostring(receiver_id))

  local sender = assert(runtime.agents[sender_id], "unknown sender")
  local receiver = assert(runtime.agents[receiver_id], "unknown receiver")
  local receiver_trust = receiver.trust[sender_id]
  if receiver_trust == nil then receiver_trust = link.trust end

  self.sequence = self.sequence + 1
  local token = table.concat({
    tostring(runtime.seed),
    tostring(runtime.tick),
    tostring(sender_id),
    tostring(receiver_id),
    tostring(self.sequence),
  }, ":")

  local base_lineage = opts.lineage or {
    origin_observation_ids = Util.deepcopy((opts.provenance or {}).origin_observation_ids or {}),
    route = Util.deepcopy((opts.provenance or {}).route or {}),
    hop_count = tonumber((opts.provenance or {}).hop_count) or 0,
  }
  local lineage = Lineage.extend(base_lineage, {
    kind = "agent_to_agent",
    from = sender_id,
    to = receiver_id,
    at = runtime.tick,
  })

  local distorted = distort_claim(claim, link.distortion, token)
  local confidence = Util.clamp(
    (claim.confidence or 0.5) * link.trust * receiver_trust * 0.92
  )
  if distorted.distorted then confidence = confidence * 0.82 end

  local transmission = {
    id = "tx_" .. tostring(self.sequence),
    sender_id = sender_id,
    receiver_id = receiver_id,
    created_at = runtime.tick,
    deliver_at = runtime.tick + math.max(0, link.delay),
    claim = distorted,
    confidence = Util.round(confidence, 6),
    source_claim_key = claim.key,
    distortion_applied = distorted.distorted,
    sender_sector = Util.deepcopy(sender.sector),
    receiver_sector = Util.deepcopy(receiver.sector),
    lineage = Util.deepcopy(lineage),
    provenance = Util.deepcopy(opts.provenance or {}),
  }
  self.queue[#self.queue + 1] = transmission
  runtime.bus:emit("propagation.queued", Util.deepcopy(transmission))
  return Util.deepcopy(transmission)
end

function Propagation:advance(runtime)
  local pending = {}
  for _, tx in ipairs(self.queue) do
    if tx.deliver_at <= runtime.tick then
      local receiver = runtime.agents[tx.receiver_id]
      if receiver then
        local obs = Observation.from_claim(
          "rumor_" .. tx.id,
          tx.claim,
          {
            source_event_id = tx.id,
            subject_type = "rumor",
            subject_id = tx.source_claim_key,
            sector = Util.deepcopy(receiver.sector),
            evidence = "transmitted",
            confidence = tx.confidence,
            observed_at = runtime.tick,
            observer_id = tx.receiver_id,
            source_agent_id = tx.sender_id,
            provenance = {
              transmission_id = tx.id,
              source_agent_id = tx.sender_id,
              inherited = Util.deepcopy(tx.provenance),
              origin_observation_ids = Util.deepcopy((tx.lineage or {}).origin_observation_ids or {}),
              route = Util.deepcopy((tx.lineage or {}).route or {}),
              hop_count = tonumber((tx.lineage or {}).hop_count) or 0,
              distortion_applied = tx.distortion_applied,
            },
          }
        )
        runtime:_deliver_observation(tx.receiver_id, obs)
        runtime.bus:emit("propagation.delivered", {
          transmission = Util.deepcopy(tx),
          observation_id = obs.id,
        })
      end
    else
      pending[#pending + 1] = tx
    end
  end
  self.queue = pending
end

function Propagation:snapshot()
  return {
    links = Util.deepcopy(self.links),
    queue = Util.deepcopy(self.queue),
    sequence = self.sequence,
    default_delay = self.default_delay,
    default_trust = self.default_trust,
    default_distortion = self.default_distortion,
  }
end

function Propagation.restore(data)
  local p = Propagation.new(data or {})
  p.links = Util.deepcopy((data or {}).links or {})
  p.queue = Util.deepcopy((data or {}).queue or {})
  p.sequence = tonumber((data or {}).sequence) or 0
  return p
end

return Propagation
