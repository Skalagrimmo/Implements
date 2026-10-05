# EBE v0.7 → v0.8 migration

- All v0.7 public APIs remain available.
- `Runtime.VERSION` and package version become `0.8.0`.
- v0.7 snapshots restore into v0.8.
- Migrated v0.7 snapshots receive an empty semantic-action history.
- Existing reactions remain reactions; v0.8 additionally maps the two built-in reactions to local `agent_intent` requests.
- No built-in reaction is allowed to mutate PixelGen state.
- PixelGen world-event adapters must be explicitly registered.
