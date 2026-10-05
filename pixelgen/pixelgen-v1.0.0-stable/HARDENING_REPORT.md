# PixelGen v0.5 Hardened — Hardening Report

**Release line:** v0.5  
**Patch version:** 0.5.1  
**Scope:** stabilization only; no v0.6 feature expansion.

## Goal

Freeze feature growth at the halfway milestone and make the existing v0.5 pipeline dependable before proceeding toward 1.0.

The hardening pass treated the generator as a hostile system: invalid API input, extreme seeds, one-row/one-column worlds, maximal supported worlds, repeated exports, collisions, route reachability, overlapping objects, incomplete serializers, old v0.4 commands, and mobile-oriented resource limits were all tested.

## Baseline defects found before hardening

A diagnostic fuzz run against the original v0.5 found several real correctness problems:

1. **Sector exits could exist in metadata but be unreachable in gameplay.**
   - 9 unreachable linked exits across 7,200 tested sector-links in the baseline matrix.
   - Cause: `_force_corridor()` opened only the boundary cell and never guaranteed a route from the scene's walkable core/spawn to that exit.

2. **Spawn safety was not guaranteed.**
   - 66 non-walkable spawn cells across 2,700 baseline sectors.
   - Cause: hazard blobs were centered away from spawn, but their radius could still spread onto the spawn cell.

3. **Secret hollows could overwrite already-placed content.**
   - 1,101 hollow/entity cell overlaps in the baseline world sample.
   - Cause: encounters/finds were generated before `insert_hollow()`.

4. **Invalid world sizes were silently accepted.**
   - `cols=0`, negative dimensions, and `rows=0` could return empty worlds instead of an error.
   - An empty `biome_cycle` was also accepted until later indexing behavior became relevant.

5. **v0.5 scene exports were incomplete.**
   - Scene JSON/Lua omitted encounters, finds, and hollows.
   - World Lua exported sector/link metadata but not full scene state.

6. **Legacy v0.4 `scene` generation could overlap objects.**
   - Random props could land on landmark/prop footprints.

7. **Generated object metadata was not consistently applied to scene collision.**
   - A shrine or low obstacle could be visible but not represented in the collision grid.

8. **Atlas regeneration could include its own previous `atlas.png`.**
   - Re-running atlas generation in the same directory could recursively contaminate the input set.

9. **Lua arrays could contain `nil` holes.**
   - Overlay grids serialized with `nil` entries, which makes Lua's `#table` semantics unsafe.

10. **Many public APIs silently coerced invalid parameters.**
    - Floating seeds, impossible masks, invalid probabilities, unknown structural variants, and unsupported profile tile sizes did not have one consistent contract.

## Architectural fixes

### Generation order

World generation now follows this order:

```text
biome terrain
    ↓
protected spawn/core path
    ↓
landmarks + object footprints
    ↓
sector links + guaranteed internal routes
    ↓
secret hollows
    ↓
encounters
    ↓
finds
    ↓
integrity validation
    ↓
export
```

This prevents later systems from overwriting required traversal topology.

### Reachability

A navigation layer now provides:

- flood-fill reachability;
- least-cost routing through walk/hazard cells;
- solid-object avoidance;
- route carving when a boundary exit is disconnected;
- protected route reservation so later props/entities cannot block it.

Every linked exit is checked from the sector spawn before the world is accepted.

### Object footprints

`STRUCTURE_META` and `PROP_META` are now used by placement/collision logic.

- full/low obstacles become `solid` collision;
- Silt hazard props become `hazard`;
- overlays/wall decor remain non-blocking;
- object placement checks map bounds, reserved routes, collision, and existing object footprints.

### Spawn safety

The spawn area is explicitly protected and restored after hazard/overlay generation. A route to the main traversal spine is guaranteed.

### Hollow safety

Hollows now:

- validate probability input;
- search for a valid in-bounds region;
- avoid spawn safety zones;
- avoid protected routes;
- avoid object footprints;
- reserve their cells before encounters/finds are generated.

### Export completeness

Scene JSON, Scene Lua, Tiled-like JSON, World JSON, and World Lua now preserve the complete supported state.

Scene exports include:

- ground;
- overlay;
- collision;
- objects;
- encounters;
- finds;
- hollows;
- landmarks;
- spawn/enemy metadata;
- tile-id grids;
- summary counters.

Tiled-like exports now contain `ground`, `overlay`, `collision`, and `entities` layers.

World Lua is no longer metadata-only; it contains complete sector scene data.

### Lua serialization

The serializer now:

- escapes quotes, backslashes, tabs and newlines;
- sorts dictionary keys for deterministic output;
- removes private generator-only keys;
- converts `None` inside Lua arrays to `0` instead of `nil` to preserve dense grid indexing;
- rejects NaN/Infinity.

### Defensive contract

v0.5 Hardened intentionally defines what is supported instead of pretending every input is valid.

- base tile size: **exactly 16×16**;
- world dimensions: **1..12 sectors per axis**;
- maximum preview world: **144 sectors**;
- probabilities: **0..1**;
- batch counts: **1..10,000**;
- preview scale: **1..64**;
- unknown biomes/materials/props/structure variants: rejected;
- noncanonical 47-mask autotile masks: rejected;
- world render safety cap: **32,000,000 pixels**.

The 12×12 limit is a mobile-oriented preview safety boundary, not a statement about the eventual 1.0 world size.

## Hardening test results

### Regression suite

```text
15 tests passed
```

This includes the existing v0.2, v0.3, v0.4 and v0.5 tests plus the new hardening suite.

### Scene fuzz matrix

```text
11,000 scene cases: PASS
```

Coverage:

- all five biomes;
- 2,000 seeds per biome (`-500..1499`);
- variable hollow probabilities;
- 1,000 legacy v0.4 scene seeds;
- spawn/collision checks;
- object overlap checks;
- encounter/find placement checks.

Observed test runtime in the build environment: ~15.4 s.

### World fuzz matrix

```text
707 generated worlds: PASS
```

Dimension matrix:

```text
1×1
1×6
6×1
2×2
3×3
4×4
5×3
```

Seeds: `-50..50`.

Checks:

- reciprocal sector links;
- matching corridor coordinates;
- every linked exit reachable from spawn;
- no malformed scenes;
- no entity/object overlap;
- no non-walkable encounter placement.

Observed test runtime: ~12.6 s.

### Maximum supported world

```text
12×12 = 144 sectors: PASS
```

Measured in the build environment:

- world generation: ~0.33 s;
- world render: ~6.31 s;
- rendered image: 3851×2891 px with gap=1;
- process peak RSS during an isolated benchmark process: ~142 MB.

These measurements are environment-specific and are not guaranteed Termux performance numbers.

### Deterministic full-world output

A 3×3 world generated twice with the same seed produced identical SHA-256 hashes for:

- PNG preview;
- JSON export;
- Lua export.

### CLI smoke matrix

```text
21 valid public command invocations: PASS
7 intentionally invalid invocations: correctly rejected
```

Valid coverage includes terrain, Silt, decals, both autotile systems, structures, props, manifest, scene, scene-batch, biome-scene, world, preview, atlas and validation.

All demo entry points (`demo`, `material-demo`, `structure-demo`, `scene-demo`, `biome-demo`, `world-demo`) were also executed successfully.

## Remaining known limits

No test suite can prove software mathematically “perfect.” Within the frozen v0.5 contract, no known integrity failures remain in the matrices above.

Known scope limits rather than bugs:

- exact character sprite generation is not part of v0.5;
- world progression/ability gates are intentionally deferred beyond the frozen milestone;
- Tiled export is **Tiled-like**, not a promise of every Tiled schema feature;
- the build environment did not contain a Lua/LuaJIT executable, so Lua files were not executed by an external Lua interpreter; serializer behavior is regression-tested and deterministic;
- renderer performance on a specific Android device depends on device memory/CPU.

## Freeze rule

After this milestone, v0.5 should receive only:

- bug fixes;
- compatibility fixes;
- test additions;
- documentation corrections.

New gameplay/generation capabilities should begin only after explicitly reopening feature development toward the next milestone.
