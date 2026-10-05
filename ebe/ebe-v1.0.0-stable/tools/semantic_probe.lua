local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path
local EBE=require("ebe")
local Util=require("ebe.util")
local rt=EBE.Runtime.new({seed=7301,actions={log_capacity=64}})
rt:add_agent({id="mara",sector={0,2},faction="watch",trust={iva=0.9}})
rt:add_agent({id="iva",sector={1,2},faction="watch",trust={mara=0.8}})
rt:add_agent({id="levko",sector={5,4},faction="civilian"})
rt:add_institution({id="press",kind="printing_house",sector={0,2}})
rt:set_institution_editorial_policy("press",{
  agenda={["front:"]=0.4},
  rules={{id="levko_priority",match={target_id="levko",key_prefix="front:"},action="publish",priority=0.8}},
})
rt:subscribe_institution("press","levko",{})
rt:add_collective({id="watch_council",kind="council",faction="watch",members={"mara","iva"}})
local a=rt:request_action({domain="agent_intent",action_type="wait",actor_id="mara",origin_observation_ids={"obs_2","obs_1","obs_1"}})
rt:resolve_action_request(a.id,"applied",{local_only=true})
local w=rt:request_action({domain="pixelgen_world_event",action_type="territory_alert",actor_id="iva",target_type="territory",target_id="territory_0",amount=0.2,origin_observation_ids={"obs_3"}})
rt:export_pixelgen_action(w.id)
rt.action_gateway:correlate_pixelgen_bundle(rt,{events={{id="derived_1",cause_event_id=w.id,event_type="territory_state_changed",subject_type="territory",subject_id="territory_0",revision=1}}})
rt:advance(0.5)
local s=rt:snapshot()
s.version=nil; s.contract_version=nil
if s.action_gateway then
  s.action_gateway.version=nil
  for _,req in pairs(s.action_gateway.requests or {}) do req.version=nil end
end
print("semantic_hash="..tostring(Util.stable_hash(s)))
print("actions="..tostring(#(s.action_gateway.order or {})))
print("agents="..tostring(#Util.sorted_keys(s.agents or {})))
print("institutions="..tostring(#Util.sorted_keys((s.ecology or {}).institutions or {})))
print("collectives="..tostring(#Util.sorted_keys(s.collectives or {})))
