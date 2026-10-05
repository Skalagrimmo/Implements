import csv
import io
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

def load_environment_log(path):
    path=Path(path)
    data=json.loads(path.read_text(encoding="utf-8"))
    if "environment" not in data or "cases" not in data:
        raise ValueError(f"not a PixelGen environment log: {path}")
    data["_source"]=str(path)
    return data

def _case_key(case):
    return (
        case.get("name"),
        case.get("seed"),
        case.get("cols"),
        case.get("rows"),
        case.get("ability_count"),
    )

def _total_ms(case):
    return case.get("timings_ms",{}).get("total")

def _cv(case):
    cv=case.get("timing_stats",{}).get("total",{}).get("cv")
    return cv if isinstance(cv,(int,float)) else None

def _geomean(values):
    vals=[float(v) for v in values if isinstance(v,(int,float)) and v>0]
    if not vals:
        return None
    return math.exp(sum(math.log(v) for v in vals)/len(vals))

def compare_logs(logs, baseline_label=None):
    if len(logs)<2:
        raise ValueError("at least two environment logs are required")

    labels=[x["environment"]["label"] for x in logs]
    if len(labels)!=len(set(labels)):
        raise ValueError("environment labels must be unique")
    if baseline_label is not None and baseline_label not in labels:
        raise ValueError(f"baseline label not found: {baseline_label}")

    cases_by_key=defaultdict(list)
    for log in logs:
        for case in log["cases"]:
            cases_by_key[_case_key(case)].append((log["environment"]["label"],case))

    comparisons=[]
    fingerprint_mismatches=[]
    missing_cases=[]
    failed_envs=[]
    ratios_by_env=defaultdict(list)
    cvs_by_env=defaultdict(list)
    pass_counts=defaultdict(int)
    present_counts=defaultdict(int)

    for key in sorted(cases_by_key,key=str):
        entries=cases_by_key[key]
        present={label for label,_ in entries}
        missing=[label for label in labels if label not in present]
        if missing:
            missing_cases.append({"case":list(key),"missing":missing})

        fps={
            label:case.get("fingerprint")
            for label,case in entries
            if case.get("status")=="pass" and case.get("fingerprint")
        }
        distinct=sorted(set(fps.values()))
        deterministic=len(distinct)<=1 and len(fps)>=2
        if len(distinct)>1:
            fingerprint_mismatches.append({"case":list(key),"fingerprints":fps})

        totals={
            label:_total_ms(case)
            for label,case in entries
            if isinstance(_total_ms(case),(int,float)) and _total_ms(case)>0
        }
        fastest=min(totals.values()) if totals else None
        baseline_ms=totals.get(baseline_label) if baseline_label else fastest
        if not baseline_ms:
            baseline_ms=fastest

        rows=[]
        for label,case in entries:
            present_counts[label]+=1
            if case.get("status")=="pass":
                pass_counts[label]+=1

            total=_total_ms(case)
            ratio=(total/baseline_ms) if (
                baseline_ms and isinstance(total,(int,float)) and total>0
            ) else None
            cv=_cv(case)

            if ratio is not None:
                ratios_by_env[label].append(ratio)
            if cv is not None:
                cvs_by_env[label].append(cv)

            rows.append({
                "environment":label,
                "status":case.get("status"),
                "repeat":case.get("repeat",1),
                "total_ms":total,
                "relative_to_baseline":None if ratio is None else round(ratio,3),
                "stability_cv":cv,
                "generate_ms":case.get("timings_ms",{}).get("generate"),
                "render_world_ms":case.get("timings_ms",{}).get("render_world"),
                "render_cognitive_ms":case.get("timings_ms",{}).get("render_cognitive"),
                "export_io_ms":case.get("timings_ms",{}).get("export_io"),
            })

        comparisons.append({
            "case":{
                "name":key[0],"seed":key[1],"cols":key[2],
                "rows":key[3],"ability_count":key[4],
            },
            "present_in":sorted(present),
            "missing_in":missing,
            "deterministic":deterministic,
            "fingerprints":fps,
            "baseline_ms":baseline_ms,
            "performance":rows,
        })

    for log in logs:
        failed=[c["name"] for c in log["cases"] if c.get("status")!="pass"]
        if failed:
            failed_envs.append({
                "environment":log["environment"]["label"],
                "failed_cases":failed,
            })

    env_summary=[]
    for log in logs:
        label=log["environment"]["label"]
        gm=_geomean(ratios_by_env[label])
        avg_cv=statistics.mean(cvs_by_env[label]) if cvs_by_env[label] else None
        total=present_counts[label]
        passed=pass_counts[label]
        pass_rate=(passed/total) if total else 0.0
        env_summary.append({
            "label":label,
            "cases_present":total,
            "cases_passed":passed,
            "pass_rate":round(pass_rate,4),
            "performance_index":None if gm is None else round(gm,3),
            "stability_cv_mean":None if avg_cv is None else round(avg_cv,4),
            "stability_grade":(
                None if avg_cv is None else
                ("A" if avg_cv<=0.03 else
                 "B" if avg_cv<=0.06 else
                 "C" if avg_cv<=0.10 else "D")
            ),
        })

    if failed_envs or fingerprint_mismatches:
        status="fail"
    elif missing_cases:
        status="warn"
    else:
        status="pass"

    return {
        "comparison_version":"0.6.4.2",
        "status":status,
        "baseline_label":baseline_label,
        "environment_count":len(logs),
        "environments":[
            {
                "label":l["environment"]["label"],
                "detected_runtime":l["environment"].get("detected_runtime"),
                "suite":l.get("suite"),
                "repeat":l.get("repeat",1),
                "python":l["environment"]["platform"].get("python_version"),
                "python_implementation":l["environment"]["platform"].get("python_implementation"),
                "pillow":l["environment"]["platform"].get("pillow_version"),
                "system":l["environment"]["platform"].get("system"),
                "machine":l["environment"]["platform"].get("machine"),
                "source":l.get("_source"),
            }
            for l in logs
        ],
        "environment_summary":env_summary,
        "cases":comparisons,
        "summary":{
            "fingerprint_mismatches":len(fingerprint_mismatches),
            "missing_case_groups":len(missing_cases),
            "environment_case_failures":len(failed_envs),
            "all_shared_fingerprints_match":len(fingerprint_mismatches)==0,
        },
        "fingerprint_mismatches":fingerprint_mismatches,
        "missing_cases":missing_cases,
        "failed_environments":failed_envs,
    }

def comparison_text(result):
    lines=[
        f"ENVIRONMENT COMPARISON: {result['status'].upper()}",
        f"Environments: {result['environment_count']}",
        f"Baseline: {result.get('baseline_label') or 'fastest-per-case'}",
        f"Fingerprint mismatches: {result['summary']['fingerprint_mismatches']}",
        f"Missing case groups: {result['summary']['missing_case_groups']}",
        f"Environment case failures: {result['summary']['environment_case_failures']}",
        "",
        "SUMMARY:",
    ]
    for e in sorted(
        result["environment_summary"],
        key=lambda x: float("inf") if x["performance_index"] is None else x["performance_index"]
    ):
        perf="—" if e["performance_index"] is None else f"{e['performance_index']:.2f}x"
        cv="—" if e["stability_cv_mean"] is None else f"{e['stability_cv_mean']:.3f}"
        lines.append(
            f"  {e['label']}: pass={e['cases_passed']}/{e['cases_present']} "
            f"perf={perf} stability_cv={cv} grade={e['stability_grade'] or '—'}"
        )
    lines.append("")

    for case in result["cases"]:
        c=case["case"]
        lines.append(
            f"{c['name']} {c['cols']}x{c['rows']} seed={c['seed']} "
            f"deterministic={'YES' if case['deterministic'] else 'NO'}"
        )
        for row in sorted(
            case["performance"],
            key=lambda r: float("inf") if r["total_ms"] is None else r["total_ms"]
        ):
            ratio=row["relative_to_baseline"]
            ratio_text="—" if ratio is None else f"{ratio:.2f}x"
            cv=row["stability_cv"]
            cv_text="—" if cv is None else f"{cv:.3f}"
            lines.append(
                f"  {row['environment']}: total={row['total_ms']} ms "
                f"relative={ratio_text} cv={cv_text} repeat={row['repeat']} status={row['status']}"
            )
        if case["missing_in"]:
            lines.append("  missing: "+", ".join(case["missing_in"]))
        lines.append("")

    if result["fingerprint_mismatches"]:
        lines.append("DETERMINISM MISMATCHES:")
        for item in result["fingerprint_mismatches"]:
            lines.append(f"  {item['case']}: {item['fingerprints']}")
    elif result["summary"]["all_shared_fingerprints_match"]:
        lines.append("All shared benchmark cases have matching semantic fingerprints.")
    return "\n".join(lines).rstrip()+"\n"

def comparison_markdown(result):
    lines=[
        "# PixelGen cross-environment compatibility matrix",
        "",
        f"Overall status: **{result['status'].upper()}**",
        f"Baseline: **{result.get('baseline_label') or 'fastest per case'}**",
        "",
        "## Environment summary",
        "",
        "| Environment | Pass | Performance index | Mean CV | Stability | Python | Pillow |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    emap={e["label"]:e for e in result["environments"]}
    for s in sorted(
        result["environment_summary"],
        key=lambda x: float("inf") if x["performance_index"] is None else x["performance_index"]
    ):
        e=emap[s["label"]]
        perf="—" if s["performance_index"] is None else f"{s['performance_index']:.2f}×"
        cv="—" if s["stability_cv_mean"] is None else f"{s['stability_cv_mean']:.3f}"
        lines.append(
            f"| {s['label']} | {s['cases_passed']}/{s['cases_present']} | {perf} | {cv} | "
            f"{s['stability_grade'] or '—'} | {e['python_implementation']} {e['python']} | {e['pillow']} |"
        )

    lines += [
        "",
        "## Determinism",
        "",
        f"- fingerprint mismatches: **{result['summary']['fingerprint_mismatches']}**",
        f"- missing case groups: **{result['summary']['missing_case_groups']}**",
        f"- environment case failures: **{result['summary']['environment_case_failures']}**",
        "",
    ]

    for case in result["cases"]:
        c=case["case"]
        lines += [
            f"### {c['name']} — {c['cols']}×{c['rows']}, seed {c['seed']}",
            "",
            f"Semantic fingerprint agreement: **{'PASS' if case['deterministic'] else 'FAIL'}**",
            "",
            "| Environment | Status | Repeat | Total median ms | vs baseline | CV | Generate | World render | Cognitive | Export I/O |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for r in sorted(
            case["performance"],
            key=lambda x: float("inf") if x["total_ms"] is None else x["total_ms"]
        ):
            ratio="—" if r["relative_to_baseline"] is None else f"{r['relative_to_baseline']:.2f}×"
            cv="—" if r["stability_cv"] is None else f"{r['stability_cv']:.3f}"
            lines.append(
                f"| {r['environment']} | {r['status']} | {r['repeat']} | {r['total_ms']} | {ratio} | {cv} | "
                f"{r['generate_ms']} | {r['render_world_ms']} | {r['render_cognitive_ms']} | {r['export_io_ms']} |"
            )
        lines.append("")

    lines += [
        "## Conclusion",
        "",
        (
            "All shared cases completed and semantic fingerprints match across environments."
            if result["status"]=="pass" else
            "Review missing cases, failures, or fingerprint mismatches before declaring cross-environment compatibility."
        ),
    ]
    return "\n".join(lines)+"\n"

def comparison_csv(result):
    buf=io.StringIO()
    w=csv.writer(buf)
    w.writerow([
        "case","seed","cols","rows","environment","status","repeat",
        "total_ms","relative_to_baseline","stability_cv",
        "generate_ms","render_world_ms","render_cognitive_ms","export_io_ms",
        "deterministic",
    ])
    for case in result["cases"]:
        c=case["case"]
        for r in case["performance"]:
            w.writerow([
                c["name"],c["seed"],c["cols"],c["rows"],
                r["environment"],r["status"],r["repeat"],
                r["total_ms"],r["relative_to_baseline"],r["stability_cv"],
                r["generate_ms"],r["render_world_ms"],
                r["render_cognitive_ms"],r["export_io_ms"],
                case["deterministic"],
            ])
    return buf.getvalue()
