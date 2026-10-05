# EBE v0.6.0 — Collective Epistemics Test Report

## Release gate

```text
Lua syntax: 72 files PASS
EBE core love.* dependencies: 0

historical v0.2.1 smoke: PASS
historical v0.2.1 hardening: PASS
renderer forwarding: PASS

v0.3 cognition / PixelGen bridge / distortion: PASS
v0.4 information ecology / source lineage: PASS
v0.5 network synthesis: PASS
v0.6 collective epistemics: PASS
PixelGen 1.0 stable-contract compatibility: PASS
```

## Fuzz / soak

```text
EBE v0.3.0 fuzz passed: 200 simulations, 400 received rumor memories, 44 distorted transmissions
EBE v0.4.0 ecology fuzz passed: 120 simulations, 240 institutional evidence memories
EBE v0.5.0 network synthesis fuzz passed: 120 variants, avg institutions 11.04, avg routes 9.75, disconnected forests 48, routing log entries 2015
EBE v0.6.0 collective fuzz passed: 120 simulations, 120 echo reports, 120 independent consensuses, 120 publications
EBE v0.6.0 collective soak passed: 300 simulations, 240 consensus, 60 conflicts, 60 institution publications, 6900 submitted reports
```

## Core invariant

Membership never creates knowledge by itself.

```text
membership != shared memory
membership != shared belief
membership != shared knowledge
```

Repeated relays preserve evidence roots:

```text
message copies != independent evidence
```

Independent roots are required for corroboration/consensus.

## Determinism

The canonical collective demo was executed in five fresh `texlua` processes.
All outputs had the same SHA-256:

```text
fce1f250178c3b1fd082682b4fa4acf79872d52622d868d0affd928f8f10cceb
```

## LÖVE2D

`main.lua` / `conf.lua` and the release `.love` archive are syntax/package-structure
checked. This validation environment does not expose a `love` executable, so the
visual runtime is not claimed as executed here.
