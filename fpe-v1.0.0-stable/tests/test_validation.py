import copy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fpe.bridge import load_json, validate_projection, projection_fingerprint
p = load_json(Path(__file__).resolve().parents[1] / 'data/projections/canonical_initial.json')
assert not validate_projection(p)
for key in ['source', 'layout', 'hierarchy', 'summary', 'clusters', 'authority']:
    for bad in [None, True, 12, 'bad']:
        q = copy.deepcopy(p)
        q[key] = bad
        q['projection_fingerprint'] = projection_fingerprint(q)
        assert validate_projection(q), (key, bad)
for key in ['buds', 'state', 'projection']:
    q = copy.deepcopy(p)
    q['clusters'][0][key] = 7
    assert validate_projection(q)
q = copy.deepcopy(p)
q['clusters'][0]['buds'][0]['offset'] = [9, 9]
q['projection_fingerprint'] = projection_fingerprint(q)
assert validate_projection(q)
print('Python malformed validation PASS')
