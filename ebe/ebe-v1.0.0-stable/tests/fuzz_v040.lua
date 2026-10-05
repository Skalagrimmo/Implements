local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local Runtime=require("ebe.runtime")
local PixelGen=require("ebe.integrations.pixelgen_v080")

local bundle=PixelGen.load_file(root.."/demo/pixelgen_v080_runtime.lua")
local key="front:front_0:status"

local cases=0
local institutional_deliveries=0

for seed=1,120 do
  local rt=Runtime.new({seed=seed,ecology={max_hops=7}})
  rt:add_agent({id="a",sector={0,2},trust={far=.9}})
  rt:add_agent({id="b",sector={0,3},trust={far=.9}})
  rt:add_agent({id="far",sector={5,4},trust={press=.92,caravan=.82,a=.9,b=.9}})
  rt:add_agent({id="echo",sector={4,4},trust={far=.9}})

  rt:ingest_pixelgen(bundle)
  rt:assign_local_observations()
  assert(rt.agents.far.beliefs[key]==nil,"far agent starts omniscient")

  rt:add_institution({id="press",kind="printing_house",policy={distortion=(seed%4)*.01}})
  rt:add_institution({id="caravan",kind="caravan_exchange",policy={distortion=(seed%5)*.02}})
  rt:subscribe_institution("press","caravan")
  rt:subscribe_institution("caravan","far")
  if seed%3==0 then rt:subscribe_institution("caravan","press") end

  rt:report_to_institution("a","press",key)

  -- Progress enough for press + caravan route.
  rt:advance(0.5)
  rt:advance(0.75)
  rt:advance(1.5)
  rt:advance(2.5)
  rt:advance(10)

  assert(#rt.ecology.queue==0,"institution queue failed to drain")
  assert(#rt.ecology.routing_log<80,"routing loop exploded")

  local first=rt.agents.far.beliefs[key]
  assert(first,"far agent never received institutional report")
  assert(first.source_count==1,"single lineage became multiple origins")

  -- Echo path cannot add an independent root.
  rt:connect_agents("far","echo",{delay=0,trust=1,distortion=0})
  rt:connect_agents("echo","far",{delay=0,trust=1,distortion=0})
  rt:share("far","echo",key); rt:advance(0)
  rt:share("echo","far",key); rt:advance(0)
  assert(rt.agents.far.beliefs[key].source_count==1,"echo manufactured independent evidence")

  -- Independent witness via same institutions must add a new root.
  rt:report_to_institution("b","press",key)
  rt:advance(0.5)
  rt:advance(0.75)
  rt:advance(1.5)
  rt:advance(2.5)
  rt:advance(10)

  local final=rt.agents.far.beliefs[key]
  local roots={}
  for _,option in pairs(final.alternatives or {}) do
    for _,root_id in ipairs(option.origin_observation_ids or {}) do
      roots[root_id]=true
    end
  end
  local root_count=0
  for _ in pairs(roots) do root_count=root_count+1 end
  assert(root_count>=2,"independent witness roots did not survive institution route")
  assert(final.confidence>=0 and final.confidence<=1,"belief confidence out of bounds")

  for _,entry in ipairs(rt.agents.far.memory:all()) do
    local p=entry.observation.provenance or {}
    if p.institution_id then
      assert(type(p.origin_observation_ids)=="table" and #p.origin_observation_ids>=1,
        "institutional evidence lost root lineage")
      assert((p.hop_count or 0)<=9,"institution hop count escaped bound")
      institutional_deliveries=institutional_deliveries+1
    end
  end

  cases=cases+1
end

print(string.format(
  "EBE v0.4.0 ecology fuzz passed: %d simulations, %d institutional evidence memories",
  cases,institutional_deliveries
))
