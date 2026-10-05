# PixelGen v0.5 Hardened — Test Report

**Package:** PixelGen v0.5 Hardened / patch 0.5.1

## PASS summary

- Python syntax compilation: PASS
- v0.2 regression tests: PASS
- v0.3 regression tests: PASS
- v0.4 regression tests: PASS
- v0.5 regression tests: PASS
- hardening pytest suite: PASS
- total pytest result: **15 passed**
- scene fuzz cases: **11,000 PASS**
- world fuzz cases: **707 PASS**
- legacy scene fuzz: included / PASS
- maximum 12×12 world generation: PASS
- maximum 12×12 world render: PASS
- spawn safety: PASS
- object footprint collision: PASS
- hollow/entity non-overlap: PASS
- reciprocal sector links: PASS
- linked-exit reachability: PASS
- JSON scene export completeness: PASS
- Lua scene export completeness: PASS
- Tiled-like collision/entity layers: PASS
- JSON world export completeness: PASS
- Lua world export completeness: PASS
- deterministic PNG/JSON/Lua output: PASS
- atlas repeated-generation idempotency: PASS
- preview repeated-generation idempotency: PASS
- invalid CLI values rejected: PASS
- invalid direct API parameters rejected: PASS

## Reproduce

With Pillow installed:

```bash
python tests/cli_smoke.py
python tests/fuzz_hardening.py
```

For the full pytest suite:

```bash
python -m pip install -r requirements-dev.txt
pytest -q tests/test_v02.py tests/test_v03.py tests/test_v04.py tests/test_v05.py tests/test_hardening.py
```

## Environment used for this report

- Python 3.13.5
- Pillow 12.3.0
- x86_64 build environment

Lua/LuaJIT was not installed in the build environment; generated Lua was therefore not executed by a separate Lua interpreter.
