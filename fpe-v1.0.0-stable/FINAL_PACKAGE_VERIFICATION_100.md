# FPE 1.0 stable package verification

This tree is the stable-promotion candidate. The package is accepted only if the ZIP is unpacked into a fresh directory and the release gates pass from those extracted bytes without source modification.

## Pre-package verified gates

- bridge regression and malformed validation — PASS;
- 256 Python↔JavaScript projection fingerprint parity cases — PASS;
- 10/10 fresh-process deterministic trace hashes — PASS;
- hierarchy/scheduler/handoff/public API/action request/persistence regressions — PASS;
- 2000 hierarchy-fuzz operations — PASS;
- 4500 persistence-fuzz operations / 460 restores / 790 full-state checks — PASS;
- 64 frozen 0.12→1.0 promotion semantic traces — PASS;
- RC hardening — PASS;
- 2400 corrupt snapshots rejected / 250 valid snapshots preserved — PASS;
- 5000 extended persistence operations / 698 restores / 923 comparisons — PASS;
- 10,000 clusters / 40,000 buds / 200 scheduler ticks / exact large snapshot restore — PASS;
- 500 current v1.0 round-trips / 500 historical 0.11+0.12 migrations / 500 hostile snapshot rejects — PASS;
- exact PixelGen 1.0 stable cross-engine fuzz — 96 worlds PASS.

## Package acceptance procedure

1. build `fpe-v1.0.0-demo.html` from checked-in sources;
2. remove transient caches and stale versioned demo artifacts;
3. create the ZIP candidate;
4. run ZIP integrity test;
5. unpack into a new directory;
6. compare extracted package files with the packaged source tree;
7. rerun normal, promotion and extended gates from extracted bytes;
8. rerun exact PixelGen 1.0 cross-engine fuzz from extracted bytes;
9. if no byte is changed after step 3, rename the exact candidate ZIP bytes to `fpe-v1.0.0-stable.zip` and publish a SHA-256 sidecar.

The external sidecar verification report records the final archive SHA-256 and clean-archive replay result so the archive itself does not need to be repacked after verification.
