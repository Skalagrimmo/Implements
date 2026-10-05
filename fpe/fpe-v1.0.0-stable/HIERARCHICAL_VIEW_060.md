# FPE v0.6.0 — Hierarchical View Contract

## Boundary

The semantic authority contract is unchanged:

```text
PixelGen = objective semantic state
FPE      = physical/geometric manifestation
viewer   = transient expansion state
```

Expansion has `semantic_effect = none`; it cannot change the projection fingerprint or write to PixelGen.

## Levels

```text
world
└── cluster proxy (one per PixelGen sector)
    └── bud proxy (exactly four per expanded cluster)
        └── geometry (nodes and edges for an expanded bud)
```

Projection schema: `fpe.pixelgen_hierarchy/0.6.0`.

Hierarchy schema: `fpe.view_hierarchy/0.6.0`.

## View state

View state contains sorted, deduplicated arrays:

```json
{"expandedClusters": [], "expandedBuds": []}
```

Unknown IDs are discarded. A bud can remain expanded only while its parent cluster is expanded. Collapsing a cluster atomically removes all descendant bud expansions.

## Determinism and cost

Collapsed worlds materialize only 30 cluster proxies in the canonical fixture. Opening one cluster replaces one proxy with four bud proxies. Full node/edge geometry is generated only for buds selected for detail. Identical projection plus normalized view state yields byte-identical hierarchy plans.

All geometry variation remains hash-derived; executable browser code contains no `Math.random()`.

## Deferred

- multi-rate scheduling is reserved for v0.7;
- semantic action requests and PixelGen round-trip remain deferred;
- FPE still has no mutable semantic state.
