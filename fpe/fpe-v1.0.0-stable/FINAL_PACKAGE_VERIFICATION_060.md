# FPE v0.6.0 Final Package Verification

## Promotion decision

FPE v0.6.0 is accepted as the hierarchical-view milestone toward v1.0.

## Frozen contracts

- projection: `fpe.pixelgen_hierarchy/0.6.0`;
- hierarchy: `fpe.view_hierarchy/0.6.0`;
- authority: PixelGen owns objective state, FPE owns geometry, viewer owns transient expansion state;
- expansion semantic effect: none;
- exactly one cluster per PixelGen sector and four buds per cluster;
- deterministic hash-derived geometry with no executable `Math.random()`.

## Package contents

The package includes Python bridge/CLI, canonical PixelGen 1.0 fixtures, initial and after-state projections, modular browser viewer, single-file demo, regression/fuzz tests, migration notes, hierarchy contract, historical v0.5 documentation, changelog, and version marker.

Transient `__pycache__`, `.pyc`, and generated fuzz-world artifacts are excluded from the release archive.

## Next milestone

FPE v0.7 should add a deterministic multi-rate scheduler over the stable v0.6 hierarchy. It must not introduce an independent semantic clock or mutate PixelGen authority.
