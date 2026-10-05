local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local EBE=require("ebe")
local Util=require("ebe.util")
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

-- Stable package + contract promotion.
eq(EBE.version,"1.0.0","wrong stable package version")
eq(Contract.VERSION,"1.0.0","wrong stable persistence contract")
eq(Contract.SNAPSHOT_VERSION,"1.0.0","wrong stable snapshot version")
eq(EBE.PublicContract.VERSION,"1.0.0","wrong stable public API version")
eq(EBE.PublicContract.describe().compatibility,"stable 1.0 public contract","wrong compatibility label")
eq(EBE.PublicContract.fingerprint(),"ebe-stablehash-v1:251571066","public contract fingerprint changed")
eq(Contract.fingerprint(),"ebe-stablehash-v1:254293849","persistence contract fingerprint changed")
eq(EBE.ActionRequest.VERSION,"0.9.0","action-request schema was needlessly renumbered")
eq(EBE.Json.VERSION,"0.9.0","JSON codec schema was needlessly renumbered")
eq(EBE.Snapshot.VERSION,"0.9.0","snapshot codec schema was needlessly renumbered")
eq(EBE.PixelGenV080.SUPPORTED_BUNDLE_VERSION,"0.8.0","PixelGen bridge schema changed")
truth(EBE.PublicContract.assert_package(EBE),"stable package contract failed")

-- The frozen package export surface is exact.
local expected={}
for _,k in ipairs(EBE.PublicContract.EXPORTS) do expected[k]=true end
local actual_count=0
for k in pairs(EBE) do
  actual_count=actual_count+1
  truth(expected[k],"unexpected stable package export "..tostring(k))
end
eq(actual_count,#EBE.PublicContract.EXPORTS,"stable package export count changed")
for _,name in ipairs({"assign_local_observations","share","get_belief","get_knowledge","restore"}) do
  local found=false
  for _,m in ipairs(EBE.PublicContract.RUNTIME_METHODS) do if m==name then found=true break end end
  truth(found,"documented Runtime method missing from stable public contract: "..name)
end

-- Canonical semantic payload must match the v0.9 baseline after release metadata is stripped.
local rt=EBE.Runtime.new({seed=7301,actions={log_capacity=64}})
rt:add_agent({id="mara",sector={0,2},faction="watch",trust={iva=0.9}})
rt:add_agent({id="iva",sector={1,2},faction="watch",trust={mara=0.8}})
rt:add_agent({id="levko",sector={5,4},faction="civilian"})
rt:add_institution({id="press",kind="printing_house",sector={0,2}})
rt:set_institution_editorial_policy("press",{
  agenda={["front:"]=0.4},
  rules={{id="levko_priority",match={target_id="levko",key_prefix="front:"},action="publish",priority=0.8}},
})
rt:subscribe_institution("press","levko",{})
rt:add_collective({id="watch_council",kind="council",faction="watch",members={"mara","iva"}})
local a=rt:request_action({domain="agent_intent",action_type="wait",actor_id="mara",origin_observation_ids={"obs_2","obs_1","obs_1"}})
rt:resolve_action_request(a.id,"applied",{local_only=true})
local w=rt:request_action({domain="pixelgen_world_event",action_type="territory_alert",actor_id="iva",target_type="territory",target_id="territory_0",amount=0.2,origin_observation_ids={"obs_3"}})
rt:export_pixelgen_action(w.id)
rt.action_gateway:correlate_pixelgen_bundle(rt,{events={{id="derived_1",cause_event_id=w.id,event_type="territory_state_changed",subject_type="territory",subject_id="territory_0",revision=1}}})
rt:advance(0.5)
local snap=rt:snapshot()
local semantic=copy(snap)
semantic.version=nil; semantic.contract_version=nil
semantic.action_gateway.version=nil
for _,req in pairs(semantic.action_gateway.requests or {}) do req.version=nil end
eq(Util.stable_hash(semantic),676699684,"v1.0 promotion changed canonical semantic payload")

-- v0.9 -> v1.0 is metadata-only.
local legacy=copy(snap)
legacy.version="0.9.0"; legacy.contract_version="0.9.0"
local migrated=Contract.migrate_snapshot(legacy)
eq(migrated.version,"1.0.0","v0.9 snapshot did not promote")
eq(migrated.contract_version,"1.0.0","v0.9 contract did not promote")
local projection=copy(migrated); projection.version="0.9.0"; projection.contract_version="0.9.0"
eq(Util.canonical(projection),Util.canonical(legacy),"v0.9 -> v1.0 migration changed semantic payload")

-- Explicit migration matrix: old metadata is accepted, unknown future metadata is not.
for _,v in ipairs({"0.3.0","0.4.0","0.5.0","0.6.0","0.7.0","0.8.0","0.9.0","1.0.0"}) do
  local old=copy(snap); old.version=v; old.contract_version=nil
  local m=Contract.migrate_snapshot(old)
  eq(m.version,"1.0.0","migration matrix failed for "..v)
  eq(m.contract_version,"1.0.0","contract migration matrix failed for "..v)
end
for _,v in ipairs({"1.0.1","1.1.0","2.0.0","9.9.9"}) do
  rejects(function() local f=copy(snap); f.version=v; Contract.migrate_snapshot(f) end,"unsupported EBE snapshot version")
end

-- Nested schema spoofing is fail-closed while the real legacy action schema remains readable.
local action_id=snap.action_gateway.order[1]
local old_action=copy(snap); old_action.action_gateway.requests[action_id].version="0.8.0"
truth(Contract.validate_snapshot(old_action),"supported legacy action-request schema rejected")
local future_action=copy(snap); future_action.action_gateway.requests[action_id].version="9.9.9"
truth(not Contract.validate_snapshot(future_action),"future action-request schema accepted")
local future_gateway=copy(snap); future_gateway.action_gateway.version="9.9.9"
truth(not Contract.validate_snapshot(future_gateway),"future action-gateway schema accepted")
local bad_seq=copy(snap); bad_seq.action_gateway.sequence=bad_seq.action_gateway.sequence+100
truth(not Contract.validate_snapshot(bad_seq),"forged action sequence accepted")
local bad_log=copy(snap); bad_log.action_gateway.log_capacity=1
truth(not Contract.validate_snapshot(bad_log),"oversized action log accepted")

-- Stable JSON must be Unicode JSON, not arbitrary byte strings.
local bad_utf8=string.char(0xC0,0xAF)
rejects(function() Json.decode('{"x":"'..bad_utf8..'"}') end,"invalid UTF-8")
rejects(function() Json.encode({x=bad_utf8}) end,"not valid UTF-8")
local unicode={city="Київ",symbol="✓"}
eq(Util.canonical(Json.decode(Json.encode(unicode))),Util.canonical(unicode),"valid UTF-8 roundtrip failed")

print("EBE v1.0.0 stable promotion / parity / hostile-contract tests passed")
