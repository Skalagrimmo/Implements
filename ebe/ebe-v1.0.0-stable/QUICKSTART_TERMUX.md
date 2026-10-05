# EBE v1.0.0 — Termux quickstart

Core tests do not require LÖVE. Install a Lua 5.3+ runtime (for example the Termux `lua53`/available Lua package) and run from the project root.

```bash
lua tests/run_all.lua .
lua tests/fuzz_v090.lua .
lua tests/fuzz_json_v090.lua .
lua tests/fuzz_v100.lua .
lua tests/soak_v100.lua .
```

Stable persistence from Lua:

```lua
local EBE=require("ebe")
local rt=EBE.Runtime.new({seed=7301})
-- ...
EBE.Snapshot.write_runtime_json_atomic("save.json",rt:snapshot())
local snap=EBE.Snapshot.read_runtime_json("save.json")
local restored=EBE.Runtime.restore(snap)
```

Verifier:

```bash
lua tools/verify_snapshot.lua . save.json json
```

---

# EBE v0.7.0 — Termux quickstart

Install Lua and Python:

```bash
pkg update
pkg install lua54 python
```

Unpack:

```bash
unzip ebe-v0.7.0-collective-epistemics.zip
cd ebe-v0.7.0-collective-epistemics
```

Run the collective demo:

```bash
lua demo/collective_epistemics_demo.lua .
```

Run the auto-network demo:

```bash
lua demo/network_synthesis_demo.lua .
```

Generate a network view from a PixelGen 1.0 world JSON:

```bash
python tools/pixelgen_world_json_to_lua.py \
  /path/to/dynamic_state_6x5_seed7301.world.json \
  generated/my_world_network.lua

lua tools/synthesize_network.lua \
  generated/my_world_network.lua \
  generated/my_network_plan
```

Core regression:

```bash
lua tests/smoke.lua
lua tests/hardening.lua
lua tests/renderer_forwarding.lua
lua tests/run_all.lua .
```

Fuzz / soak:

```bash
lua tests/fuzz_v030.lua .
lua tests/fuzz_v040.lua .
lua tests/fuzz_v050.lua .
lua tests/fuzz_v060.lua .
lua tests/soak_v060.lua .
```

Core `ebe/` remains pure Lua and does not depend on LÖVE2D.

Python is only required for the optional PixelGen JSON → compact Lua network converter.


Institutional policy demo:

```bash
texlua demo/institutional_policy_demo.lua .
```

Policy regression:

```bash
texlua tests/test_institutional_policy.lua .
texlua tests/fuzz_v070.lua .
texlua tests/soak_v070.lua .
```


## v0.8 action-request demo

```bash
texlua demo/action_request_demo.lua .
```

Real PixelGen 1.0 roundtrip (when both source trees are present):

```bash
python tools/pixelgen_action_roundtrip.py --ebe-root . --pixelgen-root ../pixelgen-v1.0.0-stable
```
