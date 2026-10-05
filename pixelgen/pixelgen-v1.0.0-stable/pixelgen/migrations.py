"""Explicit, conservative artifact migrations for the stable 1.0 contract."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .fingerprint import world_fingerprint
from .schema_contracts import (
    CONTRACT_FREEZE_VERSION,
    CONTRACT_REGISTRY,
    detect_artifact_type,
    validate_artifact,
)


class MigrationError(ValueError):
    pass


class MigrationRequiresRegeneration(MigrationError):
    pass


def _migrate_world(world: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(world, dict):
        raise MigrationError("world artifact must be an object")

    before = deepcopy(world)
    before_fp = world_fingerprint(before)
    schema = before.get("schema_versions") or {}
    generator_version = str((before.get("generator") or {}).get("version", ""))

    if schema.get("world") != "0.7":
        raise MigrationError("unsupported world payload schema; expected 0.7")
    if schema.get("regional_corridors") != "0.9.0" or not isinstance(before.get("regional_corridors"), dict):
        raise MigrationRequiresRegeneration(
            "world predates the regional-corridor contract; regeneration is required rather than inventing corridor data"
        )
    if schema.get("territory_graph") != "0.7.5" or not isinstance(before.get("territory_graph"), dict):
        raise MigrationRequiresRegeneration(
            "world lacks the territory-graph contract required by the current runtime"
        )

    # A world already stamped with the current contract is a no-op migration,
    # regardless of package provenance (for example a 0.9.3 hardening build).
    if schema.get("contract_manifest") == CONTRACT_FREEZE_VERSION:
        validation = validate_artifact(before, "world")
        if validation["status"] != "pass":
            raise MigrationError("current-contract world failed validation: " + "; ".join(validation["errors"][:20]))
        return deepcopy(before), {
            "artifact_type": "world",
            "source_generator": generator_version,
            "target_contract": CONTRACT_FREEZE_VERSION,
            "mode": "already_compatible",
            "changes": [],
            "semantic_fingerprint_before": before_fp,
            "semantic_fingerprint_after": before_fp,
            "semantic_identity_preserved": True,
            "validation": validation,
        }

    allowed = set(CONTRACT_REGISTRY["artifacts"]["world"]["metadata_migration_from_generators"])
    if generator_version not in allowed:
        raise MigrationError(
            f"generator provenance {generator_version!r} is not approved for metadata migration; "
            "unknown/future generators require an explicit compatibility decision"
        )

    after = deepcopy(before)
    versions = after.setdefault("schema_versions", {})
    changes = []

    def set_meta(key: str, value: str) -> None:
        old = versions.get(key)
        if old != value:
            versions[key] = value
            changes.append({"path": f"schema_versions.{key}", "before": old, "after": value})

    set_meta("runtime_api", "1.0.0")
    set_meta("render_api", "0.9.1")
    set_meta("contract_manifest", CONTRACT_FREEZE_VERSION)

    after_fp = world_fingerprint(after)
    if before_fp != after_fp:
        raise MigrationError("metadata-only world migration changed semantic fingerprint")

    report = {
        "artifact_type": "world",
        "source_generator": generator_version,
        "target_contract": CONTRACT_FREEZE_VERSION,
        "mode": "metadata_only",
        "changes": changes,
        "semantic_fingerprint_before": before_fp,
        "semantic_fingerprint_after": after_fp,
        "semantic_identity_preserved": before_fp == after_fp,
    }
    return after, report


def _validate_noop(value: Any, artifact_type: str) -> tuple[Any, dict[str, Any]]:
    report = validate_artifact(value, artifact_type)
    if report["status"] != "pass":
        raise MigrationError("artifact is not compatible with the supported payload schema: " + "; ".join(report["errors"][:20]))
    return deepcopy(value), {
        "artifact_type": artifact_type,
        "target_contract": CONTRACT_FREEZE_VERSION,
        "mode": "already_compatible",
        "changes": [],
    }


def migrate_artifact(value: Any, artifact_type: str | None = None) -> tuple[Any, dict[str, Any]]:
    resolved = artifact_type or detect_artifact_type(value)
    if resolved is None:
        raise MigrationError("artifact type could not be detected; specify it explicitly")
    if resolved == "world":
        migrated, report = _migrate_world(value)
    elif resolved in ("world_state", "runtime_events", "ebe_runtime", "ebe_seed_bundle", "regional_corridors"):
        migrated, report = _validate_noop(value, resolved)
    else:
        raise MigrationError(f"unsupported migration artifact type: {resolved}")

    validation = validate_artifact(migrated, resolved)
    if validation["status"] != "pass":
        raise MigrationError("migrated artifact failed contract validation: " + "; ".join(validation["errors"][:20]))
    report["validation"] = validation
    return migrated, report


__all__ = [
    "MigrationError",
    "MigrationRequiresRegeneration",
    "migrate_artifact",
]
