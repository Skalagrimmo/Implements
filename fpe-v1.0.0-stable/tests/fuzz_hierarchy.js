"use strict";
const fs=require('fs'),vm=require('vm'),path=require('path');
const root=path.resolve(__dirname,'..'),code=fs.readFileSync(path.join(root,'web','fpe_core.js'),'utf8');
const sandbox={module:{exports:{}},exports:{},console};vm.createContext(sandbox);vm.runInContext(code,sandbox);const F=sandbox.module.exports;
const p=JSON.parse(fs.readFileSync(path.join(root,'data','projections','canonical_initial.json'),'utf8')),before=JSON.stringify(p);F.deepFreeze(p);F.assertProjection(p);
let state=F.emptyViewState(),seed=0x7301;
function next(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;}
for(let i=0;i<2000;i++){
  const cluster=p.clusters[next()%p.clusters.length];
  if((next()>>>16)&1)state=F.toggleCluster(p,state,cluster.id);else state=F.toggleBud(p,state,cluster.buds[(next()>>>16)%cluster.buds.length].id);
  const normalized=F.normalizeViewState(p,state),a=F.buildHierarchyPlan(p,normalized),b=F.buildHierarchyPlan(p,normalized);
  if(JSON.stringify(a)!==JSON.stringify(b))throw new Error(`nondeterministic plan at operation ${i}`);
  for(const budId of normalized.expandedBuds){const parent=p.clusters.find(c=>c.buds.some(b=>b.id===budId));if(!parent||!normalized.expandedClusters.includes(parent.id))throw new Error(`orphan bud at operation ${i}`);}
  if(a.counts.cluster_proxy+a.state.expandedClusters.length!==p.clusters.length)throw new Error(`cluster accounting failed at operation ${i}`);
}
if(JSON.stringify(p)!==before)throw new Error('fuzz operations mutated projection');
console.log('FPE v0.6 hierarchy fuzz: PASS');
console.log('operations=2000 final_view='+F.viewStateFingerprint(p,state));
