#!/usr/bin/env python3
"""Generate frozen-style Python FPE projection vectors for the native C parity test."""
from __future__ import annotations

import copy
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STABLE = ROOT / "fpe-v1.0.0-stable"
sys.path.insert(0, str(STABLE))

from fpe.bridge import projection_fingerprint, validate_projection  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: generate_fingerprint_vectors.py OUTPUT.jsonl", file=sys.stderr)
        return 2
    source = STABLE / "data" / "projections" / "canonical_initial.json"
    base = json.loads(source.read_text(encoding="utf-8"))
    rng = random.Random(12012026)
    edge = [0.0, 0.000001, 0.00001, 0.000099, 0.0001, 0.123456, 0.999999, 1.0]
    output = Path(sys.argv[1])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        for i in range(256):
            projection = copy.deepcopy(base)
            cluster = projection["clusters"][i % len(projection["clusters"])]
            alert = edge[i] if i < len(edge) else round(rng.random(), 6)
            cluster["state"]["alert"] = alert
            cluster["state"]["front_tension"] = round(rng.random(), 6)
            cluster["projection"]["agitation"] = round(rng.random(), 6)
            cluster["projection"]["cohesion"] = round(rng.random(), 6)
            cluster["source"]["biome"] = f"ліс_{i}_🌲"
            projection["projection_fingerprint"] = projection_fingerprint(projection)
            errors = validate_projection(projection)
            if errors:
                raise RuntimeError(f"generated vector {i} failed stable validation: {errors[:5]}")
            stream.write(json.dumps(projection, ensure_ascii=False, separators=(",", ":"), allow_nan=False))
            stream.write("\n")
    print(f"generated {256} Python FPE fingerprint vectors: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
