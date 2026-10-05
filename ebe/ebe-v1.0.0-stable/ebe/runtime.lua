local Util = require("ebe.util")
local EventBus = require("ebe.event_bus")
local Memory = require("ebe.cognition.memory")
local Belief = require("ebe.cognition.belief")
local Knowledge = require("ebe.cognition.knowledge")
local Interpretation = require("ebe.cognition.interpretation")
local Propagation = require("ebe.social.propagation")
local Reaction = require("ebe.social.reaction")
local Ecology = require("ebe.social.information_ecology")
local Collective = require("ebe.social.collective")
local Observation = require("ebe.cognition.observation")
local Lineage = require("ebe.social.source_lineage")
local PixelGen = require("ebe.integrations.pixelgen_v080")
local NetworkSynth = require("ebe.integrations.pixelgen_network_synth")
local ActionGateway = require("ebe.action.action_gateway")
local PersistenceContract = require("ebe.persistence.contract")

local Runtime = {}
Runtime.__index = Runtime
Runtime.VERSION = "1.0.0"

local function sorted_agent_ids(agents)
  return Util.sorted_keys(agents)
end

function Runtime.new(opts)
  opts = opts or {}
  local self = setmetatable({
    version = Runtime.VERSION,
    tick = tonumber(opts.tick) or 0,
    seed = tonumber(opts.seed) or 0,
    bus = EventBus.new({ history_limit = opts.bus_history_limit or 512 }),
    entities = {},
    agents = {},
    available_observations = {},
    external_events = {},
    reaction_log = {},
    integration_log = {},
    integration_state = {},
    delivery_log = {},
    network_plan = nil,
    agent_institution_access = {},
    propagation = Propagation.new(opts.propagation or {}),
    ecology = Ecology.new(opts.ecology or {}),
    collectives = {},
    collective_log = {},
    reaction = Reaction.new(opts.reaction or {}),
    action_gateway = ActionGateway.new(opts.actions or {}),
    knowledge_opts = Util.deepcopy(opts.knowledge or {}),
  }, Runtime)

  return self
end

function Runtime:add_agent(spec)
  spec = spec or {}
  assert(type(spec.id) == "string" and spec.id ~= "", "agent id is required")
  assert(not self.agents[spec.id], "duplicate agent id " .. spec.id)

  local agent = {
    id = spec.id,
    sector = Util.deepcopy(spec.sector or { 0, 0 }),
    faction = spec.faction or "none",
    trust = Util.deepcopy(spec.trust or {}),
    biases = Util.deepcopy(spec.biases or {}),
    memory = Memory.new(spec.memory or {}),
    beliefs = {},
    knowledge = {},
    interpretations = {},
    received_observations = {},
  }
  self.agents[agent.id] = agent
  for _,collective_id in ipairs(Util.sorted_keys(self.collectives or {})) do
    local collective=self.collectives[collective_id]
    if collective.metadata and collective.metadata.auto_enroll_faction == true
       and collective.faction ~= "none"
       and collective.faction == agent.faction then
      collective:add_member(agent.id,{auto=true})
    end
  end
  self.bus:emit("agent.added", {
    id = agent.id,
    sector = Util.deepcopy(agent.sector),
    faction = agent.faction,
  })
  if self.network_plan then
    NetworkSynth.attach_agent(self,self.network_plan,agent.id,{})
  end
  return agent
end

function Runtime:move_agent(id, sector)
  local agent = assert(self.agents[id], "unknown agent " .. tostring(id))
  assert(type(sector) == "table" and #sector == 2, "sector must be [sx, sy]")
  local before = Util.deepcopy(agent.sector)
  agent.sector = Util.deepcopy(sector)
  self.bus:emit("agent.moved", {
    id = id,
    before = before,
    after = Util.deepcopy(sector),
  })
  if self.network_plan then
    NetworkSynth.attach_agent(self,self.network_plan,id,{})
  end
end

function Runtime:connect_agents(a, b, opts)
  assert(self.agents[a], "unknown agent " .. tostring(a))
  assert(self.agents[b], "unknown agent " .. tostring(b))
  self.propagation:connect(a, b, opts or {})
end


function Runtime:add_institution(spec)
  return self.ecology:add_institution(spec)
end

function Runtime:set_institution_editorial_policy(institution_id, spec)
  local inst=assert(self.ecology.institutions[institution_id],
    "unknown institution "..tostring(institution_id))
  local policy=inst:set_editorial_policy(spec or {})
  self.bus:emit("institution.policy_changed",{
    institution_id=institution_id,
    policy=Util.deepcopy(policy),
  })
  return policy
end

function Runtime:institution_policy_view(institution_id)
  local inst=assert(self.ecology.institutions[institution_id],
    "unknown institution "..tostring(institution_id))
  return {
    institution_id=inst.id,
    editorial=Util.deepcopy(inst.editorial),
    policy_log=Util.deepcopy(inst.policy_log),
  }
end

function Runtime:subscribe_institution(institution_id, target_id, opts)
  assert(self.agents[target_id] or self.ecology.institutions[target_id],
    "unknown institution subscriber "..tostring(target_id))
  self.ecology:subscribe(institution_id,target_id,opts or {})
end

function Runtime:report_to_institution(sender_id, institution_id, claim_key, opts)
  return self.ecology:submit_agent_report(
    self,sender_id,institution_id,claim_key,opts or {}
  )
end

function Runtime:add_collective(spec)
  spec = spec or {}
  assert(type(spec.id)=="string" and spec.id~="", "collective id is required")
  assert(not self.collectives[spec.id], "duplicate collective id "..spec.id)
  local collective=Collective.new(spec)
  for _,member_id in ipairs(Util.sorted_keys(collective.members)) do
    assert(self.agents[member_id], "unknown collective member "..tostring(member_id))
  end
  self.collectives[collective.id]=collective

  if collective.metadata and collective.metadata.auto_enroll_faction == true
     and collective.faction ~= "none" then
    for _,agent_id in ipairs(sorted_agent_ids(self.agents)) do
      if self.agents[agent_id].faction == collective.faction then
        collective:add_member(agent_id,{auto=true})
      end
    end
  end

  self.bus:emit("collective.added",{
    id=collective.id,
    kind=collective.kind,
    faction=collective.faction,
  })
  return collective
end

function Runtime:add_collective_member(collective_id, agent_id, metadata)
  local collective=assert(self.collectives[collective_id], "unknown collective "..tostring(collective_id))
  assert(self.agents[agent_id], "unknown agent "..tostring(agent_id))
  collective:add_member(agent_id,metadata or {})
  self.bus:emit("collective.member_added",{
    collective_id=collective_id,
    agent_id=agent_id,
  })
  return true
end

function Runtime:remove_collective_member(collective_id, agent_id)
  local collective=assert(self.collectives[collective_id], "unknown collective "..tostring(collective_id))
  collective:remove_member(agent_id)
  self.bus:emit("collective.member_removed",{
    collective_id=collective_id,
    agent_id=agent_id,
  })
  return true
end

function Runtime:subscribe_collective(collective_id, target_id, opts)
  local collective=assert(self.collectives[collective_id], "unknown collective "..tostring(collective_id))
  assert(self.agents[target_id] or self.ecology.institutions[target_id],
    "unknown collective subscriber "..tostring(target_id))
  collective:subscribe(target_id,opts or {})
  return true
end

function Runtime:submit_to_collective(sender_id, collective_id, claim_key, opts)
  opts=opts or {}
  local sender=assert(self.agents[sender_id], "unknown sender "..tostring(sender_id))
  local collective=assert(self.collectives[collective_id], "unknown collective "..tostring(collective_id))
  if collective.policy.members_only_submit then
    assert(collective:is_member(sender_id), "sender is not a member of collective "..collective_id)
  end
  local belief=assert(sender.beliefs[claim_key], "sender has no belief "..tostring(claim_key))
  collective.sequence=collective.sequence+1
  local lineage=Lineage.from_belief(belief)
  local report={
    id=opts.id or ("collective_report_"..collective.id.."_"..tostring(collective.sequence)),
    reporter_type="agent",
    reporter_id=sender_id,
    sender_id=sender_id,
    created_at=self.tick,
    claim={
      key=claim_key,
      value=Util.deepcopy(belief.value),
      confidence=belief.confidence,
    },
    confidence=Util.clamp((tonumber(opts.trust) or 1.0) * belief.confidence),
    lineage=lineage,
    provenance={
      belief_sources=Util.deepcopy(belief.sources),
      origin_observation_ids=Util.deepcopy(lineage.origin_observation_ids),
      inherited=Util.deepcopy(opts.provenance or {}),
    },
  }
  local accepted=collective:archive_report(report)
  self.collective_log[#self.collective_log+1]={
    tick=self.tick,
    kind=accepted and "collective_report_accepted" or "collective_report_duplicate",
    collective_id=collective_id,
    report_id=report.id,
    reporter_id=sender_id,
    claim_key=claim_key,
  }
  self.bus:emit("collective.report_submitted",{
    collective_id=collective_id,
    report=Util.deepcopy(report),
    accepted=accepted,
  })
  return Util.deepcopy(report),accepted
end

function Runtime:get_collective_consensus(collective_id, claim_key)
  local collective=assert(self.collectives[collective_id], "unknown collective "..tostring(collective_id))
  return collective:get_consensus(claim_key)
end

function Runtime:collective_view(collective_id)
  local collective=assert(self.collectives[collective_id], "unknown collective "..tostring(collective_id))
  return {
    id=collective.id,
    kind=collective.kind,
    faction=collective.faction,
    metadata=Util.deepcopy(collective.metadata),
    policy=Util.deepcopy(collective.policy),
    members=Util.deepcopy(collective.members),
    subscribers=Util.deepcopy(collective.subscribers),
    consensus=Util.deepcopy(collective.consensus),
    report_count=#collective.report_order,
    duplicate_report_count=collective.duplicate_report_count,
  }
end

function Runtime:publish_collective(collective_id, claim_key, target_ids, opts)
  opts=opts or {}
  local collective=assert(self.collectives[collective_id], "unknown collective "..tostring(collective_id))
  local consensus=assert(collective:get_consensus(claim_key),
    "collective has no consensus record for "..tostring(claim_key))

  local targets={}
  if target_ids==nil then
    targets=Util.sorted_keys(collective.subscribers)
  elseif type(target_ids)=="string" then
    targets={target_ids}
  else
    targets=Util.deepcopy(target_ids)
    table.sort(targets,function(a,b) return tostring(a)<tostring(b) end)
  end

  local publications={}
  for _,target_id in ipairs(targets) do
    local sub=collective.subscribers[target_id] or {}
    local trust=Util.clamp(tonumber(sub.trust) or tonumber(opts.trust) or collective.policy.publication_trust)
    local confidence=Util.clamp(consensus.confidence*trust)
    collective.publication_sequence=collective.publication_sequence+1
    local publication_id="collective_pub_"..collective.id.."_"..tostring(collective.publication_sequence)
    local lineage=Lineage.extend({
      origin_observation_ids=Util.deepcopy(consensus.origin_observation_ids or {}),
      route={},
      hop_count=0,
    },{
      kind="collective",
      id=collective.id,
      collective_kind=collective.kind,
      at=self.tick,
    })
    local claim={
      key=claim_key,
      value=Util.deepcopy(consensus.value),
      confidence=1.0,
    }

    if self.agents[target_id] then
      local obs=Observation.from_claim(
        publication_id.."_"..target_id,
        claim,
        {
          source_event_id=publication_id,
          subject_type="collective_consensus",
          subject_id=collective.id,
          sector=Util.deepcopy(self.agents[target_id].sector),
          evidence="transmitted",
          confidence=confidence,
          observed_at=self.tick,
          observer_id=target_id,
          source_agent_id=collective.id,
          provenance={
            collective_id=collective.id,
            collective_kind=collective.kind,
            consensus_state=consensus.state,
            origin_observation_ids=Util.deepcopy(lineage.origin_observation_ids),
            route=Util.deepcopy(lineage.route),
            hop_count=lineage.hop_count,
            publication_id=publication_id,
          },
        }
      )
      self:_deliver_observation(target_id,obs)
      publications[#publications+1]={
        id=publication_id,
        target_type="agent",
        target_id=target_id,
        observation_id=obs.id,
      }
    elseif self.ecology.institutions[target_id] then
      local report=self.ecology:submit_external_report(
        self,
        "collective",
        collective.id,
        target_id,
        {
          id=publication_id,
          claim=claim,
          confidence=confidence,
          lineage=lineage,
          provenance={
            collective_id=collective.id,
            collective_kind=collective.kind,
            consensus_state=consensus.state,
            origin_observation_ids=Util.deepcopy(lineage.origin_observation_ids),
            route=Util.deepcopy(lineage.route),
            hop_count=lineage.hop_count,
          },
        },
        sub
      )
      publications[#publications+1]={
        id=publication_id,
        target_type="institution",
        target_id=target_id,
        report_id=report.id,
      }
    else
      error("unknown collective publication target "..tostring(target_id))
    end

    self.collective_log[#self.collective_log+1]={
      tick=self.tick,
      kind="collective_published",
      collective_id=collective.id,
      publication_id=publication_id,
      target_id=target_id,
      claim_key=claim_key,
      source_count=consensus.source_count,
    }
  end

  self.bus:emit("collective.published",{
    collective_id=collective.id,
    claim_key=claim_key,
    publications=Util.deepcopy(publications),
  })
  return publications
end


function Runtime:register_reaction_action_adapter(reaction_kind, spec)
  return self.action_gateway:register_adapter(reaction_kind,spec)
end

function Runtime:request_action(spec)
  spec=Util.deepcopy(spec or {})
  return self.action_gateway:submit(self,spec,{})
end

function Runtime:_handle_reaction_action(reaction, agent, belief)
  return self.action_gateway:from_reaction(self,reaction,agent,belief)
end

function Runtime:action_request(id)
  return self.action_gateway:get(id)
end

function Runtime:action_requests(status, domain)
  return self.action_gateway:list(status,domain)
end

function Runtime:export_pixelgen_action(id, opts)
  return self.action_gateway:export_pixelgen(self,id,opts or {})
end

function Runtime:resolve_action_request(id, status, result)
  return self.action_gateway:resolve(self,id,status,result or {})
end

function Runtime:synthesize_pixelgen_network(world, opts)
  opts = opts or {}
  local plan = NetworkSynth.synthesize(world, opts)
  local errors = NetworkSynth.validate_plan(plan, world)
  assert(#errors==0, "invalid synthesized network: "..table.concat(errors, "; "))
  NetworkSynth.apply(self, plan, {
    attach_existing_agents = opts.attach_existing_agents ~= false,
    agent_delivery_delay = opts.agent_delivery_delay,
    agent_delivery_trust = opts.agent_delivery_trust,
  })
  return plan
end

function Runtime:synthesize_pixelgen_network_file(path, opts)
  return self:synthesize_pixelgen_network(NetworkSynth.load_world(path), opts or {})
end

function Runtime:attach_agent_to_network(agent_id, opts)
  assert(self.network_plan, "no synthesized network plan is active")
  return NetworkSynth.attach_agent(self, self.network_plan, agent_id, opts or {})
end

function Runtime:local_institution(agent_id)
  return NetworkSynth.local_institution(self, agent_id)
end

function Runtime:report_to_local_network(sender_id, claim_key, opts)
  opts = opts or {}
  local institution_id = self:local_institution(sender_id)
  if not institution_id and self.network_plan then
    local access = self:attach_agent_to_network(sender_id, opts)
    institution_id = access and access.institution_id or nil
  end
  assert(institution_id, "agent has no accessible synthesized institution")
  local access = (self.agent_institution_access or {})[sender_id] or {}
  local report_opts = Util.deepcopy(opts)
  if report_opts.trust == nil then report_opts.trust = access.trust end
  if report_opts.delay == nil then report_opts.delay = access.delay end
  if report_opts.route == nil then
    report_opts.route = {
      route_id = "access:"..sender_id..":"..institution_id,
      path = Util.deepcopy(access.path),
      path_cost = access.cost,
      access = true,
    }
  end
  return self:report_to_institution(sender_id, institution_id, claim_key, report_opts)
end

function Runtime:ingest_pixelgen(bundle)
  local imported=PixelGen.ingest(self, bundle)
  imported.action_results=self.action_gateway:correlate_pixelgen_bundle(self,bundle)
  return imported
end

function Runtime:ingest_pixelgen_file(path)
  return self:ingest_pixelgen(PixelGen.load_file(path))
end

function Runtime:_recompute(agent)
  agent.beliefs = Belief.rebuild(agent.memory, agent)
  agent.knowledge = Knowledge.rebuild(agent.beliefs, self.knowledge_opts)
  agent.interpretations = Interpretation.rebuild(agent.beliefs, agent)
  self.reaction:evaluate(self, agent)

  self.bus:emit("cognition.recomputed", {
    agent_id = agent.id,
    beliefs = #Util.sorted_keys(agent.beliefs),
    knowledge = #Util.sorted_keys(agent.knowledge),
    interpretations = #agent.interpretations,
  })
end

function Runtime:_deliver_observation(agent_id, observation)
  local agent = assert(self.agents[agent_id], "unknown agent " .. tostring(agent_id))
  if agent.received_observations[observation.id] then return false end

  local obs = Util.deepcopy(observation)
  obs.observer_id = agent_id
  obs.knowledge_state = "assigned_as_evidence"
  if obs.observed_at == nil then obs.observed_at = self.tick end

  local added = agent.memory:add(obs, self.tick)
  if not added then return false end

  agent.received_observations[obs.id] = true
  self.delivery_log[#self.delivery_log + 1] = {
    tick = self.tick,
    agent_id = agent_id,
    observation_id = obs.id,
    evidence = obs.evidence,
    source_agent_id = obs.source_agent_id,
  }

  self.bus:emit("observation.delivered", {
    agent_id = agent_id,
    observation = Util.deepcopy(obs),
  })

  self:_recompute(agent)
  return true
end

function Runtime:assign_local_observations()
  local delivered = 0

  -- Crucial locality rule: PixelGen has already decided which sectors have
  -- direct evidence. EBE assigns evidence only to agents occupying that exact
  -- sector. It does not expand that evidence radius again.
  for _, obs_id in ipairs(Util.sorted_keys(self.available_observations)) do
    local obs = self.available_observations[obs_id]
    for _, agent_id in ipairs(sorted_agent_ids(self.agents)) do
      local agent = self.agents[agent_id]
      if Util.same_sector(agent.sector, obs.sector) then
        if self:_deliver_observation(agent_id, obs) then
          delivered = delivered + 1
        end
      end
    end
  end

  return delivered
end

function Runtime:get_belief(agent_id, claim_key)
  local agent = assert(self.agents[agent_id], "unknown agent " .. tostring(agent_id))
  return agent.beliefs[claim_key]
end

function Runtime:get_knowledge(agent_id, claim_key)
  local agent = assert(self.agents[agent_id], "unknown agent " .. tostring(agent_id))
  return agent.knowledge[claim_key]
end

function Runtime:share(sender_id, receiver_id, claim_key, opts)
  local sender = assert(self.agents[sender_id], "unknown sender")
  assert(self.agents[receiver_id], "unknown receiver")
  local belief = assert(sender.beliefs[claim_key], "sender has no belief " .. tostring(claim_key))

  local claim = {
    key = claim_key,
    value = Util.deepcopy(belief.value),
    confidence = belief.confidence,
  }
  return self.propagation:queue_claim(
    self,
    sender_id,
    receiver_id,
    claim,
    {
      lineage = {
        origin_observation_ids = Util.deepcopy(belief.origin_observation_ids or belief.sources or {}),
        route = Util.deepcopy(((opts or {}).provenance or {}).route or {}),
        hop_count = tonumber(((opts or {}).provenance or {}).hop_count) or 0,
      },
      provenance = {
        belief_sources = Util.deepcopy(belief.sources),
        origin_observation_ids = Util.deepcopy(belief.origin_observation_ids or belief.sources or {}),
        inherited = Util.deepcopy((opts or {}).provenance or {}),
      },
    }
  )
end

function Runtime:advance(hours)
  hours = math.max(0, tonumber(hours) or 0)
  self.tick = self.tick + hours

  for _, agent_id in ipairs(sorted_agent_ids(self.agents)) do
    local agent = self.agents[agent_id]
    agent.memory:advance(hours, self.tick)
  end

  -- First deliver transmissions that became due at the new time.
  self.propagation:advance(self)

  -- Then advance institutional information routes.
  self.ecology:advance(self)

  -- Then rebuild beliefs/knowledge from decayed memories.
  for _, agent_id in ipairs(sorted_agent_ids(self.agents)) do
    self:_recompute(self.agents[agent_id])
  end

  self.bus:emit("time.advanced", { tick = self.tick, hours = hours })
end

function Runtime:agent_view(agent_id)
  local agent = assert(self.agents[agent_id], "unknown agent " .. tostring(agent_id))
  return {
    id = agent.id,
    sector = Util.deepcopy(agent.sector),
    faction = agent.faction,
    beliefs = Util.deepcopy(agent.beliefs),
    knowledge = Util.deepcopy(agent.knowledge),
    interpretations = Util.deepcopy(agent.interpretations),
    memory = agent.memory:snapshot(),
  }
end

function Runtime:snapshot()
  local agents = {}
  for _, id in ipairs(sorted_agent_ids(self.agents)) do
    local a = self.agents[id]
    agents[id] = {
      id = a.id,
      sector = Util.deepcopy(a.sector),
      faction = a.faction,
      trust = Util.deepcopy(a.trust),
      biases = Util.deepcopy(a.biases),
      memory = a.memory:snapshot(),
      beliefs = Util.deepcopy(a.beliefs),
      knowledge = Util.deepcopy(a.knowledge),
      interpretations = Util.deepcopy(a.interpretations),
      received_observations = Util.deepcopy(a.received_observations),
    }
  end

  return {
    version = self.version,
    contract_version = PersistenceContract.VERSION,
    tick = self.tick,
    seed = self.seed,
    entities = Util.deepcopy(self.entities),
    agents = agents,
    available_observations = Util.deepcopy(self.available_observations),
    external_events = Util.deepcopy(self.external_events),
    reaction_log = Util.deepcopy(self.reaction_log),
    integration_log = Util.deepcopy(self.integration_log),
    integration_state = Util.deepcopy(self.integration_state),
    delivery_log = Util.deepcopy(self.delivery_log),
    network_plan = Util.deepcopy(self.network_plan),
    agent_institution_access = Util.deepcopy(self.agent_institution_access),
    propagation = self.propagation:snapshot(),
    ecology = self.ecology:snapshot(),
    collectives = (function()
      local out={}
      for _,id in ipairs(Util.sorted_keys(self.collectives)) do
        out[id]=self.collectives[id]:snapshot()
      end
      return out
    end)(),
    collective_log = Util.deepcopy(self.collective_log),
    reaction = self.reaction:snapshot(),
    action_gateway = self.action_gateway:snapshot(),
    knowledge_opts = Util.deepcopy(self.knowledge_opts),
    bus_history = self.bus:snapshot(),
  }
end

function Runtime.restore(snapshot)
  snapshot = PersistenceContract.migrate_snapshot(snapshot)
  PersistenceContract.assert_snapshot(snapshot)

  local rt = Runtime.new({
    tick = snapshot.tick,
    seed = snapshot.seed,
    knowledge = snapshot.knowledge_opts,
  })

  rt.entities = Util.deepcopy(snapshot.entities or {})
  rt.available_observations = Util.deepcopy(snapshot.available_observations or {})
  rt.external_events = Util.deepcopy(snapshot.external_events or {})
  rt.reaction_log = Util.deepcopy(snapshot.reaction_log or {})
  rt.integration_log = Util.deepcopy(snapshot.integration_log or {})
  rt.integration_state = Util.deepcopy(snapshot.integration_state or {})
  rt.delivery_log = Util.deepcopy(snapshot.delivery_log or {})
  rt.network_plan = Util.deepcopy(snapshot.network_plan)
  rt.agent_institution_access = Util.deepcopy(snapshot.agent_institution_access or {})
  rt.propagation = Propagation.restore(snapshot.propagation or {})
  rt.ecology = Ecology.restore(snapshot.ecology or {})
  rt.collectives = {}
  for _,id in ipairs(Util.sorted_keys(snapshot.collectives or {})) do
    rt.collectives[id]=Collective.restore(snapshot.collectives[id])
  end
  rt.collective_log = Util.deepcopy(snapshot.collective_log or {})
  rt.reaction:restore(snapshot.reaction or {})
  rt.action_gateway=ActionGateway.restore(snapshot.action_gateway or {})
  rt.bus.history = Util.deepcopy(snapshot.bus_history or {})

  for _, id in ipairs(Util.sorted_keys(snapshot.agents or {})) do
    local src = snapshot.agents[id]
    local agent = {
      id = src.id,
      sector = Util.deepcopy(src.sector),
      faction = src.faction,
      trust = Util.deepcopy(src.trust or {}),
      biases = Util.deepcopy(src.biases or {}),
      memory = Memory.restore(src.memory or {}),
      beliefs = Util.deepcopy(src.beliefs or {}),
      knowledge = Util.deepcopy(src.knowledge or {}),
      interpretations = Util.deepcopy(src.interpretations or {}),
      received_observations = Util.deepcopy(src.received_observations or {}),
    }
    rt.agents[id] = agent
  end

  return rt
end

function Runtime:summary()
  local knowledge = 0
  local beliefs = 0
  local memories = 0
  for _, id in ipairs(sorted_agent_ids(self.agents)) do
    local a = self.agents[id]
    beliefs = beliefs + #Util.sorted_keys(a.beliefs)
    knowledge = knowledge + #Util.sorted_keys(a.knowledge)
    memories = memories + #a.memory.order
  end

  return {
    version = self.version,
    tick = self.tick,
    agents = #sorted_agent_ids(self.agents),
    entities = #Util.sorted_keys(self.entities),
    external_events = #self.external_events,
    available_observations = #Util.sorted_keys(self.available_observations),
    memory_entries = memories,
    beliefs = beliefs,
    knowledge = knowledge,
    queued_transmissions = #self.propagation.queue,
    institutions = #Util.sorted_keys(self.ecology.institutions),
    collectives = #Util.sorted_keys(self.collectives),
    collective_reports = (function()
      local n=0
      for _,id in ipairs(Util.sorted_keys(self.collectives)) do
        n=n+#self.collectives[id].report_order
      end
      return n
    end)(),
    queued_institution_messages = #self.ecology.queue,
    synthesized_routes = self.network_plan and #(self.network_plan.routes or {}) or 0,
    attached_agents = #Util.sorted_keys(self.agent_institution_access),
    reactions = #self.reaction_log,
    action_requests = #self.action_gateway.order,
    pending_action_requests = #self.action_gateway:list("pending"),
    exported_action_requests = #self.action_gateway:list("exported"),
    applied_action_requests = #self.action_gateway:list("applied"),
    rejected_action_requests = #self.action_gateway:list("rejected"),
  }
end

return Runtime
