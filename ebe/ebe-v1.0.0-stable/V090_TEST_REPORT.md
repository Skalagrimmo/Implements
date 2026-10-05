# EBE v0.9.0 — Test Report

## Release gate

Source-tree validation completed successfully with Lua 5.3 (`texlua`/LuaTeX runtime):

```text
Lua syntax files checked: 93 PASS
combined regression suite: PASS
legacy v0.2.1 smoke: PASS
legacy v0.2.1 hardening: PASS
renderer forwarding regression: PASS
core `ebe/` executable-data loaders (`dofile`/`loadfile`): 0
```

## Historical regression

The combined suite passed:

```text
package API
v0.3 cognition
v0.3 PixelGen runtime bridge
PixelGen 1.0 stable-contract compatibility
v0.3 deterministic distortion
v0.4 information ecology / source lineage
v0.5 network synthesis
v0.6 collective epistemics
v0.7 institutional policy
v0.8 semantic action requests
v0.9 persistence / hostile input / public contract
```

## Historical fuzz

```text
v0.3: 200 simulations, 400 received rumor memories, 44 distorted transmissions PASS
v0.4: 120 simulations, 240 institutional evidence memories PASS
v0.5: 120 network variants, 48 disconnected forests PASS
v0.6: 120 collective simulations PASS
v0.7: 120 policy simulations, 200 lineage checks PASS
v0.8: 160 action simulations; 160 requests / 160 exports / 40 rejected / 120 applied PASS
```

## v0.9 persistence / hostile-input fuzz

```text
160 simulations
160 JSON snapshot roundtrips
160 runtime restores
160 migrations from v0.8 metadata
160 hostile snapshot mutations rejected
PASS
```

Hostile mutations include non-finite clocks, invalid sectors, agent key/id mismatch, duplicate action-order IDs, forged source counts and wrong contract versions.

## Strict JSON corpus

```text
5,001 hostile JSON inputs rejected
500 valid deterministic JSON roundtrips
PASS
```

The hostile corpus covers duplicate keys, nulls, numeric overflow, trailing data, invalid escapes, trailing commas, unquoted keys, missing separators, unterminated strings and excessive nesting.

## Persistence soak

```text
2,000 semantic action requests
1,092,089-byte runtime snapshot JSON
bounded action audit log: 512
exact JSON → Runtime.restore() semantic roundtrip PASS
```

Historical soaks also passed:

```text
v0.6: 300 simulations / 6,900 collective reports
v0.7: 300 simulations / 1,500 policy decisions
v0.8: 1,200 semantic action requests
```

## Security / authority checks

Confirmed:

```text
Snapshot.read_lua() does not execute arbitrary snapshot code
PixelGen network/runtime Lua loading uses the safe literal-only parser
new requests cannot forge applied/exported status
PixelGen world actions cannot become applied before explicit export
wrong-subject feedback cannot resolve an exported request
matching authority feedback does resolve the exported request
source_count must match independent root count
cyclic snapshot tables are rejected
NaN / Infinity are rejected
failed staged write preserves previous committed snapshot
failed commit rolls back previous committed snapshot
```

## PixelGen 1.0 real roundtrip

Real cross-engine test passed:

```text
EBE v0.9.0 <-> PixelGen 1.0 real action roundtrip: PASS
request=ebe_action_1
front_deescalation front_0 amount=0.120000
pixelgen_revision=2
derived_event=derived_event_2
```

## Contract fingerprints

```text
public API contract:
ebe-stablehash-v1:851079155

persistence contract:
ebe-stablehash-v1:1931923589
```

## Environment limitation

The source/package can be syntax-checked and exercised as pure Lua in this environment. A LÖVE executable is not installed here, so the generated `.love` archive can be structurally verified but its graphical runtime launch is not claimed as PASS until run under LÖVE2D.
