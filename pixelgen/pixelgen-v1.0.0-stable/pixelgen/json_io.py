"""Strict JSON parsing for public PixelGen artifacts.

Python's default json module accepts NaN/Infinity and silently keeps the last
of duplicate object keys.  Public contract artifacts reject both behaviors so
hashing/validation cannot depend on parser quirks.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class StrictJSONError(ValueError):
    pass


def _reject_constant(value: str):
    raise StrictJSONError(f"non-finite JSON constant is not allowed: {value}")


def _unique_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise StrictJSONError(f"duplicate JSON object key: {key!r}")
        out[key] = value
    return out


def strict_json_loads(text: str) -> Any:
    try:
        return json.loads(
            text,
            parse_constant=_reject_constant,
            object_pairs_hook=_unique_object,
        )
    except StrictJSONError:
        raise
    except json.JSONDecodeError as exc:
        raise StrictJSONError(f"invalid JSON: {exc.msg} at line {exc.lineno} column {exc.colno}") from exc


def read_json(path: str | Path) -> Any:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise StrictJSONError(f"JSON must be UTF-8: {path}") from exc
    return strict_json_loads(text)


__all__ = ["StrictJSONError", "strict_json_loads", "read_json"]
