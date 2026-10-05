local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local Runtime=require("ebe.runtime")
local PixelGen=require("ebe.integrations.pixelgen_v080")
local Util=require("ebe.util")
local ActionRequest=require("ebe.action.action_request")

local function truth(v,msg) if not v then error(msg or "expected truthy") end end
local function eq(a,b,msg) if a~=b then error((msg or "values differ")..": "..tostring(a).." ~= "..tostring(b)) end end

-- Direct validation and strict PixelGen event mapping.
local normalized=ActionRequest.normalize({
  id="manual",
  domain="pixelgen_world_event",
  action_type="territory_alert",
  actor_id="mara",
  target_type="territory",
  target_id="territory_0",
  amount=.2,
  origin_observation_ids={"root_b","root_a","root_a"},
},{})
eq(normalized.source_count,2,"action lineage did not deduplicate roots")
local pg=ActionRequest.to_pixelgen_event(normalized)
eq(pg.id,"manual","PixelGen event id must preserve action request id")
eq(pg.event_type,"territory_alert","wrong PixelGen event type")
eq(pg.cause_id,"manual","manual action cause must default to request id")

local bundle=PixelGen.load_file(root.."/demo/pixelgen_v080_runtime.lua")
local rt=Runtime.new({seed=8080})
rt:add_agent({id="mara",sector={0,2}})
rt:ingest_pixelgen(bundle)
rt:assign_local_observations()

local key="front:front_0:status"
truth(rt.agents.mara.beliefs[key],"Mara lacks front belief")

-- v0.8 default: old reaction produces a semantic local intent, not world mutation.
local intents=rt:action_requests(nil,"agent_intent")
truth(#intents>=1,"reaction did not produce default local semantic intent")
local avoid=nil
for _,req in ipairs(intents) do if req.action_type=="avoid_front" then avoid=req end end
truth(avoid,"avoid_front local intent missing")
eq(avoid.target_type,"front","claim target type not derived")
eq(avoid.target_id,"front_0","claim target id not derived")
eq(avoid.source_count,rt.agents.mara.beliefs[key].source_count,"action request lost evidence lineage")

-- A declarative adapter can make a reaction request a PixelGen world event.
local rt2=Runtime.new({seed=8081,actions={default_reaction_intents=false}})
rt2:add_agent({id="mara",sector={0,2}})
rt2.reaction:register({
  id="request_deescalation",
  match=function(agent,belief)
    return belief.key==key and (belief.value=="tense" or belief.value=="volatile") and belief.confidence>.5
  end,
  build=function(agent,belief,tick)
    return {kind="request_front_deescalation",agent_id=agent.id,tick=tick,claim_key=belief.key,believed_value=belief.value,confidence=belief.confidence}
  end,
})
rt2:register_reaction_action_adapter("request_front_deescalation",{
  domain="pixelgen_world_event",
  action_type="front_deescalation",
  target_from_claim=true,
  amount=.12,
  metadata={reason="belief_driven_deescalation"},
})
rt2:ingest_pixelgen(bundle)
rt2:assign_local_observations()
local world_actions=rt2:action_requests("pending","pixelgen_world_event")
eq(#world_actions,1,"expected exactly one world action request")
local req=world_actions[1]
eq(req.target_id,"front_0","world action target id wrong")
eq(req.action_type,"front_deescalation","world action type wrong")
truth(req.source_reaction_id,"reaction provenance missing")
eq(req.source_count,rt2.agents.mara.beliefs[key].source_count,"world action lineage lost")

local event=rt2:export_pixelgen_action(req.id)
eq(event.id,req.id,"export must preserve action request id")
eq(event.actor_id,"mara","export actor missing")
eq(rt2:action_request(req.id).status,"exported","request did not enter exported state")
local event2=rt2:export_pixelgen_action(req.id)
eq(Util.canonical(event2),Util.canonical(event),"re-export is not idempotent")

-- Explicit authority rejection is supported and idempotent.
local manual=rt2:request_action({
  domain="pixelgen_world_event",action_type="territory_alert",actor_id="mara",
  target_type="territory",target_id="territory_0",amount=.1,
})
rt2:resolve_action_request(manual.id,"rejected",{reason="authority_policy"})
eq(rt2:action_request(manual.id).status,"rejected","request was not rejected")
local _,changed=rt2:resolve_action_request(manual.id,"rejected",{reason="authority_policy"})
eq(changed,false,"same terminal resolution must be idempotent")

-- PixelGen derived event correlation resolves exported request as applied.
local result_bundle={
  version="0.8.0",
  source={world_seed=7301,world_dimensions={6,5},state_revision=4},
  contract={global_knowledge="forbidden",observation_semantics="local evidence only"},
  static_entities={},dynamic_entities={},observations={},
  events={{
    id="derived_from_action",revision=4,event_type="front_state_changed",
    subject_type="front",subject_id="front_0",sector={0,2},changes={},
    cause_event_id=req.id,observability="local_or_transmitted",
  }},
}
local imported=rt2:ingest_pixelgen(result_bundle)
eq(imported.action_results,1,"PixelGen result was not correlated")
local applied=rt2:action_request(req.id)
eq(applied.status,"applied","exported request did not resolve as applied")
eq(applied.result.derived_event_id,"derived_from_action","derived event provenance missing")

-- Snapshot/restore preserves requests, adapters, terminal state and deterministic IDs.
local snap=rt2:snapshot()
local restored=Runtime.restore(snap)
eq(Util.canonical(restored:snapshot()),Util.canonical(snap),"v0.8 action snapshot restore mismatch")
local next_req=restored:request_action({domain="agent_intent",action_type="wait",actor_id="mara"})
truth(next_req.id~=req.id,"restored action sequence reused an id")

-- v0.7 snapshot migration creates an empty gateway without disturbing old state.
local legacy=Util.deepcopy(snap)
legacy.version="0.7.0"
legacy.action_gateway=nil
local migrated=Runtime.restore(legacy)
eq(migrated.version,"1.0.0","v0.7 snapshot did not migrate to v1.0")
eq(#migrated:action_requests(),0,"v0.7 migration invented historical action requests")

print("EBE v0.8.0 semantic action request tests passed")
