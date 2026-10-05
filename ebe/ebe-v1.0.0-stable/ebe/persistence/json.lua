local Json = {}

Json.VERSION = "0.9.0"
Json.DEFAULT_MAX_BYTES = 16 * 1024 * 1024
Json.DEFAULT_MAX_DEPTH = 96
Json.DEFAULT_MAX_NODES = 250000

local function finite(v)
  return type(v)=="number" and v==v and v~=math.huge and v~=-math.huge
end

local function is_array(t)
  if type(t)~="table" then return false,0 end
  local n,count=0,0
  local k,v=next(t,nil)
  while k~=nil do
    count=count+1
    if type(k)~="number" or k<1 or k%1~=0 then return false,0 end
    if k>n then n=k end
    k,v=next(t,k)
  end
  if count~=n then return false,0 end
  return true,n
end


local function valid_utf8(s)
  local i,n=1,#s
  local function cont(pos)
    local b=string.byte(s,pos)
    return b~=nil and b>=0x80 and b<=0xBF
  end
  while i<=n do
    local b1=string.byte(s,i)
    if b1<=0x7F then
      i=i+1
    elseif b1>=0xC2 and b1<=0xDF then
      if not cont(i+1) then return false,i end
      i=i+2
    elseif b1==0xE0 then
      local b2=string.byte(s,i+1)
      if not (b2 and b2>=0xA0 and b2<=0xBF and cont(i+2)) then return false,i end
      i=i+3
    elseif (b1>=0xE1 and b1<=0xEC) or (b1>=0xEE and b1<=0xEF) then
      if not (cont(i+1) and cont(i+2)) then return false,i end
      i=i+3
    elseif b1==0xED then
      local b2=string.byte(s,i+1)
      if not (b2 and b2>=0x80 and b2<=0x9F and cont(i+2)) then return false,i end
      i=i+3
    elseif b1==0xF0 then
      local b2=string.byte(s,i+1)
      if not (b2 and b2>=0x90 and b2<=0xBF and cont(i+2) and cont(i+3)) then return false,i end
      i=i+4
    elseif b1>=0xF1 and b1<=0xF3 then
      if not (cont(i+1) and cont(i+2) and cont(i+3)) then return false,i end
      i=i+4
    elseif b1==0xF4 then
      local b2=string.byte(s,i+1)
      if not (b2 and b2>=0x80 and b2<=0x8F and cont(i+2) and cont(i+3)) then return false,i end
      i=i+4
    else
      return false,i
    end
  end
  return true
end

local ESC={
  ['"']='\\"', ['\\']='\\\\', ['\b']='\\b', ['\f']='\\f',
  ['\n']='\\n', ['\r']='\\r', ['\t']='\\t',
}

local function quote(s)
  local ok,pos=valid_utf8(s)
  assert(ok,"JSON string is not valid UTF-8 at byte "..tostring(pos))
  return '"'..s:gsub('[%z\1-\31\\"]',function(c)
    return ESC[c] or string.format('\\u%04x',string.byte(c))
  end)..'"'
end

local function encode_value(v,depth,seen,stats,opts)
  stats.nodes=stats.nodes+1
  assert(stats.nodes<=opts.max_nodes,"JSON value exceeds max_nodes")
  assert(depth<=opts.max_depth,"JSON value exceeds max_depth")
  local tv=type(v)
  if tv=="nil" then error("JSON null/nil is not supported by EBE persistence",0) end
  if tv=="boolean" then return v and "true" or "false" end
  if tv=="number" then
    assert(finite(v),"JSON cannot encode NaN/Infinity")
    return string.format("%.17g",v)
  end
  if tv=="string" then return quote(v) end
  assert(tv=="table","JSON unsupported type: "..tv)
  assert(getmetatable(v)==nil,"JSON refuses tables with metatables")
  assert(not seen[v],"JSON cannot encode cyclic tables")
  seen[v]=true
  local arr,n=is_array(v)
  local out={}
  if arr then
    for i=1,n do out[#out+1]=encode_value(v[i],depth+1,seen,stats,opts) end
    seen[v]=nil
    return "["..table.concat(out,",").."]"
  end
  local keys={}
  local k,val=next(v,nil)
  while k~=nil do
    assert(type(k)=="string","JSON object keys must be strings")
    keys[#keys+1]=k
    k,val=next(v,k)
  end
  table.sort(keys)
  for _,key in ipairs(keys) do
    out[#out+1]=quote(key)..":"..encode_value(v[key],depth+1,seen,stats,opts)
  end
  seen[v]=nil
  return "{"..table.concat(out,",").."}"
end

function Json.encode(v,opts)
  opts=opts or {}
  local o={max_depth=opts.max_depth or Json.DEFAULT_MAX_DEPTH,max_nodes=opts.max_nodes or Json.DEFAULT_MAX_NODES}
  return encode_value(v,0,{}, {nodes=0}, o)
end

local function utf8_encode(cp)
  if cp<=0x7F then return string.char(cp) end
  if cp<=0x7FF then
    return string.char(0xC0+math.floor(cp/0x40),0x80+(cp%0x40))
  end
  if cp<=0xFFFF then
    return string.char(0xE0+math.floor(cp/0x1000),0x80+(math.floor(cp/0x40)%0x40),0x80+(cp%0x40))
  end
  assert(cp<=0x10FFFF,"invalid Unicode codepoint")
  return string.char(0xF0+math.floor(cp/0x40000),0x80+(math.floor(cp/0x1000)%0x40),0x80+(math.floor(cp/0x40)%0x40),0x80+(cp%0x40))
end

function Json.decode(text,opts)
  opts=opts or {}
  assert(type(text)=="string","JSON input must be a string")
  local max_bytes=opts.max_bytes or Json.DEFAULT_MAX_BYTES
  assert(#text<=max_bytes,"JSON input exceeds max_bytes")
  local max_depth=opts.max_depth or Json.DEFAULT_MAX_DEPTH
  local max_nodes=opts.max_nodes or Json.DEFAULT_MAX_NODES
  local i,n,nodes=1,#text,0

  local function fail(msg)
    error("invalid JSON at byte "..tostring(i)..": "..msg,0)
  end
  local function ws()
    while i<=n do
      local c=string.byte(text,i)
      if c==32 or c==9 or c==10 or c==13 then i=i+1 else break end
    end
  end
  local function bump(depth)
    nodes=nodes+1
    if nodes>max_nodes then fail("max_nodes exceeded") end
    if depth>max_depth then fail("max_depth exceeded") end
  end
  local parse_value
  local function parse_string()
    if text:sub(i,i)~='"' then fail("expected string") end
    i=i+1
    local out={}
    while i<=n do
      local c=string.byte(text,i)
      if c==34 then
        i=i+1
        local value=table.concat(out)
        local ok,pos=valid_utf8(value)
        if not ok then fail("invalid UTF-8 in string at relative byte "..tostring(pos)) end
        return value
      end
      if c<32 then fail("control character in string") end
      if c==92 then
        i=i+1
        if i>n then fail("unterminated escape") end
        local e=text:sub(i,i)
        local simple={['"']='"',['\\']='\\',['/']='/',b='\b',f='\f',n='\n',r='\r',t='\t'}
        if simple[e] then out[#out+1]=simple[e]; i=i+1
        elseif e=='u' then
          local hex=text:sub(i+1,i+4)
          if #hex<4 or not hex:match('^[0-9a-fA-F]+$') then fail("invalid unicode escape") end
          local cp=tonumber(hex,16); i=i+5
          if cp>=0xD800 and cp<=0xDBFF then
            if text:sub(i,i+1)~='\\u' then fail("high surrogate without low surrogate") end
            local lowhex=text:sub(i+2,i+5)
            if #lowhex<4 or not lowhex:match('^[0-9a-fA-F]+$') then fail("invalid low surrogate") end
            local low=tonumber(lowhex,16)
            if low<0xDC00 or low>0xDFFF then fail("invalid low surrogate") end
            cp=0x10000+(cp-0xD800)*0x400+(low-0xDC00)
            i=i+6
          elseif cp>=0xDC00 and cp<=0xDFFF then
            fail("unexpected low surrogate")
          end
          out[#out+1]=utf8_encode(cp)
        else fail("invalid escape") end
      else
        local start=i
        repeat
          i=i+1
          if i>n then break end
          c=string.byte(text,i)
        until c==34 or c==92 or c<32
        out[#out+1]=text:sub(start,i-1)
      end
    end
    fail("unterminated string")
  end
  local function parse_number()
    local start=i
    if text:sub(i,i)=='-' then i=i+1 end
    if text:sub(i,i)=='0' then
      i=i+1
      if text:sub(i,i):match('%d') then fail("leading zero") end
    else
      if not text:sub(i,i):match('[1-9]') then fail("invalid number") end
      repeat i=i+1 until i>n or not text:sub(i,i):match('%d')
    end
    if text:sub(i,i)=='.' then
      i=i+1
      if not text:sub(i,i):match('%d') then fail("missing fraction digit") end
      repeat i=i+1 until i>n or not text:sub(i,i):match('%d')
    end
    local e=text:sub(i,i)
    if e=='e' or e=='E' then
      i=i+1
      local s=text:sub(i,i)
      if s=='+' or s=='-' then i=i+1 end
      if not text:sub(i,i):match('%d') then fail("missing exponent digit") end
      repeat i=i+1 until i>n or not text:sub(i,i):match('%d')
    end
    local v=tonumber(text:sub(start,i-1))
    if not finite(v) then fail("non-finite number") end
    return v
  end
  local function parse_array(depth)
    i=i+1; ws(); local out={}
    if text:sub(i,i)==']' then i=i+1 return out end
    while true do
      out[#out+1]=parse_value(depth+1); ws()
      local c=text:sub(i,i)
      if c==']' then i=i+1 return out end
      if c~=',' then fail("expected ',' or ']'") end
      i=i+1; ws()
    end
  end
  local function parse_object(depth)
    i=i+1; ws(); local out,seen_keys={},{} 
    if text:sub(i,i)=='}' then i=i+1 return out end
    while true do
      if text:sub(i,i)~='"' then fail("object key must be a string") end
      local key=parse_string(); ws()
      if seen_keys[key] then fail("duplicate object key '"..key.."'") end
      seen_keys[key]=true
      if text:sub(i,i)~=':' then fail("expected ':'") end
      i=i+1; ws(); out[key]=parse_value(depth+1); ws()
      local c=text:sub(i,i)
      if c=='}' then i=i+1 return out end
      if c~=',' then fail("expected ',' or '}'") end
      i=i+1; ws()
    end
  end
  parse_value=function(depth)
    bump(depth); ws()
    local c=text:sub(i,i)
    if c=='"' then return parse_string() end
    if c=='{' then return parse_object(depth) end
    if c=='[' then return parse_array(depth) end
    if c=='-' or c:match('%d') then return parse_number() end
    if text:sub(i,i+3)=='true' then i=i+4 return true end
    if text:sub(i,i+4)=='false' then i=i+5 return false end
    if text:sub(i,i+3)=='null' then fail("null is not supported by EBE persistence") end
    fail("unexpected token")
  end
  ws(); local value=parse_value(0); ws()
  if i<=n then fail("trailing data") end
  return value
end

return Json
