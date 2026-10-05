local root = (... and ... ~= "") and ... or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local Runtime=require("ebe.runtime")

local function truth(v,msg) if not v then error(msg or "expected truthy") end end

local seen_distortion=false

-- Deterministic search over runtime seeds: at least one high-distortion path
-- must alter the reported front status, while never inventing an invalid status.
local valid={quiet=true,active=true,tense=true,volatile=true}

for seed=1,80 do
  local rt=Runtime.new({seed=seed})
  rt:add_agent({id="a",sector={0,0},trust={b=1}})
  rt:add_agent({id="b",sector={5,5},trust={a=1}})
  rt:connect_agents("a","b",{delay=1,trust=1,distortion=1})

  -- Seed sender cognition using a local synthetic observation.
  rt:_deliver_observation("a",{
    id="source_"..seed,
    source_event_id="evt",
    subject_type="front",
    subject_id="front_x",
    sector={0,0},
    evidence="direct_local",
    confidence=0.96,
    fact={claims={{key="front:front_x:status",value="tense"}}},
  })

  local tx=rt:share("a","b","front:front_x:status")
  truth(valid[tx.claim.value],"distortion invented invalid status")
  if tx.distortion_applied then
    seen_distortion=true
    truth(tx.claim.value~="tense","distortion flag set without changing value")
    break
  end
end

truth(seen_distortion,"100% distortion policy never distorted a rumor")
print("EBE v0.3.0 deterministic distortion test passed")
