local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path

local Runtime=require("ebe.runtime")
local PixelGen=require("ebe.integrations.pixelgen_v080")
local Snapshot=require("ebe.persistence.snapshot")
local Util=require("ebe.util")

local function claim_text(agent,key)
  local belief=agent.beliefs[key]
  local knowledge=agent.knowledge[key]
  if not belief then return "no belief / no knowledge" end
  return string.format(
    "belief=%s conf=%.3f sources=%d knowledge=%s",
    tostring(belief.value),
    belief.confidence,
    belief.source_count or 0,
    knowledge and (tostring(knowledge.value).." ["..knowledge.basis.."]") or "no"
  )
end

local bundle=PixelGen.load_file(root.."/demo/pixelgen_v080_runtime.lua")
local rt=Runtime.new({seed=3030})

rt:add_agent({
  id="mara",
  sector={0,2},
  faction="pilgrims",
  trust={levko=0.85,iva=0.95},
  biases={threat_sensitivity=1.15},
})
rt:add_agent({
  id="iva",
  sector={0,3},
  faction="printers",
  trust={mara=0.95,levko=0.9},
  biases={skepticism=0.05},
})
rt:add_agent({
  id="levko",
  sector={5,4},
  faction="none",
  trust={mara=0.95,iva=0.95},
  biases={skepticism=0.08},
})

rt:connect_agents("mara","levko",{delay=2,trust=0.95,distortion=0.06})
rt:connect_agents("iva","levko",{delay=3,trust=0.95,distortion=0.04})

local imported=rt:ingest_pixelgen(bundle)
local direct=rt:assign_local_observations()
local key="front:front_0:status"

print("=== EBE v0.3.0 — Information Locality / PixelGen Runtime Bridge ===")
print(string.format(
  "PixelGen import: entities=%d events=%d observations=%d direct-deliveries=%d",
  imported.entities, imported.events, imported.observations, direct
))
print("")
print("[t=0] same external event, different epistemic states")
print("Mara : "..claim_text(rt.agents.mara,key))
print("Iva  : "..claim_text(rt.agents.iva,key))
print("Levko: "..claim_text(rt.agents.levko,key))
print("")

local tx1=rt:share("mara","levko",key)
print(string.format(
  "Mara transmits rumor %s -> Levko; deliver_at=%.1f distortion=%s",
  tx1.id,tx1.deliver_at,tostring(tx1.distortion_applied)
))

rt:advance(1)
print("[t=1] Levko: "..claim_text(rt.agents.levko,key))

rt:advance(1)
print("[t=2] Levko after one report: "..claim_text(rt.agents.levko,key))

local tx2=rt:share("iva","levko",key)
print(string.format(
  "Iva independently transmits %s; deliver_at=%.1f distortion=%s",
  tx2.id,tx2.deliver_at,tostring(tx2.distortion_applied)
))

rt:advance(3)
print("[t=5] Levko after corroboration: "..claim_text(rt.agents.levko,key))
print("")

print("Reactions:")
for _,r in ipairs(rt.reaction_log) do
  print(string.format(
    "  %s agent=%s kind=%s belief=%s conf=%.3f",
    r.id,r.agent_id,r.kind,tostring(r.believed_value),r.confidence or 0
  ))
end

print("")
print("Propagation delivery log:")
for _,d in ipairs(rt.delivery_log) do
  print(string.format(
    "  t=%s agent=%s obs=%s evidence=%s source=%s",
    tostring(d.tick),d.agent_id,d.observation_id,d.evidence,tostring(d.source_agent_id)
  ))
end

local summary=rt:summary()
print("")
print(string.format(
  "Summary: tick=%s agents=%d memory=%d beliefs=%d knowledge=%d queued=%d reactions=%d",
  tostring(summary.tick),
  summary.agents,
  summary.memory_entries,
  summary.beliefs,
  summary.knowledge,
  summary.queued_transmissions,
  summary.reactions
))

local snapshot=rt:snapshot()
local path=root.."/generated/demo_snapshot.lua"
local f=io.open(root.."/generated/.keep","w")
if f then f:close() end
Snapshot.write_lua(path,snapshot)
local restored=Runtime.restore(Snapshot.read_lua(path))
print("Snapshot semantic equality: "..tostring(
  Util.canonical(snapshot)==Util.canonical(restored:snapshot())
))
print("Snapshot hash: "..Snapshot.hash(snapshot))
