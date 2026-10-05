local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local Runtime=require("ebe.runtime")
local PixelGen=require("ebe.integrations.pixelgen_v080")
local Util=require("ebe.util")

local function truth(v,msg) if not v then error(msg or "expected truthy") end end
local function eq(a,b,msg)
  if a~=b then error((msg or "values differ")..": "..tostring(a).." ~= "..tostring(b)) end
end

local bundle=PixelGen.load_file(root.."/demo/pixelgen_v080_runtime.lua")
local rt=Runtime.new({seed=4040,ecology={max_hops=8}})

rt:add_agent({id="mara",sector={0,2},trust={levko=.95,oles=.9}})
rt:add_agent({id="iva",sector={0,3},trust={levko=.95}})
rt:add_agent({id="levko",sector={5,4},trust={mara=.95,iva=.95,oles=.9,print_house=.95,caravan=.85}})
rt:add_agent({id="oles",sector={4,4},trust={levko=.9}})

rt:ingest_pixelgen(bundle)
rt:assign_local_observations()

local key="front:front_0:status"
truth(rt.agents.mara.beliefs[key],"Mara lacks direct evidence")
truth(rt.agents.iva.beliefs[key],"Iva lacks direct evidence")
truth(rt.agents.levko.beliefs[key]==nil,"Levko started omniscient")

rt:add_institution({
  id="print_house",
  kind="printing_house",
  sector={2,2},
  policy={distortion=0},
})
rt:add_institution({
  id="caravan",
  kind="caravan_exchange",
  sector={4,3},
  policy={distortion=0},
})

rt:subscribe_institution("print_house","caravan")
rt:subscribe_institution("caravan","levko")

-- Mara's direct evidence enters the institutional route.
local report1=rt:report_to_institution("mara","print_house",key)
truth(report1.lineage and #report1.lineage.origin_observation_ids>=1,"Mara report lost evidence roots")

-- receive at print_house
rt:advance(0.5)
eq(#rt.ecology.institutions.print_house.archive_order,1,"printing house did not archive report")
truth(rt.agents.levko.beliefs[key]==nil,"institution broadcast arrived too early")

-- print_house -> caravan
rt:advance(0.75)
truth(rt.agents.levko.beliefs[key]==nil,"caravan route arrived too early")

-- caravan receive
rt:advance(1.5)
eq(#rt.ecology.institutions.caravan.archive_order,1,"caravan did not archive forwarded report")

-- caravan -> Levko
rt:advance(2.5)
local b1=rt.agents.levko.beliefs[key]
truth(b1,"Levko never received institutional report")
eq(b1.value,"tense","undistorted institutional route changed claim")
eq(b1.source_count,1,"single evidence root counted as multiple confirmations")
truth(rt.agents.levko.knowledge[key]==nil,"single institutional lineage became knowledge")
truth(b1.reporter_count>=1,"institution reporter identity missing")

-- Route provenance contains institutions.
local institution_route_ok=false
for _,entry in ipairs(rt.agents.levko.memory:all()) do
  local route=(entry.observation.provenance or {}).route or {}
  local saw_print,saw_caravan=false,false
  for _,hop in ipairs(route) do
    if hop.id=="print_house" then saw_print=true end
    if hop.id=="caravan" then saw_caravan=true end
  end
  if saw_print and saw_caravan then institution_route_ok=true end
end
truth(institution_route_ok,"institution route provenance was lost")

-- Echo chamber: Levko -> Oles -> Levko must not manufacture a second root.
rt:connect_agents("levko","oles",{delay=0,trust=1,distortion=0})
rt:connect_agents("oles","levko",{delay=0,trust=1,distortion=0})

rt:share("levko","oles",key)
rt:advance(0)
truth(rt.agents.oles.beliefs[key],"Oles did not receive Levko relay")
rt:share("oles","levko",key)
rt:advance(0)

local echoed=rt.agents.levko.beliefs[key]
eq(echoed.source_count,1,"echo loop manufactured independent corroboration")
truth(rt.agents.levko.knowledge[key]==nil,"echo loop manufactured knowledge")

-- Iva is an independent direct witness: second root can legitimately corroborate.
local report2=rt:report_to_institution("iva","print_house",key)
truth(report2.id~=report1.id,"institution reports reused id")
rt:advance(0.5)
rt:advance(0.75)
rt:advance(1.5)
rt:advance(2.5)

local b2=rt.agents.levko.beliefs[key]
truth(b2.source_count>=2,"independent witness root was not preserved")
truth(rt.agents.levko.knowledge[key],"independent institutional corroboration did not become knowledge")
eq(rt.agents.levko.knowledge[key].basis,"corroborated_reports","wrong knowledge basis")

-- Non-subscribed agents are not globally broadcast to.
local outsider=rt:add_agent({id="outsider",sector={5,4}})
truth(outsider.beliefs[key]==nil,"new outsider inherited global institution knowledge")

-- A cyclic institutional subscription is safe: lineage prevents endless recirculation.
rt:subscribe_institution("caravan","print_house")
local queued_before=#rt.ecology.queue
rt:advance(20)
truth(#rt.ecology.queue==0,"institution cycle did not terminate")
truth(#rt.ecology.routing_log < 100,"institution cycle exploded routing log")

-- Snapshot/restore preserves institutional state.
local snapshot=rt:snapshot()
local restored=Runtime.restore(snapshot)
eq(Util.canonical(restored:snapshot()),Util.canonical(snapshot),"ecology snapshot restore mismatch")
eq(#restored.ecology.institutions.print_house.archive_order,
   #rt.ecology.institutions.print_house.archive_order,
   "institution archive not restored")

-- v0.3 runtime snapshots remain loadable; they simply start with an empty ecology.
local legacy_snapshot=Util.deepcopy(snapshot)
legacy_snapshot.version="0.3.0"
legacy_snapshot.ecology=nil
local migrated=Runtime.restore(legacy_snapshot)
eq(migrated.version,"1.0.0","v0.3 snapshot did not migrate to current runtime")
eq(#Util.sorted_keys(migrated.ecology.institutions),0,"v0.3 snapshot invented institutions")

print("EBE v0.4.0 information ecology / source-lineage tests passed")
