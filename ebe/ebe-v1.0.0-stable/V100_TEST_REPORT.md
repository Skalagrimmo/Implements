# EBE v1.0.0 — Test Report

## Stable promotion gate

- combined regression: **PASS**
- Lua syntax gate: **96 files PASS**
- v0.9 → v1.0 semantic parity: **PASS**
- fresh-process determinism: **10/10 identical semantic hash**
- real EBE 1.0 ↔ PixelGen 1.0 action roundtrip: **PASS**

Canonical semantic promotion hash after release metadata is stripped:

```text
676699684
```

## Historical fuzz / soak

```text
v0.3 fuzz   200 simulations PASS
v0.4 fuzz   120 simulations PASS
v0.5 fuzz   120 network variants PASS
v0.6 fuzz   120 simulations PASS
v0.7 fuzz   120 simulations PASS
v0.8 fuzz   160 simulations PASS
v0.9 fuzz   160 simulations PASS

v0.6 soak   300 simulations / 6900 reports PASS
v0.7 soak   300 simulations / 1500 decisions PASS
v0.8 soak   1200 action requests PASS
v0.9 soak   2000 action requests PASS
```

Strict JSON extended corpus:

```text
10,001 hostile inputs rejected
1,000 valid roundtrips
PASS
```

## New v1.0 torture

```text
500 simulations
500 JSON/snapshot roundtrips
500 historical migrations
500 hostile snapshot rejects
500 hostile JSON rejects
PASS
```

Long v1.0 soak:

```text
5,000 action requests
10 full serialization/restore checkpoints
2,204,715-byte final JSON snapshot
bounded action audit log = 512
PASS
```

## Defects found during final promotion review

The pre-1.0 review found and fixed three contract issues before release:

1. documented Runtime methods (`assign_local_observations`, `share`, `get_belief`, `get_knowledge`, `restore`) existed but were missing from the freeze-candidate method list;
2. strict JSON accepted invalid raw UTF-8 bytes;
3. nested action-gateway/request version metadata and action log/sequence bounds were not validated tightly enough.

All are now covered by v1.0 regression tests.

## Promotion parity demo SHA-256

```text
action_request_demo        044f0311280ca1958ae4f854509ae644753a7efb8afd8e59c498e0281c82a204
collective_epistemics_demo fce1f250178c3b1fd082682b4fa4acf79872d52622d868d0affd928f8f10cceb
institutional_policy_demo  d2953bbf18b262f70153a1bd5c170bfac23e5819d2f28881f23a30817968d4da
network_synthesis_demo     ee088f2b07d92f56b814fdb83a3982bf8c074d6e081c388d9261624d34644663
information_ecology_demo   91985b7c3e93c247b3352895e3060155073aadf4174706e06831c697d4890cd1
```
