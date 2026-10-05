"""Cross-engine fuzz runner.

Requires a PixelGen 1.0 source tree only for test generation; FPE runtime itself
does not depend on PixelGen Python modules.
"""
import argparse
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fpe.bridge import build_projection, validate_projection


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pixelgen-root", required=True)
    ap.add_argument("--worlds", type=int, default=48)
    ap.add_argument("--start", type=int, default=0)
    ns = ap.parse_args()
    pg = pathlib.Path(ns.pixelgen_root).resolve()
    sys.path.insert(0, str(pg))
    from pixelgen.runtime_api import load_runtime_profile, generate_semantic_world, initialize_state, apply_event
    from pixelgen.serialization import to_plain

    profile = load_runtime_profile()
    rng = random.Random(500)
    seeds = [rng.randint(-50000, 50000) for _ in range(ns.start + ns.worlds)]
    dims = [(4,3),(6,5),(8,6),(12,12)]
    total_clusters = total_buds = mutated = 0
    fingerprints = set()
    for local_i in range(ns.worlds):
        i = ns.start + local_i
        cols, rows = dims[i % len(dims)]
        seed = seeds[i]
        world = generate_semantic_world(profile, seed=seed, cols=cols, rows=rows)
        state = initialize_state(world)
        p = build_projection(to_plain(world), to_plain(state))
        assert not validate_projection(p)
        assert p == build_projection(to_plain(world), to_plain(state))
        assert p["summary"]["cluster_count"] == cols * rows
        assert p["summary"]["bud_count"] == cols * rows * 4
        total_clusters += cols * rows
        total_buds += cols * rows * 4
        fingerprints.add(p["projection_fingerprint"])

        # Mutate only through PixelGen's authoritative API where possible.
        if state["territories"]:
            tid = sorted(state["territories"])[i % len(state["territories"])]
            sector = next(t["center"] for t in world["territory_graph"]["territories"] if t["id"] == tid)
            event = {"id": f"fuzz_{i}", "event_type": "territory_alert", "target_type": "territory", "target_id": tid, "amount": 0.08, "sector": sector, "source": "fpe_v050_fuzz"}
            nxt = apply_event(world, state, event)
            p2 = build_projection(to_plain(world), to_plain(nxt))
            assert not validate_projection(p2)
            assert p2["source"]["state_revision"] == 1
            assert p2["source"]["pixelgen_world_fingerprint"] == p["source"]["pixelgen_world_fingerprint"]
            mutated += 1
    assert len(fingerprints) == ns.worlds
    print("FPE v0.6 cross-engine fuzz: PASS")
    print(f"start={ns.start} worlds={ns.worlds} mutated={mutated} clusters={total_clusters} buds={total_buds}")


if __name__ == "__main__":
    main()
