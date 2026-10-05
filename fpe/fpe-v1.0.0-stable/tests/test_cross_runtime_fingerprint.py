import copy, json, pathlib, random, subprocess, sys, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fpe.bridge import projection_fingerprint, validate_projection
base=json.loads((ROOT/'data/projections/canonical_initial.json').read_text(encoding='utf-8'))
rng=random.Random(12012026)
items=[]
edge=[0.0,0.000001,0.00001,0.000099,0.0001,0.123456,0.999999,1.0]
for i in range(256):
    p=copy.deepcopy(base)
    c=p['clusters'][i%len(p['clusters'])]
    vals=edge if i < len(edge) else None
    if vals:
        v=vals[i]
    else:
        v=round(rng.random(),6)
    c['state']['alert']=v
    c['state']['front_tension']=round(rng.random(),6)
    c['projection']['agitation']=round(rng.random(),6)
    c['projection']['cohesion']=round(rng.random(),6)
    # Exercise UTF-8 canonicalization using opaque source metadata.
    c['source']['biome']=f"ліс_{i}_🌲"
    p['projection_fingerprint']=projection_fingerprint(p)
    assert not validate_projection(p), validate_projection(p)[:5]
    items.append(p)
with tempfile.NamedTemporaryFile('w',encoding='utf-8',suffix='.json',delete=False) as f:
    json.dump(items,f,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    name=f.name
script=r'''
const fs=require('fs'),C=require(process.argv[1]);
const xs=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
for(let i=0;i<xs.length;i++){
  const got=C.projectionFingerprint(xs[i]);
  if(got!==xs[i].projection_fingerprint)throw new Error(`fingerprint mismatch at ${i}: ${got} != ${xs[i].projection_fingerprint}`);
  C.assertProjection(xs[i]);
}
console.log(`cross-runtime fingerprint PASS: ${xs.length} Python↔JS projections`);
'''
try:
    subprocess.run(['node','-e',script,str(ROOT/'web/fpe_core.js'),name],check=True,cwd=ROOT)
finally:
    pathlib.Path(name).unlink(missing_ok=True)
