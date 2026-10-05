# PixelGen machine-readable schemas

These files define the structural minimum for public PixelGen artifacts.

```text
world-0.7.schema.json
world-state-0.8.0.schema.json
runtime-events-0.8.0.schema.json
ebe-runtime-0.8.0.schema.json
regional-corridors-0.9.0.schema.json
contract-manifest-0.9.3.schema.json
contract-manifest-1.0.0.schema.json
public-contract-0.9.3.json
public-contract-1.0.0.json
```

The JSON Schema documents are intentionally permissive toward unknown additive
fields (`additionalProperties: true`).  Semantic invariants and cross-file
relationships are enforced by `pixelgen.schema_contracts` and
`pixelgen.contract_bundle`.

This separation is deliberate: JSON Schema validates structure; PixelGen
validates world semantics and artifact relationships.
