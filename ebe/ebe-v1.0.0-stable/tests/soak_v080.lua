local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path
local Runtime=require("ebe.runtime")

local rt=Runtime.new({seed=8181,actions={default_reaction_intents=false},bus_history_limit=128})
rt:add_agent({id="a",sector={0,0}})
local n=1200
for i=1,n do
  local req=rt:request_action({
    domain=(i%3==0) and "pixelgen_world_event" or "agent_intent",
    action_type=(i%3==0) and "territory_alert" or "wait",
    actor_id="a",
    target_type=(i%3==0) and "territory" or nil,
    target_id=(i%3==0) and "territory_0" or nil,
    amount=(i%3==0) and .01 or nil,
    origin_observation_ids={"root_"..tostring((i-1)%17)},
  })
  if req.domain=="pixelgen_world_event" then
    rt:export_pixelgen_action(req.id)
    if i%2==0 then rt:resolve_action_request(req.id,"applied",{revision=i})
    else rt:resolve_action_request(req.id,"rejected",{reason="soak"}) end
  end
end
assert(#rt.action_gateway.order==n,"soak request count mismatch")
assert(#rt.action_gateway.log<=rt.action_gateway.log_capacity,"action log exceeded bound")
local snap=rt:snapshot()
local restored=Runtime.restore(snap)
assert(#restored.action_gateway.order==n,"soak restore lost requests")
print(string.format("EBE v0.8.0 action soak: %d requests PASS",n))
print(string.format("bounded_action_log=%d",#rt.action_gateway.log))
