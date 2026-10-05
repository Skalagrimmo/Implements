return {
  institutions = {
    {
      faction = "none",
      id = "auto_caravan_01",
      kind = "caravan_exchange",
      metadata = {
        generated_by = "pixelgen_network_synth",
        main_path_index = 10,
        main_path_length = 19,
        roles = {
          "front_watch",
          "road_corridor",
        },
        source_kind = "main_path",
        sources = {
          {
            id = "main_path",
            kind = "caravan_exchange",
            type = "gameplay_main_path",
          },
          {
            id = "front_4",
            kind = "front_watch",
            type = "front",
          },
        },
      },
      sector = {
        3,
        4,
      },
    },
    {
      faction = "none",
      id = "auto_front_01",
      kind = "front_watch",
      metadata = {
        front_id = "front_0",
        front_site_id = "front_site_0",
        generated_by = "pixelgen_network_synth",
        pair = {
          "nano_signal",
          "print_civic",
        },
        pressure = 0.40500000000000003,
        roles = {
          "front_watch",
        },
        source_kind = "front_site",
        sources = {
          {
            id = "front_0",
            kind = "front_watch",
            type = "front",
          },
        },
      },
      sector = {
        0,
        3,
      },
    },
    {
      faction = "none",
      id = "auto_front_02",
      kind = "front_watch",
      metadata = {
        front_id = "front_1",
        front_site_id = "front_site_1",
        generated_by = "pixelgen_network_synth",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.44440000000000002,
        roles = {
          "front_watch",
        },
        source_kind = "front_site",
        sources = {
          {
            id = "front_1",
            kind = "front_watch",
            type = "front",
          },
        },
      },
      sector = {
        1,
        1,
      },
    },
    {
      faction = "none",
      id = "auto_front_03",
      kind = "front_watch",
      metadata = {
        front_id = "front_2",
        front_site_id = "front_site_2",
        generated_by = "pixelgen_network_synth",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.69440000000000002,
        roles = {
          "front_watch",
        },
        source_kind = "front_site",
        sources = {
          {
            id = "front_2",
            kind = "front_watch",
            type = "front",
          },
        },
      },
      sector = {
        2,
        2,
      },
    },
    {
      faction = "none",
      id = "auto_front_04",
      kind = "front_watch",
      metadata = {
        front_id = "front_3",
        front_site_id = "front_site_3",
        generated_by = "pixelgen_network_synth",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.40500000000000003,
        roles = {
          "front_watch",
        },
        source_kind = "front_site",
        sources = {
          {
            id = "front_3",
            kind = "front_watch",
            type = "front",
          },
        },
      },
      sector = {
        2,
        4,
      },
    },
    {
      faction = "silt_contamination",
      id = "auto_landmark_01",
      kind = "shrine_circle",
      metadata = {
        generated_by = "pixelgen_network_synth",
        label = "Silt Spire",
        landmark_id = "world_01_silt_spire",
        landmark_kind = "silt_spire",
        landmark_scope = "world",
        roles = {
          "landmark_node",
        },
        semantic = "remote_silt",
        source_kind = "landmark",
        sources = {
          {
            id = "world_01_silt_spire",
            kind = "silt_spire",
            type = "landmark",
          },
        },
      },
      policy = {
        distortion = 0.14000000000000001,
        trust = 0.78000000000000003,
      },
      sector = {
        3,
        2,
      },
    },
    {
      faction = "print_civic",
      id = "auto_landmark_02",
      kind = "printing_house",
      metadata = {
        generated_by = "pixelgen_network_synth",
        label = "Press Altar",
        landmark_id = "regional_01_printing_press_altar",
        landmark_kind = "printing_press_altar",
        landmark_scope = "regional",
        roles = {
          "landmark_node",
          "regional_hub",
        },
        semantic = "civic_path",
        source_kind = "landmark",
        sources = {
          {
            id = "regional_01_printing_press_altar",
            kind = "printing_press_altar",
            type = "landmark",
          },
          {
            id = 2,
            kind = "reformed_chapel",
            type = "region",
          },
        },
      },
      policy = {
      },
      sector = {
        0,
        4,
      },
    },
    {
      faction = "nano_signal",
      id = "auto_landmark_03",
      kind = "shrine_circle",
      metadata = {
        generated_by = "pixelgen_network_synth",
        label = "Nanolith Shrine",
        landmark_id = "regional_02_nanolith_shrine",
        landmark_kind = "nanolith_shrine",
        landmark_scope = "regional",
        roles = {
          "landmark_node",
        },
        semantic = "remote_silt",
        source_kind = "landmark",
        sources = {
          {
            id = "regional_02_nanolith_shrine",
            kind = "nanolith_shrine",
            type = "landmark",
          },
        },
      },
      policy = {
      },
      sector = {
        1,
        0,
      },
    },
    {
      faction = "nano_signal",
      id = "auto_landmark_04",
      kind = "shrine_circle",
      metadata = {
        generated_by = "pixelgen_network_synth",
        label = "Nanolith Shrine",
        landmark_id = "regional_03_nanolith_shrine",
        landmark_kind = "nanolith_shrine",
        landmark_scope = "regional",
        roles = {
          "landmark_node",
        },
        semantic = "remote_silt",
        source_kind = "landmark",
        sources = {
          {
            id = "regional_03_nanolith_shrine",
            kind = "nanolith_shrine",
            type = "landmark",
          },
        },
      },
      policy = {
      },
      sector = {
        5,
        0,
      },
    },
    {
      faction = "print_civic",
      id = "auto_landmark_05",
      kind = "printing_house",
      metadata = {
        generated_by = "pixelgen_network_synth",
        label = "Press Altar",
        landmark_id = "regional_04_printing_press_altar",
        landmark_kind = "printing_press_altar",
        landmark_scope = "regional",
        roles = {
          "landmark_node",
          "regional_hub",
        },
        semantic = "civic_path",
        source_kind = "landmark",
        sources = {
          {
            id = "regional_04_printing_press_altar",
            kind = "printing_press_altar",
            type = "landmark",
          },
          {
            id = 1,
            kind = "ruined_settlement",
            type = "region",
          },
        },
      },
      policy = {
      },
      sector = {
        5,
        4,
      },
    },
    {
      faction = "nano_signal",
      id = "auto_landmark_06",
      kind = "shrine_circle",
      metadata = {
        generated_by = "pixelgen_network_synth",
        label = "Nanolith Shrine",
        landmark_id = "regional_05_nanolith_shrine",
        landmark_kind = "nanolith_shrine",
        landmark_scope = "regional",
        roles = {
          "landmark_node",
        },
        semantic = "remote_silt",
        source_kind = "landmark",
        sources = {
          {
            id = "regional_05_nanolith_shrine",
            kind = "nanolith_shrine",
            type = "landmark",
          },
        },
      },
      policy = {
      },
      sector = {
        2,
        3,
      },
    },
    {
      faction = "none",
      id = "auto_landmark_07",
      kind = "roadside_relay",
      metadata = {
        generated_by = "pixelgen_network_synth",
        label = "Mask Cross",
        landmark_id = "local_01_mask_cross",
        landmark_kind = "mask_cross",
        landmark_scope = "local",
        roles = {
          "landmark_node",
        },
        semantic = "roadside",
        source_kind = "landmark",
        sources = {
          {
            id = "local_01_mask_cross",
            kind = "mask_cross",
            type = "landmark",
          },
        },
      },
      policy = {
      },
      sector = {
        0,
        0,
      },
    },
    {
      faction = "none",
      id = "auto_landmark_08",
      kind = "roadside_relay",
      metadata = {
        generated_by = "pixelgen_network_synth",
        label = "Mask Cross",
        landmark_id = "local_02_mask_cross",
        landmark_kind = "mask_cross",
        landmark_scope = "local",
        roles = {
          "landmark_node",
        },
        semantic = "roadside",
        source_kind = "landmark",
        sources = {
          {
            id = "local_02_mask_cross",
            kind = "mask_cross",
            type = "landmark",
          },
        },
      },
      policy = {
      },
      sector = {
        4,
        3,
      },
    },
    {
      faction = "none",
      id = "auto_region_01",
      kind = "shrine_circle",
      metadata = {
        generated_by = "pixelgen_network_synth",
        primary_biome = "dark_forest",
        region_id = 0,
        region_name = "Chervonolis — Rootlands 1",
        roles = {
          "regional_hub",
        },
        sector_count = 16,
        source_kind = "region",
        sources = {
          {
            id = 0,
            kind = "dark_forest",
            type = "region",
          },
        },
      },
      sector = {
        2,
        1,
      },
    },
  },
  policy = {
    allow_gated = true,
    allow_secret = false,
    caravan_hubs = true,
    caravan_spacing = 12,
    front_watches = true,
    main_path_discount = 0.78000000000000003,
    max_degree = 3,
    redundancy = "deterministic local degree completion",
    route_backbone = "minimum spanning forest over weighted sector paths",
    sealed_links = "excluded",
    target_degree = 2,
  },
  routes = {
    {
      a = "auto_caravan_01",
      access_states = {
        gated = 0,
        main_path = 0,
        open = 1,
        secret = 0,
      },
      b = "auto_front_04",
      delay = 0.64000000000000001,
      distortion = 0.055,
      front_crossings = 1,
      id = "auto_route_01",
      main_path_steps = 0,
      path = {
        {
          3,
          4,
        },
        {
          2,
          4,
        },
      },
      path_cost = 1,
      reason = "backbone",
      region_crossings = 1,
      risk = 0.20999999999999999,
      transition_sectors = 2,
      trust = 0.88300000000000001,
    },
    {
      a = "auto_caravan_01",
      access_states = {
        gated = 1,
        main_path = 2,
        open = 1,
        secret = 0,
      },
      b = "auto_landmark_01",
      delay = 0.77000000000000002,
      distortion = 0.052299999999999999,
      front_crossings = 0,
      id = "auto_route_02",
      main_path_steps = 2,
      path = {
        {
          3,
          4,
        },
        {
          3,
          3,
        },
        {
          3,
          2,
        },
      },
      path_cost = 2.028,
      reason = "backbone",
      region_crossings = 1,
      risk = 0.11,
      transition_sectors = 3,
      trust = 0.8901,
    },
    {
      a = "auto_caravan_01",
      access_states = {
        gated = 0,
        main_path = 2,
        open = 2,
        secret = 0,
      },
      b = "auto_landmark_08",
      delay = 0.96999999999999997,
      distortion = 0.096699999999999994,
      front_crossings = 2,
      id = "auto_route_03",
      main_path_steps = 2,
      path = {
        {
          3,
          4,
        },
        {
          4,
          4,
        },
        {
          4,
          3,
        },
      },
      path_cost = 1.5600000000000001,
      reason = "backbone",
      region_crossings = 0,
      risk = 0.32000000000000001,
      transition_sectors = 1,
      trust = 0.80010000000000003,
    },
    {
      a = "auto_front_01",
      access_states = {
        gated = 0,
        main_path = 0,
        open = 5,
        secret = 0,
      },
      b = "auto_front_03",
      delay = 2.3799999999999999,
      distortion = 0.13800000000000001,
      front_crossings = 2,
      id = "auto_route_04",
      main_path_steps = 0,
      path = {
        {
          0,
          3,
        },
        {
          0,
          2,
        },
        {
          1,
          2,
        },
        {
          1,
          3,
        },
        {
          2,
          3,
        },
        {
          2,
          2,
        },
      },
      path_cost = 5,
      reason = "redundancy",
      region_crossings = 3,
      risk = 0.46999999999999997,
      transition_sectors = 4,
      trust = 0.68999999999999995,
    },
    {
      a = "auto_front_01",
      access_states = {
        gated = 0,
        main_path = 0,
        open = 1,
        secret = 0,
      },
      b = "auto_landmark_02",
      delay = 0.34000000000000002,
      distortion = 0.02,
      front_crossings = 0,
      id = "auto_route_05",
      main_path_steps = 0,
      path = {
        {
          0,
          3,
        },
        {
          0,
          4,
        },
      },
      path_cost = 1,
      reason = "backbone",
      region_crossings = 0,
      risk = 0,
      transition_sectors = 0,
      trust = 0.94799999999999995,
    },
    {
      a = "auto_front_01",
      access_states = {
        gated = 0,
        main_path = 0,
        open = 4,
        secret = 0,
      },
      b = "auto_landmark_06",
      delay = 1.8200000000000001,
      distortion = 0.090999999999999998,
      front_crossings = 1,
      id = "auto_route_06",
      main_path_steps = 0,
      path = {
        {
          0,
          3,
        },
        {
          0,
          2,
        },
        {
          1,
          2,
        },
        {
          1,
          3,
        },
        {
          2,
          3,
        },
      },
      path_cost = 4,
      reason = "backbone",
      region_crossings = 3,
      risk = 0.31,
      transition_sectors = 4,
      trust = 0.78700000000000003,
    },
    {
      a = "auto_front_02",
      access_states = {
        gated = 0,
        main_path = 1,
        open = 1,
        secret = 0,
      },
      b = "auto_landmark_03",
      delay = 0.26500000000000001,
      distortion = 0.017399999999999999,
      front_crossings = 0,
      id = "auto_route_07",
      main_path_steps = 1,
      path = {
        {
          1,
          1,
        },
        {
          1,
          0,
        },
      },
      path_cost = 0.78000000000000003,
      reason = "backbone",
      region_crossings = 0,
      risk = 0,
      transition_sectors = 0,
      trust = 0.95499999999999996,
    },
    {
      a = "auto_front_02",
      access_states = {
        gated = 0,
        main_path = 2,
        open = 2,
        secret = 0,
      },
      b = "auto_landmark_07",
      delay = 0.53000000000000003,
      distortion = 0.026700000000000002,
      front_crossings = 0,
      id = "auto_route_08",
      main_path_steps = 2,
      path = {
        {
          1,
          1,
        },
        {
          0,
          1,
        },
        {
          0,
          0,
        },
      },
      path_cost = 1.5600000000000001,
      reason = "backbone",
      region_crossings = 0,
      risk = 0,
      transition_sectors = 1,
      trust = 0.93010000000000004,
    },
    {
      a = "auto_front_03",
      access_states = {
        gated = 0,
        main_path = 0,
        open = 1,
        secret = 0,
      },
      b = "auto_landmark_06",
      delay = 0.56000000000000005,
      distortion = 0.055,
      front_crossings = 1,
      id = "auto_route_09",
      main_path_steps = 0,
      path = {
        {
          2,
          2,
        },
        {
          2,
          3,
        },
      },
      path_cost = 1,
      reason = "backbone",
      region_crossings = 0,
      risk = 0.16,
      transition_sectors = 1,
      trust = 0.88300000000000001,
    },
    {
      a = "auto_front_04",
      access_states = {
        gated = 0,
        main_path = 0,
        open = 2,
        secret = 0,
      },
      b = "auto_landmark_02",
      delay = 0.90000000000000002,
      distortion = 0.067000000000000004,
      front_crossings = 1,
      id = "auto_route_10",
      main_path_steps = 0,
      path = {
        {
          2,
          4,
        },
        {
          1,
          4,
        },
        {
          0,
          4,
        },
      },
      path_cost = 2,
      reason = "backbone",
      region_crossings = 0,
      risk = 0.16,
      transition_sectors = 1,
      trust = 0.85099999999999998,
    },
    {
      a = "auto_landmark_01",
      access_states = {
        gated = 0,
        main_path = 2,
        open = 2,
        secret = 0,
      },
      b = "auto_region_01",
      delay = 0.53000000000000003,
      distortion = 0.026700000000000002,
      front_crossings = 0,
      id = "auto_route_11",
      main_path_steps = 2,
      path = {
        {
          3,
          2,
        },
        {
          3,
          1,
        },
        {
          2,
          1,
        },
      },
      path_cost = 1.5600000000000001,
      reason = "backbone",
      region_crossings = 0,
      risk = 0,
      transition_sectors = 1,
      trust = 0.93010000000000004,
    },
    {
      a = "auto_landmark_03",
      access_states = {
        gated = 0,
        main_path = 3,
        open = 3,
        secret = 0,
      },
      b = "auto_landmark_07",
      delay = 0.79600000000000004,
      distortion = 0.0361,
      front_crossings = 0,
      id = "auto_route_12",
      main_path_steps = 3,
      path = {
        {
          1,
          0,
        },
        {
          1,
          1,
        },
        {
          0,
          1,
        },
        {
          0,
          0,
        },
      },
      path_cost = 2.3399999999999999,
      reason = "redundancy",
      region_crossings = 0,
      risk = 0,
      transition_sectors = 1,
      trust = 0.90510000000000002,
    },
    {
      a = "auto_landmark_03",
      access_states = {
        gated = 1,
        main_path = 2,
        open = 1,
        secret = 0,
      },
      b = "auto_region_01",
      delay = 0.91000000000000003,
      distortion = 0.087300000000000003,
      front_crossings = 1,
      id = "auto_route_13",
      main_path_steps = 2,
      path = {
        {
          1,
          0,
        },
        {
          2,
          0,
        },
        {
          2,
          1,
        },
      },
      path_cost = 2.028,
      reason = "backbone",
      region_crossings = 0,
      risk = 0.22,
      transition_sectors = 0,
      trust = 0.82509999999999994,
    },
    {
      a = "auto_landmark_04",
      access_states = {
        gated = 1,
        main_path = 3,
        open = 3,
        secret = 0,
      },
      b = "auto_landmark_05",
      delay = 1.8149999999999999,
      distortion = 0.14369999999999999,
      front_crossings = 2,
      id = "auto_route_14",
      main_path_steps = 3,
      path = {
        {
          5,
          0,
        },
        {
          5,
          1,
        },
        {
          5,
          2,
        },
        {
          5,
          3,
        },
        {
          5,
          4,
        },
      },
      path_cost = 3.8079999999999998,
      reason = "backbone",
      region_crossings = 1,
      risk = 0.42999999999999999,
      transition_sectors = 2,
      trust = 0.70309999999999995,
    },
    {
      a = "auto_landmark_04",
      access_states = {
        gated = 2,
        main_path = 4,
        open = 2,
        secret = 0,
      },
      b = "auto_landmark_08",
      delay = 2.1190000000000002,
      distortion = 0.20169999999999999,
      front_crossings = 3,
      id = "auto_route_15",
      main_path_steps = 4,
      path = {
        {
          5,
          0,
        },
        {
          5,
          1,
        },
        {
          5,
          2,
        },
        {
          5,
          3,
        },
        {
          4,
          3,
        },
      },
      path_cost = 4.056,
      reason = "redundancy",
      region_crossings = 1,
      risk = 0.65000000000000002,
      transition_sectors = 2,
      trust = 0.60519999999999996,
    },
    {
      a = "auto_landmark_05",
      access_states = {
        gated = 1,
        main_path = 1,
        open = 1,
        secret = 0,
      },
      b = "auto_landmark_08",
      delay = 0.98399999999999999,
      distortion = 0.089999999999999997,
      front_crossings = 1,
      id = "auto_route_16",
      main_path_steps = 1,
      path = {
        {
          5,
          4,
        },
        {
          5,
          3,
        },
        {
          4,
          3,
        },
      },
      path_cost = 2.2480000000000002,
      reason = "backbone",
      region_crossings = 0,
      risk = 0.22,
      transition_sectors = 0,
      trust = 0.81810000000000005,
    },
  },
  sector_access = {
    ["0,0"] = {
      cost = 0,
      delay = 0.14999999999999999,
      institution_id = "auto_landmark_07",
      path = {
        {
          0,
          0,
        },
      },
      trust = 0.96999999999999997,
    },
    ["0,1"] = {
      cost = 0.78000000000000003,
      delay = 0.32200000000000001,
      institution_id = "auto_front_02",
      path = {
        {
          0,
          1,
        },
        {
          1,
          1,
        },
      },
      trust = 0.93489999999999995,
    },
    ["0,2"] = {
      cost = 1,
      delay = 0.37,
      institution_id = "auto_front_01",
      path = {
        {
          0,
          2,
        },
        {
          0,
          3,
        },
      },
      trust = 0.92500000000000004,
    },
    ["0,3"] = {
      cost = 0,
      delay = 0.14999999999999999,
      institution_id = "auto_front_01",
      path = {
        {
          0,
          3,
        },
      },
      trust = 0.96999999999999997,
    },
    ["0,4"] = {
      cost = 0,
      delay = 0.14999999999999999,
      institution_id = "auto_landmark_02",
      path = {
        {
          0,
          4,
        },
      },
      trust = 0.96999999999999997,
    },
    ["1,0"] = {
      cost = 0,
      delay = 0.14999999999999999,
      institution_id = "auto_landmark_03",
      path = {
        {
          1,
          0,
        },
      },
      trust = 0.96999999999999997,
    },
    ["1,1"] = {
      cost = 0,
      delay = 0.14999999999999999,
      institution_id = "auto_front_02",
      path = {
        {
          1,
          1,
        },
      },
      trust = 0.96999999999999997,
    },
    ["1,2"] = {
      cost = 2,
      delay = 0.58999999999999997,
      institution_id = "auto_front_01",
      path = {
        {
          1,
          2,
        },
        {
          0,
          2,
        },
        {
          0,
          3,
        },
      },
      trust = 0.88,
    },
    ["1,3"] = {
      cost = 1,
      delay = 0.37,
      institution_id = "auto_landmark_06",
      path = {
        {
          1,
          3,
        },
        {
          2,
          3,
        },
      },
      trust = 0.92500000000000004,
    },
    ["1,4"] = {
      cost = 1,
      delay = 0.37,
      institution_id = "auto_front_04",
      path = {
        {
          1,
          4,
        },
        {
          2,
          4,
        },
      },
      trust = 0.92500000000000004,
    },
    ["2,0"] = {
      cost = 0.78000000000000003,
      delay = 0.32200000000000001,
      institution_id = "auto_landmark_03",
      path = {
        {
          2,
          0,
        },
        {
          1,
          0,
        },
      },
      trust = 0.93489999999999995,
    },
    ["2,1"] = {
      cost = 0,
      delay = 0.14999999999999999,
      institution_id = "auto_region_01",
      path = {
        {
          2,
          1,
        },
      },
      trust = 0.96999999999999997,
    },
    ["2,2"] = {
      cost = 0,
      delay = 0.14999999999999999,
      institution_id = "auto_front_03",
      path = {
        {
          2,
          2,
        },
      },
      trust = 0.96999999999999997,
    },
    ["2,3"] = {
      cost = 0,
      delay = 0.14999999999999999,
      institution_id = "auto_landmark_06",
      path = {
        {
          2,
          3,
        },
      },
      trust = 0.96999999999999997,
    },
    ["2,4"] = {
      cost = 0,
      delay = 0.14999999999999999,
      institution_id = "auto_front_04",
      path = {
        {
          2,
          4,
        },
      },
      trust = 0.96999999999999997,
    },
    ["3,0"] = {
      cost = 1.78,
      delay = 0.54200000000000004,
      institution_id = "auto_landmark_04",
      path = {
        {
          3,
          0,
        },
        {
          4,
          0,
        },
        {
          5,
          0,
        },
      },
      trust = 0.88990000000000002,
    },
    ["3,1"] = {
      cost = 0.78000000000000003,
      delay = 0.32200000000000001,
      institution_id = "auto_landmark_01",
      path = {
        {
          3,
          1,
        },
        {
          3,
          2,
        },
      },
      trust = 0.93489999999999995,
    },
    ["3,2"] = {
      cost = 0,
      delay = 0.14999999999999999,
      institution_id = "auto_landmark_01",
      path = {
        {
          3,
          2,
        },
      },
      trust = 0.96999999999999997,
    },
    ["3,3"] = {
      cost = 0.78000000000000003,
      delay = 0.32200000000000001,
      institution_id = "auto_caravan_01",
      path = {
        {
          3,
          3,
        },
        {
          3,
          4,
        },
      },
      trust = 0.93489999999999995,
    },
    ["3,4"] = {
      cost = 0,
      delay = 0.14999999999999999,
      institution_id = "auto_caravan_01",
      path = {
        {
          3,
          4,
        },
      },
      trust = 0.96999999999999997,
    },
    ["4,0"] = {
      cost = 0.78000000000000003,
      delay = 0.32200000000000001,
      institution_id = "auto_landmark_04",
      path = {
        {
          4,
          0,
        },
        {
          5,
          0,
        },
      },
      trust = 0.93489999999999995,
    },
    ["4,1"] = {
      cost = 1.5600000000000001,
      delay = 0.49299999999999999,
      institution_id = "auto_landmark_04",
      path = {
        {
          4,
          1,
        },
        {
          4,
          0,
        },
        {
          5,
          0,
        },
      },
      trust = 0.89980000000000004,
    },
    ["4,2"] = {
      cost = 2.3399999999999999,
      delay = 0.66500000000000004,
      institution_id = "auto_landmark_04",
      path = {
        {
          4,
          2,
        },
        {
          4,
          1,
        },
        {
          4,
          0,
        },
        {
          5,
          0,
        },
      },
      trust = 0.86470000000000002,
    },
    ["4,3"] = {
      cost = 0,
      delay = 0.14999999999999999,
      institution_id = "auto_landmark_08",
      path = {
        {
          4,
          3,
        },
      },
      trust = 0.96999999999999997,
    },
    ["4,4"] = {
      cost = 0.78000000000000003,
      delay = 0.32200000000000001,
      institution_id = "auto_caravan_01",
      path = {
        {
          4,
          4,
        },
        {
          3,
          4,
        },
      },
      trust = 0.93489999999999995,
    },
    ["5,0"] = {
      cost = 0,
      delay = 0.14999999999999999,
      institution_id = "auto_landmark_04",
      path = {
        {
          5,
          0,
        },
      },
      trust = 0.96999999999999997,
    },
    ["5,1"] = {
      cost = 1.248,
      delay = 0.42499999999999999,
      institution_id = "auto_landmark_04",
      path = {
        {
          5,
          1,
        },
        {
          5,
          0,
        },
      },
      trust = 0.91379999999999995,
    },
    ["5,2"] = {
      cost = 1.78,
      delay = 0.54200000000000004,
      institution_id = "auto_landmark_05",
      path = {
        {
          5,
          2,
        },
        {
          5,
          3,
        },
        {
          5,
          4,
        },
      },
      trust = 0.88990000000000002,
    },
    ["5,3"] = {
      cost = 1,
      delay = 0.37,
      institution_id = "auto_landmark_05",
      path = {
        {
          5,
          3,
        },
        {
          5,
          4,
        },
      },
      trust = 0.92500000000000004,
    },
    ["5,4"] = {
      cost = 0,
      delay = 0.14999999999999999,
      institution_id = "auto_landmark_05",
      path = {
        {
          5,
          4,
        },
      },
      trust = 0.96999999999999997,
    },
  },
  source = {
    dimensions = {
      6,
      5,
    },
    generator = {
      name = "PixelGen",
      version = "0.8.0",
    },
    world_seed = 7301,
  },
  summary = {
    accessible_sector_count = 30,
    candidate_count = 91,
    component_count = 1,
    institution_count = 14,
    kind_counts = {
      caravan_exchange = 1,
      front_watch = 4,
      printing_house = 2,
      roadside_relay = 2,
      shrine_circle = 5,
    },
    role_counts = {
      front_watch = 5,
      landmark_node = 8,
      regional_hub = 3,
      road_corridor = 1,
    },
    route_count = 16,
    route_front_crossings = 15,
  },
  version = "0.5.0",
  warnings = {
  },
}
