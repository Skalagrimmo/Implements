# FPE C 0.1.0 — contract and parity notes

## Authority boundary

- PixelGen owns objective world state.
- FPE owns viewer-local hierarchy and manifestation geometry.
- Expansion/collapse is local view state.
- Scheduler ticks are supplied by the host; the C runtime never advances PixelGen clocks.
- `fpe_runtime_request()` returns a semantic intent bound to the accepted source identity/revision/tick. It has no execution or writeback path.

## Projection structure

The C input represents `fpe.pixelgen_hierarchy/0.6.0` and `fpe.view_hierarchy/0.6.0` with typed fields. Validation checks:

- canonical schema and read-only hierarchical mode;
- 64-character lowercase hex fingerprint fields;
- safe integer seed/source clocks;
- positive dimensions and exact `columns × rows` sector coverage;
- valid finite layout ranges;
- unique, in-bounds sector coordinates and canonical `sector_X_Y` IDs;
- all six normalized cluster projection metrics and five state values;
- valid front/territory references;
- exactly four canonical buds per cluster with indices 0–3, fixed offsets and stable seed keys;
- summary counts against the actual input arrays.

Sector uniqueness uses a dense occupancy bitmap, so projection validation is linear in the number of clusters and buds rather than pairwise over the cluster list.

## Hierarchy and geometry

The normalized view stores sorted unique expanded cluster and bud IDs. Unknown IDs are dropped during normalization, as in FPE 0.6. Expanded buds whose parent cluster is closed are dropped. Collapsing a cluster removes all four descendant bud expansions. Explicitly toggling a bud under a collapsed parent returns `PARENT_COLLAPSED` at the runtime API boundary.

Sector centers use the stable FPE layout rule:

```text
x = (sector_x - (columns - 1) / 2) × sector_spacing
z = (sector_y - (rows - 1) / 2) × sector_spacing
y = 3
```

Bud centers use the signed local offset and deterministic height `3 + rand01(seed_key + ":height") × 1.8`.

Straight buds form a cube with 8 vertices and 12 axis-aligned edges. Curved buds use 14 Fibonacci-sphere points. Each point proposes its three nearest neighbours; undirected edges are emitted once in deterministic traversal order with the stable 0.35–0.60 edge weight.

Per-node random value, phase and glyph index use the existing FPE FNV-1a 32-bit key derivation. C 0.1 defines parity for ASCII seed keys only.

## Scheduler

Default budget is host-selected (the JavaScript default is 8); C rejects a zero budget. Entries are sorted by cluster ID. Due work sorts by `next_tick`, then ID. A repeated tick is a no-op. Changing detail marks that cluster due no later than the current host tick.

| Update rate | Base period |
|---|---:|
| `>= 0.66` | 1 |
| `>= 0.33` | 2 |
| otherwise | 4 |

Detail multiplier:

| Detail | Multiplier |
|---|---:|
| cluster proxy | 4 |
| bud proxy | 2 |
| geometry | 1 |

Only the first `budget` overdue entries are serviced per host tick. Deferred work retains its due tick, so it is considered first on a later tick.

## Revision handoff

An incoming projection must retain seed, PixelGen world fingerprint and dimensions. Revision or source tick rollback is stale. An identical projection at the same revision is a no-op; changed content at the same revision is a conflict. A higher revision is cloned, the view is normalized against it, the hierarchy plan is preflighted and a fresh scheduler is prepared before state replacement.

## Native checkpoint

C 0.1 checkpoints own a deep copy of projection, normalized view, scheduler entries/budget and runtime clock. Restore validates the projection, view and scheduler ordering before constructing a new runtime. The object is process-local memory, not a serialized representation of `fpe.runtime_snapshot/0.11.0`.

## Stable FPE 1.0 deltas still required

- Parse and validate the complete JSON projection envelope.
- Match Python canonical JSON numeric formatting and recompute SHA-256 fingerprints.
- Match JSON action-request payload boundaries and exact schema serialization.
- Serialize/restore the stable 0.11 snapshot schema and explicitly migrate 0.11.0 / 0.12.0 / 1.0.0 runtime versions.
- Add JS↔C frozen trace and cross-runtime projection parity fixtures.
- Verify non-ASCII identifier/key behavior, or explicitly constrain the shared contract to canonical ASCII keys.
