local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local Runtime=require("ebe.runtime")
local PixelGen=require("ebe.integrations.pixelgen_v080")
local NetworkSynth=require("ebe.integrations.pixelgen_network_synth")
local Util=require("ebe.util")

local function truth(v,msg) if not v then error(msg or "expected truthy") end end
local function eq(a,b,msg)
  if a~=b then error((msg or "values differ")..": "..tostring(a).." ~= "..tostring(b)) end
end

local bundle=PixelGen.load_file(root.."/demo/pixelgen_v100_runtime.lua")
eq(bundle.version,"0.8.0","PixelGen 1.0 changed frozen EBE bundle schema unexpectedly")
eq((((bundle.source or {}).world or {}).generator or {}).version,"1.0.0",
   "fixture is not from PixelGen 1.0")

local validation=PixelGen.validate(bundle)
eq(validation.dynamic_entities,11,"unexpected PixelGen 1.0 dynamic entity count")
eq(validation.events,3,"unexpected PixelGen 1.0 event count")
eq(validation.observations,13,"unexpected PixelGen 1.0 observation count")

local rt=Runtime.new({seed=1000})
rt:add_agent({id="mara",sector={0,2},faction="watch"})
rt:add_agent({id="iva",sector={0,3},faction="watch"})
local imported=rt:ingest_pixelgen(bundle)
eq(imported.entities,11,"PixelGen 1.0 entity ingestion changed")
eq(imported.events,3,"PixelGen 1.0 event ingestion changed")
eq(imported.observations,13,"PixelGen 1.0 observation ingestion changed")
truth(rt:assign_local_observations()>=2,"PixelGen 1.0 local evidence assignment failed")

local key="front:front_0:status"
truth(rt.agents.mara.beliefs[key],"PixelGen 1.0 evidence did not form Mara belief")
truth(rt.agents.iva.beliefs[key],"PixelGen 1.0 evidence did not form Iva belief")

-- The full PixelGen 1.0 world remains valid input for the v0.5 network layer.
local world=dofile(root.."/demo/pixelgen_v100_network.lua")
local plan1=NetworkSynth.synthesize(world,{allow_gated=true,allow_secret=false})
local plan2=NetworkSynth.synthesize(world,{allow_gated=true,allow_secret=false})
local errors=NetworkSynth.validate_plan(plan1,world)
eq(#errors,0,"PixelGen 1.0 network plan invalid")
eq(plan1.fingerprint,plan2.fingerprint,"PixelGen 1.0 network synthesis lost determinism")
eq(plan1.summary.institution_count,14,"PixelGen 1.0 canonical institution count changed")
eq(plan1.summary.route_count,16,"PixelGen 1.0 canonical route count changed")
eq(plan1.summary.component_count,1,"PixelGen 1.0 canonical network disconnected")
eq(plan1.summary.accessible_sector_count,30,"PixelGen 1.0 network access incomplete")
eq((world.cols or 0)*(world.rows or 0),30,"PixelGen 1.0 network sector count wrong")

-- v0.6 collective layer consumes the same evidence without changing ownership.
rt:add_collective({
  id="watch_council",
  faction="watch",
  members={"mara","iva"},
  policy={acceptance_min=.2,consensus_min=.55,confidence_min=.45,min_independent_roots=2},
})
rt:submit_to_collective("mara","watch_council",key)
rt:submit_to_collective("iva","watch_council",key)
local c=rt:get_collective_consensus("watch_council",key)
truth(c and c.source_count>=2,"PixelGen 1.0 evidence roots were lost in collective layer")
eq(c.state,"consensus","PixelGen 1.0 independent roots failed collective consensus")

-- Frozen bridge version is explicit: a future bundle version must not be guessed compatible.
local future=Util.deepcopy(bundle)
future.version="0.9.0"
local ok=pcall(function() PixelGen.validate(future) end)
truth(not ok,"future PixelGen bridge schema was silently accepted")

print("EBE v0.6.0 PixelGen 1.0 stable-contract compatibility test passed")
