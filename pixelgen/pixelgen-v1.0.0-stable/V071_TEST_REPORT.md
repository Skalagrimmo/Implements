# PixelGen v0.7.1 — Biome Structural Grammar Test Report

## Release gate

- combined historical regression suite through v0.7.1: **15 PASS**
- v0.7.1 structural fuzz: **300 worlds PASS**
- larger-world structural stress: **40 worlds PASS**
  - 8×6
  - 10×8
- `doctor`: **PASS**
- `gameplay-check`: **PASS**
- `structural-check`: **PASS**
- `inspect`: **PASS**
- canonical structural score: **100/100**

## Canonical five-biome signatures

| Biome | Grammar | Path visual | Junctions | Endpoints | Turns | Loop rank |
|---|---|---|---:|---:|---:|---:|
| silt_marsh | meandering_causeways | peat | 0 | 2 | 6 | 0 |
| dark_forest | root_branch_network | pine | 8 | 5 | 9 | 3 |
| frozen_pass | ridge_zigzag | ice | 1 | 3 | 10 | 0 |
| ruined_settlement | street_grid | chapel | 10 | 8 | 2 | 4 |
| reformed_chapel | axial_cloister | chapel | 14 | 4 | 7 | 10 |

## Canonical 6×5 seed 7000

Structural analyzer:

```text
PASS
score 100/100
3 biome grammars present
3 distinct visible path materials
```

The world contains:

```text
frozen_pass       → ridge_zigzag
ruined_settlement → street_grid
dark_forest       → root_branch_network
```

All structural networks are connected.

## Edge cases caught during development

### Isolated settlement plaza

An early `street_grid` sample could generate a plaza loop not connected to the main streets.

Fix:

```text
plaza
↓
explicit connector
↓
street fabric
```

Connectivity is now guaranteed by construction and checked by `components == 1`.

### Civic landmark vs dense street grid

A world-scale Printing Cathedral could fail placement because all structural street paving was treated as untouchable reserved path.

Fix:

- structural path reservations and critical reservations are distinguished;
- regional/world civic landmarks may consume structural paving;
- spawn safety cells remain forbidden.

### Lua nil regression

Standalone scenes have no region/subbiome context. Empty optional fields initially serialized as Lua `nil`, violating the historical export contract.

Fix:

- absent optional structural fields are omitted instead of serialized as nil.
