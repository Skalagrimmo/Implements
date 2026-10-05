# PixelGen v0.7.4 — Influence Topology Test Report

## Release gate

- combined regression suite: **15 PASS**
- dedicated topology fuzz: **200 worlds PASS**
- 60-world 6×5 topology distribution: **0 hard failures**
- 12×12 topology stress: **4/4 PASS**
- `topology-demo`: **PASS**
- `gameplay-check`: **PASS**
- `inspect`: **PASS**
- `world-diff` self comparison: **PASS**

## Canonical seed 7301 / 6×5

```text
raw affected sectors: 30/30

neutral:    2
contested:  3
dominated: 25

fronts: 5
boundary edges: 19
```

Semantic fingerprint:

```text
e53c4056a48398a5c8b5391cd73ccceb6331bbd638f4ddfe31b2efd1bb9ce0de
```

## 60-world 6×5 distribution

All sampled raw 0.7.3 fields still mathematically affected:

```text
30/30 sectors on average
```

After topology classification:

```text
neutral:
  mean 1.7
  median 2.0
  range 0…4

contested:
  mean 2.683
  median 3.0
  range 0…6

dominated:
  mean 25.617
  median 25.0
  range 20…30

fronts/world:
  mean 3.35
  median 4.0
  range 0…7
```

Front pair components observed across 60 worlds:

```json
{
  "nano_signal + silt_contamination": 59,
  "print_civic + silt_contamination": 76,
  "nano_signal + print_civic": 66
}
```

## 12×12 scale behavior

### seed 0

```text
neutral/dominated/contested: {'dominated': 38, 'neutral': 106}
fronts: 0
boundary edges: 0
generation: 1.063 s
fingerprint: 8642cccd3e3d74ead09b30b9da695cce776df3fc0719ddbc89d6e58d83cd4026
```

### seed 1

```text
neutral/dominated/contested: {'dominated': 36, 'neutral': 108}
fronts: 0
boundary edges: 0
generation: 1.213 s
fingerprint: 940444f7534716c0f3522d00eccfa4406a67ebf11c450957c9901e3b80fc08cb
```

### seed 6060

```text
neutral/dominated/contested: {'dominated': 35, 'neutral': 109}
fronts: 0
boundary edges: 0
generation: 2.168 s
fingerprint: ca56c023e6dc785ba687295882ba58b6fec87984bafba7d52332fc20b7fa7c00
```

### seed 7301

```text
neutral/dominated/contested: {'dominated': 36, 'neutral': 108}
fronts: 0
boundary edges: 0
generation: 1.218 s
fingerprint: 61e38d96b59f93229355d98fdeb393bdbbfeb91196a4d2b5b4b49dfa8367cd0d
```

At 12×12 the tested landmark fields usually do not touch one another strongly enough to form fronts.

This is not a failure. It demonstrates the intended scale dependence:

```text
fixed landmark radius
+
larger world
=
separate influence islands
+
broad neutral background
```

## Design result

0.7.4 resolves the semantic ambiguity found during 0.7.3.1 testing:

```text
"affected by some weak field"
```

is no longer equivalent to:

```text
"meaningfully controlled by that field"
```

The raw causal layer remains continuous, while topology provides the discrete layer needed by future gameplay/event systems.
