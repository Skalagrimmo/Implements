local Util = require("ebe.util")
local Observation = require("ebe.cognition.observation")
local Institution = require("ebe.social.institution")
local Lineage = require("ebe.social.source_lineage")

local Ecology = {}
Ecology.__index = Ecology

function Ecology.new(opts)
  opts = opts or {}
  return setmetatable({
    institutions = {},
    queue = {},
    sequence = 0,
    routing_log = {},
    max_hops = tonumber(opts.max_hops) or 8,
  }, Ecology)
end

function Ecology:add_institution(spec)
  local inst = Institution.new(spec)
  assert(not self.institutions[inst.id], "duplicate institution id "..inst.id)
  self.institutions[inst.id] = inst
  return inst
end

function Ecology:subscribe(institution_id, target_id, opts)
  local inst = assert(self.institutions[institution_id], "unknown institution "..tostring(institution_id))
  inst:subscribe(target_id, opts)
end


local function route_has_institution(lineage, institution_id)
  for _, hop in ipairs((lineage or {}).route or {}) do
    if hop.kind=="institution" and hop.id==institution_id then return true end
  end
  return false
end

function Ecology:_enqueue(item)
  self.sequence = self.sequence + 1
  item.id = item.id or ("eco_"..tostring(self.sequence))
  self.queue[#self.queue+1] = item
  return item
end

function Ecology:_report_from_belief(runtime, sender_id, claim_key, opts)
  opts = opts or {}
  local agent = assert(runtime.agents[sender_id], "unknown sender")
  local belief = assert(agent.beliefs[claim_key], "sender has no belief "..tostring(claim_key))
  local lineage = Lineage.from_belief(belief)

  return {
    id = opts.id,
    claim = {
      key = claim_key,
      value = Util.deepcopy(belief.value),
      confidence = belief.confidence,
    },
    sender_type = "agent",
    sender_id = sender_id,
    created_at = runtime.tick,
    source_confidence = belief.confidence,
    lineage = lineage,
    provenance = {
      belief_sources = Util.deepcopy(belief.sources),
      origin_observation_ids = Util.deepcopy(lineage.origin_observation_ids),
    },
  }
end

function Ecology:submit_agent_report(runtime, sender_id, institution_id, claim_key, opts)
  opts = opts or {}
  local inst = assert(self.institutions[institution_id], "unknown institution")
  local report = self:_report_from_belief(runtime, sender_id, claim_key, opts)
  report.id = report.id or ("institution_report_"..tostring(self.sequence+1))
  report.institution_id = institution_id
  report.confidence = Util.clamp(report.source_confidence * (tonumber(opts.trust) or inst.policy.trust))
  report.deliver_at = runtime.tick + (tonumber(opts.delay) or inst.policy.receive_delay)
  report.provenance = report.provenance or {}
  if opts.route then report.provenance.ingress_route = Util.deepcopy(opts.route) end

  self:_enqueue({
    kind = "institution_receive",
    deliver_at = report.deliver_at,
    institution_id = institution_id,
    report = report,
  })

  runtime.bus:emit("institution.report_queued", Util.deepcopy(report))
  return Util.deepcopy(report)
end

function Ecology:submit_external_report(runtime, sender_type, sender_id, institution_id, spec, opts)
  opts = opts or {}
  spec = spec or {}
  local inst = assert(self.institutions[institution_id], "unknown institution")
  assert(type(spec.claim)=="table", "external report claim is required")
  assert(type(spec.claim.key)=="string" and spec.claim.key~="", "external report claim key is required")

  self.sequence = self.sequence + 1
  local source_confidence = Util.clamp(tonumber(spec.confidence) or tonumber(spec.source_confidence) or 0.5)
  local report = {
    id = spec.id or ("institution_external_"..tostring(self.sequence)),
    claim = Util.deepcopy(spec.claim),
    sender_type = sender_type or "external",
    sender_id = sender_id,
    created_at = runtime.tick,
    source_confidence = source_confidence,
    lineage = Util.deepcopy(spec.lineage or {
      origin_observation_ids = Util.deepcopy((spec.provenance or {}).origin_observation_ids or {}),
      route = Util.deepcopy((spec.provenance or {}).route or {}),
      hop_count = tonumber((spec.provenance or {}).hop_count) or 0,
    }),
    provenance = Util.deepcopy(spec.provenance or {}),
    institution_id = institution_id,
  }
  report.confidence = Util.clamp(source_confidence * (tonumber(opts.trust) or inst.policy.trust))
  report.deliver_at = runtime.tick + (tonumber(opts.delay) or inst.policy.receive_delay)
  if opts.route then report.provenance.ingress_route = Util.deepcopy(opts.route) end

  self:_enqueue({
    kind = "institution_receive",
    deliver_at = report.deliver_at,
    institution_id = institution_id,
    report = report,
  })

  runtime.bus:emit("institution.report_queued", Util.deepcopy(report))
  return Util.deepcopy(report)
end

function Ecology:_institution_distort(runtime, inst, report)
  local out = Util.deepcopy(report)
  local roll = Util.roll01("institution-distort", runtime.seed, inst.id, report.id)
  out.distorted = false

  if roll < Util.clamp(inst.policy.distortion) then
    local v = out.claim.value
    if type(v)=="number" then
      local sign = Util.roll01("institution-sign", inst.id, report.id) < 0.5 and -1 or 1
      out.claim.value = Util.round(v * (1 + sign*0.08), 4)
      out.distorted = true
    elseif type(v)=="string" then
      local ladders = {
        quiet={"quiet","active"},
        active={"quiet","active","tense"},
        tense={"active","tense","volatile"},
        volatile={"tense","volatile"},
        secure={"secure","stable"},
        stable={"secure","stable","pressured"},
        pressured={"stable","pressured","fragile"},
        fragile={"pressured","fragile"},
      }
      local options = ladders[v]
      if options then
        local idx = 1 + math.floor(Util.roll01("institution-status", inst.id, report.id) * #options)
        local shifted = options[math.min(idx,#options)]
        if shifted ~= v then
          out.claim.value = shifted
          out.distorted = true
        end
      end
    end
  end

  if out.distorted then out.confidence = out.confidence * 0.86 end
  return out
end

function Ecology:_broadcast(runtime, inst, report)
  if report.confidence < inst.policy.rebroadcast_min then return end
  if tonumber((report.lineage or {}).hop_count) >= self.max_hops then return end

  local transformed = self:_institution_distort(runtime, inst, report)
  transformed.lineage = Lineage.extend(transformed.lineage, {
    kind="institution", id=inst.id, institution_kind=inst.kind, at=runtime.tick,
  })

  for _, target_id in ipairs(Util.sorted_keys(inst.subscribers)) do
    local sub = inst.subscribers[target_id] or {}
    local base_delay = tonumber(sub.delay) or inst.policy.broadcast_delay
    local target_type = self.institutions[target_id] and "institution" or "agent"
    local decision = inst:evaluate_editorial(report, {
      tick=runtime.tick,
      target_id=target_id,
      target_type=target_type,
    })

    local policy_entry = {
      tick=runtime.tick,
      institution_id=inst.id,
      report_id=report.id,
      claim_key=((report.claim or {}).key),
      target_id=target_id,
      target_type=target_type,
      action=decision.action,
      priority=decision.priority,
      matched_rule_id=decision.matched_rule_id,
      agenda_prefix=decision.agenda_prefix,
      confidence_multiplier=decision.confidence_multiplier,
      delay_add=decision.delay_add,
      effective_delay_multiplier=decision.effective_delay_multiplier,
      tag=decision.tag,
      origin_observation_ids=Util.deepcopy(((report.lineage or {}).origin_observation_ids) or {}),
    }
    inst:log_policy(policy_entry)
    runtime.bus:emit("institution.policy_decision", Util.deepcopy(policy_entry))

    if decision.action ~= "suppress" then
      if target_type=="institution" and route_has_institution(transformed.lineage,target_id) then
        -- Explicit cycle prevention: do not route the same evidence back through
        -- an institution already present in its lineage.
      else
        local delay = base_delay * decision.effective_delay_multiplier + decision.delay_add
        local routed = Util.deepcopy(transformed)
        routed.confidence = Util.clamp(
          (tonumber(routed.confidence) or 0) * decision.confidence_multiplier
        )
        routed.provenance = routed.provenance or {}
        routed.provenance.institution_policy = Util.deepcopy(policy_entry)

        local route_options = Util.deepcopy(sub)
        route_options.editorial_policy = Util.deepcopy(policy_entry)

        self:_enqueue({
          kind="institution_broadcast",
          deliver_at=runtime.tick+delay,
          sender_institution_id=inst.id,
          target_type=target_type,
          target_id=target_id,
          route_options=route_options,
          report=routed,
          editorial_decision=Util.deepcopy(policy_entry),
        })
      end
    end
  end
end

function Ecology:_deliver_to_agent(runtime, sender_inst, target_id, report, route_options)
  if not runtime.agents[target_id] then return end
  route_options = route_options or {}
  local lineage = Lineage.extend(report.lineage, {
    kind="agent", id=target_id, at=runtime.tick,
  })

  local obs = Observation.from_claim(
    "institution_obs_"..sender_inst.id.."_"..report.id.."_"..target_id,
    report.claim,
    {
      source_event_id=report.id,
      subject_type="institution_report",
      subject_id=report.claim.key,
      sector=Util.deepcopy(runtime.agents[target_id].sector),
      evidence="transmitted",
      confidence=Util.clamp(
        report.confidence *
        (tonumber(route_options.trust) or sender_inst.policy.trust) *
        (1 - (tonumber(route_options.distortion) or 0) * 0.20)
      ),
      observed_at=runtime.tick,
      observer_id=target_id,
      source_agent_id=sender_inst.id,
      provenance={
        institution_id=sender_inst.id,
        institution_kind=sender_inst.kind,
        origin_observation_ids=Util.deepcopy(lineage.origin_observation_ids),
        route=Util.deepcopy(lineage.route),
        hop_count=lineage.hop_count,
        distortion_applied=report.distorted or false,
        route_edges=Util.deepcopy((report.provenance or {}).route_edges or {}),
        ingress_route=Util.deepcopy((report.provenance or {}).ingress_route),
        route_edge=Util.deepcopy(route_options.route),
        route_trust=tonumber(route_options.trust),
        route_distortion=tonumber(route_options.distortion),
        institution_policy=Util.deepcopy(route_options.editorial_policy),
      },
    }
  )
  runtime:_deliver_observation(target_id, obs)
end

function Ecology:_deliver_to_institution(runtime, sender_inst, target_id, report, route_options)
  route_options = route_options or {}
  local target = self.institutions[target_id]
  if not target then return end

  local forwarded = Util.deepcopy(report)
  forwarded.id = report.id.."->"..target_id
  forwarded.confidence = Util.clamp(report.confidence * (tonumber(route_options.trust) or target.policy.trust))
  if tonumber(route_options.distortion) and tonumber(route_options.distortion) > 0 then
    forwarded.confidence = Util.clamp(forwarded.confidence * (1 - tonumber(route_options.distortion) * 0.20))
  end
  forwarded.provenance = forwarded.provenance or {}
  forwarded.provenance.route_edges = Util.deepcopy(forwarded.provenance.route_edges or {})
  if route_options.route then
    forwarded.provenance.route_edges[#forwarded.provenance.route_edges+1] = Util.deepcopy(route_options.route)
  end
  if route_options.editorial_policy then
    forwarded.provenance.institution_policy = Util.deepcopy(route_options.editorial_policy)
  end
  -- The target institution is added to lineage when it actually broadcasts.
  -- Recording it here as well would duplicate the same institution as
  -- "received" and "broadcast" hops without adding causal information.
  forwarded.lineage = Util.deepcopy(report.lineage)

  self:_enqueue({
    kind="institution_receive",
    deliver_at=runtime.tick+target.policy.receive_delay,
    institution_id=target_id,
    report=forwarded,
  })
end

function Ecology:advance(runtime)
  local pending = {}
  table.sort(self.queue, function(a,b)
    if a.deliver_at == b.deliver_at then return tostring(a.id) < tostring(b.id) end
    return a.deliver_at < b.deliver_at
  end)

  for _, item in ipairs(self.queue) do
    if item.deliver_at <= runtime.tick then
      if item.kind == "institution_receive" then
        local inst = self.institutions[item.institution_id]
        if inst and item.report.confidence >= inst.policy.acceptance_min then
          if inst:archive_report(item.report) then
            self.routing_log[#self.routing_log+1] = {
              tick=runtime.tick, kind="institution_received",
              institution_id=inst.id, report_id=item.report.id,
            }
            runtime.bus:emit("institution.report_received", {
              institution_id=inst.id, report=Util.deepcopy(item.report),
            })
            self:_broadcast(runtime, inst, item.report)
          end
        end
      elseif item.kind == "institution_broadcast" then
        local sender = self.institutions[item.sender_institution_id]
        if sender then
          if item.target_type == "agent" then
            self:_deliver_to_agent(runtime, sender, item.target_id, item.report, item.route_options)
          else
            self:_deliver_to_institution(runtime, sender, item.target_id, item.report, item.route_options)
          end
          self.routing_log[#self.routing_log+1] = {
            tick=runtime.tick, kind="institution_broadcast_delivered",
            sender_institution_id=sender.id, target_id=item.target_id,
            target_type=item.target_type, report_id=item.report.id,
            route_id=((((item.route_options or {}).route) or {}).route_id),
          }
        end
      end
    else
      pending[#pending+1] = item
    end
  end
  self.queue = pending
end

function Ecology:snapshot()
  local institutions = {}
  for _, id in ipairs(Util.sorted_keys(self.institutions)) do
    institutions[id] = self.institutions[id]:snapshot()
  end
  return {
    institutions=institutions,
    queue=Util.deepcopy(self.queue),
    sequence=self.sequence,
    routing_log=Util.deepcopy(self.routing_log),
    max_hops=self.max_hops,
  }
end

function Ecology.restore(data)
  local eco = Ecology.new()
  for _, id in ipairs(Util.sorted_keys((data or {}).institutions or {})) do
    eco.institutions[id] = Institution.restore(data.institutions[id])
  end
  eco.queue = Util.deepcopy((data or {}).queue or {})
  eco.sequence = tonumber((data or {}).sequence) or 0
  eco.routing_log = Util.deepcopy((data or {}).routing_log or {})
  eco.max_hops = tonumber((data or {}).max_hops) or eco.max_hops
  return eco
end

return Ecology
