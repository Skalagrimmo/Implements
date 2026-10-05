from pathlib import Path
import sys, json, tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from pixelgen.palette import load_profile
from pixelgen.gameplay_world import generate_gameplay_world
from pixelgen.fingerprint import world_fingerprint, canonical_json_bytes
from pixelgen.inspect_world import inspect_world
from pixelgen.world_diff import compare_worlds
from pixelgen.bundle_manifest import write_manifest, verify_manifest
from pixelgen.serialization import to_plain

profile=load_profile(ROOT/"profiles"/"techno_animist_gothic.json")

a=generate_gameplay_world(profile,6401,4,3,4)
b=generate_gameplay_world(profile,6401,4,3,4)
c=generate_gameplay_world(profile,6402,4,3,4)

assert a["generator"]["name"]=="PixelGen"
assert a["gameplay"]["version"]=="0.6"

fa=world_fingerprint(a)
fb=world_fingerprint(b)
fc=world_fingerprint(c)
assert fa==fb
assert fa!=fc
assert len(fa)==64

# Generator label alone must not change semantic fingerprint.
clone=to_plain(a)
clone["generator"]["version"]="99.99"
clone["gameplay"]["generator_version"]="99.99"
assert world_fingerprint(clone)==fa

info=inspect_world(a)
assert info["fingerprint"]==fa
assert info["dimensions"]["sectors"]==12
assert info["navigation"]["main_path_nodes"]>=1

same=compare_worlds(a,b)
diff=compare_worlds(a,c)
assert same["identical"]
assert not diff["identical"]

with tempfile.TemporaryDirectory() as td:
    d=Path(td)
    (d/"a.txt").write_text("alpha",encoding="utf-8")
    (d/"b.bin").write_bytes(b"\x00\x01\x02")
    out,manifest=write_manifest(d,world_fingerprint=fa)
    assert out.exists()
    assert manifest["file_count"]==2
    ok=verify_manifest(d)
    assert ok["status"]=="pass"
    (d/"a.txt").write_text("changed",encoding="utf-8")
    bad=verify_manifest(d)
    assert bad["status"]=="fail"
    assert any("mismatch" in x for x in bad["errors"])

print("PixelGen v0.6.4 tests passed")
