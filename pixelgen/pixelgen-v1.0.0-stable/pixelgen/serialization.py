import math
from pathlib import Path


def to_plain(value):
    if hasattr(value, "to_dict"):
        return to_plain(value.to_dict())
    if isinstance(value, dict):
        return {k: to_plain(v) for k, v in value.items() if not str(k).startswith("_")}
    if isinstance(value, (list, tuple)):
        return [to_plain(v) for v in value]
    if isinstance(value, set):
        return [to_plain(v) for v in sorted(value)]
    return value


def lua_quote(text):
    text = str(text)
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    text = text.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")
    return '"' + text + '"'


def lua_serialize(value, indent=0, in_array=False):
    pad = "  " * indent
    next_pad = "  " * (indent + 1)
    value = to_plain(value)
    if value is None:
        return "0" if in_array else "nil"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Lua export does not support NaN/Infinity")
        return repr(value)
    if isinstance(value, str):
        return lua_quote(value)
    if isinstance(value, list):
        if not value:
            return "{}"
        items = [next_pad + lua_serialize(v, indent+1, True) + "," for v in value]
        return "{\n" + "\n".join(items) + "\n" + pad + "}"
    if isinstance(value, dict):
        if not value:
            return "{}"
        items = []
        for k in sorted(value, key=lambda x: str(x)):
            v=value[k]
            # A missing optional dictionary field is represented by omission.
            # This keeps exported tables compact and avoids explicit `key = nil`.
            if v is None:
                continue
            if isinstance(k, str) and k.isidentifier():
                key = k
            else:
                key = "[" + lua_serialize(k, indent+1, False) + "]"
            items.append(next_pad + key + " = " + lua_serialize(v, indent+1, False) + ",")
        return "{\n" + "\n".join(items) + "\n" + pad + "}"
    raise TypeError(f"unsupported Lua export type: {type(value).__name__}")


def write_lua_return(value, out_path):
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("return " + lua_serialize(value) + "\n", encoding="utf-8")
    return p
