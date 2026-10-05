# EBE Migration — v0.3.0 → v0.4.0

## Existing v0.3 code

No change is required for:

```lua
rt:add_agent(...)
rt:connect_agents(...)
rt:share(...)
rt:advance(...)
rt:ingest_pixelgen(...)
```

## New institutional layer

Add institutions only where useful:

```lua
rt:add_institution({
  id="print_house",
  kind="printing_house",
  sector={2,2},
})

rt:subscribe_institution(
  "print_house",
  "levko"
)
```

Then:

```lua
rt:report_to_institution(
  "mara",
  "print_house",
  "front:front_0:status"
)
```

## Belief metadata change

v0.3:

```text
source_count
≈ distinct reporting agents
```

v0.4:

```text
source_count
= independent evidence roots

reporter_count
= distinct immediate reporters
```

This is the main semantic change.

## Snapshot migration

v0.3 runtime snapshots are accepted.

Missing institutional state is initialized empty.

## Recommended migration

1. Keep direct NPC links working.
2. Add one institutional route.
3. Compare rumor timing and belief behavior.
4. Add more institutions gradually.
5. Use `source_count` for epistemic independence.
6. Use `reporter_count` only for social/reporting diversity.
