"""Crash-resistant atomic file and directory helpers for PixelGen public artifacts."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid
from typing import Any


def _fsync_dir(path: Path) -> None:
    """Best-effort parent directory sync; unsupported platforms simply skip it."""
    try:
        flags = getattr(os, "O_DIRECTORY", 0) | os.O_RDONLY
        fd = os.open(str(path), flags)
    except (OSError, AttributeError):
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def atomic_write_bytes(path: str | Path, data: bytes) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        _fsync_dir(path.parent)
        return path
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def atomic_write_text(path: str | Path, text: str, *, encoding: str = "utf-8") -> Path:
    return atomic_write_bytes(path, text.encode(encoding))


def atomic_write_json(path: str | Path, value: Any) -> Path:
    payload = json.dumps(
        value,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"
    return atomic_write_text(path, payload)


def make_staging_directory(target: str | Path) -> Path:
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f".{target.name}.stage.", dir=str(target.parent)))


def commit_staged_directory(stage: str | Path, target: str | Path) -> Path:
    """Replace target with a completely prepared directory, rolling back ordinary failures.

    POSIX does not provide a portable atomic exchange for non-empty directories via Python,
    so replacement uses a sibling backup and rollback.  The important contract is that all
    validation and serialization happen in the staging tree before the destination is touched.
    """
    stage = Path(stage)
    target = Path(target)
    if not stage.is_dir():
        raise ValueError("staged bundle directory does not exist")
    target.parent.mkdir(parents=True, exist_ok=True)

    backup: Path | None = None
    if target.exists():
        backup = target.parent / f".{target.name}.backup.{uuid.uuid4().hex}"
        os.replace(target, backup)
    try:
        os.replace(stage, target)
        _fsync_dir(target.parent)
    except Exception:
        if backup is not None and backup.exists() and not target.exists():
            os.replace(backup, target)
            _fsync_dir(target.parent)
        raise
    else:
        if backup is not None and backup.exists():
            shutil.rmtree(backup)
        _fsync_dir(target.parent)
    return target


__all__ = [
    "atomic_write_bytes",
    "atomic_write_text",
    "atomic_write_json",
    "make_staging_directory",
    "commit_staged_directory",
]
