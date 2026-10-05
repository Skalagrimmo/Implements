# EBE v0.7.0 — Institutional Policy Test Report

## Release gate

```text
Lua syntax: 77 files PASS
EBE core love.* dependencies: 0

historical v0.2.1 smoke: PASS
historical v0.2.1 hardening: PASS
renderer forwarding: PASS

v0.3 cognition / PixelGen bridge / distortion: PASS
v0.4 information ecology / source lineage: PASS
v0.5 network synthesis: PASS
v0.6 collective epistemics: PASS
v0.7 institutional policy: PASS
PixelGen 1.0 compatibility: PASS
```

## v0.7 policy behavior

The new editorial layer is subscriber-specific:

```text
same archived report
├─ publish to A
├─ timed hold for B
└─ suppress for C
```

Suppression does not remove the source report from the institution archive.

Agenda priority changes scheduling only. It does not mutate:

```text
claim value
origin_observation_ids
source_count
```

A publication confidence multiplier may only reduce confidence.

## Fuzz / soak

```text
EBE v0.3.0 fuzz passed: 200 simulations, 400 received rumor memories, 44 distorted transmissions
EBE v0.4.0 ecology fuzz passed: 120 simulations, 240 institutional evidence memories
EBE v0.5.0 network synthesis fuzz passed: 120 variants, avg institutions 11.04, avg routes 9.75, disconnected forests 48, routing log entries 2015
EBE v0.6.0 collective fuzz passed: 120 simulations, 120 echo reports, 120 independent consensuses, 120 publications
EBE v0.6.0 collective soak passed: 300 simulations, 240 consensus, 60 conflicts, 60 institution publications, 6900 submitted reports
EBE v0.7.0 policy fuzz passed: 120 simulations, 40 suppressions, 30 holds, 90 direct publications, 200 root-lineage checks
EBE v0.7.0 policy soak passed: 300 simulations, 1500 decisions, 1200 delivered, 300 suppressed, 300 held
```

## Determinism

The canonical institutional-policy demo ran in five fresh `texlua` processes.

All five outputs had SHA-256:

```text
d2953bbf18b262f70153a1bd5c170bfac23e5819d2f28881f23a30817968d4da
```

## Snapshot compatibility

Verified:

```text
v0.7 snapshot
→ restore
→ semantic equality

v0.6 institution snapshot without editorial state
→ Runtime.restore()
→ pass-through editorial policy
```

## Critical invariants

```text
message copies != independent evidence
membership != shared knowledge
censorship != historical erasure
agenda priority != truth mutation
```

## LÖVE2D

The release contains `main.lua`, `conf.lua`, and a ready `.love` archive.

The validation environment does not expose a `love` executable, so the LÖVE visual runtime
is syntax/package-structure checked but not claimed as executed here.
