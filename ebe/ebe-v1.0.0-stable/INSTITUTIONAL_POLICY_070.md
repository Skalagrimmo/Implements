# EBE v0.7.0 — Institutional Policy / Editorial Control

## 1. Purpose

v0.7 adds an explicit institutional editorial layer on top of the v0.4 information ecology.

An institution may now decide **whether, when, and with what scheduling priority** a retained report is rebroadcast.

The core boundary remains:

```text
evidence truth
!=
institutional publication behavior
```

Censorship does not delete the original report from the institution archive and does not create new evidence roots.

## 2. Flow

```text
incoming report
↓
institution receive threshold
↓
bounded archive
↓
editorial policy
├─ publish
├─ hold (timed delay)
└─ suppress
↓
agenda priority
↓
subscriber route
↓
agent / institution
```

## 3. Policy shape

```lua
rt:add_institution({
  id="press",
  kind="printing_house",
  editorial={
    agenda={
      ["front:"]=0.40,
      ["territory:"]=-0.10,
    },
    rules={
      {
        id="censor_outsider",
        match={
          target_id="outsider",
          key_prefix="front:",
        },
        action="suppress",
      },
      {
        id="hold_archive",
        match={
          target_type="institution",
        },
        action="hold",
        hold_delay=1.0,
      },
    },
  },
})
```

The same policy can be replaced at runtime:

```lua
rt:set_institution_editorial_policy("press", spec)
```

## 4. Supported rule matching

A rule may match:

```text
claim key
claim key prefix
claim value
sender type
sender id
target type
target id
minimum / maximum confidence
minimum / maximum independent root count
```

Rules are evaluated in declared order.

The first matching rule wins.

This keeps policy behavior deterministic and inspectable.

## 5. Actions

### publish

The report is routed normally.

### hold

The report is still published, but receives an additional deterministic delay.

v0.7 `hold` is a **timed editorial hold**, not an indefinite manual moderation queue.

### suppress

The report is not queued to that subscriber.

The institution archive still retains the accepted source report.

Therefore:

```text
suppression
!=
historical erasure
```

## 6. Agenda priority

Agenda entries are claim-key prefixes:

```lua
agenda={
  ["front:"]=0.40,
  ["front:front_0:"]=0.60,
}
```

The longest matching prefix wins.

Priority is clamped to:

```text
-1.0 .. +1.0
```

It affects scheduling only:

```text
priority +1.0 → 0.5 × route delay
priority  0.0 → 1.0 × route delay
priority -1.0 → 1.5 × route delay
```

It never changes evidence roots or objective claim identity.

## 7. Confidence multiplier

A rule may lower publication confidence:

```lua
confidence_multiplier=0.80
```

This models institutional caution or weak endorsement.

The multiplier is constrained to:

```text
0.0 .. 1.0
```

v0.7 does not allow editorial policy to boost a report above its incoming confidence.

## 8. Provenance

Every policy decision can record:

```text
institution_id
report_id
claim_key
target_id
target_type
action
priority
matched_rule_id
agenda_prefix
confidence_multiplier
delay
tag
origin_observation_ids[]
```

Delivered observations retain the corresponding policy record under provenance.

This allows later debugging of:

```text
why did this agent receive this report?
why was another subscriber censored?
why did one report arrive earlier?
```

## 9. Bounded audit log

Each institution has a bounded `policy_log`.

Default:

```text
256 entries
```

The capacity can be overridden:

```lua
editorial={
  policy_log_capacity=64
}
```

## 10. Critical invariants

### No manufactured corroboration

```text
one evidence root
→ many institutions
→ many policy decisions
→ still one evidence root
```

### Membership is still not knowledge

Collective membership remains independent from institutional publication.

### Censorship is audience-specific

The same archived report may be:

```text
published to A
held for B
suppressed for C
```

without changing the underlying evidence.

### Default compatibility

An institution restored from v0.6 without an editorial layer receives:

```text
default_action = publish
priority = 0
delay multiplier = 1
confidence multiplier = 1
```

so old behavior remains pass-through.

## 11. Non-goals

v0.7 deliberately does not yet implement:

```text
semantic action requests back to PixelGen
autonomous political strategy
manual indefinite moderation queues
cryptographic signatures
physical document items
route congestion
agent deception policies
```

Those remain separate later layers.
