local Util = require("ebe.util")

local ActionRequest = {}

ActionRequest.VERSION = "0.9.0"
ActionRequest.SUPPORTED_VERSIONS = { ["0.8.0"]=true, ["0.9.0"]=true }
ActionRequest.PIXELGEN_EVENTS = {
  front_escalation = "front",
  front_deescalation = "front",
  territory_strengthen = "territory",
  territory_weaken = "territory",
  territory_alert = "territory",
}

local function finite_number(v)
  return type(v)=="number" and v==v and v~=math.huge and v~=-math.huge
end

local function nonempty_string(v)
  return type(v)=="string" and v~=""
end

local function normalized_roots(list)
  assert(type(list or {})=="table","origin_observation_ids must be a table")
  local seen,out={},{}
  for _,id in ipairs(list or {}) do
    assert(nonempty_string(id),"origin observation ids must be nonempty strings")
    if not seen[id] then
      seen[id]=true
      out[#out+1]=id
    end
  end
  table.sort(out,function(a,b) return tostring(a)<tostring(b) end)
  return out
end

local function normalize_sector(v)
  if v==nil then return nil end
  assert(type(v)=="table" and #v==2,"action sector must be [sx, sy]")
  local x,y=tonumber(v[1]),tonumber(v[2])
  assert(x and y and x>=0 and y>=0 and x%1==0 and y%1==0,
    "action sector coordinates must be nonnegative integers")
  return {x,y}
end

function ActionRequest.subject_from_claim_key(key)
  if type(key)~="string" then return nil,nil end
  local subject_type,subject_id=string.match(key,"^([^:]+):([^:]+):")
  if subject_type=="front" or subject_type=="territory" then
    return subject_type,subject_id
  end
  return nil,nil
end

function ActionRequest.normalize(spec, ctx)
  spec=spec or {}
  ctx=ctx or {}
  assert(type(spec)=="table","action request spec must be a table")

  local domain=spec.domain or "agent_intent"
  assert(domain=="agent_intent" or domain=="pixelgen_world_event",
    "unsupported action request domain "..tostring(domain))

  local action_type=spec.action_type or spec.kind
  assert(nonempty_string(action_type),"action request action_type is required")

  local actor_id=spec.actor_id or ctx.actor_id
  assert(nonempty_string(actor_id),"action request actor_id is required")

  local claim_key=spec.claim_key or ctx.claim_key
  local derived_type,derived_id=ActionRequest.subject_from_claim_key(claim_key)
  local target_type=spec.target_type
  local target_id=spec.target_id
  if spec.target_from_claim==true then
    target_type=target_type or derived_type
    target_id=target_id or derived_id
  end

  local amount=spec.amount
  if domain=="pixelgen_world_event" then
    local expected=ActionRequest.PIXELGEN_EVENTS[action_type]
    assert(expected,"unsupported PixelGen action_type "..tostring(action_type))
    target_type=target_type or expected
    assert(target_type==expected,"PixelGen action target_type does not match action_type")
    assert(nonempty_string(target_id),"PixelGen action request target_id is required")
    amount=tonumber(amount or 0.10)
    assert(finite_number(amount) and amount>0 and amount<=1,
      "PixelGen action request amount must be finite, >0 and <=1")
  else
    if target_type~=nil then assert(nonempty_string(target_type),"agent action target_type must be a string") end
    if target_id~=nil then assert(nonempty_string(target_id),"agent action target_id must be a string") end
    if amount~=nil then
      amount=tonumber(amount)
      assert(finite_number(amount),"agent action amount must be finite")
    end
  end

  local belief=Util.deepcopy(spec.belief or ctx.belief or {})
  local roots=normalized_roots(
    spec.origin_observation_ids or
    belief.origin_observation_ids or
    ctx.origin_observation_ids or {}
  )

  if spec.id~=nil then
    assert(nonempty_string(spec.id) and #spec.id<=256 and not string.find(spec.id,"[%z\1-\31]"),
      "action request id is invalid")
  end

  local out={
    id=spec.id,
    version=ActionRequest.VERSION,
    domain=domain,
    action_type=action_type,
    actor_id=actor_id,
    target_type=target_type,
    target_id=target_id,
    amount=amount,
    sector=normalize_sector(spec.sector or ctx.sector),
    created_at=tonumber(spec.created_at or ctx.created_at) or 0,
    status=spec.status or "pending",
    claim_key=claim_key,
    believed_value=Util.deepcopy(spec.believed_value ~= nil and spec.believed_value or ctx.believed_value),
    confidence=tonumber(spec.confidence or ctx.confidence),
    source_reaction_id=spec.source_reaction_id or ctx.source_reaction_id,
    source_rule_id=spec.source_rule_id or ctx.source_rule_id,
    origin_observation_ids=roots,
    source_count=#roots,
    belief=belief,
    provenance=Util.deepcopy(spec.provenance or ctx.provenance or {}),
    metadata=Util.deepcopy(spec.metadata or {}),
  }
  if out.confidence~=nil then
    assert(finite_number(out.confidence),"action request confidence must be finite")
    out.confidence=Util.clamp(out.confidence)
  end
  assert(out.status=="pending" or out.status=="exported" or
         out.status=="applied" or out.status=="rejected",
    "invalid action request status")
  return out
end

function ActionRequest.validate(req)
  if type(req)~="table" then return false,"action request must be a table" end
  if req.version~=nil and not ActionRequest.SUPPORTED_VERSIONS[req.version] then
    return false,"unsupported action request version "..tostring(req.version)
  end
  local ok,normalized=pcall(ActionRequest.normalize,req,{
    actor_id=req and req.actor_id,
    created_at=req and req.created_at,
    claim_key=req and req.claim_key,
    believed_value=req and req.believed_value,
    confidence=req and req.confidence,
    source_reaction_id=req and req.source_reaction_id,
    source_rule_id=req and req.source_rule_id,
    sector=req and req.sector,
    belief=req and req.belief,
    origin_observation_ids=req and req.origin_observation_ids,
    provenance=req and req.provenance,
  })
  if not ok then return false,tostring(normalized) end
  if not nonempty_string(req.id) or #req.id>256 or string.find(req.id,"[%z\1-\31]") then
    return false,"action request id is invalid"
  end
  return true,normalized
end

function ActionRequest.to_pixelgen_event(req, opts)
  opts=opts or {}
  local ok,err=ActionRequest.validate(req)
  assert(ok,err)
  assert(req.domain=="pixelgen_world_event","request is not a PixelGen world event")
  return {
    id=req.id,
    event_type=req.action_type,
    target_type=req.target_type,
    target_id=req.target_id,
    amount=req.amount,
    sector=Util.deepcopy(req.sector),
    source=opts.source or "ebe_v080_action_request",
    actor_id=req.actor_id,
    cause_id=req.source_reaction_id or req.id,
  }
end

return ActionRequest
