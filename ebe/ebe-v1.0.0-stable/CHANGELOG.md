# Changelog

## 1.0.0 — Stable Epistemic Runtime

- Promoted the frozen v0.9 architecture without adding a new cognition subsystem.
- Froze stable package/runtime and persistence contracts at 1.0.0.
- Added explicit v0.9 → v1.0 metadata-only migration.
- Added promotion parity tooling and canonical cross-version demo hashes.
- Added invalid UTF-8 rejection to strict JSON encode/decode.
- Added nested action-request/action-gateway schema-version validation.
- Tightened action sequence and bounded audit-log validation.
- Added historically documented Runtime methods to the stable public contract.
- Preserved action-request/JSON/safe-Lua schema versions at 0.9.0 and PixelGen bridge schema at 0.8.0.
- Added 500-case v1.0 hostile/migration fuzz and 5,000-request soak.


## 0.9.0 — Persistence / Hostile Input / Public Contract Freeze

- Added strict deterministic JSON encoder/decoder for persistence.
- Rejected duplicate JSON keys, nulls, non-finite numbers, trailing data and excessive nesting.
- Replaced executable `dofile()` snapshot/world loading with a safe literal-only Lua subset parser.
- Added runtime snapshot contract validation with bounded depth/node/queue/action limits.
- Added action-request lifecycle, source-count and exported-authority correlation checks.
- Prevented forged PixelGen feedback from resolving an unexported or mismatched action request.
- Added transactional temp+rename runtime snapshot writes with rollback on failed commit.
- Added metadata-only migration for EBE runtime snapshots 0.3.0 through 0.8.0.
- Added machine-readable public-contract description/fingerprint and API freeze tests.
- Preserved PixelGen EBE runtime bundle schema `0.8.0`.
- Added hostile-input fuzz, strict-JSON corpus and persistence soak.

## 0.8.0 — Semantic Action Requests

- Added snapshot-safe semantic action-request gateway.
- Added `agent_intent` and strict `pixelgen_world_event` domains.
- Added reaction → action adapters with belief/source-lineage provenance.
- Added explicit `pending → exported → applied/rejected` lifecycle.
- Added PixelGen derived-event correlation by `cause_event_id`.
- Added real PixelGen 1.0 cross-language roundtrip harness.
- Preserved PixelGen as sole authority for world mutation.


## 0.7.0 — Institutional Policy / Editorial Control

- Added explicit per-institution editorial policy.
- Added deterministic `publish`, timed `hold`, and `suppress` actions.
- Added claim-prefix agendas that affect route scheduling priority.
- Added target-specific audience rules.
- Added sender, target, key, value, confidence and root-count rule matching.
- Added bounded per-institution policy audit logs.
- Added policy provenance to delivered observations and forwarded reports.
- Added confidence down-weighting without evidence-root mutation.
- Added runtime policy replacement and policy inspection APIs.
- Added v0.6 snapshot migration to pass-through editorial behavior.
- Preserved source-lineage / echo-protection invariants.
- Added 120-simulation policy fuzz.
- Added 300-simulation / 1,500-decision policy soak.
- Updated LÖVE demo to show a live front-priority agenda node.


## 0.6.0 — Collective Epistemics / Bounded Group Information

- Added explicit collective epistemic nodes for factions, councils, settlements and other bounded groups.
- Added collective membership without automatic shared memory or knowledge.
- Added explicit agent → collective reporting.
- Added bounded collective report archives.
- Added one-root-one-vote aggregation per claim.
- Added source-lineage echo protection at the collective layer.
- Added reporter-count vs independent-root-count distinction.
- Added explicit contradictory alternatives and conflict metrics.
- Added aggregate states: `tentative`, `corroborated`, `consensus`.
- Added explicit collective publication to agents.
- Added collective → institution publication while preserving evidence roots.
- Added optional faction auto-enrollment that changes membership only.
- Added collective snapshot persistence and v0.5 snapshot migration.
- Added `collective_view()`.
- Added actual PixelGen 1.0 stable-contract compatibility fixtures/tests.
- Added fail-closed rejection of unsupported future PixelGen EBE bundle versions.
- Added 120-simulation collective fuzz.
- Added 300-simulation collective soak with 6,900 reports, contradiction cases and institution publication.
- Updated LÖVE demo with a visible `watch_council` aggregate.

## 0.5.0 — PixelGen Information Infrastructure / Auto-Synthesis

- Added automatic institutional-network synthesis from PixelGen v0.8 world topology.
- Added landmark → institution mapping.
- Added regional fallback hubs.
- Added front-site watch nodes.
- Added main-path caravan exchange synthesis.
- Added `roadside_relay` institution preset.
- Added `front_watch` institution preset.
- Added weighted route graph from PixelGen sector links.
- Sealed links are never used.
- Secret links are disabled by default.
- Gated links receive higher cost.
- Gameplay main-path edges receive a route-cost discount.
- Added route front-crossing, region-crossing and transition metadata.
- Added route delay/trust/distortion/risk derivation.
- Added deterministic minimum-spanning-forest backbone.
- Added bounded local route redundancy.
- Added sector → nearest institution access index.
- Added automatic agent attachment to synthesized networks.
- Agent movement now updates institutional access and removes stale subscriptions.
- Agents added after synthesis attach automatically.
- Added `report_to_local_network()`.
- Added route/ingress provenance to delivered observations.
- Added lineage-aware institutional duplicate suppression for dense route graphs.
- Added network plan validation and deterministic fingerprinting.
- Different plans cannot silently replace a live synthesized plan.
- Added compact PixelGen JSON → Lua network-view converter.
- Added network plan Lua/DOT export tool.
- Added Graphviz canonical network visualization.
- Added pure-Lua and LÖVE network demos.
- Added v0.4 snapshot migration to current runtime.
- Added 120-variant network synthesis fuzz.
- Added four fresh PixelGen 12×12 synthesis stress cases.

## 0.4.0 — Information Ecology / Institutional Networks

- Added institutional routing nodes, source lineage, echo protection and institutional archives.

## 0.3.0 — Information Locality / PixelGen Runtime Bridge

- Added per-agent observation, memory, belief, knowledge, delayed rumor propagation and PixelGen v0.8 dynamic handoff.

## 0.2.1 — Legacy hardening / LÖVE renderer hotfix

- Preserved as backward-compatible runtime and test baseline.
