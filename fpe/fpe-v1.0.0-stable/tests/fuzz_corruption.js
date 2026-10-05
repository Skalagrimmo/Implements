'use strict';
const A=require('assert'),F=require('../web/fpe'),C=require('../web/fpe_core'),p=require('../data/projections/canonical_initial.json');
const copy=x=>JSON.parse(JSON.stringify(x)),cid=p.clusters[0].id,bid=p.clusters[0].buds[0].id;
const r=F.create(p,{budget:3});r.toggleCluster(cid);r.toggleBud(bid);for(let t=0;t<=23;t++)r.step(t);
const base=r.serialize();
const mutations=[
 s=>{s.schema='x'},s=>{s.runtime_version='0.10.0'},s=>{s.projection_schema='x'},s=>{s.action_request_schema='x'},
 s=>{s.options.budget=0},s=>{s.options.budget=4},s=>{s.clock.last_tick=-2},s=>{s.clock.last_tick=Number.MAX_SAFE_INTEGER},
 s=>{s.scheduler.last_tick=s.clock.last_tick-1},s=>{s.scheduler.last_tick=s.clock.last_tick+1},s=>{s.scheduler.schema='x'},s=>{s.scheduler.budget++},
 s=>{s.scheduler.projection_fingerprint='f'.repeat(64)},s=>{s.scheduler.source_revision++},s=>{s.scheduler.source_tick++},
 s=>{s.scheduler.entries.pop()},s=>{s.scheduler.entries[1].id=s.scheduler.entries[0].id},s=>{s.scheduler.entries[0].id='missing'},
 s=>{s.scheduler.entries[0].rate=0.123456789},s=>{s.scheduler.entries[0].next=-1},s=>{s.scheduler.entries[0].next=Number.MAX_SAFE_INTEGER+1},
 s=>{const e=s.scheduler.entries.find(x=>x.last!==null);e.next=e.last},s=>{const e=s.scheduler.entries.find(x=>x.last===null);if(e)e.next=1;else{s.scheduler.entries[0].last=null;s.scheduler.entries[0].next=1}},
 s=>{s.scheduler.entries[0].detail='x'},s=>{s.view.expandedClusters.push('missing')},s=>{s.view.expandedBuds.push('missing')},
 s=>{s.request_context.action_request_schema='x'},s=>{s.request_context.source.state_revision++},s=>{s.request_context.source.state_tick++},s=>{s.request_context.source.seed++},
 s=>{s.projection.clusters[0].projection.agitation=Math.min(1,s.projection.clusters[0].projection.agitation+0.01)},
 s=>{s.projection.summary.front_cluster_count++;s.projection.projection_fingerprint=C.projectionFingerprint(s.projection)},
 s=>{s.projection.clusters[0].id='sector_bad';s.projection.projection_fingerprint=C.projectionFingerprint(s.projection)},
 s=>{s.projection.clusters[0].buds[0].id='bad';s.projection.projection_fingerprint=C.projectionFingerprint(s.projection)},
 s=>{s.projection.clusters[0].state.front_status='unknown';s.projection.projection_fingerprint=C.projectionFingerprint(s.projection)},
 s=>{s.projection.layout.cluster_kind='other';s.projection.projection_fingerprint=C.projectionFingerprint(s.projection)}
];
let rejected=0;for(let i=0;i<2400;i++){const s=copy(base);mutations[i%mutations.length](s);A.throws(()=>F.restore(s),e=>e instanceof F.FPEError&&e.code==='INVALID_SNAPSHOT');rejected++;}
// Valid snapshot survives repeated parse/stringify noise while maintaining byte-stable canonical runtime output.
for(let i=0;i<250;i++){const s=JSON.parse(JSON.stringify(base));const x=F.restore(s).serialize();A.deepStrictEqual(x,base);}
console.log(`corruption fuzz PASS: ${rejected} targeted invalid snapshots rejected, 250 valid JSON round-trips preserved`);
