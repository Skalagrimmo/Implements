local util = require("ebe.core.util")
local MemoryStore = {}
MemoryStore.__index = MemoryStore

function MemoryStore.new()
  return setmetatable({ _records = {} }, MemoryStore)
end

function MemoryStore:_bucket(owner)
  local bucket = self._records[owner]
  if not bucket then bucket = {}; self._records[owner] = bucket end
  return bucket
end

function MemoryStore:remember(owner, key, value, time, metadata)
  time = time or 0
  metadata = metadata or {}
  local bucket = self:_bucket(owner)
  local old = bucket[key]
  local merged = {}
  if old and old.metadata then for k, v in pairs(old.metadata) do merged[k] = v end end
  for k, v in pairs(metadata) do merged[k] = v end
  local record = {
    owner = owner,
    key = key,
    value = util.deep_copy(value),
    created_at = old and old.created_at or time,
    updated_at = time,
    metadata = merged,
  }
  bucket[key] = record
  return record
end

function MemoryStore:recall(owner, key)
  local bucket = self._records[owner]
  return bucket and bucket[key] or nil
end

function MemoryStore:list(owner)
  local out = {}
  local bucket = self._records[owner] or {}
  for _, record in pairs(bucket) do out[#out + 1] = record end
  return out
end

function MemoryStore:snapshot()
  return util.deep_copy(self._records)
end

function MemoryStore:restore(data)
  self._records = util.deep_copy(data or {})
end

function MemoryStore:clear()
  self._records = {}
end

return MemoryStore
