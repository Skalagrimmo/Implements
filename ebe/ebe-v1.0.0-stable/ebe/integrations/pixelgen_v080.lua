local Util = require("ebe.util")
local Observation = require("ebe.cognition.observation")

local PixelGen = {}
PixelGen.VERSION = "0.7.0"
PixelGen.SUPPORTED_BUNDLE_VERSION = "0.8.0"

local function count_table(t)
  local n = 0
  for _ in pairs(t or {}) do n = n + 1 end
  return n
end

function PixelGen.validate(bundle)
  assert(type(bundle) == "table", "PixelGen EBE bundle must be a table")
  if bundle.version ~= nil then
    assert(
      bundle.version == PixelGen.SUPPORTED_BUNDLE_VERSION,
      "unsupported PixelGen EBE bundle version "..tostring(bundle.version)
    )
  end

  local contract = bundle.contract or {}
  if contract.global_knowledge ~= nil then
    assert(
      contract.global_knowledge == "forbidden",
      "PixelGen bundle must forbid global knowledge"
    )
  end

  if contract.observation_semantics ~= nil then
    assert(
      contract.observation_semantics == "local evidence only",
      "PixelGen observations must be local evidence only"
    )
  end

  assert(type(bundle.dynamic_entities or {}) == "table", "dynamic_entities must be a table")
  assert(type(bundle.events or {}) == "table", "events must be a table")
  assert(type(bundle.observations or {}) == "table", "observations must be a table")

  local entity_ids = {}
  for _, entity in ipairs(bundle.dynamic_entities or {}) do
    assert(type(entity.id) == "string" and entity.id ~= "", "dynamic entity id is required")
    assert(not entity_ids[entity.id], "duplicate dynamic entity id " .. entity.id)
    entity_ids[entity.id] = true
  end

  local observation_ids = {}
  for _, raw in ipairs(bundle.observations or {}) do
    assert(type(raw.id) == "string" and raw.id ~= "", "observation id is required")
    assert(not observation_ids[raw.id], "duplicate observation id " .. raw.id)
    observation_ids[raw.id] = true
    assert(type(raw.sector) == "table" and #raw.sector == 2, "observation sector must be [sx, sy]")
    if raw.knowledge_state ~= nil then
      assert(
        raw.knowledge_state == "not_yet_assigned_to_any_agent",
        "PixelGen observation already claims agent knowledge"
      )
    end
  end

  return {
    dynamic_entities = #bundle.dynamic_entities,
    events = #bundle.events,
    observations = #bundle.observations,
    static_entities = #(bundle.static_entities or {}),
    contract = Util.deepcopy(contract),
  }
end

function PixelGen.load_file(path)
  assert(type(path) == "string" and path ~= "", "bundle path is required")
  -- v0.9: bridge fixtures are data, never executable input.
  local Snapshot = require("ebe.persistence.snapshot")
  local bundle = Snapshot.read_lua(path)
  PixelGen.validate(bundle)
  return bundle
end

function PixelGen.ingest(runtime, bundle)
  local validation = PixelGen.validate(bundle)
  local imported = {
    entities = 0,
    events = 0,
    observations = 0,
    duplicates = 0,
  }

  runtime.integration_state.pixelgen = runtime.integration_state.pixelgen or {
    entity_ids = {},
    event_ids = {},
    observation_ids = {},
    revisions = {},
  }
  local state = runtime.integration_state.pixelgen

  local revision = tonumber((bundle.source or {}).state_revision) or 0
  state.revisions[revision] = true

  for _, entity in ipairs(bundle.static_entities or {}) do
    local record = runtime.entities[entity.id]
    if not record then
      record = { id = entity.id }
      runtime.entities[entity.id] = record
    end

    if record.static == nil then
      record.static = Util.deepcopy(entity)
      if not state.entity_ids[entity.id] then
        state.entity_ids[entity.id] = true
        imported.entities = imported.entities + 1
      end
    else
      imported.duplicates = imported.duplicates + 1
    end
  end

  for _, entity in ipairs(bundle.dynamic_entities or {}) do
    local record = runtime.entities[entity.id]
    if not record then
      record = { id = entity.id }
      runtime.entities[entity.id] = record
    end

    -- Dynamic state may legitimately be refreshed by a newer PixelGen revision.
    record.dynamic = Util.deepcopy(entity)

    if not state.entity_ids[entity.id] then
      state.entity_ids[entity.id] = true
      imported.entities = imported.entities + 1
    end
  end

  for _, event in ipairs(bundle.events or {}) do
    if not state.event_ids[event.id] then
      local e = Util.deepcopy(event)
      runtime.external_events[#runtime.external_events + 1] = e
      state.event_ids[e.id] = true
      imported.events = imported.events + 1
      runtime.bus:emit("pixelgen.event", Util.deepcopy(e))
    else
      imported.duplicates = imported.duplicates + 1
    end
  end

  for _, raw in ipairs(bundle.observations or {}) do
    if not state.observation_ids[raw.id] then
      local obs = Observation.normalize(raw, {
        evidence = raw.evidence or "direct_local",
        confidence = raw.confidence,
        observed_at = runtime.tick,
        provenance = {
          integration = "pixelgen_v080",
          state_revision = raw.revision or revision,
        },
      })

      -- The evidence is available in a sector. It is NOT automatically
      -- assigned to any agent's memory/knowledge here.
      runtime.available_observations[obs.id] = obs
      state.observation_ids[obs.id] = true
      imported.observations = imported.observations + 1
      runtime.bus:emit("pixelgen.observation_available", Util.deepcopy(obs))
    else
      imported.duplicates = imported.duplicates + 1
    end
  end

  runtime.integration_log[#runtime.integration_log + 1] = {
    kind = "pixelgen_v080",
    tick = runtime.tick,
    revision = revision,
    validation = validation,
    imported = Util.deepcopy(imported),
  }

  return imported
end

return PixelGen
