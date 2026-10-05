'use strict';
const A=require('assert'),F=require('../web/fpe'),p=require('../data/projections/canonical_initial.json'),q=require('../data/projections/canonical_after.json');
const clusters=p.clusters.map(c=>c.id),buds=p.clusters.flatMap(c=>c.buds.map(b=>({id:b.id,parent:c.id})));
function rng(seed){let x=seed>>>0;return ()=>{x=(Math.imul(x,1664525)+1013904223)>>>0;return x;};}
let operations=0,restores=0,checks=0;
for(let seed=1;seed<=25;seed++){
 const rand=rng(seed*2654435761),budget=1+(rand()%8);let a=F.create(p,{budget}),b=F.create(p,{budget}),tick=-1,accepted=false;
 for(let i=0;i<200;i++){
  const op=rand()%100;
  if(op<42){tick=tick<0?0:tick+(rand()%5);A.deepStrictEqual(b.step(tick),a.step(tick));}
  else if(op<58){const id=clusters[rand()%clusters.length];A.deepStrictEqual(b.toggleCluster(id),a.toggleCluster(id));}
  else if(op<70){const x=buds[rand()%buds.length];if(!a.getView().expandedClusters.includes(x.parent))A.deepStrictEqual(b.toggleCluster(x.parent),a.toggleCluster(x.parent));A.deepStrictEqual(b.toggleBud(x.id),a.toggleBud(x.id));}
  else if(op<78){const v=a.getView(),id=clusters[rand()%clusters.length],set=new Set(v.expandedClusters);set.has(id)?set.delete(id):set.add(id);const next={expandedClusters:[...set],expandedBuds:v.expandedBuds};A.deepStrictEqual(b.setView(next),a.setView(next));}
  else if(op<86){const target=rand()%2?clusters[rand()%clusters.length]:buds[rand()%buds.length].id;const payload={seed,i,n:rand()%100000};A.deepStrictEqual(b.request('stress',target,payload),a.request('stress',target,payload));}
  else if(op<89&&!accepted){A.deepStrictEqual(b.accept(q),a.accept(q));accepted=true;}
  else {b=F.restore(JSON.parse(JSON.stringify(b.serialize())));restores++;A.deepStrictEqual(b.serialize(),a.serialize());checks++;}
  if(i%25===0){A.deepStrictEqual(b.serialize(),a.serialize());checks++;}
  operations++;
 }
 A.deepStrictEqual(b.serialize(),a.serialize());checks++;
}
console.log(`persistence stress PASS: ${operations} operations, ${restores} restore cycles, ${checks} full-state checks, 25 seeds`);
