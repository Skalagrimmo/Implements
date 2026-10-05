local root=arg[1]
local bundle_path=arg[2]
local snapshot_path=arg[3]
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path
local EBE=require("ebe")
local Snapshot=EBE.Snapshot
local bundle=EBE.PixelGenV080.load_file(bundle_path)
assert(#bundle.observations>0,"PixelGen bundle has no observations")
local sector=bundle.observations[1].sector
local rt=EBE.Runtime.new({seed=8082,actions={default_reaction_intents=false}})
rt:add_agent({id="mara",sector=sector})
rt.reaction:register({
  id="request_deescalation",
  match=function(agent,b)
    return b.key=="front:front_0:status" and (b.value=="tense" or b.value=="volatile") and b.confidence>.5
  end,
  build=function(agent,b,tick) return {kind="request_front_deescalation",agent_id=agent.id,tick=tick,claim_key=b.key,believed_value=b.value,confidence=b.confidence} end,
})
rt:register_reaction_action_adapter("request_front_deescalation",{
  domain="pixelgen_world_event",action_type="front_deescalation",target_from_claim=true,amount=.12,
})
rt:ingest_pixelgen(bundle)
rt:assign_local_observations()
local req=assert(rt:action_requests("pending","pixelgen_world_event")[1],"no action request")
local ev=rt:export_pixelgen_action(req.id)
Snapshot.write_lua(snapshot_path,rt:snapshot())
print("id="..ev.id)
print("event_type="..ev.event_type)
print("target_type="..ev.target_type)
print("target_id="..ev.target_id)
print("amount="..string.format("%.6f",ev.amount))
print("source="..ev.source)
print("actor_id="..ev.actor_id)
print("cause_id="..ev.cause_id)
