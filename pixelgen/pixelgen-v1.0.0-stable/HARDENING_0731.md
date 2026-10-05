# PixelGen 0.7.3.1 — Hardening Contract

## Patch goal

Preserve the 0.7.3 feature set while making influence effects causally trustworthy.

## Invariants

### Hazard monotonicity

For fixed:

```text
seed
biome
subbiome
geography
```

and otherwise equal modifiers:

```text
hazard_mult A < hazard_mult B
```

must not produce more hazard cells under A than under B.

### Encounter monotonicity

For fixed seed:

```text
encounter_mult A < encounter_mult B
```

must not produce a larger encounter target under A.

Fractional changes must survive integer conversion across a distribution of seeds.

### Civic safety

`print_civic` may raise civic prop density, but must not do so by increasing hazardous Silt-growth props.

### Morphology

```text
Frozen Pass
→ angular ridge / low-loop morphology

Silt Marsh
→ meandering causeways / thin island spurs
```

Subbiome variation must remain deterministic and connected.

### Lua export

Optional dictionary fields with no value are omitted.

### Compatibility

The patch must preserve:

```text
regional geography
landmarks
subbiome/ecotone structure
progression
fingerprinting
influence maps
JSON/Lua export
doctor/audit/inspect
```

## Versioning

```text
generator        0.7.3.1
regional influence schema  0.7.3
structural grammar behavior 0.7.3.1
```

Influence field data format itself was not replaced.
