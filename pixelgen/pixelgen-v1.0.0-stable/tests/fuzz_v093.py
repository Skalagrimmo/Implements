from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.runtime_api import (
    load_runtime_profile, generate_semantic_world, initialize_state, apply_event,
    replay_events, ebe_runtime_bundle, validate_public_artifact,
    migrate_public_artifact, write_public_bundle, verify_public_bundle,
    world_fingerprint,
)
from pixelgen.world_state import state_fingerprint, apply_world_event
from pixelgen.json_io import strict_json_loads
from pixelgen.serialization import to_plain

profile=load_runtime_profile()
dims=[(1,1),(2,2),(4,3),(6,5),(8,6)]
worlds=0
events_applied=0
bundles=0
migrations=0
hostile_rejections=0
incremental_checks=0

for seed in range(-4,4):
    for cols,rows in dims:
        world=generate_semantic_world(profile,seed,cols,rows,4)
        fp=world_fingerprint(world)
        assert validate_public_artifact(world,"world")["status"]=="pass"

        # Same-process determinism and strict JSON round-trip.
        world2=generate_semantic_world(profile,seed,cols,rows,4)
        assert world_fingerprint(world2)==fp
        plain=json.loads(json.dumps(to_plain(world),ensure_ascii=False,sort_keys=True,allow_nan=False))
        strict=strict_json_loads(json.dumps(plain,ensure_ascii=False,sort_keys=True,allow_nan=False))
        assert world_fingerprint(strict)==fp

        # Simulated previous-release metadata migration preserves unknown additive fields.
        legacy=deepcopy(world)
        legacy["generator"]["version"]="0.9.2"
        legacy["schema_versions"]["runtime_api"]="0.9.2"
        legacy["schema_versions"]["contract_manifest"]="0.9.2"
        legacy["schema_versions"].pop("contract_manifest",None)
        legacy["x_future_additive"]={"seed":seed,"dims":[cols,rows]}
        if isinstance(legacy.get("gameplay"),dict): legacy["gameplay"]["generator_version"]="0.9.2"
        legacy_fp=world_fingerprint(legacy)
        migrated,report=migrate_public_artifact(legacy,"world")
        assert report["semantic_identity_preserved"]
        assert world_fingerprint(migrated)==legacy_fp
        assert migrated["x_future_additive"]==legacy["x_future_additive"]
        migrations+=1

        # Hostile structural variants must reject cleanly.
        corrupt=deepcopy(world); corrupt["seed"]=False
        assert validate_public_artifact(corrupt,"world")["status"]=="fail"; hostile_rejections+=1
        corrupt=deepcopy(world); corrupt["sectors"][0]["sx"]=cols+5
        assert validate_public_artifact(corrupt,"world")["status"]=="fail"; hostile_rejections+=1

        state=initialize_state(world)
        fronts=sorted(state.get("fronts",{}))
        territories=sorted(state.get("territories",{}))
        sequence=[]
        if fronts:
            sequence.extend([
                {"event_type":"front_escalation","target_id":fronts[0],"amount":0.17,"source":"fuzz_v093"},
                {"event_type":"front_deescalation","target_id":fronts[0],"amount":0.06,"source":"fuzz_v093"},
            ])
        if len(fronts)>1:
            sequence.append({"event_type":"front_escalation","target_id":fronts[-1],"amount":0.09,"source":"fuzz_v093"})
        if territories:
            sequence.extend([
                {"event_type":"territory_alert","target_id":territories[0],"amount":0.11,"source":"fuzz_v093"},
                {"event_type":"territory_weaken","target_id":territories[0],"amount":0.08,"source":"fuzz_v093"},
                {"event_type":"territory_strengthen","target_id":territories[0],"amount":0.05,"source":"fuzz_v093"},
            ])
        if len(territories)>1:
            sequence.append({"event_type":"territory_weaken","target_id":territories[-1],"amount":0.07,"source":"fuzz_v093"})

        # Repeat a bounded subsequence for longer state histories.
        if sequence and (seed+cols+rows)%2==0:
            sequence += deepcopy(sequence[:min(3,len(sequence))])

        for event in sequence:
            state=apply_world_event(world,state,event,source_fingerprint=fp)
            events_applied+=1
        assert world_fingerprint(world)==fp
        assert validate_public_artifact(state,"world_state")["status"]=="pass"
        assert validate_public_artifact(state["event_log"],"runtime_events")["status"]=="pass"

        replayed=replay_events(world,state["event_log"])
        assert replayed==state
        assert state_fingerprint(replayed)==state_fingerprint(state)

        ebe=ebe_runtime_bundle(world,state)
        assert validate_public_artifact(ebe,"ebe_runtime")["status"]=="pass"
        if state["clock"]["revision"]>0:
            inc=ebe_runtime_bundle(world,state,since_revision=state["clock"]["revision"]-1)
            assert len(inc["events"])==1
            assert all(o.get("revision")==state["clock"]["revision"] for o in inc["observations"])
            incremental_checks+=1

            bad_event=deepcopy(state["event_log"])
            bad_event[-1]["amount"]=True
            assert validate_public_artifact(bad_event,"runtime_events")["status"]=="fail"
            hostile_rejections+=1

        # Transactional frozen bundle sampling across the fuzz matrix.
        if worlds % 4 == 0:
            with tempfile.TemporaryDirectory() as td:
                write_public_bundle(td,world=world,state=state,events=state["event_log"],ebe_runtime=ebe)
                result=verify_public_bundle(td)
                assert result["status"]=="pass",result
                bundles+=1

        worlds+=1

print(
    f"PixelGen v0.9.3 torture fuzz passed: {worlds} worlds, {events_applied} runtime events, "
    f"{migrations} migrations, {bundles} verified bundles, {hostile_rejections} hostile rejects, "
    f"{incremental_checks} incremental EBE checks"
)
