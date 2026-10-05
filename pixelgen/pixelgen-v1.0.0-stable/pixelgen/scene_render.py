from pathlib import Path
from PIL import Image, ImageDraw
from .terrain import generate_terrain
from .compose import composite
from .decals import moss_overlay, paper_wax_overlay
from .silt import generate_silt_overlay
from .structures import generate_cliff, generate_timber_wall, generate_nanolith_shrine, generate_printing_press_altar, generate_mask_cross, generate_printing_cathedral, generate_silt_spire
from .props import generate_prop
from .scene_structure import STYLE_BY_BIOME

STRUCTURE_TILE_OFFSET = {
    "nanolith_shrine": (0, -2),
    "printing_press_altar": (0, -2),
    "mask_cross": (0, -3),
    "printing_cathedral": (0, -4),
    "silt_spire": (0, -4),
    "cliff_straight": (0, -2),
}


class RenderAssetCache:
    """Small deterministic variant pool for preview rendering.

    Exact rendering keeps the historical per-cell seed behavior. Fast rendering
    maps those seeds into a bounded pool of pre-rendered visual variants. This
    changes PNG cosmetics only; semantic world/state data is untouched.
    """
    def __init__(self, profile, variants=8):
        self.profile = profile
        self.variants = max(1, int(variants))
        self.tiles = {}
        self.structures = {}
        self.props = {}

    def _variant(self, seed):
        return int(seed) % self.variants

    def tile(self, material, seed, overlay=None, path_visual="chapel"):
        v=self._variant(seed)
        key=(material, overlay, path_visual, v)
        if key not in self.tiles:
            stable_seed = 910_000 + v * 104729
            self.tiles[key] = render_tile(
                material, self.profile, seed=stable_seed, overlay=overlay,
                path_visual=path_visual,
            )
        return self.tiles[key]

    def structure(self, kind, seed):
        v=self._variant(seed)
        key=(kind,v)
        if key not in self.structures:
            self.structures[key]=_structure_image(kind,self.profile,920_000+v*104729)
        return self.structures[key]

    def prop(self, kind, seed):
        v=self._variant(seed)
        key=(kind,v)
        if key not in self.props:
            self.props[key]=_prop_image(kind,self.profile,930_000+v*104729)
        return self.props[key]

def render_tile(material, profile, seed=0, overlay=None, path_visual="chapel"):
    base = generate_terrain(material if material in ("peat","pine","chapel","water","ice") else "peat", profile, seed=seed, variant_index=0).convert("RGBA")
    if material == "path":
        # v0.7.1: path is a navigation token; its visible material is biome-specific.
        visual = path_visual if path_visual in ("peat","pine","chapel","water","ice") else "chapel"
        base = generate_terrain(visual, profile, seed=seed+77, variant_index=1).convert("RGBA")
    if overlay == "moss":
        base = composite(base, moss_overlay(profile, seed=seed, variant_index=0, density=0.12))
    elif overlay == "silt":
        base = composite(base, generate_silt_overlay(profile, seed=seed, variant_index=0, density=0.20))
    return base

def _structure_image(kind, profile, seed):
    if kind.startswith("cliff_"):
        return generate_cliff(profile, seed, kind.replace("cliff_", ""))
    if kind.startswith("wall_"):
        return generate_timber_wall(profile, seed, kind.replace("wall_", ""))
    if kind == "nanolith_shrine":
        return generate_nanolith_shrine(profile, seed)
    if kind == "printing_press_altar":
        return generate_printing_press_altar(profile, seed)
    if kind == "mask_cross":
        return generate_mask_cross(profile, seed)
    if kind == "printing_cathedral":
        return generate_printing_cathedral(profile, seed)
    if kind == "silt_spire":
        return generate_silt_spire(profile, seed)
    return None

def _prop_image(kind, profile, seed):
    return generate_prop(profile, seed, kind)

def render_scene(scene, profile, cache=None):
    ts = scene["tile_size"]
    wpx = scene["width"] * ts
    hpx = scene["height"] * ts
    img = Image.new("RGBA", (wpx, hpx), (26,26,30,255))

    # v0.7.2 ecotone adapters may visually inherit a neighboring route material.
    structural_meta = scene.get("structural_grammar",{})
    ecotone_visuals = {}
    for adapter in structural_meta.get("ecotone_adapters",[]):
        neighbor = adapter.get("neighbor_biome")
        neighbor_visual = STYLE_BY_BIOME.get(neighbor,{}).get(
            "path_visual", structural_meta.get("path_visual","chapel")
        )
        for cell in adapter.get("path_cells",[]):
            if isinstance(cell,(list,tuple)) and len(cell)==2:
                ecotone_visuals[(int(cell[0]),int(cell[1]))] = neighbor_visual

    # ground + overlay
    for y in range(scene["height"]):
        for x in range(scene["width"]):
            path_visual = ecotone_visuals.get(
                (x,y),
                structural_meta.get("path_visual","chapel")
            )
            tile_seed = scene["seed"] + y*scene["width"] + x
            if cache is None:
                tile = render_tile(
                    scene["ground"][y][x],
                    profile,
                    seed=tile_seed,
                    overlay=scene["overlay"][y][x],
                    path_visual=path_visual,
                )
            else:
                tile = cache.tile(
                    scene["ground"][y][x], tile_seed,
                    overlay=scene["overlay"][y][x],
                    path_visual=path_visual,
                )
            img.alpha_composite(tile, (x*ts, y*ts))

    # helpful shadow strips for path readability
    draw = ImageDraw.Draw(img)
    grammar_id = scene.get("structural_grammar",{}).get("grammar_id")
    for y in range(scene["height"]):
        for x in range(scene["width"]):
            if scene["ground"][y][x] == "path":
                draw.line([(x*ts, y*ts+ts-1), (x*ts+ts-1, y*ts+ts-1)], fill=(0,0,0,80))
                if grammar_id == "ridge_zigzag" and (x+y)%3==0:
                    draw.line((x*ts+3,y*ts+4,x*ts+ts-4,y*ts+ts-5),fill=(210,225,220,65))
                elif grammar_id == "root_branch_network" and (x*3+y)%4==0:
                    draw.line((x*ts+2,y*ts+ts//2,x*ts+ts-3,y*ts+ts//2),fill=(15,28,18,70))
                elif grammar_id == "street_grid":
                    draw.line((x*ts+ts//2,y*ts+2,x*ts+ts//2,y*ts+ts-3),fill=(20,22,25,45))
                elif grammar_id == "axial_cloister" and (x+y)%2==0:
                    draw.rectangle((x*ts+3,y*ts+3,x*ts+ts-4,y*ts+ts-4),outline=(220,210,190,35))
                if (x,y) in ecotone_visuals:
                    # Thin glow marks a route cell that belongs to a regional transition adapter.
                    draw.rectangle(
                        (x*ts+2,y*ts+2,x*ts+ts-3,y*ts+ts-3),
                        outline=(82,229,197,42)
                    )

    # objects sorted by y
    objs = [o.to_dict() if hasattr(o, "to_dict") else o for o in scene["objects"]]
    objs = sorted(objs, key=lambda o: (o["y"], o["x"], o["kind"]))

    for idx, obj in enumerate(objs):
        kind = obj["kind"]
        seed = scene["seed"] + 10000 + idx * 101
        if kind.startswith("cliff_") or kind.startswith("wall_") or kind in ("nanolith_shrine", "printing_press_altar", "mask_cross", "printing_cathedral", "silt_spire"):
            sp = _structure_image(kind, profile, seed) if cache is None else cache.structure(kind, seed)
            if sp is None:
                continue
            offx, offy = STRUCTURE_TILE_OFFSET.get(kind, (0, -1))
            px = obj["x"] * ts + offx * ts
            py = obj["y"] * ts + offy * ts
            img.alpha_composite(sp, (px, py))
        else:
            sp = _prop_image(kind, profile, seed) if cache is None else cache.prop(kind, seed)
            px = obj["x"] * ts
            py = obj["y"] * ts + (ts - sp.height)
            img.alpha_composite(sp, (px, py))

    # Encounter markers (placeholder silhouettes until sprite grammar lands).
    encounters = scene.get("encounters", [])
    if encounters:
        for e in encounters:
            ex = e["x"] * ts + 4
            ey = e["y"] * ts + 2
            base = {
                "striga": (90,90,98,255),
                "zealot": (74,38,38,255),
                "larva": (94,50,80,255),
                "silt_construct": (32,70,66,255),
            }.get(e["kind"], (90,90,98,255))
            draw.rectangle((ex+2, ey+6, ex+10, ey+14), fill=base)
            draw.rectangle((ex+4, ey+2, ex+8, ey+7), fill=(217,200,169,255))
            if e["kind"] in ("striga","silt_construct"):
                draw.line((ex+3, ey+10, ex+11, ey+10), fill=(82,229,197,255))
    else:
        ex = scene["enemy_spawn"]["x"] * ts + 4
        ey = scene["enemy_spawn"]["y"] * ts + 2
        draw.rectangle((ex+2, ey+6, ex+10, ey+14), fill=(90,90,98,255))
        draw.rectangle((ex+4, ey+2, ex+8, ey+7), fill=(217,200,169,255))

    # Find markers.
    for f in scene.get("finds", []):
        fx = f["x"]*ts + ts//2
        fy = f["y"]*ts + ts//2
        c = (242,227,198,255) if f.get("rarity") == "common" else (82,229,197,255)
        draw.rectangle((fx-2,fy-2,fx+2,fy+2), fill=c)

    # v0.6 traversal ability pickups.
    ability_colors = {
        "freeze_water": (126, 190, 205, 255),
        "wall_run": (196, 151, 90, 255),
        "high_jump": (217, 200, 169, 255),
        "nano_bridge": (82, 229, 197, 255),
    }
    for p in scene.get("ability_pickups", []):
        cx = p["x"]*ts + ts//2
        cy = p["y"]*ts + ts//2
        c = ability_colors.get(p["ability"], (242,227,198,255))
        draw.polygon([(cx,cy-4),(cx+4,cy),(cx,cy+4),(cx-4,cy)], fill=c)

    # Optional traversal secrets.
    for s in scene.get("secrets", []):
        cx = s["x"]*ts + ts//2
        cy = s["y"]*ts + ts//2
        draw.rectangle((cx-3,cy-3,cx+3,cy+3), outline=(82,229,197,220))

    # Link gate markers. Open links remain visually unobtrusive.
    for g in scene.get("gates", []):
        if g.get("state") == "open":
            continue
        cx = g["x"]*ts + ts//2
        cy = g["y"]*ts + ts//2
        if g.get("state") == "sealed":
            c = (120,120,125,220)
        elif g.get("state") == "secret":
            c = (82,229,197,235)
        else:
            c = ability_colors.get(g.get("requires"), (196,151,90,235))
        draw.line((cx-5,cy-5,cx+5,cy+5), fill=c, width=2)
        draw.line((cx+5,cy-5,cx-5,cy+5), fill=c, width=2)

    # spawn marker
    sx = scene["spawn"]["x"] * ts + ts//2
    sy = scene["spawn"]["y"] * ts + ts//2
    draw.ellipse((sx-3, sy-3, sx+3, sy+3), fill=(242,227,198,220))

    return img
