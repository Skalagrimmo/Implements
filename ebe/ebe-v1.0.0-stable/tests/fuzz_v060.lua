local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local Runtime=require("ebe.runtime")
local Observation=require("ebe.cognition.observation")

local function truth(v,msg) if not v then error(msg or "expected truthy") end end
local function eq(a,b,msg)
  if a~=b then error((msg or "values differ")..": "..tostring(a).." ~= "..tostring(b)) end
end

local simulations=120
local publications=0
local echo_reports=0
local independent_consensus=0

for seed=1,simulations do
  local rt=Runtime.new({seed=6000+seed})
  rt:add_agent({id="a",sector={0,0},faction="f",trust={relay=1,council=1}})
  rt:add_agent({id="b",sector={0,1},faction="f",trust={council=1}})
  rt:add_agent({id="relay",sector={2,2},faction="f",trust={a=1,council=1}})
  rt:add_agent({id="target",sector={3,3},faction="f",trust={council=1}})

  rt:add_collective({
    id="council",
    kind="faction_council",
    faction="f",
    members={"a","b","relay","target"},
    policy={
      acceptance_min=.1,
      consensus_min=.55,
      confidence_min=.45,
      min_independent_roots=2,
      publication_trust=1,
    },
  })

  local key="front:f"..tostring(seed)..":status"
  local value=(seed%3==0) and "active" or "tense"

  local oa=Observation.normalize({
    id="root_a_"..seed,
    subject_type="front",
    subject_id="f"..seed,
    sector={0,0},
    evidence="direct_local",
    confidence=.96,
    observer_id="a",
    fact={claims={{key=key,value=value}}},
  })
  rt:_deliver_observation("a",oa)
  local _,ok1=rt:submit_to_collective("a","council",key)
  truth(ok1,"first report rejected")

  -- Same root travels through relay and is submitted again.
  rt:connect_agents("a","relay",{delay=0,trust=1,distortion=0})
  rt:share("a","relay",key)
  rt:advance(0)
  truth(rt.agents.relay.beliefs[key],"relay did not receive root")
  local _,ok2=rt:submit_to_collective("relay","council",key)
  truth(ok2,"relay report rejected")
  echo_reports=echo_reports+1

  local c1=rt:get_collective_consensus("council",key)
  eq(c1.source_count,1,"echo manufactured root in fuzz")
  truth(c1.reporter_count>=2,"reporter diversity lost in fuzz")
  eq(c1.state,"tentative","echo manufactured collective consensus in fuzz")

  -- Independent second root agrees.
  local ob=Observation.normalize({
    id="root_b_"..seed,
    subject_type="front",
    subject_id="f"..seed,
    sector={0,1},
    evidence="direct_local",
    confidence=.94,
    observer_id="b",
    fact={claims={{key=key,value=value}}},
  })
  rt:_deliver_observation("b",ob)
  local _,ok3=rt:submit_to_collective("b","council",key)
  truth(ok3,"independent report rejected")

  local c2=rt:get_collective_consensus("council",key)
  truth(c2.source_count>=2,"independent roots collapsed in fuzz")
  eq(c2.state,"consensus","agreeing roots failed to reach consensus")
  independent_consensus=independent_consensus+1

  -- Membership alone is still not telepathy.
  truth(rt.agents.target.beliefs[key]==nil,"target learned collective state without publication")

  rt:subscribe_collective("council","target",{trust=1})
  local p=rt:publish_collective("council",key)
  eq(#p,1,"publication missing in fuzz")
  publications=publications+1
  local tb=rt.agents.target.beliefs[key]
  truth(tb and tb.value==value,"published consensus not received")
  truth(tb.source_count>=2,"publication dropped roots in fuzz")

  -- A contradictory duplicate of root A cannot create a third independent root.
  local contradictory=Observation.normalize({
    id="root_a_distorted_"..seed,
    subject_type="rumor",
    subject_id=key,
    sector={2,2},
    evidence="transmitted",
    confidence=.40,
    source_agent_id="a",
    provenance={origin_observation_ids={"root_a_"..seed}},
    fact={claims={{key=key,value=(value=="tense" and "active" or "tense")}}},
  })
  rt:_deliver_observation("relay",contradictory)
  -- Rebuild relay may still choose the stronger original value. We only assert
  -- that any later submission cannot invent a new root.
  local report=rt.agents.relay.beliefs[key] and rt:submit_to_collective("relay","council",key,{id="late_"..seed})
  local c3=rt:get_collective_consensus("council",key)
  truth(c3.source_count<=2,"distorted echo invented extra root")

  -- Snapshot must be stable.
  local snap=rt:snapshot()
  local restored=Runtime.restore(snap)
  eq(restored.collectives.council.consensus[key].source_count,c3.source_count,
    "snapshot changed collective root count")
end

print(string.format(
  "EBE v0.6.0 collective fuzz passed: %d simulations, %d echo reports, %d independent consensuses, %d publications",
  simulations,echo_reports,independent_consensus,publications
))
