local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path
local EBE=require("ebe")
local Util=require("ebe.util")
local Contract=EBE.PersistenceContract
local Snapshot=EBE.Snapshot

local n=tonumber(arg[2]) or 5000
local rt=EBE.Runtime.new({seed=10000,actions={log_capacity=512}})
rt:add_agent({id="mara",sector={0,0},faction="watch"})
rt:add_agent({id="iva",sector={1,0},faction="watch"})
rt:add_institution({id="press",kind="printing_house",sector={0,0},policy_log_capacity=128})
rt:set_institution_editorial_policy("press",{agenda={["front:"]=0.25}})
rt:add_collective({id="watch",kind="council",faction="watch",members={"mara","iva"}})

local checkpoints=0
for i=1,n do
  local actor=(i%2==0) and "mara" or "iva"
  if i%5==0 then
    local req=rt:request_action({domain="pixelgen_world_event",action_type="territory_alert",actor_id=actor,target_type="territory",target_id="territory_"..(i%29),amount=0.1,origin_observation_ids={"obs_"..i}})
    rt:export_pixelgen_action(req.id)
    if i%10==0 then rt:resolve_action_request(req.id,"rejected",{reason="soak"}) end
  else
    local req=rt:request_action({domain="agent_intent",action_type="wait",actor_id=actor,origin_observation_ids={"obs_"..i}})
    if i%3==0 then rt:resolve_action_request(req.id,"applied",{local_only=true}) end
  end
  if i%100==0 then rt:advance(0.01) end
  if i%500==0 then
    local snap=rt:snapshot()
    assert(Contract.validate_snapshot(snap))
    local text=Snapshot.to_json(snap)
    local restored=EBE.Runtime.restore(Snapshot.from_json(text))
    assert(Util.canonical(restored:snapshot())==Util.canonical(snap),"checkpoint restore mismatch at "..i)
    checkpoints=checkpoints+1
  end
end
local snap=rt:snapshot()
assert(Contract.validate_snapshot(snap))
assert(#snap.action_gateway.order==n,"request count mismatch")
assert(#snap.action_gateway.log<=512,"bounded action log overflow")
local text=Snapshot.to_json(snap)
local restored=EBE.Runtime.restore(Snapshot.from_json(text))
assert(Util.canonical(restored:snapshot())==Util.canonical(snap),"final soak restore mismatch")
print(string.format("EBE v1.0.0 soak: %d requests, %d checkpoints, %d-byte JSON, bounded action log %d PASS",n,checkpoints,#text,#snap.action_gateway.log))
