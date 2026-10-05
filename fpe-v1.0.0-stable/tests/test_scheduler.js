"use strict";
const assert=require('assert'),fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..'),F=require('../web/fpe_core'),S=require('../web/fpe_scheduler');
const p=JSON.parse(fs.readFileSync(path.join(root,'data/projections/canonical_initial.json'))),before=JSON.stringify(p);
const full={expandedClusters:p.clusters.map(c=>c.id),expandedBuds:p.clusters.flatMap(c=>c.buds.map(b=>b.id))};
function run(view,budget=8) {
  const s=S.create(p,{budget}),log=[],counts=new Map();
  for(let tick=0;tick<2000;tick++) {
    const out=s.step(tick,view);assert(out.updates.length<=budget);
    for(const u of out.updates)counts.set(u.id,(counts.get(u.id)||0)+1);
    assert.equal(s.step(tick,view).updates.length,0);log.push(out);
  }
  assert.equal(counts.size,30);return {log,counts};
}
const a=run(full),b=run(full);assert.deepStrictEqual(a,b);
const collapsed=run(F.emptyViewState(),100),detailed=run(full,100);
assert(detailed.log.flatMap(x=>x.updates).length>collapsed.log.flatMap(x=>x.updates).length);
const active=p.clusters.find(c=>c.projection.update_rate>=0.33),quiet=p.clusters.find(c=>c.projection.update_rate<0.33);
assert(detailed.counts.get(active.id)>detailed.counts.get(quiet.id));
run(full,1); // overload: every cluster eventually receives service
const s=S.create(p);s.step(0,{});assert.throws(()=>s.step(-1,{}));assert.throws(()=>s.step(NaN,{}));
s.step(2,{});assert.throws(()=>s.step(1,{}));assert.throws(()=>S.create(p,{budget:0}));
assert(s.step(1000000,{}).updates.length<=8); // no unbounded catch-up
const q=JSON.parse(before),detached=S.create(q);q.clusters.length=0;assert(detached.step(0,{}).updates.length===8);
assert.equal(JSON.stringify(p),before);
const changing=S.create(p,{budget:100});changing.step(0,{});
const one=F.toggleCluster(p,{},p.clusters[0].id);
assert(changing.step(1,one).updates.some(u=>u.id===p.clusters[0].id&&u.detail==='bud_proxy'));
const two=F.toggleBud(p,one,p.clusters[0].buds[0].id);
assert(changing.step(2,two).updates.some(u=>u.id===p.clusters[0].id&&u.detail==='geometry'));
assert(changing.step(3,{}).updates.some(u=>u.id===p.clusters[0].id&&u.detail==='cluster_proxy'));
assert.throws(()=>changing.step(Number.MAX_SAFE_INTEGER,two));
assert(changing.step(4,two).updates.some(u=>u.detail==='geometry'));

// v0.11 persistence extension: restore exact internal service schedule.
const persisted=S.create(p,{budget:3});persisted.step(0,full);persisted.step(3,full);const state=persisted.snapshot(),stateCopy=JSON.parse(JSON.stringify(state));
const resumed=S.create(p,{budget:3,state:stateCopy});assert.deepStrictEqual(resumed.snapshot(),state);assert(resumed.step(3,full).repeated);
for(let tick=4;tick<25;tick++)assert.deepStrictEqual(resumed.step(tick,full),persisted.step(tick,full));
stateCopy.entries.length=0;assert.equal(resumed.snapshot().entries.length,p.clusters.length);
const badState=JSON.parse(JSON.stringify(state));badState.entries[0].rate=.123;assert.throws(()=>S.create(p,{budget:3,state:badState}));
console.log('scheduler PASS: replay, rates, budget, fairness, tick validation, persistence restore, copy isolation, no mutation');
