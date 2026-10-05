# Migration: FPE v0.5.0 → v0.6.0

## Projection envelope

The bridge now emits `fpe.pixelgen_hierarchy/0.6.0` with mode `read_only_hierarchical_projection`. Consumers must require the new `hierarchy` object. Cluster records, bud records, PixelGen source identity, semantic mappings, and the four-buds-per-sector invariant are unchanged.

Because the hierarchy contract is part of the projection, v0.5 and v0.6 projection fingerprints intentionally differ even for the same PixelGen world/state pair.

## Browser API

The global/module name changes from `FPE05` to `FPE06`. Existing `buildGeometryPlan()` remains available. New APIs are:

```text
emptyViewState()
normalizeViewState(projection, state)
toggleCluster(projection, state, clusterId)
toggleBud(projection, state, budId)
buildHierarchyPlan(projection, state)
viewStateFingerprint(projection, state)
```

View state is deliberately not persisted inside the projection and is never submitted to PixelGen.
