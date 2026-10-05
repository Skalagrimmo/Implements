import json
from pathlib import Path
from .serialization import to_plain, write_lua_return


def export_world_json(world,out_path):
    p=Path(out_path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(to_plain(world),indent=2,ensure_ascii=False,sort_keys=True),encoding="utf-8")
    return p


def export_world_lua(world,out_path):
    # Full world export, including every sector's scene, links, encounters/finds/hollows.
    return write_lua_return(to_plain(world),out_path)
