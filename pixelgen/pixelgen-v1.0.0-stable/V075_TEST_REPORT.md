# PixelGen v0.7.5 — Territory Graph / Event Seed Test Report

## Release gate

- combined regression suite: **15 PASS**
- dedicated territory fuzz: **200 worlds PASS**
- 60-world 6×5 territory distribution: **0 hard failures**
- 12×12 territory stress: **4/4 PASS**
- `territory-demo`: **PASS**
- `gameplay-check`: **PASS**
- `inspect`: **PASS**
- deterministic EBE seed export: **PASS**

## Canonical seed 7301 / 6×5

```text
territories: 6
front sites: 5
event seeds: 24
EBE entities: 11
EBE events: 24
```

Territory alignment count:

```json
{
  "nano_signal": 3,
  "print_civic": 2,
  "silt_contamination": 1
}
```

Event kinds:

```json
{
  "border_encounter": 5,
  "contested_observation": 3,
  "front_observation": 5,
  "front_rumor": 5,
  "territory_presence": 6
}
```

Semantic fingerprint:

```text
d31eb68dca90c054286620be9b5d3327c499e379dc713387ccf9cbc6d975e9f5
```

## 60-world 6×5 distribution

```text
territories/world
  mean 3.633
  median 4.0
  range 1…6

front sites/world
  mean 3.35
  median 4.0
  range 0…7

event seeds/world
  mean 16.05
  median 18.0
  range 1…31
```

Territories observed across 60 worlds:

```json
{
  "nano_signal": 88,
  "print_civic": 96,
  "silt_contamination": 34
}
```

Event hooks observed across 60 worlds:

```json
{
  "border_encounter": 201,
  "contested_observation": 161,
  "front_observation": 201,
  "front_rumor": 201,
  "territory_presence": 199
}
```

## 12×12 scale behavior

### seed 0

```text
territories: 6
front sites: 0
event seeds: 6
generation: 0.643 s
fingerprint: 1d3107164e5733a269dfa495b2d573e6e1d382ce485f99bac2fb0c280a65a4f9
```

### seed 1

```text
territories: 7
front sites: 0
event seeds: 7
generation: 0.655 s
fingerprint: a5201b2a58a50b4c9a50fe79261a70e10b4912deb713ec2dc5e68b0da4ee6a46
```

### seed 6060

```text
territories: 7
front sites: 0
event seeds: 7
generation: 0.637 s
fingerprint: 8603e6b07c406e4ad948b1b829e42a4060ae7178642cd2272fbd8f4d9ec3020a
```

### seed 7301

```text
territories: 7
front sites: 0
event seeds: 7
generation: 0.662 s
fingerprint: 29b7e113e0d1cd9dd03aceccd00adc009402a6dcbf1ee6db9b8980593ae5891e
```

On the tested 12×12 worlds, influence islands are separated by neutral background, so there are no active cross-alignment fronts. The territory graph still produces persistent isolated control islands and `territory_presence` event seeds.

## EBE bridge contract

The canonical bundle contains:

```text
entities = territories + influence fronts
events = deterministic semantic event seeds
```

Every bridge event starts as:

```text
state = seeded
observability = local_or_transmitted
```

PixelGen does not assign those events to NPC knowledge or memory. That remains the EBE runtime's responsibility.

## Integrity result

Validated properties include:

1. dominated sectors are partitioned exactly once;
2. every territory contains one alignment only;
3. territory membership is connected by construction;
4. front sites reference real fronts and adjacent sectors;
5. event IDs are unique;
6. event references resolve to real fronts/territories;
7. local scene territory context matches the world graph;
8. same seed gives the same graph, EBE seed bundle and semantic fingerprint;
9. progression remains fully reachable.
