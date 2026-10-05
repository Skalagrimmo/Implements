# FPE v1.0.0 — Stable

FPE 1.0 is the stable deterministic manifestation/view runtime for PixelGen objective state. The 1.0 release promotes the hardened 0.12 freeze candidate **without widening the public API or serialized schemas**.

PixelGen owns objective world state. FPE owns local hierarchy/render manifestation, transient view state, bounded scheduling, semantic intent envelopes and FPE runtime checkpoints. FPE never commits objective state back into PixelGen.

Open `fpe-v1.0.0-demo.html` for the visual demo. The demo loads Three.js from CDN; the FPE runtime modules themselves are dependency-free JavaScript.

## Stable API

Top level:

```js
FPE.version                  // "1.0.0"
FPE.create(projection, opts)
FPE.restore(snapshot)
FPE.describe()
FPE.FPEError
```

Runtime methods are frozen at exactly:

```text
accept
setView
toggleCluster
toggleBud
step
request
serialize
getProjection
getView
getPlan
```

There are 11 stable error codes. See `PUBLIC_API_100.md` and `FPE_1_0_CONTRACT.md`.

## Stable schemas

```text
projection             fpe.pixelgen_hierarchy/0.6.0
hierarchy/view         fpe.view_hierarchy/0.6.0
action request         fpe.action_request/0.10.0
runtime snapshot       fpe.runtime_snapshot/0.11.0
scheduler state        fpe.scheduler_state/0.11.0
```

Schema versions remain independent from the runtime release because the serialized shapes did not change during promotion.

## Checkpoint compatibility

FPE 1.0 restores valid runtime snapshots produced by 0.11.0, 0.12.0 and 1.0.0 under the frozen 0.11 snapshot schema. Restored historical checkpoints serialize forward as `runtime_version: 1.0.0`. Unknown historical/future versions remain rejected unless compatibility is explicitly added later.

## Integrity and determinism

JavaScript recomputes the PixelGen→FPE projection SHA-256 using the Python bridge canonicalization contract. Accepted projections are detached, validated and deep-frozen. JSON boundaries reject cycles, accessors, symbols, hidden state, sparse/extended arrays, non-plain objects and non-finite values where applicable.

0.12→1.0 promotion behavior is pinned by 64 frozen semantic trace hashes, and fresh-process determinism is checked across 10 independent Node processes.

## Semantic requests

`runtime.request(action, targetId, payload)` emits a detached `fpe.action_request/0.10.0` intent bound to the accepted PixelGen world identity/revision/tick. FPE does not execute the request and does not write state back into PixelGen.

## Release gates

Normal suite:

```bash
python tools/run_tests.py
```

Extended stable stress suite:

```bash
python tools/run_stress_tests.py
```

Important individual gates include:

```bash
node tests/test_v100_promotion.js
python tests/test_fresh_process_determinism.py
node tests/torture_v100.js all 0 100
node tests/fuzz_corruption.js
node tests/stress_persistence.js
node tests/stress_large_world.js
```

Cross-engine fuzz against an exact PixelGen 1.0 source tree:

```bash
python tests/fuzz_bridge.py --pixelgen-root /path/to/pixelgen-v1.0.0-stable --worlds 48
```

See `V100_TEST_REPORT.md`, `MIGRATION_012_TO_100.md` and `FPE_1_0_CONTRACT.md` for stable-promotion details.
