# PixelGen 0.7.3 — Regional Influence Fields

## Principle

A major landmark should change the world around it.

```text
landmark
≠
map decoration

landmark
=
regional cause
```

## Field source schema

```text
id
kind
scope
sector
channel
radius
strength
```

## Sector influence schema

```text
channels
├── print_civic
├── silt_contamination
└── nano_signal

dominant_channel

contributions[]
├── source_id
├── kind
├── channel
├── distance
└── weight

modifier_mults
├── hazard_mult
├── prop_mult
└── encounter_mult
```

## Integration point

Influence is applied before scene generation:

```text
geography modifiers
×
regional influence modifiers
↓
final local generation modifiers
↓
hazards / props / encounters
```

This is deliberately before encounter/prop generation so the field is causal rather than descriptive.

## Example

```text
Silt Spire
sector [3,2]

distance 0
→ strong contamination

distance 1
→ lower contamination

distance 2
→ lower again
...
```

Overlapping Nano Shrine and Printing Press fields can change which channel is dominant without deleting the weaker contributions.

## Invariants

1. Every influence source must correspond to a known field-producing landmark.
2. Every sector has finite non-negative channel values.
3. Every contribution references a known source.
4. Local scene influence metadata must agree with world influence metadata.
5. Field generation is deterministic.
6. Influence must not break navigation/progression.
7. Legacy no-geography generation remains usable for regression/reference work.
