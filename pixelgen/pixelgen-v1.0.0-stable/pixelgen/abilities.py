ABILITIES = [
    {
        "id": "freeze_water",
        "name": "Freeze Water",
        "gate_kind": "frozen_crossing",
        "description": "Allows traversal across designated unstable water crossings."
    },
    {
        "id": "wall_run",
        "name": "Wall Run",
        "gate_kind": "wall_run_gap",
        "description": "Allows traversal across designated wall-run passages."
    },
    {
        "id": "high_jump",
        "name": "High Jump",
        "gate_kind": "high_ledge",
        "description": "Allows traversal through designated high ledges."
    },
    {
        "id": "nano_bridge",
        "name": "Nano Bridge",
        "gate_kind": "broken_floor",
        "description": "Allows temporary floor/bridge creation at designated gaps."
    },
]

ABILITY_BY_ID = {a["id"]: a for a in ABILITIES}
ABILITY_ORDER = [a["id"] for a in ABILITIES]

def ability_ids():
    return list(ABILITY_ORDER)

def ability_info(ability_id):
    if ability_id not in ABILITY_BY_ID:
        raise ValueError(f"unknown ability {ability_id!r}")
    return ABILITY_BY_ID[ability_id]

def validate_ability_count(count):
    if isinstance(count, bool) or not isinstance(count, int):
        raise TypeError("ability_count must be an integer")
    if not 0 <= count <= len(ABILITY_ORDER):
        raise ValueError(f"ability_count must be between 0 and {len(ABILITY_ORDER)}")
    return count
