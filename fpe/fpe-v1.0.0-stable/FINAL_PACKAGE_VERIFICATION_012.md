# FPE v0.12.0 — final package verification

This file records the clean-archive procedure used for the 0.12 freeze candidate.

## Procedure

1. Rebuild `fpe-v0.12.0-demo.html` from the current sources.
2. Package a clean tree with no stale 0.11 demo and no temporary browser experiments.
3. Compute the archive SHA-256.
4. Unpack that exact archive into a new directory.
5. Run the release gates from the unpacked bytes, with heavy fuzz gates invoked independently to avoid a wrapper wall-clock timeout.
6. Run the extended corruption, persistence and large-world stress gates from the unpacked bytes.
7. Run cross-engine FPE fuzz from the unpacked bytes against the exact PixelGen 1.0 stable source tree whose archive SHA-256 is `f24008bd95682164b89d0d49ed346d5ba1a0728ce17a54abdd5fa518167304ee`.

The final outcome and package checksum are reported alongside the delivered archive after the replay completes.
