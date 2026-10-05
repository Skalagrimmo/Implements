'use strict';
const A=require('assert'),fs=require('fs'),path=require('path'),F=require('../web/fpe'),C=require('../web/fpe_core');
const root=path.resolve(__dirname,'..'),copy=x=>JSON.parse(JSON.stringify(x));
const p=JSON.parse(fs.readFileSync(path.join(root,'data/projections/canonical_initial.json')));
const error=(fn,code)=>A.throws(fn,e=>e instanceof F.FPEError&&e.code===code);
// SHA-256 core has independent public vectors, including UTF-8.
for(const [text,hex] of [
  ['', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'],
  ['abc','ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'],
  ['Привіт 🌍','f8e7697f004b0b0e5db8d42c4ae68d0c5da8d5d6787aa33dcd4d52d5a740f353']
]) A.equal(C.sha256(text),hex);
A.equal(C.projectionFingerprint(p),p.projection_fingerprint);
// Range-valid tampering with a stale hash must be rejected.
let bad=copy(p);bad.clusters[0].projection.agitation=0.5;error(()=>F.create(bad),'INVALID_PROJECTION');
// Rehashing cannot hide semantic contradictions that the schema can derive.
bad=copy(p);bad.summary.front_cluster_count++;bad.projection_fingerprint=C.projectionFingerprint(bad);error(()=>F.create(bad),'INVALID_PROJECTION');
bad=copy(p);bad.layout.cluster_kind='other';bad.projection_fingerprint=C.projectionFingerprint(bad);error(()=>F.create(bad),'INVALID_PROJECTION');
bad=copy(p);bad.fpe_version='9.9.9';bad.projection_fingerprint=C.projectionFingerprint(bad);error(()=>F.create(bad),'INVALID_PROJECTION');
const hostile=copy(p);Object.defineProperty(hostile.clusters[0].projection,'agitation',{enumerable:true,get(){return 0.5;}});error(()=>F.create(hostile),'INVALID_PROJECTION');
const hiddenProjection=copy(p);Object.defineProperty(hiddenProjection,'secret',{value:1,enumerable:false});error(()=>F.create(hiddenProjection),'INVALID_PROJECTION');
// Unpaired UTF-16 cannot occur in the Python bridge's UTF-8 fingerprint contract.
bad=copy(p);bad.clusters[0].source.biome='bad\ud800';bad.projection_fingerprint='0'.repeat(64);error(()=>F.create(bad),'INVALID_PROJECTION');
// Impossible scheduler states are never normalized into a different runtime.
let r=F.create(p,{budget:1}),s=r.serialize();
s.scheduler.entries[0].next=1;error(()=>F.restore(s),'INVALID_SNAPSHOT');
s=r.serialize();s.scheduler.entries[0].detail='geometry';error(()=>F.restore(s),'INVALID_SNAPSHOT');
r.step(0);r.step(1);s=r.serialize();s.clock.last_tick++;error(()=>F.restore(s),'INVALID_SNAPSHOT');
s=r.serialize();let served=s.scheduler.entries.find(e=>e.last!==null);served.next=served.last;error(()=>F.restore(s),'INVALID_SNAPSHOT');
s=r.serialize();let never=s.scheduler.entries.find(e=>e.last===null);if(never){never.next=1;error(()=>F.restore(s),'INVALID_SNAPSHOT');}
// The documented near-limit tick is valid and remains stable through persistence.
r=F.create(p,{budget:2});const near=Number.MAX_SAFE_INTEGER-16;const out=r.step(near);A.equal(out.tick,near);const rr=F.restore(JSON.parse(JSON.stringify(r.serialize())));A(rr.step(near).repeated);error(()=>rr.step(Number.MAX_SAFE_INTEGER-15),'INVALID_TICK');
// Snapshot validator rejects JS state that JSON itself could not faithfully represent.
s=r.serialize();Object.defineProperty(s,'hidden',{value:1,enumerable:false});error(()=>F.restore(s),'INVALID_SNAPSHOT');
s=r.serialize();s[Symbol('x')]=1;error(()=>F.restore(s),'INVALID_SNAPSHOT');
s=r.serialize();Object.defineProperty(s.clock,'last_tick',{enumerable:true,get(){return near;}});error(()=>F.restore(s),'INVALID_SNAPSHOT');
// Repeat serialization is stable and detached.
r=F.create(p,{budget:4});for(let t=0;t<64;t++)r.step(t);const a=JSON.stringify(r.serialize());for(let i=0;i<100;i++)A.equal(JSON.stringify(r.serialize()),a);
console.log('RC hardening PASS: fingerprint integrity, SHA-256 vectors, semantic rehash guards, impossible scheduler states, tick boundary, hostile JS objects, stable serialization');
