"use strict";
const FPE06 = (() => {
  const GLYPHS = ['#','%','&','8','@','+','=','-',':','.','/','\\'];
  const VERIFIED_PROJECTIONS=new WeakSet();
  function deepFreeze(value,seen=new WeakSet()){if(!value||typeof value!=='object'||seen.has(value))return value;seen.add(value);for(const k of Object.keys(value))deepFreeze(value[k],seen);return Object.freeze(value);}
  function isDeepFrozen(value,seen=new WeakSet()){if(!value||typeof value!=='object'||seen.has(value))return true;if(!Object.isFrozen(value))return false;seen.add(value);return Object.keys(value).every(k=>isDeepFrozen(value[k],seen));}
  function assertJsonData(value,path='projection',seen=new WeakSet(),depth=0){
    if(depth>64)throw new Error(path+' exceeds maximum JSON depth');
    if(value===null||typeof value==='string'||typeof value==='boolean')return;
    if(typeof value==='number'){if(!Number.isFinite(value))throw new Error(path+' contains non-finite number');return;}
    if(typeof value!=='object')throw new Error(path+' is not JSON data');
    if(seen.has(value))throw new Error(path+' contains a cycle');seen.add(value);
    if(Object.getOwnPropertySymbols(value).length)throw new Error(path+' contains symbol properties');
    if(Array.isArray(value)){
      const keys=Object.keys(value);if(keys.length!==value.length||keys.some((k,i)=>k!==String(i)))throw new Error(path+' must be a dense JSON array');
      for(let i=0;i<value.length;i++){const d=Object.getOwnPropertyDescriptor(value,String(i));if(!d||!('value' in d)||!d.enumerable)throw new Error(path+' contains an accessor');assertJsonData(d.value,path+'['+i+']',seen,depth+1);}
      seen.delete(value);return;
    }
    const proto=Object.getPrototypeOf(value);if(proto!==null&&Object.getPrototypeOf(proto)!==null)throw new Error(path+' must contain only plain objects');
    const keys=Object.keys(value),own=Reflect.ownKeys(value);if(keys.length!==own.length)throw new Error(path+' contains hidden properties');
    for(const k of keys){const d=Object.getOwnPropertyDescriptor(value,k);if(!d||!('value' in d)||!d.enumerable)throw new Error(path+' contains an accessor');assertJsonData(d.value,path+'.'+k,seen,depth+1);}
    seen.delete(value);
  }
  function hash32(s){ let h=2166136261>>>0; for(let i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619);} return h>>>0; }
  function rand01(key){ return (hash32(key)%1000000)/1000000; }
  // Synchronous SHA-256 keeps projection integrity checks available in both
  // browsers and Node without depending on WebCrypto's async API.
  function utf8Bytes(text){
    const out=[];
    for(let i=0;i<text.length;i++){let cp=text.charCodeAt(i);
      if(cp>=0xd800&&cp<=0xdbff){if(i+1>=text.length)throw new Error('invalid unpaired UTF-16 surrogate');const lo=text.charCodeAt(++i);if(lo<0xdc00||lo>0xdfff)throw new Error('invalid unpaired UTF-16 surrogate');cp=0x10000+((cp-0xd800)<<10)+(lo-0xdc00);}
      else if(cp>=0xdc00&&cp<=0xdfff)throw new Error('invalid unpaired UTF-16 surrogate');
      if(cp<0x80)out.push(cp);else if(cp<0x800)out.push(0xc0|(cp>>6),0x80|(cp&63));else if(cp<0x10000)out.push(0xe0|(cp>>12),0x80|((cp>>6)&63),0x80|(cp&63));else out.push(0xf0|(cp>>18),0x80|((cp>>12)&63),0x80|((cp>>6)&63),0x80|(cp&63));
    }
    return Uint8Array.from(out);
  }
  function sha256(text){
    const bytes=utf8Bytes(text),K=new Uint32Array([
      0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
      0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
      0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
      0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
      0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
      0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
      0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
      0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]);
    const bitLen=bytes.length*8,total=((bytes.length+9+63)>>6)<<6,msg=new Uint8Array(total);msg.set(bytes);msg[bytes.length]=0x80;
    const dv=new DataView(msg.buffer);dv.setUint32(total-8,Math.floor(bitLen/0x100000000),false);dv.setUint32(total-4,bitLen>>>0,false);
    const h=new Uint32Array([0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]),w=new Uint32Array(64),rotr=(x,n)=>(x>>>n)|(x<<(32-n));
    for(let off=0;off<total;off+=64){
      for(let i=0;i<16;i++)w[i]=dv.getUint32(off+i*4,false);
      for(let i=16;i<64;i++){const a=w[i-15],b=w[i-2],s0=rotr(a,7)^rotr(a,18)^(a>>>3),s1=rotr(b,17)^rotr(b,19)^(b>>>10);w[i]=(w[i-16]+s0+w[i-7]+s1)>>>0;}
      let [a,b,c,d,e,f,g,hh]=h;
      for(let i=0;i<64;i++){const S1=rotr(e,6)^rotr(e,11)^rotr(e,25),ch=(e&f)^((~e)&g),t1=(hh+S1+ch+K[i]+w[i])>>>0,S0=rotr(a,2)^rotr(a,13)^rotr(a,22),maj=(a&b)^(a&c)^(b&c),t2=(S0+maj)>>>0;hh=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;}
      h[0]=(h[0]+a)>>>0;h[1]=(h[1]+b)>>>0;h[2]=(h[2]+c)>>>0;h[3]=(h[3]+d)>>>0;h[4]=(h[4]+e)>>>0;h[5]=(h[5]+f)>>>0;h[6]=(h[6]+g)>>>0;h[7]=(h[7]+hh)>>>0;
    }
    return [...h].map(x=>x.toString(16).padStart(8,'0')).join('');
  }
  const FLOAT_STATE=new Set(['control_strength','stability','alert','front_tension','front_activity']);
  const FLOAT_PROJECTION=new Set(['cohesion','breakup_resistance','agitation','collapse_bias','damage_proxy','update_rate']);
  function projectionFloatPath(path){
    if(path.length===2&&path[0]==='layout'&&(path[1]==='sector_spacing'||path[1]==='local_bud_offset'))return true;
    if(path.length===4&&path[0]==='clusters'&&Number.isInteger(path[1])&&path[2]==='state'&&FLOAT_STATE.has(path[3]))return true;
    return path.length===4&&path[0]==='clusters'&&Number.isInteger(path[1])&&path[2]==='projection'&&FLOAT_PROJECTION.has(path[3]);
  }
  // PixelGen bridge fingerprints use Python json.dumps(sort_keys=True,
  // ensure_ascii=False). Numeric fields produced as Python floats retain '.0'.
  function pythonFloatNumber(v){
    if(!Number.isFinite(v))throw new Error('non-finite projection number');
    if(Object.is(v,-0))return '-0.0';
    if(Number.isInteger(v))return String(v)+'.0';
    const a=Math.abs(v);
    if(a!==0&&a<1e-4){
      const parts=v.toExponential().split('e'),exp=Number(parts[1]);
      return parts[0]+'e'+(exp<0?'-':'+')+String(Math.abs(exp)).padStart(2,'0');
    }
    return String(v);
  }
  function projectionCanonical(v,path=[]){
    if(v===null)return 'null';
    if(typeof v==='number'){if(projectionFloatPath(path))return pythonFloatNumber(v);return JSON.stringify(v);}
    if(typeof v!=='object')return JSON.stringify(v);
    if(Array.isArray(v))return '['+v.map((x,i)=>projectionCanonical(x,path.concat(i))).join(',')+']';
    return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+projectionCanonical(v[k],path.concat(k))).join(',')+'}';
  }
  function projectionFingerprint(p){const copy={...p};delete copy.projection_fingerprint;return sha256(projectionCanonical(copy));}
  function assertProjection(p){
    if(p&&typeof p==='object'&&VERIFIED_PROJECTIONS.has(p))return p;
    assertJsonData(p);
    const obj=(v)=>v!==null&&typeof v==='object'&&!Array.isArray(v);
    const need=(ok,msg)=>{if(!ok)throw new Error(msg);};
    const num=(v,lo,hi)=>typeof v==='number'&&Number.isFinite(v)&&v>=lo&&v<=hi;
    const text=(v)=>typeof v==='string'&&v.length>0;
    const hex=(v)=>typeof v==='string'&&/^[0-9a-f]{64}$/.test(v);
    need(obj(p)&&obj(p.source)&&obj(p.layout)&&obj(p.authority)&&obj(p.summary),'missing projection objects');
    need(p.fpe_version==='0.6.0'&&p.bridge_version==='0.6.0','unsupported bridge/runtime projection version');
    need(p.authority.objective_state_owner==='PixelGen'&&p.authority.geometry_owner==='FPE'&&p.authority.writeback==='disabled_in_v0.6','invalid authority');
    need(hex(p.projection_fingerprint)&&hex(p.source.pixelgen_world_fingerprint),'invalid fingerprints');
    need(Number.isSafeInteger(p.source.seed),'invalid seed');
    for(const key of ['state_revision','state_tick'])need(Number.isSafeInteger(p.source[key])&&p.source[key]>=0,'invalid source clock');
    need(num(p.layout.sector_spacing,0.001,1000000)&&num(p.layout.local_bud_offset,0.001,1000000)&&p.layout.buds_per_sector===4,'invalid layout');
    if(!p || p.schema!=="fpe.pixelgen_hierarchy/0.6.0") throw new Error("unsupported FPE projection schema");
    if(p.mode!=="read_only_hierarchical_projection") throw new Error("v0.6 viewer accepts read-only hierarchical projections only");
    if(!p.hierarchy || p.hierarchy.schema!=="fpe.view_hierarchy/0.6.0") throw new Error("missing FPE hierarchy contract");
    if(JSON.stringify(p.hierarchy.levels)!==JSON.stringify(["world","cluster","bud","geometry"])) throw new Error("invalid hierarchy levels");
    need(p.hierarchy.initial_detail==='cluster_proxy'&&p.hierarchy.expansion_state_owner==='viewer'&&p.hierarchy.semantic_effect==='none','invalid hierarchy authority');
    const [cols,rows]=p.source.dimensions||[];
    if(!Number.isSafeInteger(cols)||!Number.isSafeInteger(rows)||cols<1||rows<1) throw new Error("invalid source dimensions");
    need(p.layout.cluster_kind==='pixelgen_sector','invalid cluster kind');
    if(!Array.isArray(p.clusters)||p.clusters.length!==cols*rows) throw new Error("cluster count mismatch");
    const clusterIds=new Set(),budIds=new Set(),coordinates=new Set();
    for(const c of p.clusters){
      need(obj(c)&&obj(c.state)&&obj(c.projection)&&obj(c.source),'invalid cluster objects');
      need(Array.isArray(c.sector)&&c.sector.length===2&&c.sector.every(Number.isSafeInteger),'invalid sector');
      const [x,y]=c.sector,key=`${x},${y}`;
      need(x>=0&&x<cols&&y>=0&&y<rows&&!coordinates.has(key),'duplicate/outside sector');coordinates.add(key);
      need(c.id===`sector_${x}_${y}`,'noncanonical cluster id');
      for(const k of ['cohesion','breakup_resistance','agitation','collapse_bias','damage_proxy','update_rate'])need(num(c.projection[k],0,1),'invalid projection number');
      for(const k of ['stability','alert','front_tension','front_activity'])need(num(c.state[k],0,1),'invalid state number');
      need(num(c.state.control_strength,0,1.75)&&['quiet','active','tense','volatile'].includes(c.state.front_status),'invalid cluster state');
      need(Array.isArray(c.source.front_ids)&&c.source.front_ids.every(text),'invalid fronts');
      need(c.source.territory_id===null||text(c.source.territory_id),'invalid territory');
      if(typeof c.id!=="string"||clusterIds.has(c.id)) throw new Error("invalid or duplicate cluster id");clusterIds.add(c.id);
      if(!Array.isArray(c.buds)||c.buds.length!==4) throw new Error(`cluster ${c.id} must contain 4 buds`);
      for(const [i,b] of c.buds.entries()){
        need(obj(b)&&b.index===i&&b.id===`${c.id}_bud_${i}`&&text(b.seed_key),'invalid bud identity');
        need(JSON.stringify(b.offset)===JSON.stringify([[-1,-1],[1,-1],[-1,1],[1,1]][i]),'invalid bud offset');
        if(b.type!=="STRAIGHT"&&b.type!=="CURVED") throw new Error(`invalid bud type in ${c.id}`);if(typeof b.id!=="string"||budIds.has(b.id)) throw new Error(`invalid or duplicate bud id in ${c.id}`);budIds.add(b.id);
      }
    }
    const straight=p.clusters.reduce((n,c)=>n+c.buds.filter(b=>b.type==='STRAIGHT').length,0),curved=budIds.size-straight;
    for(const k of ['cluster_count','bud_count','territory_cluster_count','front_cluster_count','straight_bud_count','curved_bud_count'])need(Number.isSafeInteger(p.summary[k])&&p.summary[k]>=0,'invalid summary integer');
    need(p.summary.cluster_count===p.clusters.length&&p.summary.bud_count===budIds.size,'invalid summary counts');
    need(Number.isSafeInteger(p.summary.territory_cluster_count)&&p.summary.territory_cluster_count===p.clusters.filter(c=>c.source.territory_id!==null).length,'invalid territory summary');
    need(Number.isSafeInteger(p.summary.front_cluster_count)&&p.summary.front_cluster_count===p.clusters.filter(c=>c.source.front_ids.length>0).length,'invalid front summary');
    need(p.summary.straight_bud_count===straight&&p.summary.curved_bud_count===curved,'invalid bud type summary');
    need(projectionFingerprint(p)===p.projection_fingerprint,'projection_fingerprint mismatch');
    if(isDeepFrozen(p))VERIFIED_PROJECTIONS.add(p);
    return p;
  }
  function sectorKey(sx,sy){return `${sx},${sy}`;}
  function sectorCenter(p,sx,sy){const [cols,rows]=p.source.dimensions,spacing=p.layout.sector_spacing;return {x:(sx-(cols-1)/2)*spacing,y:3,z:(sy-(rows-1)/2)*spacing};}
  function makeStraightBud(center,size){
    const pts=[],s=size/2;for(let x=-1;x<=1;x+=2)for(let y=-1;y<=1;y+=2)for(let z=-1;z<=1;z+=2)pts.push({x:center.x+x*s,y:center.y+y*s,z:center.z+z*s});
    const edges=[];for(let i=0;i<pts.length;i++)for(let j=i+1;j<pts.length;j++){const a=pts[i],b=pts[j],d=(a.x!==b.x?1:0)+(a.y!==b.y?1:0)+(a.z!==b.z?1:0);if(d===1)edges.push([i,j,0]);}return {points:pts,edges};
  }
  function makeCurvedBud(center,size,key){
    const n=14,pts=[],g=Math.PI*(3-Math.sqrt(5)),r=size/1.8;for(let i=0;i<n;i++){const y=1-(i/(n-1))*2,rr=Math.sqrt(Math.max(0,1-y*y)),t=g*i;pts.push({x:center.x+Math.cos(t)*rr*r,y:center.y+y*r*.8+size*.35,z:center.z+Math.sin(t)*rr*r});}
    const edges=[],seen=new Set();for(let i=0;i<n;i++){const ds=[];for(let j=0;j<n;j++)if(i!==j){const a=pts[i],b=pts[j];ds.push([j,Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z)]);}ds.sort((a,b)=>a[1]-b[1]);for(let k=0;k<3;k++){const j=ds[k][0],ek=i<j?`${i}_${j}`:`${j}_${i}`;if(seen.has(ek))continue;seen.add(ek);edges.push([i,j,.35+rand01(`${key}:edge:${ek}`)*.25]);}}return {points:pts,edges};
  }
  function buildBudGeometry(projection,cluster,bud,center){
    const local=projection.layout.local_bud_offset,c={x:center.x+bud.offset[0]*local,y:3.0+rand01(`${bud.seed_key}:height`)*1.8,z:center.z+bud.offset[1]*local};
    const geom=(bud.type==="STRAIGHT"?makeStraightBud:makeCurvedBud)(c,3.2,bud.seed_key);
    const nodes=geom.points.map((pt,ni)=>({base:pt,rnd:rand01(`${bud.seed_key}:node:${ni}:rnd`),phase:rand01(`${bud.seed_key}:node:${ni}:phase`)*Math.PI*2,glyphIdx:Math.floor(rand01(`${bud.seed_key}:node:${ni}:glyph`)*GLYPHS.length)}));
    return {...bud,center:c,edges:geom.edges,nodes,cluster_id:cluster.id};
  }
  function buildGeometryPlan(projection){const p=assertProjection(projection),result=[];for(const cluster of p.clusters){const center=sectorCenter(p,...cluster.sector);result.push({...cluster,center,buds:cluster.buds.map(b=>buildBudGeometry(p,cluster,b,center))});}return result;}
  function emptyViewState(){return {expandedClusters:[],expandedBuds:[]};}
  function normalizeViewState(projection,state){
    const p=assertProjection(projection),s=state||{},clusterIds=new Set(p.clusters.map(c=>c.id)),budParent=new Map();for(const c of p.clusters)for(const b of c.buds)budParent.set(b.id,c.id);
    const expandedClusters=[...new Set(Array.isArray(s.expandedClusters)?s.expandedClusters:[])].filter(id=>clusterIds.has(id)).sort(),expandedSet=new Set(expandedClusters);
    const expandedBuds=[...new Set(Array.isArray(s.expandedBuds)?s.expandedBuds:[])].filter(id=>budParent.has(id)&&expandedSet.has(budParent.get(id))).sort();return {expandedClusters,expandedBuds};
  }
  function toggleCluster(projection,state,clusterId){
    const s=normalizeViewState(projection,state),clusters=new Set(s.expandedClusters),buds=new Set(s.expandedBuds);
    if(clusters.has(clusterId)){clusters.delete(clusterId);const c=projection.clusters.find(x=>x.id===clusterId);if(c)for(const b of c.buds)buds.delete(b.id);}else if(projection.clusters.some(c=>c.id===clusterId))clusters.add(clusterId);
    return normalizeViewState(projection,{expandedClusters:[...clusters],expandedBuds:[...buds]});
  }
  function toggleBud(projection,state,budId){
    const s=normalizeViewState(projection,state),buds=new Set(s.expandedBuds),parent=projection.clusters.find(c=>c.buds.some(b=>b.id===budId));if(!parent||!s.expandedClusters.includes(parent.id))return s;
    if(buds.has(budId))buds.delete(budId);else buds.add(budId);return normalizeViewState(projection,{expandedClusters:s.expandedClusters,expandedBuds:[...buds]});
  }
  function buildHierarchyPlan(projection,state){
    const p=assertProjection(projection),s=normalizeViewState(p,state),openC=new Set(s.expandedClusters),openB=new Set(s.expandedBuds),items=[];
    for(const cluster of p.clusters){const center=sectorCenter(p,...cluster.sector);if(!openC.has(cluster.id)){items.push({kind:"cluster_proxy",id:cluster.id,cluster,center});continue;}for(const bud of cluster.buds){const local=p.layout.local_bud_offset,budCenter={x:center.x+bud.offset[0]*local,y:3.0+rand01(`${bud.seed_key}:height`)*1.8,z:center.z+bud.offset[1]*local};if(!openB.has(bud.id))items.push({kind:"bud_proxy",id:bud.id,cluster,bud,center:budCenter});else items.push({kind:"geometry",id:bud.id,cluster,bud:buildBudGeometry(p,cluster,bud,center),center:budCenter});}}
    const counts={cluster_proxy:0,bud_proxy:0,geometry:0,nodes:0,edges:0};for(const item of items){counts[item.kind]++;if(item.kind==="geometry"){counts.nodes+=item.bud.nodes.length;counts.edges+=item.bud.edges.length;}}return {state:s,items,counts};
  }
  function viewStateFingerprint(projection,state){const s=normalizeViewState(projection,state);return `fpe-view-v1:${hash32(JSON.stringify(s)).toString(16).padStart(8,'0')}`;}
  return {GLYPHS,hash32,rand01,sha256,projectionFingerprint,deepFreeze,assertProjection,sectorKey,sectorCenter,buildGeometryPlan,emptyViewState,normalizeViewState,toggleCluster,toggleBud,buildHierarchyPlan,viewStateFingerprint};
})();
if(typeof module!=="undefined"&&module.exports)module.exports=FPE06;
