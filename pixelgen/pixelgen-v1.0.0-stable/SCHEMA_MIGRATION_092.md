# PixelGen v0.9.2 — Schema and Migration Freeze Contract

## 1. Purpose

v0.9.2 is the candidate data contract that PixelGen intends to carry into 1.0
unless release testing discovers a concrete defect.

The release does not rename every older subsystem to `0.9.2`.

A mature schema keeps its own version:

```text
world                    0.7
territory_graph          0.7.5
dynamic_world_state      0.8.0
EBE dynamic bridge       0.8.0
regional_corridors       0.9.0
runtime API              0.9.2
contract manifest        0.9.2
```

## 2. Compatibility principle

```text
package version != payload schema version
```

A payload schema changes only when the payload contract changes.

This avoids meaningless migrations such as:

```text
state 0.8.0
→ state 0.9.0
→ state 0.9.1
→ state 0.9.2
```

when the state shape itself never changed.

## 3. Unknown fields

Policy:

```text
preserve and ignore unknown fields
unless they violate a semantic invariant
```

This makes additive future evolution possible.

## 4. Missing fields

```text
missing optional field
→ allowed

missing required field
→ reject
```

PixelGen does not infer required semantic data merely to make an artifact pass.

## 5. World migration

### v0.9.0 / v0.9.1

If the artifact already contains:

```text
world schema        0.7
territory graph     0.7.5
regional corridors  0.9.0
```

migration is metadata-only.

The migration may add/update:

```text
schema_versions.runtime_api       = 0.9.2
schema_versions.render_api        = 0.9.1
schema_versions.contract_manifest = 0.9.2
```

It does **not** change generated content.

The migration is rejected if:

```text
world_fingerprint(before)
!=
world_fingerprint(after)
```

The original `generator.version` is preserved as provenance.

### v0.8 and older pre-corridor worlds

PixelGen refuses to synthesize missing regional corridors during migration.

```text
missing corridor subsystem
→ regeneration required
```

This is intentional.  Migration is not generation.

## 6. Dynamic state migration

Current state schema:

```text
0.8.0
```

No shape migration is required.

A compatible state is copied exactly.

## 7. Runtime event migration

Current event-log contract:

```text
0.8.0
```

The event log is an array and therefore does not carry a top-level schema
field.  Its version is owned by the contract registry.

A compatible event log is copied exactly.

## 8. EBE runtime migration

Current dynamic bridge contract:

```text
0.8.0
```

Required epistemic invariants include:

```text
global_knowledge = forbidden
observation_semantics = local evidence only
```

A bundle that claims global knowledge is rejected rather than migrated.

## 9. Contract bundle manifest

Manifest:

```text
pixelgen_contract_manifest.json
```

Version:

```text
0.9.2
```

Each artifact entry records:

```text
role
artifact_type
path
payload_version
bytes
sha256
canonical_sha256
```

Semantic artifacts add relevant identities such as:

```text
world semantic fingerprint
state fingerprint
state revision
event count
EBE state revision
```

## 10. Cross-artifact invariants

A valid full bundle requires:

```text
state.source_world.fingerprint
== world_fingerprint(world)
```

and:

```text
events
== state.event_log
```

and:

```text
EBE.source.state_revision
== state.clock.revision
```

and EBE world identity must match:

```text
world seed
world dimensions
```

## 11. Contract fingerprint

The contract registry is canonicalized and hashed.

v0.9.2:

```text
ce2324e2c472162f39dbe0ee460e847dca97edfd0634215ea671da2b4f3b7bb9
```

A different contract definition must not reuse this fingerprint.

## 12. Semantic fingerprint rule

PixelGen's semantic world fingerprint intentionally ignores:

```text
generator label
schema version labels
gameplay generator label
```

Therefore metadata migration can be proven not to modify generated world
semantics.

## 13. 1.0 freeze criterion

The v0.9.2 contract is suitable for 1.0 if release testing confirms:

```text
no required field must be renamed
no required semantic invariant is missing
migration rules are sufficient
EBE/FPE consumers can depend on the exported identities
bundle verification catches corruption/mismatch
```

New gameplay mechanics are not a prerequisite for PixelGen 1.0.
