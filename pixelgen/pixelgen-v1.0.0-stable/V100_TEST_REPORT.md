# PixelGen v1.0.0 — Stable Promotion Test Report

## Stable contract

```text
package/runtime API: 1.0.0
contract manifest:    1.0.0
contract status:      stable
contract fingerprint: eb2deceb5913231addf4d9ddb323843c0832f25ee1f0b737378f53cbc892727c
```

Mature semantic payload schemas were deliberately not renumbered.

## Fresh 1.0 promotion/parity gate

Eight worlds were generated independently from the final 0.9.3 baseline and the 1.0.0 tree:

```text
7301   6×5
6060   4×3
42     8×6
-777   1×1
0      12×12
1      12×12
6060   12×12
7301   12×12
```

For all 8 cases:

```text
world semantic fingerprint: identical
initial dynamic-state fingerprint: identical
```

Canonical 7301 / 6×5 remains:

```text
ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a
```

## Fresh compatibility/hardening gates

```text
test_v091  runtime / renderer separation       PASS
test_v092  schema / migration compatibility    PASS
test_v093  hostile input / atomic I/O           PASS
test_v100  stable promotion / bundle            PASS

fuzz_v090 regional corridors                   PASS
fuzz_v091 renderer-free runtime                 PASS
fuzz_v092 contract migration                    PASS
fuzz_v093 hostile input / bundles / EBE         PASS
```

The v0.9.3 fuzz retained:

```text
40 worlds
225 runtime events
40 migrations
10 verified bundles
112 hostile-input rejects
32 incremental EBE checks
```

## Legacy manifest compatibility

A real bundle was written by the 0.9.3 package, then verified by PixelGen 1.0.0. Result:

```text
status: pass
manifest version: 0.9.3
historical contract fingerprint recognized
world semantic fingerprint preserved
```

## Fresh 12×12 replay check

Seed 7301 / 12×12 was generated under 1.0.0 and subjected to 30 runtime mutations.

```text
revision: 30
territories: 7
fronts: 0
exact replay: PASS
world fingerprint: e4edb22d22f2fb2ca50bb7312e9415da3a0d6505134e2f75abcdfe90b80565c9
state fingerprint: c1d595916f975e4822cebecd1efc7f5aed5bdffb8cddd61ba6210d8fbfd8c9be
```

The lack of fronts for this 12×12 case is the known fixed-radius influence behavior from the pre-1.0 line, not a 1.0 regression.

## Historical pre-1.0 evidence retained

The immediately preceding 0.9.3 release already passed the dense pre-1.0 torture campaign: historical regression/fuzz, hostile JSON, migration matrix, transactional write/rollback tests, fresh-process determinism, 12×12 mutation/replay stress and package-level verification. The 1.0 promotion changed contract/package metadata rather than semantic generation rules, and the fresh parity gate above verifies that semantic identity was preserved.

## Release conclusion

```text
PixelGen 1.0.0 stable promotion: PASS
```
