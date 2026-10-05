# FPE v0.6.0 Test Report

## Result

All v0.6 release gates pass.

| Gate | Result | Coverage |
| --- | --- | --- |
| Python bridge regression | PASS | schema, hierarchy contract, source identity, deterministic projection, validation failures |
| JavaScript hierarchical core | PASS | collapsed/cluster/bud detail plans, reversible collapse, projection immutability, script syntax, standalone demo |
| Hierarchy state fuzz | PASS | 2,000 deterministic toggle operations, no orphan buds, stable accounting |
| PixelGen cross-engine fuzz | PASS | 48 worlds, 48 dynamic mutations, 2,808 clusters, 11,232 buds |
| Python bytecode compilation | PASS | bridge, CLI, tests, asset builder |

## Canonical fixture

- PixelGen: 1.0.0
- seed/dimensions: `7301 / 6×5`
- world fingerprint: `ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a`
- initial v0.6 projection fingerprint: `e62718146d9393f265317e3a2351fecc0ba0757862748be2d322ec4043e699c8`
- after-state v0.6 projection fingerprint: `678c6027a279ceeade30c7f0284554bdc47dfe94507a6aa1d4276dc4f69750c1`
- changed clusters after PixelGen revision 3: 25

## Hierarchy checks

- collapsed: 30 cluster proxies and zero detailed geometry;
- one expanded cluster: 29 cluster proxies plus 4 bud proxies;
- one expanded curved bud in the canonical first cluster: 14 nodes / 22 edges;
- identical normalized view states produce identical plans and view fingerprints;
- collapsing a cluster removes descendant bud expansion;
- projection JSON remains byte-identical through every view operation.
