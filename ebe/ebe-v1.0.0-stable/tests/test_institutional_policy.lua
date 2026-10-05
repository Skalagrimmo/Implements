local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local Runtime=require("ebe.runtime")
local PixelGen=require("ebe.integrations.pixelgen_v080")
local Policy=require("ebe.social.institution_policy")
local Util=require("ebe.util")

local function truth(v,msg) if not v then error(msg or "expected truthy") end end
local function eq(a,b,msg)
  if a~=b then error((msg or "values differ")..": "..tostring(a).." ~= "..tostring(b)) end
end
local function near(a,b,eps,msg)
  if math.abs(a-b)>(eps or 1e-6) then
    error((msg or "values not near")..": "..tostring(a).." ~= "..tostring(b))
  end
end

-- Standalone policy evaluation is deterministic and first-match.
local normalized=Policy.normalize({
  agenda={["front:"]=.4,["front:front_0:"]=.6},
  rules={
    {id="specific",match={key_prefix="front:front_0:"},action="hold",priority=.2,hold_delay=1.5,confidence_multiplier=.8},
    {id="later",match={key_prefix="front:"},action="suppress"},
  },
})
local decision=Policy.evaluate(normalized,{
  id="r",
  confidence=.9,
  sender_type="agent",
  sender_id="mara",
  claim={key="front:front_0:status",value="tense"},
  lineage={origin_observation_ids={"root_a"},route={},hop_count=0},
},{target_type="agent",target_id="levko"})
eq(decision.matched_rule_id,"specific","policy did not use first matching rule")
eq(decision.action,"hold","hold action lost")
near(decision.priority,.8,1e-9,"longest-prefix agenda priority wrong")
near(decision.delay_add,1.5,1e-9,"hold delay wrong")
near(decision.confidence_multiplier,.8,1e-9,"confidence multiplier wrong")

local bundle=PixelGen.load_file(root.."/demo/pixelgen_v080_runtime.lua")
local rt=Runtime.new({seed=7070})

rt:add_agent({id="mara",sector={0,2}})
rt:add_agent({id="levko",sector={5,4},trust={press=1}})
rt:add_agent({id="outsider",sector={5,4},trust={press=1}})

rt:ingest_pixelgen(bundle)
rt:assign_local_observations()
local key="front:front_0:status"
truth(rt.agents.mara.beliefs[key],"Mara lacks source belief")

rt:add_institution({
  id="press",
  kind="printing_house",
  sector={2,2},
  policy={
    receive_delay=.1,
    broadcast_delay=.5,
    distortion=0,
    trust=1,
    acceptance_min=.1,
    rebroadcast_min=.1,
  },
  editorial={
    agenda={["front:"]=.4},
    policy_log_capacity=32,
    rules={
      {
        id="censor_outsider",
        match={target_id="outsider",key_prefix="front:"},
        action="suppress",
        tag="restricted-audience",
      },
      {
        id="prioritize_watch",
        match={target_id="levko",key_prefix="front:"},
        action="publish",
        priority=.4,
        confidence_multiplier=.8,
        tag="front-priority",
      },
    },
  },
})
rt:add_institution({
  id="archive",
  kind="settlement_square",
  sector={4,4},
  policy={
    receive_delay=.1,
    broadcast_delay=.1,
    distortion=0,
    trust=1,
    acceptance_min=.1,
    rebroadcast_min=.1,
  },
})

rt:subscribe_institution("press","levko",{trust=1})
rt:subscribe_institution("press","outsider",{trust=1})
rt:subscribe_institution("press","archive",{trust=1})

-- Add a target-specific hold rule for the archive.
local view=rt:institution_policy_view("press")
local spec=Util.deepcopy(view.editorial)
table.insert(spec.rules,2,{
  id="hold_archive",
  match={target_id="archive",key_prefix="front:"},
  action="hold",
  priority=-.2,
  hold_delay=1.0,
  tag="delayed-record",
})
rt:set_institution_editorial_policy("press",spec)

local report=rt:report_to_institution("mara","press",key,{trust=1})
local root_count=#report.lineage.origin_observation_ids
truth(root_count>=1,"source evidence roots missing")

-- The institution receives and archives the report at t=.1.
rt:advance(.1)
eq(#rt.ecology.institutions.press.archive_order,1,"press did not archive report")

local pview=rt:institution_policy_view("press")
eq(#pview.policy_log,3,"expected one policy decision per subscriber")

local actions={}
for _,entry in ipairs(pview.policy_log) do actions[entry.target_id]=entry end
eq(actions.outsider.action,"suppress","censorship rule did not suppress outsider")
eq(actions.levko.action,"publish","priority rule did not publish Levko")
eq(actions.levko.matched_rule_id,"prioritize_watch","wrong rule matched Levko")
near(actions.levko.priority,.8,1e-9,"agenda + rule priority wrong")
eq(actions.archive.action,"hold","archive hold rule missing")

-- Base delay .5, priority .8 => multiplier .6 => .3 hours after t=.1.
rt:advance(.29)
truth(rt.agents.levko.beliefs[key]==nil,"priority delivery arrived too early")
rt:advance(.01)
truth(rt.agents.levko.beliefs[key],"priority delivery did not arrive")
truth(rt.agents.outsider.beliefs[key]==nil,"suppressed report leaked to outsider")
eq(rt.agents.levko.beliefs[key].source_count,root_count,
  "editorial policy manufactured or lost evidence roots")
truth(rt.agents.levko.beliefs[key].confidence < rt.agents.mara.beliefs[key].confidence,
  "confidence multiplier did not affect publication confidence")

local policy_seen=false
for _,entry in ipairs(rt.agents.levko.memory:all()) do
  local p=((entry.observation or {}).provenance or {}).institution_policy
  if p and p.matched_rule_id=="prioritize_watch" then policy_seen=true end
end
truth(policy_seen,"policy provenance not carried into delivered evidence")

-- Hold: agenda +.4 and rule -.2 => priority .2; .5 * .9 + 1.0 = 1.45.
-- Broadcast was scheduled from t=.1, so it becomes due at t=1.55.
rt:advance(1.14) -- t=1.54
eq(#rt.ecology.institutions.archive.archive_order,0,"held publication released too early")
rt:advance(.01) -- t=1.55, broadcast reaches target institution queue
eq(#rt.ecology.institutions.archive.archive_order,0,"target archived before receive delay")
rt:advance(.1) -- t=1.65
eq(#rt.ecology.institutions.archive.archive_order,1,"held publication never reached archive")

-- Suppression is editorial, not historical erasure: press retained the original report.
eq(#rt.ecology.institutions.press.archive_order,1,"censorship erased institutional archive")

-- Policy logs are bounded.
local inst=rt.ecology.institutions.press
inst.editorial.policy_log_capacity=2
inst:log_policy({id="a"})
inst:log_policy({id="b"})
inst:log_policy({id="c"})
eq(#inst.policy_log,2,"institution policy log exceeded capacity")

-- Snapshot/restore retains editorial policy and audit log.
local snapshot=rt:snapshot()
local restored=Runtime.restore(snapshot)
eq(Util.canonical(restored:snapshot()),Util.canonical(snapshot),
  "v0.7 policy snapshot restore mismatch")

-- v0.6 snapshots migrate with pass-through editorial policy.
local legacy=Util.deepcopy(snapshot)
legacy.version="0.6.0"
for _,data in pairs((legacy.ecology or {}).institutions or {}) do
  data.editorial=nil
  data.policy_log=nil
end
local migrated=Runtime.restore(legacy)
eq(migrated.version,"1.0.0","v0.6 snapshot did not migrate to current runtime")
for _,migrated_inst in pairs(migrated.ecology.institutions) do
  eq(migrated_inst.editorial.default_action,"publish",
    "v0.6 institution did not receive pass-through editorial policy")
end

print("EBE v0.7.0 institutional policy / censorship / agenda tests passed")
