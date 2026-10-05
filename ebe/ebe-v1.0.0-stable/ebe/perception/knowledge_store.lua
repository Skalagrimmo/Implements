local util = require("ebe.core.util")
local KnowledgeStore = {}
KnowledgeStore.__index = KnowledgeStore

function KnowledgeStore.new()
  return setmetatable({ _knowledge = {} }, KnowledgeStore)
end

function KnowledgeStore:_bucket(observer_id)
  local bucket = self._knowledge[observer_id]
  if not bucket then bucket = {}; self._knowledge[observer_id] = bucket end
  return bucket
end

function KnowledgeStore:set(observer_id, event_id, confidence, opts)
  opts = opts or {}
  local bucket = self:_bucket(observer_id)
  local previous = bucket[event_id]
  local old_conf = previous and previous.confidence or 0
  local record = {
    observer_id = observer_id,
    event_id = event_id,
    confidence = util.clamp01(math.max(old_conf, confidence or 0)),
    source = opts.source ~= nil and opts.source or (previous and previous.source or nil),
    spin = opts.spin ~= nil and opts.spin or (previous and previous.spin or nil),
    updated_at = opts.time or 0,
  }
  bucket[event_id] = record
  return record
end

function KnowledgeStore:get(observer_id, event_id)
  local bucket = self._knowledge[observer_id]
  return bucket and bucket[event_id] or nil
end

function KnowledgeStore:confidence(observer_id, event_id)
  local record = self:get(observer_id, event_id)
  return record and record.confidence or 0
end

function KnowledgeStore:set_spin(observer_id, event_id, spin)
  local record = self:get(observer_id, event_id)
  if record then record.spin = spin end
end

function KnowledgeStore:decay(rate, minimum)
  rate = rate or 0.96
  minimum = minimum or 0.08
  for _, bucket in pairs(self._knowledge) do
    for event_id, record in pairs(bucket) do
      record.confidence = record.confidence * rate
      if record.confidence < minimum then bucket[event_id] = nil end
    end
  end
end

function KnowledgeStore:snapshot()
  return util.deep_copy(self._knowledge)
end

function KnowledgeStore:restore(data)
  self._knowledge = util.deep_copy(data or {})
end

function KnowledgeStore:clear()
  self._knowledge = {}
end

return KnowledgeStore
