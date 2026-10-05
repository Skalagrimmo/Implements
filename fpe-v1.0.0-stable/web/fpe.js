'use strict';
const FPE=(()=>{
  const node=typeof module!=='undefined'&&module.exports;
  const C=node?require('./fpe_core'):FPE06;
  const H=node?require('./fpe_handoff'):FPEHandoff08;
  const S=node?require('./fpe_scheduler'):FPEScheduler07;
  const VERSION='1.0.0',PROJECTION_SCHEMA='fpe.pixelgen_hierarchy/0.6.0',ACTION_SCHEMA='fpe.action_request/0.10.0',SNAPSHOT_SCHEMA='fpe.runtime_snapshot/0.11.0',RESTORE_VERSIONS=new Set(['0.11.0','0.12.0','1.0.0']);
  const clone=x=>JSON.parse(JSON.stringify(x));
  const freezeProjection=p=>{C.deepFreeze(p);C.assertProjection(p);return p;};
  class FPEError extends Error {
    constructor(code,message){super(message);this.name='FPEError';this.code=code;}
  }
  function call(code,fn){try{return fn();}catch(e){if(e instanceof FPEError)throw e;throw new FPEError(code,e.message||String(e));}}
  function canonical(v){
    if(v===null||typeof v!=='object')return JSON.stringify(v);
    if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';
    return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
  }
  function assertJsonValue(value,path='payload',code='INVALID_REQUEST',seen=new WeakSet(),depth=0){
    if(depth>32)throw new FPEError(code,path+' exceeds maximum nesting depth');
    if(value===null||typeof value==='string'||typeof value==='boolean')return;
    if(typeof value==='number'){if(!Number.isFinite(value))throw new FPEError(code,path+' must contain finite JSON values');return;}
    if(typeof value!=='object')throw new FPEError(code,path+' must be JSON-compatible');
    if(seen.has(value))throw new FPEError(code,path+' must not contain cycles');
    seen.add(value);
    if(Array.isArray(value)){
      if(Object.getOwnPropertySymbols(value).length)throw new FPEError(code,path+' must not contain symbol properties');
      const keys=Object.keys(value);
      if(keys.length!==value.length||keys.some((k,i)=>k!==String(i)))throw new FPEError(code,path+' must be a dense JSON array without extra properties');
      for(let i=0;i<value.length;i++){const d=Object.getOwnPropertyDescriptor(value,String(i));if(!d||!('value' in d)||!d.enumerable)throw new FPEError(code,path+' must contain data properties only');assertJsonValue(d.value,path+'['+i+']',code,seen,depth+1);}
      seen.delete(value);return;
    }
    const proto=Object.getPrototypeOf(value);
    if(proto!==Object.prototype&&proto!==null)throw new FPEError(code,path+' must contain only plain objects');
    if(Object.getOwnPropertySymbols(value).length)throw new FPEError(code,path+' must not contain symbol properties');
    const own=Reflect.ownKeys(value),keys=Object.keys(value);
    if(own.length!==keys.length)throw new FPEError(code,path+' must not contain hidden properties');
    for(const k of keys){const d=Object.getOwnPropertyDescriptor(value,k);if(!d||!('value' in d)||!d.enumerable)throw new FPEError(code,path+' must contain data properties only');assertJsonValue(d.value,path+'.'+k,code,seen,depth+1);}
    seen.delete(value);
  }
  function assertViewShape(value,code='INVALID_VIEW'){
    if(!value||typeof value!=='object'||Array.isArray(value)||!Array.isArray(value.expandedClusters)||!Array.isArray(value.expandedBuds)||![...value.expandedClusters,...value.expandedBuds].every(x=>typeof x==='string'))throw new FPEError(code,'view requires two arrays of string IDs');
  }
  function requestSource(projection){
    return clone({seed:projection.source.seed,pixelgen_world_fingerprint:projection.source.pixelgen_world_fingerprint,
      dimensions:projection.source.dimensions,state_revision:projection.source.state_revision,state_tick:projection.source.state_tick});
  }
  function validateOptions(options){
    if(!options||typeof options!=='object'||Array.isArray(options))throw new FPEError('INVALID_OPTIONS','options must be an object');
    const budget=options.budget===undefined?8:options.budget;
    if(!Number.isSafeInteger(budget)||budget<1)throw new FPEError('INVALID_OPTIONS','budget must be a positive safe integer');
    return {budget};
  }
  function validateSnapshot(input){
    assertJsonValue(input,'snapshot','INVALID_SNAPSHOT');
    if(!input||typeof input!=='object'||Array.isArray(input))throw new FPEError('INVALID_SNAPSHOT','snapshot must be an object');
    if(input.schema!==SNAPSHOT_SCHEMA||!RESTORE_VERSIONS.has(input.runtime_version))throw new FPEError('INVALID_SNAPSHOT','unsupported runtime snapshot schema or version');
    if(input.projection_schema!==PROJECTION_SCHEMA||input.action_request_schema!==ACTION_SCHEMA)throw new FPEError('INVALID_SNAPSHOT','snapshot contract mismatch');
    if(!input.options||typeof input.options!=='object'||Array.isArray(input.options)||!Number.isSafeInteger(input.options.budget)||input.options.budget<1)throw new FPEError('INVALID_SNAPSHOT','invalid snapshot options');
    call('INVALID_SNAPSHOT',()=>C.assertProjection(input.projection));
    assertViewShape(input.view,'INVALID_SNAPSHOT');
    const normalized=call('INVALID_SNAPSHOT',()=>C.normalizeViewState(input.projection,input.view));
    if(canonical(normalized)!==canonical(input.view))throw new FPEError('INVALID_SNAPSHOT','snapshot view is not canonical for its projection');
    if(!input.clock||typeof input.clock!=='object'||Array.isArray(input.clock)||!Number.isSafeInteger(input.clock.last_tick)||input.clock.last_tick < -1 || input.clock.last_tick > Number.MAX_SAFE_INTEGER-16)throw new FPEError('INVALID_SNAPSHOT','invalid runtime clock');
    if(!input.scheduler||typeof input.scheduler!=='object'||Array.isArray(input.scheduler))throw new FPEError('INVALID_SNAPSHOT','missing scheduler state');
    if(!Number.isSafeInteger(input.scheduler.last_tick)||input.scheduler.last_tick>input.clock.last_tick)throw new FPEError('INVALID_SNAPSHOT','scheduler clock is ahead of runtime clock');
    if(input.scheduler.last_tick!==-1&&input.scheduler.last_tick!==input.clock.last_tick)throw new FPEError('INVALID_SNAPSHOT','scheduler/runtime clocks describe an impossible runtime state');
    call('INVALID_SNAPSHOT',()=>S.create(input.projection,{budget:input.options.budget,state:input.scheduler}));
    if(!input.request_context||typeof input.request_context!=='object'||Array.isArray(input.request_context)||input.request_context.action_request_schema!==ACTION_SCHEMA)throw new FPEError('INVALID_SNAPSHOT','invalid request context');
    if(canonical(input.request_context.source)!==canonical(requestSource(input.projection)))throw new FPEError('INVALID_SNAPSHOT','request context does not match projection source');
    return clone(input);
  }
  function createRuntime(initial,options={},restored=null){
    const {budget}=validateOptions(options);
    let projection=call(restored?'INVALID_SNAPSHOT':'INVALID_PROJECTION',()=>freezeProjection(H.prepare(null,initial,{}).projection));
    let view,scheduler,lastTick;
    if(restored){
      view=clone(restored.view);
      scheduler=call('INVALID_SNAPSHOT',()=>S.create(projection,{budget,state:restored.scheduler}));
      lastTick=restored.clock.last_tick;
    }else{
      view=C.emptyViewState();scheduler=S.create(projection,{budget});lastTick=-1;
    }
    function accept(incoming){
      call('INVALID_PROJECTION',()=>C.assertProjection(incoming));
      const a=projection.source,b=incoming.source;
      if(a.seed!==b.seed||a.pixelgen_world_fingerprint!==b.pixelgen_world_fingerprint||JSON.stringify(a.dimensions)!==JSON.stringify(b.dimensions))throw new FPEError('FOREIGN_WORLD','create a new runtime for another world');
      if(b.state_revision<a.state_revision||b.state_tick<a.state_tick)throw new FPEError('STALE_REVISION','revision or tick moved backward');
      const next=call('REVISION_CONFLICT',()=>H.prepare(projection,incoming,view));
      if(!next.changed)return {changed:false,revision:a.state_revision};
      const nextProjection=call('INVALID_PROJECTION',()=>freezeProjection(next.projection));
      const prepared=call('INVALID_PROJECTION',()=>{C.buildHierarchyPlan(nextProjection,next.viewState);return S.create(nextProjection,{budget});});
      projection=nextProjection;view=next.viewState;scheduler=prepared;
      return {changed:true,revision:projection.source.state_revision};
    }
    function setView(value){
      assertViewShape(value);
      view=C.normalizeViewState(projection,value);return clone(view);
    }
    function toggleCluster(id){
      if(!projection.clusters.some(c=>c.id===id))throw new FPEError('UNKNOWN_ID','unknown cluster');
      view=C.toggleCluster(projection,view,id);return clone(view);
    }
    function toggleBud(id){
      const parent=projection.clusters.find(c=>c.buds.some(b=>b.id===id));
      if(!parent)throw new FPEError('UNKNOWN_ID','unknown bud');
      if(!view.expandedClusters.includes(parent.id))throw new FPEError('PARENT_COLLAPSED','expand parent first');
      view=C.toggleBud(projection,view,id);return clone(view);
    }
    function step(tick){
      if(!Number.isSafeInteger(tick)||tick<0||tick>Number.MAX_SAFE_INTEGER-16||tick<lastTick)throw new FPEError('INVALID_TICK','tick must be monotonic and in safe range');
      const result=scheduler.step(tick,view);lastTick=tick;return result;
    }
    function request(action,targetId,payload={}){
      if(typeof action!=='string'||!action.trim()||action.length>64)throw new FPEError('INVALID_REQUEST','action must be a non-empty string up to 64 characters');
      if(typeof targetId!=='string'||!targetId)throw new FPEError('INVALID_REQUEST','targetId must be a non-empty string');
      let targetKind=null;
      if(projection.clusters.some(c=>c.id===targetId))targetKind='cluster';
      else if(projection.clusters.some(c=>c.buds.some(b=>b.id===targetId)))targetKind='bud';
      else throw new FPEError('UNKNOWN_ID','unknown request target');
      if(!payload||typeof payload!=='object'||Array.isArray(payload))throw new FPEError('INVALID_REQUEST','payload must be an object');
      assertJsonValue(payload);
      return clone({schema:ACTION_SCHEMA,action:action.trim(),target:{kind:targetKind,id:targetId},payload,source:requestSource(projection)});
    }
    function serialize(){
      const schedulerState=scheduler.snapshot();
      return clone({schema:SNAPSHOT_SCHEMA,runtime_version:VERSION,projection_schema:PROJECTION_SCHEMA,action_request_schema:ACTION_SCHEMA,
        options:{budget},projection,view,clock:{last_tick:lastTick},scheduler:schedulerState,
        request_context:{action_request_schema:ACTION_SCHEMA,source:requestSource(projection)}});
    }
    return Object.freeze({accept,setView,toggleCluster,toggleBud,step,request,serialize,
      getProjection:()=>clone(projection),getView:()=>clone(view),
      getPlan:()=>clone(C.buildHierarchyPlan(projection,view))});
  }
  function create(initial,options={}){return createRuntime(initial,options,null);}
  function restore(snapshot){const s=validateSnapshot(snapshot);return createRuntime(s.projection,s.options,s);}
  function describe(){return {version:VERSION,projectionSchema:PROJECTION_SCHEMA,actionRequestSchema:ACTION_SCHEMA,snapshotSchema:SNAPSHOT_SCHEMA,writeback:false,
    methods:['accept','setView','toggleCluster','toggleBud','step','request','serialize','getProjection','getView','getPlan'],
    errors:['INVALID_OPTIONS','INVALID_PROJECTION','FOREIGN_WORLD','STALE_REVISION','REVISION_CONFLICT','INVALID_VIEW','UNKNOWN_ID','PARENT_COLLAPSED','INVALID_TICK','INVALID_REQUEST','INVALID_SNAPSHOT']};}
  return Object.freeze({version:VERSION,create,restore,describe,FPEError});
})();
if(typeof module!=='undefined'&&module.exports)module.exports=FPE;
