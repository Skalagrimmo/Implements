from .rng import SeededRNG

BIOMES = {
    "silt_marsh": {
        "name": "Smoliani Bolota",
        "base_ground": "peat",
        "secondary_ground": "pine",
        "hazard_ground": "water",
        "accent_ground": "ice",
        "enemy_weights": [("striga", 6), ("silt_construct", 2)],
        "loot_weights": [("vellum_bundle", 3), ("bio_gel", 2), ("bone_charm", 2), ("silt_fragment", 1)],
        "landmark_weights": [("nanolith_shrine", 3), ("mask_cross", 2), ("printing_press_altar", 1)],
        "hazard_density": 0.26,
        "prop_density": 0.08,
        "encounter_density": 0.040,
    },
    "dark_forest": {
        "name": "Chervonolis",
        "base_ground": "pine",
        "secondary_ground": "peat",
        "hazard_ground": "water",
        "accent_ground": "moss",
        "enemy_weights": [("striga", 4), ("larva", 3), ("silt_construct", 1)],
        "loot_weights": [("bone_charm", 3), ("printed_anathema", 2), ("silt_fragment", 1)],
        "landmark_weights": [("mask_cross", 3), ("nanolith_shrine", 1)],
        "hazard_density": 0.12,
        "prop_density": 0.10,
        "encounter_density": 0.050,
    },
    "frozen_pass": {
        "name": "Zblidli Perevaly",
        "base_ground": "ice",
        "secondary_ground": "chapel",
        "hazard_ground": "water",
        "accent_ground": "silt",
        "enemy_weights": [("striga", 2), ("zealot", 3), ("silt_construct", 2)],
        "loot_weights": [("printed_anathema", 3), ("bio_gel", 1), ("silt_fragment", 2)],
        "landmark_weights": [("printing_press_altar", 2), ("mask_cross", 2)],
        "hazard_density": 0.10,
        "prop_density": 0.05,
        "encounter_density": 0.045,
    },
    "ruined_settlement": {
        "name": "Pospaleni Slobody",
        "base_ground": "chapel",
        "secondary_ground": "peat",
        "hazard_ground": "water",
        "accent_ground": "silt",
        "enemy_weights": [("zealot", 4), ("silt_construct", 3), ("larva", 1)],
        "loot_weights": [("printed_anathema", 4), ("vellum_bundle", 3), ("bio_gel", 2), ("silt_fragment", 1)],
        "landmark_weights": [("printing_press_altar", 3), ("mask_cross", 2), ("nanolith_shrine", 1)],
        "hazard_density": 0.08,
        "prop_density": 0.12,
        "encounter_density": 0.055,
    },
    "reformed_chapel": {
        "name": "Drukarski Kaplytsi",
        "base_ground": "chapel",
        "secondary_ground": "pine",
        "hazard_ground": "water",
        "accent_ground": "silt",
        "enemy_weights": [("zealot", 6), ("larva", 1)],
        "loot_weights": [("printed_anathema", 5), ("vellum_bundle", 3), ("wax_seal_cache", 2)],
        "landmark_weights": [("printing_press_altar", 5), ("mask_cross", 2)],
        "hazard_density": 0.04,
        "prop_density": 0.07,
        "encounter_density": 0.035,
    },
}


def _validate_weights(items, name):
    if not items:
        raise ValueError(f"{name} cannot be empty")
    total = 0.0
    for value, weight in items:
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name} contains invalid value")
        if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight < 0:
            raise ValueError(f"{name} contains invalid weight for {value!r}")
        total += weight
    if total <= 0:
        raise ValueError(f"{name} total weight must be > 0")


def weighted_choice(rng, items):
    _validate_weights(items, "weighted choices")
    total = sum(weight for _, weight in items)
    roll = rng.random() * total
    acc = 0.0
    for value, weight in items:
        acc += weight
        if roll < acc:
            return value
    return items[-1][0]


def get_biome(kind):
    if kind not in BIOMES:
        raise ValueError(f"Unknown biome: {kind}")
    biome = BIOMES[kind]
    _validate_weights(biome["enemy_weights"], f"{kind}.enemy_weights")
    _validate_weights(biome["loot_weights"], f"{kind}.loot_weights")
    _validate_weights(biome["landmark_weights"], f"{kind}.landmark_weights")
    return biome


def biome_names():
    return list(BIOMES.keys())
