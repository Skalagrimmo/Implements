from pathlib import Path
import json
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.runtime_api import (
    capabilities, generate_semantic_world, initialize_state, apply_event,
    replay_events, ebe_runtime_bundle, world_fingerprint,
)
from pixelgen.render_api import renderer_status, render_world_preview
from pixelgen.world_render import render_world

profile=load_profile(ROOT/'profiles'/'techno_animist_gothic.json')
world=generate_semantic_world(profile,7301,6,5,4)
assert world['generator']['version'] in ('0.9.1','0.9.2','0.9.3','1.0.0')
assert world['schema_versions']['regional_corridors']=='0.9.0'
assert world['schema_versions']['runtime_api'] in ('0.9.1','0.9.2','0.9.3','1.0.0')
assert world['schema_versions']['render_api']=='0.9.1'
assert capabilities()['renderer_required'] is False

# Runtime API must preserve deterministic semantics.
world2=generate_semantic_world(profile,7301,6,5,4)
assert world_fingerprint(world)==world_fingerprint(world2)

# Dynamic state remains exact/replayable through the renderer-free facade.
state=initialize_state(world)
fronts=sorted(state.get('fronts',{}))
if fronts:
    state=apply_event(world,state,{
        'event_type':'front_escalation','target_id':fronts[0],
        'amount':0.2,'source':'test_v091',
    })
replayed=replay_events(world,state['event_log'])
assert replayed==state
bundle=ebe_runtime_bundle(world,state)
assert bundle['contract']['global_knowledge']=='forbidden'
assert isinstance(bundle['observations'],list)

# Runtime import/generation must work when PIL imports are explicitly forbidden.
probe=r'''
import sys, importlib.abc
for _k in list(sys.modules):
    if _k == "PIL" or _k.startswith("PIL."):
        del sys.modules[_k]
class BlockPIL(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "PIL" or fullname.startswith("PIL."):
            raise ImportError("PIL blocked for renderer-free runtime test")
        return None
sys.meta_path.insert(0, BlockPIL())
sys.path.insert(0, %r)
from pixelgen.runtime_api import load_runtime_profile, generate_semantic_world, world_fingerprint
p=load_runtime_profile()
w=generate_semantic_world(p,7301,4,3,4)
assert not any(k == "PIL" or k.startswith("PIL.") for k in sys.modules)
print(world_fingerprint(w))
''' % str(ROOT)
p=subprocess.run([sys.executable,'-c',probe],capture_output=True,text=True,timeout=30)
assert p.returncode==0, p.stderr
assert len(p.stdout.strip())==64

# The dedicated runtime CLI must also import while Pillow is blocked.
cli_probe = (
    probe.split('from pixelgen.runtime_api', 1)[0]
    + 'import runtime_cli\n'
    + 'print(\"runtime-cli-import-ok\")\n'
)
p2=subprocess.run([sys.executable,'-c',cli_probe],capture_output=True,text=True,timeout=30)
assert p2.returncode==0, p2.stderr
assert p2.stdout.strip()=='runtime-cli-import-ok'

# Exact and pooled-preview rendering must have identical canvas geometry, and
# the optimized path must actually reduce work on the canonical 6x5 world.
assert renderer_status()['available'] is True
t=time.perf_counter(); exact=render_world(world,profile,gap=4,quality='exact'); exact_s=time.perf_counter()-t
t=time.perf_counter(); fast=render_world(world,profile,gap=4,quality='fast'); fast_s=time.perf_counter()-t
assert exact.size==fast.size
assert fast_s < exact_s, (exact_s,fast_s)

# Fast preview is deterministic at the PNG byte level for the same world.
fast2=render_world_preview(world,profile,gap=4,quality='fast')
assert fast.tobytes()==fast2.tobytes()

print(
    'PixelGen runtime/renderer separation compatibility tests passed: '
    f'exact={exact_s:.4f}s fast={fast_s:.4f}s'
)
