STRUCTURE_META = {
    "cliff_straight": {"size":[16,48], "footprint":[16,16], "collision":"full", "y_anchor":"bottom-center"},
    "cliff_corner_inner": {"size":[32,48], "footprint":[32,16], "collision":"full", "y_anchor":"bottom-center"},
    "cliff_corner_outer": {"size":[32,48], "footprint":[32,16], "collision":"full", "y_anchor":"bottom-center"},
    "cliff_broken": {"size":[32,48], "footprint":[32,16], "collision":"partial", "y_anchor":"bottom-center"},
    "cliff_silt": {"size":[16,48], "footprint":[16,16], "collision":"full", "y_anchor":"bottom-center"},

    "wall_straight": {"size":[16,48], "footprint":[16,16], "collision":"full", "y_anchor":"bottom-center"},
    "wall_corner_inner": {"size":[32,48], "footprint":[32,16], "collision":"full", "y_anchor":"bottom-center"},
    "wall_corner_outer": {"size":[32,48], "footprint":[32,16], "collision":"full", "y_anchor":"bottom-center"},
    "wall_broken": {"size":[32,48], "footprint":[32,16], "collision":"partial", "y_anchor":"bottom-center"},
    "wall_doorway": {"size":[48,48], "footprint":[48,16], "collision":"portal", "y_anchor":"bottom-center"},

    "nanolith_shrine": {"size":[48,64], "footprint":[48,32], "collision":"full", "y_anchor":"bottom-center"},
    "printing_press_altar": {"size":[64,64], "footprint":[64,32], "collision":"full", "y_anchor":"bottom-center"},
    "mask_cross": {"size":[32,64], "footprint":[32,16], "collision":"full", "y_anchor":"bottom-center"},
    "printing_cathedral": {"size":[96,96], "footprint":[96,32], "collision":"full", "y_anchor":"bottom-center"},
    "silt_spire": {"size":[64,96], "footprint":[48,32], "collision":"full", "y_anchor":"bottom-center"},
}

PROP_META = {
    "brazier_lit":{"size":[16,32],"footprint":[10,8],"collision":"low"},
    "brazier_off":{"size":[16,32],"footprint":[10,8],"collision":"low"},
    "paper_stack":{"size":[16,16],"footprint":[16,16],"collision":"overlay"},
    "chest":{"size":[32,32],"footprint":[24,12],"collision":"full"},
    "nano_capsule_broken":{"size":[32,32],"footprint":[22,12],"collision":"low"},
    "skull_stake_a":{"size":[16,32],"footprint":[6,6],"collision":"low"},
    "skull_stake_b":{"size":[16,32],"footprint":[6,6],"collision":"low"},
    "biogel_barrel":{"size":[16,32],"footprint":[10,10],"collision":"low"},
    "biogel_barrel_leaking":{"size":[32,32],"footprint":[12,10],"collision":"low"},
    "ritual_mask":{"size":[16,16],"footprint":[0,0],"collision":"wall_decor"},
    "warning_board":{"size":[32,32],"footprint":[12,8],"collision":"low"},
    "silt_growth":{"size":[16,16],"footprint":[16,16],"collision":"hazard"},
}

def combined_manifest():
    return {"structures":STRUCTURE_META, "props":PROP_META}
