'use strict';
const A=require('assert'),F=require('../web/fpe'),p=require('../data/projections/canonical_initial.json'),q=require('../data/projections/canonical_after.json'),fixture=require('../data/promotion/v0.12-semantic-vectors.json'),T=require('./v100_trace');
A.equal(F.version,'1.0.0');A.equal(fixture.source_runtime,'0.12.0');A.equal(fixture.vectors.length,64);
for(const v of fixture.vectors)A.equal(T.digest(T.trace(F,p,q,v.seed)),v.digest,`0.12→1.0 semantic parity failed at seed ${v.seed}`);
const d=F.describe();
A.deepStrictEqual(d.methods,['accept','setView','toggleCluster','toggleBud','step','request','serialize','getProjection','getView','getPlan']);
A.deepStrictEqual(d.errors,['INVALID_OPTIONS','INVALID_PROJECTION','FOREIGN_WORLD','STALE_REVISION','REVISION_CONFLICT','INVALID_VIEW','UNKNOWN_ID','PARENT_COLLAPSED','INVALID_TICK','INVALID_REQUEST','INVALID_SNAPSHOT']);
A.equal(d.projectionSchema,'fpe.pixelgen_hierarchy/0.6.0');A.equal(d.actionRequestSchema,'fpe.action_request/0.10.0');A.equal(d.snapshotSchema,'fpe.runtime_snapshot/0.11.0');A.equal(d.writeback,false);
console.log('v1.0 promotion parity PASS: 64 frozen v0.12 semantic traces, API/schema/authority freeze unchanged');
