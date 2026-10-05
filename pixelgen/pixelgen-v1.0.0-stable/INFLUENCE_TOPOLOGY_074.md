# PixelGen 0.7.4 — Influence Topology Contract

## Purpose

Convert continuous landmark influence values into a discrete regional semantic layer without changing the underlying causal field mathematics.

## Classification

```text
NEUTRAL_THRESHOLD       = 0.28
CONTEST_MIN_SECONDARY   = 0.12
CONTEST_MARGIN          = 0.12
```

Given ranked channel values:

```text
top
second
```

### neutral

```text
top < 0.28
```

### contested

```text
top >= 0.28
second >= 0.12
top - second <= 0.12
```

### dominated

Everything else with a meaningful top channel.

## Important semantic distinction

```text
neutral != zero raw influence
```

A neutral sector may retain weak field modifiers.

Neutral means:

```text
below map-semantic salience threshold
```

not:

```text
physics disabled
```

This avoids discontinuous causal jumps at an arbitrary map classification boundary.

## Alignment

```text
neutral
→ alignment = None

dominated
→ alignment = top channel

contested
→ alignment = current top channel
  + contest_pair records the top two
```

A contested sector therefore still has a current leaning while explicitly remembering its near-tie.

## Front graph

For each east/south 4-neighbor pair:

```text
alignment A != alignment B
AND
A non-neutral
AND
B non-neutral
↓
boundary edge
```

Edges are grouped by:

```text
unordered channel pair
+
topological connectivity
```

into fronts.

## Pressure

For pair `(P0, P1)` across edge `(A, B)`:

```text
pressure =
min(
    max(A.P0, B.P0),
    max(A.P1, B.P1)
)
```

This approximates how strongly both opposing channels are represented at that boundary.

## Invariants

1. Every world sector has exactly one topology classification.
2. Topology classification is reproducible from raw channel values.
3. Scene-local topology equals world topology.
4. Every front edge connects orthogonally adjacent sectors.
5. Front edge endpoints have different non-neutral alignments.
6. Every front uses exactly one unordered channel pair.
7. Front IDs are unique.
8. Same seed/profile/dimensions gives the same semantic topology and fingerprint.
9. Topology does not break progression.
10. Raw 0.7.3 influence values remain available unchanged.

## Intended future consumers

The front graph is deliberately generic enough for:

```text
EBE observations/events
faction control
rumor propagation
regional encounter tables
dynamic world-state updates
quests
NPC belief/knowledge systems
```
