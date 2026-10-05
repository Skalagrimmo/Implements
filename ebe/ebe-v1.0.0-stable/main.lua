package.path="./?.lua;./?/init.lua;"..package.path

local EBE=require("ebe")
local Synth=EBE.PixelGenNetworkSynth
local Util=require("ebe.util")

local world,plan,rt
local log={}
local cell=82
local ox,oy=35,90
local key="front:front_0:status"
local collective_id="watch_council"
local policy_inst_id=nil

local kind_letter={
  printing_house="P",
  shrine_circle="S",
  roadside_relay="R",
  front_watch="W",
  settlement_square="Q",
  caravan_exchange="C",
  military_post="M",
}

local function add(msg)
  log[#log+1]=msg
  while #log>16 do table.remove(log,1) end
end

local function inst_by_id(id)
  for _,i in ipairs(plan.institutions or {}) do if i.id==id then return i end end
end

local function belief_line(id)
  local a=rt.agents[id]
  local b=a and a.beliefs[key]
  local k=a and a.knowledge[key]
  if not b then return id..": no belief" end
  return string.format("%s: %s %.2f roots=%d K=%s",
    id,tostring(b.value),b.confidence,b.source_count or 0,k and "yes" or "no")
end

local function setup()
  world=Synth.load_world("demo/pixelgen_world_network_7301.lua")
  plan=Synth.synthesize(world,{allow_gated=true,allow_secret=false})
  rt=EBE.Runtime.new({seed=5050,ecology={max_hops=8}})
  -- Demonstration-only world adapter. It creates a request, never a direct mutation.
  rt:register_reaction_action_adapter("avoid_front",{
    domain="pixelgen_world_event",
    action_type="front_deescalation",
    target_from_claim=true,
    amount=.12,
    metadata={demo=true},
  })

  rt:add_agent({id="mara",sector={0,2},faction="watch"})
  rt:add_agent({id="iva",sector={0,3},faction="watch"})
  rt:add_agent({id="levko",sector={5,4},faction="watch",trust={[collective_id]=1}})

  -- PixelGen dynamic observations still work beside the synthesized static network.
  rt:ingest_pixelgen(EBE.PixelGenV080.load_file("demo/pixelgen_v080_runtime.lua"))
  rt:assign_local_observations()
  rt:synthesize_pixelgen_network(world,{attach_existing_agents=true})
  policy_inst_id=rt:local_institution("mara")
  if policy_inst_id then
    rt:set_institution_editorial_policy(policy_inst_id,{
      agenda={["front:"]=0.40},
      policy_log_capacity=64,
    })
  end
  rt:add_collective({
    id=collective_id,
    kind="faction_council",
    faction="watch",
    members={"mara","iva","levko"},
    policy={acceptance_min=.2,consensus_min=.60,confidence_min=.50,min_independent_roots=2,publication_trust=1},
  })
  rt:subscribe_collective(collective_id,"levko",{trust=1})

  add("Network auto-synthesized from PixelGen world.")
  if policy_inst_id then add("Agenda node "..policy_inst_id..": front:* priority +0.40") end
  add("G/H = Mara/Iva -> council. P = publish council -> Levko.")
  add("M/I = institutional report. X = export pending action. A/F time. R reset.")
end

function love.load()
  love.window.setTitle("EBE v1.0.0 — Stable Epistemic Runtime")
  love.window.setMode(1180,720,{resizable=true})
  setup()
end

function love.keypressed(k)
  if k=="m" then
    if rt.agents.mara.beliefs[key] then
      local report=rt:report_to_local_network("mara",key)
      add("Mara -> "..report.institution_id.." at t="..string.format("%.1f",rt.tick))
    end
  elseif k=="i" then
    if rt.agents.iva.beliefs[key] then
      local report=rt:report_to_local_network("iva",key)
      add("Iva -> "..report.institution_id.." at t="..string.format("%.1f",rt.tick))
    end
  elseif k=="g" then
    if rt.agents.mara.beliefs[key] then
      local _,accepted=rt:submit_to_collective("mara",collective_id,key)
      add("Mara -> council "..(accepted and "accepted" or "duplicate"))
    end
  elseif k=="h" then
    if rt.agents.iva.beliefs[key] then
      local _,accepted=rt:submit_to_collective("iva",collective_id,key)
      add("Iva -> council "..(accepted and "accepted" or "duplicate"))
    end
  elseif k=="p" then
    local c=rt:get_collective_consensus(collective_id,key)
    if c then
      rt:publish_collective(collective_id,key)
      add("Council -> Levko roots="..tostring(c.source_count).." state="..tostring(c.state))
    else
      add("Council has no record yet")
    end
  elseif k=="x" then
    local pending=rt:action_requests("pending","pixelgen_world_event")
    if #pending>0 then
      local ev=rt:export_pixelgen_action(pending[1].id)
      add("EXPORT "..ev.id.." -> PixelGen "..ev.event_type.." "..ev.target_id)
    else
      add("No pending PixelGen action request")
    end
  elseif k=="a" then
    rt:advance(.5)
    add(string.format("t=%.1f queue=%d routing=%d",rt.tick,#rt.ecology.queue,#rt.ecology.routing_log))
  elseif k=="f" then
    for _=1,10 do rt:advance(.5) end
    add(string.format("t=%.1f queue=%d routing=%d",rt.tick,#rt.ecology.queue,#rt.ecology.routing_log))
  elseif k=="r" then
    log={}; setup(); add("reset")
  end
end

local function center(pos)
  return ox+pos[1]*cell+cell/2, oy+pos[2]*cell+cell/2
end

function love.draw()
  love.graphics.setColor(1,1,1,1)
  love.graphics.print("EBE v1.0.0 — stable epistemic runtime",25,18)
  love.graphics.print(string.format(
    "seed %s | institutions %d | routes %d | components %d | tick %.1f | queue %d",
    tostring(world.seed),plan.summary.institution_count,plan.summary.route_count,
    plan.summary.component_count,rt.tick,#rt.ecology.queue
  ),25,42)

  -- Sector grid.
  love.graphics.setColor(.33,.33,.36,1)
  for y=0,world.rows-1 do
    for x=0,world.cols-1 do
      love.graphics.rectangle("line",ox+x*cell,oy+y*cell,cell,cell)
      love.graphics.print(x..","..y,ox+x*cell+4,oy+y*cell+4)
    end
  end

  -- Synthesized routes.
  for _,route in ipairs(plan.routes) do
    local a,b=inst_by_id(route.a),inst_by_id(route.b)
    local ax,ay=center(a.sector); local bx,by=center(b.sector)
    if route.front_crossings and route.front_crossings>0 then
      love.graphics.setColor(.88,.67,.42,.68)
    else
      love.graphics.setColor(.55,.68,.74,.58)
    end
    love.graphics.line(ax,ay,bx,by)
  end

  -- Institutions.
  for _,inst in ipairs(plan.institutions) do
    local x,y=center(inst.sector)
    if inst.kind=="printing_house" then love.graphics.setColor(.95,.78,.38,1)
    elseif inst.kind=="shrine_circle" then love.graphics.setColor(.50,.84,.76,1)
    elseif inst.kind=="front_watch" then love.graphics.setColor(.95,.48,.42,1)
    elseif inst.kind=="roadside_relay" then love.graphics.setColor(.76,.76,.76,1)
    else love.graphics.setColor(.72,.63,.86,1) end
    love.graphics.circle("fill",x,y,12)
    love.graphics.setColor(.08,.08,.09,1)
    love.graphics.print(kind_letter[inst.kind] or "?",x-4,y-7)
  end

  -- Agents.
  local agent_offset={mara={-18,18},iva={0,18},levko={18,18}}
  for _,id in ipairs({"mara","iva","levko"}) do
    local a=rt.agents[id]
    local x,y=center(a.sector); local d=agent_offset[id]
    x=x+d[1]; y=y+d[2]
    love.graphics.setColor(1,1,1,1)
    love.graphics.rectangle("fill",x-5,y-5,10,10)
    love.graphics.print(string.sub(id,1,1):upper(),x+7,y-8)
  end

  local px=560
  love.graphics.setColor(1,1,1,1)
  love.graphics.print("Legend: P print | S shrine | W front watch | R roadside",px,90)
  love.graphics.print("Orange-ish route = crosses influence front",px,112)
  love.graphics.print("",px,130)
  love.graphics.print("Agent access:",px,145)
  local y=168
  for _,id in ipairs({"mara","iva","levko"}) do
    love.graphics.print(id.." -> "..tostring(rt:local_institution(id)),px,y); y=y+22
  end
  y=y+8
  love.graphics.print("Epistemic state:",px,y); y=y+22
  for _,id in ipairs({"mara","iva","levko"}) do
    love.graphics.print(belief_line(id),px,y); y=y+22
  end

  y=y+8
  love.graphics.print("Collective state:",px,y); y=y+22
  local c=rt:get_collective_consensus(collective_id,key)
  if c then
    love.graphics.print(string.format(
      "watch_council: %s %.2f roots=%d reporters=%d %s",
      tostring(c.value),c.confidence,c.source_count or 0,c.reporter_count or 0,tostring(c.state)
    ),px,y)
  else
    love.graphics.print("watch_council: no record",px,y)
  end
  y=y+30
  love.graphics.print("Institutional policy:",px,y); y=y+22
  if policy_inst_id and rt.ecology.institutions[policy_inst_id] then
    local pi=rt.ecology.institutions[policy_inst_id]
    love.graphics.print(string.format(
      "%s | front:* agenda +0.40 | decisions=%d",
      policy_inst_id,#(pi.policy_log or {})
    ),px,y)
  else
    love.graphics.print("no policy node",px,y)
  end
  y=y+30
  love.graphics.print("Semantic actions:",px,y); y=y+22
  local actions=rt:action_requests()
  if #actions==0 then
    love.graphics.print("none",px,y); y=y+20
  else
    local start=math.max(1,#actions-2)
    for i=start,#actions do
      local ar=actions[i]
      love.graphics.print(string.format("%s %s %s [%s]",ar.id,ar.action_type,tostring(ar.target_id or "-"),ar.status),px,y); y=y+19
    end
  end
  y=y+10
  love.graphics.print("Event / routing log:",px,y); y=y+22
  for _,line in ipairs(log) do
    love.graphics.print(line,px,y); y=y+19
  end
end
