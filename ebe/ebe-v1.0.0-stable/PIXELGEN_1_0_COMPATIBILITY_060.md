# EBE v0.6.0 — PixelGen 1.0 Stable Compatibility

PixelGen 1.0 keeps its EBE runtime handoff schema at:

```text
bundle version = 0.8.0
```

while the source generator identifies itself as:

```text
PixelGen 1.0.0
```

EBE v0.6 therefore keeps the explicit bridge name:

```lua
EBE.PixelGenV080
```

because that name describes the **bundle contract**, not the current PixelGen package release.

## Verified PixelGen 1.0 canonical fixture

Fresh PixelGen 1.0 `state-demo` output for:

```text
seed 7301
6 × 5
```

was imported into the v0.6 test fixture.

The runtime bundle contains:

```text
11 static/dynamic semantic entities
3 derived events
13 local observations
```

and declares:

```text
version = 0.8.0
source.world.generator.version = 1.0.0
```

EBE v0.6 verifies:

```text
local evidence assignment
agent cognition
source lineage
collective aggregation
```

against that real 1.0-generated fixture.

## Full-world network compatibility

A compact network view generated from the same PixelGen 1.0 world produces:

```text
14 institutions
16 routes
1 connected component
30 / 30 sectors accessible
```

with deterministic synthesis across repeated runs.

## Fail-closed bridge versioning

If a future PixelGen release changes the EBE handoff schema from `0.8.0`, v0.6 does not guess compatibility.

For example:

```text
bundle version = 0.9.0
```

is rejected until EBE explicitly supports that contract.

This keeps package-version compatibility separate from handoff-schema compatibility.
