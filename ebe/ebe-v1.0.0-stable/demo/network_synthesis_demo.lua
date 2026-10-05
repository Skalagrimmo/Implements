local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local EBE=require("ebe")
local Util=require("ebe.util")
local Synth=EBE.PixelGenNetworkSynth

local world=Synth.load_world(root.."/demo/pixelgen_world_network_7301.lua")
local plan=Synth.synthesize(world,{allow_gated=true,allow_secret=false})

print("=== EBE v0.5.0 — PixelGen Automatic Information Network ===")
print(string.format(
  "World seed=%s size=%dx%d institutions=%d routes=%d components=%d access=%d/%d",
  tostring(world.seed),world.cols,world.rows,
  plan.summary.institution_count,plan.summary.route_count,
  plan.summary.component_count,plan.summary.accessible_sector_count,
  world.cols*world.rows
))
print("Plan fingerprint: "..Synth.fingerprint(plan))
print("")
print("Institution kinds:")
for _,kind in ipairs(Util.sorted_keys(plan.summary.kind_counts)) do
  print(string.format("  %-18s %d",kind,plan.summary.kind_counts[kind]))
end
print("")
print("Generated institutions:")
for _,inst in ipairs(plan.institutions) do
  print(string.format(
    "  %-16s %-16s sector=(%d,%d) roles=%s",
    inst.id,inst.kind,inst.sector[1],inst.sector[2],
    table.concat(inst.metadata.roles or {},",")
  ))
end
print("")
print("Route backbone:")
for _,route in ipairs(plan.routes) do
  print(string.format(
    "  %-13s %s -> %s cost=%.2f delay=%.2f trust=%.3f frontX=%d %s",
    route.id,route.a,route.b,route.path_cost,route.delay,route.trust,
    route.front_crossings or 0,route.reason
  ))
end

-- Demonstrate automatic agent access and one world-derived route.
local mara_access=plan.sector_access["0,2"]
local neighbor=nil
for _,route in ipairs(plan.routes) do
  if route.a==mara_access.institution_id then neighbor=route.b break end
  if route.b==mara_access.institution_id then neighbor=route.a break end
end
assert(neighbor,"canonical Mara node has no route")
local inst_by_id={}
for _,i in ipairs(plan.institutions) do inst_by_id[i.id]=i end

local rt=EBE.Runtime.new({seed=5050,ecology={max_hops=8}})
rt:add_agent({id="mara",sector={0,2}})
rt:add_agent({id="reader",sector=Util.deepcopy(inst_by_id[neighbor].sector)})
rt:synthesize_pixelgen_network(world,{attach_existing_agents=true})

local key="front:front_0:status"
rt:_deliver_observation("mara",{
  id="demo_root_mara",source_event_id="demo_event",
  subject_type="front",subject_id="front_0",sector={0,2},
  evidence="direct_local",confidence=.96,
  fact={claims={{key=key,value="tense"}}},
  provenance={origin_observation_ids={"demo_root_mara"}},
})

print("")
print("Automatic access:")
print("  Mara   -> "..tostring(rt:local_institution("mara")))
print("  Reader -> "..tostring(rt:local_institution("reader")))
local report=rt:report_to_local_network("mara",key)
print("Mara report enters: "..report.institution_id)

for _=1,80 do rt:advance(.25) end
local b=rt.agents.reader.beliefs[key]
print(string.format(
  "Reader after network propagation: belief=%s confidence=%.3f roots=%d",
  tostring(b and b.value),b and b.confidence or 0,b and b.source_count or 0
))
print("Queue drained: "..tostring(#rt.ecology.queue==0))
print("Routing log entries: "..#rt.ecology.routing_log)

local route_seen=false
for _,entry in ipairs(rt.agents.reader.memory:all()) do
  local p=entry.observation.provenance or {}
  if #(p.route_edges or {})>0 then
    route_seen=true
    print("World-route provenance:")
    for _,edge in ipairs(p.route_edges) do
      print(string.format(
        "  %s cost=%s front_crossings=%s path_cells=%d",
        tostring(edge.route_id),tostring(edge.path_cost),
        tostring(edge.front_crossings),#(edge.path or {})
      ))
    end
  end
end
print("Route provenance preserved: "..tostring(route_seen))
