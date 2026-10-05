# FPE v0.7 scheduling contract

`FPEScheduler07.create(projection, {budget:8}).step(tick, viewState)` returns update descriptors. The scheduler holds a detached projection copy; create a new instance when loading a new authoritative projection. No writeback and no PixelGen clock advancement occur.

Ticks are nonnegative safe integers supplied by the host. Repeated ticks return no work; backwards ticks throw. Identical input sequences produce identical descriptors. Browser demo uses 50 ms view ticks; reproducibility is defined by input tick/view sequences, not wall-clock frame timing.

| update_rate | geometry period | bud proxy period | cluster proxy period |
| --- | --- | --- | --- |
| below 0.33 | 4 | 8 | 16 |
| 0.33 to below 0.66 | 2 | 4 | 8 |
| 0.66 and above | 1 | 2 | 4 |

Entries start due at zero. Detail changes mark work due at the next distinct tick. Due entries are sorted by deadline then code-unit ID order, not locale. Each served entry gets next deadline `tick + period`. Overdue entries retain their deadline; a large time jump coalesces missed work rather than replaying it. `elapsed` reports time since last service, or zero on first service.

Budget limits cluster update descriptors, NOT milliseconds, draw calls or nodes. Discovery scans all clusters and sorts due entries; this is not yet a spatial index or a large-world streaming scheduler. The demo consumes descriptors to pulse existing materials; it does not rebuild geometry every tick. Geometry remains regenerated on explicit view changes.

Versioning: package/scheduler 0.7.0; bridge and geometry contracts remain 0.6.0, including canonical fingerprints. EBE and PixelGen are unchanged.

Next: harden projection input validation and revision handoff before semantic action round-trip. Interactive WebGL performance and appearance require a real-browser check; syntax and core tests alone do not certify those.
