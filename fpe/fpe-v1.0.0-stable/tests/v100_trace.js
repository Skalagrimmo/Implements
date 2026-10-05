'use strict';
const crypto=require('crypto');
function rng(seed){let x=(seed>>>0)||1;return ()=>{x=(Math.imul(x,1664525)+1013904223)>>>0;return x;};}
function copy(x){return JSON.parse(JSON.stringify(x));}
function trace(F,p,q,seed){
  const rand=rng(seed),budget=1+(rand()%8),r=F.create(copy(p),{budget}),log=[];
  const clusters=p.clusters.map(c=>c.id),buds=p.clusters.flatMap(c=>c.buds.map(b=>({id:b.id,parent:c.id})));
  let tick=-1,accepted=false;
  for(let i=0;i<80;i++){
    if(i===37){log.push(['accept',r.accept(copy(q))]);accepted=true;}
    if(i%7===0){const id=clusters[rand()%clusters.length];log.push(['cluster',id,r.toggleCluster(id)]);}
    if(i%13===0){const b=buds[rand()%buds.length],v=r.getView();if(!v.expandedClusters.includes(b.parent))log.push(['parent',b.parent,r.toggleCluster(b.parent)]);log.push(['bud',b.id,r.toggleBud(b.id)]);}
    if(i%11===0){const target=(rand()%2)?clusters[rand()%clusters.length]:buds[rand()%buds.length].id;log.push(['request',r.request('parity',target,{seed,i,n:rand()%100000,accepted})]);}
    if(i%17===0){const v=r.getView(),id=clusters[rand()%clusters.length],set=new Set(v.expandedClusters);set.has(id)?set.delete(id):set.add(id);log.push(['view',r.setView({expandedClusters:[...set],expandedBuds:v.expandedBuds})]);}
    tick=tick<0?0:tick+1+(rand()%3);log.push(['step',r.step(tick)]);
  }
  const snapshot=r.serialize();snapshot.runtime_version='$RUNTIME';
  return {budget,log,snapshot};
}
function digest(value){return crypto.createHash('sha256').update(JSON.stringify(value)).digest('hex');}
module.exports={trace,digest};
