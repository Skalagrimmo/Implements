import json
import locale
import os
import platform
import re
import sys
import tempfile
import time
import statistics
from datetime import datetime, timezone
from pathlib import Path

import PIL

from .audit import audit_world
from .fingerprint import world_fingerprint
from .gameplay_export import export_gameplay_json, export_gameplay_lua
from .gameplay_world import generate_gameplay_world
from .world_render import render_world
from .cognitive_map import render_cognitive_map

LOG_SCHEMA_VERSION = "0.6.4.2"

SUITES = {
    "quick": [
        {"name": "tiny", "seed": 6401, "cols": 2, "rows": 2, "ability_count": 2},
        {"name": "reference", "seed": 6401, "cols": 4, "rows": 3, "ability_count": 4},
    ],
    "standard": [
        {"name": "tiny", "seed": 6401, "cols": 2, "rows": 2, "ability_count": 2},
        {"name": "reference", "seed": 6401, "cols": 4, "rows": 3, "ability_count": 4},
        {"name": "medium", "seed": 6401, "cols": 6, "rows": 5, "ability_count": 4},
    ],
    "stress": [
        {"name": "tiny", "seed": 6401, "cols": 2, "rows": 2, "ability_count": 2},
        {"name": "reference", "seed": 6401, "cols": 4, "rows": 3, "ability_count": 4},
        {"name": "medium", "seed": 6401, "cols": 6, "rows": 5, "ability_count": 4},
        {"name": "large", "seed": 6401, "cols": 8, "rows": 6, "ability_count": 4},
        {"name": "stress", "seed": 6401, "cols": 10, "rows": 8, "ability_count": 4},
    ],
}

def _ms(start):
    return round((time.perf_counter() - start) * 1000.0, 3)

def _safe_label(label):
    label = (label or "environment").strip()
    label = re.sub(r"[^A-Za-z0-9._-]+", "_", label)
    return label.strip("._-") or "environment"

def detect_runtime():
    env = os.environ
    exe = str(sys.executable).lower()
    prefix = str(sys.prefix).lower()

    if "com.termux" in exe or "com.termux" in prefix or "TERMUX_VERSION" in env:
        return "termux"
    if "pydroid" in exe or "pydroid" in prefix:
        return "pydroid"
    if "PROOT_TMP_DIR" in env or "proot" in " ".join(env.keys()).lower():
        return "proot-like"
    if "ANDROID_ROOT" in env or "ANDROID_DATA" in env:
        return "android-python"
    return "desktop-python"

def environment_info(label=None, device=None, notes=None):
    return {
        "label": label or detect_runtime(),
        "detected_runtime": detect_runtime(),
        "device": device,
        "notes": notes,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "pillow_version": getattr(PIL, "__version__", "unknown"),
            "encoding": locale.getpreferredencoding(False),
            "cpu_count": os.cpu_count(),
            "android_environment": bool(os.environ.get("ANDROID_ROOT") or os.environ.get("ANDROID_DATA")),
        },
    }

def _benchmark_case_once(profile, case):
    result = {
        "name": case["name"],
        "seed": case["seed"],
        "cols": case["cols"],
        "rows": case["rows"],
        "ability_count": case["ability_count"],
        "status": "fail",
        "fingerprint": None,
        "audit_status": None,
        "visual_score": None,
        "visual_grade": None,
        "timings_ms": {},
        "errors": [],
    }

    total_start = time.perf_counter()
    try:
        t = time.perf_counter()
        world = generate_gameplay_world(
            profile,
            seed=case["seed"],
            cols=case["cols"],
            rows=case["rows"],
            ability_count=case["ability_count"],
        )
        result["timings_ms"]["generate"] = _ms(t)

        t = time.perf_counter()
        audit = audit_world(world)
        result["timings_ms"]["audit"] = _ms(t)
        result["audit_status"] = audit["status"]
        result["errors"].extend(audit.get("errors", []))

        t = time.perf_counter()
        result["fingerprint"] = world_fingerprint(world)
        result["timings_ms"]["fingerprint"] = _ms(t)

        vm = audit.get("visual", {}).get("metrics", {})
        result["visual_score"] = vm.get("visual_repetition_score")
        result["visual_grade"] = vm.get("visual_grade")

        # Render to memory; no GUI/display is required.
        t = time.perf_counter()
        world_img = render_world(world, profile, gap=4)
        world_img.tobytes()
        result["timings_ms"]["render_world"] = _ms(t)

        t = time.perf_counter()
        cognitive = render_cognitive_map(world, profile)
        cognitive.tobytes()
        result["timings_ms"]["render_cognitive"] = _ms(t)

        # Export into a temporary directory to exercise JSON/Lua serialization + filesystem I/O.
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            t = time.perf_counter()
            export_gameplay_json(world, td / "world.json")
            export_gameplay_lua(world, td / "world.lua")
            # Read back so the timing covers a complete small round trip.
            (td / "world.json").read_bytes()
            (td / "world.lua").read_bytes()
            result["timings_ms"]["export_io"] = _ms(t)

        result["status"] = "pass" if audit["status"] != "fail" else "fail"
    except Exception as e:
        result["errors"].append(f"{type(e).__name__}: {e}")

    result["timings_ms"]["total"] = _ms(total_start)
    return result

def _aggregate_numbers(values):
    vals=[float(v) for v in values if isinstance(v,(int,float))]
    if not vals:
        return {"mean":None,"median":None,"min":None,"max":None,"stdev":None,"cv":None}
    mean=statistics.mean(vals)
    median=statistics.median(vals)
    stdev=statistics.pstdev(vals) if len(vals)>1 else 0.0
    cv=(stdev/mean) if mean else 0.0
    return {
        "mean":round(mean,3),
        "median":round(median,3),
        "min":round(min(vals),3),
        "max":round(max(vals),3),
        "stdev":round(stdev,3),
        "cv":round(cv,4),
    }

def benchmark_case(profile, case, repeat=1):
    if isinstance(repeat,bool) or not isinstance(repeat,int) or repeat < 1:
        raise ValueError("repeat must be a positive integer")

    runs=[]
    for i in range(repeat):
        run=_benchmark_case_once(profile,case)
        run["run_index"]=i+1
        runs.append(run)

    fps={r.get("fingerprint") for r in runs if r.get("fingerprint")}
    statuses=[r.get("status") for r in runs]
    timing_keys=sorted({
        k for r in runs
        for k,v in r.get("timings_ms",{}).items()
        if isinstance(v,(int,float))
    })
    timing_stats={
        key:_aggregate_numbers([r.get("timings_ms",{}).get(key) for r in runs])
        for key in timing_keys
    }

    first=runs[0]
    result={
        "name":case["name"],
        "seed":case["seed"],
        "cols":case["cols"],
        "rows":case["rows"],
        "ability_count":case["ability_count"],
        "status":"pass" if all(s=="pass" for s in statuses) else "fail",
        "repeat":repeat,
        "fingerprint":next(iter(fps)) if len(fps)==1 else None,
        "fingerprint_consistent":len(fps)<=1,
        "audit_status":first.get("audit_status"),
        "visual_score":first.get("visual_score"),
        "visual_grade":first.get("visual_grade"),
        "timings_ms":{key:stats["median"] for key,stats in timing_stats.items()},
        "timing_stats":timing_stats,
        "runs":runs,
        "errors":[e for r in runs for e in r.get("errors",[])],
    }
    if not result["fingerprint_consistent"]:
        result["errors"].append("fingerprint changed between repeated runs")
        result["status"]="fail"
    return result

def run_environment_log(profile, suite="standard", label=None, device=None, notes=None, repeat=1):
    if suite not in SUITES:
        raise ValueError(f"unknown suite {suite!r}; expected one of {', '.join(SUITES)}")

    started = datetime.now(timezone.utc)
    cases = [benchmark_case(profile, spec, repeat=repeat) for spec in SUITES[suite]]
    ended = datetime.now(timezone.utc)

    return {
        "schema_version": LOG_SCHEMA_VERSION,
        "generator_version": "1.0.0",
        "created_utc": started.isoformat(),
        "completed_utc": ended.isoformat(),
        "suite": suite,
        "repeat": repeat,
        "environment": environment_info(label=label, device=device, notes=notes),
        "cases": cases,
        "summary": summarize_single_log(cases),
    }

def summarize_single_log(cases):
    passed = sum(c["status"] == "pass" for c in cases)
    failed = len(cases) - passed
    total_ms = round(sum(c["timings_ms"].get("total", 0.0) for c in cases), 3)
    return {
        "status": "pass" if failed == 0 else "fail",
        "cases": len(cases),
        "passed": passed,
        "failed": failed,
        "benchmark_total_ms": total_ms,
    }

def default_log_filename(log):
    label = _safe_label(log["environment"]["label"])
    suite = _safe_label(log["suite"])
    return f"{label}_{suite}.envlog.json"

def write_environment_log(log, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    return path

def environment_log_markdown(log):
    e = log["environment"]
    p = e["platform"]
    lines = [
        f"# PixelGen environment log — {e['label']}",
        "",
        f"- schema: **{log['schema_version']}**",
        f"- generator: **{log['generator_version']}**",
        f"- suite: **{log['suite']}**",
        f"- repeats per case: **{log.get('repeat',1)}**",
        f"- detected runtime: **{e['detected_runtime']}**",
        f"- system: **{p['system']} {p['release']}**",
        f"- machine: **{p['machine']}**",
        f"- Python: **{p['python_implementation']} {p['python_version']}**",
        f"- Pillow: **{p['pillow_version']}**",
        f"- CPU count: **{p['cpu_count']}**",
    ]
    if e.get("device"):
        lines.append(f"- device: **{e['device']}**")
    if e.get("notes"):
        lines.append(f"- notes: {e['notes']}")

    lines += [
        "",
        "| Case | Size | Status | Fingerprint | Generate median | World render median | Cognitive median | Total median | Total CV |",
        "|---|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for c in log["cases"]:
        t = c["timings_ms"]
        fp = (c.get("fingerprint") or "—")[:16]
        cv=c.get("timing_stats",{}).get("total",{}).get("cv")
        cv_text="—" if cv is None else f"{cv:.3f}"
        lines.append(
            f"| {c['name']} | {c['cols']}×{c['rows']} | {c['status']} | `{fp}` | "
            f"{t.get('generate','—')} | {t.get('render_world','—')} | "
            f"{t.get('render_cognitive','—')} | {t.get('total','—')} | {cv_text} |"
        )
    lines += [
        "",
        f"Overall: **{log['summary']['status'].upper()}**, "
        f"{log['summary']['passed']}/{log['summary']['cases']} cases passed.",
    ]
    return "\n".join(lines) + "\n"

def write_markdown_companion(log, json_path):
    json_path = Path(json_path)
    md_path = json_path.with_suffix("").with_suffix(".md")
    md_path.write_text(environment_log_markdown(log), encoding="utf-8")
    return md_path
