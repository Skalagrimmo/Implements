local Util=require("ebe.util")
local Persistence=require("ebe.persistence.contract")

local C={}
C.VERSION="1.0.0"
C.EXPORTS={
  "version","create","LegacyEvent","LegacyEventBus","ManualClock","StateStore","RingBuffer","SpatialGrid",
  "MemoryStore","KnowledgeStore","ObservationSystem","ObserverRegistry","LegacyInterpreter","PropagationSystem",
  "ReactionSystem","Runtime","Event","EventBus","Observation","Memory","Belief","Knowledge","Interpretation",
  "Propagation","Reaction","ActionRequest","ActionGateway","SourceLineage","Institution","InstitutionalPolicy",
  "InformationEcology","Collective","PixelGenV080","PixelGenNetworkSynth","Snapshot","Json","PersistenceContract",
  "PublicContract",
}
C.RUNTIME_METHODS={
  "new","add_agent","move_agent","connect_agents","add_institution","set_institution_editorial_policy",
  "institution_policy_view","subscribe_institution","report_to_institution","add_collective","add_collective_member",
  "remove_collective_member","subscribe_collective","submit_to_collective","get_collective_consensus","collective_view",
  "publish_collective","register_reaction_action_adapter","request_action","action_request","action_requests",
  "export_pixelgen_action","resolve_action_request","synthesize_pixelgen_network","synthesize_pixelgen_network_file",
  "attach_agent_to_network","local_institution","report_to_local_network","ingest_pixelgen","ingest_pixelgen_file",
  "assign_local_observations","share","get_belief","get_knowledge","restore",
  "advance","agent_view","snapshot","summary",
}
function C.describe()
  return {
    version=C.VERSION,
    compatibility="stable 1.0 public contract",
    package_exports=Util.deepcopy(C.EXPORTS),
    runtime_methods=Util.deepcopy(C.RUNTIME_METHODS),
    persistence=Persistence.public_contract(),
    pixelgen_runtime_bundle="0.8.0",
    invariants={
      event_observation_memory_belief_knowledge_separation=true,
      message_copies_not_independent_evidence=true,
      membership_not_shared_knowledge=true,
      policy_priority_not_truth=true,
      action_request_not_authority=true,
      pixelgen_remains_world_authority=true,
    },
  }
end
function C.fingerprint()
  return "ebe-stablehash-v1:"..tostring(Util.stable_hash(C.describe()))
end
function C.assert_package(pkg)
  for _,name in ipairs(C.EXPORTS) do assert(pkg[name]~=nil,"missing frozen package export "..name) end
  local Runtime=assert(pkg.Runtime,"Runtime missing")
  for _,name in ipairs(C.RUNTIME_METHODS) do assert(type(Runtime[name])=="function","missing frozen Runtime method "..name) end
  return true
end
return C
