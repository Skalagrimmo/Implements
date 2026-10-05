from copy import deepcopy
from pathlib import Path
import tempfile

from pixelgen import __version__
from pixelgen.runtime_api import (
    RUNTIME_API_VERSION, load_runtime_profile, generate_semantic_world,
    initialize_state, apply_event, replay_events, ebe_runtime_bundle,
    contract, capabilities, migrate_public_artifact, write_public_bundle,
    verify_public_bundle, world_fingerprint,
)
from pixelgen.schema_contracts import CONTRACT_FREEZE_VERSION, CONTRACT_STATUS

assert __version__ == "1.0.0"
assert RUNTIME_API_VERSION == "1.0.0"
assert CONTRACT_FREEZE_VERSION == "1.0.0"
assert CONTRACT_STATUS == "stable"
assert contract()["status"] == "stable"
assert capabilities()["version"] == "1.0.0"
assert capabilities()["contract_status"] == "stable"

profile=load_runtime_profile()
world=generate_semantic_world(profile,7301,6,5,4)
assert world["generator"]["version"] == "1.0.0"
assert world["schema_versions"]["runtime_api"] == "1.0.0"
assert world["schema_versions"]["contract_manifest"] == "1.0.0"
# Promotion is metadata-only relative to the 0.9.x semantic baseline.
assert world_fingerprint(world) == "ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a"

legacy=deepcopy(world)
legacy["generator"]["version"]="0.9.3"
legacy["schema_versions"]["runtime_api"]="0.9.3"
legacy["schema_versions"]["contract_manifest"]="0.9.3"
if isinstance(legacy.get("gameplay"),dict): legacy["gameplay"]["generator_version"]="0.9.3"
fp=world_fingerprint(legacy)
migrated,report=migrate_public_artifact(legacy,"world")
assert report["mode"] == "metadata_only"
assert report["semantic_identity_preserved"] is True
assert world_fingerprint(migrated) == fp
assert migrated["generator"]["version"] == "0.9.3"  # provenance stays truthful
assert migrated["schema_versions"]["runtime_api"] == "1.0.0"
assert migrated["schema_versions"]["contract_manifest"] == "1.0.0"

state=initialize_state(world)
fronts=sorted(state["fronts"])
territories=sorted(state["territories"])
if fronts:
    state=apply_event(world,state,{"event_type":"front_escalation","target_id":fronts[0],"amount":.2,"source":"v100"})
if territories:
    state=apply_event(world,state,{"event_type":"territory_alert","target_id":territories[0],"amount":.1,"source":"v100"})
assert replay_events(world,state["event_log"]) == state
ebe=ebe_runtime_bundle(world,state)

with tempfile.TemporaryDirectory() as td:
    bundle=Path(td)/"bundle"
    _,manifest=write_public_bundle(bundle,world=world,state=state,events=state["event_log"],ebe_runtime=ebe)
    assert manifest["manifest_version"] == "1.0.0"
    assert manifest["contract_status"] == "stable"
    result=verify_public_bundle(bundle)
    assert result["status"] == "pass", result
    assert result["contract_version"] == "1.0.0"

print("PixelGen v1.0.0 stable promotion / parity / bundle tests passed")
