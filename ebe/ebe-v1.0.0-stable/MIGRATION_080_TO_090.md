# Migration — EBE 0.8.0 → 0.9.0

No cognition or information semantics are intentionally changed by this migration.

Runtime snapshots from 0.8.0 are accepted and migrated in memory:

```text
version          0.8.0 → 0.9.0
contract_version absent → 0.9.0
```

Existing payload data is preserved. Missing containers introduced by later releases are initialized empty when required.

Important behavioral hardening:

```text
Snapshot.read_lua()
```

no longer executes the file with `dofile()`.

New writes should prefer:

```lua
EBE.Snapshot.write_runtime_json_atomic(path,rt:snapshot())
```

For a v0.8 semantic PixelGen action request, the state machine remains:

```text
pending → exported → applied/rejected
```

but v0.9 now enforces that a PixelGen request cannot be marked `applied` before export and cannot be resolved by mismatched authority feedback.
