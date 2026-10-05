local root = (... and ... ~= "") and ... or "."
package.path =
  root .. "/?.lua;" ..
  root .. "/?/init.lua;" ..
  package.path

local Runtime = require("ebe.runtime")
local Snapshot = require("ebe.persistence.snapshot")
local Util = require("ebe.util")
local PixelGen = require("ebe.integrations.pixelgen_v080")

local function truth(v,msg)
  if not v then error(msg or "expected truthy value") end
end
local function eq(a,b,msg)
  if a ~= b then error((msg or "values differ") .. ": " .. tostring(a) .. " ~= " .. tostring(b)) end
end

local bundle_path = root .. "/demo/pixelgen_v080_runtime.lua"
local bundle = PixelGen.load_file(bundle_path)
eq(bundle.contract.global_knowledge,"forbidden","fixture does not forbid global knowledge")
eq(bundle.contract.observation_semantics,"local evidence only","fixture observation contract changed")

local rt=Runtime.new({seed=3030})
rt:add_agent({
  id="mara",
  sector={0,2},
  trust={levko=0.9,iva=0.95},
  biases={threat_sensitivity=1.1},
})
rt:add_agent({
  id="iva",
  sector={0,3},
  trust={mara=0.95,levko=0.9},
  biases={},
})
rt:add_agent({
  id="levko",
  sector={5,4},
  trust={mara=0.95,iva=0.95},
  biases={skepticism=0.05},
})

rt:connect_agents("mara","levko",{delay=2,trust=0.95,distortion=0})
rt:connect_agents("iva","levko",{delay=3,trust=0.95,distortion=0})

local imported=rt:ingest_pixelgen(bundle)
eq(imported.observations,13,"unexpected PixelGen observation count")
truth(#Util.sorted_keys(rt.available_observations)==13,"observations were not staged")
truth(rt.entities.territory_0 and rt.entities.territory_0.static,"static territory entity missing")
truth(rt.entities.territory_0.dynamic,"dynamic territory state missing")
truth(rt.entities.territory_0.static.center,"static territory geometry/identity was overwritten")
truth(rt.entities.territory_0.dynamic.control_strength~=nil,"dynamic territory state was overwritten")

-- Ingestion alone must NOT assign knowledge/memory to anyone.
eq(#rt.agents.mara.memory.order,0,"ingestion manufactured Mara memory")
eq(#rt.agents.levko.memory.order,0,"ingestion manufactured Levko memory")

local delivered=rt:assign_local_observations()
truth(delivered >= 2,"local observations were not assigned")

local key="front:front_0:status"
truth(rt:get_belief("mara",key),"Mara missed local front evidence")
eq(rt:get_belief("mara",key).value,"tense","Mara interpreted wrong front state")
truth(rt:get_knowledge("mara",key),"Mara direct evidence did not become knowledge")

truth(rt:get_belief("iva",key),"Iva missed local front evidence")
truth(rt:get_belief("levko",key)==nil,"far-away Levko got omniscient belief")
truth(rt:get_knowledge("levko",key)==nil,"far-away Levko got omniscient knowledge")
eq(#rt.agents.levko.memory.order,0,"far-away Levko got direct memory")

-- Direct evidence triggers a reaction locally.
local mara_reacted=false
for _,r in ipairs(rt.reaction_log) do
  if r.agent_id=="mara" and r.kind=="avoid_front" then mara_reacted=true end
end
truth(mara_reacted,"direct tense-front belief did not produce Mara reaction")

-- Mara tells Levko; delayed propagation means no instant belief.
local tx1=rt:share("mara","levko",key)
eq(tx1.deliver_at,2,"wrong first rumor delivery time")
truth(rt:get_belief("levko",key)==nil,"rumor arrived instantly")

rt:advance(1)
truth(rt:get_belief("levko",key)==nil,"rumor ignored transmission delay")

rt:advance(1)
local levko_belief=rt:get_belief("levko",key)
truth(levko_belief,"delayed rumor never reached Levko")
eq(levko_belief.value,"tense","undistorted rumor changed value")
truth(rt:get_knowledge("levko",key)==nil,"single rumor incorrectly became Levko knowledge")

-- A second independent local witness corroborates the report later.
local tx2=rt:share("iva","levko",key)
eq(tx2.deliver_at,5,"wrong second rumor delivery time")
rt:advance(3)
truth(rt:get_belief("levko",key),"Levko lost corroborated belief")
truth(rt:get_knowledge("levko",key),"independent corroboration did not become knowledge")
eq(rt:get_knowledge("levko",key).basis,"corroborated_reports","wrong knowledge basis")

-- Provenance survives the rumor path.
local found_provenance=false
for _,entry in ipairs(rt.agents.levko.memory:all()) do
  local p=entry.observation.provenance or {}
  if p.transmission_id and p.source_agent_id then found_provenance=true end
end
truth(found_provenance,"rumor provenance was lost")

-- Duplicate PixelGen import is idempotent for evidence/events.
local memory_before=#rt.agents.mara.memory.order
local imported_again=rt:ingest_pixelgen(bundle)
eq(imported_again.events,0,"duplicate PixelGen events were imported twice")
eq(imported_again.observations,0,"duplicate PixelGen observations were imported twice")
rt:assign_local_observations()
eq(#rt.agents.mara.memory.order,memory_before,"duplicate import duplicated agent memory")

-- Runtime snapshot / restore keeps the semantic state.
local snap=rt:snapshot()
local snap_path=root .. "/tests/_runtime_snapshot.lua"
Snapshot.write_lua(snap_path,snap)
local loaded=Snapshot.read_lua(snap_path)
local restored=Runtime.restore(loaded)
eq(Util.canonical(restored:snapshot()),Util.canonical(snap),"snapshot restore changed runtime semantics")
os.remove(snap_path)

print("EBE v0.3.0 PixelGen v0.8 runtime bridge tests passed")
