from collections import defaultdict

INFLUENCE_VERSION="0.7.3"

SOURCE_PROFILES={
    "printing_cathedral":{
        "channel":"print_civic",
        "radius":5,
        "strength":1.00,
        "hazard_mult":0.92,
        "prop_mult":1.18,
        "encounter_mult":0.94,
    },
    "silt_spire":{
        "channel":"silt_contamination",
        "radius":5,
        "strength":1.00,
        "hazard_mult":1.24,
        "prop_mult":1.08,
        "encounter_mult":1.14,
    },
    "printing_press_altar":{
        "channel":"print_civic",
        "radius":3,
        "strength":0.72,
        "hazard_mult":0.97,
        "prop_mult":1.12,
        "encounter_mult":0.98,
    },
    "nanolith_shrine":{
        "channel":"nano_signal",
        "radius":3,
        "strength":0.72,
        "hazard_mult":1.10,
        "prop_mult":1.05,
        "encounter_mult":1.06,
    },
}

CHANNELS=("print_civic","silt_contamination","nano_signal")

def _falloff(distance,radius):
    if distance>radius:
        return 0.0
    # Smooth but deterministic integer-grid falloff.
    x=1.0-(distance/(radius+1.0))
    return round(max(0.0,x*x),4)

def plan_influences(cols,rows,landmark_plan):
    sources=[]
    for item in landmark_plan.get("placements",[]):
        kind=item.get("kind")
        profile=SOURCE_PROFILES.get(kind)
        if not profile:
            continue
        sector=item.get("sector")
        if not sector or len(sector)!=2:
            continue
        sx,sy=int(sector[0]),int(sector[1])
        sources.append({
            "id":item.get("id"),
            "kind":kind,
            "scope":item.get("scope"),
            "sector":[sx,sy],
            "channel":profile["channel"],
            "radius":profile["radius"],
            "strength":profile["strength"],
        })

    per_sector={}
    for sy in range(rows):
        for sx in range(cols):
            channels={c:0.0 for c in CHANNELS}
            contributions=[]
            h=1.0; p=1.0; e=1.0
            for source in sources:
                prof=SOURCE_PROFILES[source["kind"]]
                dist=abs(sx-source["sector"][0])+abs(sy-source["sector"][1])
                f=_falloff(dist,prof["radius"])*prof["strength"]
                if f<=0:
                    continue
                channels[prof["channel"]] += f
                h *= 1.0 + (prof["hazard_mult"]-1.0)*f
                p *= 1.0 + (prof["prop_mult"]-1.0)*f
                e *= 1.0 + (prof["encounter_mult"]-1.0)*f
                contributions.append({
                    "source_id":source["id"],
                    "kind":source["kind"],
                    "channel":prof["channel"],
                    "distance":dist,
                    "weight":round(f,4),
                })

            channels={k:round(min(1.75,v),4) for k,v in channels.items()}
            dominant=max(channels,key=channels.get) if any(channels.values()) else None
            per_sector[(sx,sy)]={
                "channels":channels,
                "dominant_channel":dominant,
                "contributions":sorted(
                    contributions,
                    key=lambda x:(-x["weight"],x["source_id"] or "")
                ),
                "modifier_mults":{
                    "hazard_mult":round(h,4),
                    "prop_mult":round(p,4),
                    "encounter_mult":round(e,4),
                },
            }

    return {
        "version":INFLUENCE_VERSION,
        "policy":{
            "distance":"Manhattan sector distance",
            "falloff":"quadratic",
            "stacking":"multiplicative local density modifiers; additive channel intensity",
            "sources":"world/regional landmark anchors",
        },
        "sources":sources,
        "per_sector":per_sector,
    }

def public_influences(plan,cols,rows):
    return {
        "version":plan["version"],
        "policy":plan["policy"],
        "sources":plan["sources"],
        "sectors":[
            {"sx":sx,"sy":sy,**plan["per_sector"][(sx,sy)]}
            for sy in range(rows)
            for sx in range(cols)
        ],
    }

def apply_influence_to_geography_context(ctx,influence):
    out=dict(ctx or {})
    base=dict(out.get("modifiers",{}))
    mults=influence.get("modifier_mults",{})
    for key in ("hazard_mult","prop_mult","encounter_mult"):
        base[key]=round(float(base.get(key,1.0))*float(mults.get(key,1.0)),4)
    out["modifiers"]=base
    out["regional_influence"]={
        "channels":dict(influence.get("channels",{})),
        "dominant_channel":influence.get("dominant_channel"),
        "contributions":list(influence.get("contributions",[])),
    }
    return out
