#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, sys, tempfile
from pathlib import Path


def parse_kv(text:str):
    out={}
    for line in text.splitlines():
        if "=" in line:
            k,v=line.strip().split("=",1)
            out[k]=v
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ebe-root",required=True)
    ap.add_argument("--pixelgen-root",required=True)
    args=ap.parse_args()
    ebe=Path(args.ebe_root).resolve(); px=Path(args.pixelgen_root).resolve()
    sys.path.insert(0,str(px))
    from pixelgen.runtime_api import load_runtime_profile, generate_semantic_world, initialize_state, apply_event, ebe_runtime_bundle, export_lua

    profile=load_runtime_profile()
    world=generate_semantic_world(profile,7301,6,5,4)
    state=initialize_state(world)
    fronts=sorted(state["fronts"])
    if not fronts:
        raise SystemExit("canonical PixelGen world has no front")
    # Create one real fact for EBE to observe.
    state=apply_event(world,state,{"id":"px_seed_event","event_type":"front_escalation","target_id":fronts[0],"amount":0.20,"source":"roundtrip_seed"})

    with tempfile.TemporaryDirectory(prefix="ebe_v100_roundtrip_") as td:
        td=Path(td)
        first=td/"first.lua"; feedback=td/"feedback.lua"; snap=td/"ebe_snapshot.lua"
        export_lua(ebe_runtime_bundle(world,state,since_revision=0),first)
        p1=subprocess.run(["texlua",str(ebe/"demo/action_roundtrip_phase1.lua"),str(ebe),str(first),str(snap)],capture_output=True,text=True,check=True)
        event=parse_kv(p1.stdout)
        request={
            "id":event["id"],"event_type":event["event_type"],"target_type":event["target_type"],
            "target_id":event["target_id"],"amount":float(event["amount"]),"source":event["source"],
            "actor_id":event["actor_id"],"cause_id":event["cause_id"],
        }
        before=state["clock"]["revision"]
        state=apply_event(world,state,request)
        after=state["clock"]["revision"]
        if after != before+1: raise AssertionError("PixelGen authority did not advance one revision")
        export_lua(ebe_runtime_bundle(world,state,since_revision=before),feedback)
        p2=subprocess.run(["texlua",str(ebe/"demo/action_roundtrip_phase2.lua"),str(ebe),str(snap),str(feedback)],capture_output=True,text=True,check=True)
        result=parse_kv(p2.stdout)
        if result.get("status")!="applied": raise AssertionError(result)
        print("EBE v1.0.0 <-> PixelGen 1.0 real action roundtrip: PASS")
        print(f"request={event['id']} {event['event_type']} {event['target_id']} amount={event['amount']}")
        print(f"pixelgen_revision={after} derived_event={result.get('derived_event_id')}")

if __name__=="__main__":
    main()
