from collections import deque
from .rng import SeededRNG
from .abilities import ABILITY_ORDER, ability_info, validate_ability_count
from .navigation import exit_cell
from .placement import occupied_cells, reserved_cells

OPPOSITE = {"N":"S","S":"N","E":"W","W":"E"}

def _sector_key(s):
    return (s["sx"], s["sy"])

def _lookup(world):
    return {_sector_key(s): s for s in world["sectors"]}

def _neighbors(world):
    out = {}
    for s in world["sectors"]:
        key = _sector_key(s)
        out[key] = []
        for edge, link in s["links"].items():
            out[key].append((edge, tuple(link["to"])))
        out[key].sort(key=lambda item: (item[1][1], item[1][0], item[0]))
    return out

def _shuffle(items, rng):
    items = list(items)
    for i in range(len(items)-1, 0, -1):
        j = rng.randint(0, i)
        items[i], items[j] = items[j], items[i]
    return items

def build_spanning_tree(world, seed=0, start=(0,0)):
    lookup = _lookup(world)
    if start not in lookup:
        raise ValueError("gameplay start sector is outside the world")
    neigh = _neighbors(world)
    rng = SeededRNG(int(seed) + 1_600_000)

    parent = {start: None}
    parent_edge = {}
    order = []
    stack = [start]

    # Randomized DFS gives a long, deterministic backbone while preserving branches.
    while stack:
        cur = stack[-1]
        if cur not in order:
            order.append(cur)
        unvisited = [(edge,n) for edge,n in _shuffle(neigh[cur], rng) if n not in parent]
        if not unvisited:
            stack.pop()
            continue
        edge, nxt = unvisited[0]
        parent[nxt] = cur
        parent_edge[nxt] = edge
        stack.append(nxt)

    if len(parent) != len(world["sectors"]):
        raise RuntimeError("could not build a spanning tree across all sectors")

    children = {k: [] for k in parent}
    for node, par in parent.items():
        if par is not None:
            children[par].append(node)

    depth = {start: 0}
    q = deque([start])
    while q:
        cur = q.popleft()
        for child in children[cur]:
            depth[child] = depth[cur] + 1
            q.append(child)

    farthest = max(depth, key=lambda k: (depth[k], k[1], k[0]))
    main_path = []
    cur = farthest
    while cur is not None:
        main_path.append(cur)
        cur = parent[cur]
    main_path.reverse()

    tree_edges = set()
    for node, par in parent.items():
        if par is not None:
            tree_edges.add(frozenset((node, par)))

    return {
        "start": start,
        "parent": parent,
        "parent_edge": parent_edge,
        "children": children,
        "depth": depth,
        "main_path": main_path,
        "tree_edges": tree_edges,
    }

def _free_cells(scene):
    blocked = occupied_cells(scene) | reserved_cells(scene)
    for e in scene.get("encounters", []):
        blocked.add((e["x"], e["y"]))
    for f in scene.get("finds", []):
        blocked.add((f["x"], f["y"]))
    for h in scene.get("hollows", []):
        for y in range(h["y"], h["y"] + h["h"]):
            for x in range(h["x"], h["x"] + h["w"]):
                blocked.add((x,y))
    for p in scene.get("ability_pickups", []):
        blocked.add((p["x"], p["y"]))
    for s in scene.get("secrets", []):
        blocked.add((s["x"], s["y"]))
    sx, sy = scene["spawn"]["x"], scene["spawn"]["y"]
    cells = []
    for y in range(scene["height"]):
        for x in range(scene["width"]):
            if scene["collision"][y][x] != "walk" or (x,y) in blocked:
                continue
            if (x,y) == (sx,sy):
                continue
            cells.append((x,y))
    return cells

def _choose_free_cell(scene, seed, salt=0):
    cells = _free_cells(scene)
    if not cells:
        # Spawn is guaranteed walkable by v0.5 Hardened; only use it as last resort.
        return (scene["spawn"]["x"], scene["spawn"]["y"])
    rng = SeededRNG(int(seed) + 1_700_000 + salt * 1009)
    return cells[rng.randint(0, len(cells)-1)]

def _edge_between(world, a, b):
    lookup = _lookup(world)
    sec = lookup[a]
    for edge, link in sec["links"].items():
        if tuple(link["to"]) == b:
            return edge
    raise KeyError(f"no world edge between {a} and {b}")

def _set_link_gameplay(world, a, b, state, requires=None, gate_id=None, gate_kind=None):
    lookup = _lookup(world)
    ea = _edge_between(world, a, b)
    eb = OPPOSITE[ea]
    la = lookup[a]["links"][ea]
    lb = lookup[b]["links"][eb]
    payload = {
        "state": state,
        "requires": requires,
        "gate_id": gate_id,
        "gate_kind": gate_kind,
    }
    la["gameplay"] = dict(payload)
    lb["gameplay"] = dict(payload)

    # Per-scene descriptors make runtime integration independent from world graph traversal.
    for sector, edge, link in ((lookup[a], ea, la), (lookup[b], eb, lb)):
        scene = sector["scene"]
        cell = exit_cell(scene, edge, link["coord"])
        desc = {
            "edge": edge,
            "coord": link["coord"],
            "x": cell[0], "y": cell[1],
            "state": state,
            "requires": requires,
            "gate_id": gate_id,
            "gate_kind": gate_kind,
            "to": list(link["to"]),
        }
        scene.setdefault("gates", []).append(desc)

def _tree_path(tree, a, b):
    parent = tree["parent"]
    ancestors = {}
    cur = a
    d = 0
    while cur is not None:
        ancestors[cur] = d
        cur = parent[cur]
        d += 1
    cur = b
    tail = []
    while cur not in ancestors:
        tail.append(cur)
        cur = parent[cur]
    lca = cur
    head = []
    cur = a
    while cur != lca:
        head.append(cur)
        cur = parent[cur]
    head.append(lca)
    return head + list(reversed(tail))

def _gate_requirement_on_tree_path(world, tree, path):
    abilities = []
    lookup = _lookup(world)
    order_index = {a:i for i,a in enumerate(ABILITY_ORDER)}
    for a,b in zip(path, path[1:]):
        edge = _edge_between(world,a,b)
        gp = lookup[a]["links"][edge].get("gameplay", {})
        req = gp.get("requires")
        if req:
            abilities.append(req)
    if not abilities:
        return None
    return max(abilities, key=lambda a: order_index.get(a, -1))

def _main_path_gate_positions(edge_count, gate_count):
    if gate_count <= 0:
        return []
    # Spread gates over the path and avoid placing the first gate at edge zero when possible.
    positions = []
    for i in range(gate_count):
        pos = round((i + 1) * edge_count / (gate_count + 1))
        pos = max(1 if edge_count > 1 else 0, min(edge_count - 1, pos))
        while pos in positions and pos + 1 < edge_count:
            pos += 1
        while pos in positions and pos - 1 >= 0:
            pos -= 1
        positions.append(pos)
    return sorted(set(positions))

def apply_gameplay_grammar(world, seed=0, ability_count=4):
    ability_count = validate_ability_count(ability_count)
    if not world.get("sectors"):
        raise ValueError("world has no sectors")

    start = (0,0)
    tree = build_spanning_tree(world, seed=seed, start=start)
    main_path = tree["main_path"]
    edge_count = max(0, len(main_path)-1)
    effective = min(ability_count, edge_count)
    abilities = ABILITY_ORDER[:effective]
    gate_positions = _main_path_gate_positions(edge_count, effective)
    # If a very short path collapsed duplicate positions, use only the achievable count.
    abilities = abilities[:len(gate_positions)]
    effective = len(abilities)

    # Initialize clean gameplay metadata.
    for s in world["sectors"]:
        s["scene"]["gates"] = []
        s["scene"]["ability_pickups"] = []
        s["scene"]["secrets"] = []
        for edge, link in s["links"].items():
            link.pop("gameplay", None)

    # Tree edges are the guaranteed traversable topology; non-tree edges begin sealed.
    handled = set()
    lookup = _lookup(world)
    for s in world["sectors"]:
        a = _sector_key(s)
        for edge, link in s["links"].items():
            b = tuple(link["to"])
            key = frozenset((a,b))
            if key in handled:
                continue
            handled.add(key)
            if key in tree["tree_edges"]:
                _set_link_gameplay(world, a, b, "open")
            else:
                _set_link_gameplay(world, a, b, "sealed", gate_kind="sealed_passage")

    gates = []
    pickups = []
    gate_by_tree_edge = {}

    for index, (ability, pos) in enumerate(zip(abilities, gate_positions), start=1):
        a = main_path[pos]
        b = main_path[pos+1]
        info = ability_info(ability)
        gate_id = f"gate_{index:02d}_{ability}"
        _set_link_gameplay(world, a, b, "gated", requires=ability, gate_id=gate_id, gate_kind=info["gate_kind"])
        gate_by_tree_edge[frozenset((a,b))] = ability

        # Place the ability in the sector immediately before the gate.
        pickup_sector = a
        scene = lookup[pickup_sector]["scene"]
        px, py = _choose_free_cell(scene, seed, salt=100 + index)
        pickup = {
            "id": f"ability_{index:02d}_{ability}",
            "ability": ability,
            "x": px, "y": py,
            "stage": index,
        }
        scene["ability_pickups"].append(pickup)
        pickups.append({"sector": list(pickup_sector), **pickup})
        gates.append({
            "id": gate_id,
            "ability": ability,
            "kind": info["gate_kind"],
            "from": list(a),
            "to": list(b),
            "main_path_edge": pos,
        })

    # Convert selected non-tree edges into late-unlocking shortcuts.
    shortcuts = []
    handled = set()
    shortcut_index = 0
    for s in world["sectors"]:
        a = _sector_key(s)
        for edge, link in s["links"].items():
            b = tuple(link["to"])
            key = frozenset((a,b))
            if key in handled or key in tree["tree_edges"]:
                continue
            handled.add(key)
            path = _tree_path(tree, a, b)
            req = _gate_requirement_on_tree_path(world, tree, path)
            if not req:
                continue
            shortcut_index += 1
            sid = f"shortcut_{shortcut_index:02d}_{req}"
            kind = ability_info(req)["gate_kind"]
            _set_link_gameplay(world, a, b, "secret", requires=req, gate_id=sid, gate_kind=kind)
            shortcuts.append({
                "id": sid,
                "requires": req,
                "from": list(a),
                "to": list(b),
                "tree_distance": len(path)-1,
            })

    # Ability-based local secrets. They do not block critical progression.
    secrets = []
    for index, ability in enumerate(abilities, start=1):
        # Place a secret one step after its corresponding gate when possible.
        gate_pos = gate_positions[index-1]
        sector_key = main_path[min(len(main_path)-1, gate_pos+1)]
        scene = lookup[sector_key]["scene"]
        x,y = _choose_free_cell(scene, seed, salt=500 + index)
        secret = {
            "id": f"secret_{index:02d}_{ability}",
            "requires": ability,
            "x": x, "y": y,
            "reward": ["lore_fragment","sealed_cache","alternate_route","rare_find"][(index-1) % 4],
        }
        scene["secrets"].append(secret)
        secrets.append({"sector": list(sector_key), **secret})

    final_sector = main_path[-1] if main_path else start
    world["gameplay"] = {
        "version": "0.6",
        "generator_version": "1.0.0",
        "start_sector": list(start),
        "final_sector": list(final_sector),
        "requested_ability_count": ability_count,
        "effective_ability_count": effective,
        "ability_order": list(abilities),
        "main_path": [list(k) for k in main_path],
        "tree_edge_count": len(tree["tree_edges"]),
        "gates": gates,
        "ability_pickups": pickups,
        "shortcuts": shortcuts,
        "secrets": secrets,
        "contract": {
            "sealed_links_are_not_traversable": True,
            "open_links_are_traversable": True,
            "gated_links_require_ability": True,
            "secret_links_require_ability": True,
        },
    }
    return world

def _can_traverse(link, abilities):
    gp = link.get("gameplay")
    if not gp:
        return True
    state = gp.get("state", "open")
    if state == "sealed":
        return False
    req = gp.get("requires")
    return (not req) or (req in abilities)

def reachable_sectors(world, abilities=None, start=None):
    abilities = set(abilities or [])
    start = tuple(start or world.get("gameplay", {}).get("start_sector", [0,0]))
    lookup = _lookup(world)
    if start not in lookup:
        return set()
    seen = {start}
    q = deque([start])
    while q:
        cur = q.popleft()
        for edge, link in lookup[cur]["links"].items():
            nxt = tuple(link["to"])
            if nxt in seen or not _can_traverse(link, abilities):
                continue
            seen.add(nxt)
            q.append(nxt)
    return seen

def simulate_progression(world):
    gp = world.get("gameplay")
    if not gp:
        raise ValueError("world has no gameplay grammar")
    lookup = _lookup(world)
    abilities = set()
    collected = set()
    stages = []
    iteration = 0

    while True:
        iteration += 1
        reach = reachable_sectors(world, abilities)
        gained = []
        for key in sorted(reach, key=lambda k:(k[1],k[0])):
            for p in lookup[key]["scene"].get("ability_pickups", []):
                aid = p["ability"]
                pid = p["id"]
                if pid not in collected:
                    collected.add(pid)
                    if aid not in abilities:
                        abilities.add(aid)
                        gained.append(aid)
        stages.append({
            "iteration": iteration,
            "abilities": sorted(abilities),
            "reachable_sectors": [list(k) for k in sorted(reach, key=lambda k:(k[1],k[0]))],
            "gained": gained,
        })
        if not gained:
            break
        if iteration > len(ABILITY_ORDER) + 2:
            raise RuntimeError("progression simulation did not converge")

    final_reach = reachable_sectors(world, abilities)
    final_sector = tuple(gp["final_sector"])
    return {
        "abilities": sorted(abilities),
        "collected_pickups": sorted(collected),
        "reachable_sectors": [list(k) for k in sorted(final_reach, key=lambda k:(k[1],k[0]))],
        "final_sector_reachable": final_sector in final_reach,
        "all_sectors_reachable": len(final_reach) == len(world["sectors"]),
        "stages": stages,
    }
