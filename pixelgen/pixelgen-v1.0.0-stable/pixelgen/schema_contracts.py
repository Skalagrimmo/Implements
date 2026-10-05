"""Stable versioned public artifact contracts for PixelGen 1.0.

PixelGen 1.0 intentionally keeps the mature payload schemas frozen.  The
package/runtime/contract labels become 1.0.0, while world/state/event/EBE and
regional-corridor payload schemas retain the versions that introduced their
semantics.  0.9.3 manifests remain readable for compatibility verification.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

CONTRACT_FREEZE_VERSION = "1.0.0"
CONTRACT_STATUS = "stable"

KNOWN_RUNTIME_EVENTS = {
    "front_escalation": "front",
    "front_deescalation": "front",
    "territory_strengthen": "territory",
    "territory_weaken": "territory",
    "territory_alert": "territory",
}

STANDARD_MANIFEST_FILES = {
    "world": "world.json",
    "world_state": "state.json",
    "runtime_events": "events.json",
    "ebe_runtime": "ebe-runtime.json",
}

CONTRACT_REGISTRY = {
    "contract_version": CONTRACT_FREEZE_VERSION,
    "status": CONTRACT_STATUS,
    "artifacts": {
        "world": {
            "payload_schema": "0.7",
            "current_generator": "1.0.0",
            "readable_payload_schemas": ["0.7"],
            "metadata_migration_from_generators": ["0.9.0", "0.9.1", "0.9.2", "0.9.3"],
            "required_features_for_current": {
                "territory_graph": "0.7.5",
                "dynamic_world_state": "0.8.0",
                "regional_corridors": "0.9.0",
            },
        },
        "world_state": {
            "payload_schema": "0.8.0",
            "readable_payload_schemas": ["0.8.0"],
        },
        "runtime_events": {
            "payload_schema": "0.8.0",
            "readable_payload_schemas": ["0.8.0"],
        },
        "ebe_runtime": {
            "payload_schema": "0.8.0",
            "readable_payload_schemas": ["0.8.0"],
        },
        "ebe_seed_bundle": {
            "payload_schema": "0.7.5",
            "readable_payload_schemas": ["0.7.5"],
        },
        "regional_corridors": {
            "payload_schema": "0.9.0",
            "readable_payload_schemas": ["0.9.0"],
        },
        "contract_manifest": {
            "payload_schema": "1.0.0",
            "readable_payload_schemas": ["0.9.3", "1.0.0"],
        },
    },
    "policies": {
        "unknown_fields": "preserve_and_ignore_unless_semantically_invalid",
        "missing_optional_fields": "allowed",
        "missing_required_fields": "reject",
        "semantic_fingerprint": "generator_and_schema_labels_are_not_semantic",
        "migration": "never_invent_missing_world_features_or_assume_unknown_future_generators",
        "state_authority": "world_state_overlay_never_rewrites_static_world",
        "ebe_knowledge": "local_evidence_only_global_knowledge_forbidden",
        "public_bundle": "current_feature_world_required_transactional_stage_then_commit",
        "hostile_json": "validators_must_reject_cleanly_never_raise_for_json_values",
    },
}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def contract_registry() -> dict[str, Any]:
    return deepcopy(CONTRACT_REGISTRY)


def contract_fingerprint() -> str:
    raw = json.dumps(
        CONTRACT_REGISTRY,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _err(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _is_int(value: Any, *, minimum: int | None = None) -> bool:
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    return minimum is None or value >= minimum


def _is_number(value: Any, *, minimum: float | None = None, maximum: float | None = None, exclusive_min: bool = False) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    value = float(value)
    if not math.isfinite(value):
        return False
    if minimum is not None:
        if exclusive_min and not value > minimum:
            return False
        if not exclusive_min and value < minimum:
            return False
    if maximum is not None and value > maximum:
        return False
    return True


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256_RE.fullmatch(value))


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _coord(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and _is_int(value[0], minimum=0)
        and _is_int(value[1], minimum=0)
    )


def _unique_string_ids(values: Any, errors: list[str], label: str) -> None:
    if not isinstance(values, list):
        return
    seen: set[str] = set()
    for i, item in enumerate(values):
        if not isinstance(item, dict):
            continue
        ident = item.get("id")
        if not _nonempty_string(ident):
            errors.append(f"{label}[{i}].id must be a nonempty string")
            continue
        if ident in seen:
            errors.append(f"{label} ids must be unique")
        seen.add(ident)


def detect_artifact_type(value: Any) -> str | None:
    if isinstance(value, list):
        if not value:
            return None
        if all(isinstance(x, dict) and "event_type" in x and "target_id" in x for x in value):
            return "runtime_events"
        return None

    if not isinstance(value, dict):
        return None

    if value.get("manifest_version") in set(CONTRACT_REGISTRY["artifacts"]["contract_manifest"]["readable_payload_schemas"]) and "artifacts" in value:
        return "contract_manifest"
    if "source_world" in value and "territories" in value and "fronts" in value and "event_log" in value:
        return "world_state"
    if "static_entities" in value and "dynamic_entities" in value and "observations" in value:
        return "ebe_runtime"
    if "entities" in value and "events" in value and value.get("version") == "0.7.5":
        return "ebe_seed_bundle"
    if "corridors" in value and "local_realization" in value and value.get("version") == "0.9.0":
        return "regional_corridors"
    if "sectors" in value and "schema_versions" in value and "generator" in value:
        return "world"
    return None


def artifact_payload_version(value: Any, artifact_type: str) -> str | None:
    if artifact_type == "world":
        return str((value.get("schema_versions") or {}).get("world")) if isinstance(value, dict) else None
    if artifact_type == "world_state":
        return str(value.get("version")) if isinstance(value, dict) else None
    if artifact_type == "runtime_events":
        return "0.8.0" if isinstance(value, list) else None
    if artifact_type in ("ebe_runtime", "ebe_seed_bundle", "regional_corridors"):
        return str(value.get("version")) if isinstance(value, dict) else None
    if artifact_type == "contract_manifest":
        return str(value.get("manifest_version")) if isinstance(value, dict) else None
    return None


def _validate_world(value: Any, errors: list[str], warnings: list[str]) -> dict[str, Any]:
    _err(errors, isinstance(value, dict), "world must be an object")
    if not isinstance(value, dict):
        return {}

    schema = value.get("schema_versions")
    _err(errors, isinstance(schema, dict), "world.schema_versions must be an object")
    schema = schema if isinstance(schema, dict) else {}
    _err(errors, schema.get("world") == "0.7", "world payload schema must be 0.7")

    generator = value.get("generator")
    _err(errors, isinstance(generator, dict), "world.generator must be an object")
    generator = generator if isinstance(generator, dict) else {}
    _err(errors, generator.get("name") == "PixelGen", "world.generator.name must be PixelGen")
    _err(errors, _nonempty_string(generator.get("version")), "world.generator.version must be a nonempty string")

    _err(errors, _is_int(value.get("seed")), "world.seed must be an integer (boolean is not allowed)")
    cols, rows = value.get("cols"), value.get("rows")
    _err(errors, _is_int(cols, minimum=1), "world.cols must be a positive integer")
    _err(errors, _is_int(rows, minimum=1), "world.rows must be a positive integer")

    sectors = value.get("sectors")
    _err(errors, isinstance(sectors, list), "world.sectors must be an array")
    if isinstance(sectors, list) and _is_int(cols, minimum=1) and _is_int(rows, minimum=1):
        _err(errors, len(sectors) == cols * rows, "world.sectors length must equal cols*rows")
        seen_coords: set[tuple[int, int]] = set()
        for i, sector in enumerate(sectors):
            if not isinstance(sector, dict):
                errors.append(f"world.sectors[{i}] must be an object")
                continue
            sx, sy = sector.get("sx"), sector.get("sy")
            if not _is_int(sx, minimum=0) or not _is_int(sy, minimum=0):
                errors.append(f"world.sectors[{i}] sx/sy must be nonnegative integers")
                continue
            if sx >= cols or sy >= rows:
                errors.append(f"world.sectors[{i}] coordinate outside world bounds")
                continue
            coord = (sx, sy)
            if coord in seen_coords:
                errors.append(f"world sector coordinates must be unique; duplicate {coord}")
            seen_coords.add(coord)
        if len(sectors) == cols * rows:
            _err(errors, len(seen_coords) == cols * rows, "world sectors must cover every coordinate exactly once")

    feature_versions = {
        "territory_graph": schema.get("territory_graph"),
        "dynamic_world_state": schema.get("dynamic_world_state"),
        "regional_corridors": schema.get("regional_corridors"),
    }
    current_requirements = CONTRACT_REGISTRY["artifacts"]["world"]["required_features_for_current"]
    current_features = all(feature_versions.get(k) == v for k, v in current_requirements.items())
    if current_features:
        _err(errors, isinstance(value.get("territory_graph"), dict), "current world requires territory_graph payload")
        _err(errors, isinstance(value.get("regional_corridors"), dict), "current world requires regional_corridors payload")
    else:
        warnings.append("world is readable but lacks one or more 1.0 current-feature schema markers")

    generator_version = str(generator.get("version", ""))
    contract_marker = schema.get("contract_manifest")
    migratable = set(CONTRACT_REGISTRY["artifacts"]["world"]["metadata_migration_from_generators"])
    compatibility = (
        "current" if contract_marker == CONTRACT_FREEZE_VERSION and current_features
        else "metadata_migratable" if generator_version in migratable and current_features
        else "legacy_readable"
    )
    return {
        "generator_version": generator_version,
        "feature_versions": feature_versions,
        "current_features": current_features,
        "compatibility": compatibility,
    }


def _validate_events(value: Any, errors: list[str], warnings: list[str]) -> dict[str, Any]:
    _err(errors, isinstance(value, list), "runtime event log must be an array")
    if not isinstance(value, list):
        return {}

    seen: set[str] = set()
    for i, event in enumerate(value):
        prefix = f"events[{i}]"
        if not isinstance(event, dict):
            errors.append(prefix + " must be an object")
            continue

        event_id = event.get("id")
        _err(errors, _nonempty_string(event_id), f"{prefix}.id must be a nonempty string")
        if _nonempty_string(event_id):
            if event_id in seen:
                errors.append("runtime event ids must be unique")
            seen.add(event_id)

        event_type = event.get("event_type")
        _err(errors, event_type in KNOWN_RUNTIME_EVENTS, f"{prefix}.event_type is unsupported")
        expected_target = KNOWN_RUNTIME_EVENTS.get(event_type)
        _err(errors, event.get("target_type") in ("front", "territory"), f"{prefix}.target_type must be front or territory")
        if expected_target is not None:
            _err(errors, event.get("target_type") == expected_target, f"{prefix}.target_type does not match event_type")
        _err(errors, _nonempty_string(event.get("target_id")), f"{prefix}.target_id must be a nonempty string")
        _err(errors, _is_number(event.get("amount"), minimum=0.0, maximum=1.0, exclusive_min=True), f"{prefix}.amount must be finite, >0 and <=1")
        _err(errors, _nonempty_string(event.get("source")), f"{prefix}.source must be a nonempty string")
        if event.get("sector") is not None:
            _err(errors, _coord(event.get("sector")), f"{prefix}.sector must be [nonnegative int, nonnegative int]")
        for optional_id in ("actor_id", "cause_id"):
            if event.get(optional_id) is not None:
                _err(errors, _nonempty_string(event.get(optional_id)), f"{prefix}.{optional_id} must be null or nonempty string")

    return {"compatibility": "current", "event_count": len(value)}


def _validate_state(value: Any, errors: list[str], warnings: list[str]) -> dict[str, Any]:
    _err(errors, isinstance(value, dict), "world state must be an object")
    if not isinstance(value, dict):
        return {}
    _err(errors, value.get("version") == "0.8.0", "world-state payload schema must be 0.8.0")

    source = value.get("source_world")
    _err(errors, isinstance(source, dict), "state.source_world must be an object")
    if isinstance(source, dict):
        _err(errors, _is_sha256(source.get("fingerprint")), "state source world fingerprint must be lowercase sha256 hex")
        _err(errors, _is_int(source.get("seed")), "state source seed must be an integer")
        dims = source.get("dimensions")
        _err(errors, isinstance(dims, list) and len(dims) == 2 and all(_is_int(x, minimum=1) for x in dims), "state source dimensions must be two positive integers")

    clock = value.get("clock")
    _err(errors, isinstance(clock, dict), "state.clock must be an object")
    rev = tick = None
    if isinstance(clock, dict):
        rev = clock.get("revision")
        tick = clock.get("tick")
        _err(errors, _is_int(rev, minimum=0), "state.clock.revision must be nonnegative integer")
        _err(errors, _is_int(tick, minimum=0), "state.clock.tick must be nonnegative integer")

    for key in ("territories", "fronts"):
        _err(errors, isinstance(value.get(key), dict), f"state.{key} must be an object")
    for key in ("event_log", "mutations", "derived_events", "observations"):
        _err(errors, isinstance(value.get(key), list), f"state.{key} must be an array")

    if isinstance(value.get("event_log"), list):
        _validate_events(value["event_log"], errors, warnings)
        if _is_int(rev, minimum=0):
            _err(errors, rev == len(value["event_log"]), "state revision must equal event_log length")
    if _is_int(rev, minimum=0):
        for key in ("mutations", "derived_events"):
            if isinstance(value.get(key), list):
                _err(errors, len(value[key]) == rev, f"state {key} length must equal revision")
        if _is_int(tick, minimum=0):
            _err(errors, tick >= rev, "state.clock.tick must be >= revision")

    for key in ("mutations", "derived_events", "observations"):
        _unique_string_ids(value.get(key), errors, f"state.{key}")

    territories = value.get("territories")
    if isinstance(territories, dict):
        for tid, item in territories.items():
            _err(errors, _nonempty_string(tid), "territory state keys must be nonempty strings")
            if not isinstance(item, dict):
                errors.append(f"state.territories[{tid!r}] must be an object")
                continue
            _err(errors, _is_number(item.get("control_strength"), minimum=0, maximum=1.75), f"{tid}.control_strength out of bounds")
            _err(errors, _is_number(item.get("stability"), minimum=0, maximum=1), f"{tid}.stability out of bounds")
            _err(errors, _is_number(item.get("alert"), minimum=0, maximum=1), f"{tid}.alert out of bounds")
            _err(errors, _is_int(item.get("revision"), minimum=0), f"{tid}.revision must be nonnegative integer")

    fronts = value.get("fronts")
    if isinstance(fronts, dict):
        for fid, item in fronts.items():
            _err(errors, _nonempty_string(fid), "front state keys must be nonempty strings")
            if not isinstance(item, dict):
                errors.append(f"state.fronts[{fid!r}] must be an object")
                continue
            _err(errors, _is_number(item.get("tension"), minimum=0, maximum=1), f"{fid}.tension out of bounds")
            _err(errors, _is_number(item.get("activity"), minimum=0, maximum=1), f"{fid}.activity out of bounds")
            _err(errors, _is_int(item.get("revision"), minimum=0), f"{fid}.revision must be nonnegative integer")

    observations = value.get("observations")
    if isinstance(observations, list):
        for i, obs in enumerate(observations):
            if not isinstance(obs, dict):
                errors.append(f"state.observations[{i}] must be an object")
                continue
            _err(errors, _coord(obs.get("sector")), f"state.observations[{i}].sector must be a coordinate")
            if obs.get("revision") is not None:
                _err(errors, _is_int(obs.get("revision"), minimum=1), f"state.observations[{i}].revision must be positive integer")
                if _is_int(rev, minimum=0) and _is_int(obs.get("revision"), minimum=1):
                    _err(errors, obs["revision"] <= rev, f"state.observations[{i}].revision exceeds state revision")

    return {"compatibility": "current"}


def _validate_ebe_runtime(value: Any, errors: list[str], warnings: list[str]) -> dict[str, Any]:
    _err(errors, isinstance(value, dict), "EBE runtime bundle must be an object")
    if not isinstance(value, dict):
        return {}
    _err(errors, value.get("version") == "0.8.0", "EBE runtime bundle version must be 0.8.0")

    source = value.get("source")
    _err(errors, isinstance(source, dict), "EBE runtime source must be an object")
    if isinstance(source, dict):
        _err(errors, _is_int(source.get("state_revision"), minimum=0), "EBE state_revision must be nonnegative integer")
        _err(errors, _is_int(source.get("since_revision"), minimum=0), "EBE since_revision must be nonnegative integer")
        if _is_int(source.get("state_revision"), minimum=0) and _is_int(source.get("since_revision"), minimum=0):
            _err(errors, source["since_revision"] <= source["state_revision"], "EBE since_revision cannot exceed state_revision")
        world = source.get("world")
        _err(errors, isinstance(world, dict), "EBE source.world must be an object")
        if isinstance(world, dict):
            _err(errors, _is_int(world.get("world_seed")), "EBE source world_seed must be integer")
            dims = world.get("dimensions")
            _err(errors, isinstance(dims, list) and len(dims) == 2 and all(_is_int(x, minimum=1) for x in dims), "EBE source dimensions must be two positive integers")

    contract = value.get("contract")
    _err(errors, isinstance(contract, dict), "EBE runtime contract must be an object")
    if isinstance(contract, dict):
        _err(errors, contract.get("global_knowledge") == "forbidden", "EBE runtime must forbid global knowledge")
        _err(errors, contract.get("observation_semantics") == "local evidence only", "EBE observations must be local evidence only")

    for key in ("static_entities", "dynamic_entities", "events", "observations"):
        _err(errors, isinstance(value.get(key), list), f"EBE runtime {key} must be an array")
        _unique_string_ids(value.get(key), errors, f"EBE.{key}")

    observations = value.get("observations")
    if isinstance(observations, list):
        for i, obs in enumerate(observations):
            if not isinstance(obs, dict):
                errors.append(f"EBE.observations[{i}] must be an object")
                continue
            _err(errors, _coord(obs.get("sector")), f"EBE.observations[{i}].sector must be a coordinate")
            _err(errors, obs.get("knowledge_state") == "not_yet_assigned_to_any_agent", f"EBE.observations[{i}] must not claim agent knowledge")
            _err(errors, obs.get("evidence") == "direct_local", f"EBE.observations[{i}] evidence must be direct_local")
            if obs.get("revision") is not None:
                _err(errors, _is_int(obs.get("revision"), minimum=1), f"EBE.observations[{i}].revision must be positive integer")

    return {"compatibility": "current"}


def _validate_ebe_seed(value: Any, errors: list[str], warnings: list[str]) -> dict[str, Any]:
    _err(errors, isinstance(value, dict), "EBE seed bundle must be an object")
    if not isinstance(value, dict):
        return {}
    _err(errors, value.get("version") == "0.7.5", "EBE seed bundle version must be 0.7.5")
    _err(errors, isinstance(value.get("entities"), list), "EBE seed entities must be an array")
    _err(errors, isinstance(value.get("events"), list), "EBE seed events must be an array")
    _unique_string_ids(value.get("entities"), errors, "EBE seed entities")
    _unique_string_ids(value.get("events"), errors, "EBE seed events")
    return {"compatibility": "current"}


def _validate_corridors(value: Any, errors: list[str], warnings: list[str]) -> dict[str, Any]:
    _err(errors, isinstance(value, dict), "regional corridors must be an object")
    if not isinstance(value, dict):
        return {}
    _err(errors, value.get("version") == "0.9.0", "regional corridor schema must be 0.9.0")
    corridors = value.get("corridors")
    local_realization = value.get("local_realization")
    _err(errors, isinstance(corridors, list), "regional corridors list is required")
    _err(errors, isinstance(local_realization, list), "regional corridor local_realization list is required")
    _err(errors, isinstance(value.get("policy"), dict), "regional corridor policy must be an object")
    _err(errors, isinstance(value.get("summary"), dict), "regional corridor summary must be an object")
    _unique_string_ids(corridors, errors, "regional_corridors.corridors")
    if isinstance(corridors, list):
        for i, corridor in enumerate(corridors):
            if not isinstance(corridor, dict):
                errors.append(f"regional_corridors.corridors[{i}] must be an object")
                continue
            path = corridor.get("path")
            _err(errors, isinstance(path, list) and bool(path), f"corridor[{i}].path must be a nonempty array")
            if isinstance(path, list):
                for j, c in enumerate(path):
                    _err(errors, _coord(c), f"corridor[{i}].path[{j}] must be a coordinate")
            if _is_int(corridor.get("sector_count"), minimum=1) and isinstance(path, list):
                _err(errors, corridor["sector_count"] == len(path), f"corridor[{i}].sector_count must match path length")
    return {"compatibility": "current"}


def _validate_manifest(value: Any, errors: list[str], warnings: list[str]) -> dict[str, Any]:
    _err(errors, isinstance(value, dict), "contract manifest must be an object")
    if not isinstance(value, dict):
        return {}
    manifest_version = value.get("manifest_version")
    readable = set(CONTRACT_REGISTRY["artifacts"]["contract_manifest"]["readable_payload_schemas"])
    _err(errors, manifest_version in readable, "contract manifest version mismatch")
    if manifest_version == CONTRACT_FREEZE_VERSION:
        _err(errors, value.get("contract_status") == CONTRACT_STATUS, "contract manifest status mismatch")
        _err(errors, value.get("contract_fingerprint") == contract_fingerprint(), "contract manifest fingerprint mismatch")
        compatibility = "current"
    elif manifest_version == "0.9.3":
        _err(errors, value.get("contract_status") == "release_candidate", "0.9.3 manifest status mismatch")
        _err(errors, value.get("contract_fingerprint") == "9cbdf1f51003342c86a145577f903caee1df48f8e263c5a1d309dcbc896dda7f", "0.9.3 manifest fingerprint mismatch")
        compatibility = "legacy_readable"
    else:
        compatibility = "unsupported"
    artifacts = value.get("artifacts")
    _err(errors, isinstance(artifacts, list), "contract manifest artifacts must be an array")
    _err(errors, isinstance(value.get("relationships"), dict), "contract manifest relationships must be an object")
    _err(errors, _is_int(value.get("artifact_count"), minimum=1), "contract manifest artifact_count must be a positive integer")
    if isinstance(artifacts, list):
        _err(errors, value.get("artifact_count") == len(artifacts), "contract manifest artifact_count mismatch")
        seen_types: set[str] = set()
        seen_paths: set[str] = set()
        for i, entry in enumerate(artifacts):
            if not isinstance(entry, dict):
                errors.append(f"manifest.artifacts[{i}] must be an object")
                continue
            typ = entry.get("artifact_type")
            rel = entry.get("path")
            _err(errors, typ in STANDARD_MANIFEST_FILES, f"manifest.artifacts[{i}].artifact_type unsupported")
            if typ in STANDARD_MANIFEST_FILES:
                _err(errors, rel == STANDARD_MANIFEST_FILES[typ], f"manifest artifact {typ} must use canonical path {STANDARD_MANIFEST_FILES[typ]}")
            _err(errors, isinstance(rel, str) and not Path(rel).is_absolute() and ".." not in Path(rel).parts, f"manifest.artifacts[{i}].path unsafe")
            _err(errors, _is_int(entry.get("bytes"), minimum=0), f"manifest.artifacts[{i}].bytes must be nonnegative integer")
            _err(errors, _is_sha256(entry.get("sha256")), f"manifest.artifacts[{i}].sha256 invalid")
            _err(errors, _is_sha256(entry.get("canonical_sha256")), f"manifest.artifacts[{i}].canonical_sha256 invalid")
            if isinstance(typ, str):
                if typ in seen_types:
                    errors.append(f"duplicate manifest artifact type: {typ}")
                seen_types.add(typ)
            if isinstance(rel, str):
                if rel in seen_paths:
                    errors.append(f"duplicate manifest artifact path: {rel}")
                seen_paths.add(rel)

    rels = value.get("relationships")
    if isinstance(rels, dict):
        _err(errors, _is_sha256(rels.get("world_semantic_fingerprint")), "manifest world semantic fingerprint invalid")
        for key in ("state_matches_world", "events_match_state_log", "ebe_matches_state_revision", "ebe_matches_world_identity"):
            _err(errors, rels.get(key) in (True, False, None), f"manifest relationship {key} must be boolean or null")
    return {"compatibility": compatibility}


_VALIDATORS = {
    "world": _validate_world,
    "world_state": _validate_state,
    "runtime_events": _validate_events,
    "ebe_runtime": _validate_ebe_runtime,
    "ebe_seed_bundle": _validate_ebe_seed,
    "regional_corridors": _validate_corridors,
    "contract_manifest": _validate_manifest,
}


def validate_artifact(value: Any, artifact_type: str | None = None) -> dict[str, Any]:
    """Validate arbitrary JSON-compatible data without throwing for malformed values."""
    try:
        detected = detect_artifact_type(value)
        resolved = artifact_type or detected
        errors: list[str] = []
        warnings: list[str] = []
        if resolved is None:
            return {
                "status": "fail",
                "artifact_type": None,
                "detected_type": detected,
                "payload_version": None,
                "errors": ["artifact type could not be detected; specify it explicitly"],
                "warnings": [],
                "contract_version": CONTRACT_FREEZE_VERSION,
                "contract_fingerprint": contract_fingerprint(),
            }
        if resolved not in _VALIDATORS:
            return {
                "status": "fail",
                "artifact_type": resolved,
                "detected_type": detected,
                "payload_version": None,
                "errors": [f"unsupported artifact type: {resolved}"],
                "warnings": [],
                "contract_version": CONTRACT_FREEZE_VERSION,
                "contract_fingerprint": contract_fingerprint(),
            }
        if detected is not None and artifact_type is not None and detected != artifact_type:
            errors.append(f"artifact type mismatch: requested {artifact_type}, detected {detected}")
        details = _VALIDATORS[resolved](value, errors, warnings)
        payload_version = artifact_payload_version(value, resolved)
        return {
            "status": "pass" if not errors else "fail",
            "artifact_type": resolved,
            "detected_type": detected,
            "payload_version": payload_version,
            "errors": errors,
            "warnings": warnings,
            "details": details,
            "contract_version": CONTRACT_FREEZE_VERSION,
            "contract_fingerprint": contract_fingerprint(),
        }
    except Exception as exc:
        # A public validator must never turn hostile JSON into a validator crash.
        return {
            "status": "fail",
            "artifact_type": artifact_type,
            "detected_type": None,
            "payload_version": None,
            "errors": [f"validator rejected malformed artifact safely: {type(exc).__name__}: {exc}"],
            "warnings": [],
            "contract_version": CONTRACT_FREEZE_VERSION,
            "contract_fingerprint": contract_fingerprint(),
        }


def public_contract() -> dict[str, Any]:
    data = contract_registry()
    data["contract_fingerprint"] = contract_fingerprint()
    return data


__all__ = [
    "CONTRACT_FREEZE_VERSION",
    "CONTRACT_STATUS",
    "CONTRACT_REGISTRY",
    "KNOWN_RUNTIME_EVENTS",
    "contract_registry",
    "contract_fingerprint",
    "public_contract",
    "detect_artifact_type",
    "artifact_payload_version",
    "validate_artifact",
]
