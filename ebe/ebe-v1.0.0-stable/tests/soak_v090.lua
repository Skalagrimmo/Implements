local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path
local EBE=require("ebe")
local Util=require("ebe.util")
local Contract=EBE.PersistenceContract
local Snapshot=EBE.Snapshot

local n=tonumber(arg[2]) or 2000
local rt=EBE.Runtime.new({seed=9001,actions={log_capacity=512}})
rt:add_agent({id="mara",sector={0,0},faction="watch"})
for i=1,n do
  local req
  if i%4==0 then
    req=rt:request_action({domain="pixelgen_world_event",action_type="territory_alert",actor_id="mara",target_type="territory",target_id="territory_"..(i%17),amount=0.1,origin_observation_ids={"obs_"..i}})
    rt:export_pixelgen_action(req.id)
    if i%8==0 then rt:resolve_action_request(req.id,"rejected",{reason="soak"}) end
  else
    req=rt:request_action({domain="agent_intent",action_type="wait",actor_id="mara",origin_observation_ids={"obs_"..i}})
    if i%3==0 then rt:resolve_action_request(req.id,"applied",{local_only=true}) end
  end
  if i%100==0 then rt:advance(0.01) end
end
local snap=rt:snapshot()
assert(Contract.validate_snapshot(snap))
assert(#snap.action_gateway.order==n,"request count mismatch")
assert(#snap.action_gateway.log<=512,"bounded action log overflow")
local text=Snapshot.to_json(snap)
local restored=EBE.Runtime.restore(Snapshot.from_json(text))
assert(Util.canonical(restored:snapshot())==Util.canonical(snap),"soak snapshot roundtrip mismatch")
print(string.format("EBE v0.9.0 persistence soak: %d requests, %d-byte JSON, bounded log %d PASS",n,#text,#snap.action_gateway.log))
