from .gameplay_world import generate_gameplay_world
from .audit import audit_world

def _grade(score):
    if score >= 90: return "A"
    if score >= 80: return "B"
    if score >= 70: return "C"
    if score >= 60: return "D"
    return "E"

def sweep_seeds(profile, start_seed=0, count=20, cols=4, rows=3, ability_count=4, strict_visual=False):
    if isinstance(count,bool) or not isinstance(count,int) or count < 1:
        raise ValueError("count must be a positive integer")
    results=[]
    for i in range(count):
        seed=start_seed+i
        try:
            world=generate_gameplay_world(profile,seed,cols,rows,ability_count)
            audit=audit_world(world,strict_visual=strict_visual)
            metrics=audit["visual"]["metrics"]
            score=metrics["visual_repetition_score"]
            results.append({
                "seed":seed,
                "status":audit["status"],
                "score":score,
                "grade":metrics.get("visual_grade") or _grade(score),
                "warnings":len(audit["warnings"]),
                "errors":len(audit["errors"]),
                "landmarks":metrics["landmark_count"],
                "dominant_quadrant_share":metrics["dominant_quadrant_share"],
                "exact_position_repeat_share":metrics["exact_position_repeat_share"],
            })
        except Exception as e:
            results.append({
                "seed":seed,
                "status":"fail",
                "score":0,
                "grade":"F",
                "warnings":0,
                "errors":1,
                "landmarks":0,
                "error":str(e),
            })

    results.sort(key=lambda r:(
        r["status"]!="pass",
        r["status"]=="fail",
        -r["score"],
        r["warnings"],
        r["seed"],
    ))
    best=next((r for r in results if r["status"]!="fail"),None)
    return {
        "start_seed":start_seed,
        "count":count,
        "cols":cols,
        "rows":rows,
        "ability_count":ability_count,
        "strict_visual":bool(strict_visual),
        "best_seed":None if best is None else best["seed"],
        "best_score":None if best is None else best["score"],
        "results":results,
    }
