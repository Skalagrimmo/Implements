from .world import generate_world
from .progression import apply_gameplay_grammar
from .gameplay_integrity import validate_gameplay_integrity

def generate_gameplay_world(profile, seed=0, cols=4, rows=3, ability_count=4):
    world = generate_world(profile, seed=seed, cols=cols, rows=rows)
    apply_gameplay_grammar(world, seed=seed, ability_count=ability_count)
    errors = validate_gameplay_integrity(world)
    if errors:
        raise RuntimeError("generated gameplay world failed validation: " + "; ".join(errors[:12]))
    return world
