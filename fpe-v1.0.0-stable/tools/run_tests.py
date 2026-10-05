#!/usr/bin/env python3
"""Run the local release gates from any working directory."""
import subprocess
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
commands = [[sys.executable, 'tools/build_web_assets.py']]
commands += [[sys.executable, 'tests/' + name] for name in ['test_bridge.py', 'test_validation.py', 'test_cross_runtime_fingerprint.py', 'test_fresh_process_determinism.py']]
commands += [['node', 'tests/' + name] for name in ['test_web_core.js', 'test_scheduler.js', 'test_handoff.js', 'fuzz_hierarchy.js', 'test_public_api.js', 'test_action_requests.js', 'test_persistence.js', 'fuzz_persistence.js', 'test_rc_hardening.js', 'test_v100_promotion.js']]
for command in commands:
    subprocess.run(command, cwd=root, check=True)
print('All local release gates PASS')
