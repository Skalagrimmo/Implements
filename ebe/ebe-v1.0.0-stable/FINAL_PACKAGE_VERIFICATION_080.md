# EBE v0.8.0 — Final Package Verification

The release ZIP was extracted into a clean directory and validated from that extracted copy.

```text
Lua syntax PASS
historical smoke PASS
historical hardening PASS
renderer forwarding PASS
combined v0.3 → v0.8 regression PASS
v0.8 fuzz PASS
v0.8 soak PASS
canonical action demo PASS
real EBE ↔ PixelGen 1.0 roundtrip PASS
.love root structure PASS
```

The validation environment has no `love` executable, so `.love` runtime execution is not claimed.

Initial package hashes before embedding this verification manifest:

```text
ZIP  452963f635c8302aa8bd3e6fefaa48306287aed515440a5e907adc9fb41aa9a6
LOVE 6cedfbf0db24d393ba7be340eda275e22605346fd3f1d657ec0309d79b354bca
```
