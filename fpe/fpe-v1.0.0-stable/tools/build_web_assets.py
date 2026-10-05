#!/usr/bin/env python3
"""Build checked-in browser data and the single-file FPE demo."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
projection = json.loads((ROOT / "data/projections/canonical_initial.json").read_text(encoding="utf-8"))
projection_text = json.dumps(projection, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
assignment = "const FPE_CANONICAL_PROJECTION=" + projection_text + ";\n"
(ROOT / "web/canonical_projection.js").write_text(assignment, encoding="utf-8")

html = (ROOT / "web/index.html").read_text(encoding="utf-8")
core = (ROOT / "web/fpe_core.js").read_text(encoding="utf-8")
html = html.replace('<script src="fpe_core.js"></script>', "<script>\n" + core + "\n</script>")
html = html.replace('<script src="canonical_projection.js"></script>', "<script>\n" + assignment + "</script>")
scheduler = (ROOT / "web/fpe_scheduler.js").read_text(encoding="utf-8")
html = html.replace('<script src="fpe_scheduler.js"></script>', "<script>\n" + scheduler + "\n</script>")
handoff = (ROOT / "web/fpe_handoff.js").read_text(encoding="utf-8")
html = html.replace('<script src="fpe_handoff.js"></script>', "<script>\n" + handoff + "\n</script>")
api = (ROOT / "web/fpe.js").read_text(encoding="utf-8")
html = html.replace('<script src="fpe.js"></script>', "<script>\n" + api + "\n</script>")
version=(ROOT / "VERSION").read_text(encoding="utf-8").strip()
(ROOT / f"fpe-v{version}-demo.html").write_text(html, encoding="utf-8")
