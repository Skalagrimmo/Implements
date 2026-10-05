import hashlib
import json
from pathlib import Path

MANIFEST_NAME="pixelgen_bundle_manifest.json"
MANIFEST_VERSION="0.6.4"

def sha256_file(path, chunk_size=1024*1024):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        while True:
            chunk=f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def build_manifest(folder, world_fingerprint=None):
    folder=Path(folder)
    if not folder.is_dir():
        raise ValueError(f"bundle folder not found: {folder}")
    files=[]
    for p in sorted(folder.rglob("*")):
        if not p.is_file():
            continue
        if p.name == MANIFEST_NAME:
            continue
        rel=p.relative_to(folder).as_posix()
        files.append({
            "path":rel,
            "bytes":p.stat().st_size,
            "sha256":sha256_file(p),
        })
    return {
        "manifest_version":MANIFEST_VERSION,
        "world_fingerprint":world_fingerprint,
        "file_count":len(files),
        "total_bytes":sum(x["bytes"] for x in files),
        "files":files,
    }

def write_manifest(folder, world_fingerprint=None):
    folder=Path(folder)
    manifest=build_manifest(folder, world_fingerprint=world_fingerprint)
    out=folder/MANIFEST_NAME
    out.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    return out,manifest

def verify_manifest(folder, manifest_path=None):
    folder=Path(folder)
    manifest_path=Path(manifest_path) if manifest_path else folder/MANIFEST_NAME
    if not manifest_path.exists():
        return {"status":"fail","errors":[f"manifest not found: {manifest_path}"],"checked":0}

    data=json.loads(manifest_path.read_text(encoding="utf-8"))
    errors=[]
    checked=0
    listed=set()
    for item in data.get("files",[]):
        rel=item["path"]
        listed.add(rel)
        p=folder/rel
        if not p.exists():
            errors.append(f"missing file: {rel}")
            continue
        if not p.is_file():
            errors.append(f"not a file: {rel}")
            continue
        actual_size=p.stat().st_size
        if actual_size != item.get("bytes"):
            errors.append(f"size mismatch: {rel}")
            continue
        actual_hash=sha256_file(p)
        if actual_hash != item.get("sha256"):
            errors.append(f"hash mismatch: {rel}")
            continue
        checked += 1

    actual={
        p.relative_to(folder).as_posix()
        for p in folder.rglob("*")
        if p.is_file() and p.name != MANIFEST_NAME
    }
    extras=sorted(actual-listed)
    if extras:
        errors.append("unlisted files: " + ", ".join(extras[:20]))

    return {
        "status":"pass" if not errors else "fail",
        "checked":checked,
        "expected":len(data.get("files",[])),
        "errors":errors,
        "world_fingerprint":data.get("world_fingerprint"),
    }
