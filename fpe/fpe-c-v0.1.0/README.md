# FPE C — native runtime and JSON bridge iteration

This folder contains an independent, dependency-free C11 implementation of the first native FPE runtime slice. It does **not** replace or edit the stable JavaScript FPE 1.0 package.

FPE in this repository is the deterministic **manifestation/view runtime** for PixelGen objective state. PixelGen remains authoritative for the world; FPE owns its local hierarchy/view state, generated manifestation geometry, bounded update scheduling, semantic-intent envelopes and runtime checkpoints. FPE never writes objective state back to PixelGen.

## C 0.1.0 typed runtime

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

## JSON projection bridge — C 0.2 development

The next compatibility slice now has a bounded JSON entry point, separate from the original typed C API:

- `fpe_json_canonical_fingerprint()` parses an object, sorts object keys recursively, preserves array order and emits canonical UTF-8 JSON before hashing it with the internal SHA-256 implementation. The root `projection_fingerprint` member is excluded from the hash.
- `fpe_projection_from_json()` verifies the supplied fingerprint **before** mapping stable FPE 0.6 projection fields into the typed C representation.
- `fpe_projection_json_destroy()` releases the projection returned by the JSON parser. `fpe_runtime_create()` then deep-copies it, so the parsed projection may be destroyed immediately after runtime creation.
- The JSON parser rejects duplicate object keys, invalid UTF-8, malformed escapes, unpaired surrogate escapes, embedded NUL escapes, non-finite numbers, trailing data, and inputs beyond its explicit resource limits (8 MiB, depth 64, 300,000 parsed nodes, 100,000 clusters).

The C tests include SHA-256/canonicalization checks, both stable FPE 1.0 golden projection fixtures (30 clusters / 120 buds each), and a generated 256-case Python→C fingerprint corpus. The corpus follows the stable FPE reference generator exactly: numeric boundary values, deterministic mutations, Ukrainian + emoji metadata and Python-produced fingerprints. The C parser verifies each complete document before conversion, creates runtimes from the golden fixtures, then verifies ownership after releasing the temporary parsed projections.

This is **projection JSON compatibility work**, not full FPE 1.0 wire compatibility. Portable JSON checkpoint restore, historical 0.11/0.12 snapshot migration, complete JSON action-request envelopes, and the full 256-case Python↔JavaScript numeric/UTF-8 differential corpus remain open gates.

## Build and test

Requires a C11 compiler and CMake 3.16 or newer. There are no third-party runtime dependencies.

```sh
cmake -S . -B build/fpe-c -DCMAKE_BUILD_TYPE=Debug
cmake --build build/fpe-c --parallel
python tests/generate_fingerprint_vectors.py build/fpe-c/fpe-json-vectors.jsonl
ctest --test-dir build/fpe-c --output-on-failure
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

## Deliberate compatibility limits — not yet full FPE 1.0 wire-compatible

This iteration combines the typed C 0.1 runtime with an in-progress projection JSON bridge. It is still not a drop-in FPE 1.0 runtime:

1. Portable JSON snapshots are not implemented. Checkpoints remain deep-owned in-memory C objects and do not restore JavaScript runtime snapshot versions 0.11.0 / 0.12.0 / 1.0.0.
2. Full JSON action-request envelope serialization is not implemented; `fpe_runtime_request()` still returns the typed C request structure.
3. The 256-case Python→C fingerprint test is now included in CI; the JavaScript↔C runtime trace and portable checkpoint round-trip remain open gates.
4. The parser rejects escaped U+0000 because the current public C structures use NUL-terminated strings. JSON input is bounded to 8 MiB, depth 64, 300,000 parsed nodes and 100,000 clusters.
5. IDs and seed keys are bounded to 127 bytes and the deterministic runtime key hash uses canonical ASCII identifiers. Full non-ASCII JavaScript UTF-16 key parity is not claimed.
6. Parsed source metadata outside the typed runtime fields is integrity-checked as part of the full projection fingerprint, but is not retained in the reduced C `FPEProjection` representation.
7. Geometry is renderer-neutral points/edges. This library does not own a GPU renderer, lighting, particles, rigid-body physics, fracture simulation or destruction effects.
8. Runtime instances are not internally synchronized; callers must serialize access to a given runtime.

The next gates are the stable 256-case numeric/UTF-8 differential corpus, a broader malformed-input suite, portable/versioned JSON checkpoints and JS↔C trace fixtures. Only after those gates pass should the C implementation be described as fully FPE 1.0 wire-compatible.

## Ownership notes

- Projection input is borrowed only during `create` / `accept`; the runtime deep-copies it.
- `fpe_runtime_projection()` returns a borrowed read-only pointer valid until `accept` or runtime destruction.
- View, plan, update-batch, action-request and checkpoint outputs own allocated memory. Initialize output structs to zero before first use and release them with their matching `*_destroy` function before reuse.
- `fpe_runtime_accept()` prepares the new projection, normalized view, plan preflight and scheduler before replacing current runtime state.
