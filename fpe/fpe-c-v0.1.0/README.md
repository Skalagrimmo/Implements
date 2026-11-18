# FPE C 0.1.0 — Native runtime iteration

This folder contains an independent, dependency-free C11 implementation of the first native FPE runtime slice. It does **not** replace or edit the stable JavaScript FPE 1.0 package.

FPE in this repository is the deterministic **manifestation/view runtime** for PixelGen objective state. PixelGen remains authoritative for the world; FPE owns its local hierarchy/view state, generated manifestation geometry, bounded update scheduling, semantic-intent envelopes and runtime checkpoints. FPE never writes objective state back to PixelGen.

## Included in C 0.1.0

- Typed, read-only projection input with schema, source identity/clock, sector layout, per-cluster state/projection metrics, four buds per cluster and summary validation.
- Deep-copy ownership at runtime creation and revision handoff.
- World → cluster → bud → geometry view normalization and toggles.
- Deterministic sector centers and manifestation geometry:
  - straight buds: 8 vertices / 12 edges;
  - curved buds: 14 Fibonacci-sphere vertices and up to 42 deterministic nearest-neighbour edges;
  - stable FNV-1a-derived per-node values, phases, glyph choices and edge weights.
- Bounded host-tick scheduler, overdue-first / ID-stable ordering, coalesced due work, detail-sensitive periods and repeated-tick no-op behavior.
- Revision handoff: foreign-world, stale-revision and same-revision conflict rejection; identical duplicate revisions are no-ops.
- Semantic action-request envelopes bound to world identity, revision and source tick. Requests are intents only; they are never executed or written back.
- In-memory typed checkpoint/restore for projection, view, scheduler entries and runtime clock.
- The stable 11 error names and C cleanup functions for allocated outputs.

## Build and test

Requires a C11 compiler and CMake 3.16 or newer. There are no third-party runtime dependencies.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

The test suite covers projection validation, ownership isolation, hierarchy transitions, straight and curved geometry determinism, scheduler budget/rates/replay, revision handoff, request validation and checkpoint restore. It also creates a 100×100 projection (10,000 clusters / 40,000 buds) and exercises plan generation plus bounded scheduling.

The same test executable has been run with AddressSanitizer and UndefinedBehaviorSanitizer, and as a Release build with `-Werror` on GCC 14.2.

## Contract mapping

The public functions in `include/fpe/fpe.h` are C equivalents of the FPE 1.0 responsibilities:

| Stable FPE responsibility | C API |
|---|---|
| create | `fpe_runtime_create` |
| accept / revision handoff | `fpe_runtime_accept` |
| setView | `fpe_runtime_set_view` |
| toggleCluster | `fpe_runtime_toggle_cluster` |
| toggleBud | `fpe_runtime_toggle_bud` |
| step | `fpe_runtime_step` |
| request | `fpe_runtime_request` |
| serialize / restore | `fpe_runtime_checkpoint` / `fpe_runtime_restore` |
| getProjection | `fpe_runtime_projection` |
| getView | `fpe_runtime_get_view` |
| getPlan | `fpe_runtime_get_plan` |

The C version keeps the FPE 1.0 error code names: `INVALID_OPTIONS`, `INVALID_PROJECTION`, `FOREIGN_WORLD`, `STALE_REVISION`, `REVISION_CONFLICT`, `INVALID_VIEW`, `UNKNOWN_ID`, `PARENT_COLLAPSED`, `INVALID_TICK`, `INVALID_REQUEST` and `INVALID_SNAPSHOT`.

## Deliberate 0.1 limits — not yet 1.0 wire-compatible

This iteration is a typed C ABI, not a drop-in JSON runtime:

1. It does not parse PixelGen JSON projections or emit the stable JSON snapshot/request schemas. C callers construct `FPEProjection` structures.
2. Fingerprint fields are checked for the expected 64-character lowercase-hex form, but C 0.1 does **not** recompute the Python-compatible canonical SHA-256 projection fingerprint. Structural validation is not cryptographic verification.
3. Checkpoints are deep-owned in-memory C objects. They are not yet portable files and do not yet restore the JavaScript 0.11/0.12/1.0 historical checkpoint formats.
4. IDs and seed keys are bounded to 127 bytes and expected to use the canonical ASCII identifiers. The JSON action payload is limited to 64 KiB and depth 32.
5. The deterministic hash currently follows the stable FPE FNV-1a 32-bit key derivation for ASCII keys. Full non-ASCII JavaScript UTF-16 key parity is not claimed.
6. Geometry is returned as renderer-neutral points/edges. This library does not own a GPU renderer, lighting, particles, rigid-body physics, fracture simulation or destruction effects.
7. Runtime instances are not internally synchronized; callers must serialize access to a given runtime.

These are explicit porting boundaries, not silent substitutions. The next compatibility milestone is a strict JSON bridge/canonicalizer plus SHA-256 parity and a versioned portable checkpoint format. Only after those tests pass should the C implementation be described as a full FPE 1.0-compatible runtime.

## Ownership notes

- Projection input is borrowed only during `create` / `accept`; the runtime deep-copies it.
- `fpe_runtime_projection()` returns a borrowed read-only pointer valid until `accept` or runtime destruction.
- View, plan, update-batch, action-request and checkpoint outputs own allocated memory. Initialize output structs to zero before first use and release them with their matching `*_destroy` function before reuse.
- `fpe_runtime_accept()` prepares the new projection, normalized view, plan preflight and scheduler before replacing current runtime state.
