# PixelGen v0.7.2 — Test Report

## Release gate

- combined historical regression suite through v0.7.2: **15 PASS**
- v0.7.2 fuzz: **300 worlds PASS**
- large-world stress: **40 worlds PASS**
  - 8×6
  - 10×8
- `doctor`: **PASS**
- `gameplay-check`: **PASS**
- `structural-check`: **PASS**
- `inspect`: **PASS**

## Canonical 6×5 seed 7000

- sectors: **30**
- regions: **3**
- parent structural grammars: **3**
- distinct subbiome structural variants: **16**
- ecotone adapters: **22**
- structural score: **100/100**
- visual score: **100/100**
- semantic fingerprint: `c6ddf5e71be816165ab38841f70cd7836905e982c347760a531957b4665c8f16`

## Canonical structural summary

```text
status: PASS
score: 100/100
distinct variants: 16
ecotone adapters: 22
```

## Development regressions caught

### Old morphology ceiling vs intentional ecotones

The first 0.7.2 run caused Frozen Pass to exceed the old 0.7.1 junction/loop ceiling.

Generation was valid; the analyzer was wrong because it treated deliberate boundary connectors as accidental branching.

Fix:

```text
old fixed ceiling
↓
ecotone-aware allowance
+
operator-aware allowance
```

The analyzer now accounts only for structural complexity intentionally introduced by known variant operators and ecotone adapters.

### Standalone Lua `nil`

Standalone scenes have no subbiome/zone.

An early 0.7.2 variant record included explicit null values, which serialized to Lua `nil`.

Fix:

```text
optional absent field
→ omitted
```

The historical nil-free Lua contract remains intact.

## Dark Forest subbiome demo

The bundled atlas includes:

- `core/redwood_core` — J33 E6 T10 L20 adapters=0
- `core/root_maze` — J14 E6 T11 L6 adapters=0
- `mid/moss_grove` — J13 E3 T15 L7 adapters=0
- `mid/wet_pine` — J16 E6 T12 L6 adapters=0
- `margin/forest_edge` — J8 E5 T14 L3 adapters=0
- `margin/scrub_march` — J33 E4 T10 L17 adapters=0
- `margin/frostwood_edge` — J9 E4 T16 L4 adapters=1
