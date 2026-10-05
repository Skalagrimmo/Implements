local Util = require("ebe.util")

local Event = {}
Event.__index = Event

function Event.new(kind, payload, meta)
  assert(type(kind) == "string" and kind ~= "", "event kind is required")
  payload = payload or {}
  meta = meta or {}

  local self = {
    id = meta.id,
    kind = kind,
    payload = Util.deepcopy(payload),
    tick = tonumber(meta.tick) or 0,
    source = meta.source or "runtime",
    actor_id = meta.actor_id,
    cause_id = meta.cause_id,
    sector = meta.sector and Util.deepcopy(meta.sector) or nil,
    tags = Util.deepcopy(meta.tags or {}),
    provenance = Util.deepcopy(meta.provenance or {}),
  }

  return setmetatable(self, Event)
end

function Event:plain()
  return {
    id = self.id,
    kind = self.kind,
    payload = Util.deepcopy(self.payload),
    tick = self.tick,
    source = self.source,
    actor_id = self.actor_id,
    cause_id = self.cause_id,
    sector = self.sector and Util.deepcopy(self.sector) or nil,
    tags = Util.deepcopy(self.tags),
    provenance = Util.deepcopy(self.provenance),
  }
end

return Event
