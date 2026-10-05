#!/usr/bin/env python3
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for name in ["fuzz_corruption.js","stress_persistence.js","stress_large_world.js"]:
    subprocess.run(["node","tests/"+name],cwd=root,check=True)
for start in range(0,500,100):
    for mode in ["roundtrip","migration","reject"]:
        subprocess.run(["node","tests/torture_v100.js",mode,str(start),"100"],cwd=root,check=True)
print("All extended v1.0 stress gates PASS")
