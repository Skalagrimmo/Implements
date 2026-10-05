# FPE 0.12 RC hardening

## Findings from the stricter 0.11 audit

1. JavaScript validated the *format* of `projection_fingerprint` but did not recompute it. A range-valid mutation could therefore enter the JS runtime with a stale fingerprint.
2. Snapshot restore allowed scheduler/runtime clock combinations and queue entry combinations that could never be produced by an uninterrupted runtime.
3. Request/snapshot JS objects could contain accessors or hidden/non-JSON state whose value/shape was not guaranteed to survive `JSON.stringify()` unchanged.
4. Naively adding full SHA-256 checks to every core call caused a hot-path performance regression.
5. Python and JavaScript validators were not equally strict on several canonical projection invariants.

## Fixes

- synchronous browser-compatible SHA-256 plus Python-compatible canonical projection serialization;
- 256-case Python↔JS fingerprint parity gate including UTF-8 and small float edge cases;
- stale fingerprint rejection and semantic checks that remain effective even after a malicious rehash;
- strict projection/request/snapshot JSON-data boundaries;
- impossible scheduler state rejection;
- 0.11 snapshot migration fixture;
- recursively frozen internal projection ownership and validation caching only after a proven deep freeze;
- tighter Python projection validation parity;
- separate normal release and extended stress suites.

## Scheduler persistence invariants added

- scheduler clock is either equal to runtime clock or `-1` after scheduler reset/handoff;
- an entry with `last === null` has `next === 0`;
- an entry with a service history has `next > last`;
- a scheduler at `last_tick === -1` is in canonical fresh state (`last=null`, `next=0`, `detail=cluster_proxy` for all entries).

These rules reject corrupted checkpoints rather than converting them into a different but apparently valid execution history.
