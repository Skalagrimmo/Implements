import json
from pathlib import Path
from .scene import tile_id_grid, flatten_grid, scene_summary
from .serialization import to_plain, write_lua_return

COLLISION_IDS={"walk":0,"solid":1,"hazard":2,"portal":3}


def _write_json(data,out_path):
    p=Path(out_path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(to_plain(data),indent=2,ensure_ascii=False,sort_keys=True),encoding="utf-8")
    return p


def scene_payload(scene):
    payload=to_plain(scene)
    payload["summary"]=scene_summary(scene)
    payload["tile_ids"]={
        "ground":tile_id_grid(scene,"ground"),
        "overlay":tile_id_grid(scene,"overlay"),
    }
    return payload


def export_scene_json(scene,out_path):
    return _write_json(scene_payload(scene),out_path)


def export_scene_tiled_like(scene,out_path):
    w,h=scene["width"],scene["height"]
    ground=tile_id_grid(scene,"ground")
    overlay=tile_id_grid(scene,"overlay")
    collision=[[COLLISION_IDS.get(v,255) for v in row] for row in scene["collision"]]
    objects=[o.to_dict() if hasattr(o,"to_dict") else dict(o) for o in scene.get("objects",[])]
    tiled_objects=[]; oid=1
    for o in objects:
        tiled_objects.append({
            "id":oid,"name":o["kind"],"type":"asset",
            "x":o["x"]*scene["tile_size"],"y":o["y"]*scene["tile_size"],
            "point":True,
            "properties":[
                {"name":"layer","type":"string","value":o.get("layer","objects")},
                {"name":"note","type":"string","value":o.get("note","")},
            ],
        }); oid+=1
    for e in scene.get("encounters",[]):
        tiled_objects.append({"id":oid,"name":e["kind"],"type":"encounter","x":e["x"]*scene["tile_size"],"y":e["y"]*scene["tile_size"],"point":True,"properties":[{"name":"tier","type":"int","value":e.get("tier",1)}]}); oid+=1
    for f in scene.get("finds",[]):
        tiled_objects.append({"id":oid,"name":f["kind"],"type":"find","x":f["x"]*scene["tile_size"],"y":f["y"]*scene["tile_size"],"point":True,"properties":[{"name":"rarity","type":"string","value":f.get("rarity","common")}]}); oid+=1
    for ho in scene.get("hollows",[]):
        tiled_objects.append({"id":oid,"name":ho["kind"],"type":"hollow","x":ho["x"]*scene["tile_size"],"y":ho["y"]*scene["tile_size"],"width":ho["w"]*scene["tile_size"],"height":ho["h"]*scene["tile_size"],"properties":[{"name":"secret","type":"bool","value":bool(ho.get("secret"))}]}); oid+=1
    sx,sy=scene["spawn"]["x"],scene["spawn"]["y"]
    tiled_objects.append({"id":oid,"name":"player_spawn","type":"spawn","x":sx*scene["tile_size"],"y":sy*scene["tile_size"],"point":True}); oid+=1

    tiled={
        "type":"map","orientation":"orthogonal","renderorder":"right-down",
        "width":w,"height":h,"tilewidth":scene["tile_size"],"tileheight":scene["tile_size"],
        "infinite":False,
        "properties":[{"name":"biome","type":"string","value":scene.get("kind","")},{"name":"seed","type":"int","value":int(scene.get("seed",0))}],
        "layers":[
            {"type":"tilelayer","name":"ground","width":w,"height":h,"data":flatten_grid(ground)},
            {"type":"tilelayer","name":"overlay","width":w,"height":h,"data":flatten_grid(overlay)},
            {"type":"tilelayer","name":"collision","width":w,"height":h,"data":flatten_grid(collision)},
            {"type":"objectgroup","name":"entities","objects":tiled_objects},
        ],
    }
    return _write_json(tiled,out_path)


def export_scene_lua(scene,out_path):
    return write_lua_return(scene_payload(scene),out_path)
