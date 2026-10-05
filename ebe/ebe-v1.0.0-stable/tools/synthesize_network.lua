package.path="./?.lua;./?/init.lua;"..package.path

local EBE=require("ebe")
local Util=require("ebe.util")
local Synth=EBE.PixelGenNetworkSynth
local Snapshot=EBE.Snapshot

local world_path=arg[1]
local out_base=arg[2] or "generated/network_plan"
assert(world_path,"usage: lua tools/synthesize_network.lua <pixelgen-world.lua> [out-base]")

local world=Synth.load_world(world_path)
local plan=Synth.synthesize(world,{allow_gated=true,allow_secret=false})
local errors=Synth.validate_plan(plan,world)
assert(#errors==0,table.concat(errors,"; "))

Snapshot.write_lua(out_base..".lua",plan)

local f=assert(io.open(out_base..".dot","wb"))
f:write("graph EBE_InfoNetwork {\n")
f:write('  graph [overlap=false,splines=true,label="EBE v0.5.0 PixelGen Information Network"];\n')
f:write('  node [shape=box,fontname="Arial"];\n')
for _,inst in ipairs(plan.institutions) do
  local label=string.format("%s\\n%s\\n(%d,%d)",inst.id,inst.kind,inst.sector[1],inst.sector[2])
  f:write(string.format('  "%s" [label="%s"];\n',inst.id,label))
end
for _,route in ipairs(plan.routes) do
  local label=string.format("%s c=%.2f d=%.2f t=%.2f F=%d",route.id,route.path_cost,route.delay,route.trust,route.front_crossings or 0)
  f:write(string.format('  "%s" -- "%s" [label="%s"];\n',route.a,route.b,label))
end
f:write("}\n")
f:close()

print(string.format(
  "Network plan: institutions=%d routes=%d components=%d accessible=%d/%d fingerprint=%s",
  plan.summary.institution_count,plan.summary.route_count,plan.summary.component_count,
  plan.summary.accessible_sector_count,world.cols*world.rows,Synth.fingerprint(plan)
))
print("Lua plan -> "..out_base..".lua")
print("Graphviz  -> "..out_base..".dot")
