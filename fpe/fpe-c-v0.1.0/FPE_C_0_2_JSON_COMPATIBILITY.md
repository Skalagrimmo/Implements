# FPE C 0.2 — JSON compatibility contract

Status: partially implemented. The bounded parser, canonical projection fingerprint verifier, typed projection mapping, two stable golden projections and the generated 256-case Python→C numeric/UTF-8 differential corpus are implemented. The 256-case corpus and all three base test suites have passed on Ubuntu and Windows CI; macOS is still queued. Portable snapshot compatibility remains open.

This document pins the compatibility target to the repository's stable FPE 1.0 package at `fpe-v1.0.0-stable/`. It does not change the C 0.1 ABI or claim JSON interoperability yet.

## 1. Authoritative references

The implementation must follow these existing files, not a newly invented serialization format:

- `fpe-v1.0.0-stable/fpe/bridge.py`
- `fpe-v1.0.0-stable/web/fpe_core.js`
- `fpe-v1.0.0-stable/web/fpe.js`
- `fpe-v1.0.0-stable/FPE_1_0_CONTRACT.md`
- `fpe-v1.0.0-stable/PERSISTENCE_011.md`
- `fpe-v1.0.0-stable/tests/test_cross_runtime_fingerprint.py`
- `fpe-v1.0.0-stable/tests/test_persistence.js`
- canonical projections in `fpe-v1.0.0-stable/data/projections/`
- historical snapshots in `fpe-v1.0.0-stable/data/snapshots/`

## 2. Projection fingerprint contract

The stable Python bridge computes a projection fingerprint by deep-copying the projection, removing only the root `projection_fingerprint` member, serializing the remaining JSON value canonically, then computing SHA-256 over its UTF-8 bytes. The digest is 64 lowercase hexadecimal characters.

Canonical JSON rules:

1. Object keys are sorted recursively; arrays retain their original order.
2. There is no insignificant whitespace.
3. Strings are UTF-8, not ASCII-escaped. JSON quotes, backslashes and control characters are escaped as JSON requires.
4. Null, booleans and integer-valued fields retain JSON semantics.
5. Non-finite numbers are rejected.
6. The following projection numeric paths are Python-float paths and must retain a floating representation even when mathematically integral:
   - `layout.sector_spacing`
   - `layout.local_bud_offset`
   - `clusters[*].state.{control_strength,stability,alert,front_tension,front_activity}`
   - `clusters[*].projection.{cohesion,breakup_resistance,agitation,collapse_bias,damage_proxy,update_rate}`
7. Python-float formatting must match the stable JavaScript compatibility implementation in `web/fpe_core.js`: negative zero is `-0.0`; integral floats include `.0`; small magnitudes use normalized exponent notation with a signed, at-least-two-digit exponent. Other numeric paths use ordinary JSON number formatting.

The existing cross-runtime regression test is a required reference: it creates 256 projections, exercises edge values (including 0, 1e-6, 1e-5, 1e-4, 0.123456, 0.999999 and 1.0), injects Ukrainian and emoji UTF-8 text, and checks Python-produced fingerprints against the JavaScript runtime.

Important distinction: the source bridge's `_canonical_bytes` uses Python `json.dumps(sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)`. The browser runtime deliberately applies `pythonFloatNumber` only to the frozen float paths before hashing. C must reproduce the resulting bytes/digest, not merely produce valid JSON or a self-consistent C hash.

## 3. JSON bridge scope for C 0.2

The current C 0.2 development slice adds a bounded, dependency-free JSON boundary around the existing typed C runtime:

- parse UTF-8 JSON objects/arrays/scalars with explicit input-size and nesting limits;
- reject malformed JSON, invalid UTF-8, duplicate object keys, non-finite numbers, invalid escapes, trailing data and resource-limit violations;
- canonicalize the accepted projection using the exact rules above;
- calculate and verify the projection SHA-256 before the typed projection is accepted;
- convert the frozen `fpe.pixelgen_hierarchy/0.6.0` projection fields into the existing C 0.1 typed structures;
- retain all required source identity, schema, authority, hierarchy, layout, cluster, state, metric, bud and summary invariants;
- keep the PixelGen authority boundary unchanged: parsing and verification are read-only and never write back to PixelGen.

The JSON layer must not silently normalize a malformed projection into a valid one. Any future optional-field policy must be explicit and tested against the stable JavaScript validator.

The C 0.1 typed API remains available. JSON entry points are additive and must not alter its ownership or runtime semantics.

## 4. SHA-256 implementation requirements

- A small internal SHA-256 implementation is acceptable; no OpenSSL or platform crypto dependency is required.
- Hash input is the canonical UTF-8 byte stream, excluding the root fingerprint field.
- Digest output is lowercase hexadecimal.
- Test known SHA-256 vectors independently of FPE, then test canonical projection vectors.
- Do not treat a syntactically valid 64-character fingerprint as verified. C 0.2 must recompute and compare it.

## 5. Differential test plan

The implementation is not considered fully compatible until all of these are covered. Current coverage includes the canonical initial/after-state 30-cluster fixtures, SHA digest checks, duplicate-key rejection, trailing-data rejection, embedded-NUL escape rejection, runtime ownership after projection decoding and all 256 generated Python→C numeric/UTF-8 fingerprint vectors:

1. Standard SHA-256 vectors (empty input, `abc`, and a multi-block input).
2. The stable canonical initial and after-state projections.
3. The same 256 deterministic edge/UTF-8 projections produced by the stable Python test.
4. Mutations of each float path, integer path, nested object key order, array order, UTF-8 string content and root fingerprint.
5. Invalid JSON and malformed projection rejection, including duplicate keys, over-depth input, over-size input, invalid UTF-8, escaped Unicode and non-finite numeric tokens.
6. A JS↔C differential trace fixture after the JSON projection bridge is stable.

Golden values must be generated from the stable Python/JavaScript sources and committed as fixtures. Never generate expected values from the C implementation under test.

## 6. Explicitly out of scope for this first compatibility slice

- Portable runtime snapshot serialization and restoration.
- Migration of snapshot runtime versions 0.11.0 and 0.12.0 to 1.0.0.
- Full action-request JSON envelope serialization.
- Any renderer, GPU, rigid-body physics, particle, fracture or destruction system.
- Any writeback or mutation of PixelGen world state.

Those remain separate milestones after projection parsing and fingerprint parity are demonstrated.

## 7. Acceptance gate

C 0.2 is a projection-compatibility milestone only when the C implementation independently verifies the stable golden fingerprints and passes the same deterministic cross-runtime edge corpus. The two checked-in canonical projection fixtures and 256-case Python→C corpus pass on Ubuntu and Windows CI; macOS verification is still pending. Broader malformed-input coverage, portable/versioned JSON checkpoints, the stable historical snapshot migrations and JS↔C runtime trace fixtures remain incomplete, so this branch must not yet be described as fully FPE 1.0 wire-compatible.
