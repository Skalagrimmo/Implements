# PixelGen 0.7.5 — Territory Graph / EBE Seed Contract

## Territory invariant

Every `dominated` topology sector belongs to exactly one territory.

Every territory is:

```text
4-neighbor connected
+
single alignment
```

Neutral and contested sectors do not belong to a dominated territory.

## Front-site invariant

Each existing influence front gets at most one representative front site.

The representative site is chosen from the highest-pressure front edge with deterministic coordinate tie-breaking.

## Event-seed invariant

For every front site PixelGen emits:

```text
front_observation
front_rumor
border_encounter
```

For every territory of at least two sectors:

```text
territory_presence
```

For every contested sector:

```text
contested_observation
```

Therefore:

```text
event_seed_count
=
3 × front_site_count
+ territories_with_2_or_more_sectors
+ contested_sector_count
```

## EBE ownership boundary

PixelGen event seeds mean:

```text
"this semantic situation exists and may become observable"
```

They do **not** mean:

```text
"every NPC already knows this"
```

The EBE runtime is responsible for:

```text
observation
transmission delay
memory
knowledge
belief
interpretation
distortion
rumor propagation
reaction
state mutation
```

## Locality

Every generated local scene receives:

```text
scene.geography.territory
├── territory_id
├── alignment
├── front_site_ids[]
└── event_seed_ids[]
```

so a runtime can query relevant local semantic hooks without scanning the full world graph.

## EBE bridge schema

```text
version
source
contract
entities[]
events[]
```

Entity types:

```text
territory
influence_front
```

Seed event state:

```text
state = seeded
observability = local_or_transmitted
```

## No runtime mutation

0.7.5 does not dynamically move fronts or rewrite territory control during play.

It establishes stable initial semantic entities and event hooks. Dynamic mutation belongs to the future PixelGen/EBE integration layer.
