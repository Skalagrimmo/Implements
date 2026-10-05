from copy import deepcopy
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.runtime_api import (
    load_runtime_profile, generate_semantic_world, initialize_state,
    replay_events, ebe_runtime_bundle, validate_public_artifact,
    write_public_bundle, verify_public_bundle, world_fingerprint,
)
from pixelgen.world_state import apply_world_event, state_fingerprint
from pixelgen.world_state_integrity import validate_world_state

profile=load_runtime_profile()
PROGRESS=Path("/tmp/v093_progress.txt")
PROGRESS.write_text("start\n")
def mark(x):
    with PROGRESS.open("a") as f: f.write(x+"\n")


# ---------------------------------------------------------------------------
# 1. Validator hostile/random JSON corpus: public validators must never crash.
# ---------------------------------------------------------------------------
rng=random.Random(930001)

def random_json(depth=0):
    scalars=[None,True,False,0,1,-1,10**50,0.0,1.5,-2.5,"", "x", "\u2603", "0"*64]
    if depth>=3 or rng.random()<0.55:
        return deepcopy(rng.choice(scalars))
    if rng.random()<0.5:
        return [random_json(depth+1) for _ in range(rng.randrange(0,5))]
    out={}
    for _ in range(rng.randrange(0,5)):
        out[rng.choice(["id","event_type","target_id","version","x","source_world","clock",str(rng.randrange(10))])]=random_json(depth+1)
    return out

validator_cases=0
for _ in range(1000):
    value=random_json()
    for kind in ("world","world_state","runtime_events","ebe_runtime","ebe_seed_bundle","regional_corridors","contract_manifest"):
        result=validate_public_artifact(value,kind)
        assert isinstance(result,dict)
        assert result.get("status") in ("pass","fail")
        validator_cases+=1

mark("phase1_done")
# ---------------------------------------------------------------------------
# 2. Fresh-process determinism: world + dynamic state fingerprints.
# ---------------------------------------------------------------------------
helper=r'''
import sys
from pathlib import Path
root=Path(sys.argv[1]); seed=int(sys.argv[2]); cols=int(sys.argv[3]); rows=int(sys.argv[4])
sys.path.insert(0,str(root))
from pixelgen.runtime_api import load_runtime_profile, generate_semantic_world, initialize_state, world_fingerprint
from pixelgen.world_state import apply_world_event, state_fingerprint
p=load_runtime_profile(); w=generate_semantic_world(p,seed,cols,rows,4); fp=world_fingerprint(w); s=initialize_state(w)
fronts=sorted(s.get("fronts",{})); territories=sorted(s.get("territories",{}))
events=[]
if fronts: events += [{"event_type":"front_escalation","target_id":fronts[0],"amount":.17,"source":"crossproc"},{"event_type":"front_deescalation","target_id":fronts[0],"amount":.06,"source":"crossproc"}]
if territories: events += [{"event_type":"territory_alert","target_id":territories[0],"amount":.11,"source":"crossproc"},{"event_type":"territory_weaken","target_id":territories[0],"amount":.08,"source":"crossproc"}]
for e in events: s=apply_world_event(w,s,e,source_fingerprint=fp)
print(fp)
print(state_fingerprint(s))
'''
cross_process={}
for seed,cols,rows in ((7301,6,5),(0,12,12),(6060,12,12),(7301,12,12)):
    outputs=[]
    for _ in range(3):
        p=subprocess.run([sys.executable,"-c",helper,str(ROOT),str(seed),str(cols),str(rows)],capture_output=True,text=True,timeout=90)
        assert p.returncode==0,p.stderr
        outputs.append(tuple(p.stdout.strip().splitlines()))
    assert len(set(outputs))==1,(seed,outputs)
    cross_process[f"{seed}:{cols}x{rows}"]=outputs[0]

mark("phase2_done")
# ---------------------------------------------------------------------------
# 3. 12x12 stress matrix with substantial mutation histories and replay.
# ---------------------------------------------------------------------------
stress=[]
for seed in (-17,-1,0,1,2,7,42,99,6060,7000,7301,9999):
    t0=time.perf_counter()
    w=generate_semantic_world(profile,seed,12,12,4)
    generation=time.perf_counter()-t0
    fp=world_fingerprint(w)
    s=initialize_state(w)
    fronts=sorted(s.get("fronts",{})); territories=sorted(s.get("territories",{}))
    base=[]
    if fronts:
        base.extend([
            {"event_type":"front_escalation","target_id":fronts[0],"amount":.21,"source":"torture12"},
            {"event_type":"front_deescalation","target_id":fronts[0],"amount":.14,"source":"torture12"},
        ])
    if territories:
        base.extend([
            {"event_type":"territory_alert","target_id":territories[0],"amount":.19,"source":"torture12"},
            {"event_type":"territory_weaken","target_id":territories[0],"amount":.13,"source":"torture12"},
            {"event_type":"territory_strengthen","target_id":territories[0],"amount":.09,"source":"torture12"},
        ])
    if len(territories)>1:
        base.append({"event_type":"territory_weaken","target_id":territories[-1],"amount":.07,"source":"torture12"})
    if len(fronts)>1:
        base.append({"event_type":"front_escalation","target_id":fronts[-1],"amount":.08,"source":"torture12"})

    # At least 40 accepted events whenever the world has mutable semantic entities.
    target_events=60 if base else 0
    i=0
    while i<target_events:
        e=deepcopy(base[i % len(base)])
        s=apply_world_event(w,s,e,source_fingerprint=fp)
        i+=1
    assert world_fingerprint(w)==fp
    assert validate_world_state(w,s)==[]
    assert validate_public_artifact(s,"world_state")["status"]=="pass"
    replayed=replay_events(w,s["event_log"])
    assert replayed==s
    assert state_fingerprint(replayed)==state_fingerprint(s)
    ebe=ebe_runtime_bundle(w,s)
    assert validate_public_artifact(ebe,"ebe_runtime")["status"]=="pass"

    # Deep frozen-bundle verification for the four canonical stress seeds.
    bundled=seed in (0,1,6060,7301)
    if bundled:
        with tempfile.TemporaryDirectory() as td:
            write_public_bundle(td,world=w,state=s,events=s["event_log"],ebe_runtime=ebe)
            vr=verify_public_bundle(td)
            assert vr["status"]=="pass",vr

    mark(f"stress_seed_{seed}_done")
    stress.append({
        "seed":seed,"world_fingerprint":fp,"state_fingerprint":state_fingerprint(s),
        "revision":s["clock"]["revision"],"observations":len(s["observations"]),
        "territories":len(s["territories"]),"fronts":len(s["fronts"]),
        "bundle_verified":bundled,"generation_seconds":round(generation,4),
    })

mark("phase3_done")
# ---------------------------------------------------------------------------
# 4. Long-history canonical soak: 250 mutations, exact replay, bounded values.
# ---------------------------------------------------------------------------
w=generate_semantic_world(profile,7301,6,5,4); fp=world_fingerprint(w); s=initialize_state(w)
fronts=sorted(s["fronts"]); territories=sorted(s["territories"])
pattern=[]
if fronts:
    pattern.extend([
        {"event_type":"front_escalation","target_id":fronts[0],"amount":.23,"source":"longsoak"},
        {"event_type":"front_deescalation","target_id":fronts[0],"amount":.17,"source":"longsoak"},
    ])
if territories:
    pattern.extend([
        {"event_type":"territory_weaken","target_id":territories[0],"amount":.19,"source":"longsoak"},
        {"event_type":"territory_alert","target_id":territories[0],"amount":.15,"source":"longsoak"},
        {"event_type":"territory_strengthen","target_id":territories[0],"amount":.11,"source":"longsoak"},
    ])
assert pattern
for i in range(250):
    s=apply_world_event(w,s,deepcopy(pattern[i%len(pattern)]),source_fingerprint=fp)
assert s["clock"]["revision"]==250
assert validate_world_state(w,s)==[]
for item in s["territories"].values():
    assert 0<=item["control_strength"]<=1.75 and 0<=item["stability"]<=1 and 0<=item["alert"]<=1
for item in s["fronts"].values():
    assert 0<=item["tension"]<=1 and 0<=item["activity"]<=1
replayed=replay_events(w,s["event_log"])
assert replayed==s
long_state_fp=state_fingerprint(s)

with tempfile.TemporaryDirectory() as td:
    ebe=ebe_runtime_bundle(w,s)
    write_public_bundle(td,world=w,state=s,events=s["event_log"],ebe_runtime=ebe)
    assert verify_public_bundle(td)["status"]=="pass"

mark("phase4_done")
# ---------------------------------------------------------------------------
# 5. CLI corruption behavior: fail closed, nonzero, no Python traceback.
# ---------------------------------------------------------------------------
cli_cases=[]
with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    fixtures={
        "duplicate.json":'{"generator":{},"generator":{},"schema_versions":{},"sectors":[]}',
        "nan.json":'{"seed":NaN}',
        "broken.json":'{"seed":',
    }
    for name,text in fixtures.items():
        path=td/name; path.write_text(text,encoding="utf-8")
        p=subprocess.run([sys.executable,str(ROOT/"runtime_cli.py"),"validate-artifact","--input",str(path),"--type","world"],capture_output=True,text=True,timeout=30)
        assert p.returncode==2,(name,p.stdout,p.stderr)
        assert "Traceback" not in p.stderr
        assert "ERROR:" in p.stderr
        cli_cases.append({"case":name,"returncode":p.returncode,"stderr":p.stderr.strip()})
    badutf=td/"badutf.json"; badutf.write_bytes(b'\xff\xfe{}')
    p=subprocess.run([sys.executable,str(ROOT/"runtime_cli.py"),"validate-artifact","--input",str(badutf),"--type","world"],capture_output=True,text=True,timeout=30)
    assert p.returncode==2 and "Traceback" not in p.stderr and "ERROR:" in p.stderr
    cli_cases.append({"case":"badutf.json","returncode":p.returncode,"stderr":p.stderr.strip()})

mark("phase5_done")
# Write report as a test artifact when executed in-tree.
report={
    "test":"v093_pre1_torture",
    "validator_random_cases":validator_cases,
    "cross_process_determinism":cross_process,
    "stress_12x12":stress,
    "long_history":{"seed":7301,"dimensions":[6,5],"revision":250,"state_fingerprint":long_state_fp,"status":"pass"},
    "cli_corrupt_input_cases":cli_cases,
    "status":"pass",
    "timing_note":"generation timings are validation-environment measurements, not device benchmarks",
}
out=ROOT/"generated"/"v093_torture_report.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
print(f"PixelGen v0.9.3 pre-1.0 torture PASS: {validator_cases} validator cases, {len(cross_process)*3} fresh-process runs, {len(stress)} 12x12 worlds, 720 12x12 mutations, 250-event long replay, {len(cli_cases)} corrupt CLI cases")
