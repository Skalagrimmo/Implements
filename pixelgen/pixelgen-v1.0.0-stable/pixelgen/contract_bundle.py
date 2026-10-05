"""Transactional deterministic contract bundles for PixelGen public artifacts."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

from .fingerprint import world_fingerprint
from .world_state import state_fingerprint
from .serialization import to_plain
from .schema_contracts import (
    CONTRACT_FREEZE_VERSION,
    CONTRACT_STATUS,
    contract_fingerprint,
    artifact_payload_version,
    validate_artifact,
)
from .atomic_io import atomic_write_json, make_staging_directory, commit_staged_directory
from .json_io import read_json
from .audit import audit_world
from .world_state_integrity import validate_world_state

CONTRACT_MANIFEST_NAME = "pixelgen_contract_manifest.json"

STANDARD_FILES = {
    "world": "world.json",
    "world_state": "state.json",
    "runtime_events": "events.json",
    "ebe_runtime": "ebe-runtime.json",
}


def _canonical_sha(value: Any) -> str:
    value = to_plain(value)
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _artifact_entry(role: str, artifact_type: str, path: Path, value: Any) -> dict[str, Any]:
    validation = validate_artifact(value, artifact_type)
    if validation["status"] != "pass":
        raise ValueError(f"{role} failed contract validation: " + "; ".join(validation["errors"][:20]))
    entry = {
        "role": role,
        "artifact_type": artifact_type,
        "path": path.name,
        "payload_version": artifact_payload_version(value, artifact_type),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "canonical_sha256": _canonical_sha(value),
    }
    if artifact_type == "world":
        entry["semantic_fingerprint"] = world_fingerprint(value)
    elif artifact_type == "world_state":
        entry["state_fingerprint"] = state_fingerprint(value)
        entry["source_world_fingerprint"] = (value.get("source_world") or {}).get("fingerprint")
        entry["revision"] = (value.get("clock") or {}).get("revision")
    elif artifact_type == "runtime_events":
        entry["event_count"] = len(value)
    elif artifact_type == "ebe_runtime":
        entry["state_revision"] = (value.get("source") or {}).get("state_revision")
        entry["event_count"] = len(value.get("events", []))
        entry["observation_count"] = len(value.get("observations", []))
    return entry


def _relationships(world: Any, state: Any = None, events: Any = None, ebe: Any = None) -> dict[str, Any]:
    world_fp = world_fingerprint(world)
    result = {
        "world_semantic_fingerprint": world_fp,
        "state_matches_world": None,
        "events_match_state_log": None,
        "ebe_matches_state_revision": None,
        "ebe_matches_world_identity": None,
    }
    if state is not None:
        result["state_matches_world"] = (state.get("source_world") or {}).get("fingerprint") == world_fp
    if state is not None and events is not None:
        result["events_match_state_log"] = events == state.get("event_log", [])
    if state is not None and ebe is not None:
        result["ebe_matches_state_revision"] = (
            (ebe.get("source") or {}).get("state_revision") == (state.get("clock") or {}).get("revision")
        )
    if ebe is not None:
        src_world = (ebe.get("source") or {}).get("world") or {}
        result["ebe_matches_world_identity"] = (
            src_world.get("world_seed") == world.get("seed")
            and list(src_world.get("dimensions") or []) == [world.get("cols"), world.get("rows")]
        )
    return result


def _assert_relationships(rel: dict[str, Any]) -> None:
    failed = [k for k, v in rel.items() if k != "world_semantic_fingerprint" and v is False]
    if failed:
        raise ValueError("contract bundle relationship failure: " + ", ".join(failed))


def _assert_freezable_world(world: dict[str, Any]) -> None:
    validation = validate_artifact(world, "world")
    if validation["status"] != "pass":
        raise ValueError("world failed contract validation: " + "; ".join(validation["errors"][:20]))
    details = validation.get("details") or {}
    if not details.get("current_features"):
        raise ValueError(
            "contract bundle requires a current-feature world; legacy readable worlds must be regenerated or migrated without inventing missing semantics"
        )
    if details.get("compatibility") not in ("current", "metadata_migratable"):
        raise ValueError("world generator provenance is not approved for a current contract bundle")
    try:
        audit = audit_world(world)
    except Exception as exc:
        raise ValueError(f"world semantic audit crashed on malformed data: {type(exc).__name__}: {exc}") from exc
    if audit.get("status") == "fail":
        raise ValueError("world failed semantic audit: " + "; ".join(audit.get("errors", [])[:20]))


def _build_bundle_in_stage(
    stage: Path,
    *,
    world: dict[str, Any],
    state: dict[str, Any] | None,
    events: list[dict[str, Any]] | None,
    ebe_runtime: dict[str, Any] | None,
) -> tuple[Path, dict[str, Any]]:
    _assert_freezable_world(world)

    artifacts: list[dict[str, Any]] = []
    values: dict[str, Any] = {"world": to_plain(deepcopy(world))}
    if state is not None:
        values["world_state"] = to_plain(deepcopy(state))
    if events is not None:
        values["runtime_events"] = to_plain(deepcopy(events))
    if ebe_runtime is not None:
        values["ebe_runtime"] = to_plain(deepcopy(ebe_runtime))

    # Validate relationships before writing anything even to the staging tree.
    rel = _relationships(
        values["world"],
        state=values.get("world_state"),
        events=values.get("runtime_events"),
        ebe=values.get("ebe_runtime"),
    )
    _assert_relationships(rel)

    for artifact_type, value in values.items():
        validation = validate_artifact(value, artifact_type)
        if validation["status"] != "pass":
            raise ValueError(f"{artifact_type} failed contract validation: " + "; ".join(validation["errors"][:20]))
        filename = STANDARD_FILES[artifact_type]
        path = stage / filename
        atomic_write_json(path, value)
        artifacts.append(_artifact_entry(artifact_type, artifact_type, path, value))

    manifest = {
        "manifest_version": CONTRACT_FREEZE_VERSION,
        "contract_status": CONTRACT_STATUS,
        "contract_fingerprint": contract_fingerprint(),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "relationships": rel,
    }
    manifest_path = stage / CONTRACT_MANIFEST_NAME
    atomic_write_json(manifest_path, manifest)

    # Self-validate the completed staging tree before committing it.
    verification = verify_contract_bundle(stage)
    if verification["status"] != "pass":
        raise ValueError("staged contract bundle failed self-verification: " + "; ".join(verification["errors"][:20]))
    return manifest_path, manifest


def write_contract_bundle(
    folder: str | Path,
    *,
    world: dict[str, Any],
    state: dict[str, Any] | None = None,
    events: list[dict[str, Any]] | None = None,
    ebe_runtime: dict[str, Any] | None = None,
) -> tuple[Path, dict[str, Any]]:
    folder = Path(folder)
    stage = make_staging_directory(folder)
    try:
        _, manifest = _build_bundle_in_stage(
            stage,
            world=world,
            state=state,
            events=events,
            ebe_runtime=ebe_runtime,
        )
        commit_staged_directory(stage, folder)
        stage = None
        return folder / CONTRACT_MANIFEST_NAME, manifest
    finally:
        if stage is not None and Path(stage).exists():
            shutil.rmtree(stage, ignore_errors=True)


def freeze_existing_bundle(
    folder: str | Path,
    *,
    world_path: str | Path,
    state_path: str | Path | None = None,
    events_path: str | Path | None = None,
    ebe_runtime_path: str | Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    def load(path: str | Path | None):
        if path is None:
            return None
        return read_json(path)

    # Load every source before the destination is touched.  This also makes
    # in-place freeze operations safe with respect to read/write ordering.
    world = load(world_path)
    state = load(state_path)
    events = load(events_path)
    ebe = load(ebe_runtime_path)
    return write_contract_bundle(folder, world=world, state=state, events=events, ebe_runtime=ebe)


def verify_contract_bundle(folder: str | Path) -> dict[str, Any]:
    folder = Path(folder)
    manifest_path = folder / CONTRACT_MANIFEST_NAME
    errors: list[str] = []
    if not manifest_path.is_file() or manifest_path.is_symlink():
        return {"status": "fail", "errors": [f"manifest not found or unsafe: {manifest_path}"], "checked": 0}

    try:
        manifest = read_json(manifest_path)
    except Exception as exc:
        return {"status": "fail", "errors": [f"manifest parse failed: {exc}"], "checked": 0}

    manifest_validation = validate_artifact(manifest, "contract_manifest")
    errors.extend(manifest_validation["errors"])

    values: dict[str, Any] = {}
    checked = 0
    seen_types: set[str] = set()
    seen_paths: set[str] = set()
    entries = manifest.get("artifacts", []) if isinstance(manifest.get("artifacts"), list) else []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        artifact_type = entry.get("artifact_type")
        rel = entry.get("path")
        if artifact_type in seen_types:
            errors.append(f"duplicate artifact type in manifest: {artifact_type}")
            continue
        if isinstance(artifact_type, str):
            seen_types.add(artifact_type)
        if rel in seen_paths:
            errors.append(f"duplicate artifact path in manifest: {rel}")
            continue
        if isinstance(rel, str):
            seen_paths.add(rel)
        if artifact_type not in STANDARD_FILES:
            errors.append(f"unsupported manifest artifact type: {artifact_type}")
            continue
        expected_rel = STANDARD_FILES[artifact_type]
        if rel != expected_rel:
            errors.append(f"noncanonical artifact path for {artifact_type}: {rel}; expected {expected_rel}")
            continue
        if not isinstance(rel, str) or Path(rel).is_absolute() or ".." in Path(rel).parts:
            errors.append(f"unsafe artifact path: {rel}")
            continue
        path = folder / rel
        if path.is_symlink():
            errors.append(f"symlink artifact is not allowed: {rel}")
            continue
        if not path.is_file():
            errors.append(f"missing artifact: {rel}")
            continue
        if path.stat().st_size != entry.get("bytes"):
            errors.append(f"size mismatch: {rel}")
            continue
        if sha256_file(path) != entry.get("sha256"):
            errors.append(f"sha256 mismatch: {rel}")
            continue
        try:
            value = read_json(path)
        except Exception as exc:
            errors.append(f"JSON parse failed for {rel}: {exc}")
            continue
        try:
            canonical = _canonical_sha(value)
        except Exception as exc:
            errors.append(f"canonicalization failed for {rel}: {exc}")
            continue
        if canonical != entry.get("canonical_sha256"):
            errors.append(f"canonical hash mismatch: {rel}")
            continue
        validation = validate_artifact(value, artifact_type)
        if validation["status"] != "pass":
            errors.extend(f"{rel}: {e}" for e in validation["errors"])
            continue
        if artifact_type == "world":
            details = validation.get("details") or {}
            if not details.get("current_features"):
                errors.append("bundle world is legacy-readable but not current-feature compatible")
                continue
            try:
                audit = audit_world(value)
            except Exception as exc:
                errors.append(f"world semantic audit crashed: {type(exc).__name__}: {exc}")
                continue
            if audit.get("status") == "fail":
                errors.extend(f"world semantic audit: {e}" for e in audit.get("errors", [])[:20])
                continue
            if world_fingerprint(value) != entry.get("semantic_fingerprint"):
                errors.append(f"semantic fingerprint mismatch: {rel}")
                continue
        if artifact_type == "world_state" and state_fingerprint(value) != entry.get("state_fingerprint"):
            errors.append(f"state fingerprint mismatch: {rel}")
            continue
        values[artifact_type] = value
        checked += 1

    world = values.get("world")
    if world is None:
        errors.append("contract bundle must contain world artifact")
    else:
        state_value = values.get("world_state")
        if state_value is not None:
            try:
                state_errors = validate_world_state(world, state_value)
            except Exception as exc:
                errors.append(f"world-state semantic validation crashed: {type(exc).__name__}: {exc}")
            else:
                errors.extend(f"world-state semantic validation: {e}" for e in state_errors[:20])
        rel = _relationships(
            world,
            state=state_value,
            events=values.get("runtime_events"),
            ebe=values.get("ebe_runtime"),
        )
        try:
            _assert_relationships(rel)
        except Exception as exc:
            errors.append(str(exc))
        if rel != manifest.get("relationships"):
            errors.append("manifest relationship summary does not match artifact contents")

    return {
        "status": "pass" if not errors else "fail",
        "checked": checked,
        "expected": len(entries),
        "errors": errors,
        "contract_version": manifest.get("manifest_version"),
        "contract_fingerprint": manifest.get("contract_fingerprint"),
        "world_fingerprint": (manifest.get("relationships") or {}).get("world_semantic_fingerprint") if isinstance(manifest.get("relationships"), dict) else None,
    }


__all__ = [
    "CONTRACT_MANIFEST_NAME",
    "STANDARD_FILES",
    "sha256_file",
    "write_contract_bundle",
    "freeze_existing_bundle",
    "verify_contract_bundle",
]
