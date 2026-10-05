local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path
local EBE=require("ebe")
local Util=require("ebe.util")
local Contract=EBE.PersistenceContract
local Snapshot=EBE.Snapshot

local sims=tonumber(arg[2]) or 160
local hostile_rejects,roundtrips,migrations=0,0,0
for seed=1,sims do
  local rt=EBE.Runtime.new({seed=seed,actions={log_capacity=64}})
  local agent_count=1+(seed%4)
  for i=1,agent_count do
    rt:add_agent({id="a"..i,sector={(seed+i)%7,(seed*3+i)%7},faction=(i%2==0 and "north" or "south")})
  end
  local count=1+(seed%5)
  for i=1,count do
    local actor="a"..(1+((i-1)%agent_count))
    if (seed+i)%3==0 then
      local req=rt:request_action({domain="pixelgen_world_event",action_type="territory_alert",actor_id=actor,target_type="territory",target_id="territory_"..(seed%5),amount=0.05+((seed+i)%5)*0.05,origin_observation_ids={"obs_"..seed.."_"..i}})
      rt:export_pixelgen_action(req.id)
      if (seed+i)%2==0 then rt:resolve_action_request(req.id,"rejected",{reason="fuzz"}) end
    else
      local req=rt:request_action({domain="agent_intent",action_type="wait",actor_id=actor,origin_observation_ids={"obs_"..seed.."_"..i,"obs_"..seed.."_"..i}})
      if i%2==0 then rt:resolve_action_request(req.id,"applied",{local_only=true}) end
    end
  end
  rt:advance((seed%7)/10)
  local snap=rt:snapshot()
  assert(Contract.validate_snapshot(snap))
  local encoded=Snapshot.to_json(snap)
  local decoded=Snapshot.from_json(encoded)
  assert(Util.canonical(decoded)==Util.canonical(snap),"JSON roundtrip mismatch seed "..seed)
  local restored=EBE.Runtime.restore(decoded)
  assert(Util.canonical(restored:snapshot())==Util.canonical(snap),"restore mismatch seed "..seed)
  roundtrips=roundtrips+1

  local legacy=Util.deepcopy(snap); legacy.version="0.8.0"; legacy.contract_version=nil
  local mig=Contract.migrate_snapshot(legacy)
  assert(mig.version=="1.0.0" and mig.contract_version=="1.0.0")
  migrations=migrations+1

  local h=Util.deepcopy(snap)
  local mode=seed%6
  if mode==0 then h.tick=math.huge
  elseif mode==1 then h.agents["a1"].sector={-1,0}
  elseif mode==2 then h.agents["a1"].id="other"
  elseif mode==3 and #h.action_gateway.order>0 then h.action_gateway.order[#h.action_gateway.order+1]=h.action_gateway.order[1]
  elseif mode==4 and #h.action_gateway.order>0 then local id=h.action_gateway.order[1]; h.action_gateway.requests[id].source_count=999
  else h.contract_version="9.9.9" end
  local ok=Contract.validate_snapshot(h)
  assert(not ok,"hostile mutation accepted seed "..seed.." mode "..mode)
  hostile_rejects=hostile_rejects+1
end
print(string.format("EBE v0.9.0 fuzz: %d simulations, %d roundtrips, %d migrations, %d hostile rejects PASS",sims,roundtrips,migrations,hostile_rejects))
