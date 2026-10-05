local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local Runtime=require("ebe.runtime")
local Observation=require("ebe.cognition.observation")
local Util=require("ebe.util")

local function truth(v,msg) if not v then error(msg or "expected truthy") end end
local function eq(a,b,msg)
  if a~=b then error((msg or "values differ")..": "..tostring(a).." ~= "..tostring(b)) end
end

local simulations=300
local consensus_cases=0
local conflict_cases=0
local institutional_publications=0
local total_reports=0

for seed=1,simulations do
  local rt=Runtime.new({seed=90000+seed})
  rt:add_agent({id="a",sector={0,0},faction="f",trust={relay=1,council=1}})
  rt:add_agent({id="b",sector={0,1},faction="f",trust={council=1}})
  rt:add_agent({id="relay",sector={1,1},faction="f",trust={a=1,council=1}})
  rt:add_agent({id="target",sector={2,2},faction="f",trust={council=1}})
  rt:add_agent({id="outside",sector={3,3},faction="none",trust={print_house=1}})

  rt:add_collective({
    id="council",
    kind="faction_council",
    faction="f",
    members={"a","b","relay","target"},
    policy={
      acceptance_min=.1,
      consensus_min=.60,
      confidence_min=.50,
      min_independent_roots=2,
      archive_capacity=16,
      publication_trust=1,
    },
  })

  local key="territory:t"..seed..":status"
  local va=(seed%4==0) and "pressured" or "stable"
  local vb=(seed%5==0) and (va=="stable" and "pressured" or "stable") or va

  local oa=Observation.normalize({
    id="root_a_"..seed,
    subject_type="territory",
    subject_id="t"..seed,
    sector={0,0},
    evidence="direct_local",
    confidence=.96,
    observer_id="a",
    fact={claims={{key=key,value=va}}},
  })
  rt:_deliver_observation("a",oa)
  rt:submit_to_collective("a","council",key)
  total_reports=total_reports+1

  -- Same evidence root through another reporter.
  rt:connect_agents("a","relay",{delay=0,trust=1,distortion=0})
  rt:share("a","relay",key)
  rt:advance(0)
  rt:submit_to_collective("relay","council",key)
  total_reports=total_reports+1

  local after_echo=rt:get_collective_consensus("council",key)
  eq(after_echo.source_count,1,"echo created a second root in soak")
  truth(after_echo.reporter_count>=2,"echo reporter diversity missing in soak")
  eq(after_echo.total_independent_root_count,1,"echo changed total root count")

  local ob=Observation.normalize({
    id="root_b_"..seed,
    subject_type="territory",
    subject_id="t"..seed,
    sector={0,1},
    evidence="direct_local",
    confidence=.94,
    observer_id="b",
    fact={claims={{key=key,value=vb}}},
  })
  rt:_deliver_observation("b",ob)
  rt:submit_to_collective("b","council",key)
  total_reports=total_reports+1

  local c=rt:get_collective_consensus("council",key)
  eq(c.total_independent_root_count,2,"independent roots not retained in soak")
  if va==vb then
    consensus_cases=consensus_cases+1
    eq(c.source_count,2,"agreeing roots not both counted")
    eq(c.state,"consensus","agreeing roots did not become consensus")
  else
    conflict_cases=conflict_cases+1
    eq(c.source_count,1,"conflicting alternatives merged roots")
    eq(c.conflicting_root_count,1,"conflict count wrong in soak")
    eq(c.state,"tentative","split roots became consensus")
  end

  -- Still no collective telepathy.
  truth(rt.agents.target.beliefs[key]==nil,"collective leaked to member in soak")
  rt:subscribe_collective("council","target",{trust=1})
  rt:publish_collective("council",key)
  local tb=rt.agents.target.beliefs[key]
  truth(tb,"explicit publication failed in soak")
  eq(tb.source_count,c.source_count,"publication altered winning root count")

  if seed%5==0 then
    rt:add_institution({
      id="print_house",kind="printing_house",sector={1,2},
      policy={receive_delay=0,broadcast_delay=0,trust=1,distortion=0,acceptance_min=.1,rebroadcast_min=.1},
    })
    rt:subscribe_institution("print_house","outside",{delay=0,trust=1,distortion=0})
    rt:subscribe_collective("council","print_house",{trust=1})
    rt:publish_collective("council",key,{"print_house"})
    rt:advance(0)
    truth(rt.agents.outside.beliefs[key],"collective->institution route failed in soak")
    eq(rt.agents.outside.beliefs[key].source_count,c.source_count,
      "institution route changed root lineage")
    institutional_publications=institutional_publications+1
  end

  -- Bounded archives stay bounded even with extra duplicate/echo reports.
  for n=1,20 do
    rt:submit_to_collective("a","council",key,{id="extra_"..seed.."_"..n})
    total_reports=total_reports+1
  end
  truth(#rt.collectives.council.report_order<=16,"collective archive exceeded capacity")

  local snap=rt:snapshot()
  local restored=Runtime.restore(snap)
  eq(Util.canonical(restored:snapshot()),Util.canonical(snap),
    "snapshot mismatch in collective soak")
end

print(string.format(
  "EBE v0.6.0 collective soak passed: %d simulations, %d consensus, %d conflicts, %d institution publications, %d submitted reports",
  simulations,consensus_cases,conflict_cases,institutional_publications,total_reports
))
