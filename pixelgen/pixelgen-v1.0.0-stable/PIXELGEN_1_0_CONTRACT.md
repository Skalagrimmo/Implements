# PixelGen 1.0 Stable Contract

## Responsibility

```text
seed + profile + dimensions
        ↓
static semantic world
        ↓
dynamic world state
        ↓
ordered runtime events
        ↓
mutations + derived events + local observations
```

PixelGen is the authority for objective world state. It does not own NPC memory, beliefs, rumor propagation or subjective knowledge.

## Stable payload schemas

The 1.0 package does not renumber mature payload formats merely to match the package version. World remains `0.7`, dynamic state/events/EBE runtime remain `0.8.0`, regional corridors remain `0.9.0`, while the stable runtime/manifest contract is `1.0.0`.

## Semantic identity

Generator and schema labels are metadata. `world_fingerprint()` identifies semantic generated content and must remain unchanged by metadata-only migration.

## Replay

For a fixed static world and the same ordered accepted event log, replay must reconstruct the exact dynamic state and state fingerprint.

## Strict public input

Public JSON rejects duplicate keys, non-finite numeric constants, invalid UTF-8, malformed IDs, boolean-as-integer confusion, invalid hashes, unsafe manifest paths and symlink artifacts. Validators fail closed and return structured failures rather than crashing on arbitrary JSON-compatible values.

## Transactional bundles

A public bundle is committed only after every artifact and every cross-artifact relationship has passed validation and the staged tree has self-verified. Failed staging or commit preserves the previous committed bundle.

## Migration

0.9.0–0.9.3 worlds with the required feature schemas may receive 1.0 runtime/contract metadata without changing generator provenance or semantic identity. Missing semantic systems require regeneration. Unknown future generators are rejected until a compatibility rule exists.

## Downstream boundary

The EBE runtime handoff exports semantic entities, derived events and local observations. Observation availability never means an NPC automatically knows the fact. FPE or other renderers may project the world but do not become an independent source of objective truth unless an explicit semantic action returns to PixelGen.
