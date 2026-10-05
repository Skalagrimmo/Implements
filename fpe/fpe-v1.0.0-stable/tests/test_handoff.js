'use strict';
const A=require('assert'),fs=require('fs'),H=require('../web/fpe_handoff'),C=require('../web/fpe_core');
const load=n=>JSON.parse(fs.readFileSync(require('path').join(__dirname,'../data/projections',n)));
const p=load('canonical_initial.json'),q=load('canonical_after.json'),copy=x=>JSON.parse(JSON.stringify(x));
C.deepFreeze(p);C.deepFreeze(q);C.assertProjection(p);C.assertProjection(q);
const view={expandedClusters:[p.clusters[0].id],expandedBuds:[p.clusters[0].buds[0].id]},before=JSON.stringify({p,q,view});
let r=H.prepare(p,q,view);A(r.changed);A.deepStrictEqual(r.viewState,view);A.notStrictEqual(r.projection,q);
A.strictEqual(H.prepare(q,copy(q),view).changed,false);
const reordered=Object.fromEntries(Object.entries(q).reverse());A(!H.prepare(q,reordered,view).changed);
A.throws(()=>H.prepare(q,p,view),/stale/);
const cases=[
 x=>x.source=null,x=>x.layout=null,x=>x.summary=null,
 x=>x.source.state_revision=-1,x=>x.source.state_tick=NaN,
 x=>x.source.seed+=1,x=>x.source.pixelgen_world_fingerprint='0'.repeat(64),
 x=>x.clusters[0].projection.cohesion=Infinity,x=>x.clusters[0].buds[0].offset=[],
 x=>x.clusters[0].buds[0].index=3,x=>x.clusters[0].source.front_ids=null,
 x=>x.clusters[0].state=null,x=>x.clusters[0].buds[0]=null,
 x=>x.clusters[1].sector=x.clusters[0].sector,x=>x.summary.bud_count=0,
 x=>x.authority.objective_state_owner='FPE',x=>x.hierarchy.semantic_effect='mutation',
 x=>x.source.state_revision=p.source.state_revision
];
for(const mutate of cases){const bad=copy(q);mutate(bad);A.throws(()=>H.prepare(p,bad,view));A.equal(JSON.stringify({p,q,view}),before);}
const conflict=copy(p);conflict.clusters[0].projection.agitation=0.9;conflict.projection_fingerprint=C.projectionFingerprint(conflict);A.throws(()=>H.prepare(p,conflict,view),/conflicting/);
for(let i=0;i<1000;i++){A(!H.prepare(q,copy(q),view).changed);A.throws(()=>H.prepare(q,p,view));}
A.equal(JSON.stringify({p,q,view}),before);
console.log('handoff PASS: revision 0→3, duplicate, stale, conflict, foreign world, 18 malformed cases, 1000 replays');
