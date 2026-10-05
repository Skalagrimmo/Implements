local Util = require("ebe.util")

local Synth = {}
Synth.VERSION = "0.5.0"

local LANDMARK_RULES = {
  printing_press_altar = { kind="printing_house", faction="print_civic" },
  nanolith_shrine = { kind="shrine_circle", faction="nano_signal" },
  silt_spire = { kind="shrine_circle", faction="silt_contamination",
    policy={ distortion=0.14, trust=0.78 } },
  mask_cross = { kind="roadside_relay", faction="none" },
}

local REGION_RULES = {
  ruined_settlement = { kind="settlement_square", faction="none" },
  reformed_chapel = { kind="printing_house", faction="print_civic" },
  dark_forest = { kind="shrine_circle", faction="none" },
  silt_marsh = { kind="settlement_square", faction="none" },
  frozen_pass = { kind="front_watch", faction="none" },
}

local LINK_COST = {
  open = 1.0,
  gated = 1.60,
  secret = 2.35,
}

local function clamp(v,lo,hi)
  if v<lo then return lo end
  if v>hi then return hi end
  return v
end

local function round(v,n)
  return Util.round(v,n or 4)
end

local function pos_key(pos)
  return tostring(pos[1])..","..tostring(pos[2])
end

local function edge_key(a,b)
  local ka,kb=pos_key(a),pos_key(b)
  if ka<kb then return ka.."|"..kb end
  return kb.."|"..ka
end

local function copy_pos(pos)
  return { tonumber(pos[1]) or 0, tonumber(pos[2]) or 0 }
end

local function sorted_positions(map)
  local result={}
  for _,v in pairs(map or {}) do result[#result+1]=v end
  table.sort(result,function(a,b)
    if a[2]==b[2] then return a[1]<b[1] end
    return a[2]<b[2]
  end)
  return result
end

local function sector_lookup(world)
  local out={}
  for _,s in ipairs(world.sectors or {}) do
    out[pos_key({s.sx,s.sy})]=s
  end
  return out
end

local function build_front_edge_set(world)
  local out={}
  for _,edge in ipairs(((world.influence_topology or {}).boundary_edges) or {}) do
    if edge.a and edge.b then out[edge_key(edge.a,edge.b)]=true end
  end
  return out
end

local function build_main_path_edge_set(world)
  local out={}
  local path=((world.gameplay or {}).main_path) or {}
  for i=1,#path-1 do
    out[edge_key(path[i],path[i+1])]=true
  end
  return out
end

local function build_sector_graph(world,opts)
  opts=opts or {}
  local allow_gated = opts.allow_gated ~= false
  local allow_secret = opts.allow_secret == true
  local lookup=sector_lookup(world)
  local graph={}
  local main_path_edges=build_main_path_edge_set(world)
  local main_path_discount=tonumber(opts.main_path_discount) or 0.78

  for key,s in pairs(lookup) do
    graph[key]=graph[key] or {}
    for _,dir in ipairs(Util.sorted_keys(s.links or {})) do
      local link=s.links[dir]
      local to=link and link.to
      local state=(((link or {}).gameplay or {}).state) or "open"
      local cost=LINK_COST[state]
      if state=="gated" and not allow_gated then cost=nil end
      if state=="secret" and not allow_secret then cost=nil end
      if state=="sealed" then cost=nil end
      if to and cost then
        local tk=pos_key(to)
        if lookup[tk] then
          local on_main_path=main_path_edges[edge_key({s.sx,s.sy},to)]==true
          local effective_cost=cost*(on_main_path and main_path_discount or 1.0)
          graph[key][#graph[key]+1]={
            to=tk,
            pos=copy_pos(to),
            cost=effective_cost,
            raw_cost=cost,
            state=state,
            main_path=on_main_path,
            gate_kind=((link.gameplay or {}).gate_kind),
          }
        end
      end
    end
    table.sort(graph[key],function(a,b)
      if a.cost==b.cost then return a.to<b.to end
      return a.cost<b.cost
    end)
  end
  return graph,lookup
end

local function dijkstra(graph,start_key,target_key)
  if start_key==target_key then
    local x,y=string.match(start_key,"^(-?%d+),(-?%d+)$")
    return 0,{{tonumber(x),tonumber(y)}},{open=0,gated=0,secret=0,main_path=0}
  end
  if not graph[start_key] or not graph[target_key] then return nil end

  local dist={[start_key]=0}
  local prev={}
  local prev_edge={}
  local visited={}

  while true do
    local best,best_dist=nil,math.huge
    for key,value in pairs(dist) do
      if not visited[key] and (value<best_dist or (value==best_dist and (best==nil or key<best))) then
        best,best_dist=key,value
      end
    end
    if not best then break end
    if best==target_key then break end
    visited[best]=true

    for _,edge in ipairs(graph[best] or {}) do
      local nd=best_dist+edge.cost
      local old=dist[edge.to]
      if old==nil or nd<old-1e-9 or (math.abs(nd-old)<=1e-9 and best<(prev[edge.to] or "~")) then
        dist[edge.to]=nd
        prev[edge.to]=best
        prev_edge[edge.to]=edge
      end
    end
  end

  if dist[target_key]==nil then return nil end

  local rev={target_key}
  local states={open=0,gated=0,secret=0,main_path=0}
  local cur=target_key
  while cur~=start_key do
    local e=prev_edge[cur]
    if not e then return nil end
    states[e.state]=(states[e.state] or 0)+1
    if e.main_path then states.main_path=states.main_path+1 end
    cur=prev[cur]
    rev[#rev+1]=cur
  end

  local path={}
  for i=#rev,1,-1 do
    local x,y=string.match(rev[i],"^(-?%d+),(-?%d+)$")
    path[#path+1]={tonumber(x),tonumber(y)}
  end
  return dist[target_key],path,states
end

local function add_role(spec,role,source)
  spec.metadata=spec.metadata or {}
  spec.metadata.roles=spec.metadata.roles or {}
  if not Util.list_contains(spec.metadata.roles,role) then
    spec.metadata.roles[#spec.metadata.roles+1]=role
    table.sort(spec.metadata.roles)
  end
  spec.metadata.sources=spec.metadata.sources or {}
  if source then spec.metadata.sources[#spec.metadata.sources+1]=Util.deepcopy(source) end
end

local function create_institutions(world,opts)
  opts=opts or {}
  local institutions={}
  local by_sector={}
  local counters={}

  local function make_id(prefix)
    counters[prefix]=(counters[prefix] or 0)+1
    return string.format("auto_%s_%02d",prefix,counters[prefix])
  end

  local function add(spec,role,source,merge_at_sector)
    local key=pos_key(spec.sector)
    if merge_at_sector and by_sector[key] then
      local existing=by_sector[key]
      add_role(existing,role,source)
      return existing
    end
    add_role(spec,role,source)
    institutions[#institutions+1]=spec
    if not by_sector[key] then by_sector[key]=spec end
    return spec
  end

  for _,placement in ipairs(((world.landmark_system or {}).placements) or {}) do
    local rule=LANDMARK_RULES[placement.kind]
    if rule and placement.sector then
      local spec={
        id=make_id("landmark"),
        kind=rule.kind,
        sector=copy_pos(placement.sector),
        faction=rule.faction or "none",
        policy=Util.deepcopy(rule.policy or {}),
        metadata={
          generated_by="pixelgen_network_synth",
          source_kind="landmark",
          landmark_kind=placement.kind,
          landmark_id=placement.id,
          landmark_scope=placement.scope,
          label=placement.map_label,
          semantic=placement.semantic,
        },
      }
      add(spec,"landmark_node",{
        type="landmark",id=placement.id,kind=placement.kind,
      },false)
    end
  end

  for _,region in ipairs(((world.geography or {}).regions) or {}) do
    if region.center then
      local rule=REGION_RULES[region.primary_biome] or {kind="settlement_square",faction="none"}
      local spec={
        id=make_id("region"),
        kind=rule.kind,
        sector=copy_pos(region.center),
        faction=rule.faction or "none",
        metadata={
          generated_by="pixelgen_network_synth",
          source_kind="region",
          region_id=region.id,
          region_name=region.name,
          primary_biome=region.primary_biome,
          sector_count=region.sector_count,
        },
      }
      add(spec,"regional_hub",{
        type="region",id=region.id,kind=region.primary_biome,
      },true)
    end
  end

  if opts.caravan_hubs ~= false then
    local main_path=((world.gameplay or {}).main_path) or {}
    local spacing=math.max(8,tonumber(opts.caravan_spacing) or 12)
    local count=math.floor(#main_path/spacing)
    if #main_path>=8 and count<1 then count=1 end
    for n=1,count do
      local target=math.floor(n*(#main_path+1)/(count+1)+0.5)
      local chosen=nil
      for radius=0,#main_path do
        local candidates={target-radius,target+radius}
        for _,idx in ipairs(candidates) do
          if idx>=1 and idx<=#main_path then
            local pos=main_path[idx]
            if pos and not by_sector[pos_key(pos)] then chosen=pos break end
          end
        end
        if chosen then break end
      end
      if chosen then
        local spec={
          id=make_id("caravan"),
          kind="caravan_exchange",
          sector=copy_pos(chosen),
          faction="none",
          metadata={
            generated_by="pixelgen_network_synth",
            source_kind="main_path",
            main_path_index=target,
            main_path_length=#main_path,
          },
        }
        add(spec,"road_corridor",{
          type="gameplay_main_path",id="main_path",kind="caravan_exchange",
        },false)
      end
    end
  end

  if opts.front_watches ~= false then
    for _,site in ipairs(((world.territory_graph or {}).front_sites) or {}) do
      if site.sector then
        local spec={
          id=make_id("front"),
          kind="front_watch",
          sector=copy_pos(site.sector),
          faction="none",
          metadata={
            generated_by="pixelgen_network_synth",
            source_kind="front_site",
            front_id=site.front_id,
            front_site_id=site.id,
            pair=Util.deepcopy(site.pair or {}),
            pressure=site.pressure,
          },
        }
        add(spec,"front_watch",{
          type="front",id=site.front_id,kind="front_watch",
        },true)
      end
    end
  end

  table.sort(institutions,function(a,b) return a.id<b.id end)
  return institutions
end

local function route_features(world,path,front_edges,main_edges,lookup)
  local features={
    front_crossings=0,
    region_crossings=0,
    transition_sectors=0,
    main_path_steps=0,
  }
  for _,pos in ipairs(path or {}) do
    local s=lookup[pos_key(pos)]
    if s and s.transition then features.transition_sectors=features.transition_sectors+1 end
  end
  for i=1,#(path or {})-1 do
    local a,b=path[i],path[i+1]
    if front_edges[edge_key(a,b)] then features.front_crossings=features.front_crossings+1 end
    if main_edges[edge_key(a,b)] then features.main_path_steps=features.main_path_steps+1 end
    local sa,sb=lookup[pos_key(a)],lookup[pos_key(b)]
    if sa and sb and sa.region_id~=sb.region_id then features.region_crossings=features.region_crossings+1 end
  end
  return features
end

local function build_candidates(world,institutions,graph,lookup,opts)
  opts=opts or {}
  local max_cost=tonumber(opts.max_route_cost) or math.huge
  local front_edges=build_front_edge_set(world)
  local main_edges=build_main_path_edge_set(world)
  local result={}

  for i=1,#institutions do
    for j=i+1,#institutions do
      local a,b=institutions[i],institutions[j]
      local cost,path,states=dijkstra(graph,pos_key(a.sector),pos_key(b.sector))
      if cost and cost<=max_cost then
        local f=route_features(world,path,front_edges,main_edges,lookup)
        local risk=
          f.front_crossings*0.16 +
          f.region_crossings*0.05 +
          (states.gated or 0)*0.06 +
          (states.secret or 0)*0.10
        local delay=math.max(0.20,0.34*cost+0.22*f.front_crossings+0.08*f.region_crossings)
        local trust=clamp(0.98-0.032*cost-0.065*f.front_crossings-0.025*(states.gated or 0),0.48,0.98)
        local distortion=clamp(0.008+0.012*cost+0.035*f.front_crossings+0.020*(states.gated or 0),0.008,0.24)
        result[#result+1]={
          a=a.id,b=b.id,
          path=path,
          path_cost=round(cost,3),
          delay=round(delay,3),
          trust=round(trust,4),
          distortion=round(distortion,4),
          risk=round(risk,4),
          front_crossings=f.front_crossings,
          region_crossings=f.region_crossings,
          transition_sectors=f.transition_sectors,
          main_path_steps=f.main_path_steps,
          access_states=states,
        }
      end
    end
  end

  table.sort(result,function(x,y)
    if x.path_cost~=y.path_cost then return x.path_cost<y.path_cost end
    if x.a~=y.a then return x.a<y.a end
    return x.b<y.b
  end)
  return result
end

local function route_pair_key(a,b)
  if a<b then return a.."|"..b end
  return b.."|"..a
end

local function select_routes(institutions,candidates,opts)
  opts=opts or {}
  local parent={}
  local degree={}
  for _,inst in ipairs(institutions) do parent[inst.id]=inst.id; degree[inst.id]=0 end

  local function find(x)
    while parent[x]~=x do
      parent[x]=parent[parent[x]]
      x=parent[x]
    end
    return x
  end
  local function union(a,b)
    local ra,rb=find(a),find(b)
    if ra==rb then return false end
    if ra<rb then parent[rb]=ra else parent[ra]=rb end
    return true
  end

  local chosen={}
  local used={}
  local function add(c,reason)
    local k=route_pair_key(c.a,c.b)
    if used[k] then return false end
    used[k]=true
    local e=Util.deepcopy(c)
    e.reason=reason
    chosen[#chosen+1]=e
    degree[e.a]=(degree[e.a] or 0)+1
    degree[e.b]=(degree[e.b] or 0)+1
    return true
  end

  -- Minimum spanning forest: global continuity where public sector routes permit it.
  for _,c in ipairs(candidates) do
    if union(c.a,c.b) then add(c,"backbone") end
  end

  -- One or two local redundancies prevent a pure tree from making every route brittle.
  local target_degree=tonumber(opts.target_degree) or 2
  local max_degree=tonumber(opts.max_degree) or 3
  for _,inst in ipairs(institutions) do
    if degree[inst.id]<target_degree then
      for _,c in ipairs(candidates) do
        if (c.a==inst.id or c.b==inst.id) and
           degree[inst.id]<target_degree and
           degree[c.a]<max_degree and degree[c.b]<max_degree then
          add(c,"redundancy")
        end
      end
    end
  end

  table.sort(chosen,function(a,b)
    local ka,kb=route_pair_key(a.a,a.b),route_pair_key(b.a,b.b)
    return ka<kb
  end)
  for i,e in ipairs(chosen) do e.id=string.format("auto_route_%02d",i) end
  return chosen,degree
end

local function components(institutions,routes)
  local adj={}
  for _,i in ipairs(institutions) do adj[i.id]={} end
  for _,e in ipairs(routes) do
    adj[e.a][#adj[e.a]+1]=e.b
    adj[e.b][#adj[e.b]+1]=e.a
  end
  local seen,count={},0
  for _,inst in ipairs(institutions) do
    if not seen[inst.id] then
      count=count+1
      local q={inst.id}; seen[inst.id]=true; local head=1
      while q[head] do
        local cur=q[head]; head=head+1
        for _,n in ipairs(adj[cur] or {}) do
          if not seen[n] then seen[n]=true; q[#q+1]=n end
        end
      end
    end
  end
  return count
end

local function build_sector_access(world,institutions,graph)
  local access={}
  for _,s in ipairs(world.sectors or {}) do
    local sk=pos_key({s.sx,s.sy})
    local best=nil
    for _,inst in ipairs(institutions) do
      local cost,path=dijkstra(graph,sk,pos_key(inst.sector))
      if cost and (not best or cost<best.cost-1e-9 or (math.abs(cost-best.cost)<=1e-9 and inst.id<best.institution_id)) then
        best={institution_id=inst.id,cost=cost,path=path}
      end
    end
    if best then
      best.cost=round(best.cost,3)
      best.delay=round(0.15+0.22*best.cost,3)
      best.trust=round(clamp(0.97-0.045*best.cost,0.58,0.97),4)
      access[sk]=best
    end
  end
  return access
end

function Synth.validate_world(world)
  assert(type(world)=="table","PixelGen world must be a table")
  assert(type(world.cols)=="number" and type(world.rows)=="number","world dimensions required")
  assert(type(world.sectors)=="table","world.sectors required")
  assert(type(world.landmark_system)=="table","world.landmark_system required")
  assert(type(world.geography)=="table","world.geography required")
  assert(type(world.territory_graph)=="table","world.territory_graph required")
  return true
end

function Synth.synthesize(world,opts)
  Synth.validate_world(world)
  opts=opts or {}
  local graph,lookup=build_sector_graph(world,opts)
  local institutions=create_institutions(world,opts)
  local candidates=build_candidates(world,institutions,graph,lookup,opts)
  local routes,degree=select_routes(institutions,candidates,opts)
  local access=build_sector_access(world,institutions,graph)

  local kind_counts={}
  local role_counts={}
  for _,i in ipairs(institutions) do
    kind_counts[i.kind]=(kind_counts[i.kind] or 0)+1
    for _,role in ipairs((i.metadata or {}).roles or {}) do
      role_counts[role]=(role_counts[role] or 0)+1
    end
  end
  local front_crossings=0
  for _,e in ipairs(routes) do front_crossings=front_crossings+(e.front_crossings or 0) end

  local warnings={}
  local component_count=components(institutions,routes)
  if #institutions>0 and component_count>1 then
    warnings[#warnings+1]="public information infrastructure is a forest with "..component_count.." components"
  end

  return {
    version=Synth.VERSION,
    source={
      world_seed=world.seed,
      dimensions={world.cols,world.rows},
      generator=Util.deepcopy(world.generator or {}),
    },
    policy={
      allow_gated=opts.allow_gated~=false,
      allow_secret=opts.allow_secret==true,
      sealed_links="excluded",
      route_backbone="minimum spanning forest over weighted sector paths",
      redundancy="deterministic local degree completion",
      target_degree=tonumber(opts.target_degree) or 2,
      max_degree=tonumber(opts.max_degree) or 3,
      front_watches=opts.front_watches~=false,
      caravan_hubs=opts.caravan_hubs~=false,
      caravan_spacing=math.max(8,tonumber(opts.caravan_spacing) or 12),
      main_path_discount=tonumber(opts.main_path_discount) or 0.78,
    },
    institutions=institutions,
    routes=routes,
    sector_access=access,
    summary={
      institution_count=#institutions,
      route_count=#routes,
      component_count=component_count,
      candidate_count=#candidates,
      kind_counts=kind_counts,
      role_counts=role_counts,
      route_front_crossings=front_crossings,
      accessible_sector_count=#Util.sorted_keys(access),
    },
    warnings=warnings,
  }
end

function Synth.fingerprint(plan)
  return tostring(Util.stable_hash(plan))
end

function Synth.validate_plan(plan,world)
  local errors={}
  if type(plan)~="table" or plan.version~=Synth.VERSION then
    return {"network plan version mismatch"}
  end
  local validation_graph=build_sector_graph(world,{
    allow_gated=(plan.policy or {}).allow_gated~=false,
    allow_secret=(plan.policy or {}).allow_secret==true,
  })
  local institution_by_id={}
  local sector_keys={}
  for _,s in ipairs((world or {}).sectors or {}) do
    sector_keys[pos_key({s.sx,s.sy})]=true
  end
  for _,inst in ipairs(plan.institutions or {}) do
    if institution_by_id[inst.id] then
      errors[#errors+1]="duplicate institution id "..tostring(inst.id)
    end
    institution_by_id[inst.id]=inst
    if not sector_keys[pos_key(inst.sector or {})] then
      errors[#errors+1]="institution outside world "..tostring(inst.id)
    end
  end
  local route_ids={}
  for _,route in ipairs(plan.routes or {}) do
    if route_ids[route.id] then errors[#errors+1]="duplicate route id "..tostring(route.id) end
    route_ids[route.id]=true
    local a,b=institution_by_id[route.a],institution_by_id[route.b]
    if not a or not b then
      errors[#errors+1]="route references unknown institution "..tostring(route.id)
    else
      local path=route.path or {}
      if #path<1 or not Util.same_sector(path[1],a.sector) or not Util.same_sector(path[#path],b.sector) then
        errors[#errors+1]="route endpoint/path mismatch "..tostring(route.id)
      end
      for i=1,#path-1 do
        if Util.manhattan(path[i],path[i+1])~=1 then
          errors[#errors+1]="non-adjacent sector step in route "..tostring(route.id)
          break
        end
        local from_key,to_key=pos_key(path[i]),pos_key(path[i+1])
        local allowed=false
        for _,edge in ipairs(validation_graph[from_key] or {}) do
          if edge.to==to_key then allowed=true break end
        end
        if not allowed then
          errors[#errors+1]="route uses forbidden/missing world link "..tostring(route.id)
          break
        end
      end
    end
    if tonumber(route.trust or -1)<0 or tonumber(route.trust or 2)>1 then
      errors[#errors+1]="route trust out of bounds "..tostring(route.id)
    end
    if tonumber(route.distortion or -1)<0 or tonumber(route.distortion or 2)>1 then
      errors[#errors+1]="route distortion out of bounds "..tostring(route.id)
    end
    if plan.policy and plan.policy.allow_secret==false and ((route.access_states or {}).secret or 0)>0 then
      errors[#errors+1]="secret route escaped policy "..tostring(route.id)
    end
  end
  for key,access in pairs(plan.sector_access or {}) do
    if not sector_keys[key] then errors[#errors+1]="access index has unknown sector "..tostring(key) end
    local inst=institution_by_id[access.institution_id]
    if not inst then
      errors[#errors+1]="access index references unknown institution "..tostring(key)
    else
      local path=access.path or {}
      local expected_start={}
      local sx,sy=string.match(key,"^(-?%d+),(-?%d+)$")
      expected_start={tonumber(sx),tonumber(sy)}
      if #path<1 or not Util.same_sector(path[1],expected_start) or not Util.same_sector(path[#path],inst.sector) then
        errors[#errors+1]="access path endpoint mismatch "..tostring(key)
      end
    end
  end
  return errors
end

function Synth.load_world(path)
  assert(type(path)=="string" and path~="","PixelGen Lua world path required")
  local Snapshot=require("ebe.persistence.snapshot")
  local world=Snapshot.read_lua(path)
  Synth.validate_world(world)
  return world
end

function Synth.apply(runtime,plan,opts)
  opts=opts or {}
  assert(type(plan)=="table" and plan.version==Synth.VERSION,"unsupported network synthesis plan")
  if runtime.network_plan then
    assert(
      Synth.fingerprint(runtime.network_plan)==Synth.fingerprint(plan),
      "a different synthesized network plan is already active; create a new runtime for a different world/plan"
    )
  end
  runtime.network_plan=Util.deepcopy(plan)
  runtime.agent_institution_access=runtime.agent_institution_access or {}

  for _,spec in ipairs(plan.institutions or {}) do
    local existing=runtime.ecology.institutions[spec.id]
    if not existing then
      runtime:add_institution(spec)
    else
      assert(
        existing.kind==spec.kind and Util.same_sector(existing.sector,spec.sector),
        "synthesized institution id collision: "..tostring(spec.id)
      )
    end
  end

  for _,route in ipairs(plan.routes or {}) do
    local route_meta={
      route_id=route.id,
      path=Util.deepcopy(route.path),
      path_cost=route.path_cost,
      risk=route.risk,
      front_crossings=route.front_crossings,
      region_crossings=route.region_crossings,
      main_path_steps=route.main_path_steps,
      access_states=Util.deepcopy(route.access_states),
    }
    runtime:subscribe_institution(route.a,route.b,{
      delay=route.delay,trust=route.trust,distortion=route.distortion,
      route=Util.deepcopy(route_meta),
    })
    runtime:subscribe_institution(route.b,route.a,{
      delay=route.delay,trust=route.trust,distortion=route.distortion,
      route=Util.deepcopy(route_meta),
    })
  end

  if opts.attach_existing_agents then
    for _,agent_id in ipairs(Util.sorted_keys(runtime.agents)) do
      Synth.attach_agent(runtime,plan,agent_id,opts)
    end
  end

  runtime.bus:emit("network.synthesized",{
    version=plan.version,
    summary=Util.deepcopy(plan.summary),
    warnings=Util.deepcopy(plan.warnings or {}),
  })
  return plan.summary
end

function Synth.attach_agent(runtime,plan,agent_id,opts)
  opts=opts or {}
  local agent=assert(runtime.agents[agent_id],"unknown agent "..tostring(agent_id))
  runtime.agent_institution_access=runtime.agent_institution_access or {}
  local previous=runtime.agent_institution_access[agent_id]
  local access=(plan.sector_access or {})[pos_key(agent.sector)]

  if previous and (not access or previous.institution_id~=access.institution_id) then
    local old_inst=runtime.ecology.institutions[previous.institution_id]
    if old_inst then old_inst:unsubscribe(agent_id) end
  end

  if not access then
    runtime.agent_institution_access[agent_id]=nil
    return nil
  end
  local inst=runtime.ecology.institutions[access.institution_id]
  if not inst then
    runtime.agent_institution_access[agent_id]=nil
    return nil
  end

  local delay=tonumber(opts.agent_delivery_delay) or access.delay
  local trust=tonumber(opts.agent_delivery_trust) or access.trust
  runtime:subscribe_institution(inst.id,agent_id,{
    delay=delay,
    trust=trust,
    distortion=0,
    route={
      route_id="access:"..agent_id..":"..inst.id,
      path=Util.deepcopy(access.path),
      path_cost=access.cost,
      access=true,
    },
  })
  runtime.agent_institution_access[agent_id]=Util.deepcopy(access)
  return Util.deepcopy(access)
end

function Synth.local_institution(runtime,agent_id)
  local access=(runtime.agent_institution_access or {})[agent_id]
  return access and access.institution_id or nil
end

return Synth
