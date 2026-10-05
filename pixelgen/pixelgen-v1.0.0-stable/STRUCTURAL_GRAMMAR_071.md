# PixelGen 0.7.1 — Biome Structural Grammar

## Problem addressed

PixelGen 0.7.0 solved large-scale geography, but many local sectors still inherited the same visual route skeleton:

```text
horizontal path
+
vertical trunk
+
small forks
```

That made unrelated biomes share a recognizable "branching slab" pattern.

0.7.1 moves this responsibility into a biome-specific structural grammar.

## New local hierarchy

```text
REGION / SUBBIOME
↓
BIOME STRUCTURAL GRAMMAR
↓
ROUTE / STREET / RIDGE / ROOT SKELETON
↓
LOCAL TERRAIN + HAZARDS
↓
LANDMARKS / PROPS / ENCOUNTERS
```

## Five structural grammars

### `silt_marsh` → `meandering_causeways`

```text
~~~~~ water / peat
───╮
   ╰──────╮
          ╰──
```

Properties:
- low branching;
- dry causeways and stepping islands;
- route material visually follows peat;
- occasional short alternate wet crossing;
- no fixed central trunk.

### `dark_forest` → `root_branch_network`

```text
      ╱──
───●───
   ├────
   ╰──
```

Properties:
- true branching is intentionally retained here;
- several irregular root/stem branches;
- multiple endpoints;
- organic turns and local loops;
- route material follows pine/forest floor.

### `frozen_pass` → `ridge_zigzag`

```text
───┐
   └──┐
      └───┐
          └─
```

Properties:
- long angular ridge traverse;
- many turns, few junctions;
- sparse side shelf;
- route material follows ice;
- avoids universal T-shaped slab networks.

### `ruined_settlement` → `street_grid`

```text
│       │
├───────┤
│  ┌──┐ │
├──┘  └─┤
│       │
```

Properties:
- orthogonal street grid;
- blocks and plaza loops;
- many intersections;
- strong urban regularity;
- large civic landmarks may integrate into paving rather than being rejected by all path reservations.

### `reformed_chapel` → `axial_cloister`

```text
    │
  ┌─┼─┐
  │ │ │
──┼─┼─┼──
  │ │ │
  └─┼─┘
    │
```

Properties:
- processional axis;
- transept;
- enclosed cloister/courtyard loops;
- intentional symmetry;
- visually distinct from settlement grid despite sharing chapel paving material.

## Navigation contract

`path` remains a logical navigation token.

0.7.1 separates:

```text
logical route
≠
visible route material
```

So a path can remain mechanically identical while rendering as:

```text
marsh   → peat
forest  → pine
frozen  → ice
ruins   → chapel paving
chapel  → chapel paving
```

This preserves navigation/gameplay compatibility while changing visual morphology.

## Structural metrics

Every scene now stores:

```text
path_cells
endpoints
junctions
turn_like_cells
loop_rank
components
```

This lets the generator test morphology rather than only storing a grammar name.

Example intended profiles:

```text
marsh       low junctions, low loops
forest      high endpoints, real branches
frozen      many turns, few branches
settlement  many junctions + loops
chapel      axial intersections + courtyard loops
```

## New commands

Generate one sample for every biome:

```bash
python cli.py biome-structure-demo --seed 7100
```

Analyze a generated world:

```bash
python cli.py structural-check world.json
```

The check reports average morphology per biome and warns if a biome drifts away from its intended structural profile.

## Integration fixes discovered during 0.7.1

Three useful edge cases were found during regression work:

1. A generated settlement plaza could become an isolated path component.
   - fixed by connecting the plaza to the street fabric by construction.

2. Dense street grids could leave no legal footprint for a world-scale civic landmark.
   - major civic landmarks can now consume structural street/courtyard paving;
   - spawn and genuinely critical reservations remain protected.

3. Standalone scenes without geography stored empty structural fields as Lua `nil`.
   - absent optional fields are now omitted, preserving the old nil-free Lua export contract.
