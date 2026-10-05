'use strict';
const A=require('assert'),F=require('../web/fpe'),C=require('../web/fpe_core'),p=require('../data/projections/canonical_initial.json'),q=require('../data/projections/canonical_after.json');
const legacy11=require('../data/snapshots/v0.11.0-reference.json'),legacy12=require('../data/snapshots/v0.12.0-reference.json');
const copy=x=>JSON.parse(JSON.stringify(x));
const mode=process.argv[2]||'all',start=Number(process.argv[3]||0),count=Number(process.argv[4]||100);
function roundtrip(i){const r=F.create(p,{budget:1+(i%8)}),cid=p.clusters[i%p.clusters.length].id;r.toggleCluster(cid);for(let t=0;t<(i%9);t++)r.step(t);if(i%3===0)r.accept(q);const s=JSON.parse(JSON.stringify(r.serialize())),rr=F.restore(s);A.deepStrictEqual(rr.serialize(),s);}
function migration(i){const src=copy(i%2?legacy11:legacy12),out=F.restore(src).serialize();A.equal(out.runtime_version,'1.0.0');A.equal(out.schema,'fpe.runtime_snapshot/0.11.0');}
const mutations=[s=>s.runtime_version='2.0.0',s=>s.schema='x',s=>s.clock.last_tick=-2,s=>s.scheduler.last_tick=(s.clock.last_tick===-1?0:s.clock.last_tick-1),s=>s.request_context.source.state_revision++,s=>{s.projection.summary.cluster_count++;s.projection.projection_fingerprint=C.projectionFingerprint(s.projection)},s=>s.scheduler.projection_fingerprint='0'.repeat(64),s=>s.view.expandedClusters.push('missing')];
const base=F.create(p,{budget:3}).serialize();
function reject(i){const s=copy(base);mutations[i%mutations.length](s);A.throws(()=>F.restore(s),e=>e instanceof F.FPEError&&e.code==='INVALID_SNAPSHOT');}
const fn={roundtrip,migration,reject};
if(mode==='all'){for(const m of Object.keys(fn))for(let i=start;i<start+count;i++)fn[m](i);console.log(`v1.0 torture PASS: ${count} each current round-trips, historical migrations, hostile rejects (start ${start})`);}
else {if(!fn[mode])throw new Error('mode must be all|roundtrip|migration|reject');for(let i=start;i<start+count;i++)fn[mode](i);console.log(`v1.0 torture ${mode} PASS: ${count} cases (start ${start})`);}
