# PixelGen v0.9.0 — Regional Corridors / Macro-to-Local Continuity

## Purpose

v0.9.0 adds the first explicit world-scale continuity layer above biome/region geography.

```text
WORLD
↓
REGION
↓
REGIONAL CORRIDOR TOPOLOGY
↓
SECTOR ENTRY / EXIT ANCHORS
↓
LOCAL WALKABLE REALIZATION
↓
SCENE
```

The important invariant is:

```text
global corridor topology is chosen once at world scale
+
local scenes realize that topology through their actual reciprocal exits
```

Local scene generation does not get to silently change the global sector order.

## Corridor kinds

```text
old_road
pilgrim_route
ridge_chain
silt_vein
drainage_channel
```

The kind affects world-scale routing cost and local visual metadata.

### Biome defaults

```text
silt_marsh        → drainage_channel
dark_forest       → old_road
frozen_pass       → ridge_chain
ruined_settlement → old_road
reformed_chapel   → pilgrim_route
```

### Landmark spurs

```text
printing_cathedral    → pilgrim_route
printing_press_altar  → pilgrim_route
silt_spire            → silt_vein
nanolith_shrine       → silt_vein
```

## Planning layers

### World spine

Every multi-sector geography world attempts one world spine:

```text
[0,0]
↓
world-scale landmark
```

If there is no world-scale landmark, the opposite corner is used.

### Regional connectors

Every region center is connected to the already established macro network.

This ensures the region is not merely a colored biome mass: it participates in world-scale continuity.

### Landmark spurs

Regional/world landmarks that are not already on the macro network receive deterministic spurs to the nearest network sector.

## Weighted routing

Routing is deterministic 4-neighbor Dijkstra-style pathing.

Different corridor kinds prefer different geography fields:

```text
old_road
→ settlement / moderate elevation

pilgrim_route
→ settlement / chapel + ruin geography

ridge_chain
→ high elevation / frozen-pass bias

silt_vein
→ moisture / Silt geography

drainage_channel
→ moisture + low elevation
```

The result is not a random Manhattan line.

## Macro-to-local realization

After physical sector links have been generated, PixelGen resolves every macro corridor step against the actual reciprocal world links.

A local record contains:

```text
corridor_id
kind
purpose
visual_material
path_index
anchors[]
route_cells[]
```

Each anchor stores:

```text
edge
coord
x / y
to sector
```

The local route uses the already walkable scene graph between those anchors.

v0.9.0 deliberately does **not** carve a second independent gameplay network on top of the scene. This keeps v0.8 scene/gameplay semantics unchanged while exposing a stable macro corridor layer to future renderers and systems.

## Link metadata

Every physical sector link crossed by a corridor gets:

```text
link.corridors[]
```

For example:

```json
{
  "id": "corridor_01_old_road",
  "kind": "old_road"
}
```

This survives later gameplay gating:

```text
physical road exists
+
gameplay state may be open / gated / secret / sealed
```

The geographic corridor and gameplay lock are intentionally separate concepts.

## Sector metadata

Every sector has:

```text
sector.corridors[]
```

and each generated scene gets:

```text
scene.regional_corridors[]
```

The geography context also contains planned corridor membership during scene generation.

## Determinism

Given the same:

```text
seed
world dimensions
geography
landmark plan
```

corridor topology and local realization are deterministic.

The corridor layer is part of the PixelGen semantic world fingerprint from v0.9.0 onward.

## Additive-compatibility invariant

v0.9.0 was compared with v0.8.0 for:

```text
7301  6×5
6060  4×3
42    8×6
-777  1×1
```

After removing only:

```text
regional_corridors
sector.corridors
link.corridors
scene.regional_corridors
release labels
```

the old v0.8 semantic projection is byte-canonical identical for every tested world.

So v0.9.0 adds continuity metadata without silently changing the established biome, scene, encounter, progression, influence, territory, or dynamic-state outputs.
