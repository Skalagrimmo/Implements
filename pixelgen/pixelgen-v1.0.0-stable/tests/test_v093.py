from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen import __version__
from pixelgen.runtime_api import (
    RUNTIME_API_VERSION, CONTRACT_FREEZE_VERSION,
    load_runtime_profile, generate_semantic_world, initialize_state, apply_event,
    replay_events, ebe_runtime_bundle, validate_public_artifact,
    migrate_public_artifact, write_public_bundle, verify_public_bundle,
    capabilities, world_fingerprint,
)
from pixelgen.schema_contracts import contract_fingerprint
from pixelgen.migrations import MigrationError, MigrationRequiresRegeneration
from pixelgen.json_io import strict_json_loads, StrictJSONError
from pixelgen.atomic_io import atomic_write_bytes, commit_staged_directory
import pixelgen.atomic_io as atomic_io
import pixelgen.contract_bundle as contract_bundle
import pixelgen.runtime_api as runtime_api

profile=load_runtime_profile()
world=generate_semantic_world(profile,7301,6,5,4)
assert __version__=="1.0.0"
assert RUNTIME_API_VERSION=="1.0.0"
assert CONTRACT_FREEZE_VERSION=="1.0.0"
assert world["generator"]["version"]=="1.0.0"
assert world["schema_versions"]["runtime_api"]=="1.0.0"
assert world["schema_versions"]["contract_manifest"]=="1.0.0"
assert world_fingerprint(world)=="ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a"
assert len(contract_fingerprint())==64
assert capabilities()["transactional_public_writes"] is True
assert capabilities()["hostile_json_safe_validation"] is True

state=initialize_state(world)
fronts=sorted(state["fronts"])
territories=sorted(state["territories"])
if fronts:
    state=apply_event(world,state,{"event_type":"front_escalation","target_id":fronts[0],"amount":0.2,"source":"test_v093"})
if territories:
    state=apply_event(world,state,{"event_type":"territory_alert","target_id":territories[0],"amount":0.11,"source":"test_v093"})
assert replay_events(world,state["event_log"])==state
ebe=ebe_runtime_bundle(world,state)

# ---------------------------------------------------------------------------
# Hostile JSON / validator hardening.
# Validators must cleanly return fail and never throw for arbitrary JSON shapes.
# ---------------------------------------------------------------------------
hostile_values=[
    None, True, False, 0, 1.5, "x", {}, [], [None], [{"id":{}}],
    {"generator":[],"schema_versions":[],"sectors":[]},
]
for kind in ("world","world_state","runtime_events","ebe_runtime","regional_corridors","contract_manifest"):
    for value in hostile_values:
        result=validate_public_artifact(value,kind)
        assert isinstance(result,dict)
        assert result["status"] in ("pass","fail")

bad=deepcopy(world); bad["seed"]=True
assert validate_public_artifact(bad,"world")["status"]=="fail"
bad=deepcopy(world); bad["cols"]=True
assert validate_public_artifact(bad,"world")["status"]=="fail"
bad=deepcopy(world); bad["sectors"][1]["sx"]=bad["sectors"][0]["sx"]; bad["sectors"][1]["sy"]=bad["sectors"][0]["sy"]
assert validate_public_artifact(bad,"world")["status"]=="fail"
bad=deepcopy(world); bad["generator"]["name"]="OtherGen"
assert validate_public_artifact(bad,"world")["status"]=="fail"

bad=deepcopy(state); bad["source_world"]["fingerprint"]="z"*64
assert validate_public_artifact(bad,"world_state")["status"]=="fail"
bad=deepcopy(state); bad["clock"]["revision"]=True
assert validate_public_artifact(bad,"world_state")["status"]=="fail"
bad=deepcopy(state); bad["mutations"]=bad["mutations"][:-1]
assert validate_public_artifact(bad,"world_state")["status"]=="fail"
if territories:
    bad=deepcopy(state); bad["territories"][territories[0]]["alert"]=float("nan")
    assert validate_public_artifact(bad,"world_state")["status"]=="fail"

valid_event={"id":"e1","event_type":"front_escalation","target_type":"front","target_id":"front_0","amount":0.2,"source":"hostile"}
for mutation in (
    {"id":{}},
    {"amount":True},
    {"amount":float("nan")},
    {"amount":float("inf")},
    {"event_type":"unknown"},
    {"target_type":"territory"},
    {"source":""},
    {"sector":[True,0]},
):
    event=deepcopy(valid_event); event.update(mutation)
    result=validate_public_artifact([event],"runtime_events")
    assert result["status"]=="fail", (mutation,result)

bad=deepcopy(ebe); bad["contract"]["global_knowledge"]="allowed"
assert validate_public_artifact(bad,"ebe_runtime")["status"]=="fail"
bad=deepcopy(ebe); bad["source"]["state_revision"]=True
assert validate_public_artifact(bad,"ebe_runtime")["status"]=="fail"
if bad.get("observations"):
    pass
bad=deepcopy(ebe)
if bad["observations"]:
    bad["observations"][0]["knowledge_state"]="known_by_everyone"
    assert validate_public_artifact(bad,"ebe_runtime")["status"]=="fail"

corr=deepcopy(world["regional_corridors"])
if corr["corridors"]:
    c=deepcopy(corr); c["corridors"].append(deepcopy(c["corridors"][0]))
    assert validate_public_artifact(c,"regional_corridors")["status"]=="fail"
    c=deepcopy(corr); c["corridors"][0]["path"][0]=[True,0]
    assert validate_public_artifact(c,"regional_corridors")["status"]=="fail"

# Strict JSON parser rejects ambiguous/nonstandard JSON.
for text in ('{"a":1,"a":2}', '{"x":NaN}', '{"x":Infinity}', '{bad json'):
    try:
        strict_json_loads(text)
        raise AssertionError("strict JSON parser accepted invalid/ambiguous JSON")
    except StrictJSONError:
        pass
assert strict_json_loads('{"a":1,"b":[true,null]}')=={"a":1,"b":[True,None]}

# ---------------------------------------------------------------------------
# Migration matrix.
# ---------------------------------------------------------------------------
for version in ("0.9.0","0.9.1","0.9.2","0.9.3"):
    legacy=deepcopy(world)
    legacy["generator"]["version"]=version
    legacy["schema_versions"].pop("contract_manifest",None)
    legacy["schema_versions"]["runtime_api"]=version
    if isinstance(legacy.get("gameplay"),dict): legacy["gameplay"]["generator_version"]=version
    fp=world_fingerprint(legacy)
    migrated,report=migrate_public_artifact(legacy,"world")
    assert report["mode"]=="metadata_only"
    assert report["semantic_identity_preserved"] is True
    assert world_fingerprint(migrated)==fp
    assert migrated["generator"]["version"]==version
    assert migrated["schema_versions"]["runtime_api"]=="1.0.0"
    assert migrated["schema_versions"]["contract_manifest"]=="1.0.0"

migrated,report=migrate_public_artifact(world,"world")
assert report["mode"]=="already_compatible"
assert migrated==world

for version in ("1.0.1","1.1.0","9.9.9"):
    future=deepcopy(world)
    future["generator"]["version"]=version
    future["schema_versions"].pop("contract_manifest",None)
    try:
        migrate_public_artifact(future,"world")
        raise AssertionError("unknown/future generator was metadata-migrated")
    except MigrationError:
        pass

legacy080=deepcopy(world)
legacy080["generator"]["version"]="0.8.0"
legacy080["schema_versions"].pop("regional_corridors",None)
legacy080["schema_versions"].pop("contract_manifest",None)
legacy080.pop("regional_corridors",None)
try:
    migrate_public_artifact(legacy080,"world")
    raise AssertionError("pre-corridor world was fabricated")
except MigrationRequiresRegeneration:
    pass

wrong_schema=deepcopy(world); wrong_schema["schema_versions"]["world"]="9.0"
try:
    migrate_public_artifact(wrong_schema,"world")
    raise AssertionError("unknown world payload schema was migrated")
except MigrationError:
    pass

# ---------------------------------------------------------------------------
# Transactional public bundle writes + verifier hostile-path checks.
# ---------------------------------------------------------------------------
def dir_hashes(folder: Path):
    return {
        str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(folder.rglob("*")) if p.is_file()
    }

with tempfile.TemporaryDirectory() as td:
    target=Path(td)/"bundle"
    write_public_bundle(target,world=world,state=state,events=state["event_log"],ebe_runtime=ebe)
    assert verify_public_bundle(target)["status"]=="pass"
    baseline=dir_hashes(target)

    # Relationship failure is rejected before destination mutation.
    mismatched=deepcopy(state); mismatched["source_world"]["fingerprint"]="0"*64
    try:
        write_public_bundle(target,world=world,state=mismatched,events=mismatched["event_log"],ebe_runtime=ebe)
        raise AssertionError("relationship-invalid bundle was written")
    except ValueError:
        pass
    assert dir_hashes(target)==baseline

    # Serialization/staging failure cannot damage the previously committed bundle.
    original_write=contract_bundle.atomic_write_json
    count={"n":0}
    def flaky_write(path,value):
        count["n"]+=1
        if count["n"]==2:
            raise OSError("simulated staged write failure")
        return original_write(path,value)
    contract_bundle.atomic_write_json=flaky_write
    try:
        try:
            write_public_bundle(target,world=world,state=state,events=state["event_log"],ebe_runtime=ebe)
            raise AssertionError("simulated staged write failure did not propagate")
        except OSError:
            pass
    finally:
        contract_bundle.atomic_write_json=original_write
    assert dir_hashes(target)==baseline

    # Commit failure before swap also leaves prior destination intact.
    original_commit=contract_bundle.commit_staged_directory
    def fail_commit(stage_path,target_path):
        raise OSError("simulated commit failure")
    contract_bundle.commit_staged_directory=fail_commit
    try:
        try:
            write_public_bundle(target,world=world,state=state,events=state["event_log"],ebe_runtime=ebe)
            raise AssertionError("simulated commit failure did not propagate")
        except OSError:
            pass
    finally:
        contract_bundle.commit_staged_directory=original_commit
    assert dir_hashes(target)==baseline

    # A legacy-readable pre-corridor world cannot be frozen as a current bundle.
    legacy=deepcopy(world); legacy.pop("regional_corridors",None); legacy["schema_versions"].pop("regional_corridors",None); legacy["schema_versions"].pop("contract_manifest",None); legacy["generator"]["version"]="0.8.0"
    other=Path(td)/"legacy_bundle"
    try:
        write_public_bundle(other,world=legacy)
        raise AssertionError("legacy world was frozen as current bundle")
    except ValueError:
        pass
    assert not other.exists()

    # Manifest traversal/noncanonical filenames are rejected.
    manifest_path=target/"pixelgen_contract_manifest.json"
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    saved=deepcopy(manifest)
    manifest["artifacts"][0]["path"]="../world.json"
    manifest_path.write_text(json.dumps(manifest),encoding="utf-8")
    assert verify_public_bundle(target)["status"]=="fail"
    manifest_path.write_text(json.dumps(saved,indent=2,sort_keys=True),encoding="utf-8")
    assert verify_public_bundle(target)["status"]=="pass"

    # Symlink artifacts are rejected even when bytes/hash point to a legitimate file.
    if hasattr(os,"symlink"):
        outside=Path(td)/"outside-world.json"
        outside.write_bytes((target/"world.json").read_bytes())
        world_path=target/"world.json"
        world_path.unlink()
        try:
            os.symlink(outside,world_path)
        except OSError:
            shutil.copy2(outside,world_path)  # environment without symlink permission
        else:
            assert verify_public_bundle(target)["status"]=="fail"
        if world_path.is_symlink(): world_path.unlink()
        shutil.copy2(outside,world_path)
        assert verify_public_bundle(target)["status"]=="pass"

# Atomic single-file failure preserves old contents and cleans temporary file.
with tempfile.TemporaryDirectory() as td:
    path=Path(td)/"state.json"; path.write_bytes(b"old")
    original_replace=atomic_io.os.replace
    def fail_replace(src,dst): raise OSError("simulated replace failure")
    atomic_io.os.replace=fail_replace
    try:
        try:
            atomic_write_bytes(path,b"new")
            raise AssertionError("atomic write failure did not propagate")
        except OSError:
            pass
    finally:
        atomic_io.os.replace=original_replace
    assert path.read_bytes()==b"old"
    assert [p for p in Path(td).iterdir() if p.name.endswith('.tmp')]==[]

# Directory commit rollback after target->backup succeeded but stage->target failed.
with tempfile.TemporaryDirectory() as td:
    td=Path(td); target=td/"target"; stage=td/"stage"
    target.mkdir(); stage.mkdir(); (target/"marker").write_text("old"); (stage/"marker").write_text("new")
    original_replace=atomic_io.os.replace; calls={"n":0}
    def fail_second(src,dst):
        calls["n"]+=1
        if calls["n"]==2: raise OSError("simulated swap failure")
        return original_replace(src,dst)
    atomic_io.os.replace=fail_second
    try:
        try:
            commit_staged_directory(stage,target)
            raise AssertionError("directory swap failure did not propagate")
        except OSError:
            pass
    finally:
        atomic_io.os.replace=original_replace
    assert target.is_dir() and (target/"marker").read_text()=="old"

# ---------------------------------------------------------------------------
# Public API freeze + renderer independence.
# ---------------------------------------------------------------------------
expected_api={
    "RUNTIME_API_VERSION","CONTRACT_FREEZE_VERSION","load_runtime_profile",
    "generate_semantic_world","runtime_snapshot","initialize_state","apply_event",
    "replay_events","ebe_runtime_bundle","contract","validate_public_artifact",
    "migrate_public_artifact","write_public_bundle","verify_public_bundle","capabilities",
    "export_lua","state_summary","world_fingerprint",
}
assert set(runtime_api.__all__)==expected_api

probe=r'''
import sys, importlib.abc
for k in list(sys.modules):
    if k=="PIL" or k.startswith("PIL."): del sys.modules[k]
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname=="PIL" or fullname.startswith("PIL."): raise ImportError("PIL blocked")
        return None
sys.meta_path.insert(0,Block())
sys.path.insert(0,%r)
from pixelgen.runtime_api import capabilities, contract
assert capabilities()["version"]=="1.0.0"
assert contract()["contract_version"]=="1.0.0"
import runtime_cli
print("renderer-free-093")
''' % str(ROOT)
p=subprocess.run([sys.executable,"-c",probe],capture_output=True,text=True,timeout=30)
assert p.returncode==0,p.stderr
assert p.stdout.strip()=="renderer-free-093"

# Current JSON Schemas compile when jsonschema is available.
try:
    import jsonschema
except ImportError:
    jsonschema=None
if jsonschema is not None:
    for path in sorted((ROOT/"schemas").glob("*.schema.json")):
        jsonschema.Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))

print("PixelGen v1.0.0 stable hostile-input / atomic-I/O / migration-matrix tests passed")
