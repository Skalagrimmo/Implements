# FPE v0.5.0 — PixelGen Local Cluster Bridge

## Boundary

PixelGen 1.0 remains the authority for objective semantic reality. FPE v0.5 consumes a matching `world.json + state.json` pair and produces a deterministic geometry projection.

```text
PixelGen world + dynamic state
        ↓ identity validation
PixelGen sector
        ↓
FPE local cluster
        ↓
4 deterministic buds
        ↓
renderer geometry plan
```

v0.5 is deliberately **read-only**. FPE interactions do not write directly into PixelGen state.

## Source identity

The bridge recomputes the PixelGen semantic world fingerprint using the PixelGen 1.0 public normalization rule and requires exact equality with `state.source_world.fingerprint`, seed, and dimensions.

## Mapping

Each PixelGen sector becomes exactly one local FPE cluster. Each cluster has exactly four buds. Static semantic tags preserve biome, subbiome, region, corridor membership, territory identity, and exact influence-topology `front_ids`.

Dynamic mapping:

```text
territory.control_strength → cohesion contribution
territory.stability        → breakup resistance
territory.alert            → agitation
front.tension              → collapse bias + straighter morphology
front.activity             → local update rate + agitation
front.status               → inspection/render context
```

Neutral/contested sectors are not assigned a fake territory. They receive explicit conservative projection defaults while retaining `territory_id = null`.

## Determinism

Bud orientation, curved-edge curvature, height variation, node phase, glyph choice, and other local variation derive from deterministic hash keys. Browser runtime code contains no `Math.random()`.

## Projection contract

Schema:

```text
fpe.pixelgen_local_cluster/0.5.0
```

The projection contains source identity, authority declaration, layout parameters, cluster records, bud records, summary counts, and a canonical SHA-256 `projection_fingerprint`.

## Authority rule

```text
PixelGen = objective semantic state
FPE      = physical/geometric manifestation
```

In v0.5:

```text
FPE → PixelGen writeback = disabled
```

A later version may emit semantic action requests, but it must not create a second authority path.
