local M = {}
function M.eq(actual, expected, message)
  if actual ~= expected then error((message or "assertion failed") .. ": expected " .. tostring(expected) .. ", got " .. tostring(actual), 2) end
end
function M.ok(value, message)
  if not value then error(message or "assertion failed", 2) end
end
return M
