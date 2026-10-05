'use strict';
const path=require('path'),F=require('../web/fpe'),p=require('../data/projections/canonical_initial.json'),q=require('../data/projections/canonical_after.json'),T=require('./v100_trace');
const seed=Number(process.argv[2]||1);process.stdout.write(T.digest(T.trace(F,p,q,seed))+'\n');
