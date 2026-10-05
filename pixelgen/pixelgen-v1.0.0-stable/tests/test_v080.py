from copy import deepcopy
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.fingerprint import world_fingerprint
from pixelgen.world_state import (
    initialize_world_state,
    apply_world_event,
    replay_world_events,
    state_fingerprint,
    state_summary,
)
from pixelgen.world_state_integrity import validate_world_state
from pixelgen.dynamic_ebe_bridge import build_dynamic_ebe_bundle
from pixelgen.world_state_render import render_world_state_map

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

world=generate_gameplay_world(profile,7301,6,5,4)
assert world["generator"]["version"].startswith(("0.8.","0.9.","1.0."))
assert world["schema_versions"]["dynamic_world_state"]=="0.8.0"

static_fp=world_fingerprint(world)
static_copy=deepcopy(world)

initial=initialize_world_state(world)
assert validate_world_state(world,initial)==[]
assert initial["clock"]=={"tick":0,"revision":0}
assert initial["event_log"]==[]
assert initial["derived_events"]==[]
assert initial["observations"]==[]
assert initial["source_world"]["fingerprint"]==static_fp

# Static generated world must never be mutated by dynamic overlay operations.
front_id=sorted(initial["fronts"])[0]
state1=apply_world_event(world,initial,{
    "event_type":"front_escalation",
    "target_id":front_id,
    "amount":0.20,
    "source":"test",
})
assert world==static_copy
assert world_fingerprint(world)==static_fp
assert validate_world_state(world,state1)==[]

before=initial["fronts"][front_id]
after=state1["fronts"][front_id]
assert after["tension"] > before["tension"]
assert after["activity"] > before["activity"]
assert state1["clock"]=={"tick":1,"revision":1}
assert len(state1["mutations"])==1
assert len(state1["derived_events"])==1
assert state1["mutations"][0]["cause_event_id"]==state1["event_log"][0]["id"]
assert state1["derived_events"][0]["cause_event_id"]==state1["event_log"][0]["id"]

# Observations are local evidence only: no NPC/global knowledge is manufactured.
origin=state1["event_log"][0]["sector"]
assert origin is not None
assert len(state1["observations"])>=1
for obs in state1["observations"]:
    sx,sy=obs["sector"]
    assert abs(sx-origin[0])+abs(sy-origin[1]) <= 1
    assert obs["evidence"]=="direct_local"
    assert obs["delivery_state"]=="available_to_local_observers"
    assert obs["knowledge_state"]=="not_yet_assigned_to_any_agent"

assert len(state1["observations"]) < world["cols"]*world["rows"]

# Territory mutation has bounded, directional behavior.
territory_id=sorted(initial["territories"])[0]
state2=apply_world_event(world,state1,{
    "event_type":"territory_weaken",
    "target_id":territory_id,
    "amount":0.15,
    "source":"test",
    "cause_id":state1["event_log"][0]["id"],
})
assert validate_world_state(world,state2)==[]
assert state2["territories"][territory_id]["control_strength"] <= state1["territories"][territory_id]["control_strength"]
assert state2["territories"][territory_id]["stability"] <= state1["territories"][territory_id]["stability"]
assert state2["territories"][territory_id]["alert"] >= state1["territories"][territory_id]["alert"]

# Replay reconstructs the exact state, including provenance, observations and fingerprint.
replayed=replay_world_events(world,state2["event_log"])
assert replayed==state2
assert state_fingerprint(replayed)==state_fingerprint(state2)

# Dynamic EBE bridge includes mutable entity state and local evidence without global knowledge.
bridge=build_dynamic_ebe_bundle(world,state2)
assert bridge["version"]=="0.8.0"
assert bridge["contract"]["global_knowledge"]=="forbidden"
assert len(bridge["events"])==2
assert len(bridge["observations"])==len(state2["observations"])
assert len(bridge["dynamic_entities"])==len(state2["territories"])+len(state2["fronts"])
assert all(o["knowledge_state"]=="not_yet_assigned_to_any_agent" for o in bridge["observations"])

incremental=build_dynamic_ebe_bundle(world,state2,since_revision=1)
assert len(incremental["events"])==1
assert all(o["source_event_id"]=="derived_event_2" for o in incremental["observations"])

# State rendering is deterministic.
a=render_world_state_map(world,state2)
b=render_world_state_map(world,replayed)
assert a.tobytes()==b.tobytes()

# Invalid source world is rejected.
other=generate_gameplay_world(profile,7302,6,5,4)
assert validate_world_state(other,state2)

# Unsupported mutation is rejected.
try:
    apply_world_event(world,state2,{
        "event_type":"teleport_reality",
        "target_id":territory_id,
        "amount":0.1,
    })
    raise AssertionError("unsupported event type was accepted")
except ValueError:
    pass

# Minimal world remains a valid empty dynamic overlay.
tiny=generate_gameplay_world(profile,-777,1,1,0)
tiny_state=initialize_world_state(tiny)
assert tiny_state["territories"]=={}
assert tiny_state["fronts"]=={}
assert validate_world_state(tiny,tiny_state)==[]

summary=state_summary(state2)
assert summary["revision"]==2
assert summary["events"]==2
assert summary["mutations"]==2
assert summary["derived_events"]==2

print("PixelGen v0.8.0 dynamic world-state / EBE runtime bridge tests passed")
