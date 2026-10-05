# EBE v0.4.0 — Source Lineage and Echo-Chamber Protection

## Problem

Without lineage:

```text
Mara says X
Iva repeats Mara's X
Levko repeats Iva's X
```

can incorrectly look like:

```text
3 confirmations
```

even though only one observation ever existed.

## v0.4 model

Every direct observation can become a root:

```text
origin_observation_id
```

Transmissions preserve those roots.

Example:

```text
obs_mara_17
↓
Mara
↓
Printing House
↓
Caravan
↓
Levko
```

still has:

```text
origin_observation_ids = [obs_mara_17]
```

If Levko relays it again:

```text
roots remain 1
```

## Independent witness

If Iva independently observes the same real event:

```text
obs_iva_22
```

then the combined belief may contain:

```text
origin_observation_ids
├── obs_mara_17
└── obs_iva_22
```

Now:

```text
source_count = 2
```

and corroborated knowledge can become valid.

## Legacy fallback

v0.3 transmitted observations did not always contain explicit origin IDs.

For those records, EBE falls back to:

```text
legacy-source:<sender_id>
```

so repeated messages from one old-format sender still count as one source.

## Route provenance

Lineage also records semantic hops:

```text
Printing House
→ Caravan
→ Levko
```

This supports future analysis of:

```text
where a rumor came from
which institutions touched it
how many hops it traveled
where distortion may have happened
whether two apparent reports share the same root
```
