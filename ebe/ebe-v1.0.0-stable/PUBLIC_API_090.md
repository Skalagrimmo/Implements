# EBE v0.9.0 — Public API Freeze Candidate

v0.9.0 freezes the API surface intended for promotion to 1.0 unless the final pre-release hardening pass finds a correctness defect.

The contract is available at runtime:

```lua
local EBE=require("ebe")
local description=EBE.PublicContract.describe()
local fingerprint=EBE.PublicContract.fingerprint()
EBE.PublicContract.assert_package(EBE)
```

Canonical public-contract fingerprint for this release:

```text
ebe-stablehash-v1:851079155
```

Persistence-contract fingerprint:

```text
ebe-stablehash-v1:1931923589
```

Core historical compatibility remains:

```lua
local legacy=EBE.create({...})
```

Current runtime entry point:

```lua
local rt=EBE.Runtime.new({...})
```

v0.9 adds these stable package exports:

```text
EBE.Json
EBE.PersistenceContract
EBE.PublicContract
```

and retains all public exports from v0.8.

The PixelGen bridge remains named `PixelGenV080` because `0.8.0` is the frozen PixelGen EBE bundle schema, not the current PixelGen package version.
