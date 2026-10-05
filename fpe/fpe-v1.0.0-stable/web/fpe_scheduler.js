"use strict";
// Scheduling ticks are supplied by the host, never PixelGen clock mutations.
const FPEScheduler07 = (() => {
  const Core = typeof module !== 'undefined' && module.exports ? require('./fpe_core.js') : FPE06;
  const STATE_SCHEMA='fpe.scheduler_state/0.11.0';
  const DETAILS=new Set(['cluster_proxy','bud_proxy','geometry']);
  const clone=x=>JSON.parse(JSON.stringify(x));
  function integer(n, name, min=0) {
    if (!Number.isSafeInteger(n) || n < min) throw new Error(`invalid ${name}`);
  }
  function expectedEntries(p){
    return p.clusters.map(c=>({id:c.id,rate:c.projection.update_rate,next:0,last:null,detail:'cluster_proxy'}))
      .sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0);
  }
  function restoreEntries(p,budget,state){
    if(!state||typeof state!=='object'||Array.isArray(state))throw new Error('invalid scheduler state');
    if(state.schema!==STATE_SCHEMA)throw new Error('unsupported scheduler state schema');
    if(state.budget!==budget)throw new Error('scheduler budget mismatch');
    if(state.projection_fingerprint!==p.projection_fingerprint)throw new Error('scheduler projection mismatch');
    if(state.source_revision!==p.source.state_revision||state.source_tick!==p.source.state_tick)throw new Error('scheduler source clock mismatch');
    if(!Number.isSafeInteger(state.last_tick)||state.last_tick < -1 || state.last_tick > Number.MAX_SAFE_INTEGER-16)throw new Error('invalid scheduler last tick');
    if(!Array.isArray(state.entries)||state.entries.length!==p.clusters.length)throw new Error('scheduler entry count mismatch');
    const byId=new Map();
    for(const raw of state.entries){
      if(!raw||typeof raw!=='object'||Array.isArray(raw)||typeof raw.id!=='string'||byId.has(raw.id))throw new Error('invalid scheduler entry');
      byId.set(raw.id,raw);
    }
    const entries=expectedEntries(p);
    for(const e of entries){
      const raw=byId.get(e.id);if(!raw)throw new Error('scheduler entry id mismatch');
      if(typeof raw.rate!=='number'||!Number.isFinite(raw.rate)||raw.rate!==e.rate)throw new Error('scheduler rate mismatch');
      if(!Number.isSafeInteger(raw.next)||raw.next<0||raw.next>Number.MAX_SAFE_INTEGER)throw new Error('invalid scheduler next tick');
      if(raw.last!==null&&(!Number.isSafeInteger(raw.last)||raw.last<0||raw.last>state.last_tick))throw new Error('invalid scheduler last service tick');
      if(raw.last===null&&raw.next!==0)throw new Error('unserved scheduler entry must remain due at tick 0');
      if(raw.last!==null&&raw.next<=raw.last)throw new Error('scheduler next tick must follow last service tick');
      if(state.last_tick===-1&&(raw.last!==null||raw.next!==0||raw.detail!=='cluster_proxy'))throw new Error('noncanonical fresh scheduler entry');
      if(!DETAILS.has(raw.detail))throw new Error('invalid scheduler detail');
      e.next=raw.next;e.last=raw.last;e.detail=raw.detail;
    }
    return {entries,lastTick:state.last_tick};
  }
  function create(projection, {budget=8,state=null}={}) {
    Core.assertProjection(projection);
    integer(budget, 'budget', 1);
    // Own an immutable detached copy; validation is cached only after a full
    // deep freeze, so hot scheduler steps never re-hash mutable input.
    const p = Core.deepFreeze(clone(projection));Core.assertProjection(p);
    let entries,lastTick;
    if(state===null){entries=expectedEntries(p);lastTick=-1;}
    else {const restored=restoreEntries(p,budget,state);entries=restored.entries;lastTick=restored.lastTick;}
    function step(tick, view) {
      integer(tick, 'tick');
      if(tick>Number.MAX_SAFE_INTEGER-16) throw new Error('tick too large');
      if (tick < lastTick) throw new Error('scheduler tick cannot move backward');
      if (tick === lastTick) return {tick, updates:[], deferred:0, repeated:true};
      const s=Core.normalizeViewState(p,view), open=new Set(s.expandedClusters), buds=new Set(s.expandedBuds);
      const details=new Map(p.clusters.map(c=>[c.id, !open.has(c.id)?'cluster_proxy':c.buds.some(b=>buds.has(b.id))?'geometry':'bud_proxy']));
      for (const e of entries) {
        const detail=details.get(e.id);
        if (detail!==e.detail) {e.next=Math.min(e.next,tick);e.detail=detail;}
      }
      const due=entries.filter(e=>e.next<=tick).sort((a,b)=>a.next-b.next || (a.id<b.id?-1:a.id>b.id?1:0));
      const updates=[];
      for (const e of due.slice(0,budget)) {
        // Integer periods: active/detailed clusters update more often.
        const base=e.rate>=0.66?1:e.rate>=0.33?2:4;
        const period=base*(e.detail==='cluster_proxy'?4:e.detail==='bud_proxy'?2:1);
        if (!Number.isSafeInteger(tick+period)) throw new Error('tick too large');
        updates.push({id:e.id, tick, elapsed:e.last===null?0:tick-e.last, period, detail:e.detail});
      }
      // Commit only after all output validation succeeds.
      for (let i=0;i<updates.length;i++) {due[i].last=tick;due[i].next=tick+updates[i].period;}
      lastTick=tick;
      return {tick,updates,deferred:due.length-updates.length,repeated:false};
    }
    function snapshot(){
      return clone({schema:STATE_SCHEMA,budget,projection_fingerprint:p.projection_fingerprint,
        source_revision:p.source.state_revision,source_tick:p.source.state_tick,last_tick:lastTick,entries});
    }
    return Object.freeze({step,snapshot});
  }
  return {create,version:'0.7.0',stateSchema:STATE_SCHEMA};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=FPEScheduler07;
