# EBE v0.8.0 — Semantic Action Requests Test Report

## Release gate

```text
Lua syntax: 85 files PASS
EBE core `love.*` dependencies: 0

historical v0.2.1 smoke: PASS
historical v0.2.1 hardening: PASS
renderer forwarding: PASS
combined v0.3 → v0.8 regression: PASS
```

## v0.8 semantic-action regression

Verified:

```text
belief → reaction → action request
agent_intent default reactions
explicit PixelGen world-event adapter
claim-key target derivation
source-lineage inheritance
pending → exported lifecycle
applied / rejected terminal states
idempotent re-export
idempotent same-status resolution
PixelGen derived-event correlation
snapshot / restore
v0.7 snapshot migration
```

## v0.8 fuzz

```text
EBE v0.8.0 action fuzz: 160 simulations PASS
requests=160 exports=160 rejected=40 applied=120
```

The fuzz alternates front escalation/de-escalation requests, preserves evidence roots, exports deterministic PixelGen event payloads, exercises both authority rejection and applied feedback, and snapshot/restores every simulation.

## v0.8 soak

```text
EBE v0.8.0 action soak: 1200 requests PASS
bounded_action_log=512
```

The action audit log remains bounded while the full request history remains snapshot-persistent.

## Historical subsystem preservation

```text
EBE v0.3.0 fuzz passed: 200 simulations, 400 received rumor memories, 44 distorted transmissions

EBE v0.4.0 ecology fuzz passed: 120 simulations, 240 institutional evidence memories

EBE v0.5.0 network synthesis fuzz passed: 120 variants, avg institutions 11.04, avg routes 9.75, disconnected forests 48, routing log entries 2015

EBE v0.6.0 collective fuzz passed: 120 simulations, 120 echo reports, 120 independent consensuses, 120 publications

EBE v0.6.0 collective soak passed: 300 simulations, 240 consensus, 60 conflicts, 60 institution publications, 6900 submitted reports

EBE v0.7.0 policy fuzz passed: 120 simulations, 40 suppressions, 30 holds, 90 direct publications, 200 root-lineage checks

EBE v0.7.0 policy soak passed: 300 simulations, 1500 decisions, 1200 delivered, 300 suppressed, 300 held
```

## Real PixelGen 1.0 roundtrip

This is not a mocked derived event. The harness generates a real PixelGen 1.0 world/state, lets EBE observe the first authoritative change, turns the resulting belief into a semantic action request, exports a `front_deescalation` runtime event, applies it through PixelGen 1.0, exports the incremental EBE bundle, and re-ingests it into the persisted EBE runtime.

```text
EBE v0.8.0 <-> PixelGen 1.0 real action roundtrip: PASS
request=ebe_action_1 front_deescalation front_0 amount=0.120000
pixelgen_revision=2 derived_event=derived_event_2
```

Causal path:

```text
PixelGen 1.0 revision 0
↓ authoritative front escalation
revision 1
↓ local evidence
EBE belief: front_0 tense
↓ reaction
EBE action request
↓ explicit export
PixelGen front_deescalation
↓ authoritative apply
revision 2
↓ derived_event_2
EBE correlates cause_event_id
↓
action request = applied
```

## Determinism

Five fresh `texlua` processes produced identical canonical demo output:

```text
044f0311280ca1958ae4f854509ae644753a7efb8afd8e59c498e0281c82a204
```

## LÖVE2D

`main.lua` visualizes pending/exported semantic actions beside the PixelGen-derived information network. The validation environment does not provide a `love` executable, so the visual path is syntax/package-structure checked rather than executed here. Core `ebe/` remains renderer-independent.
