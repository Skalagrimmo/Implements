local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local Runtime=require("ebe.runtime")
local PixelGen=require("ebe.integrations.pixelgen_v080")

local bundle=PixelGen.load_file(root.."/demo/pixelgen_v080_runtime.lua")
local rt=Runtime.new({seed=7070})

rt:add_agent({id="mara",sector={0,2}})
rt:add_agent({id="levko",sector={5,4},trust={press=1}})
rt:add_agent({id="outsider",sector={5,4},trust={press=1}})
rt:ingest_pixelgen(bundle)
rt:assign_local_observations()

local key="front:front_0:status"
rt:add_institution({
  id="press",
  kind="printing_house",
  sector={2,2},
  policy={receive_delay=.1,broadcast_delay=.5,distortion=0,trust=1,acceptance_min=.1,rebroadcast_min=.1},
  editorial={
    agenda={["front:"]=.4},
    rules={
      {id="censor_outsider",match={target_id="outsider",key_prefix="front:"},action="suppress",tag="restricted"},
      {id="prioritize_levko",match={target_id="levko",key_prefix="front:"},action="publish",priority=.4,tag="front-priority"},
    },
  },
})
rt:subscribe_institution("press","levko",{trust=1})
rt:subscribe_institution("press","outsider",{trust=1})

local r=rt:report_to_institution("mara","press",key,{trust=1})
print("Submitted: "..r.id.." roots="..#r.lineage.origin_observation_ids)
rt:advance(.1)

for _,e in ipairs(rt.ecology.institutions.press.policy_log) do
  print(string.format(
    "Policy target=%s action=%s priority=%.2f rule=%s",
    e.target_id,e.action,e.priority,tostring(e.matched_rule_id)
  ))
end

rt:advance(.3)
local lb=rt.agents.levko.beliefs[key]
local ob=rt.agents.outsider.beliefs[key]
print("Levko: "..(lb and (tostring(lb.value).." roots="..tostring(lb.source_count)) or "no belief"))
print("Outsider: "..(ob and tostring(ob.value) or "no belief"))
print("Press archive reports: "..#rt.ecology.institutions.press.archive_order)
