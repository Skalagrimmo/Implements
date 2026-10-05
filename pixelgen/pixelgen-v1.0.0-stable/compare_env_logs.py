#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from pixelgen.environment_compare import (
    compare_logs,
    comparison_markdown,
    comparison_text,
    comparison_csv,
    load_environment_log,
)

def discover(inputs):
    paths = []
    for raw in inputs:
        p = Path(raw)
        if p.is_dir():
            paths.extend(sorted(p.glob("*.envlog.json")))
        else:
            paths.append(p)
    # stable unique order
    seen = set()
    out = []
    for p in paths:
        rp = str(p.resolve())
        if rp not in seen:
            seen.add(rp)
            out.append(p)
    return out

def main():
    ap = argparse.ArgumentParser(
        description="Compare PixelGen 0.6.4.2 environment logs and summarize determinism/performance."
    )
    ap.add_argument("inputs", nargs="+", help="Environment log files or directories containing *.envlog.json")
    ap.add_argument("--json-out", help="Write machine-readable comparison JSON")
    ap.add_argument("--md-out", help="Write Markdown summary")
    ap.add_argument("--csv-out", help="Write flat CSV compatibility matrix")
    ap.add_argument("--baseline", help="Environment label used as performance baseline")
    args = ap.parse_args()

    paths = discover(args.inputs)
    if len(paths) < 2:
        ap.error("need at least two *.envlog.json files")

    logs = [load_environment_log(p) for p in paths]
    try:
        result = compare_logs(logs, baseline_label=args.baseline)
    except ValueError as e:
        ap.error(str(e))
    print(comparison_text(result), end="")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.md_out:
        Path(args.md_out).write_text(comparison_markdown(result), encoding="utf-8")
    if args.csv_out:
        Path(args.csv_out).write_text(comparison_csv(result), encoding="utf-8")

    raise SystemExit(2 if result["status"] == "fail" else 0)

if __name__ == "__main__":
    main()
