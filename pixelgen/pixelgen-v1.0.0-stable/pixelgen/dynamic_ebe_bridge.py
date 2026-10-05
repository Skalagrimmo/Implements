from .ebe_bridge import build_ebe_seed_bundle

DYNAMIC_EBE_BRIDGE_VERSION="0.8.0"

def build_dynamic_ebe_bundle(world,state,since_revision=0):
    static=build_ebe_seed_bundle(world)
    since_revision=max(0,int(since_revision))

    dynamic_entities=[]
    for tid,item in sorted(state.get("territories",{}).items()):
        dynamic_entities.append({
            "id":tid,
            "entity_type":"territory_state",
            "alignment":item.get("alignment"),
            "control_strength":item.get("control_strength"),
            "stability":item.get("stability"),
            "alert":item.get("alert"),
            "status":item.get("status"),
            "revision":item.get("revision",0),
        })

    for fid,item in sorted(state.get("fronts",{}).items()):
        dynamic_entities.append({
            "id":fid,
            "entity_type":"front_state",
            "pair":list(item.get("pair",[])),
            "tension":item.get("tension"),
            "activity":item.get("activity"),
            "status":item.get("status"),
            "revision":item.get("revision",0),
        })

    derived=[
        e for i,e in enumerate(state.get("derived_events",[]),start=1)
        if i > since_revision
    ]
    observations=[
        o for o in state.get("observations",[])
        if int(o.get("revision",0)) > since_revision
    ]

    return {
        "version":DYNAMIC_EBE_BRIDGE_VERSION,
        "source":{
            "world":static.get("source",{}),
            "state_revision":state.get("clock",{}).get("revision",0),
            "since_revision":since_revision,
        },
        "contract":{
            "pixelgen_static_role":"generate semantic world entities and seed hooks",
            "dynamic_state_role":"store deterministic mutable overlay and provenance",
            "ebe_role":"assign observations to agents, form memory/belief, propagate and react",
            "global_knowledge":"forbidden",
            "observation_semantics":"local evidence only",
        },
        "static_entities":static.get("entities",[]),
        "dynamic_entities":dynamic_entities,
        "events":derived,
        "observations":observations,
    }
