# EBE v0.9.0 — Persistence / Hostile Input Contract

## Purpose

v0.9.0 freezes EBE's pre-1.0 persistence boundary. Persistence data is treated as data, never executable code.

## Runtime snapshot identity

```text
snapshot.version          = 0.9.0
snapshot.contract_version = 0.9.0
```

Accepted historical runtime snapshots:

```text
0.3.0
0.4.0
0.5.0
0.6.0
0.7.0
0.8.0
0.9.0
```

Historical snapshots are migrated in memory to the current metadata contract. Unknown future versions fail closed.

## Stable persistence formats

### Strict JSON

Preferred stable format:

```lua
local EBE=require("ebe")
local snap=rt:snapshot()
EBE.Snapshot.write_runtime_json_atomic("save.json",snap)

local loaded=EBE.Snapshot.read_runtime_json("save.json")
local restored=EBE.Runtime.restore(loaded)
```

The JSON reader rejects:

```text
duplicate object keys
null
NaN / Infinity or overflow to infinity
trailing data
bad escapes
control characters in strings
excessive nesting / node count
```

`null` is deliberately outside the EBE persistence subset because Lua runtime snapshots have no semantic null value.

### Safe Lua subset

Legacy Lua-table snapshots remain readable, but `Snapshot.read_lua()` no longer calls `dofile()` or `loadfile()` on the file.

Accepted grammar is limited to the literal subset produced by `Snapshot.to_lua()`:

```text
return <literal table>
```

Allowed values:

```text
tables
finite numbers
strings
booleans
nil literals
```

Function calls, operators, control flow, globals and arbitrary statements are rejected.

## Runtime validation

Before restore or stable write, EBE validates:

```text
finite tick / seed
agent key ↔ id consistency
valid nonnegative integer sectors
bounded agents/entities/queues
action request key ↔ id consistency
unique action order
source_count ↔ independent root count
bounded evidence-root lineage
bounded route lineage
valid action lifecycle
exported action ↔ exported event identity
no table cycles
no metatables
no functions/userdata/threads
bounded depth/node/string size
```

## Action authority hardening

A new action request always begins:

```text
pending
```

A PixelGen world action may only become `applied` after it has been explicitly exported.

PixelGen feedback correlation requires:

```text
cause_event_id == action_request.id
request.status == exported
exported event identity matches request
subject_type matches request target_type (when supplied)
subject_id matches request target_id (when supplied)
```

A forged event with only a matching `cause_event_id` is insufficient.

## Transactional write behavior

`write_runtime_json_atomic()` and `write_runtime_lua_atomic()` use:

```text
serialize + validate
↓
write temporary file
↓
move previous file to temporary backup (if present)
↓
rename temporary file into final path
↓
remove backup
```

If the in-process commit fails, EBE attempts to restore the previous file and removes the temporary staging file.

This is a transactional application-level rollback guarantee. It is not a promise of power-loss durability across every filesystem, because EBE does not perform a portable directory `fsync` on all supported Lua environments.

## Frozen authority boundary

Persistence hardening does not change engine ownership:

```text
PixelGen = objective semantic world authority
EBE      = observation / memory / belief / knowledge / information / reaction / action requests
```

PixelGen's EBE handoff schema remains `0.8.0`.
