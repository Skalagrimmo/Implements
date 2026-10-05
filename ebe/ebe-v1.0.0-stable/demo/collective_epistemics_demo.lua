local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local EBE=require("ebe")
local rt=EBE.Runtime.new({seed=6060})
local bundle=EBE.PixelGenV080.load_file(root.."/demo/pixelgen_v100_runtime.lua")

rt:add_agent({id="mara",sector={0,2},faction="watch",trust={oles=1}})
rt:add_agent({id="iva",sector={0,3},faction="watch"})
rt:add_agent({id="oles",sector={5,4},faction="watch",trust={mara=1}})
rt:add_agent({id="levko",sector={5,4},faction="watch",trust={watch_council=1}})

rt:ingest_pixelgen(bundle)
rt:assign_local_observations()

local key="front:front_0:status"
rt:add_collective({
  id="watch_council",
  kind="faction_council",
  faction="watch",
  members={"mara","iva","oles","levko"},
  policy={acceptance_min=.2,consensus_min=.60,confidence_min=.50,min_independent_roots=2,publication_trust=1},
})

local function show(label)
  local c=rt:get_collective_consensus("watch_council",key)
  local lb=rt.agents.levko.beliefs[key]
  print(label)
  if c then
    print(string.format(
      "  collective: value=%s confidence=%.3f roots=%d reporters=%d state=%s",
      tostring(c.value),c.confidence,c.source_count,c.reporter_count,c.state
    ))
  else
    print("  collective: no record")
  end
  if lb then
    print(string.format(
      "  Levko: belief=%s confidence=%.3f roots=%d knowledge=%s",
      tostring(lb.value),lb.confidence,lb.source_count,
      rt.agents.levko.knowledge[key] and "yes" or "no"
    ))
  else
    print("  Levko: no belief")
  end
end

show("Initial")

rt:submit_to_collective("mara","watch_council",key)
show("After Mara reports")

rt:connect_agents("mara","oles",{delay=0,trust=1,distortion=0})
rt:share("mara","oles",key)
rt:advance(0)
rt:submit_to_collective("oles","watch_council",key)
show("After Oles repeats Mara's evidence")

rt:submit_to_collective("iva","watch_council",key)
show("After independent Iva report")

rt:subscribe_collective("watch_council","levko",{trust=1})
rt:publish_collective("watch_council",key)
show("After explicit council publication")

local summary=rt:summary()
print(string.format(
  "Summary: tick=%.1f agents=%d collectives=%d collective_reports=%d beliefs=%d knowledge=%d",
  summary.tick,summary.agents,summary.collectives,summary.collective_reports,summary.beliefs,summary.knowledge
))
