from .fingerprint import world_fingerprint
from .world_state import WORLD_STATE_VERSION, state_fingerprint

def validate_world_state(world,state):
    errors=[]

    if state.get("version")!=WORLD_STATE_VERSION:
        errors.append("world-state version mismatch")

    if state.get("source_world",{}).get("fingerprint")!=world_fingerprint(world):
        errors.append("world-state source fingerprint mismatch")

    graph=world.get("territory_graph",{})
    topo=world.get("influence_topology",{})
    expected_territories={t["id"] for t in graph.get("territories",[])}
    expected_fronts={f["id"] for f in topo.get("fronts",[])}

    if set(state.get("territories",{}))!=expected_territories:
        errors.append("world-state territory ids do not match static world")
    if set(state.get("fronts",{}))!=expected_fronts:
        errors.append("world-state front ids do not match static world")

    revision=int(state.get("clock",{}).get("revision",-1))
    tick=int(state.get("clock",{}).get("tick",-1))
    if revision < 0 or tick < 0:
        errors.append("world-state clock is invalid")
    if revision!=len(state.get("event_log",[])):
        errors.append("world-state revision does not match event log length")
    if revision!=len(state.get("mutations",[])):
        errors.append("world-state revision does not match mutation count")
    if revision!=len(state.get("derived_events",[])):
        errors.append("world-state revision does not match derived-event count")

    event_ids=[e.get("id") for e in state.get("event_log",[])]
    mutation_ids=[m.get("id") for m in state.get("mutations",[])]
    derived_ids=[e.get("id") for e in state.get("derived_events",[])]
    observation_ids=[o.get("id") for o in state.get("observations",[])]

    if len(event_ids)!=len(set(event_ids)):
        errors.append("duplicate runtime event ids")
    if len(mutation_ids)!=len(set(mutation_ids)):
        errors.append("duplicate mutation ids")
    if len(derived_ids)!=len(set(derived_ids)):
        errors.append("duplicate derived event ids")
    if len(observation_ids)!=len(set(observation_ids)):
        errors.append("duplicate observation ids")

    event_id_set=set(event_ids)
    derived_id_set=set(derived_ids)

    for mutation in state.get("mutations",[]):
        if mutation.get("cause_event_id") not in event_id_set:
            errors.append(f"{mutation.get('id')} references unknown cause event")
        ttype=mutation.get("target_type")
        tid=mutation.get("target_id")
        if ttype=="territory" and tid not in expected_territories:
            errors.append(f"{mutation.get('id')} references unknown territory")
        if ttype=="front" and tid not in expected_fronts:
            errors.append(f"{mutation.get('id')} references unknown front")

    for derived in state.get("derived_events",[]):
        if derived.get("cause_event_id") not in event_id_set:
            errors.append(f"{derived.get('id')} references unknown runtime cause")

    cols=int(world.get("cols",0))
    rows=int(world.get("rows",0))
    for obs in state.get("observations",[]):
        if obs.get("source_event_id") not in derived_id_set:
            errors.append(f"{obs.get('id')} references unknown derived event")
        sector=obs.get("sector",[])
        if len(sector)!=2:
            errors.append(f"{obs.get('id')} has invalid sector")
            continue
        sx,sy=sector
        if not (0 <= sx < cols and 0 <= sy < rows):
            errors.append(f"{obs.get('id')} sector outside world")
        if obs.get("knowledge_state")!="not_yet_assigned_to_any_agent":
            errors.append(f"{obs.get('id')} incorrectly claims agent knowledge")

    # Numeric range checks.
    for tid,item in state.get("territories",{}).items():
        if not (0.0 <= float(item.get("control_strength",-1)) <= 1.75):
            errors.append(f"{tid} control strength out of bounds")
        if not (0.0 <= float(item.get("stability",-1)) <= 1.0):
            errors.append(f"{tid} stability out of bounds")
        if not (0.0 <= float(item.get("alert",-1)) <= 1.0):
            errors.append(f"{tid} alert out of bounds")

    for fid,item in state.get("fronts",{}).items():
        if not (0.0 <= float(item.get("tension",-1)) <= 1.0):
            errors.append(f"{fid} tension out of bounds")
        if not (0.0 <= float(item.get("activity",-1)) <= 1.0):
            errors.append(f"{fid} activity out of bounds")

    # Ensure state is fingerprintable / JSON-canonical.
    try:
        fp=state_fingerprint(state)
        if len(fp)!=64:
            errors.append("world-state fingerprint has invalid length")
    except Exception as exc:
        errors.append(f"world-state fingerprint failed: {exc}")

    return errors
