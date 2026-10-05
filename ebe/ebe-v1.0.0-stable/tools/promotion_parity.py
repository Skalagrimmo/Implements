#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, subprocess
from pathlib import Path

def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout

def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def parse_probe(text):
    out={}
    for line in text.splitlines():
        if '=' in line:
            k,v=line.split('=',1); out[k]=v
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--baseline-root', required=True)
    ap.add_argument('--candidate-root', required=True)
    ap.add_argument('--out')
    args=ap.parse_args()
    b=Path(args.baseline_root).resolve(); c=Path(args.candidate_root).resolve()
    demos=['action_request_demo','collective_epistemics_demo','institutional_policy_demo','network_synthesis_demo','information_ecology_demo']
    result={'baseline':str(b),'candidate':str(c),'demos':{},'semantic_probe':{}}
    for name in demos:
        bo=run(['texlua',str(b/'demo'/f'{name}.lua'),str(b)])
        co=run(['texlua',str(c/'demo'/f'{name}.lua'),str(c)])
        result['demos'][name]={'baseline_sha256':sha(bo),'candidate_sha256':sha(co),'identical':bo==co}
        if bo!=co: raise SystemExit(f'parity failure: {name}')
    # Use candidate's probe script against both engines so probe logic itself is identical.
    probe=c/'tools'/'semantic_probe.lua'
    bp=parse_probe(run(['texlua',str(probe),str(b)]))
    cp=parse_probe(run(['texlua',str(probe),str(c)]))
    result['semantic_probe']={'baseline':bp,'candidate':cp,'identical':bp==cp}
    if bp!=cp: raise SystemExit('semantic probe parity failure')
    text=json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n'
    if args.out: Path(args.out).write_text(text,encoding='utf-8')
    print('EBE v0.9.0 -> v1.0.0 semantic promotion parity: PASS')
    print('semantic_hash='+cp['semantic_hash'])
    for name in demos: print(name+'='+result['demos'][name]['candidate_sha256'])

if __name__=='__main__': main()
