local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local EBE=require("ebe")
local PixelGen=EBE.PixelGenV080

local bundle=PixelGen.load_file(root.."/demo/pixelgen_v080_runtime.lua")
local rt=EBE.Runtime.new({seed=4040,ecology={max_hops=8}})

rt:add_agent({id="mara",sector={0,2},trust={levko=.95}})
rt:add_agent({id="iva",sector={0,3},trust={levko=.95}})
rt:add_agent({id="levko",sector={5,4},trust={mara=.95,iva=.95,print_house=.95,caravan=.85}})
rt:add_agent({id="oles",sector={4,4},trust={levko=.9}})

rt:ingest_pixelgen(bundle)
rt:assign_local_observations()

rt:add_institution({id="print_house",kind="printing_house",sector={2,2},policy={distortion=0}})
rt:add_institution({id="caravan",kind="caravan_exchange",sector={4,3},policy={distortion=0}})
rt:subscribe_institution("print_house","caravan")
rt:subscribe_institution("caravan","levko")

local key="front:front_0:status"

local function line(id)
  local a=rt.agents[id]
  local b=a.beliefs[key]
  local k=a.knowledge[key]
  if not b then return id..": no belief / no knowledge" end
  return string.format(
    "%s: belief=%s conf=%.3f roots=%d reporters=%d knowledge=%s",
    id,tostring(b.value),b.confidence,b.source_count or 0,b.reporter_count or 0,
    k and (tostring(k.value).." ["..k.basis.."]") or "no"
  )
end

local function advance(dt,label)
  rt:advance(dt)
  print(string.format("[t=%.2f] %s",rt.tick,label or ""))
end

print("=== EBE v0.4.0 — Information Ecology / Institutional Networks ===")
print("")
print("Initial epistemic state:")
print("  "..line("mara"))
print("  "..line("iva"))
print("  "..line("levko"))
print("")
print("Network:")
print("  Mara -> Printing House -> Caravan Exchange -> Levko")
print("  Iva  -> Printing House -> Caravan Exchange -> Levko")
print("")

local r1=rt:report_to_institution("mara","print_house",key)
print("Mara submits "..r1.id.." to Printing House")
advance(.5,"Printing House receives and archives Mara's report")
advance(.75,"Printing House dispatches toward Caravan")
advance(1.5,"Caravan receives and archives")
advance(2.5,"Caravan delivers to Levko")
print("  "..line("levko"))
print("")

rt:connect_agents("levko","oles",{delay=0,trust=1,distortion=0})
rt:connect_agents("oles","levko",{delay=0,trust=1,distortion=0})
rt:share("levko","oles",key); rt:advance(0)
rt:share("oles","levko",key); rt:advance(0)
print("After echo loop Levko -> Oles -> Levko:")
print("  "..line("levko"))
print("  source roots stay at 1: relaying one origin does not manufacture corroboration")
print("")

local r2=rt:report_to_institution("iva","print_house",key)
print("Iva independently submits "..r2.id)
advance(.5,"Printing House receives Iva's independent report")
advance(.75,"Printing House forwards it")
advance(1.5,"Caravan receives it")
advance(2.5,"Caravan delivers second root to Levko")
print("  "..line("levko"))
print("")

print("Institution archives:")
print("  print_house: "..#rt.ecology.institutions.print_house.archive_order)
print("  caravan:     "..#rt.ecology.institutions.caravan.archive_order)
print("Routing log entries: "..#rt.ecology.routing_log)
print("Queued institutional messages: "..#rt.ecology.queue)
print("")

for _,entry in ipairs(rt.agents.levko.memory:all()) do
  local p=entry.observation.provenance or {}
  if p.institution_id then
    local route={}
    for _,hop in ipairs(p.route or {}) do
      route[#route+1]=tostring(hop.id or hop.kind)
    end
    print(string.format(
      "Levko memory %s roots=%d hops=%d route=%s",
      entry.id,
      #(p.origin_observation_ids or {}),
      tonumber(p.hop_count) or 0,
      table.concat(route," -> ")
    ))
  end
end

print("")
local summary=rt:summary()
print(string.format(
  "Summary: tick=%.2f agents=%d institutions=%d beliefs=%d knowledge=%d ecology_queue=%d",
  summary.tick,summary.agents,summary.institutions,summary.beliefs,
  summary.knowledge,summary.queued_institution_messages
))
