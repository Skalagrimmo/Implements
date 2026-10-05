from collections import Counter
from math import ceil, log2

def _landmarks(world):
    out=[]
    for s in world["sectors"]:
        for item in s["scene"].get("landmarks",{}).values():
            out.append({"sector":(s["sx"],s["sy"]), **item})
    return out

def _quadrant(scene, x, y):
    mx=(scene["width"]-1)/2
    my=(scene["height"]-1)/2
    if abs(x-mx) <= 1 and abs(y-my) <= 1:
        return "C"
    return ("N" if y < my else "S") + ("W" if x < mx else "E")

def _manhattan(a,b):
    return abs(a[0]-b[0])+abs(a[1]-b[1])

def analyze_visual_patterns(world):
    landmarks=_landmarks(world)
    warnings=[]
    metrics={
        "landmark_count":len(landmarks),
        "scope_counts":dict(Counter(x.get("scope","local") for x in landmarks)),
        "kind_counts":dict(Counter(x.get("kind","?") for x in landmarks)),
        "quadrant_counts":{},
        "distinct_local_positions":len({(x.get("x"),x.get("y")) for x in landmarks}),
        "min_regional_sector_distance":None,
        "dominant_quadrant_share":0.0,
        "exact_position_repeat_share":0.0,
        "visual_repetition_score":100,
        "visual_grade":"A",
        "quadrant_entropy":0.0,
    }
    if not landmarks:
        return {"warnings":[],"metrics":metrics,"status":"pass"}

    lookup={(s["sx"],s["sy"]):s for s in world["sectors"]}
    quadrants=[]
    positions=[]
    for lm in landmarks:
        s=lookup[lm["sector"]]
        quadrants.append(_quadrant(s["scene"],lm["x"],lm["y"]))
        positions.append((lm["x"],lm["y"]))
    qc=Counter(quadrants)
    pc=Counter(positions)
    metrics["quadrant_counts"]=dict(qc)
    dominant=max(qc.values())/len(landmarks)
    repeated=max(pc.values())/len(landmarks)
    metrics["dominant_quadrant_share"]=round(dominant,3)
    metrics["exact_position_repeat_share"]=round(repeated,3)

    regional=[lm["sector"] for lm in landmarks if lm.get("scope")=="regional"]
    if len(regional)>=2:
        dists=[_manhattan(a,b) for i,a in enumerate(regional) for b in regional[i+1:]]
        metrics["min_regional_sector_distance"]=min(dists)

    if len(landmarks)>=4 and dominant >= 0.70:
        warnings.append(f"landmark quadrant concentration is high ({dominant:.0%})")
    if len(landmarks)>=4 and repeated >= 0.50:
        warnings.append(f"too many landmarks share the same local coordinate ({repeated:.0%})")
    if metrics["min_regional_sector_distance"] is not None and metrics["min_regional_sector_distance"] < 2 and world["cols"]*world["rows"] >= 9:
        warnings.append("regional landmarks are closer than 2 sectors")
    if len(landmarks) > max(4, ceil(world["cols"]*world["rows"]*0.55)):
        warnings.append("landmark density is high enough to weaken landmark salience")

    score=100
    score -= max(0, int((dominant-0.45)*80))
    score -= max(0, int((repeated-0.30)*70))
    if metrics["min_regional_sector_distance"] is not None and metrics["min_regional_sector_distance"] < 2:
        score -= 12
    score -= max(0, len(warnings)-1)*5
    metrics["visual_repetition_score"]=max(0,min(100,score))
    s=metrics["visual_repetition_score"]
    metrics["visual_grade"]="A" if s>=90 else ("B" if s>=80 else ("C" if s>=70 else ("D" if s>=60 else "E")))
    return {"warnings":warnings,"metrics":metrics,"status":"warn" if warnings else "pass"}

def validate_visual_patterns(world, strict=False):
    result=analyze_visual_patterns(world)
    return list(result["warnings"]) if strict else []
