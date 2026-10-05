# Changelog

## 1.0.0

- promote the hardened 0.12 freeze candidate to the stable 1.0 contract with no public behavior/schema widening
- preserve the frozen 10-method / 11-error API and read-only PixelGen authority boundary
- accept valid 0.11, 0.12 and 1.0 runtime checkpoints under the unchanged 0.11 snapshot schema
- add a checked-in 0.12 migration fixture and 64 frozen 0.12→1.0 semantic parity traces
- add 10-process determinism, 500 current round-trip, 500 historical migration and 500 hostile-snapshot promotion torture gates
- re-run the exact PixelGen 1.0 cross-engine, persistence, corruption and 10k-cluster stress suites on promoted code

## 0.12.0

- freeze the 10-method / 11-error public API candidate; no new public operations
- recompute and verify PixelGen→FPE projection SHA-256 in JavaScript
- add Python-compatible projection canonicalization and 256-case Python↔JS parity tests
- harden canonical projection/version/layout/summary validation in JS and Python
- reject accessors, symbols, hidden state, sparse/extended arrays and other non-JSON boundary data
- reject impossible persisted scheduler/runtime clock and queue states
- restore valid 0.11 snapshots and migrate serialization to runtime version 0.12.0
- deep-freeze accepted internal projections and cache validation only for proven immutable ownership
- add corruption fuzz, extended persistence stress and 10k-cluster/40k-bud large-world stress

## 0.11.0

- add detached `runtime.serialize()` and top-level `FPE.restore(snapshot)`
- add versioned `fpe.runtime_snapshot/0.11.0` contract
- preserve exact scheduler queue/service state across JSON checkpoint/restore
- preserve distinct monotonic runtime clock and post-handoff scheduler clock
- validate snapshot projection, canonical view, scheduler identity/state and request source-context
- add `INVALID_SNAPSHOT` and persistence ownership/isolation guards
- add scheduler persistence regression, exact round-trip tests and 4500-operation persistence fuzz

## 0.10.0

- add detached `request(action, targetId, payload)` semantic-intent envelopes
- bind requests to accepted PixelGen world identity, revision and source tick
- preserve authority boundary: FPE never executes semantic actions or writes state back
- add strict JSON/plain-object/cycle/depth validation and `INVALID_REQUEST`
- add request isolation, target typing, malformed input and post-handoff binding tests

## 0.9.0

- unified FPE runtime API and documented stable error codes
- detached public data, projection/view/scheduler ownership, monotonic tick guard across revisions
- demo integration through runtime and browser-global dependency tests
- public surface/replay/isolation tests and one-command local release gate

## 0.8.0

- validated revision handoff preserving view expansion and selection
- reject stale/foreign/conflicting revisions; identical duplicate is a no-op
- stronger renderer field checks and robust Python malformed-data diagnostics
- detached accepted projections; geometry preflight before data replacement
- tests for 18 invalid handoffs, revision replay, and nested Python inputs

## 0.7.0

- deterministic host-tick scheduler with per-cluster activity/detail periods
- bounded update descriptors, overdue-first ordering, coalesced catch-up
- visual-pulse integration and scheduler counters in demo
- replay, overload, rate, isolation and invalid-tick tests
- retain v0.6 bridge/schema and source fingerprints unchanged

## 0.6.0

- add explicit `world → cluster → bud → geometry` hierarchy contract
- begin at cluster-proxy detail and materialize bud geometry on demand
- normalize transient view state and reject orphan bud expansion
- make cluster collapse remove all descendant detail state
- add deterministic view-state fingerprints
- preserve projection bytes/fingerprint across all viewer operations
- update interactive and single-file demos with double-click expansion
- add hierarchy regression tests while retaining full-geometry compatibility

## 0.5.0

- replace arbitrary GRID authority with `PixelGen sector → local FPE cluster`
- exactly four deterministic buds per sector
- stable read-only bridge schema and projection fingerprint
- exact PixelGen world/state source identity validation
- preserve biome/subbiome/territory/front/corridor semantic tags
- map dynamic territory/front state into FPE cohesion/breakup/agitation/collapse/update-rate fields
- deterministic browser geometry; no `Math.random()`
- canonical PixelGen 1.0 seed 7301 / 6×5 fixture
- regression, JS-core, and cross-engine fuzz coverage
