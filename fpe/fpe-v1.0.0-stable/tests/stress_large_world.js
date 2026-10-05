'use strict';
const A=require('assert'),F=require('../web/fpe'),C=require('../web/fpe_core'),base=require('../data/projections/canonical_initial.json');
function make(cols,rows){
 const p=JSON.parse(JSON.stringify(base));p.source.dimensions=[cols,rows];p.clusters=[];
 for(let y=0;y<rows;y++)for(let x=0;x<cols;x++){
  const c=JSON.parse(JSON.stringify(base.clusters[(y*cols+x)%base.clusters.length]));c.id=`sector_${x}_${y}`;c.sector=[x,y];
  c.buds.forEach((b,i)=>{b.id=`${c.id}_bud_${i}`;b.index=i;b.seed_key=`${p.source.seed}:${x}:${y}:bud:${i}`;});p.clusters.push(c);
 }
 p.summary.cluster_count=p.clusters.length;p.summary.bud_count=p.clusters.length*4;
 p.summary.territory_cluster_count=p.clusters.filter(c=>c.source.territory_id!==null).length;
 p.summary.front_cluster_count=p.clusters.filter(c=>c.source.front_ids.length>0).length;
 p.summary.straight_bud_count=p.clusters.reduce((n,c)=>n+c.buds.filter(b=>b.type==='STRAIGHT').length,0);
 p.summary.curved_bud_count=p.summary.bud_count-p.summary.straight_bud_count;p.projection_fingerprint=C.projectionFingerprint(p);return p;
}
const p=make(100,100);C.assertProjection(p);const r=F.create(p,{budget:16});for(let t=0;t<200;t++)r.step(t);
const before=r.serialize(),json=JSON.stringify(before),restored=F.restore(JSON.parse(json));A.deepStrictEqual(restored.serialize(),before);
A.equal(before.projection.clusters.length,10000);A.equal(before.projection.summary.bud_count,40000);
console.log(`large-world stress PASS: 10000 clusters, 40000 buds, ${json.length} snapshot bytes, 200 scheduler ticks, exact restore`);
