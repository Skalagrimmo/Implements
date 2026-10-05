"""Dependency-free public CLI smoke matrix. Uses only stdlib subprocess."""
from pathlib import Path
import subprocess,sys,tempfile,shutil
ROOT=Path(__file__).resolve().parents[1]
PYTHON=sys.executable


def run(args,expect=0):
    p=subprocess.run([PYTHON,'cli.py',*args],cwd=ROOT,capture_output=True,text=True)
    if (p.returncode==0)!=(expect==0):
        raise AssertionError({'args':args,'code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    return p

out=ROOT/'generated'/'_cli_smoke'
if out.exists(): shutil.rmtree(out)
out.mkdir(parents=True)

commands=[
 ['terrain','peat','--count','2','--seed','-7','--out',str(out/'terrain')],
 ['silt','--count','2','--density','0','--out',str(out/'silt0')],
 ['silt','--count','2','--density','1','--out',str(out/'silt1')],
 ['autotile','peat','water','--out',str(out/'a16')],
 ['autotile47','peat','water','--out',str(out/'a47')],
 ['decals','paper','--count','2','--out',str(out/'paper')],
 ['decals','moss','--count','2','--density','0','--out',str(out/'moss')],
 ['structure','cliff_silt','--count','1','--out',str(out/'cliff')],
 ['structure','wall_doorway','--count','1','--out',str(out/'wall')],
 ['structure','nanolith_shrine','--count','1','--out',str(out/'shrine')],
 ['prop','chest','--count','1','--out',str(out/'chest')],
 ['manifest','--out',str(out/'manifest.json')],
 ['scene','silt_marsh','--seed','18','--out',str(out/'scene')],
 ['scene-batch','silt_marsh','--count','2','--out',str(out/'scene_batch')],
 ['biome-scene','frozen_pass','--seed','20','--hollow-chance','0','--out',str(out/'b0')],
 ['biome-scene','dark_forest','--seed','21','--hollow-chance','1','--out',str(out/'b1')],
 ['world','--cols','1','--rows','1','--gap','0','--out',str(out/'w1')],
 ['world','--cols','2','--rows','3','--gap','2','--out',str(out/'w6')],
]
for c in commands: run(c)
run(['preview',str(out/'terrain'),'--scale','2','--columns','2','--output',str(out/'preview.png')])
run(['atlas',str(out/'terrain'),'--columns','2','--padding','1','--output',str(out/'atlas.png')])
run(['validate',str(out/'terrain'),'--floor'])

invalid=[
 ['world','--cols','0','--rows','1'],['world','--cols','13','--rows','1'],
 ['silt','--density','1.1'],['decals','moss','--density','-0.1'],
 ['terrain','peat','--count','0'],['preview','missing','--scale','0'],
 ['biome-scene','silt_marsh','--hollow-chance','2'],
]
for c in invalid: run(c,expect=2)

print(f'CLI smoke PASS: {len(commands)+3} valid commands + {len(invalid)} rejected invalid commands')
