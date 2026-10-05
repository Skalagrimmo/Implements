local event_factory = require("ebe.core.event")
local EventBus = require("ebe.core.event_bus")
local ManualClock = require("ebe.core.clock")
local StateStore = require("ebe.core.state_store")
local RingBuffer = require("ebe.core.ring_buffer")
local MemoryStore = require("ebe.memory.memory_store")
local KnowledgeStore = require("ebe.perception.knowledge_store")
local ObservationSystem = require("ebe.perception.observation_system")
local ObserverRegistry = require("ebe.perception.observer_registry")
local Interpreter = require("ebe.interpretation.interpreter")
local PropagationSystem = require("ebe.propagation.propagation_system")
local ReactionSystem = require("ebe.reaction.reaction_system")
local util = require("ebe.core.util")

local M = {}

function M.create(config)
  config = config or {}
  local clock = config.clock or ManualClock.new()
  local bus = config.bus or EventBus.new()
  local state = config.state or StateStore.new()
  local memory = config.memory or MemoryStore.new()
  local knowledge = config.knowledge or KnowledgeStore.new()
  local get_observers = config.get_observers or function() return {} end
  local get_observer = config.get_observer
  local observer_registry = config.observer_registry or ObserverRegistry.new()
  local interpreter = config.interpreter or Interpreter.new(config.interpretation or {})
  local observation = config.observation or ObservationSystem.new({
    get_observers = get_observers,
    observe = config.observe or function() return 0 end,
  })
  local propagation = config.propagation or PropagationSystem.new({
    get_observers = get_observers,
    knowledge = knowledge,
    interpreter = interpreter,
    transmission_factor = config.transmission_factor or function() return 0 end,
    min_source_confidence = config.min_source_confidence or 0.5,
    min_received_confidence = config.min_received_confidence or 0.2,
    get_candidates = config.get_candidates,
    random = config.random,
  })
  local reactions = config.reactions or ReactionSystem.new(config.reaction_rules or {})
  local history = {}
  local interpretation_cache = {}

  local max_log_size = config.max_log_size
  if max_log_size == nil then max_log_size = 5000 end
  local effective_log_size = (max_log_size == 0 or max_log_size == math.huge) and math.huge or max_log_size
  if effective_log_size ~= math.huge then
    assert(type(effective_log_size) == "number" and effective_log_size > 0 and math.floor(effective_log_size) == effective_log_size,
      "max_log_size must be a positive integer, 0, or math.huge")
  end
  local reaction_log = RingBuffer.new(effective_log_size)
  local transmission_log = RingBuffer.new(effective_log_size)
  local max_depth = config.max_depth or 4
  local propagation_history_window = config.propagation_history_window or math.huge

  local api = {}

  local function cache_key(observer_id, event_id)
    return tostring(observer_id) .. "\0" .. tostring(event_id)
  end

  local function interpret_for(observer, event)
    local key = cache_key(observer.id, event.id)
    local result = interpretation_cache[key]
    if not result then
      result = interpreter:interpret(event, observer)
      interpretation_cache[key] = result
    end
    return result
  end

  local emit

  local function apply_reaction(reaction, parent_event)
    if not reaction then return end
    local log_item = util.deep_copy(reaction)
    log_item.time = clock:now()
    log_item.parent_event_id = parent_event.id
    reaction_log:push(log_item)

    if reaction.type == "mutation" then
      local key = reaction.target
      if reaction.mode == "add" then
        state:update(key, function(old)
          return tonumber(old or 0) + tonumber(reaction.value or 0)
        end, 0)
      else
        state:set(key, reaction.value)
      end
    end

    if reaction.type == "event" and parent_event.depth < max_depth then
      local input = util.deep_copy(reaction.event or {})
      input.parent_id = parent_event.id
      input.depth = parent_event.depth + 1
      emit(input)
    end
  end

  local function run_reactions(event, observer)
    local k = knowledge:get(observer.id, event.id)
    if not k then return {} end
    local interpretation = interpret_for(observer, event)
    local produced = reactions:react({
      event = event,
      observer = observer,
      knowledge = k,
      interpretation = interpretation,
      engine = api,
    })
    for i = 1, #produced do apply_reaction(produced[i], event) end
    return produced
  end

  emit = function(input)
    local event = event_factory.create(input, clock:now())
    history[#history + 1] = event
    memory:remember("world", "event:" .. event.id, event, clock:now(), { type = event.type })

    local observations = observation:observers_of(event)
    for i = 1, #observations do
      local observer = observations[i].observer
      local confidence = observations[i].confidence
      local interpretation = interpret_for(observer, event)
      knowledge:set(observer.id, event.id, confidence, {
        source = "witness",
        spin = interpretation.label,
        time = clock:now(),
      })
      memory:remember(observer.id, "event:" .. event.id, { confidence = confidence, source = "witness" }, clock:now())
      run_reactions(event, observer)
    end

    bus:emit(event)
    return event
  end

  local function advance(delta)
    clock:advance(delta or 1)
    local new_transmissions = {}
    local observers = get_observers()
    if not get_observer then observer_registry:rebuild(observers) end
    local resolve_observer = get_observer or function(id) return observer_registry:get(id) end

    local window_start = 1
    if propagation_history_window ~= math.huge then
      window_start = math.max(1, #history - propagation_history_window + 1)
    end

    for i = window_start, #history do
      local event = history[i]
      local transmissions = propagation:propagate(event, clock:now(), observers)
      for j = 1, #transmissions do
        local t = transmissions[j]
        local log_item = util.deep_copy(t)
        log_item.time = clock:now()
        transmission_log:push(log_item)
        new_transmissions[#new_transmissions + 1] = t
        local observer = resolve_observer(t.target)
        if observer then
          memory:remember(observer.id, "event:" .. event.id, { confidence = t.confidence, source = t.source }, clock:now())
          run_reactions(event, observer)
        end
      end
    end

    knowledge:decay(config.decay_rate or 0.96, config.decay_minimum or 0.08)
    return new_transmissions
  end

  local function snapshot()
    return {
      version = 1,
      time = clock:now(),
      state = state:snapshot(),
      memory = memory:snapshot(),
      knowledge = knowledge:snapshot(),
      history = util.deep_copy(history),
      reaction_log = util.deep_copy(reaction_log:to_array()),
      transmission_log = util.deep_copy(transmission_log:to_array()),
    }
  end

  local function restore(snap)
    snap = snap or {}
    state:restore(snap.state or {})
    memory:restore(snap.memory or {})
    knowledge:restore(snap.knowledge or {})
    for i = #history, 1, -1 do history[i] = nil end
    local restored_history = util.deep_copy(snap.history or {})
    for i = 1, #restored_history do history[i] = restored_history[i] end
    reaction_log:restore(util.deep_copy(snap.reaction_log or {}))
    transmission_log:restore(util.deep_copy(snap.transmission_log or {}))
    interpretation_cache = {}
    if util.is_finite(snap.time) then clock:set(snap.time) end
  end

  local function clear()
    state:clear()
    memory:clear()
    knowledge:clear()
    for i = #history, 1, -1 do history[i] = nil end
    reaction_log:clear()
    transmission_log:clear()
    interpretation_cache = {}
    observer_registry:clear()
    clock:set(0)
  end

  api.emit = emit
  api.advance = advance
  api.on = function(event_type, handler) return bus:on(event_type, handler) end
  api.interpret_for = interpret_for
  api.snapshot = snapshot
  api.restore = restore
  api.clear = clear
  api.clock = clock
  api.state = state
  api.memory = memory
  api.knowledge = knowledge
  api.history = history
  api.reaction_log = reaction_log
  api.transmission_log = transmission_log
  api.observer_registry = observer_registry

  return api
end

return M
