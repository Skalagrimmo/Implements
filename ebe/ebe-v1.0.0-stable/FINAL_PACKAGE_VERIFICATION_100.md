# EBE v1.0.0 — Final Package Verification

The release candidate archive was extracted into a clean directory and tested from that extracted tree.

## Extracted-package gate

```text
Lua syntax gate                  97 files PASS
combined regression              PASS
v1.0 fuzz                        500 simulations PASS
v1.0 soak                        5,000 requests / 10 checkpoints PASS
v0.9 → v1.0 semantic parity      PASS
real EBE 1.0 ↔ PixelGen 1.0 loop PASS
```

Promotion parity retained the canonical metadata-stripped semantic hash:

```text
676699684
```

The five canonical v0.9/v1.0 demo outputs were byte-identical.

## Source-level historical gate

Before packaging, the full historical line was rerun:

```text
v0.2.1 smoke/hardening/renderer regression PASS
v0.3 fuzz 200 PASS
v0.4 fuzz 120 PASS
v0.5 fuzz 120 PASS
v0.6 fuzz 120 PASS
v0.7 fuzz 120 PASS
v0.8 fuzz 160 PASS
v0.9 fuzz 160 PASS
v0.6 / v0.7 / v0.8 / v0.9 soaks PASS
strict JSON extended corpus: 10,001 hostile rejects + 1,000 valid roundtrips PASS
```

## LÖVE artifact

The `.love` archive is built from the same final source tree with `main.lua` and `conf.lua` at archive root. The current test environment does not provide a LÖVE executable, so an actual graphical LÖVE launch is **not** claimed as PASS; runtime launch remains a device/Windows smoke check.

The final ZIP is repacked only to embed this verification report; a post-repack smoke gate is run again against the final archive.
