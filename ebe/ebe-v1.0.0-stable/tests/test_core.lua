local root = (... and ... ~= "") and ... or "."
package.path =
  root .. "/?.lua;" ..
  root .. "/?/init.lua;" ..
  package.path

local Util = require("ebe.util")
local EventBus = require("ebe.event_bus")
local Observation = require("ebe.cognition.observation")
local Memory = require("ebe.cognition.memory")
local Belief = require("ebe.cognition.belief")
local Knowledge = require("ebe.cognition.knowledge")
local Interpretation = require("ebe.cognition.interpretation")
local Snapshot = require("ebe.persistence.snapshot")

local function eq(a,b,msg)
  if a ~= b then
    error((msg or "values differ") .. ": " .. tostring(a) .. " ~= " .. tostring(b))
  end
end

local function truth(v,msg)
  if not v then error(msg or "expected truthy value") end
end

-- Deterministic utility contract.
eq(Util.stable_hash({b=2,a=1}), Util.stable_hash({a=1,b=2}), "canonical hash changed by key order")
eq(Util.roll01("x",1,2), Util.roll01("x",1,2), "roll01 is not deterministic")

-- EventBus priority then registration-order contract.
local bus=EventBus.new()
local order={}
bus:subscribe("x",function() order[#order+1]="low" end,0)
bus:subscribe("x",function() order[#order+1]="high1" end,10)
bus:subscribe("x",function() order[#order+1]="high2" end,10)
bus:emit("x",{id="evt"})
eq(table.concat(order,","),"high1,high2,low","EventBus ordering broken")

-- Direct observation becomes memory/belief/knowledge.
local direct=Observation.normalize({
  id="obs_direct",
  subject_type="front",
  subject_id="front_0",
  sector={0,2},
  evidence="direct_local",
  fact={changes={status={before="active",after="tense"}}},
})
local memory=Memory.new({decay_per_hour=0.95})
truth(memory:add(direct,0),"direct observation not added")

local agent={
  id="mara",
  trust={},
  biases={threat_sensitivity=1.1},
}
local beliefs=Belief.rebuild(memory,agent)
local key="front:front_0:status"
truth(beliefs[key],"missing direct belief")
eq(beliefs[key].value,"tense","wrong direct belief value")
truth(beliefs[key].confidence > 0.9,"direct belief confidence too low")

local knowledge=Knowledge.rebuild(beliefs)
truth(knowledge[key],"direct evidence did not become knowledge")
eq(knowledge[key].basis,"direct_evidence","wrong knowledge basis")

local interpretations=Interpretation.rebuild(beliefs,agent)
truth(#interpretations >= 1,"no interpretation produced")
truth(interpretations[1].threat > 0.7,"tense front was not interpreted as threat")

-- Contradictory evidence remains explicit rather than overwritten.
local contradiction=Observation.normalize({
  id="obs_contradiction",
  subject_type="front",
  subject_id="front_0",
  sector={0,2},
  evidence="transmitted",
  confidence=0.45,
  source_agent_id="other",
  fact={claims={{key=key,value="quiet"}}},
})
memory:add(contradiction,0)
agent.trust.other=0.6
beliefs=Belief.rebuild(memory,agent)
eq(beliefs[key].value,"tense","weak rumor overwrote strong direct evidence")
truth(beliefs[key].evidence_count==2,"contradictory evidence was not retained")

-- A single rumor can create belief but not corroborated knowledge.
local rumor_memory=Memory.new()
local rumor=Observation.normalize({
  id="rumor_1",
  subject_type="rumor",
  subject_id=key,
  sector={5,4},
  evidence="transmitted",
  confidence=0.78,
  source_agent_id="mara",
  fact={claims={{key=key,value="tense"}}},
})
rumor_memory:add(rumor,0)
local hearer={id="levko",trust={mara=0.9},biases={}}
local rumor_beliefs=Belief.rebuild(rumor_memory,hearer)
truth(rumor_beliefs[key],"rumor did not create belief")
truth(Knowledge.rebuild(rumor_beliefs)[key]==nil,"single rumor incorrectly became knowledge")


-- Repeating the same source does NOT count as independent corroboration.
local duplicate_same_source=Observation.normalize({
  id="rumor_same_source_repeat",
  subject_type="rumor",
  subject_id=key,
  sector={5,4},
  evidence="transmitted",
  confidence=0.78,
  source_agent_id="mara",
  fact={claims={{key=key,value="tense"}}},
})
rumor_memory:add(duplicate_same_source,0)
local same_source_beliefs=Belief.rebuild(rumor_memory,hearer)
truth(same_source_beliefs[key].source_count==1,"same sender counted as independent sources")
truth(Knowledge.rebuild(same_source_beliefs)[key]==nil,"repeated same-source rumor became knowledge")

-- Independent corroboration can elevate a belief to knowledge.
local rumor2=Observation.normalize({
  id="rumor_2",
  subject_type="rumor",
  subject_id=key,
  sector={5,4},
  evidence="transmitted",
  confidence=0.78,
  source_agent_id="iva",
  fact={claims={{key=key,value="tense"}}},
})
hearer.trust.iva=0.9
rumor_memory:add(rumor2,0)
rumor_beliefs=Belief.rebuild(rumor_memory,hearer)
local corroborated=Knowledge.rebuild(rumor_beliefs)
truth(corroborated[key],"two corroborating reports did not become knowledge")
eq(corroborated[key].basis,"corroborated_reports","wrong corroborated basis")

-- Memory decay weakens/forgets old evidence.
local before=rumor_memory.entries.rumor_1.confidence
rumor_memory:advance(10,10)
local after=rumor_memory.entries.rumor_1 and rumor_memory.entries.rumor_1.confidence or 0
truth(after < before,"memory did not decay")

-- Snapshot serializer is deterministic and nil-safe for ordinary tables.
local sample={z=3,a={1,2,3},flag=true}
local lua1=Snapshot.to_lua(sample)
local lua2=Snapshot.to_lua({flag=true,a={1,2,3},z=3})
eq(lua1,lua2,"snapshot Lua output is not deterministic")
truth(string.find(lua1,"return ",1,true)==1,"snapshot does not return a Lua table")

print("EBE v0.3.0 core cognition tests passed")
