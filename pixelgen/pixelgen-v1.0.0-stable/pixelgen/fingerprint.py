import hashlib
import json
from copy import deepcopy
from .serialization import to_plain

VOLATILE_TOP_LEVEL = {
    "progression_simulation",
    "visual_quality",
}

def normalized_world(world, include_visual=False):
    data = deepcopy(to_plain(world))
    for key in list(VOLATILE_TOP_LEVEL):
        if key == "visual_quality" and include_visual:
            continue
        data.pop(key, None)

    # The fingerprint identifies semantic generated content, not the version label
    # of the tool which read/exported it.
    data.pop("generator", None)
    data.pop("schema_versions", None)
    gameplay=data.get("gameplay")
    if isinstance(gameplay, dict):
        gameplay.pop("generator_version", None)

    return data

def canonical_json_bytes(world, include_visual=False):
    data=normalized_world(world, include_visual=include_visual)
    text=json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",",":"),
        allow_nan=False,
    )
    return text.encode("utf-8")

def world_fingerprint(world, include_visual=False):
    return hashlib.sha256(canonical_json_bytes(world, include_visual=include_visual)).hexdigest()

def short_fingerprint(world, length=12):
    if not isinstance(length,int) or not 8 <= length <= 64:
        raise ValueError("fingerprint display length must be 8..64")
    return world_fingerprint(world)[:length]
