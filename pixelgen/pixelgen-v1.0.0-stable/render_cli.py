#!/usr/bin/env python3
"""PixelGen optional renderer CLI (package v0.9.2; render API v0.9.1).

Consumes semantic world JSON produced by runtime_cli.py.  This process is the
only CLI path that requires Pillow.
"""
import argparse
import json
from pathlib import Path
from time import perf_counter

from pixelgen.palette import load_profile
from pixelgen.render_api import (
    renderer_status,
    render_world_preview,
    render_diagnostic_bundle,
)

ROOT=Path(__file__).resolve().parent
DEFAULT_PROFILE=ROOT/'profiles'/'techno_animist_gothic.json'


def load_world(path):
    world=json.loads(Path(path).read_text(encoding='utf-8'))
    world.pop('progression_simulation',None)
    return world


def cmd_status(args):
    print(json.dumps(renderer_status(),indent=2,sort_keys=True))


def cmd_world(args):
    world=load_world(args.world)
    profile=load_profile(args.profile)
    t=perf_counter()
    image=render_world_preview(world,profile,gap=args.gap,quality=args.quality)
    path=Path(args.out); path.parent.mkdir(parents=True,exist_ok=True); image.save(path)
    print(f'Render -> {path}')
    print(f'Quality: {args.quality}')
    print(f'Size: {image.size[0]}x{image.size[1]}')
    print(f'Seconds: {perf_counter()-t:.6f}')


def cmd_bundle(args):
    world=load_world(args.world)
    profile=load_profile(args.profile)
    t=perf_counter()
    outputs=render_diagnostic_bundle(world,profile,args.out,quality=args.quality,include_world=not args.no_world)
    print(json.dumps({'quality':args.quality,'seconds':perf_counter()-t,'outputs':outputs},indent=2,sort_keys=True))


def cmd_benchmark(args):
    world=load_world(args.world)
    profile=load_profile(args.profile)
    rows=[]
    for quality in ('exact','fast'):
        times=[]
        for _ in range(args.runs):
            t=perf_counter(); img=render_world_preview(world,profile,gap=args.gap,quality=quality); times.append(perf_counter()-t)
        rows.append({'quality':quality,'runs':times,'mean_seconds':sum(times)/len(times),'size':list(img.size)})
    exact=rows[0]['mean_seconds']; fast=rows[1]['mean_seconds']
    print(json.dumps({'results':rows,'speedup':exact/fast if fast else None},indent=2,sort_keys=True))


def main():
    ap=argparse.ArgumentParser(description='PixelGen v0.9.2 package / render API v0.9.1')
    ap.add_argument('--profile',default=str(DEFAULT_PROFILE))
    sub=ap.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('status'); s.set_defaults(func=cmd_status)
    w=sub.add_parser('world'); w.add_argument('--world',required=True); w.add_argument('--out',required=True); w.add_argument('--quality',choices=('exact','fast'),default='fast'); w.add_argument('--gap',type=int,default=4); w.set_defaults(func=cmd_world)
    b=sub.add_parser('bundle'); b.add_argument('--world',required=True); b.add_argument('--out',required=True,help='output path base'); b.add_argument('--quality',choices=('exact','fast'),default='fast'); b.add_argument('--no-world',action='store_true'); b.set_defaults(func=cmd_bundle)
    m=sub.add_parser('benchmark'); m.add_argument('--world',required=True); m.add_argument('--runs',type=int,default=2); m.add_argument('--gap',type=int,default=4); m.set_defaults(func=cmd_benchmark)
    args=ap.parse_args(); args.func(args)

if __name__=='__main__': main()
