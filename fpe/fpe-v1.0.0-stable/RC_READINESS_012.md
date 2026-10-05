# FPE 0.12 → 1.0 readiness

0.12 closes the release-blocking issues found by the strict 0.11 audit without widening the public API.

## Automated coverage now present

- deterministic PixelGen→FPE bridge and Python malformed validation;
- Python↔JavaScript projection SHA-256 parity;
- hierarchical deterministic view/geometry fuzz;
- scheduler replay, fairness, limits and persisted-state restoration;
- revision handoff, stale/conflict/foreign guards and 1000 replay checks;
- stable 10-method/11-error public API checks in Node and browser-global loading harness;
- action-request JSON/integrity isolation;
- exact runtime persistence including split host/scheduler clocks;
- 0.11→0.12 snapshot migration fixture;
- targeted hostile-JS input tests;
- corruption fuzz and extended persistence stress;
- 10,000-cluster / 40,000-bud large-world checkpoint/restore stress;
- exact PixelGen 1.0 stable archive cross-engine fuzz: 96 worlds in six independent 16-world chunks, all PASS. The source archive SHA-256 matched the published stable checksum `f24008bd95682164b89d0d49ed346d5ba1a0728ce17a54abdd5fa518167304ee`.

## Remaining manual 1.0 gates

1. Open the exact packaged visual demo in Chromium and at least one second browser engine and exercise long-running animation plus hierarchy interactions. This execution environment blocks browser navigation to `file:`, localhost and `data:` URLs by administrator policy, so this gate cannot be honestly marked PASS here.
2. Exercise the packaged demo/runtime on the intended low-spec/mobile target and note frame/memory behavior.
3. Make the final 1.0 snapshot-support statement (for example whether 0.11/0.12 checkpoints remain accepted by 1.0).
4. If those gates reveal no defect, promote with no public API/schema rename and run both suites again from the clean 1.0 archive.

The visual demo still loads Three.js from CDN; the FPE runtime modules themselves have no Three.js dependency. Snapshot structural/integrity validation is not a digital signature. If checkpoints ever cross an untrusted transport boundary and authenticity matters, authentication belongs to the surrounding application/transport.
