# PixelGen 0.7.2 — Subbiome / Ecotone Structural Variation

## Why 0.7.2 exists

0.7.0 created region-scale geography.

0.7.1 gave each primary biome its own structural grammar.

0.7.2 pushes structural identity one level deeper:

```text
WORLD
↓
REGION
↓
PRIMARY BIOME
↓
SUBBIOME / CORE-MID-MARGIN
↓
LOCAL STRUCTURAL VARIANT
↓
ECOTONE ADAPTER
↓
SCENE
```

The same `dark_forest` grammar no longer means every forest sector has the same kind of root network.

## Structural operators

A subbiome modifies its parent biome skeleton using small deterministic operators rather than replacing the whole grammar.

Current operators:

```text
prune_leaves
small_platform
large_platform
side_loop
extra_spurs
widen
crossing
edge_bias
intensify
```

This preserves the parent's visual language while changing its local morphology.

## Examples

### Silt Marsh

```text
deep_bog
→ prune leaves + small platform

blackwater_basin
→ large platform / dry island

reed_channels
→ side loop

peat_islands
→ repeated small platforms

wet_meadow
→ lower branching + wider route

fen_edge
→ route biased toward the world edge
```

### Dark Forest

```text
redwood_core
→ thick central root mass

root_maze
→ extra spurs / branching

moss_grove
→ local loop

wet_pine
→ branches + widening

forest_edge
→ reduced interior branching + edge bias

scrub_march
→ sparse branches + edge bias
```

Equivalent operator profiles exist for Frozen Pass, Ruined Settlement and Reformed Chapel.

## Zone influence

Subbiome operators are combined with regional position:

```text
core
→ intensify

mid
→ parent grammar baseline

margin
→ edge bias
```

So even two sectors with the same subbiome family can react differently to where they sit inside the region.

## Ecotone structural adapters

In 0.7.0 an ecotone physically mixed neighboring terrain material.

In 0.7.2 the **route skeleton itself** now reacts to the regional boundary.

For every declared cross-region edge:

```text
local structural skeleton
↓
nearest path cell
↓
deterministic connector
↓
correct N/E/S/W sector edge
↓
neighboring region
```

The adapter is stored in scene metadata:

```text
edge
neighbor_biome
neighbor_region_id
path_cells[]
```

The structural integrity validator requires adapter edges to match the geography transition edges exactly.

## Hybrid route rendering

Ecotone adapter cells can inherit the neighboring biome's route material.

Example:

```text
Dark Forest route
pine / roots
────────────
          ╲
           ╲  ecotone adapter
            ╲
             peat-like route material
             → Silt Marsh
```

The adapter also receives a restrained nano-glow outline in debug/demo rendering.

## Structural analysis

`structural-check` now reports:

```text
distinct parent grammar IDs
distinct path visuals
distinct subbiome variant IDs
ecotone adapter count
average morphology per biome
ecotone pressure
```

The analyzer also distinguishes between:
- accidental morphology drift;
- junctions/loops intentionally created by a subbiome operator;
- junctions/loops intentionally created by ecotone adapters.

This prevents an intended transition from being misclassified as a broken parent grammar.

## New demo

```bash
python cli.py subbiome-structure-demo   --biome dark_forest   --seed 7200
```

It renders:

```text
core variants
mid variants
margin variants
one ecotone sample
```

with a local skeleton below each scene.

## Compatibility invariants

1. Parent biome grammar remains valid.
2. Structural network remains connected.
3. Variant identity matches the geography subbiome/zone.
4. Every geography transition edge has exactly one structural adapter.
5. Every adapter reaches the declared sector boundary.
6. Navigation still sees logical `path`.
7. Progression remains fully reachable.
8. Same seed remains fingerprint-deterministic.
