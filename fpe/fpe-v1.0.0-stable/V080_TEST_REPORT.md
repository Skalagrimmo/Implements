# v0.8 tests

PASS: cross-engine fuzz rerun, 48 worlds / 48 mutations, 2,808 clusters / 11,232 buds. Hierarchy fuzz rerun: 2,000 operations.

PASS: handoff 0→3, identical duplicate, reordered object keys, stale/conflicting/foreign revisions, 18 invalid candidates, 1,000 duplicate/stale replay pairs, unchanged caller objects.

PASS: Python malformed nested inputs and invalid bud offsets; canonical bridge regression (30 clusters, 120 buds, 25 changed after revision 3).

PASS: scheduler replay/rates/budgets/fairness and web-core tests. HTML scripts are syntax-checked, not a substitute for real-browser UI testing. Historical v0.6/v0.7 documents describe those releases.
