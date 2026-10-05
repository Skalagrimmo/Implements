return {
  agents = {
    iva = {
      beliefs = {
        ["front:front_0:activity"] = {
          agreement = 1,
          alternatives = {
            ["0.533"] = {
              direct_sources = 1,
              score = 0.89012784227099995,
              source_agents = {
                "iva",
              },
              sources = {
                "observation_1_1",
              },
              value = 0.53300000000000003,
            },
          },
          confidence = 0.89012800000000003,
          direct_sources = 1,
          evidence_count = 1,
          key = "front:front_0:activity",
          source_agents = {
            "iva",
          },
          source_count = 1,
          sources = {
            "observation_1_1",
          },
          support = 0.89012800000000003,
          value = 0.53300000000000003,
        },
        ["front:front_0:status"] = {
          agreement = 1,
          alternatives = {
            ["\"tense\""] = {
              direct_sources = 1,
              score = 0.89012784227099995,
              source_agents = {
                "iva",
              },
              sources = {
                "observation_1_1",
              },
              value = "tense",
            },
          },
          confidence = 0.89012800000000003,
          direct_sources = 1,
          evidence_count = 1,
          key = "front:front_0:status",
          source_agents = {
            "iva",
          },
          source_count = 1,
          sources = {
            "observation_1_1",
          },
          support = 0.89012800000000003,
          value = "tense",
        },
        ["front:front_0:tension"] = {
          agreement = 1,
          alternatives = {
            ["0.605"] = {
              direct_sources = 1,
              score = 0.89012784227099995,
              source_agents = {
                "iva",
              },
              sources = {
                "observation_1_1",
              },
              value = 0.60499999999999998,
            },
          },
          confidence = 0.89012800000000003,
          direct_sources = 1,
          evidence_count = 1,
          key = "front:front_0:tension",
          source_agents = {
            "iva",
          },
          source_count = 1,
          sources = {
            "observation_1_1",
          },
          support = 0.89012800000000003,
          value = 0.60499999999999998,
        },
      },
      biases = {
        skepticism = 0.050000000000000003,
      },
      faction = "printers",
      id = "iva",
      interpretations = {
        {
          claim_key = "front:front_0:status",
          confidence = 0.89012800000000003,
          salience = 0.74864200000000003,
          stance = "caution",
          threat = 0.71099999999999997,
          value = "tense",
        },
        {
          claim_key = "front:front_0:activity",
          confidence = 0.89012800000000003,
          salience = 0.40055800000000003,
          stance = "ordinary",
          threat = 0,
          value = 0.53300000000000003,
        },
        {
          claim_key = "front:front_0:tension",
          confidence = 0.89012800000000003,
          salience = 0.40055800000000003,
          stance = "ordinary",
          threat = 0,
          value = 0.60499999999999998,
        },
      },
      knowledge = {
        ["front:front_0:activity"] = {
          basis = "direct_evidence",
          confidence = 0.89012800000000003,
          key = "front:front_0:activity",
          source_count = 1,
          sources = {
            "observation_1_1",
          },
          value = 0.53300000000000003,
        },
        ["front:front_0:status"] = {
          basis = "direct_evidence",
          confidence = 0.89012800000000003,
          key = "front:front_0:status",
          source_count = 1,
          sources = {
            "observation_1_1",
          },
          value = "tense",
        },
        ["front:front_0:tension"] = {
          basis = "direct_evidence",
          confidence = 0.89012800000000003,
          key = "front:front_0:tension",
          source_count = 1,
          sources = {
            "observation_1_1",
          },
          value = 0.60499999999999998,
        },
      },
      memory = {
        capacity = 128,
        decay_per_hour = 0.98499999999999999,
        entries = {
          observation_1_1 = {
            confidence = 0.89012784227099995,
            encoded_at = 0,
            id = "observation_1_1",
            last_updated = 5,
            observation = {
              confidence = 0.95999999999999996,
              delivery_state = "available_to_local_observers",
              evidence = "direct_local",
              fact = {
                changes = {
                  activity = {
                    after = 0.53300000000000003,
                    before = 0.39300000000000002,
                  },
                  status = {
                    after = "tense",
                    before = "active",
                  },
                  tension = {
                    after = 0.60499999999999998,
                    before = 0.40500000000000003,
                  },
                },
                event_type = "front_state_changed",
              },
              id = "observation_1_1",
              knowledge_state = "assigned_as_evidence",
              observed_at = 0,
              observer_id = "iva",
              provenance = {
                integration = "pixelgen_v080",
                state_revision = 1,
              },
              revision = 1,
              sector = {
                0,
                3,
              },
              source_event_id = "derived_event_1",
              subject_id = "front_0",
              subject_type = "front",
            },
          },
        },
        min_confidence = 0.080000000000000002,
        order = {
          "observation_1_1",
        },
      },
      received_observations = {
        observation_1_1 = true,
      },
      sector = {
        0,
        3,
      },
      trust = {
        levko = 0.90000000000000002,
        mara = 0.94999999999999996,
      },
    },
    levko = {
      beliefs = {
        ["front:front_0:status"] = {
          agreement = 1,
          alternatives = {
            ["\"tense\""] = {
              direct_sources = 0,
              score = 1.4583539150165998,
              source_agents = {
                "mara",
                "iva",
              },
              sources = {
                "rumor_tx_1",
                "rumor_tx_2",
              },
              value = "tense",
            },
          },
          confidence = 1,
          direct_sources = 0,
          evidence_count = 2,
          key = "front:front_0:status",
          source_agents = {
            "mara",
            "iva",
          },
          source_count = 2,
          sources = {
            "rumor_tx_1",
            "rumor_tx_2",
          },
          support = 1.4583539999999999,
          value = "tense",
        },
      },
      biases = {
        skepticism = 0.080000000000000002,
      },
      faction = "none",
      id = "levko",
      interpretations = {
        {
          claim_key = "front:front_0:status",
          confidence = 1,
          salience = 0.83808000000000005,
          stance = "caution",
          threat = 0.7056,
          value = "tense",
        },
      },
      knowledge = {
        ["front:front_0:status"] = {
          basis = "corroborated_reports",
          confidence = 1,
          key = "front:front_0:status",
          source_count = 2,
          sources = {
            "rumor_tx_1",
            "rumor_tx_2",
          },
          value = "tense",
        },
      },
      memory = {
        capacity = 128,
        decay_per_hour = 0.98499999999999999,
        entries = {
          rumor_tx_1 = {
            confidence = 0.7617543842279999,
            encoded_at = 2,
            id = "rumor_tx_1",
            last_updated = 5,
            observation = {
              confidence = 0.79708800000000002,
              delivery_state = "delivered",
              evidence = "transmitted",
              fact = {
                claims = {
                  {
                    confidence = 0.95999999999999996,
                    key = "front:front_0:status",
                    value = "tense",
                  },
                },
              },
              id = "rumor_tx_1",
              knowledge_state = "assigned_as_evidence",
              observed_at = 2,
              observer_id = "levko",
              provenance = {
                distortion_applied = false,
                inherited = {
                  belief_sources = {
                    "observation_1_0",
                  },
                  inherited = {
                  },
                },
                source_agent_id = "mara",
                transmission_id = "tx_1",
              },
              sector = {
                5,
                4,
              },
              source_agent_id = "mara",
              source_event_id = "tx_1",
              subject_id = "front:front_0:status",
              subject_type = "rumor",
            },
          },
          rumor_tx_2 = {
            confidence = 0.77335500000000001,
            encoded_at = 5,
            id = "rumor_tx_2",
            last_updated = 5,
            observation = {
              confidence = 0.77335500000000001,
              delivery_state = "delivered",
              evidence = "transmitted",
              fact = {
                claims = {
                  {
                    confidence = 0.93141600000000002,
                    key = "front:front_0:status",
                    value = "tense",
                  },
                },
              },
              id = "rumor_tx_2",
              knowledge_state = "assigned_as_evidence",
              observed_at = 5,
              observer_id = "levko",
              provenance = {
                distortion_applied = false,
                inherited = {
                  belief_sources = {
                    "observation_1_1",
                  },
                  inherited = {
                  },
                },
                source_agent_id = "iva",
                transmission_id = "tx_2",
              },
              sector = {
                5,
                4,
              },
              source_agent_id = "iva",
              source_event_id = "tx_2",
              subject_id = "front:front_0:status",
              subject_type = "rumor",
            },
          },
        },
        min_confidence = 0.080000000000000002,
        order = {
          "rumor_tx_1",
          "rumor_tx_2",
        },
      },
      received_observations = {
        rumor_tx_1 = true,
        rumor_tx_2 = true,
      },
      sector = {
        5,
        4,
      },
      trust = {
        iva = 0.94999999999999996,
        mara = 0.94999999999999996,
      },
    },
    mara = {
      beliefs = {
        ["front:front_0:activity"] = {
          agreement = 1,
          alternatives = {
            ["0.533"] = {
              direct_sources = 1,
              score = 0.89012784227099995,
              source_agents = {
                "mara",
              },
              sources = {
                "observation_1_0",
              },
              value = 0.53300000000000003,
            },
          },
          confidence = 0.89012800000000003,
          direct_sources = 1,
          evidence_count = 1,
          key = "front:front_0:activity",
          source_agents = {
            "mara",
          },
          source_count = 1,
          sources = {
            "observation_1_0",
          },
          support = 0.89012800000000003,
          value = 0.53300000000000003,
        },
        ["front:front_0:status"] = {
          agreement = 1,
          alternatives = {
            ["\"tense\""] = {
              direct_sources = 1,
              score = 0.89012784227099995,
              source_agents = {
                "mara",
              },
              sources = {
                "observation_1_0",
              },
              value = "tense",
            },
          },
          confidence = 0.89012800000000003,
          direct_sources = 1,
          evidence_count = 1,
          key = "front:front_0:status",
          source_agents = {
            "mara",
          },
          source_count = 1,
          sources = {
            "observation_1_0",
          },
          support = 0.89012800000000003,
          value = "tense",
        },
        ["front:front_0:tension"] = {
          agreement = 1,
          alternatives = {
            ["0.605"] = {
              direct_sources = 1,
              score = 0.89012784227099995,
              source_agents = {
                "mara",
              },
              sources = {
                "observation_1_0",
              },
              value = 0.60499999999999998,
            },
          },
          confidence = 0.89012800000000003,
          direct_sources = 1,
          evidence_count = 1,
          key = "front:front_0:tension",
          source_agents = {
            "mara",
          },
          source_count = 1,
          sources = {
            "observation_1_0",
          },
          support = 0.89012800000000003,
          value = 0.60499999999999998,
        },
      },
      biases = {
        threat_sensitivity = 1.1499999999999999,
      },
      faction = "pilgrims",
      id = "mara",
      interpretations = {
        {
          claim_key = "front:front_0:status",
          confidence = 0.89012800000000003,
          salience = 0.80592200000000003,
          stance = "danger",
          threat = 0.82799999999999996,
          value = "tense",
        },
        {
          claim_key = "front:front_0:activity",
          confidence = 0.89012800000000003,
          salience = 0.40055800000000003,
          stance = "ordinary",
          threat = 0,
          value = 0.53300000000000003,
        },
        {
          claim_key = "front:front_0:tension",
          confidence = 0.89012800000000003,
          salience = 0.40055800000000003,
          stance = "ordinary",
          threat = 0,
          value = 0.60499999999999998,
        },
      },
      knowledge = {
        ["front:front_0:activity"] = {
          basis = "direct_evidence",
          confidence = 0.89012800000000003,
          key = "front:front_0:activity",
          source_count = 1,
          sources = {
            "observation_1_0",
          },
          value = 0.53300000000000003,
        },
        ["front:front_0:status"] = {
          basis = "direct_evidence",
          confidence = 0.89012800000000003,
          key = "front:front_0:status",
          source_count = 1,
          sources = {
            "observation_1_0",
          },
          value = "tense",
        },
        ["front:front_0:tension"] = {
          basis = "direct_evidence",
          confidence = 0.89012800000000003,
          key = "front:front_0:tension",
          source_count = 1,
          sources = {
            "observation_1_0",
          },
          value = 0.60499999999999998,
        },
      },
      memory = {
        capacity = 128,
        decay_per_hour = 0.98499999999999999,
        entries = {
          observation_1_0 = {
            confidence = 0.89012784227099995,
            encoded_at = 0,
            id = "observation_1_0",
            last_updated = 5,
            observation = {
              confidence = 0.95999999999999996,
              delivery_state = "available_to_local_observers",
              evidence = "direct_local",
              fact = {
                changes = {
                  activity = {
                    after = 0.53300000000000003,
                    before = 0.39300000000000002,
                  },
                  status = {
                    after = "tense",
                    before = "active",
                  },
                  tension = {
                    after = 0.60499999999999998,
                    before = 0.40500000000000003,
                  },
                },
                event_type = "front_state_changed",
              },
              id = "observation_1_0",
              knowledge_state = "assigned_as_evidence",
              observed_at = 0,
              observer_id = "mara",
              provenance = {
                integration = "pixelgen_v080",
                state_revision = 1,
              },
              revision = 1,
              sector = {
                0,
                2,
              },
              source_event_id = "derived_event_1",
              subject_id = "front_0",
              subject_type = "front",
            },
          },
        },
        min_confidence = 0.080000000000000002,
        order = {
          "observation_1_0",
        },
      },
      received_observations = {
        observation_1_0 = true,
      },
      sector = {
        0,
        2,
      },
      trust = {
        iva = 0.94999999999999996,
        levko = 0.84999999999999998,
      },
    },
  },
  available_observations = {
    observation_1_0 = {
      confidence = 0.95999999999999996,
      delivery_state = "available_to_local_observers",
      evidence = "direct_local",
      fact = {
        changes = {
          activity = {
            after = 0.53300000000000003,
            before = 0.39300000000000002,
          },
          status = {
            after = "tense",
            before = "active",
          },
          tension = {
            after = 0.60499999999999998,
            before = 0.40500000000000003,
          },
        },
        event_type = "front_state_changed",
      },
      id = "observation_1_0",
      knowledge_state = "not_yet_assigned_to_any_agent",
      observed_at = 0,
      provenance = {
        integration = "pixelgen_v080",
        state_revision = 1,
      },
      revision = 1,
      sector = {
        0,
        2,
      },
      source_event_id = "derived_event_1",
      subject_id = "front_0",
      subject_type = "front",
    },
    observation_1_1 = {
      confidence = 0.95999999999999996,
      delivery_state = "available_to_local_observers",
      evidence = "direct_local",
      fact = {
        changes = {
          activity = {
            after = 0.53300000000000003,
            before = 0.39300000000000002,
          },
          status = {
            after = "tense",
            before = "active",
          },
          tension = {
            after = 0.60499999999999998,
            before = 0.40500000000000003,
          },
        },
        event_type = "front_state_changed",
      },
      id = "observation_1_1",
      knowledge_state = "not_yet_assigned_to_any_agent",
      observed_at = 0,
      provenance = {
        integration = "pixelgen_v080",
        state_revision = 1,
      },
      revision = 1,
      sector = {
        0,
        3,
      },
      source_event_id = "derived_event_1",
      subject_id = "front_0",
      subject_type = "front",
    },
    observation_1_2 = {
      confidence = 0.95999999999999996,
      delivery_state = "available_to_local_observers",
      evidence = "direct_local",
      fact = {
        changes = {
          activity = {
            after = 0.53300000000000003,
            before = 0.39300000000000002,
          },
          status = {
            after = "tense",
            before = "active",
          },
          tension = {
            after = 0.60499999999999998,
            before = 0.40500000000000003,
          },
        },
        event_type = "front_state_changed",
      },
      id = "observation_1_2",
      knowledge_state = "not_yet_assigned_to_any_agent",
      observed_at = 0,
      provenance = {
        integration = "pixelgen_v080",
        state_revision = 1,
      },
      revision = 1,
      sector = {
        1,
        3,
      },
      source_event_id = "derived_event_1",
      subject_id = "front_0",
      subject_type = "front",
    },
    observation_1_3 = {
      confidence = 0.95999999999999996,
      delivery_state = "available_to_local_observers",
      evidence = "direct_local",
      fact = {
        changes = {
          activity = {
            after = 0.53300000000000003,
            before = 0.39300000000000002,
          },
          status = {
            after = "tense",
            before = "active",
          },
          tension = {
            after = 0.60499999999999998,
            before = 0.40500000000000003,
          },
        },
        event_type = "front_state_changed",
      },
      id = "observation_1_3",
      knowledge_state = "not_yet_assigned_to_any_agent",
      observed_at = 0,
      provenance = {
        integration = "pixelgen_v080",
        state_revision = 1,
      },
      revision = 1,
      sector = {
        0,
        4,
      },
      source_event_id = "derived_event_1",
      subject_id = "front_0",
      subject_type = "front",
    },
    observation_2_0 = {
      confidence = 0.95999999999999996,
      delivery_state = "available_to_local_observers",
      evidence = "direct_local",
      fact = {
        changes = {
          alert = {
            after = 0.316,
            before = 0.28000000000000003,
          },
          control_strength = {
            after = 0.39750000000000002,
            before = 0.51749999999999996,
          },
          stability = {
            after = 0.63549999999999995,
            before = 0.6835,
          },
        },
        event_type = "territory_state_changed",
      },
      id = "observation_2_0",
      knowledge_state = "not_yet_assigned_to_any_agent",
      observed_at = 0,
      provenance = {
        integration = "pixelgen_v080",
        state_revision = 2,
      },
      revision = 2,
      sector = {
        0,
        0,
      },
      source_event_id = "derived_event_2",
      subject_id = "territory_0",
      subject_type = "territory",
    },
    observation_2_1 = {
      confidence = 0.95999999999999996,
      delivery_state = "available_to_local_observers",
      evidence = "direct_local",
      fact = {
        changes = {
          alert = {
            after = 0.316,
            before = 0.28000000000000003,
          },
          control_strength = {
            after = 0.39750000000000002,
            before = 0.51749999999999996,
          },
          stability = {
            after = 0.63549999999999995,
            before = 0.6835,
          },
        },
        event_type = "territory_state_changed",
      },
      id = "observation_2_1",
      knowledge_state = "not_yet_assigned_to_any_agent",
      observed_at = 0,
      provenance = {
        integration = "pixelgen_v080",
        state_revision = 2,
      },
      revision = 2,
      sector = {
        1,
        0,
      },
      source_event_id = "derived_event_2",
      subject_id = "territory_0",
      subject_type = "territory",
    },
    observation_2_2 = {
      confidence = 0.95999999999999996,
      delivery_state = "available_to_local_observers",
      evidence = "direct_local",
      fact = {
        changes = {
          alert = {
            after = 0.316,
            before = 0.28000000000000003,
          },
          control_strength = {
            after = 0.39750000000000002,
            before = 0.51749999999999996,
          },
          stability = {
            after = 0.63549999999999995,
            before = 0.6835,
          },
        },
        event_type = "territory_state_changed",
      },
      id = "observation_2_2",
      knowledge_state = "not_yet_assigned_to_any_agent",
      observed_at = 0,
      provenance = {
        integration = "pixelgen_v080",
        state_revision = 2,
      },
      revision = 2,
      sector = {
        2,
        0,
      },
      source_event_id = "derived_event_2",
      subject_id = "territory_0",
      subject_type = "territory",
    },
    observation_2_3 = {
      confidence = 0.95999999999999996,
      delivery_state = "available_to_local_observers",
      evidence = "direct_local",
      fact = {
        changes = {
          alert = {
            after = 0.316,
            before = 0.28000000000000003,
          },
          control_strength = {
            after = 0.39750000000000002,
            before = 0.51749999999999996,
          },
          stability = {
            after = 0.63549999999999995,
            before = 0.6835,
          },
        },
        event_type = "territory_state_changed",
      },
      id = "observation_2_3",
      knowledge_state = "not_yet_assigned_to_any_agent",
      observed_at = 0,
      provenance = {
        integration = "pixelgen_v080",
        state_revision = 2,
      },
      revision = 2,
      sector = {
        1,
        1,
      },
      source_event_id = "derived_event_2",
      subject_id = "territory_0",
      subject_type = "territory",
    },
    observation_3_0 = {
      confidence = 0.95999999999999996,
      delivery_state = "available_to_local_observers",
      evidence = "direct_local",
      fact = {
        changes = {
          activity = {
            after = 0.3619,
            before = 0.41139999999999999,
          },
          tension = {
            after = 0.34560000000000002,
            before = 0.43559999999999999,
          },
        },
        event_type = "front_state_changed",
      },
      id = "observation_3_0",
      knowledge_state = "not_yet_assigned_to_any_agent",
      observed_at = 0,
      provenance = {
        integration = "pixelgen_v080",
        state_revision = 3,
      },
      revision = 3,
      sector = {
        1,
        0,
      },
      source_event_id = "derived_event_3",
      subject_id = "front_1",
      subject_type = "front",
    },
    observation_3_1 = {
      confidence = 0.95999999999999996,
      delivery_state = "available_to_local_observers",
      evidence = "direct_local",
      fact = {
        changes = {
          activity = {
            after = 0.3619,
            before = 0.41139999999999999,
          },
          tension = {
            after = 0.34560000000000002,
            before = 0.43559999999999999,
          },
        },
        event_type = "front_state_changed",
      },
      id = "observation_3_1",
      knowledge_state = "not_yet_assigned_to_any_agent",
      observed_at = 0,
      provenance = {
        integration = "pixelgen_v080",
        state_revision = 3,
      },
      revision = 3,
      sector = {
        0,
        1,
      },
      source_event_id = "derived_event_3",
      subject_id = "front_1",
      subject_type = "front",
    },
    observation_3_2 = {
      confidence = 0.95999999999999996,
      delivery_state = "available_to_local_observers",
      evidence = "direct_local",
      fact = {
        changes = {
          activity = {
            after = 0.3619,
            before = 0.41139999999999999,
          },
          tension = {
            after = 0.34560000000000002,
            before = 0.43559999999999999,
          },
        },
        event_type = "front_state_changed",
      },
      id = "observation_3_2",
      knowledge_state = "not_yet_assigned_to_any_agent",
      observed_at = 0,
      provenance = {
        integration = "pixelgen_v080",
        state_revision = 3,
      },
      revision = 3,
      sector = {
        1,
        1,
      },
      source_event_id = "derived_event_3",
      subject_id = "front_1",
      subject_type = "front",
    },
    observation_3_3 = {
      confidence = 0.95999999999999996,
      delivery_state = "available_to_local_observers",
      evidence = "direct_local",
      fact = {
        changes = {
          activity = {
            after = 0.3619,
            before = 0.41139999999999999,
          },
          tension = {
            after = 0.34560000000000002,
            before = 0.43559999999999999,
          },
        },
        event_type = "front_state_changed",
      },
      id = "observation_3_3",
      knowledge_state = "not_yet_assigned_to_any_agent",
      observed_at = 0,
      provenance = {
        integration = "pixelgen_v080",
        state_revision = 3,
      },
      revision = 3,
      sector = {
        2,
        1,
      },
      source_event_id = "derived_event_3",
      subject_id = "front_1",
      subject_type = "front",
    },
    observation_3_4 = {
      confidence = 0.95999999999999996,
      delivery_state = "available_to_local_observers",
      evidence = "direct_local",
      fact = {
        changes = {
          activity = {
            after = 0.3619,
            before = 0.41139999999999999,
          },
          tension = {
            after = 0.34560000000000002,
            before = 0.43559999999999999,
          },
        },
        event_type = "front_state_changed",
      },
      id = "observation_3_4",
      knowledge_state = "not_yet_assigned_to_any_agent",
      observed_at = 0,
      provenance = {
        integration = "pixelgen_v080",
        state_revision = 3,
      },
      revision = 3,
      sector = {
        1,
        2,
      },
      source_event_id = "derived_event_3",
      subject_id = "front_1",
      subject_type = "front",
    },
  },
  bus_history = {
    {
      event = {
        faction = "pilgrims",
        id = "mara",
        sector = {
          0,
          2,
        },
      },
      topic = "agent.added",
    },
    {
      event = {
        faction = "printers",
        id = "iva",
        sector = {
          0,
          3,
        },
      },
      topic = "agent.added",
    },
    {
      event = {
        faction = "none",
        id = "levko",
        sector = {
          5,
          4,
        },
      },
      topic = "agent.added",
    },
    {
      event = {
        cause_event_id = "runtime_event_1",
        changes = {
          activity = {
            after = 0.53300000000000003,
            before = 0.39300000000000002,
          },
          status = {
            after = "tense",
            before = "active",
          },
          tension = {
            after = 0.60499999999999998,
            before = 0.40500000000000003,
          },
        },
        event_type = "front_state_changed",
        id = "derived_event_1",
        observability = "local_or_transmitted",
        revision = 1,
        sector = {
          0,
          3,
        },
        subject_id = "front_0",
        subject_type = "front",
      },
      topic = "pixelgen.event",
    },
    {
      event = {
        cause_event_id = "runtime_event_2",
        changes = {
          alert = {
            after = 0.316,
            before = 0.28000000000000003,
          },
          control_strength = {
            after = 0.39750000000000002,
            before = 0.51749999999999996,
          },
          stability = {
            after = 0.63549999999999995,
            before = 0.6835,
          },
        },
        event_type = "territory_state_changed",
        id = "derived_event_2",
        observability = "local_or_transmitted",
        revision = 2,
        sector = {
          1,
          0,
        },
        subject_id = "territory_0",
        subject_type = "territory",
      },
      topic = "pixelgen.event",
    },
    {
      event = {
        cause_event_id = "runtime_event_3",
        changes = {
          activity = {
            after = 0.3619,
            before = 0.41139999999999999,
          },
          tension = {
            after = 0.34560000000000002,
            before = 0.43559999999999999,
          },
        },
        event_type = "front_state_changed",
        id = "derived_event_3",
        observability = "local_or_transmitted",
        revision = 3,
        sector = {
          1,
          1,
        },
        subject_id = "front_1",
        subject_type = "front",
      },
      topic = "pixelgen.event",
    },
    {
      event = {
        confidence = 0.95999999999999996,
        delivery_state = "available_to_local_observers",
        evidence = "direct_local",
        fact = {
          changes = {
            activity = {
              after = 0.53300000000000003,
              before = 0.39300000000000002,
            },
            status = {
              after = "tense",
              before = "active",
            },
            tension = {
              after = 0.60499999999999998,
              before = 0.40500000000000003,
            },
          },
          event_type = "front_state_changed",
        },
        id = "observation_1_0",
        knowledge_state = "not_yet_assigned_to_any_agent",
        observed_at = 0,
        provenance = {
          integration = "pixelgen_v080",
          state_revision = 1,
        },
        revision = 1,
        sector = {
          0,
          2,
        },
        source_event_id = "derived_event_1",
        subject_id = "front_0",
        subject_type = "front",
      },
      topic = "pixelgen.observation_available",
    },
    {
      event = {
        confidence = 0.95999999999999996,
        delivery_state = "available_to_local_observers",
        evidence = "direct_local",
        fact = {
          changes = {
            activity = {
              after = 0.53300000000000003,
              before = 0.39300000000000002,
            },
            status = {
              after = "tense",
              before = "active",
            },
            tension = {
              after = 0.60499999999999998,
              before = 0.40500000000000003,
            },
          },
          event_type = "front_state_changed",
        },
        id = "observation_1_1",
        knowledge_state = "not_yet_assigned_to_any_agent",
        observed_at = 0,
        provenance = {
          integration = "pixelgen_v080",
          state_revision = 1,
        },
        revision = 1,
        sector = {
          0,
          3,
        },
        source_event_id = "derived_event_1",
        subject_id = "front_0",
        subject_type = "front",
      },
      topic = "pixelgen.observation_available",
    },
    {
      event = {
        confidence = 0.95999999999999996,
        delivery_state = "available_to_local_observers",
        evidence = "direct_local",
        fact = {
          changes = {
            activity = {
              after = 0.53300000000000003,
              before = 0.39300000000000002,
            },
            status = {
              after = "tense",
              before = "active",
            },
            tension = {
              after = 0.60499999999999998,
              before = 0.40500000000000003,
            },
          },
          event_type = "front_state_changed",
        },
        id = "observation_1_2",
        knowledge_state = "not_yet_assigned_to_any_agent",
        observed_at = 0,
        provenance = {
          integration = "pixelgen_v080",
          state_revision = 1,
        },
        revision = 1,
        sector = {
          1,
          3,
        },
        source_event_id = "derived_event_1",
        subject_id = "front_0",
        subject_type = "front",
      },
      topic = "pixelgen.observation_available",
    },
    {
      event = {
        confidence = 0.95999999999999996,
        delivery_state = "available_to_local_observers",
        evidence = "direct_local",
        fact = {
          changes = {
            activity = {
              after = 0.53300000000000003,
              before = 0.39300000000000002,
            },
            status = {
              after = "tense",
              before = "active",
            },
            tension = {
              after = 0.60499999999999998,
              before = 0.40500000000000003,
            },
          },
          event_type = "front_state_changed",
        },
        id = "observation_1_3",
        knowledge_state = "not_yet_assigned_to_any_agent",
        observed_at = 0,
        provenance = {
          integration = "pixelgen_v080",
          state_revision = 1,
        },
        revision = 1,
        sector = {
          0,
          4,
        },
        source_event_id = "derived_event_1",
        subject_id = "front_0",
        subject_type = "front",
      },
      topic = "pixelgen.observation_available",
    },
    {
      event = {
        confidence = 0.95999999999999996,
        delivery_state = "available_to_local_observers",
        evidence = "direct_local",
        fact = {
          changes = {
            alert = {
              after = 0.316,
              before = 0.28000000000000003,
            },
            control_strength = {
              after = 0.39750000000000002,
              before = 0.51749999999999996,
            },
            stability = {
              after = 0.63549999999999995,
              before = 0.6835,
            },
          },
          event_type = "territory_state_changed",
        },
        id = "observation_2_0",
        knowledge_state = "not_yet_assigned_to_any_agent",
        observed_at = 0,
        provenance = {
          integration = "pixelgen_v080",
          state_revision = 2,
        },
        revision = 2,
        sector = {
          0,
          0,
        },
        source_event_id = "derived_event_2",
        subject_id = "territory_0",
        subject_type = "territory",
      },
      topic = "pixelgen.observation_available",
    },
    {
      event = {
        confidence = 0.95999999999999996,
        delivery_state = "available_to_local_observers",
        evidence = "direct_local",
        fact = {
          changes = {
            alert = {
              after = 0.316,
              before = 0.28000000000000003,
            },
            control_strength = {
              after = 0.39750000000000002,
              before = 0.51749999999999996,
            },
            stability = {
              after = 0.63549999999999995,
              before = 0.6835,
            },
          },
          event_type = "territory_state_changed",
        },
        id = "observation_2_1",
        knowledge_state = "not_yet_assigned_to_any_agent",
        observed_at = 0,
        provenance = {
          integration = "pixelgen_v080",
          state_revision = 2,
        },
        revision = 2,
        sector = {
          1,
          0,
        },
        source_event_id = "derived_event_2",
        subject_id = "territory_0",
        subject_type = "territory",
      },
      topic = "pixelgen.observation_available",
    },
    {
      event = {
        confidence = 0.95999999999999996,
        delivery_state = "available_to_local_observers",
        evidence = "direct_local",
        fact = {
          changes = {
            alert = {
              after = 0.316,
              before = 0.28000000000000003,
            },
            control_strength = {
              after = 0.39750000000000002,
              before = 0.51749999999999996,
            },
            stability = {
              after = 0.63549999999999995,
              before = 0.6835,
            },
          },
          event_type = "territory_state_changed",
        },
        id = "observation_2_2",
        knowledge_state = "not_yet_assigned_to_any_agent",
        observed_at = 0,
        provenance = {
          integration = "pixelgen_v080",
          state_revision = 2,
        },
        revision = 2,
        sector = {
          2,
          0,
        },
        source_event_id = "derived_event_2",
        subject_id = "territory_0",
        subject_type = "territory",
      },
      topic = "pixelgen.observation_available",
    },
    {
      event = {
        confidence = 0.95999999999999996,
        delivery_state = "available_to_local_observers",
        evidence = "direct_local",
        fact = {
          changes = {
            alert = {
              after = 0.316,
              before = 0.28000000000000003,
            },
            control_strength = {
              after = 0.39750000000000002,
              before = 0.51749999999999996,
            },
            stability = {
              after = 0.63549999999999995,
              before = 0.6835,
            },
          },
          event_type = "territory_state_changed",
        },
        id = "observation_2_3",
        knowledge_state = "not_yet_assigned_to_any_agent",
        observed_at = 0,
        provenance = {
          integration = "pixelgen_v080",
          state_revision = 2,
        },
        revision = 2,
        sector = {
          1,
          1,
        },
        source_event_id = "derived_event_2",
        subject_id = "territory_0",
        subject_type = "territory",
      },
      topic = "pixelgen.observation_available",
    },
    {
      event = {
        confidence = 0.95999999999999996,
        delivery_state = "available_to_local_observers",
        evidence = "direct_local",
        fact = {
          changes = {
            activity = {
              after = 0.3619,
              before = 0.41139999999999999,
            },
            tension = {
              after = 0.34560000000000002,
              before = 0.43559999999999999,
            },
          },
          event_type = "front_state_changed",
        },
        id = "observation_3_0",
        knowledge_state = "not_yet_assigned_to_any_agent",
        observed_at = 0,
        provenance = {
          integration = "pixelgen_v080",
          state_revision = 3,
        },
        revision = 3,
        sector = {
          1,
          0,
        },
        source_event_id = "derived_event_3",
        subject_id = "front_1",
        subject_type = "front",
      },
      topic = "pixelgen.observation_available",
    },
    {
      event = {
        confidence = 0.95999999999999996,
        delivery_state = "available_to_local_observers",
        evidence = "direct_local",
        fact = {
          changes = {
            activity = {
              after = 0.3619,
              before = 0.41139999999999999,
            },
            tension = {
              after = 0.34560000000000002,
              before = 0.43559999999999999,
            },
          },
          event_type = "front_state_changed",
        },
        id = "observation_3_1",
        knowledge_state = "not_yet_assigned_to_any_agent",
        observed_at = 0,
        provenance = {
          integration = "pixelgen_v080",
          state_revision = 3,
        },
        revision = 3,
        sector = {
          0,
          1,
        },
        source_event_id = "derived_event_3",
        subject_id = "front_1",
        subject_type = "front",
      },
      topic = "pixelgen.observation_available",
    },
    {
      event = {
        confidence = 0.95999999999999996,
        delivery_state = "available_to_local_observers",
        evidence = "direct_local",
        fact = {
          changes = {
            activity = {
              after = 0.3619,
              before = 0.41139999999999999,
            },
            tension = {
              after = 0.34560000000000002,
              before = 0.43559999999999999,
            },
          },
          event_type = "front_state_changed",
        },
        id = "observation_3_2",
        knowledge_state = "not_yet_assigned_to_any_agent",
        observed_at = 0,
        provenance = {
          integration = "pixelgen_v080",
          state_revision = 3,
        },
        revision = 3,
        sector = {
          1,
          1,
        },
        source_event_id = "derived_event_3",
        subject_id = "front_1",
        subject_type = "front",
      },
      topic = "pixelgen.observation_available",
    },
    {
      event = {
        confidence = 0.95999999999999996,
        delivery_state = "available_to_local_observers",
        evidence = "direct_local",
        fact = {
          changes = {
            activity = {
              after = 0.3619,
              before = 0.41139999999999999,
            },
            tension = {
              after = 0.34560000000000002,
              before = 0.43559999999999999,
            },
          },
          event_type = "front_state_changed",
        },
        id = "observation_3_3",
        knowledge_state = "not_yet_assigned_to_any_agent",
        observed_at = 0,
        provenance = {
          integration = "pixelgen_v080",
          state_revision = 3,
        },
        revision = 3,
        sector = {
          2,
          1,
        },
        source_event_id = "derived_event_3",
        subject_id = "front_1",
        subject_type = "front",
      },
      topic = "pixelgen.observation_available",
    },
    {
      event = {
        confidence = 0.95999999999999996,
        delivery_state = "available_to_local_observers",
        evidence = "direct_local",
        fact = {
          changes = {
            activity = {
              after = 0.3619,
              before = 0.41139999999999999,
            },
            tension = {
              after = 0.34560000000000002,
              before = 0.43559999999999999,
            },
          },
          event_type = "front_state_changed",
        },
        id = "observation_3_4",
        knowledge_state = "not_yet_assigned_to_any_agent",
        observed_at = 0,
        provenance = {
          integration = "pixelgen_v080",
          state_revision = 3,
        },
        revision = 3,
        sector = {
          1,
          2,
        },
        source_event_id = "derived_event_3",
        subject_id = "front_1",
        subject_type = "front",
      },
      topic = "pixelgen.observation_available",
    },
    {
      event = {
        agent_id = "mara",
        observation = {
          confidence = 0.95999999999999996,
          delivery_state = "available_to_local_observers",
          evidence = "direct_local",
          fact = {
            changes = {
              activity = {
                after = 0.53300000000000003,
                before = 0.39300000000000002,
              },
              status = {
                after = "tense",
                before = "active",
              },
              tension = {
                after = 0.60499999999999998,
                before = 0.40500000000000003,
              },
            },
            event_type = "front_state_changed",
          },
          id = "observation_1_0",
          knowledge_state = "assigned_as_evidence",
          observed_at = 0,
          observer_id = "mara",
          provenance = {
            integration = "pixelgen_v080",
            state_revision = 1,
          },
          revision = 1,
          sector = {
            0,
            2,
          },
          source_event_id = "derived_event_1",
          subject_id = "front_0",
          subject_type = "front",
        },
      },
      topic = "observation.delivered",
    },
    {
      event = {
        agent_id = "mara",
        believed_value = "tense",
        claim_key = "front:front_0:status",
        confidence = 0.95999999999999996,
        id = "reaction_1",
        kind = "avoid_front",
        rule_id = "avoid_volatile_front",
        tick = 0,
      },
      topic = "reaction.emitted",
    },
    {
      event = {
        agent_id = "mara",
        beliefs = 3,
        interpretations = 3,
        knowledge = 3,
      },
      topic = "cognition.recomputed",
    },
    {
      event = {
        agent_id = "iva",
        observation = {
          confidence = 0.95999999999999996,
          delivery_state = "available_to_local_observers",
          evidence = "direct_local",
          fact = {
            changes = {
              activity = {
                after = 0.53300000000000003,
                before = 0.39300000000000002,
              },
              status = {
                after = "tense",
                before = "active",
              },
              tension = {
                after = 0.60499999999999998,
                before = 0.40500000000000003,
              },
            },
            event_type = "front_state_changed",
          },
          id = "observation_1_1",
          knowledge_state = "assigned_as_evidence",
          observed_at = 0,
          observer_id = "iva",
          provenance = {
            integration = "pixelgen_v080",
            state_revision = 1,
          },
          revision = 1,
          sector = {
            0,
            3,
          },
          source_event_id = "derived_event_1",
          subject_id = "front_0",
          subject_type = "front",
        },
      },
      topic = "observation.delivered",
    },
    {
      event = {
        agent_id = "iva",
        believed_value = "tense",
        claim_key = "front:front_0:status",
        confidence = 0.95999999999999996,
        id = "reaction_2",
        kind = "avoid_front",
        rule_id = "avoid_volatile_front",
        tick = 0,
      },
      topic = "reaction.emitted",
    },
    {
      event = {
        agent_id = "iva",
        beliefs = 3,
        interpretations = 3,
        knowledge = 3,
      },
      topic = "cognition.recomputed",
    },
    {
      event = {
        claim = {
          confidence = 0.95999999999999996,
          distorted = false,
          key = "front:front_0:status",
          value = "tense",
        },
        confidence = 0.79708800000000002,
        created_at = 0,
        deliver_at = 2,
        distortion_applied = false,
        id = "tx_1",
        provenance = {
          belief_sources = {
            "observation_1_0",
          },
          inherited = {
          },
        },
        receiver_id = "levko",
        receiver_sector = {
          5,
          4,
        },
        sender_id = "mara",
        sender_sector = {
          0,
          2,
        },
        source_claim_key = "front:front_0:status",
      },
      topic = "propagation.queued",
    },
    {
      event = {
        agent_id = "iva",
        beliefs = 3,
        interpretations = 3,
        knowledge = 3,
      },
      topic = "cognition.recomputed",
    },
    {
      event = {
        agent_id = "levko",
        beliefs = 0,
        interpretations = 0,
        knowledge = 0,
      },
      topic = "cognition.recomputed",
    },
    {
      event = {
        agent_id = "mara",
        beliefs = 3,
        interpretations = 3,
        knowledge = 3,
      },
      topic = "cognition.recomputed",
    },
    {
      event = {
        hours = 1,
        tick = 1,
      },
      topic = "time.advanced",
    },
    {
      event = {
        agent_id = "levko",
        observation = {
          confidence = 0.79708800000000002,
          delivery_state = "delivered",
          evidence = "transmitted",
          fact = {
            claims = {
              {
                confidence = 0.95999999999999996,
                key = "front:front_0:status",
                value = "tense",
              },
            },
          },
          id = "rumor_tx_1",
          knowledge_state = "assigned_as_evidence",
          observed_at = 2,
          observer_id = "levko",
          provenance = {
            distortion_applied = false,
            inherited = {
              belief_sources = {
                "observation_1_0",
              },
              inherited = {
              },
            },
            source_agent_id = "mara",
            transmission_id = "tx_1",
          },
          sector = {
            5,
            4,
          },
          source_agent_id = "mara",
          source_event_id = "tx_1",
          subject_id = "front:front_0:status",
          subject_type = "rumor",
        },
      },
      topic = "observation.delivered",
    },
    {
      event = {
        agent_id = "levko",
        believed_value = "tense",
        claim_key = "front:front_0:status",
        confidence = 0.75723399999999996,
        id = "reaction_3",
        kind = "avoid_front",
        rule_id = "avoid_volatile_front",
        tick = 2,
      },
      topic = "reaction.emitted",
    },
    {
      event = {
        agent_id = "levko",
        beliefs = 1,
        interpretations = 1,
        knowledge = 0,
      },
      topic = "cognition.recomputed",
    },
    {
      event = {
        observation_id = "rumor_tx_1",
        transmission = {
          claim = {
            confidence = 0.95999999999999996,
            distorted = false,
            key = "front:front_0:status",
            value = "tense",
          },
          confidence = 0.79708800000000002,
          created_at = 0,
          deliver_at = 2,
          distortion_applied = false,
          id = "tx_1",
          provenance = {
            belief_sources = {
              "observation_1_0",
            },
            inherited = {
            },
          },
          receiver_id = "levko",
          receiver_sector = {
            5,
            4,
          },
          sender_id = "mara",
          sender_sector = {
            0,
            2,
          },
          source_claim_key = "front:front_0:status",
        },
      },
      topic = "propagation.delivered",
    },
    {
      event = {
        agent_id = "iva",
        beliefs = 3,
        interpretations = 3,
        knowledge = 3,
      },
      topic = "cognition.recomputed",
    },
    {
      event = {
        agent_id = "levko",
        beliefs = 1,
        interpretations = 1,
        knowledge = 0,
      },
      topic = "cognition.recomputed",
    },
    {
      event = {
        agent_id = "mara",
        beliefs = 3,
        interpretations = 3,
        knowledge = 3,
      },
      topic = "cognition.recomputed",
    },
    {
      event = {
        hours = 1,
        tick = 2,
      },
      topic = "time.advanced",
    },
    {
      event = {
        claim = {
          confidence = 0.93141600000000002,
          distorted = false,
          key = "front:front_0:status",
          value = "tense",
        },
        confidence = 0.77335500000000001,
        created_at = 2,
        deliver_at = 5,
        distortion_applied = false,
        id = "tx_2",
        provenance = {
          belief_sources = {
            "observation_1_1",
          },
          inherited = {
          },
        },
        receiver_id = "levko",
        receiver_sector = {
          5,
          4,
        },
        sender_id = "iva",
        sender_sector = {
          0,
          3,
        },
        source_claim_key = "front:front_0:status",
      },
      topic = "propagation.queued",
    },
    {
      event = {
        agent_id = "levko",
        observation = {
          confidence = 0.77335500000000001,
          delivery_state = "delivered",
          evidence = "transmitted",
          fact = {
            claims = {
              {
                confidence = 0.93141600000000002,
                key = "front:front_0:status",
                value = "tense",
              },
            },
          },
          id = "rumor_tx_2",
          knowledge_state = "assigned_as_evidence",
          observed_at = 5,
          observer_id = "levko",
          provenance = {
            distortion_applied = false,
            inherited = {
              belief_sources = {
                "observation_1_1",
              },
              inherited = {
              },
            },
            source_agent_id = "iva",
            transmission_id = "tx_2",
          },
          sector = {
            5,
            4,
          },
          source_agent_id = "iva",
          source_event_id = "tx_2",
          subject_id = "front:front_0:status",
          subject_type = "rumor",
        },
      },
      topic = "observation.delivered",
    },
    {
      event = {
        agent_id = "levko",
        beliefs = 1,
        interpretations = 1,
        knowledge = 1,
      },
      topic = "cognition.recomputed",
    },
    {
      event = {
        observation_id = "rumor_tx_2",
        transmission = {
          claim = {
            confidence = 0.93141600000000002,
            distorted = false,
            key = "front:front_0:status",
            value = "tense",
          },
          confidence = 0.77335500000000001,
          created_at = 2,
          deliver_at = 5,
          distortion_applied = false,
          id = "tx_2",
          provenance = {
            belief_sources = {
              "observation_1_1",
            },
            inherited = {
            },
          },
          receiver_id = "levko",
          receiver_sector = {
            5,
            4,
          },
          sender_id = "iva",
          sender_sector = {
            0,
            3,
          },
          source_claim_key = "front:front_0:status",
        },
      },
      topic = "propagation.delivered",
    },
    {
      event = {
        agent_id = "iva",
        beliefs = 3,
        interpretations = 3,
        knowledge = 3,
      },
      topic = "cognition.recomputed",
    },
    {
      event = {
        agent_id = "levko",
        beliefs = 1,
        interpretations = 1,
        knowledge = 1,
      },
      topic = "cognition.recomputed",
    },
    {
      event = {
        agent_id = "mara",
        beliefs = 3,
        interpretations = 3,
        knowledge = 3,
      },
      topic = "cognition.recomputed",
    },
    {
      event = {
        hours = 3,
        tick = 5,
      },
      topic = "time.advanced",
    },
  },
  delivery_log = {
    {
      agent_id = "mara",
      evidence = "direct_local",
      observation_id = "observation_1_0",
      tick = 0,
    },
    {
      agent_id = "iva",
      evidence = "direct_local",
      observation_id = "observation_1_1",
      tick = 0,
    },
    {
      agent_id = "levko",
      evidence = "transmitted",
      observation_id = "rumor_tx_1",
      source_agent_id = "mara",
      tick = 2,
    },
    {
      agent_id = "levko",
      evidence = "transmitted",
      observation_id = "rumor_tx_2",
      source_agent_id = "iva",
      tick = 5,
    },
  },
  entities = {
    front_0 = {
      dynamic = {
        activity = 0.53300000000000003,
        entity_type = "front_state",
        id = "front_0",
        pair = {
          "nano_signal",
          "print_civic",
        },
        revision = 1,
        status = "tense",
        tension = 0.60499999999999998,
      },
      id = "front_0",
      static = {
        entity_type = "influence_front",
        id = "front_0",
        mean_pressure = 0.40500000000000003,
        pair = {
          "nano_signal",
          "print_civic",
        },
        sector_count = 4,
      },
    },
    front_1 = {
      dynamic = {
        activity = 0.3619,
        entity_type = "front_state",
        id = "front_1",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        revision = 1,
        status = "active",
        tension = 0.34560000000000002,
      },
      id = "front_1",
      static = {
        entity_type = "influence_front",
        id = "front_1",
        mean_pressure = 0.43559999999999999,
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        sector_count = 10,
      },
    },
    front_2 = {
      dynamic = {
        activity = 0.56659999999999999,
        entity_type = "front_state",
        id = "front_2",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        revision = 0,
        status = "tense",
        tension = 0.69440000000000002,
      },
      id = "front_2",
      static = {
        entity_type = "influence_front",
        id = "front_2",
        mean_pressure = 0.69440000000000002,
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        sector_count = 3,
      },
    },
    front_3 = {
      dynamic = {
        activity = 0.39300000000000002,
        entity_type = "front_state",
        id = "front_3",
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        revision = 0,
        status = "active",
        tension = 0.40500000000000003,
      },
      id = "front_3",
      static = {
        entity_type = "influence_front",
        id = "front_3",
        mean_pressure = 0.40500000000000003,
        pair = {
          "nano_signal",
          "silt_contamination",
        },
        sector_count = 2,
      },
    },
    front_4 = {
      dynamic = {
        activity = 0.39300000000000002,
        entity_type = "front_state",
        id = "front_4",
        pair = {
          "print_civic",
          "silt_contamination",
        },
        revision = 0,
        status = "active",
        tension = 0.40500000000000003,
      },
      id = "front_4",
      static = {
        entity_type = "influence_front",
        id = "front_4",
        mean_pressure = 0.40500000000000003,
        pair = {
          "print_civic",
          "silt_contamination",
        },
        sector_count = 5,
      },
    },
    territory_0 = {
      dynamic = {
        alert = 0.28899999999999998,
        alignment = "nano_signal",
        control_strength = 0.39750000000000002,
        entity_type = "territory_state",
        id = "territory_0",
        revision = 2,
        stability = 0.64270000000000005,
        status = "stable",
      },
      id = "territory_0",
      static = {
        alignment = "nano_signal",
        center = {
          1,
          0,
        },
        entity_type = "territory",
        id = "territory_0",
        mean_strength = 0.51749999999999996,
        sector_count = 4,
      },
    },
    territory_1 = {
      dynamic = {
        alert = 0.37,
        alignment = "print_civic",
        control_strength = 0.51000000000000001,
        entity_type = "territory_state",
        id = "territory_1",
        revision = 1,
        stability = 0.65800000000000003,
        status = "stable",
      },
      id = "territory_1",
      static = {
        alignment = "print_civic",
        center = {
          0,
          4,
        },
        entity_type = "territory",
        id = "territory_1",
        mean_strength = 0.51000000000000001,
        sector_count = 3,
      },
    },
    territory_2 = {
      dynamic = {
        alert = 0.64300000000000002,
        alignment = "nano_signal",
        control_strength = 0.52500000000000002,
        entity_type = "territory_state",
        id = "territory_2",
        revision = 2,
        stability = 0.66820000000000002,
        status = "stable",
      },
      id = "territory_2",
      static = {
        alignment = "nano_signal",
        center = {
          2,
          3,
        },
        entity_type = "territory",
        id = "territory_2",
        mean_strength = 0.52500000000000002,
        sector_count = 3,
      },
    },
    territory_3 = {
      dynamic = {
        alert = 0.55300000000000005,
        alignment = "silt_contamination",
        control_strength = 0.61719999999999997,
        entity_type = "territory_state",
        id = "territory_3",
        revision = 1,
        stability = 0.71060000000000001,
        status = "stable",
      },
      id = "territory_3",
      static = {
        alignment = "silt_contamination",
        center = {
          3,
          2,
        },
        entity_type = "territory",
        id = "territory_3",
        mean_strength = 0.61719999999999997,
        sector_count = 9,
      },
    },
    territory_4 = {
      dynamic = {
        alert = 0.253,
        alignment = "nano_signal",
        control_strength = 0.52500000000000002,
        entity_type = "territory_state",
        id = "territory_4",
        revision = 1,
        stability = 0.69220000000000004,
        status = "stable",
      },
      id = "territory_4",
      static = {
        alignment = "nano_signal",
        center = {
          5,
          0,
        },
        entity_type = "territory",
        id = "territory_4",
        mean_strength = 0.52500000000000002,
        sector_count = 3,
      },
    },
    territory_5 = {
      dynamic = {
        alert = 0.28000000000000003,
        alignment = "print_civic",
        control_strength = 0.51000000000000001,
        entity_type = "territory_state",
        id = "territory_5",
        revision = 0,
        stability = 0.68200000000000005,
        status = "stable",
      },
      id = "territory_5",
      static = {
        alignment = "print_civic",
        center = {
          5,
          4,
        },
        entity_type = "territory",
        id = "territory_5",
        mean_strength = 0.51000000000000001,
        sector_count = 3,
      },
    },
  },
  external_events = {
    {
      cause_event_id = "runtime_event_1",
      changes = {
        activity = {
          after = 0.53300000000000003,
          before = 0.39300000000000002,
        },
        status = {
          after = "tense",
          before = "active",
        },
        tension = {
          after = 0.60499999999999998,
          before = 0.40500000000000003,
        },
      },
      event_type = "front_state_changed",
      id = "derived_event_1",
      observability = "local_or_transmitted",
      revision = 1,
      sector = {
        0,
        3,
      },
      subject_id = "front_0",
      subject_type = "front",
    },
    {
      cause_event_id = "runtime_event_2",
      changes = {
        alert = {
          after = 0.316,
          before = 0.28000000000000003,
        },
        control_strength = {
          after = 0.39750000000000002,
          before = 0.51749999999999996,
        },
        stability = {
          after = 0.63549999999999995,
          before = 0.6835,
        },
      },
      event_type = "territory_state_changed",
      id = "derived_event_2",
      observability = "local_or_transmitted",
      revision = 2,
      sector = {
        1,
        0,
      },
      subject_id = "territory_0",
      subject_type = "territory",
    },
    {
      cause_event_id = "runtime_event_3",
      changes = {
        activity = {
          after = 0.3619,
          before = 0.41139999999999999,
        },
        tension = {
          after = 0.34560000000000002,
          before = 0.43559999999999999,
        },
      },
      event_type = "front_state_changed",
      id = "derived_event_3",
      observability = "local_or_transmitted",
      revision = 3,
      sector = {
        1,
        1,
      },
      subject_id = "front_1",
      subject_type = "front",
    },
  },
  integration_log = {
    {
      imported = {
        duplicates = 0,
        entities = 11,
        events = 3,
        observations = 13,
      },
      kind = "pixelgen_v080",
      revision = 3,
      tick = 0,
      validation = {
        contract = {
          dynamic_state_role = "store deterministic mutable overlay and provenance",
          ebe_role = "assign observations to agents, form memory/belief, propagate and react",
          global_knowledge = "forbidden",
          observation_semantics = "local evidence only",
          pixelgen_static_role = "generate semantic world entities and seed hooks",
        },
        dynamic_entities = 11,
        events = 3,
        observations = 13,
        static_entities = 11,
      },
    },
  },
  integration_state = {
    pixelgen = {
      entity_ids = {
        front_0 = true,
        front_1 = true,
        front_2 = true,
        front_3 = true,
        front_4 = true,
        territory_0 = true,
        territory_1 = true,
        territory_2 = true,
        territory_3 = true,
        territory_4 = true,
        territory_5 = true,
      },
      event_ids = {
        derived_event_1 = true,
        derived_event_2 = true,
        derived_event_3 = true,
      },
      observation_ids = {
        observation_1_0 = true,
        observation_1_1 = true,
        observation_1_2 = true,
        observation_1_3 = true,
        observation_2_0 = true,
        observation_2_1 = true,
        observation_2_2 = true,
        observation_2_3 = true,
        observation_3_0 = true,
        observation_3_1 = true,
        observation_3_2 = true,
        observation_3_3 = true,
        observation_3_4 = true,
      },
      revisions = {
        [3] = true,
      },
    },
  },
  knowledge_opts = {
  },
  propagation = {
    default_delay = 1,
    default_distortion = 0.080000000000000002,
    default_trust = 0.71999999999999997,
    links = {
      ["iva->levko"] = {
        delay = 3,
        distortion = 0.040000000000000001,
        from = "iva",
        to = "levko",
        trust = 0.94999999999999996,
      },
      ["mara->levko"] = {
        delay = 2,
        distortion = 0.059999999999999998,
        from = "mara",
        to = "levko",
        trust = 0.94999999999999996,
      },
    },
    queue = {
    },
    sequence = 2,
  },
  reaction = {
    fired = {
      ["iva|avoid_volatile_front|front:front_0:status|\"tense\""] = 0,
      ["levko|avoid_volatile_front|front:front_0:status|\"tense\""] = 2,
      ["mara|avoid_volatile_front|front:front_0:status|\"tense\""] = 0,
    },
  },
  reaction_log = {
    {
      agent_id = "mara",
      believed_value = "tense",
      claim_key = "front:front_0:status",
      confidence = 0.95999999999999996,
      id = "reaction_1",
      kind = "avoid_front",
      rule_id = "avoid_volatile_front",
      tick = 0,
    },
    {
      agent_id = "iva",
      believed_value = "tense",
      claim_key = "front:front_0:status",
      confidence = 0.95999999999999996,
      id = "reaction_2",
      kind = "avoid_front",
      rule_id = "avoid_volatile_front",
      tick = 0,
    },
    {
      agent_id = "levko",
      believed_value = "tense",
      claim_key = "front:front_0:status",
      confidence = 0.75723399999999996,
      id = "reaction_3",
      kind = "avoid_front",
      rule_id = "avoid_volatile_front",
      tick = 2,
    },
  },
  seed = 3030,
  tick = 5,
  version = "0.3.0",
}
