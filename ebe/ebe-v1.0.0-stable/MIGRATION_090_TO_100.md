# EBE migration: 0.9.0 → 1.0.0

The promotion is intentionally metadata-only for valid 0.9 runtime snapshots.

```text
snapshot.version          0.9.0 → 1.0.0
snapshot.contract_version 0.9.0 → 1.0.0
semantic payload          unchanged
```

Use:

```lua
local loaded=EBE.Snapshot.read_runtime_json("save.json")
local restored=EBE.Runtime.restore(loaded)
```

`read_runtime_json()` performs migration and validation. Direct `Runtime.restore()` also migrates before restore.

The final promotion parity gate compared v0.9 and v1.0 canonical demos and a multi-layer semantic snapshot after stripping release metadata. All were identical. Unknown versions such as `1.0.1`, `1.1.0`, `2.0.0`, or `9.9.9` are not guessed compatible and are rejected until explicitly supported.
