"use strict";
const fs=require('fs'),vm=require('vm'),path=require('path');
const root=path.resolve(__dirname,'..'),code=fs.readFileSync(path.join(root,'web','fpe_core.js'),'utf8');
const sandbox={module:{exports:{}},exports:{},console};vm.createContext(sandbox);vm.runInContext(code,sandbox);const F=sandbox.module.exports;
const p=JSON.parse(fs.readFileSync(path.join(root,'data','projections','canonical_initial.json'),'utf8'));F.assertProjection(p);
const projectionBefore=JSON.stringify(p),empty=F.emptyViewState(),collapsed=F.buildHierarchyPlan(p,empty);
if(collapsed.items.length!==30||collapsed.counts.cluster_proxy!==30||collapsed.counts.geometry!==0)throw new Error('initial LOD must be 30 cluster proxies');
const cluster=p.clusters[0],openCluster=F.toggleCluster(p,empty,cluster.id),clusterPlan=F.buildHierarchyPlan(p,openCluster);
if(clusterPlan.counts.cluster_proxy!==29||clusterPlan.counts.bud_proxy!==4)throw new Error('cluster expansion must replace one proxy with 4 bud proxies');
const bud=cluster.buds[0],openBud=F.toggleBud(p,openCluster,bud.id),detailA=F.buildHierarchyPlan(p,openBud),detailB=F.buildHierarchyPlan(p,openBud);
if(detailA.counts.bud_proxy!==3||detailA.counts.geometry!==1||detailA.counts.nodes<8||detailA.counts.edges<12)throw new Error('bud expansion must reveal deterministic geometry');
if(JSON.stringify(detailA)!==JSON.stringify(detailB))throw new Error('hierarchy plan is not deterministic');
if(F.viewStateFingerprint(p,openBud)!==F.viewStateFingerprint(p,F.normalizeViewState(p,{expandedClusters:[cluster.id,cluster.id,'missing'],expandedBuds:[bud.id,bud.id,'missing']})))throw new Error('normalized view fingerprint mismatch');
const closed=F.toggleCluster(p,openBud,cluster.id);if(closed.expandedClusters.length||closed.expandedBuds.length)throw new Error('cluster collapse must remove descendant expansion');
if(JSON.stringify(p)!==projectionBefore)throw new Error('view operations mutated authoritative projection');
const fullA=F.buildGeometryPlan(p),fullB=F.buildGeometryPlan(p);if(fullA.length!==30||JSON.stringify(fullA)!==JSON.stringify(fullB))throw new Error('full geometry compatibility plan failed');
if(/Math\.random\s*\(/.test(code))throw new Error('Math.random found in fpe_core.js');
const html=fs.readFileSync(path.join(root,'web','index.html'),'utf8');if(/Math\.random\s*\(/.test(html))throw new Error('Math.random found in index.html');
for(const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)){if(match[1].trim())new Function(match[1]);}
const version=fs.readFileSync(path.join(root,'VERSION'),'utf8').trim();
const standalone=fs.readFileSync(path.join(root,`fpe-v${version}-demo.html`),'utf8');
if(/src="(?:fpe_core|canonical_projection)\.js"/.test(standalone))throw new Error('standalone demo retained local script dependency');
for(const match of standalone.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)){if(match[1].trim())new Function(match[1]);}
console.log('FPE v0.6 hierarchical web core: PASS');
console.log(`collapsed=${collapsed.items.length} cluster_open=${clusterPlan.items.length} detailed_nodes=${detailA.counts.nodes} detailed_edges=${detailA.counts.edges}`);
