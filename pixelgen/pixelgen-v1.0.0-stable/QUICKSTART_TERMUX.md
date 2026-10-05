# PixelGen 1.0 — Termux quickstart

```bash
pkg update
pkg install python
unzip pixelgen-v1.0.0-stable.zip
cd pixelgen-v1.0.0-stable
```

Semantic runtime needs no renderer:

```bash
python runtime_cli.py capabilities
python runtime_cli.py contract
python runtime_cli.py world --cols 6 --rows 5 --seed 7301 --out generated/world
python runtime_cli.py state-demo --cols 6 --rows 5 --seed 7301 --out generated/state_demo
```

Optional image rendering:

```bash
python -m pip install pillow
python render_cli.py world --world generated/world/gameplay_6x5_seed7301.json --out generated/world.png --quality fast
```

Run the stable gate:

```bash
python tests/test_v100.py
python tests/test_v093.py
python tests/fuzz_v093.py
```
