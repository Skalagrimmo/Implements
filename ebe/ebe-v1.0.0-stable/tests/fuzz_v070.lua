local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local Runtime=require("ebe.runtime")
local PixelGen=require("ebe.integrations.pixelgen_v080")
local Util=require("ebe.util")

local bundle=PixelGen.load_file(root.."/demo/pixelgen_v080_runtime.lua")
local key="front:front_0:status"
local simulations=120
local suppressions=0
local holds=0
local publications=0
local root_checks=0

for i=1,simulations do
  local rt=Runtime.new({seed=7000+i})
  rt:add_agent({id="source",sector={0,2}})
  rt:add_agent({id="a",sector={5,4},trust={hub=1}})
  rt:add_agent({id="b",sector={5,4},trust={hub=1}})
  rt:ingest_pixelgen(bundle)
  rt:assign_local_observations()

  assert(rt.agents.source.beliefs[key],"fuzz source lacks belief")

  local suppress_b=(i%3==0)
  local hold_a=(i%4==0)
  local rules={}
  if suppress_b then
    rules[#rules+1]={
      id="suppress_b",match={target_id="b",key_prefix="front:"},action="suppress"
    }
  end
  if hold_a then
    rules[#rules+1]={
      id="hold_a",match={target_id="a",key_prefix="front:"},action="hold",
      priority=((i%5)-2)/4,hold_delay=.5
    }
  else
    rules[#rules+1]={
      id="publish_a",match={target_id="a",key_prefix="front:"},action="publish",
      priority=((i%5)-2)/4,confidence_multiplier=.75+.05*(i%5)
    }
  end

  rt:add_institution({
    id="hub",kind="printing_house",sector={2,2},
    policy={receive_delay=.1,broadcast_delay=.2,distortion=0,trust=1,acceptance_min=.1,rebroadcast_min=.1},
    editorial={agenda={["front:"]=((i%7)-3)/6},policy_log_capacity=16,rules=rules},
  })
  rt:subscribe_institution("hub","a",{trust=1})
  rt:subscribe_institution("hub","b",{trust=1})

  local rep=rt:report_to_institution("source","hub",key,{trust=1})
  local roots=#rep.lineage.origin_observation_ids
  rt:advance(.1)

  local log=rt.ecology.institutions.hub.policy_log
  assert(#log==2,"fuzz policy did not decide once per target")

  -- Drain even held messages.
  rt:advance(4)

  if suppress_b then
    assert(rt.agents.b.beliefs[key]==nil,"suppressed target received belief")
    suppressions=suppressions+1
  else
    assert(rt.agents.b.beliefs[key],"default publication vanished")
    assert(rt.agents.b.beliefs[key].source_count==roots,"default policy changed evidence roots")
    root_checks=root_checks+1
  end

  assert(rt.agents.a.beliefs[key],"target a never received publication/hold")
  assert(rt.agents.a.beliefs[key].source_count==roots,"policy changed a's evidence root count")
  root_checks=root_checks+1
  if hold_a then holds=holds+1 else publications=publications+1 end

  local snap=rt:snapshot()
  local restored=Runtime.restore(snap)
  assert(Util.canonical(restored:snapshot())==Util.canonical(snap),
    "v0.7 fuzz snapshot mismatch")
end

print(string.format(
  "EBE v0.7.0 policy fuzz passed: %d simulations, %d suppressions, %d holds, %d direct publications, %d root-lineage checks",
  simulations,suppressions,holds,publications,root_checks
))
