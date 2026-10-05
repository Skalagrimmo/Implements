# PixelGen v0.6 Test Report

## Release gate

- v0.5 Hardened regression + v0.6 pytest suite: **15 PASS**
- Legacy v0.2 regression: **PASS**
- Legacy v0.3 regression: **PASS**
- Legacy v0.4 regression: **PASS**
- Legacy v0.5 regression: **PASS**
- v0.6 fuzz matrix: **400 gameplay worlds PASS**
- Maximum supported topology: **12×12 / 144 sectors PASS**
- Deterministic PNG/JSON/Lua/progression exports: **PASS**
- Public `gameplay-check`: **PASS**

## Canonical 4×3 demo

- Requested traversal abilities: **4**
- Effective traversal abilities: **4**
- Main-path nodes: **11**
- Progression gates: **4**
- Secret shortcuts: **6**
- Local traversal secrets: **4**
- Final sector reachable: **True**
- All sectors reachable after progression: **True**

## Anti-softlock invariant

Each traversal ability pickup must be reachable without already possessing that same ability.

The validator additionally checks reciprocal gameplay metadata, valid ability IDs, walkable pickup/secret cells, final-sector reachability, full-world reachability after progression, and shortcut requirements that do not bypass an earlier progression stage.

## Fuzz modes

Termux-friendly default:

```bash
python tests/fuzz_v06.py
```

Extended desktop matrix:

```bash
python tests/fuzz_v06.py --extended
```
