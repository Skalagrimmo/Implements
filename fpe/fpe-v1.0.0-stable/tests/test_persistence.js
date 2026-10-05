'use strict';
const A=require('assert'),fs=require('fs'),path=require('path'),F=require('../web/fpe');
const root=path.resolve(__dirname,'..'),load=n=>JSON.parse(fs.readFileSync(path.join(root,'data/projections',n))),copy=x=>JSON.parse(JSON.stringify(x));
const p=load('canonical_initial.json'),q=load('canonical_after.json'),cid=p.clusters[0].id,bid=p.clusters[0].buds[0].id,cid2=p.clusters[1].id;
const error=(fn,code='INVALID_SNAPSHOT')=>A.throws(fn,e=>e instanceof F.FPEError&&e.code===code);
const r=F.create(p,{budget:3});
r.toggleCluster(cid);r.toggleBud(bid);
for(let t=0;t<=17;t++){if(t===7)r.toggleCluster(cid2);r.step(t);}
const snapshot=r.serialize();
A.equal(snapshot.schema,'fpe.runtime_snapshot/0.11.0');A.equal(snapshot.runtime_version,'1.0.0');A.equal(snapshot.options.budget,3);
A.equal(snapshot.clock.last_tick,17);A.equal(snapshot.scheduler.last_tick,17);A.equal(snapshot.request_context.source.state_revision,0);
const json=JSON.stringify(snapshot),restored=F.restore(JSON.parse(json));
A.equal(JSON.stringify(restored.serialize()),json);
A.deepStrictEqual(restored.request('inspect',cid,{depth:2}),r.request('inspect',cid,{depth:2}));
A(restored.step(17).repeated);A(r.step(17).repeated);
for(let t=18;t<=29;t++)A.deepStrictEqual(restored.step(t),r.step(t));
restored.toggleCluster(cid2);r.toggleCluster(cid2);A.deepStrictEqual(restored.getView(),r.getView());
A.deepStrictEqual(restored.accept(q),r.accept(q));
// After handoff the host clock is retained while scheduler state is freshly reset; persistence must keep both clocks.
const afterAccept=r.serialize(),afterAccept2=restored.serialize();A.deepStrictEqual(afterAccept2,afterAccept);
A.equal(afterAccept.clock.last_tick,29);A.equal(afterAccept.scheduler.last_tick,-1);
const post=F.restore(copy(afterAccept));
A.deepStrictEqual(post.step(29),r.step(29));
A.deepStrictEqual(post.request('inspect',cid),r.request('inspect',cid));
A.equal(post.request('inspect',cid).source.state_revision,3);
for(let t=30;t<=60;t++)A.deepStrictEqual(post.step(t),r.step(t));
A.deepStrictEqual(post.serialize(),r.serialize());
// Serialize and restore own their data.
const detached=r.serialize(),detachedProjection=r.getProjection();detached.projection.clusters.length=0;detached.view.expandedClusters.length=0;detached.scheduler.entries.length=0;
A.equal(r.getProjection().clusters.length,detachedProjection.clusters.length);A.notEqual(r.serialize().scheduler.entries.length,0);
const input=r.serialize(),fromInput=F.restore(input);input.projection.clusters.length=0;input.request_context.source.dimensions[0]=999;
A.equal(fromInput.getProjection().clusters.length,30);A.notEqual(fromInput.request('inspect',cid).source.dimensions[0],999);
// Malformed/cross-wired snapshots are rejected, never silently normalized.
const mutations=[
  s=>s.schema='other',s=>s.runtime_version='9.0.0',s=>s.projection_schema='other',s=>s.action_request_schema='other',
  s=>s.options.budget=0,s=>s.projection.clusters[0].projection.agitation=Infinity,s=>s.view.expandedClusters.push('missing'),
  s=>s.clock.last_tick=-2,s=>s.scheduler.budget++,s=>s.scheduler.entries[0].id='missing',s=>s.scheduler.entries[0].rate=.123456,
  s=>s.scheduler.last_tick=s.clock.last_tick+1,s=>s.scheduler.projection_fingerprint='0'.repeat(64),s=>s.scheduler.source_revision++,
  s=>s.request_context.action_request_schema='other',s=>s.request_context.source.state_revision++,s=>s.request_context.source.dimensions[0]++
];
for(const mutate of mutations){const s=copy(r.serialize());mutate(s);error(()=>F.restore(s));}
const cyclic=r.serialize();cyclic.self=cyclic;error(()=>F.restore(cyclic));
const dated=r.serialize();dated.extra=new Date();error(()=>F.restore(dated));

// v0.11 snapshots remain restorable under the frozen 0.11 snapshot schema.
const legacy=JSON.parse(fs.readFileSync(path.join(root,'data/snapshots/v0.11.0-reference.json'))),migrated=F.restore(legacy).serialize();
A.equal(legacy.runtime_version,'0.11.0');A.equal(migrated.runtime_version,'1.0.0');A.equal(migrated.schema,legacy.schema);
const rc=JSON.parse(fs.readFileSync(path.join(root,'data/snapshots/v0.12.0-reference.json'))),promoted=F.restore(rc).serialize();
A.equal(rc.runtime_version,'0.12.0');A.equal(promoted.runtime_version,'1.0.0');A.equal(promoted.schema,rc.schema);

// Restored runtime keeps normal API guards.
error(()=>post.step(28),'INVALID_TICK');error(()=>post.accept(p),'STALE_REVISION');
console.log('persistence PASS: JSON round-trip, exact scheduler/view/request context, split clocks, handoff restore, isolation, 17 malformed cases');
