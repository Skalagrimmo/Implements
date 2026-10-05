# FPE v0.12.0 RC test report

## 0.11 pre-audit baseline

The supplied `fpe-v0.11.0-persistence-rc.zip` passed its existing bridge, malformed validation, hierarchy, scheduler, handoff, public API, action-request, persistence and persistence-fuzz gates before 0.12 changes were applied.

The stricter audit then found and fixed four substantive RC issues: missing JS recomputation of projection SHA-256, acceptance of impossible persisted scheduler states, ambiguous non-JSON JavaScript boundary objects, and the performance regression caused by applying full integrity hashing indiscriminately on hot internal paths.

## Normal release suite

`python tools/run_tests.py` covers:

- canonical PixelGen 1.0 bridge regression;
- Python malformed projection validation;
- 256 Python↔JavaScript fingerprint parity projections;
- hierarchical web-core regression;
- scheduler replay/rate/budget/fairness/tick/persistence gates;
- revision handoff including 18 malformed cases and 1000 replay checks;
- 2000-operation hierarchy fuzz;
- public API isolation/replay/browser-global loading harness;
- semantic action request validation and ownership;
- persistence JSON round-trip and malformed checkpoints;
- 4500 mixed persistence operations, 460 serialize/JSON/restore cycles and 790 full-state checks across 30 seeds;
- RC hardening vectors for SHA-256, fingerprint tampering, semantic rehash attacks, impossible scheduler state, maximum tick boundary, hostile JavaScript objects and stable serialization.

The monolithic wrapper can exceed the execution harness wall-clock limit, so the heavy tail was also run as independent gates. `fuzz_persistence.js` and `test_rc_hardening.js` each completed with PASS independently.

## Extended RC stress

- corruption fuzz: **2400/2400** targeted invalid snapshots rejected; **250/250** valid JSON round-trips preserved — PASS;
- extended persistence: **5,000** mixed operations, **698** restore cycles, **923** full-state comparisons, **25** deterministic seeds — PASS;
- large world: **10,000 clusters / 40,000 buds**, **11,335,413-byte** snapshot, **200** scheduler ticks, serialize→JSON→restore exact equality — PASS.

## Exact PixelGen 1.0 cross-engine gate

The stable PixelGen archive used for the external gate matched SHA-256:

`f24008bd95682164b89d0d49ed346d5ba1a0728ce17a54abdd5fa518167304ee`

`tests/fuzz_bridge.py` was then run against the actual unpacked PixelGen 1.0 source tree in six independent chunks: starts 0, 16, 32, 48, 64 and 80, 16 worlds each. **96/96 worlds PASS**, and each world was projected both before and after an authoritative PixelGen event.

## Browser limitation of this execution environment

A true browser-page smoke could not be completed because the installed Chromium is administratively blocked from navigating to `file:`, localhost and `data:` URLs. This is recorded as **NOT EXECUTED**, not PASS or FAIL. Node/browser-global dependency tests remain green, but visual browser interaction must still be performed outside this restricted environment.

## Compatibility

A real 0.11.0 reference snapshot is checked into `data/snapshots/v0.11.0-reference.json`. FPE 0.12 restores it under `fpe.runtime_snapshot/0.11.0` and the next serialization migrates `runtime_version` to 0.12.0.

## Result before clean-archive replay

No automated release-blocking correctness defect remains from this audit. The remaining 1.0 gates are external/manual browser rendering, intended low-spec/mobile runtime exercise, and the final 1.0 compatibility-support decision. Clean-archive replay is recorded separately in `FINAL_PACKAGE_VERIFICATION_012.md`.
