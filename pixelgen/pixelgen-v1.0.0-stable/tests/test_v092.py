from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.runtime_api import (
    RUNTIME_API_VERSION,
    CONTRACT_FREEZE_VERSION,
    load_runtime_profile,
    generate_semantic_world,
    initialize_state,
    apply_event,
    replay_events,
    ebe_runtime_bundle,
    contract,
    validate_public_artifact,
    migrate_public_artifact,
    write_public_bundle,
    verify_public_bundle,
    world_fingerprint,
)
from pixelgen.schema_contracts import contract_fingerprint
from pixelgen.migrations import MigrationRequiresRegeneration

profile=load_runtime_profile()
world=generate_semantic_world(profile,7301,6,5,4)

assert world["generator"]["version"]=="1.0.0"
assert world["schema_versions"]["world"]=="0.7"
assert world["schema_versions"]["regional_corridors"]=="0.9.0"
assert world["schema_versions"]["runtime_api"]=="1.0.0"
assert world["schema_versions"]["render_api"]=="0.9.1"
assert world["schema_versions"]["contract_manifest"]=="1.0.0"
assert RUNTIME_API_VERSION=="1.0.0"
assert CONTRACT_FREEZE_VERSION=="1.0.0"

# Canonical semantics are intentionally unchanged from v0.9.1.
assert world_fingerprint(world)=="ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a"

public=contract()
assert public["contract_version"]=="1.0.0"
assert public["status"]=="stable"
assert public["contract_fingerprint"]==contract_fingerprint()
assert len(public["contract_fingerprint"])==64

# All public artifacts used by the three-engine bridge validate independently.
state=initialize_state(world)
fronts=sorted(state.get("fronts",{}))
territories=sorted(state.get("territories",{}))
if fronts:
    state=apply_event(world,state,{
        "event_type":"front_escalation",
        "target_id":fronts[0],
        "amount":0.20,
        "source":"test_v092",
    })
if territories:
    state=apply_event(world,state,{
        "event_type":"territory_weaken",
        "target_id":territories[0],
        "amount":0.12,
        "source":"test_v092",
    })
assert replay_events(world,state["event_log"])==state

bundle=ebe_runtime_bundle(world,state)
for value,kind in (
    (world,"world"),
    (state,"world_state"),
    (state["event_log"],"runtime_events"),
    (bundle,"ebe_runtime"),
    (world["regional_corridors"],"regional_corridors"),
):
    result=validate_public_artifact(value,kind)
    assert result["status"]=="pass", result

# EBE's epistemic boundary is part of the frozen contract.
bad_ebe=deepcopy(bundle)
bad_ebe["contract"]["global_knowledge"]="allowed"
assert validate_public_artifact(bad_ebe,"ebe_runtime")["status"]=="fail"

# v0.9.1 worlds use metadata-only migration: semantic fingerprint must survive.
legacy_091=deepcopy(world)
legacy_091["generator"]["version"]="0.9.1"
legacy_091["schema_versions"]["runtime_api"]="0.9.1"
legacy_091["schema_versions"].pop("contract_manifest",None)
legacy_091["gameplay"]["generator_version"]="0.9.1"
legacy_fp=world_fingerprint(legacy_091)
pre=validate_public_artifact(legacy_091,"world")
assert pre["status"]=="pass"
assert pre["details"]["compatibility"]=="metadata_migratable"
migrated,report=migrate_public_artifact(legacy_091,"world")
assert report["mode"]=="metadata_only"
assert report["semantic_identity_preserved"] is True
assert world_fingerprint(migrated)==legacy_fp
assert migrated["generator"]["version"]=="0.9.1"  # provenance is preserved
assert migrated["schema_versions"]["runtime_api"]=="1.0.0"
assert migrated["schema_versions"]["render_api"]=="0.9.1"
assert migrated["schema_versions"]["contract_manifest"]=="1.0.0"
assert validate_public_artifact(migrated,"world")["details"]["compatibility"]=="current"

# v0.9.0 is also metadata-migratable because it already contains corridors.
legacy_090=deepcopy(world)
legacy_090["generator"]["version"]="0.9.0"
legacy_090["schema_versions"].pop("runtime_api",None)
legacy_090["schema_versions"].pop("render_api",None)
legacy_090["schema_versions"].pop("contract_manifest",None)
m090,r090=migrate_public_artifact(legacy_090,"world")
assert r090["mode"]=="metadata_only"
assert world_fingerprint(m090)==world_fingerprint(legacy_090)
assert m090["schema_versions"]["runtime_api"]=="1.0.0"
assert m090["schema_versions"]["render_api"]=="0.9.1"

# Pre-corridor worlds cannot be "upgraded" by fabricating semantic geography.
legacy_080=deepcopy(world)
legacy_080["generator"]["version"]="0.8.0"
legacy_080["schema_versions"].pop("regional_corridors",None)
legacy_080["schema_versions"].pop("contract_manifest",None)
legacy_080.pop("regional_corridors",None)
try:
    migrate_public_artifact(legacy_080,"world")
    raise AssertionError("pre-corridor world was silently fabricated into current schema")
except MigrationRequiresRegeneration:
    pass

# State/event/EBE payload versions are already mature and migrate as exact no-ops.
for value,kind in (
    (state,"world_state"),
    (state["event_log"],"runtime_events"),
    (bundle,"ebe_runtime"),
):
    migrated_value,migration_report=migrate_public_artifact(value,kind)
    assert migrated_value==value
    assert migration_report["mode"]=="already_compatible"

# Contract bundles are deterministic, self-verifying and relationship-aware.
with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
    p1,m1=write_public_bundle(td1,world=world,state=state,events=state["event_log"],ebe_runtime=bundle)
    p2,m2=write_public_bundle(td2,world=world,state=state,events=state["event_log"],ebe_runtime=bundle)
    assert m1==m2
    assert validate_public_artifact(m1,"contract_manifest")["status"]=="pass"
    assert verify_public_bundle(td1)["status"]=="pass"
    assert verify_public_bundle(td2)["status"]=="pass"

    # Tampering must be detected by the file hash before semantics are trusted.
    events_path=Path(td1)/"events.json"
    tampered=json.loads(events_path.read_text(encoding="utf-8"))
    tampered[0]["amount"]=0.99
    events_path.write_text(json.dumps(tampered,indent=2,sort_keys=True),encoding="utf-8")
    bad=verify_public_bundle(td1)
    assert bad["status"]=="fail"
    assert any("mismatch" in e for e in bad["errors"])

# Machine-readable schema documents must be valid JSON Schema documents.
try:
    import jsonschema
except ImportError:
    jsonschema=None

schema_files={
    "world":"world-0.7.schema.json",
    "world_state":"world-state-0.8.0.schema.json",
    "runtime_events":"runtime-events-0.8.0.schema.json",
    "ebe_runtime":"ebe-runtime-0.8.0.schema.json",
    "regional_corridors":"regional-corridors-0.9.0.schema.json",
}
values={
    "world":world,
    "world_state":state,
    "runtime_events":state["event_log"],
    "ebe_runtime":bundle,
    "regional_corridors":world["regional_corridors"],
}
for kind,name in schema_files.items():
    schema=json.loads((ROOT/"schemas"/name).read_text(encoding="utf-8"))
    assert schema["$schema"].endswith("2020-12/schema")
    if jsonschema is not None:
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(values[kind],schema)

# Contract CLI remains renderer-free even with Pillow imports blocked.
probe=r'''
import sys, importlib.abc
for _k in list(sys.modules):
    if _k == "PIL" or _k.startswith("PIL."):
        del sys.modules[_k]
class BlockPIL(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "PIL" or fullname.startswith("PIL."):
            raise ImportError("PIL blocked")
        return None
sys.meta_path.insert(0, BlockPIL())
sys.path.insert(0, %r)
from pixelgen.runtime_api import contract, capabilities
assert contract()["contract_version"] == "1.0.0"
assert capabilities()["schema_contracts"] is True
import runtime_cli
print("contract-cli-renderer-free")
''' % str(ROOT)
p=subprocess.run([sys.executable,"-c",probe],capture_output=True,text=True,timeout=30)
assert p.returncode==0,p.stderr
assert p.stdout.strip()=="contract-cli-renderer-free"

print("PixelGen v1.0.0 schema / migration compatibility tests passed")
