local Util = require("ebe.util")
local ActionRequest = require("ebe.action.action_request")

local Gateway={}
Gateway.__index=Gateway

local function defaults()
  return {
    avoid_front={
      domain="agent_intent",
      action_type="avoid_front",
      target_from_claim=true,
    },
    prepare_exit={
      domain="agent_intent",
      action_type="prepare_exit",
      target_from_claim=true,
    },
  }
end

function Gateway.new(opts)
  opts=opts or {}
  local self=setmetatable({
    version="0.9.0",
    sequence=0,
    requests={},
    order={},
    adapters={},
    log={},
    log_capacity=tonumber(opts.log_capacity) or 512,
    default_reaction_intents=opts.default_reaction_intents ~= false,
  },Gateway)
  if self.default_reaction_intents then
    for kind,spec in pairs(defaults()) do self.adapters[kind]=Util.deepcopy(spec) end
  end
  for kind,spec in pairs(opts.adapters or {}) do self:register_adapter(kind,spec) end
  return self
end

function Gateway:_log(entry)
  self.log[#self.log+1]=Util.deepcopy(entry)
  while #self.log>self.log_capacity do table.remove(self.log,1) end
end

function Gateway:register_adapter(reaction_kind,spec)
  assert(type(reaction_kind)=="string" and reaction_kind~="","reaction kind is required")
  assert(type(spec)=="table","reaction action adapter must be declarative table")
  -- Store declarative data only so snapshots remain deterministic/portable.
  self.adapters[reaction_kind]=Util.deepcopy(spec)
  return self.adapters[reaction_kind]
end

function Gateway:submit(runtime,spec,ctx)
  self.sequence=self.sequence+1
  spec=Util.deepcopy(spec or {})
  assert(spec.status==nil or spec.status=="pending","new action requests must begin pending")
  spec.status="pending"
  spec.exported_at=nil; spec.exported_event=nil; spec.resolved_at=nil; spec.result=nil
  spec.id=spec.id or ("ebe_action_"..tostring(self.sequence))
  spec.created_at=spec.created_at or runtime.tick
  local req=ActionRequest.normalize(spec,ctx or {})
  assert(not self.requests[req.id],"duplicate action request id "..req.id)
  self.requests[req.id]=req
  self.order[#self.order+1]=req.id
  self:_log({tick=runtime.tick,kind="action_requested",action_id=req.id,domain=req.domain,action_type=req.action_type})
  runtime.bus:emit("action.requested",Util.deepcopy(req))
  return Util.deepcopy(req)
end

function Gateway:from_reaction(runtime,reaction,agent,belief)
  local adapter=self.adapters[reaction.kind]
  if not adapter then return nil end
  local spec=Util.deepcopy(adapter)
  spec.actor_id=spec.actor_id or agent.id
  spec.claim_key=spec.claim_key or reaction.claim_key or (belief and belief.key)
  spec.believed_value=spec.believed_value ~= nil and spec.believed_value or reaction.believed_value or (belief and belief.value)
  spec.confidence=spec.confidence or reaction.confidence or (belief and belief.confidence)
  spec.source_reaction_id=reaction.id
  spec.source_rule_id=reaction.rule_id
  spec.sector=spec.sector or Util.deepcopy(agent.sector)
  spec.belief=Util.deepcopy(belief or {})
  spec.origin_observation_ids=Util.deepcopy((belief or {}).origin_observation_ids or {})
  spec.provenance=Util.deepcopy(spec.provenance or {})
  spec.provenance.reaction={
    id=reaction.id,
    kind=reaction.kind,
    rule_id=reaction.rule_id,
    tick=reaction.tick,
  }
  return self:submit(runtime,spec,{})
end

function Gateway:get(id)
  return self.requests[id] and Util.deepcopy(self.requests[id]) or nil
end

function Gateway:list(status,domain)
  local out={}
  for _,id in ipairs(self.order) do
    local req=self.requests[id]
    if (status==nil or req.status==status) and (domain==nil or req.domain==domain) then
      out[#out+1]=Util.deepcopy(req)
    end
  end
  return out
end

function Gateway:export_pixelgen(runtime,id,opts)
  local req=assert(self.requests[id],"unknown action request "..tostring(id))
  assert(req.domain=="pixelgen_world_event","action request is not a PixelGen world event")
  assert(req.status=="pending" or req.status=="exported","action request is already resolved")
  local event=ActionRequest.to_pixelgen_event(req,opts or {})
  req.status="exported"
  req.exported_at=req.exported_at or runtime.tick
  req.exported_event=Util.deepcopy(event)
  self:_log({tick=runtime.tick,kind="action_exported",action_id=id,pixelgen_event_id=event.id})
  runtime.bus:emit("action.exported",{request=Util.deepcopy(req),pixelgen_event=Util.deepcopy(event)})
  return Util.deepcopy(event)
end

function Gateway:resolve(runtime,id,status,result)
  local req=assert(self.requests[id],"unknown action request "..tostring(id))
  assert(status=="applied" or status=="rejected","action result must be applied or rejected")
  if status=="applied" and req.domain=="pixelgen_world_event" then
    assert(req.status=="exported","PixelGen action can only be applied after export")
  end
  if req.status=="applied" or req.status=="rejected" then
    assert(req.status==status,"action request already resolved as "..tostring(req.status))
    return Util.deepcopy(req),false
  end
  req.status=status
  req.resolved_at=runtime.tick
  req.result=Util.deepcopy(result or {})
  self:_log({tick=runtime.tick,kind="action_"..status,action_id=id,result=Util.deepcopy(result or {})})
  runtime.bus:emit("action."..status,Util.deepcopy(req))
  return Util.deepcopy(req),true
end

function Gateway:correlate_pixelgen_bundle(runtime,bundle)
  local resolved=0
  for _,event in ipairs((bundle or {}).events or {}) do
    local cause=event.cause_event_id
    local req=cause and self.requests[cause] or nil
    if req and req.domain=="pixelgen_world_event" and req.status=="exported" then
      local exported=req.exported_event or {}
      local subject_match=(event.subject_type==nil or event.subject_type==req.target_type) and
                          (event.subject_id==nil or event.subject_id==req.target_id)
      local export_match=exported.id==req.id and exported.event_type==req.action_type and
                         exported.target_type==req.target_type and exported.target_id==req.target_id
      if subject_match and export_match then
        self:resolve(runtime,cause,"applied",{
          authority="PixelGen",
          derived_event_id=event.id,
          revision=event.revision,
          event_type=event.event_type,
          subject_type=event.subject_type,
          subject_id=event.subject_id,
        })
        resolved=resolved+1
      end
    end
  end
  return resolved
end

function Gateway:snapshot()
  return {
    version=self.version,
    sequence=self.sequence,
    requests=Util.deepcopy(self.requests),
    order=Util.deepcopy(self.order),
    adapters=Util.deepcopy(self.adapters),
    log=Util.deepcopy(self.log),
    log_capacity=self.log_capacity,
    default_reaction_intents=self.default_reaction_intents,
  }
end

function Gateway.restore(data)
  data=data or {}
  local g=Gateway.new({
    log_capacity=data.log_capacity,
    default_reaction_intents=false,
  })
  g.version="0.9.0"
  g.sequence=tonumber(data.sequence) or 0
  g.requests=Util.deepcopy(data.requests or {})
  g.order=Util.deepcopy(data.order or {})
  g.adapters=Util.deepcopy(data.adapters or {})
  g.log=Util.deepcopy(data.log or {})
  g.default_reaction_intents=data.default_reaction_intents ~= false
  -- Old/empty snapshots receive the harmless default local-intent adapters.
  if next(g.adapters)==nil and g.default_reaction_intents then
    for kind,spec in pairs(defaults()) do g.adapters[kind]=Util.deepcopy(spec) end
  end
  return g
end

return Gateway
