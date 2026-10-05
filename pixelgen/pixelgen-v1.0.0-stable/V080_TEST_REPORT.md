# PixelGen v0.8.0 — Dynamic World State Test Report

## Release gate

- combined historical regression suite through 0.8.0: **15 PASS**
- dedicated dynamic-state fuzz: **160 worlds PASS**
- fuzz worlds with runtime mutations: **120**
- extended dynamic soak: **45 worlds**
- runtime events in extended soak: **293**
- extended soak hard failures: **0**
- long mutation bound tests: **PASS**
- static v0.7.5 → v0.8.0 semantic parity: **PASS**
- CLI `state-demo`: **PASS**
- CLI `state-check`: **PASS**
- CLI `state-replay`: **PASS**

## Canonical seed 7301 / 6×5

Static world fingerprint remains the v0.7.5 semantic fingerprint:

```text
d31eb68dca90c054286620be9b5d3327c499e379dc713387ccf9cbc6d975e9f5
```

Initial state:

```text
revision: 0
state fingerprint: 194791bce26e9852f9bf028baf37672e67440c5fd5493cc80f3edb9af287036d
```

Canonical state demo applies three events:

```text
front_escalation
territory_weaken
front_deescalation
```

Final state:

```text
revision: 3
runtime events: 3
mutations: 3
derived events: 3
local observations: 13
state fingerprint: 54386886d50abe4703cf528ee3fd4a4aef4cee350976fba18b33506b52bc0632
```

Replay equality:

```text
True
```

## Static semantic parity

Independent v0.7.5 and v0.8.0 generators produced identical semantic world fingerprints for:

```text
7301  6×5
6060  4×3
42    8×6
-777  1×1
```

This proves the 0.8.0 dynamic subsystem was added as an overlay rather than silently changing static world generation.

## Extended dynamic soak

```text
dimensions:
4×3
6×5
8×6

worlds: 45
mutated worlds: 45
runtime events: 293
hard failures: 0
mean local observations/event: 4.276
```

Every tested state passed:

```text
source-world fingerprint validation
state reference integrity
numeric bounds
event/mutation provenance
exact replay
state fingerprint equality
incremental EBE revision export
static-world immutability
static progression reachability
```

## Long mutation bounds

### 6×5

```text
events: 50
revision: 50
observations: 200
front sample status: volatile
territory sample status: pressured
```

### 12×12

```text
events: 30
revision: 30
territories: 7
observations: 120
territory sample status: pressured
```

No numeric range or replay failure occurred.

## Information-locality test

For every direct observation created in the dedicated tests:

```text
Manhattan distance from event origin <= 1
```

and each observation explicitly remained:

```text
knowledge_state = not_yet_assigned_to_any_agent
```

So 0.8.0 does not recreate global omniscience through the EBE bridge.

## Current limitation

Dynamic state is an overlay.

A territory can become:

```text
fragile
pressured
secure
```

and a front can become:

```text
quiet
active
tense
volatile
```

without immediately recomputing the static territory/front geometry.

That separation is intentional for 0.8.0. A later 0.8.x release can introduce controlled topology reflow once the mutation/replay contract is proven.
