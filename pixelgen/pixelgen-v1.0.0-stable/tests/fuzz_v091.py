from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.runtime_api import (
    load_runtime_profile, generate_semantic_world, initialize_state,
    apply_event, replay_events, world_fingerprint,
)
from pixelgen.gameplay_integrity import validate_gameplay_integrity

profile=load_runtime_profile()
dims=[(1,1),(2,2),(4,3),(6,5),(8,6)]
cases=0
mutated=0
for seed in range(-4,4):
    for cols,rows in dims:
        w=generate_semantic_world(profile,seed,cols,rows,4)
        assert validate_gameplay_integrity(w)==[]
        fp=world_fingerprint(w)
        w2=generate_semantic_world(profile,seed,cols,rows,4)
        assert world_fingerprint(w2)==fp
        s=initialize_state(w)
        fronts=sorted(s.get('fronts',{}))
        if fronts:
            s=apply_event(w,s,{
                'event_type':'front_escalation',
                'target_id':fronts[0],
                'amount':0.11,
                'source':'fuzz_v091',
            })
            assert replay_events(w,s['event_log'])==s
            mutated+=1
        cases+=1
print(f'PixelGen v0.9.1 renderer-free runtime fuzz passed: {cases} worlds, {mutated} mutated')
