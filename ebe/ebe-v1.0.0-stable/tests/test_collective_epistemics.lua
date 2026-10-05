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
local rt=Runtime.new({seed=6060})

rt:add_agent({id="mara",sector={0,2},faction="watch",trust={oles=1}})
rt:add_agent({id="iva",sector={0,3},faction="watch"})
rt:add_agent({id="oles",sector={5,4},faction="watch",trust={mara=1}})
rt:add_agent({id="levko",sector={5,4},faction="watch",trust={watch_council=.95,print_house=.9}})
rt:add_agent({id="outsider",sector={4,4},faction="none",trust={print_house=.9}})

rt:ingest_pixelgen(bundle)
rt:assign_local_observations()

local key="front:front_0:status"
truth(rt.agents.mara.beliefs[key],"Mara lacks direct evidence")
truth(rt.agents.iva.beliefs[key],"Iva lacks direct evidence")
truth(rt.agents.levko.beliefs[key]==nil,"Levko started omniscient")

local c=rt:add_collective({
  id="watch_council",
  kind="faction_council",
  faction="watch",
  members={"mara","iva","oles","levko"},
  policy={
    acceptance_min=.2,
    consensus_min=.60,
    confidence_min=.50,
    min_independent_roots=2,
    publication_trust=.95,
  },
})
truth(c:is_member("mara"),"Mara not enrolled")
truth(c:is_member("levko"),"Levko not enrolled")

-- One direct witness enters collective memory.
local r1,accepted1=rt:submit_to_collective("mara","watch_council",key)
truth(accepted1,"Mara report rejected")
local g1=rt:get_collective_consensus("watch_council",key)
truth(g1,"collective consensus record missing")
eq(g1.value,"tense","collective selected wrong value")
eq(g1.source_count,1,"one root became multiple roots")
eq(g1.reporter_count,1,"wrong initial reporter count")
eq(g1.state,"tentative","one root should remain tentative")
truth(rt.agents.levko.beliefs[key]==nil,"membership created telepathic belief")

-- Relay the same root through a second reporter.
rt:connect_agents("mara","oles",{delay=0,trust=1,distortion=0})
rt:share("mara","oles",key)
rt:advance(0)
truth(rt.agents.oles.beliefs[key],"Oles did not receive Mara relay")
local r2,accepted2=rt:submit_to_collective("oles","watch_council",key)
truth(accepted2,"Oles relay report rejected")
local echoed=rt:get_collective_consensus("watch_council",key)
eq(echoed.source_count,1,"echo manufactured an independent collective root")
eq(echoed.reporter_count,2,"collective lost immediate reporter diversity")
eq(echoed.state,"tentative","echo manufactured collective corroboration")
truth(rt.agents.levko.beliefs[key]==nil,"collective consensus leaked to member without publication")

-- Iva is an independent direct witness.
local r3,accepted3=rt:submit_to_collective("iva","watch_council",key)
truth(accepted3,"Iva report rejected")
local corroborated=rt:get_collective_consensus("watch_council",key)
truth(corroborated.source_count>=2,"independent root was lost")
truth(corroborated.reporter_count>=3,"reporter count did not retain relays")
eq(corroborated.state,"consensus","two agreeing independent roots did not form consensus")
truth(corroborated.confidence>=.5,"collective confidence unexpectedly low")
truth(rt.agents.levko.beliefs[key]==nil,"collective consensus auto-installed member belief")

-- Publication is explicit.
rt:subscribe_collective("watch_council","levko",{trust=1})
local pubs=rt:publish_collective("watch_council",key)
eq(#pubs,1,"wrong publication count")
local levko=rt.agents.levko.beliefs[key]
truth(levko,"explicit collective publication did not reach Levko")
eq(levko.value,"tense","collective publication changed value")
truth(levko.source_count>=2,"publication lost independent evidence roots")
truth(rt.agents.levko.knowledge[key],"corroborated collective publication did not support knowledge")

-- Collective can explicitly publish into the institution graph too.
rt:add_institution({
  id="print_house",
  kind="printing_house",
  sector={2,2},
  policy={
    receive_delay=.2,
    broadcast_delay=.2,
    distortion=0,
    trust=1,
    acceptance_min=.1,
    rebroadcast_min=.1,
  },
})
rt:subscribe_institution("print_house","outsider",{delay=.2,trust=1,distortion=0})
rt:subscribe_collective("watch_council","print_house",{trust=1})
local pubs2=rt:publish_collective("watch_council",key,{"print_house"})
eq(#pubs2,1,"collective->institution publication missing")
truth(rt.agents.outsider.beliefs[key]==nil,"institution publication arrived too early")
rt:advance(.2)
rt:advance(.2)
truth(rt.agents.outsider.beliefs[key],"collective publication did not traverse institution graph")
truth(rt.agents.outsider.beliefs[key].source_count>=2,
  "institution relay lost collective root lineage")

-- Non-members cannot submit when members_only_submit is enabled.
local ok=pcall(function()
  rt:submit_to_collective("outsider","watch_council",key)
end)
truth(not ok,"non-member submission bypassed collective policy")

-- Auto-enroll by faction changes membership, not knowledge.
local auto=rt:add_collective({
  id="watch_archive",
  kind="faction_archive",
  faction="watch",
  metadata={auto_enroll_faction=true},
})
truth(auto:is_member("mara"),"auto-enroll missed existing faction member")
truth(auto:is_member("levko"),"auto-enroll missed Levko")
local new_watch=rt:add_agent({id="new_watch",sector={5,4},faction="watch"})
truth(auto:is_member("new_watch"),"auto-enroll missed later faction member")
truth(new_watch.beliefs[key]==nil,"auto-enroll created knowledge")


-- Contradictory independent roots remain explicit rather than being averaged away.
local Collective=require("ebe.social.collective")
local conflict=Collective.new({
  id="conflict_test",
  policy={acceptance_min=.1,consensus_min=.60,confidence_min=.50,min_independent_roots=2},
})
truth(conflict:archive_report({
  id="c1",reporter_id="a",confidence=.9,
  claim={key="x",value="tense"},
  lineage={origin_observation_ids={"root_a"},route={},hop_count=0},
}),"conflict report c1 rejected")
truth(conflict:archive_report({
  id="c2",reporter_id="b",confidence=.9,
  claim={key="x",value="active"},
  lineage={origin_observation_ids={"root_b"},route={},hop_count=0},
}),"conflict report c2 rejected")
local cx=conflict:get_consensus("x")
eq(cx.total_independent_root_count,2,"conflicting roots not retained")
eq(cx.source_count,1,"one alternative incorrectly claimed both conflicting roots")
eq(cx.conflicting_root_count,1,"conflict metric wrong")
eq(cx.state,"tentative","split evidence should not become consensus")
truth(conflict:archive_report({
  id="c3",reporter_id="echo",confidence=.7,
  claim={key="x",value=cx.value},
  lineage={origin_observation_ids={cx.origin_observation_ids[1]},route={},hop_count=0},
}),"echo conflict report rejected")
local cx2=conflict:get_consensus("x")
eq(cx2.total_independent_root_count,2,"echo invented a third root in conflict case")
truth(cx2.reporter_count>=2,"same-root reporter diversity was lost")

-- Snapshot/restore preserves collectives and derived consensus deterministically.
local snapshot=rt:snapshot()
local restored=Runtime.restore(snapshot)
eq(Util.canonical(restored:snapshot()),Util.canonical(snapshot),
  "collective snapshot restore mismatch")
truth(restored.collectives.watch_council,"collective not restored")
eq(restored.collectives.watch_council.consensus[key].source_count,
   rt.collectives.watch_council.consensus[key].source_count,
   "collective roots changed on restore")

-- v0.5 snapshots remain loadable and acquire an empty collective layer.
local legacy=Util.deepcopy(snapshot)
legacy.version="0.5.0"
legacy.collectives=nil
legacy.collective_log=nil
local migrated=Runtime.restore(legacy)
eq(migrated.version,"1.0.0","v0.5 snapshot did not migrate")
eq(#Util.sorted_keys(migrated.collectives),0,"v0.5 snapshot invented collectives")

print("EBE v0.6.0 collective epistemics tests passed")
