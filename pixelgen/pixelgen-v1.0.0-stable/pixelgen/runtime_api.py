"""Renderer-free public runtime facade for PixelGen.

v1.0.0 is the stable renderer-free PixelGen runtime API.  It preserves the
pre-1.0 semantic generation contract while freezing versioned artifact
contracts, conservative migration, deterministic replay and transactional
contract-bundle manifests.
"""
from pathlib import Path

from .palette import load_profile
from .gameplay_world import generate_gameplay_world
from .gameplay_integrity import validate_gameplay_integrity
from .progression import simulate_progression
from .world_state import (
    initialize_world_state,
    apply_world_event,
    replay_world_events,
    state_summary,
)
from .world_state_integrity import validate_world_state
from .dynamic_ebe_bridge import build_dynamic_ebe_bundle
from .fingerprint import world_fingerprint
from .serialization import to_plain, write_lua_return
from .schema_contracts import (
    CONTRACT_FREEZE_VERSION,
    contract_fingerprint,
    public_contract,
    validate_artifact,
)
from .migrations import migrate_artifact
from .contract_bundle import write_contract_bundle, verify_contract_bundle

RUNTIME_API_VERSION = "1.0.0"


def default_profile_path():
    return Path(__file__).resolve().parents[1] / "profiles" / "techno_animist_gothic.json"


def load_runtime_profile(path=None):
    return load_profile(Path(path) if path else default_profile_path())


def generate_semantic_world(profile, seed=0, cols=4, rows=3, ability_count=4):
    """Generate and validate a gameplay world without importing a renderer."""
    world = generate_gameplay_world(profile, seed, cols, rows, ability_count)
    errors = validate_gameplay_integrity(world)
    if errors:
        raise RuntimeError("semantic world failed validation: " + "; ".join(errors[:20]))
    contract = validate_artifact(world, "world")
    if contract["status"] != "pass":
        raise RuntimeError("generated world failed public contract: " + "; ".join(contract["errors"][:20]))
    return world


def runtime_snapshot(world):
    return {
        "runtime_api_version": RUNTIME_API_VERSION,
        "contract_version": CONTRACT_FREEZE_VERSION,
        "contract_fingerprint": contract_fingerprint(),
        "world_fingerprint": world_fingerprint(world),
        "seed": world["seed"],
        "dimensions": [world["cols"], world["rows"]],
        "world": to_plain(world),
        "progression": to_plain(simulate_progression(world)),
    }


def initialize_state(world):
    state = initialize_world_state(world)
    errors = validate_world_state(world, state)
    if errors:
        raise RuntimeError("initial state failed validation: " + "; ".join(errors[:20]))
    return state


def apply_event(world, state, event):
    nxt = apply_world_event(world, state, event)
    errors = validate_world_state(world, nxt)
    if errors:
        raise RuntimeError("runtime event produced invalid state: " + "; ".join(errors[:20]))
    return nxt


def replay_events(world, events):
    state = replay_world_events(world, events)
    errors = validate_world_state(world, state)
    if errors:
        raise RuntimeError("replayed state failed validation: " + "; ".join(errors[:20]))
    return state


def ebe_runtime_bundle(world, state, since_revision=None):
    if since_revision is None:
        return build_dynamic_ebe_bundle(world, state)
    return build_dynamic_ebe_bundle(world, state, since_revision=since_revision)


def contract():
    return public_contract()


def validate_public_artifact(value, artifact_type=None):
    return validate_artifact(value, artifact_type)


def migrate_public_artifact(value, artifact_type=None):
    return migrate_artifact(value, artifact_type)


def write_public_bundle(folder, *, world, state=None, events=None, ebe_runtime=None):
    return write_contract_bundle(
        folder,
        world=world,
        state=state,
        events=events,
        ebe_runtime=ebe_runtime,
    )


def verify_public_bundle(folder):
    return verify_contract_bundle(folder)


def capabilities():
    return {
        "version": RUNTIME_API_VERSION,
        "renderer_required": False,
        "semantic_world": True,
        "dynamic_state": True,
        "deterministic_replay": True,
        "ebe_incremental_bundle": True,
        "regional_corridors": True,
        "schema_contracts": True,
        "contract_version": CONTRACT_FREEZE_VERSION,
        "contract_status": "stable",
        "contract_freeze_candidate": None,
        "artifact_migration": True,
        "contract_bundle_manifest": True,
        "transactional_public_writes": True,
        "hostile_json_safe_validation": True,
    }


def export_lua(value, path):
    write_lua_return(to_plain(value), str(path))


__all__ = [
    "RUNTIME_API_VERSION",
    "CONTRACT_FREEZE_VERSION",
    "load_runtime_profile",
    "generate_semantic_world",
    "runtime_snapshot",
    "initialize_state",
    "apply_event",
    "replay_events",
    "ebe_runtime_bundle",
    "contract",
    "validate_public_artifact",
    "migrate_public_artifact",
    "write_public_bundle",
    "verify_public_bundle",
    "capabilities",
    "export_lua",
    "state_summary",
    "world_fingerprint",
]
