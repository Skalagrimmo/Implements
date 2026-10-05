"use strict";
const FPEHandoff08=(()=>{
  const C=typeof module!=='undefined'&&module.exports?require('./fpe_core.js'):FPE06;
  function canonical(v){
    if(v===null||typeof v!=='object')return JSON.stringify(v);
    if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';
    return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
  }
  function prepare(current,incoming,view){
    C.assertProjection(incoming);
    const next=JSON.parse(JSON.stringify(incoming));
    if(current){
      C.assertProjection(current);
      const a=current.source,b=next.source;
      if(a.pixelgen_world_fingerprint!==b.pixelgen_world_fingerprint||a.seed!==b.seed||canonical(a.dimensions)!==canonical(b.dimensions))throw new Error('foreign world: start a new viewer session');
      if(b.state_revision<a.state_revision||b.state_tick<a.state_tick)throw new Error('stale projection');
      if(b.state_revision===a.state_revision){
        if(canonical(current)!==canonical(next))throw new Error('conflicting projection at same revision');
        return {projection:current,viewState:C.normalizeViewState(current,view),changed:false};
      }
    }
    return {projection:next,viewState:C.normalizeViewState(next,view),changed:true};
  }
  return {prepare};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=FPEHandoff08;
