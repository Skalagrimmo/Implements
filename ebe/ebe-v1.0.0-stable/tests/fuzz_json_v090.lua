local root=arg[1] or "."
package.path=root.."/?.lua;"..root.."/?/init.lua;"..package.path
local Json=require("ebe.persistence.json")
local Util=require("ebe.util")

local rounds=tonumber(arg[2]) or 500
local rejects,valid=0,0
local function must_reject(s)
  local ok=pcall(Json.decode,s,{max_depth=32,max_nodes=10000,max_bytes=1024*1024})
  assert(not ok,"hostile JSON unexpectedly accepted: "..s:sub(1,120))
  rejects=rejects+1
end
for i=1,rounds do
  must_reject('{"x":'..i..',"x":'..(i+1)..'}')
  must_reject('{"x":null,"n":'..i..'}')
  must_reject('{"x":1e999,"n":'..i..'}')
  must_reject('{"x":'..i..'} garbage')
  must_reject('{"x":"bad\\q'..i..'"}')
  must_reject('{"x":['..i..',]}')
  must_reject('{x:'..i..'}')
  must_reject('{"x":'..i..' "y":2}')
  must_reject('[1,2,3,]')
  must_reject('{"x":"unterminated'..i)

  local obj={id="case_"..i,n=i,flag=(i%2==0),arr={i,i+1,i+2},nested={k="v"..i}}
  local text=Json.encode(obj)
  local back=Json.decode(text)
  assert(Util.canonical(back)==Util.canonical(obj),"valid JSON roundtrip failed "..i)
  valid=valid+1
end
local deep='0'
for _=1,40 do deep='['..deep..']' end
must_reject(deep)
print(string.format("EBE v0.9.0 strict JSON corpus: %d hostile rejects, %d valid roundtrips PASS",rejects,valid))
