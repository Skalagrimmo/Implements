local util = require("ebe.core.util")
local sequence = 0
local M = {}

function M.create(input, now)
  now = now or 0
  assert(type(input) == "table", "event input must be a table")
  assert(type(input.type) == "string" and input.type ~= "", "event.type must be a non-empty string")
  sequence = sequence + 1
  local event_time = util.is_finite(input.time) and input.time or now
  return {
    id = input.id or string.format("evt-%d-%d", math.floor(now * 1000), sequence),
    type = input.type,
    actor = input.actor,
    subject = input.subject,
    target = input.target,
    time = event_time,
    location = util.deep_copy(input.location),
    metadata = util.deep_copy(input.metadata or {}),
    parent_id = input.parent_id or input.parentId,
    depth = (type(input.depth) == "number" and math.floor(input.depth) == input.depth) and input.depth or 0,
  }
end

return M
