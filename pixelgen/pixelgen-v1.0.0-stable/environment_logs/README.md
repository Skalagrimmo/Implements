# Environment logs

Run the same suite in every environment and copy the resulting `*.envlog.json` files into one folder.

Recommended first pass:

```bash
python cli.py doctor
python cli.py env-log --label PC --suite quick
python cli.py env-log --label Termux --suite quick
python cli.py env-log --label UserLAnd --suite quick
python cli.py env-log --label Pydroid --suite quick
```

Then compare on any machine:

```bash
python compare_env_logs.py environment_logs   --json-out environment_comparison.json   --md-out environment_comparison.md
```

After quick passes everywhere, repeat with `--suite standard`.
