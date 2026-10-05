local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local EBE=require("ebe")
local Util=require("ebe.util")
local Synth=EBE.PixelGenNetworkSynth

local base=Synth.load_world(root.."/demo/pixelgen_world_network_7301.lua")
local cases=0
local total_institutions=0
local total_routes=0
local disconnected=0
local traffic_total=0

local function mutate_world(seed)
  local w=Util.deepcopy(base)

  -- Deterministically thin optional landmarks/front watches to exercise sparse worlds.
  local placements={}
  for i,p in ipairs(w.landmark_system.placements or {}) do
    if p.scope=="world" or ((i+seed)%4~=0) then placements[#placements+1]=p end
  end
  w.landmark_system.placements=placements

  local sites={}
  for i,s in ipairs(w.territory_graph.front_sites or {}) do
    if (i+seed)%3~=0 then sites[#sites+1]=s end
  end
  w.territory_graph.front_sites=sites

  -- Occasionally close one public edge pair. Synthesis should become a valid forest
  -- rather than inventing a path through a sealed link.
  if seed%6==0 then
    local target_x=(seed/6)%5
    for _,sector in ipairs(w.sectors) do
      if sector.sy==2 and sector.sx==target_x then
        local e=sector.links and sector.links.E
        if e then e.gameplay.state="sealed" end
      end
      if sector.sy==2 and sector.sx==target_x+1 then
        local west=sector.links and sector.links.W
        if west then west.gameplay.state="sealed" end
      end
    end
  end

  return w
end

for seed=1,120 do
  local world=mutate_world(seed)
  local opts={
    allow_gated=(seed%2==0),
    allow_secret=(seed%5==0),
    front_watches=(seed%7~=0),
    target_degree=1+(seed%2),
    max_degree=2+(seed%2),
    max_route_cost=(seed%9==0) and 5.5 or 99,
  }

  local p1=Synth.synthesize(world,opts)
  local p2=Synth.synthesize(world,opts)
  assert(Util.canonical(p1)==Util.canonical(p2),"synthesis nondeterminism seed "..seed)
  local errors=Synth.validate_plan(p1,world)
  assert(#errors==0,"invalid synthesized plan seed "..seed..": "..table.concat(errors,"; "))
  assert(p1.summary.institution_count>=1,"synthesis produced no institutions")
  assert(p1.summary.route_count<=p1.summary.candidate_count,"route count exceeds candidate count")
  if not opts.allow_secret then
    for _,r in ipairs(p1.routes) do assert((r.access_states.secret or 0)==0,"secret route escaped policy") end
  end

  total_institutions=total_institutions+p1.summary.institution_count
  total_routes=total_routes+p1.summary.route_count
  if p1.summary.component_count>1 then disconnected=disconnected+1 end

  -- Runtime application + snapshot roundtrip for every variant.
  local rt=EBE.Runtime.new({seed=5000+seed,ecology={max_hops=6}})
  rt:add_agent({id="a",sector={0,2}})
  rt:add_agent({id="b",sector={5,4}})
  rt:synthesize_pixelgen_network(world,{
    allow_gated=opts.allow_gated,
    allow_secret=opts.allow_secret,
    front_watches=opts.front_watches,
    target_degree=opts.target_degree,
    max_degree=opts.max_degree,
    max_route_cost=opts.max_route_cost,
    attach_existing_agents=true,
  })

  local key="test:network:signal"
  rt:_deliver_observation("a",{
    id="fuzz_root_"..seed,
    source_event_id="fuzz_event_"..seed,
    subject_type="signal",subject_id="network",
    sector={0,2},evidence="direct_local",confidence=.96,
    fact={claims={{key=key,value="active"}}},
    provenance={origin_observation_ids={"fuzz_root_"..seed}},
  })
  if rt:local_institution("a") then
    rt:report_to_local_network("a",key)
    for _=1,160 do rt:advance(.25) end
    assert(#rt.ecology.queue==0,"ecology queue did not drain seed "..seed)
    assert(#rt.ecology.routing_log<1200,"routing traffic exploded seed "..seed)
    traffic_total=traffic_total+#rt.ecology.routing_log
  end

  local snap=rt:snapshot()
  local restored=EBE.Runtime.restore(snap)
  assert(Util.canonical(restored:snapshot())==Util.canonical(snap),"snapshot mismatch seed "..seed)
  cases=cases+1
end

print(string.format(
  "EBE v0.5.0 network synthesis fuzz passed: %d variants, avg institutions %.2f, avg routes %.2f, disconnected forests %d, routing log entries %d",
  cases,total_institutions/cases,total_routes/cases,disconnected,traffic_total
))
