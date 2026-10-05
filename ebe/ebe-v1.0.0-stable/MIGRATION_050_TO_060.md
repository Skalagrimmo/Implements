# EBE Migration — v0.5.0 → v0.6.0

v0.6 is additive.

Existing v0.5 APIs remain available:

```lua
local EBE=require("ebe")
local rt=EBE.Runtime.new({seed=5050})

rt:synthesize_pixelgen_network(world)
rt:report_to_local_network("mara",claim_key)
```

New runtime state:

```text
collectives
collective_log
```

A v0.5 snapshot restores into v0.6 with both empty.

## New APIs

```lua
rt:add_collective(spec)

rt:add_collective_member(collective_id,agent_id,metadata)
rt:remove_collective_member(collective_id,agent_id)

rt:subscribe_collective(collective_id,target_id,opts)

rt:submit_to_collective(sender_id,collective_id,claim_key,opts)

rt:get_collective_consensus(collective_id,claim_key)

rt:collective_view(collective_id)

rt:publish_collective(collective_id,claim_key,target_ids,opts)
```

## New module

```lua
EBE.Collective
```

## Important semantic change

There is no automatic faction-wide knowledge.

The following is deliberately false:

```text
same faction
→ same knowledge
```

The correct flow is:

```text
member belief
→ explicit report
→ collective aggregate
→ explicit publication
→ recipient evidence
```

## Source counts

As in v0.4+, `source_count` means independent evidence roots.

`reporter_count` means distinct immediate reporters supporting the selected collective alternative.

Repeated relays of the same observation root do not count as independent corroboration.
