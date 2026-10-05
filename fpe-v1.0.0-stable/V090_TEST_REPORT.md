# v0.9 validation

`python tools/run_tests.py`: PASS.

Executed bridge regression, malformed Python validation, modular/standalone script syntax checks, scheduler tests, handoff tests, 2,000 hierarchy operations, and public API tests.

Public API tests pin exports, eight methods and nine codes; cover detached projection/view/plan results, failed handoff without data replacement, retained expansion, duplicate idempotence, monotonic ticks across revision handoff, deterministic replay, and browser-global module loading in a VM without WebGL.

No real-browser visual or device performance test for v0.9 was performed. User confirmation of browser behavior applies to earlier v0.8 only. Cross-engine 48-world fuzz was last executed for v0.8; bridge output and fixtures are unchanged in v0.9, so it was not repeated here.

Still out of scope: semantic action requests, runtime persistence, authenticated checksums in browser, GPU allocation rollback. Public API is a freeze candidate, not a v1.0 promotion.
