local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local Runtime=require("ebe.runtime")
local PixelGen=require("ebe.integrations.pixelgen_v080")

local bundle=PixelGen.load_file(root.."/demo/pixelgen_v080_runtime.lua")
local key="front:front_0:status"
local simulations=300
local decisions=0
local suppressed=0
local delivered=0
local holds=0

for i=1,simulations do
  local rt=Runtime.new({seed=9700+i})
  rt:add_agent({id="source",sector={0,2}})
  for n=1,5 do
    rt:add_agent({id="t"..n,sector={5,4},trust={hub=1}})
  end
  rt:ingest_pixelgen(bundle)
  rt:assign_local_observations()
  assert(rt.agents.source.beliefs[key])

  local rules={}
  for n=1,5 do
    local mode=(i+n)%5
    if mode==0 then
      rules[#rules+1]={id="s"..n,match={target_id="t"..n},action="suppress"}
    elseif mode==1 then
      rules[#rules+1]={id="h"..n,match={target_id="t"..n},action="hold",hold_delay=.25+.05*n,priority=-.25}
    else
      rules[#rules+1]={id="p"..n,match={target_id="t"..n},action="publish",priority=(mode-2)/4,confidence_multiplier=.8}
    end
  end

  rt:add_institution({
    id="hub",kind="printing_house",sector={2,2},
    policy={receive_delay=.05,broadcast_delay=.1,distortion=0,trust=1,acceptance_min=.1,rebroadcast_min=.1},
    editorial={agenda={["front:"]=((i%9)-4)/8},policy_log_capacity=8,rules=rules},
  })
  for n=1,5 do rt:subscribe_institution("hub","t"..n,{trust=1}) end

  local rep=rt:report_to_institution("source","hub",key,{trust=1})
  local root_count=#rep.lineage.origin_observation_ids
  rt:advance(.05)
  local log=rt.ecology.institutions.hub.policy_log
  assert(#log==5)
  decisions=decisions+#log
  local expected={}
  for _,e in ipairs(log) do expected[e.target_id]=e.action end

  rt:advance(3)
  for n=1,5 do
    local id="t"..n
    local action=expected[id]
    if action=="suppress" then
      assert(rt.agents[id].beliefs[key]==nil,"soak suppression leak")
      suppressed=suppressed+1
    else
      local b=rt.agents[id].beliefs[key]
      assert(b,"soak publication missing")
      assert(b.source_count==root_count,"soak policy changed root lineage")
      delivered=delivered+1
      if action=="hold" then holds=holds+1 end
    end
  end

  assert(#rt.ecology.institutions.hub.policy_log<=8,"bounded policy log overflow")
end

print(string.format(
  "EBE v0.7.0 policy soak passed: %d simulations, %d decisions, %d delivered, %d suppressed, %d held",
  simulations,decisions,delivered,suppressed,holds
))
