local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path
local EBE=require("ebe")
local rt=EBE.Runtime.new({seed=8080,actions={default_reaction_intents=false}})
local bundle=EBE.PixelGenV080.load_file(root.."/demo/pixelgen_v080_runtime.lua")
local key="front:front_0:status"
rt:add_agent({id="mara",sector={0,2}})
rt.reaction:register({
  id="request_deescalation",
  match=function(agent,b) return b.key==key and (b.value=="tense" or b.value=="volatile") and b.confidence>.5 end,
  build=function(agent,b,tick) return {kind="request_front_deescalation",agent_id=agent.id,tick=tick,claim_key=b.key,believed_value=b.value,confidence=b.confidence} end,
})
rt:register_reaction_action_adapter("request_front_deescalation",{
  domain="pixelgen_world_event",action_type="front_deescalation",target_from_claim=true,amount=.12,
})
rt:ingest_pixelgen(bundle)
rt:assign_local_observations()
local req=assert(rt:action_requests("pending","pixelgen_world_event")[1])
local ev=rt:export_pixelgen_action(req.id)
print("EBE v0.8.0 semantic action request demo")
print(string.format("belief: %s=%s confidence=%.3f roots=%d",key,tostring(rt.agents.mara.beliefs[key].value),rt.agents.mara.beliefs[key].confidence,rt.agents.mara.beliefs[key].source_count))
print(string.format("request: %s %s %s amount=%.2f status=%s",req.id,req.action_type,req.target_id,req.amount,rt:action_request(req.id).status))
print(string.format("PixelGen event: id=%s event_type=%s target=%s actor=%s cause=%s",ev.id,ev.event_type,ev.target_id,ev.actor_id,ev.cause_id))
print("No world mutation happened inside EBE; authority handoff is explicit.")
