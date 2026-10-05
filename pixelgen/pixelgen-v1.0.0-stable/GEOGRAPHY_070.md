# PixelGen 0.7 Geography Contract

## Invariants

1. Every sector belongs to exactly one geographic region.
2. Every region owns its seed center.
3. Every region is one connected 4-neighbor mass.
4. A sector's primary biome equals its region's primary biome.
5. A transition edge exists if and only if the adjacent sector belongs to another region.
6. Every transition sector receives a transition subbiome.
7. Every local scene carries the same geographic identity as its world sector.
8. Geography must not break the existing world topology or progression graph.
9. Same seed + same dimensions + same profile must produce the same semantic fingerprint.
10. Geography metadata is exportable independently as JSON/Lua.

## Current generation pipeline

```text
seed
↓
choose region count
↓
choose spaced region centers
↓
choose primary biome per region
↓
multi-source weighted flood growth
↓
region adjacency
↓
core/mid/margin classification
↓
transition edges
↓
subbiome assignment
↓
moisture/elevation/settlement fields
↓
local scene modifiers
↓
landmarks
↓
physical links
↓
encounters/finds
↓
navigation/progression grammar
```

## Why flood growth instead of noisy Voronoi

An early 0.7 prototype used weighted Voronoi assignment. Regression testing found a seed where a region could become geographically fragmented.

The release implementation therefore uses multi-source weighted flood growth. A sector can only be claimed through an already reached predecessor of the same region, guaranteeing connectivity by construction.
