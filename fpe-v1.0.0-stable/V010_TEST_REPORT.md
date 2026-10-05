# v0.10 validation

`python tools/run_tests.py`: PASS.

Retained gates: bridge regression, malformed Python validation, web core, scheduler, revision handoff, 2,000-operation hierarchy fuzz, public API replay/isolation/browser-global loading.

New action-request gate covers:

- cluster and bud target typing
- source binding to current PixelGen fingerprint/revision/tick
- detached payload and returned envelope ownership
- zero projection/view mutation from request creation
- malformed actions and unknown targets
- non-finite numbers, `undefined`, arrays at top level, non-plain objects, cycles and excessive nesting
- revision/tick rebinding after an accepted projection handoff

All local release gates pass with nine runtime methods and ten stable error codes.

Still outside v0.10 scope: authoritative action execution, direct writeback, runtime/scheduler persistence, authenticated browser checksums, GPU allocation rollback, spatial streaming, and real-device/browser visual-performance qualification for this exact build.
