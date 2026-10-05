import sys
from pathlib import Path
from .palette import load_profile
from .gameplay_world import generate_gameplay_world
from .audit import audit_world

def run_doctor(profile_path):
    checks=[]

    def add(name, ok, detail):
        checks.append({"name":name,"ok":bool(ok),"detail":str(detail)})

    add("python", sys.version_info >= (3,9), sys.version.split()[0])

    try:
        from PIL import Image
        add("pillow", True, getattr(Image,"__version__","installed"))
    except Exception as e:
        add("pillow", False, e)
        return {"status":"fail","checks":checks}

    try:
        p=Path(profile_path)
        profile=load_profile(p)
        add("profile", True, p)
    except Exception as e:
        add("profile", False, e)
        return {"status":"fail","checks":checks}

    try:
        world=generate_gameplay_world(profile,seed=6303,cols=2,rows=2,ability_count=2)
        result=audit_world(world)
        add("2x2_generation", result["status"]!="fail", result["status"])
        add("progression", bool(result.get("progression",{}).get("final_sector_reachable")), "final reachable")
    except Exception as e:
        add("2x2_generation", False, e)

    return {
        "status":"pass" if all(c["ok"] for c in checks) else "fail",
        "checks":checks,
    }
