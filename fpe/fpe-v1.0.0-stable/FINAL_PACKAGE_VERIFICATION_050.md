# FPE v0.5.0 — Final Package Verification

The release ZIP is extracted into a fresh directory and verified from that extracted copy.

Package-level gate:

```text
Python compileall                         PASS
bridge regression                        PASS
JavaScript geometry-core determinism      PASS
canonical projection validation           PASS
after-state projection rebuild byte match PASS
browser code Math.random executable calls 0
```

Packaged cross-engine smoke uses a real PixelGen 1.0 source tree and exercises the same bridge from fresh generated worlds:

```text
worlds      8
mutated     8
clusters    468
buds        1872
result      PASS
```

The broader release validation is recorded in `V050_TEST_REPORT.md`: 48 exact PixelGen 1.0 worlds were completed in four 12-world shards after a single monolithic 48-world attempt exceeded the interactive wall-clock. The interrupted monolithic run is not counted as a PASS.

Canonical package fixture remains:

```text
PixelGen 1.0 seed       7301
world                   6×5
clusters                30
buds                    120
world fingerprint       ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a
initial projection      5587f1abd8cc883465fdfce5d2ac8ebe84531461a827b51a10d70ba123996b2c
after-r3 projection     2d0c7d000b00416e5f727a3d84f43e559f467ce97ea8550c53cae91d051dce63
```

The final archive hash is provided in the sibling `fpe-v0.5.0-pixelgen-local-cluster.sha256` file.
