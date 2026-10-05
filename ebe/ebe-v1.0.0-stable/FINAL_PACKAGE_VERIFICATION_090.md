# EBE v0.9.0 — Final Package Verification

The release archive was tested by extracting it into a clean directory and running the release gate from the extracted copy rather than from the working source tree.

## Packaged source gate

```text
Lua syntax: 93 files PASS
combined regression: PASS
legacy v0.2.1 smoke: PASS
legacy v0.2.1 hardening: PASS
renderer forwarding regression: PASS
```

## Packaged historical fuzz

```text
v0.3: 200 simulations PASS
v0.4: 120 simulations PASS
v0.5: 120 network variants PASS
v0.6: 120 collective simulations PASS
v0.7: 120 policy simulations PASS
v0.8: 160 semantic-action simulations PASS
```

## Packaged v0.9 fuzz

```text
160 persistence simulations
160 deterministic JSON roundtrips
160 runtime restores
160 v0.8 → v0.9 migrations
160 hostile snapshot mutations rejected
PASS
```

Strict JSON corpus:

```text
5,001 hostile inputs rejected
500 valid roundtrips
PASS
```

## Packaged soak

```text
v0.6: 300 collective simulations / 6,900 reports PASS
v0.7: 300 policy simulations / 1,500 decisions PASS
v0.8: 1,200 action requests PASS
v0.9: 2,000 action requests / ~1.09 MB JSON snapshot PASS
```

## Cross-engine package test

The extracted EBE package completed a real PixelGen 1.0 feedback loop:

```text
EBE request: front_deescalation front_0 amount=0.120000
PixelGen state revision: 2
derived event: derived_event_2
status: applied
PASS
```

## `.love` package

The `.love` archive was ZIP-structure verified and contains root-level:

```text
main.lua
conf.lua
```

A LÖVE executable is not present in the validation environment, so graphical runtime launch is not claimed as tested here. The pure-Lua EBE core remains renderer-independent.

## Frozen contracts

```text
EBE package/runtime version: 0.9.0
persistence contract: 0.9.0
PixelGen EBE bundle schema: 0.8.0
public API fingerprint: ebe-stablehash-v1:851079155
persistence fingerprint: ebe-stablehash-v1:1931923589
```

Release SHA-256 checksums are distributed separately in `ebe-v0.9.0-persistence-contract-freeze.sha256`.
