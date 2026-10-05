# FPE v0.11.0 validation report

## Result

All local release gates pass for the packaged 0.11 persistence candidate.

## Regression gates retained

- Python bridge regression: PASS — canonical 30 clusters / 120 buds and state-change projection behavior.
- Python malformed projection validation: PASS.
- Hierarchical web core: PASS — deterministic cluster/bud/geometry planning and standalone demo syntax.
- Scheduler: PASS — replay, rates, budget, fairness, monotonic ticks, view-detail transitions, copy isolation; now also exact scheduler-state restore.
- Revision handoff: PASS — revision 0→3, duplicates, stale/conflict/foreign rejection, 18 malformed cases, 1000 replays.
- Hierarchy fuzz: PASS — 2000 operations.
- Action requests: PASS — target typing, JSON validation, isolation, no writeback and post-handoff revision binding.

## New persistence gates

`tests/test_persistence.js` validates:

- JSON stringify/parse round-trip;
- byte-order-stable reserialization of a restored runtime produced by the same implementation;
- exact view, projection, request-context and scheduler continuation;
- repeated-tick behavior after restore;
- preservation of separate host/scheduler clocks immediately after revision handoff;
- continued `accept()`, `request()` and tick guards after restore;
- output/input ownership isolation;
- 17 structured corruption mutations plus cyclic and non-plain-object rejection.

`tests/fuzz_persistence.js` validates 30 deterministic seeds with:

- 4500 mixed runtime operations;
- 460 actual `serialize → JSON → restore` cycles;
- 790 full-state equality checks between uninterrupted and periodically restored runtimes.

## Public contract gate

The current runtime surface is 10 methods and 11 stable error codes. Browser-global loading also executes `serialize()` + `FPE.restore()` without WebGL.

## Scope not covered by this local run

- real-browser GPU/render-performance qualification for this exact build;
- real-device/mobile performance qualification;
- cross-engine 48-world PixelGen fuzz, because a PixelGen 1.0 source tree is not bundled in this package;
- cryptographic authentication of runtime snapshots;
- migration of hypothetical future snapshot schema versions.

These are not failures of the local gate; they remain release-readiness items toward 1.0.
