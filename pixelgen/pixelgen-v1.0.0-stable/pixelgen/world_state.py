from copy import deepcopy
import hashlib
import json

from .fingerprint import world_fingerprint
from .serialization import to_plain

WORLD_STATE_VERSION="0.8.0"
MAX_CONTROL=1.75
LOCAL_OBSERVATION_RADIUS=1


def _clamp(value,lo=0.0,hi=1.0):
    return max(lo,min(hi,float(value)))


def _front_status(tension):
    if tension < 0.20:
        return "quiet"
    if tension < 0.45:
        return "active"
    if tension < 0.75:
        return "tense"
    return "volatile"


def _territory_status(stability,alert):
    if stability < 0.35:
        return "fragile"
    if alert >= 0.65:
        return "pressured"
    if stability >= 0.75 and alert < 0.30:
        return "secure"
    return "stable"


def _front_site_lookup(world):
    graph=world.get("territory_graph",{})
    return {
        site["front_id"]:list(site["sector"])
        for site in graph.get("front_sites",[])
    }


def _territory_lookup(world):
    return {
        t["id"]:t
        for t in world.get("territory_graph",{}).get("territories",[])
    }


def _front_lookup(world):
    return {
        f["id"]:f
        for f in world.get("influence_topology",{}).get("fronts",[])
    }


def _front_territories(world):
    return {
        link["front_id"]:list(link.get("territory_ids",[]))
        for link in world.get("territory_graph",{}).get("front_links",[])
    }


def initialize_world_state(world):
    territory_states={}
    for t in world.get("territory_graph",{}).get("territories",[]):
        control=_clamp(t.get("mean_strength",0.0),0.0,MAX_CONTROL)
        stability=_clamp(0.58 + min(0.25,control*0.20))
        alert=_clamp(0.18 + 0.10*len(t.get("front_ids",[])))
        territory_states[t["id"]]={
            "alignment":t.get("alignment"),
            "control_strength":round(control,4),
            "stability":round(stability,4),
            "alert":round(alert,4),
            "status":_territory_status(stability,alert),
            "revision":0,
        }

    front_states={}
    for f in world.get("influence_topology",{}).get("fronts",[]):
        tension=_clamp(f.get("mean_pressure",0.0))
        activity=_clamp(0.15 + tension*0.60)
        front_states[f["id"]]={
            "pair":list(f.get("pair",[])),
            "tension":round(tension,4),
            "activity":round(activity,4),
            "status":_front_status(tension),
            "revision":0,
        }

    return {
        "version":WORLD_STATE_VERSION,
        "source_world":{
            "fingerprint":world_fingerprint(world),
            "seed":world.get("seed"),
            "dimensions":[world.get("cols"),world.get("rows")],
        },
        "clock":{
            "tick":0,
            "revision":0,
        },
        "territories":territory_states,
        "fronts":front_states,
        "event_log":[],
        "mutations":[],
        "derived_events":[],
        "observations":[],
        "contract":{
            "static_world_mutation":"forbidden",
            "dynamic_state_model":"overlay",
            "knowledge_model":"observations are local evidence, not global NPC knowledge",
        },
    }


def _state_payload_for_fingerprint(state):
    data=deepcopy(to_plain(state))
    return data


def state_fingerprint(state):
    payload=_state_payload_for_fingerprint(state)
    raw=json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",",":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _event_origin(world,event,target_type,target_id):
    if "sector" in event and event["sector"] is not None:
        sector=list(event["sector"])
        if len(sector)!=2:
            raise ValueError("event sector must be [sx, sy]")
        return [int(sector[0]),int(sector[1])]

    if target_type=="front":
        site=_front_site_lookup(world).get(target_id)
        if site is not None:
            return list(site)

    if target_type=="territory":
        t=_territory_lookup(world).get(target_id)
        if t is not None:
            return list(t.get("center",[]))

    return None


def _normalize_event(world,state,event):
    if not isinstance(event,dict):
        raise TypeError("world-state event must be a dict")

    event_type=str(event.get("event_type",""))
    if event_type not in {
        "front_escalation",
        "front_deescalation",
        "territory_strengthen",
        "territory_weaken",
        "territory_alert",
    }:
        raise ValueError(f"unsupported world-state event type {event_type!r}")

    target_id=str(event.get("target_id",""))
    if not target_id:
        raise ValueError("world-state event requires target_id")

    target_type="front" if event_type.startswith("front_") else "territory"
    if target_type=="front" and target_id not in state["fronts"]:
        raise ValueError(f"unknown front target {target_id!r}")
    if target_type=="territory" and target_id not in state["territories"]:
        raise ValueError(f"unknown territory target {target_id!r}")

    amount=float(event.get("amount",0.10))
    if amount <= 0 or amount > 1.0:
        raise ValueError("event amount must be >0 and <=1")

    revision=int(state["clock"]["revision"])+1
    event_id=str(event.get("id") or f"runtime_event_{revision}")
    existing_ids={e.get("id") for e in state.get("event_log",[])}
    if event_id in existing_ids:
        raise ValueError(f"duplicate runtime event id {event_id!r}")

    return {
        "id":event_id,
        "event_type":event_type,
        "target_type":target_type,
        "target_id":target_id,
        "amount":round(amount,4),
        "sector":_event_origin(world,event,target_type,target_id),
        "source":str(event.get("source","runtime")),
        "actor_id":event.get("actor_id"),
        "cause_id":event.get("cause_id"),
    }


def _mutate_front(world,state,event):
    target=state["fronts"][event["target_id"]]
    before=deepcopy(target)
    amount=event["amount"]

    if event["event_type"]=="front_escalation":
        target["tension"]=round(_clamp(target["tension"]+amount),4)
        target["activity"]=round(_clamp(target["activity"]+amount*0.70),4)
        territory_alert_delta=amount*0.45
        territory_stability_delta=-amount*0.12
    else:
        target["tension"]=round(_clamp(target["tension"]-amount),4)
        target["activity"]=round(_clamp(target["activity"]-amount*0.55),4)
        territory_alert_delta=-amount*0.30
        territory_stability_delta=amount*0.08

    target["status"]=_front_status(target["tension"])
    target["revision"]+=1

    secondary=[]
    for tid in _front_territories(world).get(event["target_id"],[]):
        if tid not in state["territories"]:
            continue
        ts=state["territories"][tid]
        tbefore=deepcopy(ts)
        ts["alert"]=round(_clamp(ts["alert"]+territory_alert_delta),4)
        ts["stability"]=round(_clamp(ts["stability"]+territory_stability_delta),4)
        ts["status"]=_territory_status(ts["stability"],ts["alert"])
        ts["revision"]+=1
        secondary.append({
            "target_type":"territory",
            "target_id":tid,
            "before":tbefore,
            "after":deepcopy(ts),
            "relation":"adjacent_to_front",
        })

    return before,deepcopy(target),secondary


def _mutate_territory(state,event):
    target=state["territories"][event["target_id"]]
    before=deepcopy(target)
    amount=event["amount"]

    if event["event_type"]=="territory_strengthen":
        target["control_strength"]=round(
            _clamp(target["control_strength"]+amount,0.0,MAX_CONTROL),4
        )
        target["stability"]=round(_clamp(target["stability"]+amount*0.40),4)
        target["alert"]=round(_clamp(target["alert"]-amount*0.20),4)
    elif event["event_type"]=="territory_weaken":
        target["control_strength"]=round(
            _clamp(target["control_strength"]-amount,0.0,MAX_CONTROL),4
        )
        target["stability"]=round(_clamp(target["stability"]-amount*0.40),4)
        target["alert"]=round(_clamp(target["alert"]+amount*0.30),4)
    elif event["event_type"]=="territory_alert":
        target["alert"]=round(_clamp(target["alert"]+amount),4)
        target["stability"]=round(_clamp(target["stability"]-amount*0.10),4)

    target["status"]=_territory_status(target["stability"],target["alert"])
    target["revision"]+=1
    return before,deepcopy(target),[]


def _local_observation_sectors(world,origin,radius=LOCAL_OBSERVATION_RADIUS):
    if origin is None:
        return []
    ox,oy=int(origin[0]),int(origin[1])
    cols=int(world.get("cols",0))
    rows=int(world.get("rows",0))
    result=[]
    for sy in range(rows):
        for sx in range(cols):
            if abs(sx-ox)+abs(sy-oy) <= radius:
                result.append([sx,sy])
    return result


def _derived_event(event,before,after,revision):
    changed={
        key:{"before":before.get(key),"after":after.get(key)}
        for key in after
        if before.get(key)!=after.get(key)
        and key!="revision"
    }
    return {
        "id":f"derived_event_{revision}",
        "revision":revision,
        "event_type":(
            "front_state_changed"
            if event["target_type"]=="front"
            else "territory_state_changed"
        ),
        "subject_type":event["target_type"],
        "subject_id":event["target_id"],
        "sector":event.get("sector"),
        "changes":changed,
        "cause_event_id":event["id"],
        "observability":"local_or_transmitted",
    }


def _observations(world,derived_event,revision):
    result=[]
    for i,sector in enumerate(
        _local_observation_sectors(world,derived_event.get("sector"))
    ):
        result.append({
            "id":f"observation_{revision}_{i}",
            "revision":revision,
            "source_event_id":derived_event["id"],
            "sector":sector,
            "subject_type":derived_event["subject_type"],
            "subject_id":derived_event["subject_id"],
            "fact":{
                "event_type":derived_event["event_type"],
                "changes":deepcopy(derived_event["changes"]),
            },
            "evidence":"direct_local",
            "delivery_state":"available_to_local_observers",
            "knowledge_state":"not_yet_assigned_to_any_agent",
        })
    return result


def apply_world_event(world,state,event,source_fingerprint=None):
    if state.get("version")!=WORLD_STATE_VERSION:
        raise ValueError("unsupported world-state version")
    actual_fingerprint=(
        str(source_fingerprint)
        if source_fingerprint is not None
        else world_fingerprint(world)
    )
    if state.get("source_world",{}).get("fingerprint")!=actual_fingerprint:
        raise ValueError("world-state source fingerprint does not match world")

    next_state=deepcopy(state)
    normalized=_normalize_event(world,next_state,event)
    revision=int(next_state["clock"]["revision"])+1

    if normalized["target_type"]=="front":
        before,after,secondary=_mutate_front(world,next_state,normalized)
    else:
        before,after,secondary=_mutate_territory(next_state,normalized)

    mutation={
        "id":f"mutation_{revision}",
        "revision":revision,
        "tick":int(next_state["clock"]["tick"])+1,
        "cause_event_id":normalized["id"],
        "target_type":normalized["target_type"],
        "target_id":normalized["target_id"],
        "before":before,
        "after":after,
        "secondary_mutations":secondary,
        "provenance":{
            "source":normalized.get("source"),
            "actor_id":normalized.get("actor_id"),
            "cause_id":normalized.get("cause_id"),
            "origin_sector":normalized.get("sector"),
        },
    }

    derived=_derived_event(normalized,before,after,revision)
    observations=_observations(world,derived,revision)

    next_state["clock"]["revision"]=revision
    next_state["clock"]["tick"]+=1
    next_state["event_log"].append(normalized)
    next_state["mutations"].append(mutation)
    next_state["derived_events"].append(derived)
    next_state["observations"].extend(observations)

    return next_state


def replay_world_events(world,events):
    state=initialize_world_state(world)
    source_fingerprint=state["source_world"]["fingerprint"]
    for event in events:
        state=apply_world_event(
            world,state,event,
            source_fingerprint=source_fingerprint,
        )
    return state


def state_summary(state):
    territory_status={}
    for item in state.get("territories",{}).values():
        territory_status[item["status"]]=territory_status.get(item["status"],0)+1

    front_status={}
    for item in state.get("fronts",{}).values():
        front_status[item["status"]]=front_status.get(item["status"],0)+1

    return {
        "version":state.get("version"),
        "revision":state.get("clock",{}).get("revision",0),
        "tick":state.get("clock",{}).get("tick",0),
        "territory_status_counts":dict(sorted(territory_status.items())),
        "front_status_counts":dict(sorted(front_status.items())),
        "events":len(state.get("event_log",[])),
        "mutations":len(state.get("mutations",[])),
        "derived_events":len(state.get("derived_events",[])),
        "observations":len(state.get("observations",[])),
        "fingerprint":state_fingerprint(state),
    }
