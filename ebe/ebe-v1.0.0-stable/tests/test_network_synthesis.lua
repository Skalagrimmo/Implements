local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local EBE=require("ebe")
local Util=require("ebe.util")
local Synth=EBE.PixelGenNetworkSynth

local function truth(v,msg) if not v then error(msg or "expected truthy") end end
local function eq(a,b,msg)
  if a~=b then error((msg or "values differ")..": "..tostring(a).." ~= "..tostring(b)) end
end

local world=Synth.load_world(root.."/demo/pixelgen_world_network_7301.lua")
local plan=Synth.synthesize(world,{allow_gated=true,allow_secret=false})
local plan2=Synth.synthesize(world,{allow_gated=true,allow_secret=false})

-- Canonical deterministic topology derived entirely from PixelGen world semantics.
eq(plan.version,"0.5.0","wrong synthesis version")
eq(Util.canonical(plan),Util.canonical(plan2),"network synthesis is not deterministic")
eq(Synth.fingerprint(plan),Synth.fingerprint(plan2),"network plan fingerprint changed")
eq(#Synth.validate_plan(plan,world),0,"canonical plan failed validation")

eq(plan.summary.institution_count,14,"canonical institution count changed")
eq(plan.summary.route_count,16,"canonical route count changed")
eq(plan.summary.component_count,1,"canonical information network disconnected")
eq(plan.summary.accessible_sector_count,30,"not all canonical sectors have institution access")
eq(plan.summary.kind_counts.printing_house,2,"printing landmark mapping changed")
eq(plan.summary.kind_counts.shrine_circle,5,"shrine mapping changed")
eq(plan.summary.kind_counts.front_watch,4,"front watch synthesis changed")
eq(plan.summary.kind_counts.roadside_relay,2,"roadside relay synthesis changed")
eq(plan.summary.kind_counts.caravan_exchange,1,"main-path caravan synthesis changed")
eq(plan.summary.role_counts.front_watch,5,"front-site role synthesis changed")
eq(plan.summary.role_counts.regional_hub,3,"regional role synthesis changed")
eq(plan.summary.role_counts.road_corridor,1,"main-path road-corridor role changed")

local inst_by_id={}
for _,inst in ipairs(plan.institutions) do
  truth(not inst_by_id[inst.id],"duplicate institution id")
  inst_by_id[inst.id]=inst
  truth(inst.metadata.generated_by=="pixelgen_network_synth","institution lost synthesis provenance")
end

-- Region centers that coincide with stronger landmark institutions are merged into roles.
local regional_roles=0
for _,inst in ipairs(plan.institutions) do
  if Util.list_contains(inst.metadata.roles,"regional_hub") then regional_roles=regional_roles+1 end
end
truth(regional_roles>=3,"regional hub roles were not preserved/merged")

for _,route in ipairs(plan.routes) do
  truth(inst_by_id[route.a] and inst_by_id[route.b],"route references unknown institution")
  truth(route.a~=route.b,"self route synthesized")
  truth(route.path_cost>=0,"negative route cost")
  truth(route.trust>=0 and route.trust<=1,"route trust out of bounds")
  truth(route.distortion>=0 and route.distortion<=1,"route distortion out of bounds")
  eq((route.access_states or {}).secret or 0,0,"secret path escaped default public-route policy")
  truth(Util.same_sector(route.path[1],inst_by_id[route.a].sector),"route path wrong start")
  truth(Util.same_sector(route.path[#route.path],inst_by_id[route.b].sector),"route path wrong end")
end

-- The same world can opt into secret infrastructure explicitly, but the plan remains valid.
local secret_plan=Synth.synthesize(world,{allow_gated=true,allow_secret=true})
eq(#Synth.validate_plan(secret_plan,world),0,"secret-enabled plan failed validation")

-- Apply plan to runtime and automatically attach existing agents to their nearest reachable node.
local mara_sector={0,2}
local mara_access=plan.sector_access["0,2"]
truth(mara_access,"Mara sector has no network access")
local neighbor_id=nil
for _,route in ipairs(plan.routes) do
  if route.a==mara_access.institution_id then neighbor_id=route.b break end
  if route.b==mara_access.institution_id then neighbor_id=route.a break end
end
truth(neighbor_id,"Mara access node has no network neighbor")
local receiver_sector=inst_by_id[neighbor_id].sector

local rt=EBE.Runtime.new({seed=5050,ecology={max_hops=8}})
rt:add_agent({id="mara",sector=Util.deepcopy(mara_sector)})
rt:add_agent({id="receiver",sector=Util.deepcopy(receiver_sector)})
rt:synthesize_pixelgen_network(world,{attach_existing_agents=true,allow_gated=true,allow_secret=false})

eq(rt.version,"1.0.0","runtime version did not upgrade")
truth(rt:local_institution("mara"),"Mara was not auto-attached")
eq(rt:local_institution("receiver"),neighbor_id,"receiver attached to wrong zero-cost institution")
eq(#Util.sorted_keys(rt.ecology.institutions),14,"runtime institution count changed")
eq(#rt.network_plan.routes,16,"runtime route plan missing")

-- Reapplying the same plan is idempotent, but silently replacing a live network is forbidden.
Synth.apply(rt,rt.network_plan,{attach_existing_agents=true})
local incompatible=Synth.synthesize(world,{allow_gated=true,allow_secret=false,front_watches=false})
local ok=pcall(function() Synth.apply(rt,incompatible,{}) end)
truth(not ok,"different live network plan was silently accepted")

-- Seed one local claim and let the synthesized PixelGen infrastructure carry it.
local key="front:front_0:status"
rt:_deliver_observation("mara",{
  id="auto_network_root_mara",
  source_event_id="synthetic_event",
  subject_type="front",
  subject_id="front_0",
  sector=Util.deepcopy(mara_sector),
  evidence="direct_local",
  confidence=.96,
  fact={claims={{key=key,value="tense"}}},
  provenance={origin_observation_ids={"auto_network_root_mara"}},
})
truth(rt.agents.mara.beliefs[key],"Mara did not form seed belief")

local report=rt:report_to_local_network("mara",key)
eq(report.institution_id,mara_access.institution_id,"report entered wrong local institution")
truth(report.provenance.ingress_route,"agent ingress route provenance missing")

for i=1,80 do rt:advance(.25) end
truth(#rt.ecology.queue==0,"synthesized network queue did not drain")
local received=rt.agents.receiver.beliefs[key]
truth(received,"neighbor institution failed to deliver report to attached receiver")
eq(received.source_count,1,"one root became multiple independent sources")

local route_provenance=false
for _,entry in ipairs(rt.agents.receiver.memory:all()) do
  local p=entry.observation.provenance or {}
  if p.route_edge and p.route_edge.access then
    for _,edge in ipairs(p.route_edges or {}) do
      if edge.route_id then route_provenance=true end
    end
  end
end
truth(route_provenance,"world-derived route provenance did not reach receiver memory")

-- Agent access follows movement instead of leaving stale subscriptions behind.
local old_access=rt:local_institution("receiver")
truth(rt.ecology.institutions[old_access].subscribers.receiver,"receiver missing old institution subscription")
rt:move_agent("receiver",{5,4})
local new_access=rt:local_institution("receiver")
truth(new_access,"moved receiver lost network access")
if new_access~=old_access then
  truth(rt.ecology.institutions[old_access].subscribers.receiver==nil,"stale institution subscription survived movement")
end
truth(rt.ecology.institutions[new_access].subscribers.receiver,"new institution subscription missing after movement")

-- Agents added after network synthesis are attached automatically too.
rt:add_agent({id="late_agent",sector={1,0}})
truth(rt:local_institution("late_agent"),"late-added agent was not auto-attached")

-- Dense bidirectional network is bounded by lineage dedupe + revisit protection.
truth(#rt.ecology.routing_log<200,"canonical auto-network exploded routing traffic")
local suppressed=0
for _,inst in pairs(rt.ecology.institutions) do
  suppressed=suppressed+(inst.duplicate_lineage_count or 0)
end
truth(suppressed>=0,"invalid duplicate-lineage metric")

-- Snapshot/restore preserves synthesized infrastructure and agent access.
local snap=rt:snapshot()
local restored=EBE.Runtime.restore(snap)
eq(Util.canonical(restored.network_plan),Util.canonical(rt.network_plan),"network plan lost on restore")
eq(Util.canonical(restored.agent_institution_access),Util.canonical(rt.agent_institution_access),"agent access lost on restore")
eq(Util.canonical(restored:snapshot()),Util.canonical(snap),"v0.5 runtime snapshot restore mismatch")

-- Old v0.4 snapshots remain accepted without synthesized-network fields.
local legacy=Util.deepcopy(snap)
legacy.version="0.4.0"
legacy.network_plan=nil
legacy.agent_institution_access=nil
local migrated=EBE.Runtime.restore(legacy)
eq(migrated.version,"1.0.0","v0.4 snapshot did not migrate")
truth(migrated.network_plan==nil,"v0.4 snapshot invented a network plan")

print("EBE v0.5.0 PixelGen automatic information-network synthesis tests passed")
