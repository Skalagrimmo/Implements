return {
  cols = 6,
  gameplay = {
    main_path = {
      {
        0,
        0,
      },
      {
        0,
        1,
      },
      {
        1,
        1,
      },
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
      {
        3,
        1,
      },
      {
        3,
        2,
      },
      {
        3,
        3,
      },
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
      {
        5,
        3,
      },
      {
        5,
        2,
      },
      {
        5,
        1,
      },
      {
        5,
        0,
      },
      {
        4,
        0,
      },
      {
        4,
        1,
      },
      {
        4,
        2,
      },
    },
  },
  generator = {
    name = "PixelGen",
    version = "0.8.0",
  },
  geography = {
    regions = {
      {
        adjacent_regions = {
          1,
          2,
        },
        bounds = {
          max_x = 5,
          max_y = 3,
          min_x = 0,
          min_y = 0,
        },
        center = {
          2,
          1,
        },
        id = 0,
        max_center_distance = 4,
        name = "Chervonolis — Rootlands 1",
        primary_biome = "dark_forest",
        sector_count = 16,
      },
      {
        adjacent_regions = {
          0,
          2,
        },
        bounds = {
          max_x = 5,
          max_y = 4,
          min_x = 3,
          min_y = 2,
        },
        center = {
          5,
          4,
        },
        id = 1,
        max_center_distance = 3,
        name = "Pospaleni Slobody — Ashlands 2",
        primary_biome = "ruined_settlement",
        sector_count = 8,
      },
      {
        adjacent_regions = {
          0,
          1,
        },
        bounds = {
          max_x = 2,
          max_y = 4,
          min_x = 0,
          min_y = 2,
        },
        center = {
          0,
          4,
        },
        id = 2,
        max_center_distance = 2,
        name = "Drukarski Kaplytsi — Cloister Belt 3",
        primary_biome = "reformed_chapel",
        sector_count = 6,
      },
    },
    version = "0.7.0",
  },
  influence_topology = {
    boundary_edges = {
      {
        a = {
          2,
          0,
        },
        b = {
          3,
          0,
        },
        edge = "E",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.4444,
      },
      {
        a = {
          2,
          0,
        },
        b = {
          2,
          1,
        },
        edge = "S",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.4444,
      },
      {
        a = {
          3,
          0,
        },
        b = {
          4,
          0,
        },
        edge = "E",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.4444,
      },
      {
        a = {
          4,
          0,
        },
        b = {
          4,
          1,
        },
        edge = "S",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.4444,
      },
      {
        a = {
          1,
          1,
        },
        b = {
          2,
          1,
        },
        edge = "E",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.4444,
      },
      {
        a = {
          1,
          1,
        },
        b = {
          1,
          2,
        },
        edge = "S",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.4444,
      },
      {
        a = {
          4,
          1,
        },
        b = {
          5,
          1,
        },
        edge = "E",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.405,
      },
      {
        a = {
          5,
          1,
        },
        b = {
          5,
          2,
        },
        edge = "S",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.405,
      },
      {
        a = {
          1,
          2,
        },
        b = {
          1,
          3,
        },
        edge = "S",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.4444,
      },
      {
        a = {
          2,
          2,
        },
        b = {
          2,
          3,
        },
        edge = "S",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.6944,
      },
      {
        a = {
          5,
          2,
        },
        b = {
          5,
          3,
        },
        edge = "S",
        pair = {
          "print_civic",
          "silt_contamination",
        },
        pressure = 0.405,
      },
      {
        a = {
          0,
          3,
        },
        b = {
          1,
          3,
        },
        edge = "E",
        pair = {
          "nano_signal",
          "print_civic",
        },
        pressure = 0.405,
      },
      {
        a = {
          1,
          3,
        },
        b = {
          1,
          4,
        },
        edge = "S",
        pair = {
          "nano_signal",
          "print_civic",
        },
        pressure = 0.405,
      },
      {
        a = {
          2,
          3,
        },
        b = {
          3,
          3,
        },
        edge = "E",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.6944,
      },
      {
        a = {
          4,
          3,
        },
        b = {
          5,
          3,
        },
        edge = "E",
        pair = {
          "print_civic",
          "silt_contamination",
        },
        pressure = 0.405,
      },
      {
        a = {
          4,
          3,
        },
        b = {
          4,
          4,
        },
        edge = "S",
        pair = {
          "print_civic",
          "silt_contamination",
        },
        pressure = 0.405,
      },
      {
        a = {
          1,
          4,
        },
        b = {
          2,
          4,
        },
        edge = "E",
        pair = {
          "nano_signal",
          "print_civic",
        },
        pressure = 0.405,
      },
      {
        a = {
          2,
          4,
        },
        b = {
          3,
          4,
        },
        edge = "E",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.405,
      },
      {
        a = {
          3,
          4,
        },
        b = {
          4,
          4,
        },
        edge = "E",
        pair = {
          "print_civic",
          "silt_contamination",
        },
        pressure = 0.405,
      },
    },
    version = "0.7.4",
  },
  landmark_system = {
    placements = {
      {
        id = "world_01_silt_spire",
        kind = "silt_spire",
        map_label = "Silt Spire",
        preferred_zone = "SE",
        scope = "world",
        sector = {
          3,
          2,
        },
        semantic = "remote_silt",
      },
      {
        id = "regional_01_printing_press_altar",
        kind = "printing_press_altar",
        map_label = "Press Altar",
        preferred_zone = "SW",
        scope = "regional",
        sector = {
          0,
          4,
        },
        semantic = "civic_path",
      },
      {
        id = "regional_02_nanolith_shrine",
        kind = "nanolith_shrine",
        map_label = "Nanolith Shrine",
        preferred_zone = "NE",
        scope = "regional",
        sector = {
          1,
          0,
        },
        semantic = "remote_silt",
      },
      {
        id = "regional_03_nanolith_shrine",
        kind = "nanolith_shrine",
        map_label = "Nanolith Shrine",
        preferred_zone = "C",
        scope = "regional",
        sector = {
          5,
          0,
        },
        semantic = "remote_silt",
      },
      {
        id = "regional_04_printing_press_altar",
        kind = "printing_press_altar",
        map_label = "Press Altar",
        preferred_zone = "NW",
        scope = "regional",
        sector = {
          5,
          4,
        },
        semantic = "civic_path",
      },
      {
        id = "regional_05_nanolith_shrine",
        kind = "nanolith_shrine",
        map_label = "Nanolith Shrine",
        preferred_zone = "SE",
        scope = "regional",
        sector = {
          2,
          3,
        },
        semantic = "remote_silt",
      },
      {
        id = "local_01_mask_cross",
        kind = "mask_cross",
        map_label = "Mask Cross",
        preferred_zone = "C",
        scope = "local",
        sector = {
          0,
          0,
        },
        semantic = "roadside",
      },
      {
        id = "local_02_mask_cross",
        kind = "mask_cross",
        map_label = "Mask Cross",
        preferred_zone = "NW",
        scope = "local",
        sector = {
          4,
          3,
        },
        semantic = "roadside",
      },
    },
    policy = {
      composition = "preferred zones vary to suppress repeated corner placement",
      ["local"] = "optional / scene-scale orientation",
      regional = "sparse / multi-sector orientation",
      spacing = "regional anchors prefer >=2 sector Manhattan separation",
      world = "unique large-scale cognitive anchor",
    },
    version = "0.6.2",
  },
  rows = 5,
  sectors = {
    {
      links = {
        E = {
          coord = 6,
          gameplay = {
            gate_id = nil,
            gate_kind = "sealed_passage",
            requires = nil,
            state = "sealed",
          },
          to = {
            1,
            0,
          },
        },
        S = {
          coord = 9,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            0,
            1,
          },
        },
      },
      region_id = 0,
      sx = 0,
      sy = 0,
      transition = false,
    },
    {
      links = {
        E = {
          coord = 6,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            2,
            0,
          },
        },
        S = {
          coord = 8,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            1,
            1,
          },
        },
        W = {
          coord = 6,
          gameplay = {
            gate_id = nil,
            gate_kind = "sealed_passage",
            requires = nil,
            state = "sealed",
          },
          to = {
            0,
            0,
          },
        },
      },
      region_id = 0,
      sx = 1,
      sy = 0,
      transition = false,
    },
    {
      links = {
        E = {
          coord = 6,
          gameplay = {
            gate_id = "shortcut_01_nano_bridge",
            gate_kind = "broken_floor",
            requires = "nano_bridge",
            state = "secret",
          },
          to = {
            3,
            0,
          },
        },
        S = {
          coord = 7,
          gameplay = {
            gate_id = "gate_01_freeze_water",
            gate_kind = "frozen_crossing",
            requires = "freeze_water",
            state = "gated",
          },
          to = {
            2,
            1,
          },
        },
        W = {
          coord = 6,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            1,
            0,
          },
        },
      },
      region_id = 0,
      sx = 2,
      sy = 0,
      transition = false,
    },
    {
      links = {
        E = {
          coord = 6,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            4,
            0,
          },
        },
        S = {
          coord = 6,
          gameplay = {
            gate_id = "shortcut_02_nano_bridge",
            gate_kind = "broken_floor",
            requires = "nano_bridge",
            state = "secret",
          },
          to = {
            3,
            1,
          },
        },
        W = {
          coord = 6,
          gameplay = {
            gate_id = "shortcut_01_nano_bridge",
            gate_kind = "broken_floor",
            requires = "nano_bridge",
            state = "secret",
          },
          to = {
            2,
            0,
          },
        },
      },
      region_id = 0,
      sx = 3,
      sy = 0,
      transition = false,
    },
    {
      links = {
        E = {
          coord = 6,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            5,
            0,
          },
        },
        S = {
          coord = 5,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            4,
            1,
          },
        },
        W = {
          coord = 6,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            3,
            0,
          },
        },
      },
      region_id = 0,
      sx = 4,
      sy = 0,
      transition = false,
    },
    {
      links = {
        S = {
          coord = 4,
          gameplay = {
            gate_id = "gate_04_nano_bridge",
            gate_kind = "broken_floor",
            requires = "nano_bridge",
            state = "gated",
          },
          to = {
            5,
            1,
          },
        },
        W = {
          coord = 6,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            4,
            0,
          },
        },
      },
      region_id = 0,
      sx = 5,
      sy = 0,
      transition = false,
    },
    {
      links = {
        E = {
          coord = 12,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            1,
            1,
          },
        },
        N = {
          coord = 9,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            0,
            0,
          },
        },
        S = {
          coord = 14,
          gameplay = {
            gate_id = "shortcut_03_wall_run",
            gate_kind = "wall_run_gap",
            requires = "wall_run",
            state = "secret",
          },
          to = {
            0,
            2,
          },
        },
      },
      region_id = 0,
      sx = 0,
      sy = 1,
      transition = true,
    },
    {
      links = {
        E = {
          coord = 12,
          gameplay = {
            gate_id = "shortcut_04_freeze_water",
            gate_kind = "frozen_crossing",
            requires = "freeze_water",
            state = "secret",
          },
          to = {
            2,
            1,
          },
        },
        N = {
          coord = 8,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            1,
            0,
          },
        },
        S = {
          coord = 13,
          gameplay = {
            gate_id = "shortcut_05_wall_run",
            gate_kind = "wall_run_gap",
            requires = "wall_run",
            state = "secret",
          },
          to = {
            1,
            2,
          },
        },
        W = {
          coord = 12,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            0,
            1,
          },
        },
      },
      region_id = 0,
      sx = 1,
      sy = 1,
      transition = false,
    },
    {
      links = {
        E = {
          coord = 12,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            3,
            1,
          },
        },
        N = {
          coord = 7,
          gameplay = {
            gate_id = "gate_01_freeze_water",
            gate_kind = "frozen_crossing",
            requires = "freeze_water",
            state = "gated",
          },
          to = {
            2,
            0,
          },
        },
        S = {
          coord = 12,
          gameplay = {
            gate_id = "shortcut_06_wall_run",
            gate_kind = "wall_run_gap",
            requires = "wall_run",
            state = "secret",
          },
          to = {
            2,
            2,
          },
        },
        W = {
          coord = 12,
          gameplay = {
            gate_id = "shortcut_04_freeze_water",
            gate_kind = "frozen_crossing",
            requires = "freeze_water",
            state = "secret",
          },
          to = {
            1,
            1,
          },
        },
      },
      region_id = 0,
      sx = 2,
      sy = 1,
      transition = false,
    },
    {
      links = {
        E = {
          coord = 12,
          gameplay = {
            gate_id = "shortcut_07_nano_bridge",
            gate_kind = "broken_floor",
            requires = "nano_bridge",
            state = "secret",
          },
          to = {
            4,
            1,
          },
        },
        N = {
          coord = 6,
          gameplay = {
            gate_id = "shortcut_02_nano_bridge",
            gate_kind = "broken_floor",
            requires = "nano_bridge",
            state = "secret",
          },
          to = {
            3,
            0,
          },
        },
        S = {
          coord = 11,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            3,
            2,
          },
        },
        W = {
          coord = 12,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            2,
            1,
          },
        },
      },
      region_id = 0,
      sx = 3,
      sy = 1,
      transition = false,
    },
    {
      links = {
        E = {
          coord = 12,
          gameplay = {
            gate_id = "shortcut_08_nano_bridge",
            gate_kind = "broken_floor",
            requires = "nano_bridge",
            state = "secret",
          },
          to = {
            5,
            1,
          },
        },
        N = {
          coord = 5,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            4,
            0,
          },
        },
        S = {
          coord = 10,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            4,
            2,
          },
        },
        W = {
          coord = 12,
          gameplay = {
            gate_id = "shortcut_07_nano_bridge",
            gate_kind = "broken_floor",
            requires = "nano_bridge",
            state = "secret",
          },
          to = {
            3,
            1,
          },
        },
      },
      region_id = 0,
      sx = 4,
      sy = 1,
      transition = true,
    },
    {
      links = {
        N = {
          coord = 4,
          gameplay = {
            gate_id = "gate_04_nano_bridge",
            gate_kind = "broken_floor",
            requires = "nano_bridge",
            state = "gated",
          },
          to = {
            5,
            0,
          },
        },
        S = {
          coord = 9,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            5,
            2,
          },
        },
        W = {
          coord = 12,
          gameplay = {
            gate_id = "shortcut_08_nano_bridge",
            gate_kind = "broken_floor",
            requires = "nano_bridge",
            state = "secret",
          },
          to = {
            4,
            1,
          },
        },
      },
      region_id = 0,
      sx = 5,
      sy = 1,
      transition = true,
    },
    {
      links = {
        E = {
          coord = 11,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            1,
            2,
          },
        },
        N = {
          coord = 14,
          gameplay = {
            gate_id = "shortcut_03_wall_run",
            gate_kind = "wall_run_gap",
            requires = "wall_run",
            state = "secret",
          },
          to = {
            0,
            1,
          },
        },
        S = {
          coord = 7,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            0,
            3,
          },
        },
      },
      region_id = 2,
      sx = 0,
      sy = 2,
      transition = true,
    },
    {
      links = {
        E = {
          coord = 11,
          gameplay = {
            gate_id = nil,
            gate_kind = "sealed_passage",
            requires = nil,
            state = "sealed",
          },
          to = {
            2,
            2,
          },
        },
        N = {
          coord = 13,
          gameplay = {
            gate_id = "shortcut_05_wall_run",
            gate_kind = "wall_run_gap",
            requires = "wall_run",
            state = "secret",
          },
          to = {
            1,
            1,
          },
        },
        S = {
          coord = 6,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            1,
            3,
          },
        },
        W = {
          coord = 11,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            0,
            2,
          },
        },
      },
      region_id = 0,
      sx = 1,
      sy = 2,
      transition = true,
    },
    {
      links = {
        E = {
          coord = 11,
          gameplay = {
            gate_id = "shortcut_09_wall_run",
            gate_kind = "wall_run_gap",
            requires = "wall_run",
            state = "secret",
          },
          to = {
            3,
            2,
          },
        },
        N = {
          coord = 12,
          gameplay = {
            gate_id = "shortcut_06_wall_run",
            gate_kind = "wall_run_gap",
            requires = "wall_run",
            state = "secret",
          },
          to = {
            2,
            1,
          },
        },
        S = {
          coord = 5,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            2,
            3,
          },
        },
        W = {
          coord = 11,
          gameplay = {
            gate_id = nil,
            gate_kind = "sealed_passage",
            requires = nil,
            state = "sealed",
          },
          to = {
            1,
            2,
          },
        },
      },
      region_id = 0,
      sx = 2,
      sy = 2,
      transition = false,
    },
    {
      links = {
        E = {
          coord = 11,
          gameplay = {
            gate_id = "shortcut_10_nano_bridge",
            gate_kind = "broken_floor",
            requires = "nano_bridge",
            state = "secret",
          },
          to = {
            4,
            2,
          },
        },
        N = {
          coord = 11,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            3,
            1,
          },
        },
        S = {
          coord = 4,
          gameplay = {
            gate_id = "gate_02_wall_run",
            gate_kind = "wall_run_gap",
            requires = "wall_run",
            state = "gated",
          },
          to = {
            3,
            3,
          },
        },
        W = {
          coord = 11,
          gameplay = {
            gate_id = "shortcut_09_wall_run",
            gate_kind = "wall_run_gap",
            requires = "wall_run",
            state = "secret",
          },
          to = {
            2,
            2,
          },
        },
      },
      region_id = 0,
      sx = 3,
      sy = 2,
      transition = true,
    },
    {
      links = {
        E = {
          coord = 11,
          gameplay = {
            gate_id = "shortcut_11_nano_bridge",
            gate_kind = "broken_floor",
            requires = "nano_bridge",
            state = "secret",
          },
          to = {
            5,
            2,
          },
        },
        N = {
          coord = 10,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            4,
            1,
          },
        },
        S = {
          coord = 15,
          gameplay = {
            gate_id = "shortcut_12_nano_bridge",
            gate_kind = "broken_floor",
            requires = "nano_bridge",
            state = "secret",
          },
          to = {
            4,
            3,
          },
        },
        W = {
          coord = 11,
          gameplay = {
            gate_id = "shortcut_10_nano_bridge",
            gate_kind = "broken_floor",
            requires = "nano_bridge",
            state = "secret",
          },
          to = {
            3,
            2,
          },
        },
      },
      region_id = 1,
      sx = 4,
      sy = 2,
      transition = true,
    },
    {
      links = {
        N = {
          coord = 9,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            5,
            1,
          },
        },
        S = {
          coord = 14,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            5,
            3,
          },
        },
        W = {
          coord = 11,
          gameplay = {
            gate_id = "shortcut_11_nano_bridge",
            gate_kind = "broken_floor",
            requires = "nano_bridge",
            state = "secret",
          },
          to = {
            4,
            2,
          },
        },
      },
      region_id = 1,
      sx = 5,
      sy = 2,
      transition = true,
    },
    {
      links = {
        E = {
          coord = 10,
          gameplay = {
            gate_id = nil,
            gate_kind = "sealed_passage",
            requires = nil,
            state = "sealed",
          },
          to = {
            1,
            3,
          },
        },
        N = {
          coord = 7,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            0,
            2,
          },
        },
        S = {
          coord = 12,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            0,
            4,
          },
        },
      },
      region_id = 2,
      sx = 0,
      sy = 3,
      transition = false,
    },
    {
      links = {
        E = {
          coord = 10,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            2,
            3,
          },
        },
        N = {
          coord = 6,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            1,
            2,
          },
        },
        S = {
          coord = 11,
          gameplay = {
            gate_id = nil,
            gate_kind = "sealed_passage",
            requires = nil,
            state = "sealed",
          },
          to = {
            1,
            4,
          },
        },
        W = {
          coord = 10,
          gameplay = {
            gate_id = nil,
            gate_kind = "sealed_passage",
            requires = nil,
            state = "sealed",
          },
          to = {
            0,
            3,
          },
        },
      },
      region_id = 2,
      sx = 1,
      sy = 3,
      transition = true,
    },
    {
      links = {
        E = {
          coord = 10,
          gameplay = {
            gate_id = nil,
            gate_kind = "sealed_passage",
            requires = nil,
            state = "sealed",
          },
          to = {
            3,
            3,
          },
        },
        N = {
          coord = 5,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            2,
            2,
          },
        },
        S = {
          coord = 10,
          gameplay = {
            gate_id = nil,
            gate_kind = "sealed_passage",
            requires = nil,
            state = "sealed",
          },
          to = {
            2,
            4,
          },
        },
        W = {
          coord = 10,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            1,
            3,
          },
        },
      },
      region_id = 0,
      sx = 2,
      sy = 3,
      transition = true,
    },
    {
      links = {
        E = {
          coord = 10,
          gameplay = {
            gate_id = nil,
            gate_kind = "sealed_passage",
            requires = nil,
            state = "sealed",
          },
          to = {
            4,
            3,
          },
        },
        N = {
          coord = 4,
          gameplay = {
            gate_id = "gate_02_wall_run",
            gate_kind = "wall_run_gap",
            requires = "wall_run",
            state = "gated",
          },
          to = {
            3,
            2,
          },
        },
        S = {
          coord = 9,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            3,
            4,
          },
        },
        W = {
          coord = 10,
          gameplay = {
            gate_id = nil,
            gate_kind = "sealed_passage",
            requires = nil,
            state = "sealed",
          },
          to = {
            2,
            3,
          },
        },
      },
      region_id = 1,
      sx = 3,
      sy = 3,
      transition = true,
    },
    {
      links = {
        E = {
          coord = 10,
          gameplay = {
            gate_id = "gate_03_high_jump",
            gate_kind = "high_ledge",
            requires = "high_jump",
            state = "gated",
          },
          to = {
            5,
            3,
          },
        },
        N = {
          coord = 15,
          gameplay = {
            gate_id = "shortcut_12_nano_bridge",
            gate_kind = "broken_floor",
            requires = "nano_bridge",
            state = "secret",
          },
          to = {
            4,
            2,
          },
        },
        S = {
          coord = 8,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            4,
            4,
          },
        },
        W = {
          coord = 10,
          gameplay = {
            gate_id = nil,
            gate_kind = "sealed_passage",
            requires = nil,
            state = "sealed",
          },
          to = {
            3,
            3,
          },
        },
      },
      region_id = 1,
      sx = 4,
      sy = 3,
      transition = false,
    },
    {
      links = {
        N = {
          coord = 14,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            5,
            2,
          },
        },
        S = {
          coord = 7,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            5,
            4,
          },
        },
        W = {
          coord = 10,
          gameplay = {
            gate_id = "gate_03_high_jump",
            gate_kind = "high_ledge",
            requires = "high_jump",
            state = "gated",
          },
          to = {
            4,
            3,
          },
        },
      },
      region_id = 1,
      sx = 5,
      sy = 3,
      transition = false,
    },
    {
      links = {
        E = {
          coord = 9,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            1,
            4,
          },
        },
        N = {
          coord = 12,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            0,
            3,
          },
        },
      },
      region_id = 2,
      sx = 0,
      sy = 4,
      transition = false,
    },
    {
      links = {
        E = {
          coord = 9,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            2,
            4,
          },
        },
        N = {
          coord = 11,
          gameplay = {
            gate_id = nil,
            gate_kind = "sealed_passage",
            requires = nil,
            state = "sealed",
          },
          to = {
            1,
            3,
          },
        },
        W = {
          coord = 9,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            0,
            4,
          },
        },
      },
      region_id = 2,
      sx = 1,
      sy = 4,
      transition = false,
    },
    {
      links = {
        E = {
          coord = 9,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            3,
            4,
          },
        },
        N = {
          coord = 10,
          gameplay = {
            gate_id = nil,
            gate_kind = "sealed_passage",
            requires = nil,
            state = "sealed",
          },
          to = {
            2,
            3,
          },
        },
        W = {
          coord = 9,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            1,
            4,
          },
        },
      },
      region_id = 2,
      sx = 2,
      sy = 4,
      transition = true,
    },
    {
      links = {
        E = {
          coord = 9,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            4,
            4,
          },
        },
        N = {
          coord = 9,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            3,
            3,
          },
        },
        W = {
          coord = 9,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            2,
            4,
          },
        },
      },
      region_id = 1,
      sx = 3,
      sy = 4,
      transition = true,
    },
    {
      links = {
        E = {
          coord = 9,
          gameplay = {
            gate_id = "shortcut_13_high_jump",
            gate_kind = "high_ledge",
            requires = "high_jump",
            state = "secret",
          },
          to = {
            5,
            4,
          },
        },
        N = {
          coord = 8,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            4,
            3,
          },
        },
        W = {
          coord = 9,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            3,
            4,
          },
        },
      },
      region_id = 1,
      sx = 4,
      sy = 4,
      transition = false,
    },
    {
      links = {
        N = {
          coord = 7,
          gameplay = {
            gate_id = nil,
            gate_kind = nil,
            requires = nil,
            state = "open",
          },
          to = {
            5,
            3,
          },
        },
        W = {
          coord = 9,
          gameplay = {
            gate_id = "shortcut_13_high_jump",
            gate_kind = "high_ledge",
            requires = "high_jump",
            state = "secret",
          },
          to = {
            4,
            4,
          },
        },
      },
      region_id = 1,
      sx = 5,
      sy = 4,
      transition = false,
    },
  },
  seed = 7301,
  territory_graph = {
    front_sites = {
      {
        front_edge_count = 3,
        front_id = "front_0",
        id = "front_site_0",
        neighbor_sector = {
          1,
          3,
        },
        pair = {
          "nano_signal",
          "print_civic",
        },
        pressure = 0.405,
        sector = {
          0,
          3,
        },
      },
      {
        front_edge_count = 9,
        front_id = "front_1",
        id = "front_site_1",
        neighbor_sector = {
          1,
          2,
        },
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.4444,
        sector = {
          1,
          1,
        },
      },
      {
        front_edge_count = 2,
        front_id = "front_2",
        id = "front_site_2",
        neighbor_sector = {
          2,
          3,
        },
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.6944,
        sector = {
          2,
          2,
        },
      },
      {
        front_edge_count = 1,
        front_id = "front_3",
        id = "front_site_3",
        neighbor_sector = {
          3,
          4,
        },
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        pressure = 0.405,
        sector = {
          2,
          4,
        },
      },
      {
        front_edge_count = 4,
        front_id = "front_4",
        id = "front_site_4",
        neighbor_sector = {
          4,
          4,
        },
        pair = {
          "print_civic",
          "silt_contamination",
        },
        pressure = 0.405,
        sector = {
          3,
          4,
        },
      },
    },
    version = "0.7.5",
  },
}
