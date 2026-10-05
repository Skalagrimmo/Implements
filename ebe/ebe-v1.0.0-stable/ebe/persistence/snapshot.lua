local Util = require("ebe.util")
local Json = require("ebe.persistence.json")
local Contract = require("ebe.persistence.contract")

local Snapshot = {}
Snapshot.VERSION = "0.9.0"

local function is_array(t)
  if type(t) ~= "table" then return false end
  local n = #t
  local count = 0
  local k,v=next(t,nil)
  while k~=nil do
    count=count+1
    if type(k) ~= "number" or k < 1 or k % 1 ~= 0 then return false end
    k,v=next(t,k)
  end
  return count == n
end

local function lua_scalar(v)
  local tv = type(v)
  if tv == "nil" then return "nil" end
  if tv == "boolean" then return v and "true" or "false" end
  if tv == "number" then
    assert(v == v and v ~= math.huge and v ~= -math.huge, "cannot serialize NaN/Infinity")
    return string.format("%.17g", v)
  end
  if tv == "string" then return string.format("%q", v) end
  error("unsupported Lua snapshot scalar: " .. tv)
end

local function encode(value, indent, seen)
  indent = indent or 0
  seen = seen or {}
  if type(value) ~= "table" then return lua_scalar(value) end
  assert(getmetatable(value)==nil,"snapshot refuses tables with metatables")
  assert(not seen[value], "snapshot contains a cycle")
  seen[value] = true

  local pad = string.rep("  ", indent)
  local child_pad = string.rep("  ", indent + 1)
  local out = { "{" }

  if is_array(value) then
    for i = 1, #value do
      out[#out + 1] = child_pad .. encode(value[i], indent + 1, seen) .. ","
    end
  else
    for _, k in ipairs(Util.sorted_keys(value)) do
      local key
      if type(k) == "string" and string.match(k, "^[%a_][%w_]*$") then
        key = k
      else
        assert(type(k)=="string" or type(k)=="number" or type(k)=="boolean","unsupported snapshot table key")
        key = "[" .. lua_scalar(k) .. "]"
      end
      out[#out + 1] = child_pad .. key .. " = " .. encode(value[k], indent + 1, seen) .. ","
    end
  end

  out[#out + 1] = pad .. "}"
  seen[value] = nil
  return table.concat(out, "\n")
end

function Snapshot.hash(data)
  return tostring(Util.stable_hash(data))
end

function Snapshot.to_lua(data)
  return "return " .. encode(data, 0, {}) .. "\n"
end

local function read_all(path,max_bytes)
  assert(type(path)=="string" and path~="","snapshot path is required")
  local f,err=io.open(path,"rb"); assert(f,err)
  local data=f:read("*a"); f:close()
  max_bytes=max_bytes or Json.DEFAULT_MAX_BYTES
  assert(#data<=max_bytes,"snapshot file exceeds max_bytes")
  return data
end

local function write_all(path,data)
  local f,err=io.open(path,"wb"); assert(f,err)
  local ok,werr=f:write(data)
  if not ok then f:close(); error(werr or "snapshot write failed") end
  f:flush(); f:close()
end

-- Parser for the exact non-executable Lua subset produced by Snapshot.to_lua().
-- It accepts literals/tables only: no calls, operators, control flow, globals, or comments.
local function parse_safe_lua(text,opts)
  opts=opts or {}
  local i,n=1,#text
  local max_depth=opts.max_depth or Contract.LIMITS.max_depth
  local max_nodes=opts.max_nodes or Contract.LIMITS.max_nodes
  local nodes=0
  local function fail(msg) error("invalid safe Lua snapshot at byte "..tostring(i)..": "..msg,0) end
  local function ws()
    while i<=n and text:sub(i,i):match("%s") do i=i+1 end
  end
  local function bump(depth)
    nodes=nodes+1
    if nodes>max_nodes then fail("max_nodes exceeded") end
    if depth>max_depth then fail("max_depth exceeded") end
  end
  local function parse_string()
    local q=text:sub(i,i)
    if q~='"' and q~="'" then fail("expected quoted string") end
    local start=i; i=i+1; local escaped=false
    while i<=n do
      local c=text:sub(i,i)
      if escaped then escaped=false; i=i+1
      elseif c=='\\' then escaped=true; i=i+1
      elseif c==q then
        i=i+1
        local token=text:sub(start,i-1)
        local chunk,err=load("return "..token,"=(snapshot-string)","t",{})
        if not chunk then fail("invalid string literal: "..tostring(err)) end
        local ok,v=pcall(chunk); if not ok or type(v)~="string" then fail("invalid string literal") end
        return v
      else i=i+1 end
    end
    fail("unterminated string")
  end
  local function parse_number()
    local start=i
    while i<=n and text:sub(i,i):match("[0-9eE%+%-%.]") do i=i+1 end
    local token=text:sub(start,i-1)
    local v=tonumber(token)
    if not v or v~=v or v==math.huge or v==-math.huge then fail("invalid finite number") end
    return v
  end
  local parse_value
  local function parse_table(depth)
    if text:sub(i,i)~='{' then fail("expected '{'") end
    i=i+1; ws(); local out={}; local array_index=1; local explicit={}
    if text:sub(i,i)=='}' then i=i+1 return out end
    while true do
      ws(); local c=text:sub(i,i)
      local key=nil; local explicit_key=false
      if c=='[' then
        i=i+1; ws(); key=parse_value(depth+1); ws()
        if text:sub(i,i)~=']' then fail("expected ']'") end
        i=i+1; ws(); if text:sub(i,i)~='=' then fail("expected '='") end
        i=i+1; explicit_key=true
      else
        local ident=text:match("^([%a_][%w_]*)",i)
        if ident then
          local after=i+#ident; local j=after
          while j<=n and text:sub(j,j):match("%s") do j=j+1 end
          if text:sub(j,j)=='=' then key=ident; i=j+1; explicit_key=true end
        end
      end
      ws(); local value=parse_value(depth+1)
      if explicit_key then
        assert(type(key)=="string" or type(key)=="number" or type(key)=="boolean","invalid safe Lua table key")
        if explicit[key] or out[key]~=nil then fail("duplicate table key") end
        explicit[key]=true; out[key]=value
      else
        if out[array_index]~=nil then fail("duplicate array index") end
        out[array_index]=value; array_index=array_index+1
      end
      ws(); local sep=text:sub(i,i)
      if sep==',' or sep==';' then i=i+1; ws(); if text:sub(i,i)=='}' then i=i+1 return out end
      elseif sep=='}' then i=i+1 return out
      else fail("expected ',', ';', or '}'") end
    end
  end
  parse_value=function(depth)
    bump(depth); ws(); local c=text:sub(i,i)
    if c=='{' then return parse_table(depth) end
    if c=='"' or c=="'" then return parse_string() end
    if text:sub(i,i+3)=='true' and not text:sub(i+4,i+4):match('[%w_]') then i=i+4 return true end
    if text:sub(i,i+4)=='false' and not text:sub(i+5,i+5):match('[%w_]') then i=i+5 return false end
    if text:sub(i,i+2)=='nil' and not text:sub(i+3,i+3):match('[%w_]') then i=i+3 return nil end
    if c=='-' or c=='+' or c:match('%d') then return parse_number() end
    fail("only literal values are allowed")
  end
  ws()
  if text:sub(i,i+5)~='return' or text:sub(i+6,i+6):match('[%w_]') then fail("snapshot must begin with return") end
  i=i+6; local value=parse_value(0); ws()
  if i<=n then fail("trailing executable or malformed data") end
  assert(type(value)=="table","snapshot file must return a table")
  return value
end

function Snapshot.write_lua(path, data)
  write_all(path,Snapshot.to_lua(data))
end

function Snapshot.read_lua(path,opts)
  -- v0.9 change: no dofile/loadfile of untrusted snapshots.
  return parse_safe_lua(read_all(path,(opts or {}).max_bytes),opts)
end

function Snapshot.to_json(data,opts)
  return Json.encode(data,opts).."\n"
end

function Snapshot.from_json(text,opts)
  return Json.decode(text,opts)
end

function Snapshot.write_json(path,data,opts)
  write_all(path,Snapshot.to_json(data,opts))
end

function Snapshot.read_json(path,opts)
  return Json.decode(read_all(path,(opts or {}).max_bytes),opts)
end

local function file_exists(path)
  local f=io.open(path,"rb"); if f then f:close(); return true end
  return false
end

function Snapshot.write_runtime_json_atomic(path,data,opts)
  opts=opts or {}
  Contract.assert_snapshot(data,opts.validation)
  local payload=Snapshot.to_json(data,opts.json)
  local token=tostring(Util.stable_hash(path.."|"..payload.."|"..tostring(os.time())))
  local tmp=path..".tmp."..token
  local bak=path..".bak."..token
  local rename=opts.rename or os.rename
  local remove=opts.remove or os.remove
  remove(tmp); remove(bak)
  local ok,err=pcall(function()
    write_all(tmp,payload)
    if opts.after_temp_write then opts.after_temp_write(tmp,path) end
    local had_old=file_exists(path)
    if had_old then
      local rok,rerr=rename(path,bak); assert(rok,rerr or "failed to stage previous snapshot")
    end
    local cok,cerr=rename(tmp,path)
    if not cok then
      if had_old then rename(bak,path) end
      error(cerr or "failed to commit snapshot")
    end
    if had_old then remove(bak) end
  end)
  if not ok then
    remove(tmp)
    if file_exists(bak) and not file_exists(path) then rename(bak,path) end
    error(err,0)
  end
  return true
end

function Snapshot.read_runtime_json(path,opts)
  opts=opts or {}
  local raw=Snapshot.read_json(path,opts.json or opts)
  local migrated=Contract.migrate_snapshot(raw)
  Contract.assert_snapshot(migrated,opts.validation)
  return migrated
end

function Snapshot.write_runtime_lua_atomic(path,data,opts)
  -- Safe Lua subset is retained for compatibility with Termux/demo tooling.
  opts=opts or {}; Contract.assert_snapshot(data,opts.validation)
  local payload=Snapshot.to_lua(data)
  local token=tostring(Util.stable_hash(path.."|"..payload.."|"..tostring(os.time())))
  local tmp=path..".tmp."..token; local bak=path..".bak."..token
  local rename=opts.rename or os.rename; local remove=opts.remove or os.remove
  remove(tmp); remove(bak)
  local ok,err=pcall(function()
    write_all(tmp,payload)
    if opts.after_temp_write then opts.after_temp_write(tmp,path) end
    local had_old=file_exists(path)
    if had_old then local a,b=rename(path,bak); assert(a,b) end
    local a,b=rename(tmp,path)
    if not a then if had_old then rename(bak,path) end; error(b or "failed to commit snapshot") end
    if had_old then remove(bak) end
  end)
  if not ok then remove(tmp); if file_exists(bak) and not file_exists(path) then rename(bak,path) end; error(err,0) end
  return true
end

Snapshot.Contract=Contract
Snapshot.Json=Json

return Snapshot
