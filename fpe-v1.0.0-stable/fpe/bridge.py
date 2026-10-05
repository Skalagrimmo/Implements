"""Read-only PixelGen -> FPE projection bridge.

FPE v0.6.0 deliberately does not mutate PixelGen state. It joins the stable
PixelGen semantic world with a matching dynamic-state artifact and emits a
compact deterministic local-cluster plan suitable for FPE renderers.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

FPE_VERSION = "0.6.0"
BRIDGE_VERSION = "0.6.0"
PROJECTION_SCHEMA = "fpe.pixelgen_hierarchy/0.6.0"
BUDS_PER_SECTOR = 4

_VOLATILE_PIXELGEN_TOP_LEVEL = {"progression_simulation", "visual_quality"}
_STATUS_RANK = {"quiet": 0, "active": 1, "tense": 2, "volatile": 3}


class BridgeError(ValueError):
    pass


def _finite_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise BridgeError(f"{name} must be a finite number")
    return float(value)


def _int(value: Any, name: str, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise BridgeError(f"{name} must be an integer")
    if minimum is not None and value < minimum:
        raise BridgeError(f"{name} must be >= {minimum}")
    return value


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _round(v: float) -> float:
    return round(float(v), 6)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def pixelgen_world_fingerprint(world: dict[str, Any]) -> str:
    """Reproduce PixelGen 1.0 semantic-world fingerprint rules.

    This is intentionally tiny and pinned to the PixelGen 1.0 public rule:
    release/schema labels and visual/progression diagnostics do not define the
    semantic world identity.
    """
    data = copy.deepcopy(world)
    for key in _VOLATILE_PIXELGEN_TOP_LEVEL:
        data.pop(key, None)
    data.pop("generator", None)
    data.pop("schema_versions", None)
    gameplay = data.get("gameplay")
    if isinstance(gameplay, dict):
        gameplay.pop("generator_version", None)
    return hashlib.sha256(_canonical_bytes(data)).hexdigest()


def projection_fingerprint(projection: dict[str, Any]) -> str:
    data = copy.deepcopy(projection)
    data.pop("projection_fingerprint", None)
    return hashlib.sha256(_canonical_bytes(data)).hexdigest()


def _sector_key(sx: int, sy: int) -> str:
    return f"{sx},{sy}"


def _territory_index(world: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    tg = world.get("territory_graph") or {}
    for territory in tg.get("territories") or []:
        tid = territory.get("id")
        if not isinstance(tid, str) or not tid:
            raise BridgeError("territory id must be a non-empty string")
        for sector in territory.get("sectors") or []:
            if not (isinstance(sector, list) and len(sector) == 2):
                raise BridgeError(f"invalid sector coordinate in {tid}")
            key = _sector_key(_int(sector[0], "territory sector x", 0), _int(sector[1], "territory sector y", 0))
            if key in result:
                raise BridgeError(f"sector {key} belongs to multiple territories")
            result[key] = tid
    return result


def _topology_index(world: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    topo = world.get("influence_topology") or {}
    for item in topo.get("sectors") or []:
        sx = _int(item.get("sx"), "topology.sx", 0)
        sy = _int(item.get("sy"), "topology.sy", 0)
        key = _sector_key(sx, sy)
        if key in result:
            raise BridgeError(f"duplicate influence topology sector {key}")
        result[key] = item
    return result


def _state_maps(state: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    territories = state.get("territories") or {}
    fronts = state.get("fronts") or {}
    if not isinstance(territories, dict) or not isinstance(fronts, dict):
        raise BridgeError("dynamic state territories/fronts must be objects")
    return territories, fronts


def _validate_source_identity(world: dict[str, Any], state: dict[str, Any]) -> str:
    cols = _int(world.get("cols"), "world.cols", 1)
    rows = _int(world.get("rows"), "world.rows", 1)
    seed = _int(world.get("seed"), "world.seed")
    src = state.get("source_world")
    if not isinstance(src, dict):
        raise BridgeError("state.source_world is required")
    dims = src.get("dimensions")
    if dims != [cols, rows]:
        raise BridgeError(f"state/world dimensions mismatch: {dims!r} != {[cols, rows]!r}")
    if src.get("seed") != seed:
        raise BridgeError("state/world seed mismatch")
    actual_fp = pixelgen_world_fingerprint(world)
    if src.get("fingerprint") != actual_fp:
        raise BridgeError("state.source_world fingerprint does not match world semantics")
    return actual_fp


def _front_context(front_ids: list[str], fronts: dict[str, Any]) -> tuple[float, float, str]:
    tension = 0.0
    activity = 0.0
    status = "quiet"
    for fid in front_ids:
        f = fronts.get(fid)
        if not isinstance(f, dict):
            raise BridgeError(f"state is missing referenced front {fid}")
        tension = max(tension, _finite_number(f.get("tension", 0.0), f"{fid}.tension"))
        activity = max(activity, _finite_number(f.get("activity", 0.0), f"{fid}.activity"))
        st = f.get("status", "quiet")
        if st not in _STATUS_RANK:
            raise BridgeError(f"unknown front status {st!r}")
        if _STATUS_RANK[st] > _STATUS_RANK[status]:
            status = st
    return _clamp(tension), _clamp(activity), status


def _bud_types(tension: float, collapse_bias: float, sector_seed: str) -> list[str]:
    # Morphology is deterministic and driven by state rather than random authority.
    straight_pressure = _clamp(tension * 0.72 + collapse_bias * 0.38)
    straight_count = 1 + int(round(straight_pressure * 3.0))  # 1..4
    straight_count = max(1, min(4, straight_count))
    # Rotate the assignment deterministically so nearby equal-state sectors do
    # not all present the same visual orientation.
    rot = int(hashlib.sha256(sector_seed.encode("utf-8")).hexdigest()[:8], 16) % 4
    types = ["CURVED"] * 4
    for i in range(straight_count):
        types[(i + rot) % 4] = "STRAIGHT"
    return types


def _sector_projection(
    *,
    world_sector: dict[str, Any],
    topology: dict[str, Any],
    territory_id: str | None,
    territories: dict[str, Any],
    fronts: dict[str, Any],
    world_seed: int,
) -> dict[str, Any]:
    sx = _int(world_sector.get("sx"), "sector.sx", 0)
    sy = _int(world_sector.get("sy"), "sector.sy", 0)
    front_ids = topology.get("front_ids") or []
    if not isinstance(front_ids, list) or not all(isinstance(x, str) and x for x in front_ids):
        raise BridgeError(f"sector {sx},{sy} has invalid front_ids")

    # Neutral/contested sectors still get a physical projection.  They use
    # explicit conservative fallback values rather than inventing a territory.
    control = 0.52
    stability = 0.62
    alert = 0.12
    alignment = None
    territory_status = "neutral"
    if territory_id is not None:
        terr = territories.get(territory_id)
        if not isinstance(terr, dict):
            raise BridgeError(f"state is missing referenced territory {territory_id}")
        control = _finite_number(terr.get("control_strength"), f"{territory_id}.control_strength")
        stability = _finite_number(terr.get("stability"), f"{territory_id}.stability")
        alert = _finite_number(terr.get("alert"), f"{territory_id}.alert")
        alignment = terr.get("alignment")
        territory_status = terr.get("status", "stable")

    control01 = _clamp(control / 1.75)
    stability01 = _clamp(stability)
    alert01 = _clamp(alert)
    tension, activity, front_status = _front_context(front_ids, fronts)

    # FPE projection semantics.  These are renderer-facing state variables,
    # never written back into PixelGen by v0.6.
    cohesion = _clamp(0.36 + control01 * 0.38 + stability01 * 0.30 - tension * 0.16)
    breakup_resistance = _clamp(stability01 * 0.78 + control01 * 0.22)
    agitation = _clamp(alert01 * 0.72 + activity * 0.34)
    collapse_bias = _clamp((1.0 - breakup_resistance) * 0.46 + tension * 0.58)
    damage_proxy = _clamp(collapse_bias * 0.68 + (1.0 - cohesion) * 0.28)
    update_rate = _clamp(0.18 + activity * 0.82, 0.18, 1.0)

    seed_key = f"{world_seed}:{sx}:{sy}"
    bud_types = _bud_types(tension, collapse_bias, seed_key)
    offsets = [[-1, -1], [1, -1], [-1, 1], [1, 1]]
    buds = [
        {
            "id": f"sector_{sx}_{sy}_bud_{i}",
            "index": i,
            "type": bud_types[i],
            "offset": offsets[i],
            "seed_key": f"{seed_key}:bud:{i}",
        }
        for i in range(BUDS_PER_SECTOR)
    ]

    corridors = []
    for c in world_sector.get("corridors") or []:
        if isinstance(c, dict) and isinstance(c.get("id"), str):
            corridors.append({"id": c["id"], "kind": c.get("kind"), "role": c.get("role")})

    return {
        "id": f"sector_{sx}_{sy}",
        "sector": [sx, sy],
        "source": {
            "region_id": world_sector.get("region_id"),
            "biome": world_sector.get("biome"),
            "subbiome": world_sector.get("subbiome"),
            "geography_zone": world_sector.get("geography_zone"),
            "territory_id": territory_id,
            "territory_alignment": alignment,
            "territory_status": territory_status,
            "topology_status": topology.get("status"),
            "front_ids": list(front_ids),
            "corridors": corridors,
        },
        "state": {
            "control_strength": _round(control),
            "stability": _round(stability01),
            "alert": _round(alert01),
            "front_tension": _round(tension),
            "front_activity": _round(activity),
            "front_status": front_status,
        },
        "projection": {
            "cohesion": _round(cohesion),
            "breakup_resistance": _round(breakup_resistance),
            "agitation": _round(agitation),
            "collapse_bias": _round(collapse_bias),
            "damage_proxy": _round(damage_proxy),
            "update_rate": _round(update_rate),
        },
        "buds": buds,
    }


def build_projection(world: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(world, dict) or not isinstance(state, dict):
        raise BridgeError("world and state must be JSON objects")
    world_fp = _validate_source_identity(world, state)
    cols = _int(world.get("cols"), "world.cols", 1)
    rows = _int(world.get("rows"), "world.rows", 1)
    seed = _int(world.get("seed"), "world.seed")
    sectors = world.get("sectors")
    if not isinstance(sectors, list) or len(sectors) != cols * rows:
        raise BridgeError("world.sectors count does not match dimensions")

    territory_by_sector = _territory_index(world)
    topology_by_sector = _topology_index(world)
    territories, fronts = _state_maps(state)

    clusters = []
    seen = set()
    for ws in sorted(sectors, key=lambda s: (s.get("sy", -1), s.get("sx", -1))):
        if not isinstance(ws, dict):
            raise BridgeError("world sector entries must be objects")
        sx = _int(ws.get("sx"), "sector.sx", 0)
        sy = _int(ws.get("sy"), "sector.sy", 0)
        if not (0 <= sx < cols and 0 <= sy < rows):
            raise BridgeError(f"sector {sx},{sy} outside world dimensions")
        key = _sector_key(sx, sy)
        if key in seen:
            raise BridgeError(f"duplicate world sector {key}")
        seen.add(key)
        topo = topology_by_sector.get(key)
        if topo is None:
            raise BridgeError(f"missing influence topology for sector {key}")
        clusters.append(
            _sector_projection(
                world_sector=ws,
                topology=topo,
                territory_id=territory_by_sector.get(key),
                territories=territories,
                fronts=fronts,
                world_seed=seed,
            )
        )

    clock = state.get("clock") or {}
    revision = _int(clock.get("revision", 0), "state.clock.revision", 0)
    tick = _int(clock.get("tick", 0), "state.clock.tick", 0)

    projection = {
        "schema": PROJECTION_SCHEMA,
        "fpe_version": FPE_VERSION,
        "bridge_version": BRIDGE_VERSION,
        "mode": "read_only_hierarchical_projection",
        "authority": {
            "objective_state_owner": "PixelGen",
            "geometry_owner": "FPE",
            "writeback": "disabled_in_v0.6",
        },
        "source": {
            "pixelgen_world_fingerprint": world_fp,
            "pixelgen_generator_version": (world.get("generator") or {}).get("version"),
            "pixelgen_state_version": state.get("version"),
            "seed": seed,
            "dimensions": [cols, rows],
            "state_revision": revision,
            "state_tick": tick,
        },
        "layout": {
            "cluster_kind": "pixelgen_sector",
            "buds_per_sector": BUDS_PER_SECTOR,
            "sector_spacing": 10.0,
            "local_bud_offset": 2.15,
        },
        "hierarchy": {
            "schema": "fpe.view_hierarchy/0.6.0",
            "levels": ["world", "cluster", "bud", "geometry"],
            "initial_detail": "cluster_proxy",
            "expansion_state_owner": "viewer",
            "semantic_effect": "none",
        },
        "clusters": clusters,
        "summary": {
            "cluster_count": len(clusters),
            "bud_count": len(clusters) * BUDS_PER_SECTOR,
            "territory_cluster_count": sum(1 for c in clusters if c["source"]["territory_id"] is not None),
            "front_cluster_count": sum(1 for c in clusters if c["source"]["front_ids"]),
            "straight_bud_count": sum(1 for c in clusters for b in c["buds"] if b["type"] == "STRAIGHT"),
            "curved_bud_count": sum(1 for c in clusters for b in c["buds"] if b["type"] == "CURVED"),
        },
    }
    projection["projection_fingerprint"] = projection_fingerprint(projection)
    errors = validate_projection(projection)
    if errors:
        raise BridgeError("generated projection failed validation: " + "; ".join(errors[:20]))
    return projection


def validate_projection(value: Any) -> list[str]:
    """Return diagnostics even for malformed nested JSON; never mutate input."""
    try:
        errors = _validate_projection(value)
        if not isinstance(value, dict):
            return errors
        layout = value.get("layout")
        if not isinstance(layout, dict):
            errors.append("layout must be an object")
        else:
            for key in ("sector_spacing", "local_bud_offset"):
                v = layout.get(key)
                if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0.001 <= v <= 1000000:
                    errors.append("invalid layout." + key)
            if layout.get("buds_per_sector") != 4:
                errors.append("invalid buds_per_sector")
        if layout.get("cluster_kind") != "pixelgen_sector":
            errors.append("invalid layout.cluster_kind")
        authority = value.get("authority")
        if authority != {"objective_state_owner": "PixelGen", "geometry_owner": "FPE", "writeback": "disabled_in_v0.6"}:
            errors.append("invalid authority")
        source = value.get("source", {})
        summary = value.get("summary")
        if not isinstance(summary, dict) or summary.get("cluster_count") != len(value.get("clusters", [])) or summary.get("bud_count") != len(value.get("clusters", [])) * 4:
            errors.append("invalid summary")
        elif isinstance(value.get("clusters"), list):
            clusters_for_summary = value["clusters"]
            try:
                straight = sum(1 for c in clusters_for_summary for b in c["buds"] if b.get("type") == "STRAIGHT")
                curved = sum(1 for c in clusters_for_summary for b in c["buds"] if b.get("type") == "CURVED")
                territory = sum(1 for c in clusters_for_summary if c.get("source", {}).get("territory_id") is not None)
                fronts = sum(1 for c in clusters_for_summary if c.get("source", {}).get("front_ids"))
                expected = {"straight_bud_count": straight, "curved_bud_count": curved, "territory_cluster_count": territory, "front_cluster_count": fronts}
                for key, expected_value in expected.items():
                    actual = summary.get(key)
                    if isinstance(actual, bool) or not isinstance(actual, int) or actual < 0 or actual != expected_value:
                        errors.append("invalid summary." + key)
            except (KeyError, TypeError, AttributeError):
                errors.append("invalid summary structure")
        seed = source.get("seed")
        if isinstance(seed, bool) or not isinstance(seed, int) or not -(2**53-1) <= seed <= 2**53-1:
            errors.append("invalid source.seed")
        for key in ("state_revision", "state_tick"):
            v = source.get(key)
            if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9007199254740991:
                errors.append("invalid source." + key)
        for c in value.get("clusters", []):
            for i, b in enumerate(c.get("buds", [])):
                if b.get("index") != i or b.get("offset") != [[-1,-1],[1,-1],[-1,1],[1,1]][i]:
                    errors.append("invalid bud index/offset")
                if not isinstance(b.get("seed_key"), str) or not b["seed_key"]:
                    errors.append("invalid bud seed")
        return errors
    except (AttributeError, TypeError, ValueError, IndexError, OverflowError):
        return ["malformed projection structure"]


def _validate_projection(value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["projection must be an object"]
    if value.get("schema") != PROJECTION_SCHEMA:
        errors.append("unsupported projection schema")
    if value.get("mode") != "read_only_hierarchical_projection":
        errors.append("v0.6 projection mode must be read_only_hierarchical_projection")
    if value.get("fpe_version") != FPE_VERSION or value.get("bridge_version") != BRIDGE_VERSION:
        errors.append("unsupported bridge/runtime projection version")
    hierarchy = value.get("hierarchy")
    if not isinstance(hierarchy, dict):
        errors.append("hierarchy contract missing")
    else:
        if hierarchy.get("schema") != "fpe.view_hierarchy/0.6.0":
            errors.append("unsupported hierarchy schema")
        if hierarchy.get("levels") != ["world", "cluster", "bud", "geometry"]:
            errors.append("hierarchy levels invalid")
        if hierarchy.get("initial_detail") != "cluster_proxy":
            errors.append("hierarchy initial_detail invalid")
        if hierarchy.get("expansion_state_owner") != "viewer" or hierarchy.get("semantic_effect") != "none":
            errors.append("hierarchy authority invalid")
    source = value.get("source") or {}
    dims = source.get("dimensions")
    if not (isinstance(dims, list) and len(dims) == 2 and all(isinstance(x, int) and not isinstance(x, bool) and 0 < x <= 9007199254740991 for x in dims)):
        errors.append("source dimensions invalid")
        cols = rows = 0
    else:
        cols, rows = dims
    fp = source.get("pixelgen_world_fingerprint")
    if not (isinstance(fp, str) and len(fp) == 64 and all(ch in "0123456789abcdef" for ch in fp)):
        errors.append("source PixelGen fingerprint invalid")
    clusters = value.get("clusters")
    if not isinstance(clusters, list):
        errors.append("clusters must be an array")
        clusters = []
    if cols and rows and len(clusters) != cols * rows:
        errors.append("cluster count does not match dimensions")
    ids = set()
    coords = set()
    bud_ids = set()
    for c in clusters:
        if not isinstance(c, dict):
            errors.append("cluster entry must be an object")
            continue
        cid = c.get("id")
        if not isinstance(cid, str) or not cid or cid in ids:
            errors.append("cluster id missing or duplicate")
        else:
            ids.add(cid)
        sector = c.get("sector")
        if not (isinstance(sector, list) and len(sector) == 2 and all(isinstance(x, int) and not isinstance(x, bool) for x in sector)):
            errors.append(f"{cid}: invalid sector coordinate")
        else:
            coord = tuple(sector)
            if coord in coords:
                errors.append(f"{cid}: duplicate sector coordinate")
            coords.add(coord)
            if cols and rows and not (0 <= coord[0] < cols and 0 <= coord[1] < rows):
                errors.append(f"{cid}: sector coordinate outside dimensions")
            if cid != f"sector_{coord[0]}_{coord[1]}":
                errors.append(f"{cid}: noncanonical cluster id")
        state = c.get("state") or {}
        proj = c.get("projection") or {}
        csource = c.get("source") or {}
        if not isinstance(state, dict) or not isinstance(proj, dict) or not isinstance(csource, dict):
            errors.append(f"{cid}: invalid cluster objects")
            state = state if isinstance(state, dict) else {}
            proj = proj if isinstance(proj, dict) else {}
            csource = csource if isinstance(csource, dict) else {}
        if state.get("front_status") not in ("quiet", "active", "tense", "volatile"):
            errors.append(f"{cid}: invalid front_status")
        front_ids = csource.get("front_ids")
        if not isinstance(front_ids, list) or any(not isinstance(x, str) or not x for x in front_ids):
            errors.append(f"{cid}: invalid front_ids")
        territory_id = csource.get("territory_id")
        if territory_id is not None and (not isinstance(territory_id, str) or not territory_id):
            errors.append(f"{cid}: invalid territory_id")
        for key in ("stability", "alert", "front_tension", "front_activity"):
            v = state.get(key)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1:
                errors.append(f"{cid}: state.{key} must be finite 0..1")
        ctrl = state.get("control_strength")
        if isinstance(ctrl, bool) or not isinstance(ctrl, (int, float)) or not math.isfinite(ctrl) or not 0 <= ctrl <= 1.75:
            errors.append(f"{cid}: state.control_strength must be finite 0..1.75")
        for key in ("cohesion", "breakup_resistance", "agitation", "collapse_bias", "damage_proxy", "update_rate"):
            v = proj.get(key)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1:
                errors.append(f"{cid}: projection.{key} must be finite 0..1")
        buds = c.get("buds")
        if not isinstance(buds, list) or len(buds) != BUDS_PER_SECTOR:
            errors.append(f"{cid}: expected {BUDS_PER_SECTOR} buds")
            continue
        offsets = [[-1, -1], [1, -1], [-1, 1], [1, 1]]
        for i, b in enumerate(buds):
            if not isinstance(b, dict):
                errors.append(f"{cid}: bud must be an object")
                continue
            bid = b.get("id")
            if not isinstance(bid, str) or not bid or bid in bud_ids:
                errors.append(f"{cid}: bud id missing or duplicate")
            else:
                bud_ids.add(bid)
            if bid != f"{cid}_bud_{i}" or b.get("index") != i or b.get("offset") != offsets[i]:
                errors.append(f"{cid}: noncanonical bud identity")
            if not isinstance(b.get("seed_key"), str) or not b.get("seed_key"):
                errors.append(f"{cid}: invalid bud seed")
            if b.get("type") not in ("STRAIGHT", "CURVED"):
                errors.append(f"{cid}: unsupported bud type")
    expected_fp = value.get("projection_fingerprint")
    if not (isinstance(expected_fp, str) and len(expected_fp) == 64):
        errors.append("projection_fingerprint missing or invalid")
    else:
        try:
            actual = projection_fingerprint(value)
            if actual != expected_fp:
                errors.append("projection_fingerprint mismatch")
        except (TypeError, ValueError):
            errors.append("projection is not canonical finite JSON")
    return errors


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f, parse_constant=lambda s: (_ for _ in ()).throw(BridgeError(f"non-finite JSON constant: {s}")))


def write_json(value: Any, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    path.write_text(text, encoding="utf-8")
