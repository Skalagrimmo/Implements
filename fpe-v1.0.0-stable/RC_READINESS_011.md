# FPE 0.11 → 1.0 readiness

0.11 closes the largest remaining runtime-state gap: a live FPE session can now survive a JSON checkpoint/restore without losing scheduler determinism, view state or request source binding.

## Already covered

- deterministic PixelGen→FPE projection bridge;
- explicit authority boundary and no direct writeback;
- hierarchical LOD/view state;
- bounded deterministic scheduler;
- revision handoff with stale/conflict/foreign guards;
- stable public runtime/error surface candidate;
- semantic intent envelopes;
- exact versioned runtime persistence;
- regression + hierarchy fuzz + persistence fuzz.

## Recommended final 1.0 gates

1. Run cross-engine PixelGen fuzz again against the exact PixelGen 1.0 source tree used for release.
2. Manually open the exact 0.11/RC single-file demo in at least Chromium plus one second browser engine and exercise expand/collapse, revision load and long scheduler animation.
3. Exercise the exact build on the intended low-spec/mobile target and record frame/memory observations.
4. Decide and document the 1.0 snapshot compatibility rule: exact-version only, or a supported migration policy.
5. Freeze names/schema identifiers/error codes after any final corrections, then run the entire gate suite again from the clean release archive.

Snapshot authentication is optional unless snapshots will cross an untrusted transport boundary; structural validation alone is sufficient for ordinary local save/restore but is not a security signature.
