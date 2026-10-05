# EBE v0.3.0 — Information Locality Contract

## 1. Fundamental separation

EBE treats these as different objects:

```text
EVENT
OBSERVATION
MEMORY
BELIEF
KNOWLEDGE
INTERPRETATION
TRANSMISSION
REACTION
```

No stage may be silently collapsed into another.

## 2. Event

An event says:

```text
something happened
```

It does not say:

```text
every agent knows what happened
```

Events retain causal fields such as:

```text
id
kind
tick
source
actor
cause
sector
provenance
```

## 3. Observation

An observation says:

```text
evidence is available to a particular observer
```

For PixelGen integration, an exported local observation first enters:

```text
runtime.available_observations
```

and is not yet present in anyone's memory.

### Assignment rule

```text
PixelGen observation sector
==
agent current sector
```

is required for direct local assignment.

EBE does not expand PixelGen's observation radius again.

## 4. Memory

Memory is per agent.

```text
observation
↓
encoded confidence
↓
time decay
↓
possible forgetting
```

Default parameters:

```text
capacity         128
decay/hour       0.985
forget threshold 0.08
```

These can be configured per agent.

## 5. Belief

A belief is the agent's current best-supported interpretation of a claim.

Claims are keyed semantically, for example:

```text
front:front_0:status
territory:territory_0:alert
territory:territory_0:control_strength
```

Contradictory values coexist as alternatives.

A belief stores:

```text
chosen value
confidence
agreement
support
evidence count
distinct reporting-agent count
source observations
alternative values
```

### Same-source repetition rule

```text
Mara tells Levko X
Mara tells Levko X again
```

is still:

```text
1 reporting source
```

not two independent confirmations.

## 6. Knowledge

Knowledge is a stronger epistemic category than belief.

Default paths:

### Direct

```text
direct evidence
+
belief confidence >= 0.55
→ knowledge
```

### Corroborated report

```text
at least 2 distinct reporting agents
+
belief confidence >= 0.62
→ knowledge
```

A single rumor may produce a high-confidence belief while still not qualifying as knowledge.

## 7. Interpretation

Interpretation is agent-dependent.

The same believed front state can have different salience due to:

```text
threat_sensitivity
skepticism
```

Therefore:

```text
same evidence
≠
same interpretation
```

## 8. Propagation

Information moves through explicit directed links.

A link has:

```text
sender
receiver
delay
trust
distortion
```

A transmission is queued:

```text
created_at
deliver_at
```

so propagation is not instantaneous.

## 9. Trust

Received confidence depends on:

```text
source belief confidence
×
communication-link trust
×
receiver trust in sender
×
transmission attenuation
```

The current attenuation constant is:

```text
0.92
```

Distortion applies an additional confidence penalty.

## 10. Distortion

Distortion is deterministic for a fixed runtime history.

The same seed and same ordered sequence produce the same rumor mutations.

Current distortion is intentionally conservative:

```text
numeric claim
→ ±10%

front status
→ at most one adjacent status step

territory status
→ at most one adjacent status step
```

## 11. Reaction

Reaction can be driven by belief.

This is intentional:

```text
agents can act on false or uncertain information
```

A reaction records the believed value and confidence that caused it.

## 12. Provenance

Transmitted evidence retains:

```text
transmission_id
source_agent_id
inherited provenance
distortion_applied
```

The path can therefore be inspected later rather than treating all beliefs as anonymous facts.

## 13. Persistence

A runtime snapshot contains only plain Lua data:

```text
agents
memories
beliefs
knowledge
interpretations
propagation queue
reaction state
PixelGen import state
event/reaction/delivery logs
```

The snapshot serializer emits deterministic Lua tables.

## 14. Renderer independence

The cognitive/social runtime contains no dependency on `love.*`.

Renderer integration remains outside EBE core.

## 15. Current scope boundary

v0.3.0 models:

```text
who could observe
who remembers
what they believe
what they know
what they infer
what they tell others
how reports distort
what they do because of those beliefs
```

It does not yet model every possible social institution or autonomous life schedule.
