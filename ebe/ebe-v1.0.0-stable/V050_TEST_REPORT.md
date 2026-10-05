# EBE v0.5.0 — PixelGen Network Synthesis Test Report

## Release gate

```text
Lua syntax: 64 files PASS
EBE core love.* dependencies: 0

historical v0.2.1:
  smoke PASS
  hardening PASS
  renderer forwarding PASS

combined v0.3 / v0.4 / v0.5 regression:
PASS
```

## Fuzz

```text
v0.3 information-locality:
EBE v0.3.0 fuzz passed: 200 simulations, 400 received rumor memories, 44 distorted transmissions

v0.4 institutional ecology:
EBE v0.4.0 ecology fuzz passed: 120 simulations, 240 institutional evidence memories

v0.5 network synthesis:
EBE v0.5.0 network synthesis fuzz passed: 120 variants, avg institutions 11.04, avg routes 9.75, disconnected forests 48, routing log entries 2015
```

## Canonical PixelGen seed 7301 / 6×5

```text
institutions: 14
routes: 16
components: 1
accessible sectors: 30 / 30
network fingerprint: 1314574499
```

Five fresh `texlua` processes produced the same fingerprint:

```text
1314574499, 1314574499, 1314574499, 1314574499, 1314574499
```

Institution kinds:

```text
printing_house      2
shrine_circle       5
front_watch         4
roadside_relay      2
caravan_exchange    1
```

Important role counts:

```text
front_watch roles   5
regional_hub roles  3
road_corridor roles 1
```

A node can carry more than one role, so role counts are not required to sum to the institution count.

## Route integrity

The regression suite checks that every synthesized route:

```text
references existing institution endpoints
contains orthogonally adjacent sector steps
uses only legal PixelGen sector links
respects gated/secret access policy
keeps trust/distortion/risk in bounds
preserves route/path provenance
```

Secret links are excluded by default. An explicit secret-enabled synthesis is also validated.

## Agent access

For the canonical 6×5 world:

```text
sector access coverage = 30 / 30
```

Agents can:

```text
spawn after synthesis
move between sectors
detach from stale local institutions
attach to the new nearest reachable institution
report through their local network access path
```

## Source-lineage preservation

Institution routing retains independent observation roots.

Therefore:

```text
one observation
→ many relays
→ still one independent evidence root
```

while a genuinely independent witness can add a second root and enable corroborated knowledge.

## Disconnected-world policy

The v0.5 fuzz deliberately introduces:

```text
sealed links
route-cost cutoffs
landmark thinning
front-site thinning
secret/gated policy variants
degree variants
```

Some generated variants are intentionally disconnected.

EBE returns a deterministic minimum spanning **forest** and warning state rather than inventing an illegal connection.

## Fresh 12×12 stress from PixelGen v0.8

Four fresh 144-sector PixelGen worlds were generated and passed through the public JSON→Lua converter and v0.5 synthesizer:

```text
seed 0
landmarks=28
front_sites=0
main_path_nodes=89
institutions=38
routes=44
components=1
access=144/-1
fingerprint=1715882726
```

```text
seed 1
landmarks=37
front_sites=0
main_path_nodes=91
institutions=47
routes=54
components=1
access=144/-1
fingerprint=91977271
```

```text
seed 6060
landmarks=45
front_sites=0
main_path_nodes=97
institutions=55
routes=64
components=1
access=144/-1
fingerprint=1980580132
```

```text
seed 7301
landmarks=35
front_sites=0
main_path_nodes=101
institutions=48
routes=56
components=1
access=144/-1
fingerprint=1060458703
```

All four produced:

```text
components = 1
accessible sectors = 144 / 144
```

Timing values in `generated/v050_12x12_stress.json` are environment-specific validation measurements, not user-device benchmarks.

## LÖVE2D

The release includes:

```text
main.lua
conf.lua
start_love_windows.bat
```

and a ready `.love` archive.

The assistant validation environment does not currently provide a `love` executable, so the LÖVE visual path is syntax/package-structure checked rather than executed here. The EBE core itself remains pure Lua.
