#!/usr/bin/env python3
"""PixelGen renderer-free runtime CLI (v1.0.0 stable)."""
import argparse
import json
import sys
from pathlib import Path

from pixelgen.runtime_api import (
    RUNTIME_API_VERSION,
    CONTRACT_FREEZE_VERSION,
    load_runtime_profile,
    generate_semantic_world,
    initialize_state,
    apply_event,
    replay_events,
    ebe_runtime_bundle,
    contract,
    validate_public_artifact,
    migrate_public_artifact,
    write_public_bundle,
    verify_public_bundle,
    capabilities,
    export_lua,
    state_summary,
    world_fingerprint,
)
from pixelgen.serialization import to_plain
from pixelgen.atomic_io import atomic_write_json
from pixelgen.json_io import read_json, StrictJSONError
from pixelgen.migrations import MigrationError
from pixelgen.gameplay_export import (
    export_gameplay_json,
    export_gameplay_lua,
    export_progression_json,
    export_progression_dot,
)
from pixelgen.progression import simulate_progression
from pixelgen.world_state_integrity import validate_world_state

ROOT = Path(__file__).resolve().parent
ARTIFACT_TYPES = [
    "world",
    "world_state",
    "runtime_events",
    "ebe_runtime",
    "ebe_seed_bundle",
    "regional_corridors",
    "contract_manifest",
]


def profile(args):
    return load_runtime_profile(args.profile)


def _read_json(path):
    return read_json(path)


def _write_json(path, value):
    return atomic_write_json(Path(path), to_plain(value))


def cmd_capabilities(args):
    print(json.dumps(capabilities(), indent=2, sort_keys=True))


def cmd_contract(args):
    payload = contract()
    if args.out:
        _write_json(args.out, payload)
        print(f"Contract -> {args.out}")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))


def cmd_world(args):
    p = profile(args)
    world = generate_semantic_world(p, args.seed, args.cols, args.rows, args.ability_count)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base = out / f"gameplay_{args.cols}x{args.rows}_seed{args.seed}"
    export_gameplay_json(world, str(base) + ".json")
    export_gameplay_lua(world, str(base) + ".lua")
    export_progression_json(world, str(base) + ".progression.json")
    export_progression_dot(world, str(base) + ".progression.dot")
    print(f"Semantic world -> {base}.json")
    print(f"Fingerprint: {world_fingerprint(world)}")
    sim = simulate_progression(world)
    print(f"Progression: final={sim['final_sector_reachable']} all={sim['all_sectors_reachable']}")


def _state_events(initial, escalation, territory_delta):
    events=[]
    fronts=sorted(initial.get("fronts",{}))
    territories=sorted(initial.get("territories",{}))
    if fronts:
        events.append({"event_type":"front_escalation","target_id":fronts[0],"amount":escalation,"source":"runtime_cli"})
    if territories:
        events.append({"event_type":"territory_weaken","target_id":territories[0],"amount":territory_delta,"source":"runtime_cli"})
    if len(fronts)>1:
        events.append({"event_type":"front_deescalation","target_id":fronts[1],"amount":max(0.05, escalation*0.45),"source":"runtime_cli"})
    return events


def cmd_state_demo(args):
    p = profile(args)
    world = generate_semantic_world(p,args.seed,args.cols,args.rows,args.ability_count)
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    base=out/f"dynamic_state_{args.cols}x{args.rows}_seed{args.seed}"
    export_gameplay_json(world,str(base)+".world.json")
    initial=initialize_state(world)
    state=initial
    for event in _state_events(initial,args.escalation,args.territory_delta):
        state=apply_event(world,state,event)
    replayed=replay_events(world,state["event_log"])
    if replayed != state:
        raise RuntimeError("replay mismatch")
    for suffix,value in (("initial-state",initial),("after-state",state),("ebe-runtime",ebe_runtime_bundle(world,state))):
        _write_json(str(base)+f".{suffix}.json", value)
        export_lua(value,str(base)+f".{suffix}.lua")
    _write_json(str(base)+".events.json", state["event_log"])
    print(f"State demo -> {base}.after-state.json")
    print(f"Initial: {state_summary(initial)['fingerprint']}")
    print(f"Final:   {state_summary(state)['fingerprint']}")
    print("Replay deterministic: True")


def cmd_state_check(args):
    world=_read_json(args.world); world.pop("progression_simulation",None)
    state=_read_json(args.state)
    errors=validate_world_state(world,state)
    if errors: raise RuntimeError("world-state validation failed: "+"; ".join(errors[:20]))
    print("World-state validation: PASS")
    print(json.dumps(state_summary(state),indent=2,sort_keys=True))


def cmd_state_replay(args):
    world=_read_json(args.world); world.pop("progression_simulation",None)
    events=_read_json(args.events)
    state=replay_events(world,events)
    _write_json(args.out,state)
    print(f"Replayed state -> {args.out}")
    print(f"Fingerprint: {state_summary(state)['fingerprint']}")


def cmd_validate_artifact(args):
    value=_read_json(args.input)
    artifact_type=None if args.type=="auto" else args.type
    result=validate_public_artifact(value,artifact_type)
    print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
    if result["status"] != "pass":
        raise SystemExit(2)


def cmd_migrate_artifact(args):
    value=_read_json(args.input)
    artifact_type=None if args.type=="auto" else args.type
    migrated,report=migrate_public_artifact(value,artifact_type)
    _write_json(args.out,migrated)
    report_path=args.report or (str(args.out)+".migration.json")
    _write_json(report_path,report)
    print(f"Migrated artifact -> {args.out}")
    print(f"Migration report -> {report_path}")
    print(f"Mode: {report['mode']}")


def cmd_freeze_bundle(args):
    world=_read_json(args.world); world.pop("progression_simulation",None)
    state=_read_json(args.state) if args.state else None
    events=_read_json(args.events) if args.events else None
    ebe=_read_json(args.ebe_runtime) if args.ebe_runtime else None
    manifest_path,manifest=write_public_bundle(
        args.out,
        world=world,
        state=state,
        events=events,
        ebe_runtime=ebe,
    )
    print(f"Contract bundle -> {args.out}")
    print(f"Manifest -> {manifest_path}")
    print(f"Artifacts: {manifest['artifact_count']}")
    print(f"Contract: {manifest['manifest_version']} {manifest['contract_fingerprint']}")


def cmd_verify_bundle(args):
    result=verify_public_bundle(args.bundle)
    print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False))
    if result["status"] != "pass":
        raise SystemExit(2)


def cmd_benchmark(args):
    from time import perf_counter
    p=profile(args)
    rows=[]
    for _ in range(args.runs):
        t=perf_counter(); world=generate_semantic_world(p,args.seed,args.cols,args.rows,args.ability_count); dt=perf_counter()-t
        rows.append(dt)
    result={
        "runtime_api_version":RUNTIME_API_VERSION,
        "contract_version":CONTRACT_FREEZE_VERSION,
        "seed":args.seed,"dimensions":[args.cols,args.rows],"sectors":args.cols*args.rows,
        "runs":args.runs,"generation_seconds":rows,
        "mean_generation_seconds":sum(rows)/len(rows),
        "fingerprint":world_fingerprint(world),
    }
    print(json.dumps(result,indent=2,sort_keys=True))


def main():
    ap=argparse.ArgumentParser(description="PixelGen v1.0.0 stable renderer-free runtime / contract CLI")
    ap.add_argument("--profile")
    sub=ap.add_subparsers(dest="cmd",required=True)

    c=sub.add_parser("capabilities"); c.set_defaults(func=cmd_capabilities)
    ct=sub.add_parser("contract",help="Print the stable 1.0.0 public contract registry")
    ct.add_argument("--out"); ct.set_defaults(func=cmd_contract)

    w=sub.add_parser("world"); w.add_argument("--cols",type=int,default=6); w.add_argument("--rows",type=int,default=5); w.add_argument("--seed",type=int,default=7301); w.add_argument("--ability-count",type=int,default=4); w.add_argument("--out",default=str(ROOT/"generated"/"runtime_world")); w.set_defaults(func=cmd_world)
    s=sub.add_parser("state-demo"); s.add_argument("--cols",type=int,default=6); s.add_argument("--rows",type=int,default=5); s.add_argument("--seed",type=int,default=7301); s.add_argument("--ability-count",type=int,default=4); s.add_argument("--escalation",type=float,default=.20); s.add_argument("--territory-delta",type=float,default=.12); s.add_argument("--out",default=str(ROOT/"generated"/"runtime_state_demo")); s.set_defaults(func=cmd_state_demo)
    sc=sub.add_parser("state-check"); sc.add_argument("--world",required=True); sc.add_argument("--state",required=True); sc.set_defaults(func=cmd_state_check)
    sr=sub.add_parser("state-replay"); sr.add_argument("--world",required=True); sr.add_argument("--events",required=True); sr.add_argument("--out",required=True); sr.set_defaults(func=cmd_state_replay)

    va=sub.add_parser("validate-artifact",help="Validate a public artifact against the freeze-candidate contract")
    va.add_argument("--input",required=True); va.add_argument("--type",choices=["auto",*ARTIFACT_TYPES],default="auto"); va.set_defaults(func=cmd_validate_artifact)

    ma=sub.add_parser("migrate-artifact",help="Apply a conservative migration without inventing missing semantic systems")
    ma.add_argument("--input",required=True); ma.add_argument("--type",choices=["auto",*ARTIFACT_TYPES],default="auto"); ma.add_argument("--out",required=True); ma.add_argument("--report"); ma.set_defaults(func=cmd_migrate_artifact)

    fb=sub.add_parser("freeze-bundle",help="Write normalized artifact copies plus a transactional deterministic 1.0.0 contract manifest")
    fb.add_argument("--world",required=True); fb.add_argument("--state"); fb.add_argument("--events"); fb.add_argument("--ebe-runtime"); fb.add_argument("--out",required=True); fb.set_defaults(func=cmd_freeze_bundle)

    vb=sub.add_parser("verify-bundle",help="Verify hashes, contracts, fingerprints and cross-artifact relationships")
    vb.add_argument("--bundle",required=True); vb.set_defaults(func=cmd_verify_bundle)

    b=sub.add_parser("benchmark"); b.add_argument("--cols",type=int,default=12); b.add_argument("--rows",type=int,default=12); b.add_argument("--seed",type=int,default=7301); b.add_argument("--ability-count",type=int,default=4); b.add_argument("--runs",type=int,default=3); b.set_defaults(func=cmd_benchmark)
    args=ap.parse_args()
    try:
        args.func(args)
    except (StrictJSONError, MigrationError, ValueError, RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)

if __name__=="__main__": main()
