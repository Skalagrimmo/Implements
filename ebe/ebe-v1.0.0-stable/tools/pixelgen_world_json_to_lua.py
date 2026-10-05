#!/usr/bin/env python3
"""Convert a PixelGen world JSON into a Lua table consumable by EBE v0.5.

By default it keeps only the network-synthesis fields, making a much smaller
fixture than the full scene/world export.
"""
from __future__ import annotations
import argparse, json, math, re
from pathlib import Path

LUA_KEYWORDS=set("and break do else elseif end false for function goto if in local nil not or repeat return then true until while".split())

def compact_world(w: dict) -> dict:
    return {
        "cols":w["cols"],"rows":w["rows"],"seed":w.get("seed"),"generator":w.get("generator",{}),
        "sectors":[{
            "sx":s["sx"],"sy":s["sy"],"region_id":s.get("region_id"),
            "transition":s.get("transition",False),"links":s.get("links",{})
        } for s in w.get("sectors",[])],
        "landmark_system":w.get("landmark_system",{}),
        "gameplay":{"main_path":w.get("gameplay",{}).get("main_path",[])},
        "geography":{"version":w.get("geography",{}).get("version"),"regions":w.get("geography",{}).get("regions",[])},
        "territory_graph":{"version":w.get("territory_graph",{}).get("version"),"front_sites":w.get("territory_graph",{}).get("front_sites",[])},
        "influence_topology":{"version":w.get("influence_topology",{}).get("version"),"boundary_edges":w.get("influence_topology",{}).get("boundary_edges",[])},
    }

def quote(s: str) -> str:
    return '"'+s.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n').replace('\r','\\r').replace('\t','\\t')+'"'

def scalar(v):
    if v is None: return "nil"
    if v is True: return "true"
    if v is False: return "false"
    if isinstance(v,(int,float)):
        if isinstance(v,float) and not math.isfinite(v): raise ValueError("NaN/Infinity unsupported")
        return repr(v)
    if isinstance(v,str): return quote(v)
    raise TypeError(type(v))

def bare_key(k):
    return isinstance(k,str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*",k) and k not in LUA_KEYWORDS

def encode(v,level=0):
    if not isinstance(v,(dict,list)): return scalar(v)
    pad="  "*level; child="  "*(level+1); out=["{"]
    if isinstance(v,list):
        for x in v: out.append(child+encode(x,level+1)+",")
    else:
        for k in sorted(v,key=lambda x:str(x)):
            key=k if bare_key(k) else "["+scalar(k)+"]"
            out.append(child+str(key)+" = "+encode(v[k],level+1)+",")
    out.append(pad+"}")
    return "\n".join(out)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input",type=Path)
    ap.add_argument("output",type=Path)
    ap.add_argument("--full",action="store_true",help="keep the whole JSON instead of the compact network view")
    args=ap.parse_args()
    world=json.loads(args.input.read_text(encoding="utf-8"))
    payload=world if args.full else compact_world(world)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text("return "+encode(payload)+"\n",encoding="utf-8")
    print(f"Wrote {args.output} ({args.output.stat().st_size} bytes)")

if __name__=="__main__": main()
