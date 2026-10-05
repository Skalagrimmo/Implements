local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local Runtime=require("ebe.runtime")
local PixelGen=require("ebe.integrations.pixelgen_v080")
local Util=require("ebe.util")

local bundle=PixelGen.load_file(root.."/demo/pixelgen_v080_runtime.lua")
local key="front:front_0:status"

local cases=0
local delivered_rumors=0
local distorted=0

for seed=1,200 do
  local rt=Runtime.new({seed=seed})
  rt:add_agent({id="w1",sector={0,2},trust={far=.82 + (seed%10)*.01}})
  rt:add_agent({id="w2",sector={0,3},trust={far=.88}})
  rt:add_agent({id="far",sector={5,4},trust={w1=.88,w2=.91}})

  rt:connect_agents("w1","far",{
    delay=1+(seed%3),
    trust=.90,
    distortion=(seed%5)*.04,
  })
  rt:connect_agents("w2","far",{
    delay=2+(seed%2),
    trust=.92,
    distortion=(seed%7)*.025,
  })

  rt:ingest_pixelgen(bundle)
  rt:assign_local_observations()

  assert(rt.agents.w1.beliefs[key],"local witness 1 missed evidence")
  assert(rt.agents.w2.beliefs[key],"local witness 2 missed evidence")
  assert(rt.agents.far.beliefs[key]==nil,"far agent gained omniscient belief")
  assert(#rt.agents.far.memory.order==0,"far agent gained omniscient memory")

  local tx1=rt:share("w1","far",key)
  local tx2=rt:share("w2","far",key)
  if tx1.distortion_applied then distorted=distorted+1 end
  if tx2.distortion_applied then distorted=distorted+1 end

  -- Before minimum delay, still no rumor memory.
  local first=math.min(tx1.deliver_at,tx2.deliver_at)
  if first>0 then
    rt:advance(math.max(0,first-0.01))
    assert(#rt.agents.far.memory.order==0,"rumor arrived before scheduled delay")
    rt:advance(0.01)
  end

  -- Advance to the later delivery.
  local last=math.max(tx1.deliver_at,tx2.deliver_at)
  if rt.tick<last then rt:advance(last-rt.tick) end

  assert(#rt.agents.far.memory.order>=1,"far agent never received rumor")
  for _,entry in ipairs(rt.agents.far.memory:all()) do
    local obs=entry.observation
    assert(obs.evidence=="transmitted","far memory contains non-transmitted evidence")
    assert(obs.provenance and obs.provenance.transmission_id,"transmission provenance missing")
  end

  local b=rt.agents.far.beliefs[key]
  assert(b,"far agent did not form a post-rumor belief")
  assert(b.confidence>=0 and b.confidence<=1,"belief confidence out of bounds")
  delivered_rumors=delivered_rumors+#rt.agents.far.memory.order

  -- Long decay remains bounded and never produces invalid confidence.
  rt:advance(72)
  for _,entry in ipairs(rt.agents.far.memory:all()) do
    assert(entry.confidence>=0 and entry.confidence<=1,"memory confidence out of bounds")
  end

  cases=cases+1
end

print(string.format(
  "EBE v0.3.0 fuzz passed: %d simulations, %d received rumor memories, %d distorted transmissions",
  cases,delivered_rumors,distorted
))
