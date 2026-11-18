# Changelog — FPE C

## 0.2.0-dev — projection JSON compatibility slice

- add a bounded dependency-free JSON parser with UTF-8 and duplicate-key validation
- add canonical projection JSON serialization with recursively sorted object keys and stable float-path handling
- add internal SHA-256 verification of the supplied stable projection fingerprint before typed conversion
- add an additive JSON-to-typed-projection API with explicit ownership cleanup
- add stable FPE 1.0 initial and after-state projection fixtures (30 clusters / 120 buds each)
- add JSON, fingerprint, malformed-input and runtime-ownership regression checks
- keep portable snapshots, historical snapshot migrations, complete action-request JSON and the 256-case differential corpus as open compatibility gates

## 0.1.0 — first typed native iteration

- add dependency-free C11 static library and typed projection ABI
- add structural validation, deep-copy ownership and linear sector-uniqueness validation
- port deterministic world/cluster/bud/geometry hierarchy planning
- port view normalization, cluster/bud toggles and collapse semantics
- port bounded host-tick scheduler with overdue-first deterministic ordering
- port foreign/stale/conflicting revision handoff
- add detached semantic action-request envelopes with JSON-object payload validation
- add owned in-memory runtime checkpoint and restore
- add regression tests including a 10,000-cluster / 40,000-bud world
- document unimplemented stable snapshot and action-request wire compatibility
