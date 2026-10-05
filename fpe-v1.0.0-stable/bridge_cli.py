#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

from fpe.bridge import BridgeError, build_projection, load_json, validate_projection, write_json


def main() -> int:
    p = argparse.ArgumentParser(description="FPE v0.6.0 PixelGen -> hierarchical projection bridge")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build deterministic FPE projection")
    b.add_argument("--world", required=True)
    b.add_argument("--state", required=True)
    b.add_argument("--out", required=True)
    v = sub.add_parser("validate", help="validate an FPE projection")
    v.add_argument("projection")
    args = p.parse_args()
    try:
        if args.cmd == "build":
            world = load_json(args.world)
            state = load_json(args.state)
            projection = build_projection(world, state)
            write_json(projection, args.out)
            print(f"FPE projection -> {args.out}")
            print(f"clusters={projection['summary']['cluster_count']} buds={projection['summary']['bud_count']}")
            print(f"fingerprint={projection['projection_fingerprint']}")
            return 0
        value = load_json(args.projection)
        errors = validate_projection(value)
        if errors:
            for e in errors:
                print("ERROR:", e, file=sys.stderr)
            return 2
        print("PASS")
        print("fingerprint=" + value["projection_fingerprint"])
        return 0
    except (BridgeError, OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
