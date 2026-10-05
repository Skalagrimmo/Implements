# v0.8 revision handoff

The package version is 0.8.0. The bridge output/schema remains 0.6.0 and scheduler remains 0.7.0. Canonical fixtures and fingerprints are unchanged. PixelGen and EBE packages are unmodified.

## Acceptance rules

| Incoming data | Result |
| --- | --- |
| First valid projection | Accept detached copy |
| Same world, higher revision, nondecreasing state tick | Accept; normalize and retain expanded IDs |
| Same revision, canonically identical JSON | No-op; keep existing projection reference |
| Same revision, different content | Reject conflict |
| Lower revision or lower state tick | Reject stale data |
| Different world fingerprint, seed or dimensions | Reject; start a new viewer session explicitly |
| Invalid renderer-facing structure | Reject before replacing current data |

Canonical equality ignores object-key order but preserves array order. Fingerprint strings alone are not used to decide equal-revision identity. The handoff function is pure: rejection cannot mutate current projection/view. The viewer preflights the hierarchy plan before committing, preserves selection when its cluster exists, and the existing scheduler resets on the new projection reference only.

## Validation scope

JavaScript validates authority, source clock and identity formats, numeric bounds used by the renderer, sector uniqueness and IDs, bud IDs/indices/offsets/seeds, fronts and summary counts. Python additionally recomputes the existing SHA-256 projection fingerprint and now reports malformed nested structures as validation errors rather than uncaught exceptions.

Browser fingerprint fields are format-checked, NOT cryptographically recomputed or authenticated. Run `python bridge_cli.py validate FILE.json` to check SHA-256 before importing externally supplied files. Neither a checksum nor identity matching proves that an untrusted file was produced by PixelGen. Authenticated transport/signatures are outside this milestone.

Acceptance is not a GPU transaction: WebGL allocation/device failures after preflight are not rolled back. Resource-size quotas and a streaming spatial index remain future work. No real-browser performance or visual QA was performed in this build.

## Manual check

1. Open the v0.8 demo with internet available for the existing Three.js CDN.
2. Expand a cluster and a bud.
3. Load `data/projections/canonical_after.json`: revision should become 3 and expansion should remain.
4. Load it again: no reset.
5. Load `canonical_initial.json`: error, revision 3 stays visible.

Next toward 1.0: freeze/test the public API, then implement explicit semantic action requests through the authority boundary (never direct FPE writeback).
