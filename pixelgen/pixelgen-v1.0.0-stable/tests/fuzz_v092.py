from copy import deepcopy
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.runtime_api import (
    load_runtime_profile, generate_semantic_world, initialize_state,
    apply_event, replay_events, ebe_runtime_bundle,
    validate_public_artifact, migrate_public_artifact, world_fingerprint,
)

profile=load_runtime_profile()
dims=[(1,1),(2,2),(4,3),(6,5),(8,6)]
cases=0
mutated=0
migrations=0
for seed in range(-6,6):
    for cols,rows in dims:
        world=generate_semantic_world(profile,seed,cols,rows,4)
        assert validate_public_artifact(world,"world")["status"]=="pass"
        fp=world_fingerprint(world)

        legacy=deepcopy(world)
        legacy["generator"]["version"]="0.9.1"
        legacy["schema_versions"]["runtime_api"]="0.9.1"
        legacy["schema_versions"].pop("contract_manifest",None)
        if isinstance(legacy.get("gameplay"),dict):
            legacy["gameplay"]["generator_version"]="0.9.1"
        migrated,report=migrate_public_artifact(legacy,"world")
        assert report["semantic_identity_preserved"]
        assert world_fingerprint(migrated)==fp
        migrations+=1

        state=initialize_state(world)
        fronts=sorted(state.get("fronts",{}))
        territories=sorted(state.get("territories",{}))
        if fronts:
            state=apply_event(world,state,{
                "event_type":"front_escalation",
                "target_id":fronts[0],
                "amount":0.13,
                "source":"fuzz_v092",
            })
            mutated+=1
        if territories and (seed+cols+rows)%3==0:
            state=apply_event(world,state,{
                "event_type":"territory_alert",
                "target_id":territories[-1],
                "amount":0.09,
                "source":"fuzz_v092",
            })
        assert replay_events(world,state["event_log"])==state
        assert validate_public_artifact(state,"world_state")["status"]=="pass"
        assert validate_public_artifact(state["event_log"],"runtime_events")["status"]=="pass"
        ebe=ebe_runtime_bundle(world,state)
        assert validate_public_artifact(ebe,"ebe_runtime")["status"]=="pass"
        cases+=1

print(f"PixelGen v0.9.3 contract-compat fuzz passed: {cases} worlds, {mutated} front-mutated, {migrations} metadata migrations")
