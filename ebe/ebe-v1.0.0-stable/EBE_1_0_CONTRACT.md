# EBE v1.0.0 — Stable Epistemic Runtime Contract

## Thesis

EBE 1.0 models what subjects can observe, remember, believe, know, transmit, collectively accept, filter through institutions, and request as actions. It does **not** own objective world truth; PixelGen remains the world-state authority.

```text
PixelGen truth
  ↓ local evidence
EBE observation → memory → belief → knowledge → interpretation → reaction
  ↓
semantic action request
  ↓ explicit authority boundary
PixelGen accepts / rejects
```

## Stable package surface

The public package and Runtime methods are described by:

```lua
EBE.PublicContract.describe()
EBE.PublicContract.assert_package(EBE)
EBE.PublicContract.fingerprint()
```

Stable public-contract fingerprint:

```text
ebe-stablehash-v1:251571066
```

Stable persistence-contract fingerprint:

```text
ebe-stablehash-v1:254293849
```

The 1.0 freeze explicitly includes historically documented Runtime methods such as `assign_local_observations`, `share`, `get_belief`, `get_knowledge`, and `restore`.

## Versioned subcontracts

Promotion to 1.0 does not renumber mature subformats without a semantic reason:

```text
package/runtime API          1.0.0
runtime snapshot contract    1.0.0
public API contract          1.0.0
action-request schema        0.9.0
action-gateway schema        0.9.0
strict JSON codec            0.9.0
safe-Lua codec               0.9.0
PixelGen EBE bundle schema   0.8.0
```

## Core invariants

```text
Event ≠ Observation ≠ Memory ≠ Belief ≠ Knowledge
message copies ≠ independent evidence
membership ≠ shared knowledge
policy priority ≠ truth
action request ≠ authority
PixelGen remains objective world authority
```

## Persistence guarantees

Stable JSON rejects duplicate keys, null, non-finite numbers, malformed syntax, invalid UTF-8, cycles/metatables/functions during encoding, and over-limit structures. Runtime snapshots validate IDs, sectors, queues, source lineage, action lifecycle, nested action schema versions, action log capacity and sequence integrity.

Historical snapshots `0.3.0` through `0.9.0` migrate in memory to `1.0.0`; unknown future versions fail closed.

## Compatibility policy

Within the 1.x line, incompatible changes to this frozen surface require an explicit contract/version change and migration path. Additive internal implementation changes must preserve the published invariants and serialized compatibility guarantees.
