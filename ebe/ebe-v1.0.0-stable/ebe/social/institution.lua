local Util = require("ebe.util")
local InstitutionalPolicy = require("ebe.social.institution_policy")

local Institution = {}
Institution.__index = Institution

local PRESETS = {
  printing_house = {
    receive_delay = 0.5, broadcast_delay = 0.75,
    trust = 0.94, distortion = 0.02,
    acceptance_min = 0.42, rebroadcast_min = 0.48,
    archive_capacity = 256,
  },
  shrine_circle = {
    receive_delay = 0.25, broadcast_delay = 1.25,
    trust = 0.82, distortion = 0.12,
    acceptance_min = 0.32, rebroadcast_min = 0.38,
    archive_capacity = 128,
  },
  caravan_exchange = {
    receive_delay = 1.5, broadcast_delay = 2.5,
    trust = 0.76, distortion = 0.08,
    acceptance_min = 0.35, rebroadcast_min = 0.40,
    archive_capacity = 160,
  },
  military_post = {
    receive_delay = 0.25, broadcast_delay = 0.50,
    trust = 0.97, distortion = 0.01,
    acceptance_min = 0.62, rebroadcast_min = 0.66,
    archive_capacity = 192,
  },
  settlement_square = {
    receive_delay = 0.20, broadcast_delay = 0.80,
    trust = 0.72, distortion = 0.10,
    acceptance_min = 0.28, rebroadcast_min = 0.34,
    archive_capacity = 192,
  },
  roadside_relay = {
    receive_delay = 0.15, broadcast_delay = 0.45,
    trust = 0.68, distortion = 0.14,
    acceptance_min = 0.24, rebroadcast_min = 0.30,
    archive_capacity = 96,
  },
  front_watch = {
    receive_delay = 0.15, broadcast_delay = 0.40,
    trust = 0.95, distortion = 0.02,
    acceptance_min = 0.50, rebroadcast_min = 0.54,
    archive_capacity = 128,
  },
}

local function policy_from(kind, override)
  local base = Util.deepcopy(PRESETS[kind] or PRESETS.settlement_square)
  for k,v in pairs(override or {}) do base[k] = v end
  return base
end

local function report_lineage_key(report)
  local claim=(report or {}).claim or {}
  local roots=(((report or {}).lineage or {}).origin_observation_ids)
    or (((report or {}).provenance or {}).origin_observation_ids)
    or {}
  if type(roots)=="table" and #roots>0 then
    local copy=Util.deepcopy(roots)
    table.sort(copy,function(a,b) return tostring(a)<tostring(b) end)
    return tostring(claim.key or "claim").."|roots:"..table.concat(copy,",")
  end
  return "report-id:"..tostring((report or {}).id)
end

function Institution.new(spec)
  spec = spec or {}
  assert(type(spec.id)=="string" and spec.id~="", "institution id is required")
  local kind = spec.kind or "settlement_square"
  return setmetatable({
    id = spec.id,
    kind = kind,
    sector = Util.deepcopy(spec.sector or {0,0}),
    faction = spec.faction or "none",
    metadata = Util.deepcopy(spec.metadata or {}),
    policy = policy_from(kind, spec.policy),
    editorial = InstitutionalPolicy.normalize(spec.editorial or spec.institutional_policy or {}),
    policy_log = {},
    subscribers = {},
    archive = {},
    archive_order = {},
    received_ids = {},
    lineage_index = {},
    duplicate_lineage_count = 0,
    sequence = 0,
  }, Institution)
end

function Institution:subscribe(target_id, opts)
  self.subscribers[target_id] = Util.deepcopy(opts or {})
end

function Institution:unsubscribe(target_id)
  self.subscribers[target_id] = nil
end

function Institution:set_editorial_policy(spec)
  self.editorial = InstitutionalPolicy.normalize(spec or {})
  local cap = self.editorial.policy_log_capacity
  while #self.policy_log > cap do table.remove(self.policy_log,1) end
  return Util.deepcopy(self.editorial)
end

function Institution:evaluate_editorial(report, context)
  return InstitutionalPolicy.evaluate(self.editorial, report, context or {})
end

function Institution:log_policy(entry)
  self.policy_log[#self.policy_log+1] = Util.deepcopy(entry or {})
  local cap = (self.editorial or {}).policy_log_capacity or 256
  while #self.policy_log > cap do table.remove(self.policy_log,1) end
end

function Institution:archive_report(report)
  if self.received_ids[report.id] then return false end
  self.received_ids[report.id] = true

  local lineage_key=report_lineage_key(report)
  local existing_id=self.lineage_index[lineage_key]
  if existing_id and self.archive[existing_id] then
    self.duplicate_lineage_count=self.duplicate_lineage_count+1
    local existing=self.archive[existing_id]
    if tonumber(report.confidence or 0) > tonumber(existing.confidence or 0) then
      -- Keep the same canonical archive id but upgrade its best-known copy.
      local upgraded=Util.deepcopy(report)
      upgraded.id=existing_id
      upgraded.archive_alias_of=report.id
      self.archive[existing_id]=upgraded
    end
    return false
  end

  self.archive[report.id] = Util.deepcopy(report)
  self.archive_order[#self.archive_order+1] = report.id
  self.lineage_index[lineage_key]=report.id
  while #self.archive_order > self.policy.archive_capacity do
    local id = table.remove(self.archive_order,1)
    local old=self.archive[id]
    if old then self.lineage_index[report_lineage_key(old)]=nil end
    self.archive[id] = nil
  end
  return true
end

function Institution:snapshot()
  return {
    id=self.id, kind=self.kind, sector=Util.deepcopy(self.sector),
    faction=self.faction, metadata=Util.deepcopy(self.metadata),
    policy=Util.deepcopy(self.policy),
    editorial=Util.deepcopy(self.editorial),
    policy_log=Util.deepcopy(self.policy_log),
    subscribers=Util.deepcopy(self.subscribers),
    archive=Util.deepcopy(self.archive),
    archive_order=Util.deepcopy(self.archive_order),
    received_ids=Util.deepcopy(self.received_ids),
    lineage_index=Util.deepcopy(self.lineage_index),
    duplicate_lineage_count=self.duplicate_lineage_count,
    sequence=self.sequence,
  }
end

function Institution.restore(data)
  local inst=Institution.new(data or {})
  inst.editorial=InstitutionalPolicy.normalize((data or {}).editorial or {})
  inst.policy_log=Util.deepcopy((data or {}).policy_log or {})
  inst.subscribers=Util.deepcopy((data or {}).subscribers or {})
  inst.archive=Util.deepcopy((data or {}).archive or {})
  inst.archive_order=Util.deepcopy((data or {}).archive_order or {})
  inst.received_ids=Util.deepcopy((data or {}).received_ids or {})
  inst.lineage_index=Util.deepcopy((data or {}).lineage_index or {})
  inst.duplicate_lineage_count=tonumber((data or {}).duplicate_lineage_count) or 0
  inst.sequence=tonumber((data or {}).sequence) or 0
  return inst
end

function Institution.presets()
  return Util.deepcopy(PRESETS)
end

return Institution
