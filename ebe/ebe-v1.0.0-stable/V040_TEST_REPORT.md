# EBE v0.4.0 — Information Ecology Test Report

## Release gate

```text
historical v0.2.1 regression: 3 PASS
v0.3 + v0.4 combined regression: 5 PASS

v0.3 rumor/locality fuzz:
200 simulations PASS

v0.4 institutional ecology fuzz:
120 simulations PASS
240 institutional evidence memories
```

Validation runtime:

```text
texlua
```

All Lua files were also syntax-checked with `texluac`.

## Canonical route

```text
Mara
↓
Printing House
↓
Caravan Exchange
↓
Levko
```

First independent evidence root:

```text
Levko belief = tense
roots = 1
knowledge = no
```

After an echo loop:

```text
Levko → Oles → Levko
```

result remains:

```text
roots = 1
knowledge = no
```

The echo adds another reporter but does not add independent evidence.

After Iva independently reports the same event:

```text
roots = 2
knowledge = tense
basis = corroborated_reports
```

## Institutional route provenance

Canonical institutional evidence records:

```text
route:
print_house
→ caravan
→ levko

hop_count = 3
```

## Cycle protection

Regression test adds:

```text
print_house → caravan
caravan → print_house
```

and verifies:

```text
queue drains
routing log remains bounded
no infinite recirculation
```

Protection mechanisms:

```text
institution revisit detection
max_hops = 8
```

## Snapshot compatibility

Verified:

```text
v0.4 snapshot
→ restore
→ semantic equality
```

and:

```text
v0.3 snapshot without ecology
→ Runtime.restore()
→ valid v0.4 runtime
→ empty ecology
```

## Preserved contracts

Still passing:

```text
EBE.create legacy API
v0.2.1 smoke
v0.2.1 hardening
renderer forwarding
PixelGen v0.8 bridge
v0.3 cognition
v0.3 delayed rumor propagation
v0.3 deterministic distortion
```

## Current limitation

v0.4 institutions are semantic routing nodes.

They do not yet automatically derive their graph from PixelGen settlements, roads, factions or landmarks.

That is a natural later integration step.
