#!/usr/bin/env python3
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=[]
for _ in range(10):
    value=subprocess.check_output(['node','tests/v100_trace_cli.js','305419896'],cwd=ROOT,text=True).strip()
    out.append(value)
assert len(set(out))==1, out
print(f'fresh-process determinism PASS: 10/10 identical trace SHA-256 {out[0]}')
