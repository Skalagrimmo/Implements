local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path
local EBE=require("ebe")
local Util=require("ebe.util")
local Contract=EBE.PersistenceContract
local Snapshot=EBE.Snapshot
local Json=EBE.Json

local sims=tonumber(arg[2]) or 240
local roundtrips,migrations,hostile_rejects,json_rejects=0,0,0,0
local versions={"0.3.0","0.4.0","0.5.0","0.6.0","0.7.0","0.8.0","0.9.0"}

for seed=1,sims do
  local rt=EBE.Runtime.new({seed=seed,actions={log_capacity=64}})
  local n=1+(seed%4)
  for i=1,n do rt:add_agent({id="a"..i,sector={(seed+i)%9,(seed*5+i)%9},faction=(i%2==0 and "north" or "south")}) end
  if seed%3==0 then
    rt:add_institution({id="press",kind="printing_house",sector={seed%9,(seed+1)%9}})
    rt:set_institution_editorial_policy("press",{agenda={["front:"]=0.2}})
  end
  if n>=2 and seed%4==0 then rt:add_collective({id="council",kind="council",faction="none",members={"a1","a2"}}) end
  local reqs=1+(seed%7)
  for i=1,reqs do
    local actor="a"..(1+((i-1)%n))
    if (seed+i)%3==0 then
      local req=rt:request_action({domain="pixelgen_world_event",action_type="territory_alert",actor_id=actor,target_type="territory",target_id="territory_"..(seed%11),amount=0.05+((seed+i)%5)*0.05,origin_observation_ids={"obs_"..seed.."_"..i}})
      rt:export_pixelgen_action(req.id)
      if (seed+i)%2==0 then rt:resolve_action_request(req.id,"rejected",{reason="fuzz"}) end
    else
      local req=rt:request_action({domain="agent_intent",action_type="wait",actor_id=actor,origin_observation_ids={"obs_"..seed.."_"..i,"obs_"..seed.."_"..i}})
      if i%2==0 then rt:resolve_action_request(req.id,"applied",{local_only=true}) end
    end
  end
  rt:advance((seed%11)/10)
  local snap=rt:snapshot()
  assert(Contract.validate_snapshot(snap))
  local text=Snapshot.to_json(snap)
  local decoded=Snapshot.from_json(text)
  assert(Util.canonical(decoded)==Util.canonical(snap),"JSON roundtrip mismatch seed "..seed)
  local restored=EBE.Runtime.restore(decoded)
  assert(Util.canonical(restored:snapshot())==Util.canonical(snap),"restore mismatch seed "..seed)
  roundtrips=roundtrips+1

  local legacy=Util.deepcopy(snap); legacy.version=versions[1+((seed-1)%#versions)]; legacy.contract_version=nil
  local migrated=Contract.migrate_snapshot(legacy)
  assert(migrated.version=="1.0.0" and migrated.contract_version=="1.0.0")
  migrations=migrations+1

  local h=Util.deepcopy(snap)
  local mode=seed%10
  if mode==0 then h.version="2.0.0"
  elseif mode==1 then h.tick=math.huge
  elseif mode==2 then h.agents.a1.sector={-1,0}
  elseif mode==3 then h.agents.a1.id="other"
  elseif mode==4 then h.action_gateway.version="9.9.9"
  elseif mode==5 and #h.action_gateway.order>0 then local id=h.action_gateway.order[1]; h.action_gateway.requests[id].version="9.9.9"
  elseif mode==6 then h.action_gateway.sequence=h.action_gateway.sequence+1
  elseif mode==7 and #h.action_gateway.log>1 then h.action_gateway.log_capacity=1
  elseif mode==8 and #h.action_gateway.order>0 then h.action_gateway.order[#h.action_gateway.order+1]=h.action_gateway.order[1]
  elseif #h.action_gateway.order>0 then local id=h.action_gateway.order[1]; h.action_gateway.requests[id].source_count=999
  else h.contract_version="9.9.9" end
  local ok=Contract.validate_snapshot(h)
  assert(not ok,"hostile snapshot accepted seed "..seed.." mode "..mode)
  hostile_rejects=hostile_rejects+1

  local bads={
    '{"x":1,"x":2}',
    '{"x":null}',
    '{"x":1e999}',
    '{"x":1} trailing',
    '{"x":"bad\\q"}',
    '{"x":[1,]}',
    '{x:1}',
    '{"x":"'..string.char(0xC0,0xAF)..'"}',
  }
  local bad=bads[1+((seed-1)%#bads)]
  assert(not pcall(Json.decode,bad),"hostile JSON accepted seed "..seed)
  json_rejects=json_rejects+1
end

print(string.format("EBE v1.0.0 fuzz: %d simulations, %d roundtrips, %d migrations, %d hostile snapshot rejects, %d hostile JSON rejects PASS",sims,roundtrips,migrations,hostile_rejects,json_rejects))
