local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path
local Runtime=require("ebe.runtime")
local PixelGen=require("ebe.integrations.pixelgen_v080")
local Util=require("ebe.util")

local bundle=PixelGen.load_file(root.."/demo/pixelgen_v080_runtime.lua")
local sims,requests,exports,rejects,correlated=160,0,0,0,0
local key="front:front_0:status"

for seed=1,sims do
  local rt=Runtime.new({seed=8000+seed,actions={default_reaction_intents=false}})
  rt:add_agent({id="a",sector={0,2}})
  rt.reaction:register({
    id="r"..seed,
    match=function(agent,b) return b.key==key and b.confidence>.5 end,
    build=function(agent,b,tick) return {kind="world_req",agent_id=agent.id,tick=tick,claim_key=b.key,believed_value=b.value,confidence=b.confidence} end,
  })
  local kinds={"front_escalation","front_deescalation"}
  local action_type=kinds[(seed%2)+1]
  rt:register_reaction_action_adapter("world_req",{
    domain="pixelgen_world_event",action_type=action_type,target_from_claim=true,
    amount=.01+(seed%20)/100,
  })
  rt:ingest_pixelgen(bundle)
  rt:assign_local_observations()
  local list=rt:action_requests("pending","pixelgen_world_event")
  assert(#list==1,"fuzz action request missing")
  local req=list[1]; requests=requests+1
  assert(req.source_count>=1,"fuzz request lost roots")
  local ev=rt:export_pixelgen_action(req.id); exports=exports+1
  assert(ev.id==req.id and ev.target_id=="front_0","fuzz export malformed")
  if seed%4==0 then
    rt:resolve_action_request(req.id,"rejected",{reason="fuzz"}); rejects=rejects+1
  else
    local result={
      version="0.8.0",source={world_seed=7301,world_dimensions={6,5},state_revision=10+seed},
      contract={global_knowledge="forbidden",observation_semantics="local evidence only"},
      static_entities={},dynamic_entities={},observations={},
      events={{id="d"..seed,revision=10+seed,event_type="front_state_changed",subject_type="front",subject_id="front_0",sector={0,2},changes={},cause_event_id=req.id}},
    }
    local imported=rt:ingest_pixelgen(result)
    assert(imported.action_results==1,"fuzz correlation failed")
    correlated=correlated+1
  end
  local snap=rt:snapshot()
  local restored=Runtime.restore(snap)
  assert(Util.canonical(snap)==Util.canonical(restored:snapshot()),"fuzz snapshot mismatch")
end

print(string.format("EBE v0.8.0 action fuzz: %d simulations PASS",sims))
print(string.format("requests=%d exports=%d rejected=%d applied=%d",requests,exports,rejects,correlated))
