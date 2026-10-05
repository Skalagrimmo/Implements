local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local EBE=require("ebe")
local Util=require("ebe.util")
local Snapshot=EBE.Snapshot
local Contract=EBE.PersistenceContract
local Json=EBE.Json

local function eq(a,b,msg) assert(a==b,(msg or "not equal")..": "..tostring(a).." ~= "..tostring(b)) end
local function truth(v,msg) assert(v,msg or "expected truthy") end
local function rejects(fn,needle)
  local ok,err=pcall(fn)
  assert(not ok,"expected rejection")
  if needle then assert(tostring(err):find(needle,1,true),"wrong error: "..tostring(err)) end
  return tostring(err)
end
local function copy(v) return Util.deepcopy(v) end

truth(EBE.PublicContract.assert_package(EBE),"public API freeze failed")
truth(type(EBE.PublicContract.fingerprint())=="string","contract fingerprint missing")
eq(EBE.version,"1.0.0","wrong EBE version")
eq(Contract.VERSION,"1.0.0","wrong persistence contract")

local rt=EBE.Runtime.new({seed=7301})
rt:add_agent({id="mara",sector={1,2},faction="watch"})
rt:add_agent({id="iva",sector={2,2},faction="watch"})
local local_req=rt:request_action({domain="agent_intent",action_type="wait",actor_id="mara",origin_observation_ids={"obs_a","obs_a","obs_b"}})
eq(local_req.source_count,2,"duplicate roots manufactured evidence")
local world_req=rt:request_action({domain="pixelgen_world_event",action_type="territory_alert",actor_id="mara",target_type="territory",target_id="territory_0",amount=0.2,origin_observation_ids={"obs_a"}})
rejects(function() rt:resolve_action_request(world_req.id,"applied",{revision=1}) end,"only be applied after export")
local exported=rt:export_pixelgen_action(world_req.id)
eq(exported.id,world_req.id,"wrong export id")

-- A forged feedback event with the right cause but wrong subject may not resolve the request.
local n=rt.action_gateway:correlate_pixelgen_bundle(rt,{events={{id="fake",cause_event_id=world_req.id,event_type="territory_state_changed",subject_type="territory",subject_id="territory_OTHER",revision=1}}})
eq(n,0,"spoofed authority feedback resolved request")
eq(rt:action_request(world_req.id).status,"exported","spoofed feedback changed action state")
local n2=rt.action_gateway:correlate_pixelgen_bundle(rt,{events={{id="real",cause_event_id=world_req.id,event_type="territory_state_changed",subject_type="territory",subject_id="territory_0",revision=2}}})
eq(n2,1,"matching authority feedback did not resolve request")
eq(rt:action_request(world_req.id).status,"applied","matching feedback did not apply request")

local snap=rt:snapshot()
eq(snap.version,"1.0.0","snapshot version")
eq(snap.contract_version,"1.0.0","snapshot contract version")
truth(Contract.validate_snapshot(snap),"current snapshot validation failed")

local encoded=Snapshot.to_json(snap)
local decoded=Snapshot.from_json(encoded)
eq(Util.canonical(decoded),Util.canonical(snap),"strict JSON roundtrip changed snapshot")
local restored=EBE.Runtime.restore(decoded)
eq(Util.canonical(restored:snapshot()),Util.canonical(snap),"runtime restore changed snapshot")

rejects(function() Json.decode('{"a":1,"a":2}') end,"duplicate object key")
rejects(function() Json.decode('{"a":null}') end,"null is not supported")
rejects(function() Json.decode('{"a":1e999}') end,"non-finite number")
rejects(function() Json.decode('{"a":1} trailing') end,"trailing data")
rejects(function() Snapshot.to_json({x=0/0}) end,"NaN/Infinity")

local hostile=copy(snap); hostile.tick=0/0
truth(not Contract.validate_snapshot(hostile),"NaN tick accepted")
hostile=copy(snap); hostile.agents.mara.id="iva"
truth(not Contract.validate_snapshot(hostile),"agent key/id mismatch accepted")
hostile=copy(snap); hostile.action_gateway.order[#hostile.action_gateway.order+1]=hostile.action_gateway.order[1]
truth(not Contract.validate_snapshot(hostile),"duplicate action order accepted")
hostile=copy(snap); hostile.action_gateway.requests[world_req.id].source_count=99
truth(not Contract.validate_snapshot(hostile),"forged source_count accepted")
local cyc=copy(snap); cyc.evil=cyc
truth(not Contract.validate_snapshot(cyc),"cyclic snapshot accepted")

-- Safe legacy Lua reader must parse our serializer without executing arbitrary input.
local tmpbase=root.."/tests/_v090_tmp"
local lua_path=tmpbase..".lua"
local json_path=tmpbase..".json"
local marker=tmpbase..".PWNED"
Snapshot.write_lua(lua_path,snap)
local lua_loaded=Snapshot.read_lua(lua_path)
eq(Util.canonical(lua_loaded),Util.canonical(snap),"safe Lua roundtrip changed snapshot")
local mf=assert(io.open(lua_path,"wb")); mf:write('return (function() local f=io.open("'..marker..'","wb"); f:write("x"); f:close(); return {} end)()'); mf:close()
rejects(function() Snapshot.read_lua(lua_path) end,"only literal values are allowed")
local markerf=io.open(marker,"rb"); if markerf then markerf:close(); error("safe Lua parser executed attacker code") end

-- Atomic save must preserve the previous committed file if staging fails.
Snapshot.write_runtime_json_atomic(json_path,snap)
local before=Snapshot.read_runtime_json(json_path)
rejects(function()
  local changed=copy(snap); changed.tick=changed.tick+1
  Snapshot.write_runtime_json_atomic(json_path,changed,{after_temp_write=function() error("simulated stage failure") end})
end,"simulated stage failure")
local after=Snapshot.read_runtime_json(json_path)
eq(Util.canonical(after),Util.canonical(before),"failed atomic save damaged previous snapshot")

-- Commit failure after backup must roll back the old file.
local rename_calls=0
local function failing_rename(a,b)
  rename_calls=rename_calls+1
  if rename_calls==2 then return nil,"simulated commit failure" end
  return os.rename(a,b)
end
rejects(function()
  local changed=copy(snap); changed.tick=changed.tick+2
  Snapshot.write_runtime_json_atomic(json_path,changed,{rename=failing_rename})
end,"simulated commit failure")
local after_rollback=Snapshot.read_runtime_json(json_path)
eq(Util.canonical(after_rollback),Util.canonical(before),"commit rollback did not restore previous snapshot")

-- v0.8 snapshots migrate metadata only and retain semantic payload.
local legacy=copy(snap); legacy.version="0.8.0"; legacy.contract_version=nil
local migrated=Contract.migrate_snapshot(legacy)
eq(migrated.version,"1.0.0","legacy snapshot not migrated")
eq(migrated.contract_version,"1.0.0","legacy contract not migrated")
local projection=copy(migrated); projection.version="0.8.0"; projection.contract_version=nil
eq(Util.canonical(projection),Util.canonical(legacy),"metadata migration changed legacy payload")
rejects(function() local future=copy(snap); future.version="1.1.0"; Contract.migrate_snapshot(future) end,"unsupported EBE snapshot version")

os.remove(lua_path); os.remove(json_path); os.remove(marker)
print("EBE v1.0.0 persistence / hostile-input / public-contract tests passed")
