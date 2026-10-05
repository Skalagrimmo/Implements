'use strict';
const A=require('assert'),fs=require('fs'),path=require('path'),F=require('../web/fpe');
const root=path.resolve(__dirname,'..'),load=n=>JSON.parse(fs.readFileSync(path.join(root,'data/projections',n)));
const p=load('canonical_initial.json'),q=load('canonical_after.json'),clusters=p.clusters.map(c=>c.id),buds=p.clusters.flatMap(c=>c.buds.map(b=>({id:b.id,parent:c.id})));
function rng(seed){let x=seed>>>0;return ()=>{x=(Math.imul(x,1664525)+1013904223)>>>0;return x;};}
let operations=0,restores=0,fullChecks=0;
for(let seed=1;seed<=30;seed++){
  const rand=rng(seed*7919),budget=1+(rand()%8);let a=F.create(p,{budget}),b=F.create(p,{budget}),tick=-1,accepted=false;
  for(let i=0;i<150;i++){
    const op=rand()%100;
    if(op<45){const delta=rand()%4;if(tick<0)tick=0;else tick+=delta;A.deepStrictEqual(b.step(tick),a.step(tick));}
    else if(op<62){const id=clusters[rand()%clusters.length];A.deepStrictEqual(b.toggleCluster(id),a.toggleCluster(id));}
    else if(op<74){const x=buds[rand()%buds.length],view=a.getView();if(!view.expandedClusters.includes(x.parent)){A.deepStrictEqual(b.toggleCluster(x.parent),a.toggleCluster(x.parent));}A.deepStrictEqual(b.toggleBud(x.id),a.toggleBud(x.id));}
    else if(op<82){const view=a.getView(),id=clusters[rand()%clusters.length];const set=new Set(view.expandedClusters);set.has(id)?set.delete(id):set.add(id);const next={expandedClusters:[...set],expandedBuds:view.expandedBuds};A.deepStrictEqual(b.setView(next),a.setView(next));}
    else if(op<89){const target=rand()%2?clusters[rand()%clusters.length]:buds[rand()%buds.length].id,n=rand()%1000,payload={seed,i,n};A.deepStrictEqual(b.request('probe',target,payload),a.request('probe',target,payload));}
    else if(op<92&&!accepted){A.deepStrictEqual(b.accept(q),a.accept(q));accepted=true;}
    else {b=F.restore(JSON.parse(JSON.stringify(b.serialize())));restores++;A.deepStrictEqual(b.serialize(),a.serialize());fullChecks++;}
    A.deepStrictEqual(b.getView(),a.getView());
    if(i%15===0){A.deepStrictEqual(b.getProjection(),a.getProjection());A.deepStrictEqual(b.serialize(),a.serialize());fullChecks++;}
    operations++;
  }
  A.deepStrictEqual(b.serialize(),a.serialize());fullChecks++;
}
console.log(`persistence fuzz PASS: ${operations} mixed operations, ${restores} serialize/JSON/restore cycles, ${fullChecks} full-state checks, 30 deterministic seeds`);
