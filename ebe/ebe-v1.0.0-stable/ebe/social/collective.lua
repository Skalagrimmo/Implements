local Util = require("ebe.util")

local Collective = {}
Collective.__index = Collective

local DEFAULT_POLICY = {
  acceptance_min = 0.30,
  consensus_min = 0.62,
  confidence_min = 0.55,
  min_independent_roots = 2,
  archive_capacity = 256,
  publication_trust = 0.90,
  members_only_submit = true,
}

local function policy_from(override)
  local out = Util.deepcopy(DEFAULT_POLICY)
  for k,v in pairs(override or {}) do out[k]=v end
  out.acceptance_min = Util.clamp(tonumber(out.acceptance_min) or DEFAULT_POLICY.acceptance_min)
  out.consensus_min = Util.clamp(tonumber(out.consensus_min) or DEFAULT_POLICY.consensus_min)
  out.confidence_min = Util.clamp(tonumber(out.confidence_min) or DEFAULT_POLICY.confidence_min)
  out.publication_trust = Util.clamp(tonumber(out.publication_trust) or DEFAULT_POLICY.publication_trust)
  out.min_independent_roots = math.max(1, math.floor(tonumber(out.min_independent_roots) or DEFAULT_POLICY.min_independent_roots))
  out.archive_capacity = math.max(1, math.floor(tonumber(out.archive_capacity) or DEFAULT_POLICY.archive_capacity))
  out.members_only_submit = out.members_only_submit ~= false
  return out
end

local function unique_sorted(list)
  local seen, out = {}, {}
  for _,v in ipairs(list or {}) do
    if v ~= nil and not seen[v] then
      seen[v]=true
      out[#out+1]=v
    end
  end
  table.sort(out,function(a,b) return tostring(a)<tostring(b) end)
  return out
end

local function lineage_roots(report)
  local roots = (((report or {}).lineage or {}).origin_observation_ids)
    or (((report or {}).provenance or {}).origin_observation_ids)
    or {}
  if type(roots) ~= "table" or #roots == 0 then
    local reporter = (report or {}).reporter_id or (report or {}).sender_id
    if reporter ~= nil then
      roots = { "legacy-source:"..tostring(reporter) }
    else
      roots = { "collective-report:"..tostring((report or {}).id) }
    end
  end
  return unique_sorted(roots)
end

local function reporter_id(report)
  return tostring((report or {}).reporter_id or (report or {}).sender_id or "unknown")
end

local function better_candidate(a,b)
  if not b then return true end
  local ac = tonumber(a.confidence) or 0
  local bc = tonumber(b.confidence) or 0
  if ac ~= bc then return ac > bc end
  local av = Util.value_key(((a or {}).claim or {}).value)
  local bv = Util.value_key(((b or {}).claim or {}).value)
  if av ~= bv then return tostring(av) < tostring(bv) end
  return tostring(a.id) < tostring(b.id)
end

function Collective.new(spec)
  spec = spec or {}
  assert(type(spec.id)=="string" and spec.id~="", "collective id is required")
  local members = {}
  if type(spec.members)=="table" then
    if #spec.members>0 then
      for _,id in ipairs(spec.members) do members[id]={} end
    else
      members=Util.deepcopy(spec.members)
    end
  end
  local subscribers=Util.deepcopy(spec.subscribers or {})

  return setmetatable({
    id = spec.id,
    kind = spec.kind or "group",
    faction = spec.faction or "none",
    metadata = Util.deepcopy(spec.metadata or {}),
    policy = policy_from(spec.policy),
    members = members,
    subscribers = subscribers,
    reports = {},
    report_order = {},
    received_ids = {},
    consensus = {},
    sequence = 0,
    publication_sequence = 0,
    duplicate_report_count = 0,
  }, Collective)
end

function Collective:add_member(agent_id, metadata)
  assert(type(agent_id)=="string" and agent_id~="", "member id is required")
  self.members[agent_id] = Util.deepcopy(metadata or {})
end

function Collective:remove_member(agent_id)
  self.members[agent_id] = nil
end

function Collective:is_member(agent_id)
  return self.members[agent_id] ~= nil
end

function Collective:subscribe(target_id, opts)
  assert(type(target_id)=="string" and target_id~="", "subscriber id is required")
  self.subscribers[target_id] = Util.deepcopy(opts or {})
end

function Collective:unsubscribe(target_id)
  self.subscribers[target_id] = nil
end

function Collective:archive_report(report)
  assert(type(report)=="table", "collective report must be a table")
  assert(type(report.id)=="string" and report.id~="", "collective report id is required")
  assert(type(report.claim)=="table", "collective report claim is required")
  assert(type(report.claim.key)=="string" and report.claim.key~="", "collective report claim key is required")
  if self.received_ids[report.id] then
    self.duplicate_report_count = self.duplicate_report_count + 1
    return false
  end
  self.received_ids[report.id] = true
  self.reports[report.id] = Util.deepcopy(report)
  self.report_order[#self.report_order+1] = report.id
  while #self.report_order > self.policy.archive_capacity do
    local old_id = table.remove(self.report_order,1)
    self.reports[old_id] = nil
  end
  self:rebuild_consensus()
  return true
end

function Collective:rebuild_consensus()
  local grouped = {}

  for _,report_id in ipairs(self.report_order) do
    local report = self.reports[report_id]
    if report and (tonumber(report.confidence) or 0) >= self.policy.acceptance_min then
      local claim = report.claim or {}
      local key = claim.key
      if type(key)=="string" and key~="" then
        local bucket = grouped[key]
        if not bucket then
          bucket = {
            key=key,
            reports={},
            reporters={},
            reporter_set={},
            root_candidates={},
            value_reporters={},
          }
          grouped[key]=bucket
        end
        bucket.reports[#bucket.reports+1]=report.id
        local rid=reporter_id(report)
        if not bucket.reporter_set[rid] then
          bucket.reporter_set[rid]=true
          bucket.reporters[#bucket.reporters+1]=rid
        end
        local report_vk=Util.value_key(claim.value)
        local vr=bucket.value_reporters[report_vk]
        if not vr then
          vr={set={},list={}}
          bucket.value_reporters[report_vk]=vr
        end
        if not vr.set[rid] then
          vr.set[rid]=true
          vr.list[#vr.list+1]=rid
        end

        for _,root_id in ipairs(lineage_roots(report)) do
          local existing=bucket.root_candidates[root_id]
          if better_candidate(report,existing) then
            bucket.root_candidates[root_id]=report
          end
        end
      end
    end
  end

  local consensus={}
  for _,key in ipairs(Util.sorted_keys(grouped)) do
    local bucket=grouped[key]
    local options={}
    local total_score=0
    local total_roots=0

    for _,root_id in ipairs(Util.sorted_keys(bucket.root_candidates)) do
      local report=bucket.root_candidates[root_id]
      local claim=report.claim
      local vk=Util.value_key(claim.value)
      local option=options[vk]
      if not option then
        option={
          value=Util.deepcopy(claim.value),
          score=0,
          roots={},
          reporters={},
          reporter_set={},
          reports={},
        }
        options[vk]=option
      end
      local confidence=Util.clamp(tonumber(report.confidence) or 0)
      option.score=option.score+confidence
      option.roots[#option.roots+1]=root_id
      option.reports[#option.reports+1]=report.id
      local rid=reporter_id(report)
      if not option.reporter_set[rid] then
        option.reporter_set[rid]=true
        option.reporters[#option.reporters+1]=rid
      end
      total_score=total_score+confidence
      total_roots=total_roots+1
    end

    local best_key=nil
    local best_score=-1
    for vk,option in pairs(options) do
      table.sort(option.roots,function(a,b) return tostring(a)<tostring(b) end)
      table.sort(option.reporters,function(a,b) return tostring(a)<tostring(b) end)
      table.sort(option.reports,function(a,b) return tostring(a)<tostring(b) end)
      if option.score > best_score or
         (option.score==best_score and tostring(vk)<tostring(best_key)) then
        best_key=vk
        best_score=option.score
      end
    end

    if best_key then
      local best=options[best_key]
      local agreement=total_score>0 and best_score/total_score or 0
      local mean_support=#best.roots>0 and best_score/#best.roots or 0
      local confidence=Util.clamp(agreement*mean_support)
      local state="tentative"
      if #best.roots >= self.policy.min_independent_roots then
        state="corroborated"
        if agreement >= self.policy.consensus_min and confidence >= self.policy.confidence_min then
          state="consensus"
        end
      end

      for vk,option in pairs(options) do
        local vr=bucket.value_reporters[vk]
        if vr then
          option.reporters=Util.deepcopy(vr.list)
          table.sort(option.reporters,function(a,b) return tostring(a)<tostring(b) end)
        end
        option.score=Util.round(option.score,6)
        option.root_count=#option.roots
        option.reporter_count=#option.reporters
        option.reporter_set=nil
      end

      consensus[key]={
        key=key,
        value=Util.deepcopy(best.value),
        confidence=Util.round(confidence,6),
        agreement=Util.round(agreement,6),
        support=Util.round(best_score,6),
        mean_root_confidence=Util.round(mean_support,6),
        state=state,
        source_count=#best.roots,
        independent_root_count=#best.roots,
        total_independent_root_count=total_roots,
        conflicting_root_count=math.max(0,total_roots-#best.roots),
        reporter_count=#best.reporters,
        total_reporter_count=#bucket.reporters,
        report_count=#bucket.reports,
        origin_observation_ids=Util.deepcopy(best.roots),
        source_reports=Util.deepcopy(best.reports),
        reporters=Util.deepcopy(best.reporters),
        alternatives=Util.deepcopy(options),
      }
    end
  end

  self.consensus=consensus
  return consensus
end

function Collective:get_consensus(claim_key)
  return self.consensus[claim_key]
end

function Collective:snapshot()
  return {
    id=self.id,
    kind=self.kind,
    faction=self.faction,
    metadata=Util.deepcopy(self.metadata),
    policy=Util.deepcopy(self.policy),
    members=Util.deepcopy(self.members),
    subscribers=Util.deepcopy(self.subscribers),
    reports=Util.deepcopy(self.reports),
    report_order=Util.deepcopy(self.report_order),
    received_ids=Util.deepcopy(self.received_ids),
    consensus=Util.deepcopy(self.consensus),
    sequence=self.sequence,
    publication_sequence=self.publication_sequence,
    duplicate_report_count=self.duplicate_report_count,
  }
end

function Collective.restore(data)
  local c=Collective.new(data or {})
  c.members=Util.deepcopy((data or {}).members or {})
  c.subscribers=Util.deepcopy((data or {}).subscribers or {})
  c.reports=Util.deepcopy((data or {}).reports or {})
  c.report_order=Util.deepcopy((data or {}).report_order or {})
  c.received_ids=Util.deepcopy((data or {}).received_ids or {})
  c.consensus=Util.deepcopy((data or {}).consensus or {})
  c.sequence=tonumber((data or {}).sequence) or 0
  c.publication_sequence=tonumber((data or {}).publication_sequence) or 0
  c.duplicate_report_count=tonumber((data or {}).duplicate_report_count) or 0
  -- Rebuild rather than trusting stale derived consensus in old snapshots.
  c:rebuild_consensus()
  return c
end

function Collective.default_policy()
  return Util.deepcopy(DEFAULT_POLICY)
end

return Collective
