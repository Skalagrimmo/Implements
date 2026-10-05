# PixelGen v1.0.0 — Final Package Verification

The release archive was created, extracted into a clean temporary directory, and exercised from the extracted package rather than the working tree.

## Extracted-package gates

```text
python -m compileall pixelgen runtime_cli.py cli.py render_cli.py   PASS
python tests/test_v100.py                                          PASS
python tests/test_v093.py                                          PASS
python tests/fuzz_v093.py                                          PASS
runtime_cli.py capabilities                                        PASS
runtime_cli.py contract                                            PASS
verify real legacy 0.9.3 bundle with 1.0 package                  PASS
```

Fresh packaged `fuzz_v093.py` result:

```text
40 worlds
225 runtime events
40 migrations
10 verified bundles
112 hostile rejects
32 incremental EBE checks
PASS
```

Legacy manifest compatibility from the extracted 1.0 package:

```text
contract_version: 0.9.3
status: pass
world fingerprint:
ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a
```

Stable 1.0 contract fingerprint:

```text
eb2deceb5913231addf4d9ddb323843c0832f25ee1f0b737378f53cbc892727c
```

## Result

```text
FINAL PACKAGE GATE: PASS
```
