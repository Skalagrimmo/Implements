import json
from pathlib import Path
from .serialization import to_plain, write_lua_return
from .progression import simulate_progression

def export_gameplay_json(world, out_path):
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = to_plain(world)
    payload["progression_simulation"] = simulate_progression(world)
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return p

def export_gameplay_lua(world, out_path):
    payload = to_plain(world)
    payload["progression_simulation"] = simulate_progression(world)
    return write_lua_return(payload, out_path)

def export_progression_json(world, out_path):
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "gameplay": to_plain(world["gameplay"]),
        "simulation": simulate_progression(world),
    }
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return p

def export_progression_dot(world, out_path):
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    gp = world["gameplay"]
    lines = [
        "graph PixelGenProgression {",
        '  graph [label="PixelGen v0.7 Progression Graph", labelloc=t];',
        '  node [shape=box];',
    ]
    lookup = {(s["sx"],s["sy"]):s for s in world["sectors"]}
    start = tuple(gp["start_sector"])
    final = tuple(gp["final_sector"])
    for key, sec in sorted(lookup.items(), key=lambda kv:(kv[0][1],kv[0][0])):
        attrs = []
        if key == start:
            attrs.append('style="filled"')
        label = f"{key[0]},{key[1]}\\n{sec['biome']}"
        if key == final:
            label += "\\nFINAL"
        lines.append(f'  "s{key[0]}_{key[1]}" [label="{label}"{"," if attrs else ""}{",".join(attrs)}];')
    handled = set()
    for key, sec in lookup.items():
        for edge, link in sec["links"].items():
            dst = tuple(link["to"])
            pair = tuple(sorted((key,dst)))
            if pair in handled:
                continue
            handled.add(pair)
            meta = link["gameplay"]
            state = meta["state"]
            req = meta.get("requires")
            label = state if not req else f"{state}: {req}"
            style = "dashed" if state in ("sealed","secret") else "solid"
            lines.append(f'  "s{key[0]}_{key[1]}" -- "s{dst[0]}_{dst[1]}" [label="{label}", style="{style}"];')
    lines.append("}")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p
