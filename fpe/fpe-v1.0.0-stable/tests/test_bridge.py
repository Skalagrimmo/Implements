import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fpe.bridge import BridgeError, build_projection, pixelgen_world_fingerprint, projection_fingerprint, validate_projection

DATA = ROOT / "data" / "pixelgen_1_0"
WORLD = json.loads((DATA / "world.json").read_text(encoding="utf-8"))
INITIAL = json.loads((DATA / "initial-state.json").read_text(encoding="utf-8"))
AFTER = json.loads((DATA / "after-state.json").read_text(encoding="utf-8"))


def must_fail(world, state):
    try:
        build_projection(world, state)
    except BridgeError:
        return
    raise AssertionError("expected BridgeError")


def main():
    p = build_projection(WORLD, INITIAL)
    assert not validate_projection(p)
    assert p["summary"]["cluster_count"] == 30
    assert p["summary"]["bud_count"] == 120
    assert p["source"]["dimensions"] == [6, 5]
    assert p["source"]["seed"] == 7301
    assert p["source"]["state_revision"] == 0
    assert p["schema"] == "fpe.pixelgen_hierarchy/0.6.0"
    assert p["mode"] == "read_only_hierarchical_projection"
    assert p["hierarchy"] == {
        "schema": "fpe.view_hierarchy/0.6.0",
        "levels": ["world", "cluster", "bud", "geometry"],
        "initial_detail": "cluster_proxy",
        "expansion_state_owner": "viewer",
        "semantic_effect": "none",
    }
    assert p["source"]["pixelgen_world_fingerprint"] == "ff06afa542ab7ddc1f8d142cb979e2f8f2fa78023ce3bd049bc5b36615ba072a"
    assert pixelgen_world_fingerprint(WORLD) == p["source"]["pixelgen_world_fingerprint"]
    assert projection_fingerprint(p) == p["projection_fingerprint"]
    assert p == build_projection(WORLD, INITIAL)

    # Topology front_ids are preserved exactly sector-by-sector.
    topo = {(x["sx"], x["sy"]): x for x in WORLD["influence_topology"]["sectors"]}
    for c in p["clusters"]:
        assert c["source"]["front_ids"] == topo[tuple(c["sector"])]["front_ids"]
        assert len(c["buds"]) == 4
        assert all(b["type"] in ("STRAIGHT", "CURVED") for b in c["buds"])

    # Dynamic after-state changes the projection deterministically without
    # changing PixelGen world identity or cluster/bud counts.
    p2 = build_projection(WORLD, AFTER)
    assert p2["source"]["state_revision"] == 3
    assert p2["source"]["pixelgen_world_fingerprint"] == p["source"]["pixelgen_world_fingerprint"]
    assert p2["summary"]["cluster_count"] == 30 and p2["summary"]["bud_count"] == 120
    assert p2["projection_fingerprint"] != p["projection_fingerprint"]
    changed = [a["id"] for a, b in zip(p["clusters"], p2["clusters"]) if a != b]
    assert changed, "after-state should change at least one sector projection"

    bad = copy.deepcopy(INITIAL); bad["source_world"]["seed"] = 7302; must_fail(WORLD, bad)
    bad = copy.deepcopy(INITIAL); bad["source_world"]["dimensions"] = [5, 6]; must_fail(WORLD, bad)
    bad = copy.deepcopy(INITIAL); bad["source_world"]["fingerprint"] = "0" * 64; must_fail(WORLD, bad)
    badw = copy.deepcopy(WORLD); badw["sectors"] = badw["sectors"][:-1]; must_fail(badw, INITIAL)

    q = copy.deepcopy(p); q["clusters"][0]["projection"]["cohesion"] = 9
    assert validate_projection(q)
    q = copy.deepcopy(p); q["hierarchy"]["semantic_effect"] = "mutation"
    q["projection_fingerprint"] = projection_fingerprint(q)
    assert "hierarchy authority invalid" in validate_projection(q)
    print("FPE v0.6 bridge regression: PASS")
    print("clusters=30 buds=120 changed_after_state=" + str(len(changed)))
    print("world_fp=" + p["source"]["pixelgen_world_fingerprint"])
    print("projection_fp=" + p["projection_fingerprint"])


if __name__ == "__main__":
    main()
