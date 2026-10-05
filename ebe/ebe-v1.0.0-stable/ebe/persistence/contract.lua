local Util = require("ebe.util")
local ActionRequest = require("ebe.action.action_request")

local Contract={}
Contract.VERSION="1.0.0"
Contract.SNAPSHOT_VERSION="1.0.0"
Contract.ACCEPTED_SNAPSHOT_VERSIONS={
  ["0.3.0"]=true,["0.4.0"]=true,["0.5.0"]=true,["0.6.0"]=true,
  ["0.7.0"]=true,["0.8.0"]=true,["0.9.0"]=true,["1.0.0"]=true,
}
Contract.LIMITS={
  max_depth=96,
  max_nodes=250000,
  max_string_bytes=1024*1024,
  max_agents=10000,
  max_entities=100000,
  max_queue=100000,
  max_action_requests=100000,
  max_lineage_roots=4096,
  max_route_hops=128,
}

local function finite(v) return type(v)=="number" and v==v and v~=math.huge and v~=-math.huge end
local function int(v) return finite(v) and v%1==0 end
local function id_ok(v)
  return type(v)=="string" and v~="" and #v<=256 and not v:find("[%z\1-\31]")
end
local function count(t)
  local n=0; local k,v=next(t or {},nil)
  while k~=nil do n=n+1; k,v=next(t,k) end
  return n
end

local function validate_tree(root,limits)
  local seen,nodes={},0
  local function walk(v,depth,path)
    nodes=nodes+1
    assert(nodes<=limits.max_nodes,"snapshot exceeds max_nodes at "..path)
    assert(depth<=limits.max_depth,"snapshot exceeds max_depth at "..path)
    local tv=type(v)
    if tv=="nil" or tv=="boolean" then return end
    if tv=="number" then assert(finite(v),"non-finite number at "..path); return end
    if tv=="string" then assert(#v<=limits.max_string_bytes,"string too large at "..path); return end
    assert(tv=="table","unsupported snapshot type "..tv.." at "..path)
    assert(getmetatable(v)==nil,"metatable is forbidden at "..path)
    assert(not seen[v],"cyclic snapshot table at "..path)
    seen[v]=true
    local k,val=next(v,nil)
    while k~=nil do
      local kt=type(k)
      assert(kt=="string" or (kt=="number" and finite(k)),"unsupported table key at "..path)
      if kt=="string" then assert(#k<=limits.max_string_bytes,"table key too large at "..path) end
      walk(val,depth+1,path.."."..tostring(k))
      k,val=next(v,k)
    end
    seen[v]=nil
  end
  walk(root,0,"$")
  return nodes
end

local function validate_sector(s,path)
  assert(type(s)=="table",path.." must be a sector table")
  assert(int(s[1]) and s[1]>=0 and int(s[2]) and s[2]>=0,path.." must be [nonnegative integer, nonnegative integer]")
  local c=0; local k,v=next(s,nil)
  while k~=nil do c=c+1; assert(k==1 or k==2,path.." has extra coordinate keys"); k,v=next(s,k) end
  assert(c==2,path.." must contain exactly two coordinates")
end

local function validate_unique_ids(list,path,maxn)
  assert(type(list or {})=="table",path.." must be a table")
  assert(#(list or {})<=maxn,path.." exceeds limit")
  local seen={}
  for i,item in ipairs(list or {}) do
    assert(type(item)=="table",path.."["..i.."] must be a table")
    assert(id_ok(item.id),path.."["..i.."].id is invalid")
    assert(not seen[item.id],"duplicate id "..item.id.." in "..path)
    seen[item.id]=true
  end
end

local function validate_lineage(lineage,path,limits)
  if lineage==nil then return end
  assert(type(lineage)=="table",path.." must be a table")
  local roots=lineage.origin_observation_ids or {}
  assert(type(roots)=="table",path..".origin_observation_ids must be a table")
  assert(#roots<=limits.max_lineage_roots,path.." has too many evidence roots")
  local seen={}
  for i,id in ipairs(roots) do
    assert(id_ok(id),path.." root id is invalid")
    assert(not seen[id],path.." contains duplicate evidence root "..id)
    seen[id]=true
  end
  local route=lineage.route or {}
  assert(type(route)=="table",path..".route must be a table")
  assert(#route<=limits.max_route_hops,path.." route exceeds max_route_hops")
  local hop=tonumber(lineage.hop_count or #route)
  assert(int(hop) and hop>=0 and hop<=limits.max_route_hops,path.." hop_count is invalid")
  assert(hop>=#route,path.." hop_count cannot be shorter than route")
end

local function validate_action_gateway(g,limits)
  if g==nil then return end
  assert(type(g)=="table","action_gateway must be a table")
  if g.version~=nil then
    assert(g.version=="0.8.0" or g.version=="0.9.0",
      "unsupported action gateway version "..tostring(g.version))
  end
  local requests=g.requests or {}; local order=g.order or {}
  assert(type(requests)=="table" and type(order)=="table","action gateway requests/order must be tables")
  assert(#order<=limits.max_action_requests,"too many action requests")
  assert(count(requests)<=limits.max_action_requests,"too many action requests")
  local seq=tonumber(g.sequence or 0)
  assert(int(seq) and seq>=0,"action gateway sequence must be a nonnegative integer")
  assert(seq==#order,"action gateway sequence must equal request count")
  local log_capacity=tonumber(g.log_capacity or 512)
  assert(int(log_capacity) and log_capacity>=1 and log_capacity<=limits.max_queue,"action log capacity is invalid")
  local log=g.log or {}
  assert(type(log)=="table","action log must be a table")
  assert(#log<=log_capacity,"action log exceeds configured capacity")
  if g.default_reaction_intents~=nil then assert(type(g.default_reaction_intents)=="boolean","default_reaction_intents must be boolean") end
  local seen={}
  for i,id in ipairs(order) do
    assert(id_ok(id),"invalid action order id at "..i)
    assert(not seen[id],"duplicate action id in order: "..id); seen[id]=true
    local req=requests[id]; assert(type(req)=="table","action order references missing request "..id)
    assert(req.id==id,"action request key/id mismatch for "..id)
    local ok,err=ActionRequest.validate(req); assert(ok,"invalid action request "..id..": "..tostring(err))
    assert(tonumber(req.source_count or 0)==#(req.origin_observation_ids or {}),"action source_count mismatch for "..id)
    validate_lineage({origin_observation_ids=req.origin_observation_ids or {},route=((req.provenance or {}).route or {}),hop_count=tonumber(((req.provenance or {}).hop_count)) or #(((req.provenance or {}).route or {}))},"action:"..id..".lineage",limits)
    if req.status=="pending" then
      assert(req.resolved_at==nil and req.result==nil,"pending action has resolution data: "..id)
    elseif req.status=="exported" then
      assert(type(req.exported_event)=="table","exported action lacks exported_event: "..id)
      assert(req.exported_event.id==id,"exported event/action id mismatch: "..id)
      assert(req.resolved_at==nil,"exported action is already resolved: "..id)
    elseif req.status=="applied" or req.status=="rejected" then
      assert(req.resolved_at~=nil,"resolved action lacks resolved_at: "..id)
      if req.status=="applied" and req.domain=="pixelgen_world_event" then
        assert(type(req.exported_event)=="table","applied PixelGen action lacks exported_event: "..id)
      end
    end
    if type(req.exported_event)=="table" then
      assert(req.exported_event.id==id,"exported event/action id mismatch: "..id)
      assert(req.exported_event.event_type==req.action_type,"exported event type mismatch: "..id)
      assert(req.exported_event.target_type==req.target_type,"exported target_type mismatch: "..id)
      assert(req.exported_event.target_id==req.target_id,"exported target_id mismatch: "..id)
      assert(req.exported_event.actor_id==req.actor_id,"exported actor mismatch: "..id)
    end
  end
  local k,v=next(requests,nil)
  while k~=nil do assert(seen[k],"action request missing from order: "..tostring(k)); k,v=next(requests,k) end

  local stage={}
  for i,entry in ipairs(log) do
    assert(type(entry)=="table","action log entry must be a table")
    local id=entry.action_id
    if id~=nil then
      assert(id_ok(id),"action log contains invalid action_id")
      assert(requests[id]~=nil,"action log references unknown request "..id)
      local prev=stage[id]
      if entry.kind=="action_requested" then
        assert(prev==nil,"duplicate action_requested log for "..id); stage[id]="pending"
      elseif entry.kind=="action_exported" then
        assert(prev==nil or prev=="pending" or prev=="exported","impossible action export transition for "..id); stage[id]="exported"
      elseif entry.kind=="action_applied" or entry.kind=="action_rejected" then
        assert(prev~="applied" and prev~="rejected","multiple action resolutions for "..id)
        stage[id]=entry.kind=="action_applied" and "applied" or "rejected"
      end
    end
  end
end

function Contract.validate_snapshot(snapshot,opts)
  opts=opts or {}; local limits={}
  for k,v in pairs(Contract.LIMITS) do limits[k]=opts[k] or v end
  local ok,err=pcall(function()
    assert(type(snapshot)=="table","runtime snapshot must be a table")
    validate_tree(snapshot,limits)
    assert(Contract.ACCEPTED_SNAPSHOT_VERSIONS[snapshot.version],"unsupported EBE snapshot version "..tostring(snapshot.version))
    assert(finite(snapshot.tick or 0) and (snapshot.tick or 0)>=0,"snapshot tick must be finite and nonnegative")
    assert(finite(snapshot.seed or 0),"snapshot seed must be finite")
    local agents=snapshot.agents or {}; assert(type(agents)=="table","agents must be a table")
    assert(count(agents)<=limits.max_agents,"too many agents")
    local k,a=next(agents,nil)
    while k~=nil do
      assert(id_ok(k),"invalid agent map key")
      assert(type(a)=="table" and a.id==k,"agent key/id mismatch for "..tostring(k))
      validate_sector(a.sector or {},"agent:"..k..".sector")
      k,a=next(agents,k)
    end
    local entities=snapshot.entities or {}; assert(type(entities)=="table","entities must be a table")
    assert(count(entities)<=limits.max_entities,"too many entities")
    assert(#((snapshot.propagation or {}).queue or {})<=limits.max_queue,"propagation queue exceeds limit")
    assert(#((snapshot.ecology or {}).queue or {})<=limits.max_queue,"institution queue exceeds limit")
    validate_unique_ids(snapshot.external_events or {},"external_events",limits.max_queue)
    validate_action_gateway(snapshot.action_gateway,limits)
    if snapshot.contract_version~=nil then
      assert(snapshot.contract_version==Contract.VERSION,"unsupported persistence contract "..tostring(snapshot.contract_version))
    end
  end)
  if not ok then return false,tostring(err) end
  return true
end

function Contract.assert_snapshot(snapshot,opts)
  local ok,err=Contract.validate_snapshot(snapshot,opts)
  assert(ok,err)
  return snapshot
end

function Contract.migrate_snapshot(snapshot)
  assert(type(snapshot)=="table","runtime snapshot must be a table")
  assert(Contract.ACCEPTED_SNAPSHOT_VERSIONS[snapshot.version],"unsupported EBE snapshot version "..tostring(snapshot.version))
  local out=Util.deepcopy(snapshot)
  out.version=Contract.SNAPSHOT_VERSION
  out.contract_version=Contract.VERSION
  if out.action_gateway==nil then out.action_gateway={} end
  if out.collectives==nil then out.collectives={} end
  if out.collective_log==nil then out.collective_log={} end
  if out.integration_state==nil then out.integration_state={} end
  if out.delivery_log==nil then out.delivery_log={} end
  Contract.assert_snapshot(out)
  return out
end

function Contract.public_contract()
  return {
    version=Contract.VERSION,
    runtime_snapshot=Contract.SNAPSHOT_VERSION,
    accepted_snapshot_versions={"0.3.0","0.4.0","0.5.0","0.6.0","0.7.0","0.8.0","0.9.0","1.0.0"},
    persistence_formats={"strict-json","safe-lua-subset"},
    action_statuses={"pending","exported","applied","rejected"},
    pixelgen_bridge_version="0.8.0",
    action_request_schema="0.9.0",
    action_gateway_schema="0.9.0",
    json_codec="0.9.0",
    safe_lua_codec="0.9.0",
    guarantees={
      no_executable_snapshot_loading=true,
      duplicate_json_keys_rejected=true,
      invalid_utf8_rejected=true,
      nonfinite_numbers_rejected=true,
      cyclic_tables_rejected=true,
      atomic_runtime_snapshot_write=true,
      bounded_validation=true,
      action_transition_validation=true,
      action_schema_version_checked=true,
      action_log_capacity_validated=true,
      source_lineage_preserved=true,
      stable_1_0_contract=true,
      legacy_0_9_snapshot_migration=true,
    },
  }
end

function Contract.fingerprint()
  return "ebe-stablehash-v1:"..tostring(Util.stable_hash(Contract.public_contract()))
end

return Contract
