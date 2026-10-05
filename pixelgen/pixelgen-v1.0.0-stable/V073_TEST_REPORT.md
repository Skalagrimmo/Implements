# PixelGen v0.7.3 — Test Report

## Release gate

- combined historical regression suite through v0.7.3: **15 PASS**
- v0.7.3 fuzz: **240 worlds PASS**
- large-world stress: **20 worlds PASS**
  - 8×6
  - 10×8
- `influence-demo`: **PASS**
- `gameplay-check`: **PASS**
- `inspect`: **PASS**

## Mixed canonical demo: seed 7301 / 6×5

- sectors: **30**
- influence sources: **6**
- affected sectors: **30**
- dominant channels: **{'nano_signal': 11, 'print_civic': 6, 'silt_contamination': 13}**
- regions: **3**
- structural score: **100/100**
- visual score: **100/100**
- semantic fingerprint: `af6352af84e4ec44e16b180a9888b309017b1b8acadce79a2d08777dac01afa4`

Influence sources:

- `silt_spire` — `silt_contamination` — sector [3, 2] — radius 5
- `printing_press_altar` — `print_civic` — sector [0, 4] — radius 3
- `nanolith_shrine` — `nano_signal` — sector [1, 0] — radius 3
- `nanolith_shrine` — `nano_signal` — sector [5, 0] — radius 3
- `printing_press_altar` — `print_civic` — sector [5, 4] — radius 3
- `nanolith_shrine` — `nano_signal` — sector [2, 3] — radius 3

## Causal-profile unit checks

Verified independently:

```text
Silt Spire
→ source sector contamination > distant contamination
→ hazard multiplier > 1
→ encounter multiplier > 1

Printing Cathedral
→ print_civic > 0
→ prop multiplier > 1
```

## Determinism

Same seed / size / profile produces the same semantic fingerprint with influence data included.

## Development regression

The first influence integration also populated geography context in `geography=False` legacy mode. That broke the old reference path because it had influence context but no region identity.

Fix:

```text
regional influence application
→ geography-aware generation only

legacy geography=False
→ unchanged reference behavior
```
