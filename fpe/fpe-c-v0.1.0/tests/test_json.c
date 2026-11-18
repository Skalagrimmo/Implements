#include "fpe/fpe.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdio.h>
#include <string.h>

static const char k_projection[] =
    "{\"schema\":\"fpe.pixelgen_hierarchy/0.6.0\",\"fpe_version\":\"0.6.0\",\"bridge_version\":\"0.6.0\",\"mode\":\"read_only_hierarchical_projection\",\"authority\":{\"objective_state_owner\":\"PixelGen\",\"geometry_owner\":\"FPE\",\"writeback\":\"disabled_in_v0.6\"},\"source\":{\"pixelgen_world_fingerprint\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\",\"pixelgen_generator_version\":\"1.0.0\",\"pixelgen_state_version\":\"0.8.0\",\"seed\":7301,\"dimensions\":[1,1],\"state_revision\":0,\"state_tick\":0},\"layout\":{\"cluster_kind\":\"pixelgen_sector\",\"buds_per_sector\":4,\"sector_spacing\":10.0,\"local_bud_offset\":2.15},\"hierarchy\":{\"schema\":\"fpe.view_hierarchy/0.6.0\",\"levels\":[\"world\",\"cluster\",\"bud\",\"geometry\"],\"initial_detail\":\"cluster_proxy\",\"expansion_state_owner\":\"viewer\",\"semantic_effect\":\"none\"},\"clusters\":[{\"id\":\"sector_0_0\",\"sector\":[0,0],\"source\":{\"region_id\":0,\"biome\":\"dark_forest\",\"subbiome\":\"wet_pine\",\"geography_zone\":\"mid\",\"territory_id\":null,\"territory_alignment\":null,\"territory_status\":\"neutral\",\"topology_status\":\"neutral\",\"front_ids\":[],\"corridors\":[]},\"state\":{\"control_strength\":0.52,\"stability\":0.62,\"alert\":0.12,\"front_tension\":0.0,\"front_activity\":0.0,\"front_status\":\"quiet\"},\"projection\":{\"cohesion\":0.6,\"breakup_resistance\":0.6,\"agitation\":0.1,\"collapse_bias\":0.2,\"damage_proxy\":0.3,\"update_rate\":0.18},\"buds\":[{\"id\":\"sector_0_0_bud_0\",\"index\":0,\"type\":\"STRAIGHT\",\"offset\":[-1,-1],\"seed_key\":\"7301:0:0:bud:0\"},{\"id\":\"sector_0_0_bud_1\",\"index\":1,\"type\":\"STRAIGHT\",\"offset\":[1,-1],\"seed_key\":\"7301:0:0:bud:1\"},{\"id\":\"sector_0_0_bud_2\",\"index\":2,\"type\":\"STRAIGHT\",\"offset\":[-1,1],\"seed_key\":\"7301:0:0:bud:2\"},{\"id\":\"sector_0_0_bud_3\",\"index\":3,\"type\":\"STRAIGHT\",\"offset\":[1,1],\"seed_key\":\"7301:0:0:bud:3\"}]}],\"summary\":{\"cluster_count\":1,\"bud_count\":4,\"territory_cluster_count\":0,\"front_cluster_count\":0,\"straight_bud_count\":4,\"curved_bud_count\":0},\"projection_fingerprint\":\"3ecf678309a1665f767870f6d26b16f186909841572fc11cfe8e1ea70f4e356a\"}";

static void test_canonical_sha256(void) {
    FPEError error;
    char fingerprint[65];
    const char basic[] = "{\"projection_fingerprint\":\"ignored\",\"a\":1}";
    const char unicode[] = "{\"projection_fingerprint\":\"x\",\"z\":\"ліс 🌲\",\"a\":false}";
    const char duplicate[] = "{\"a\":1,\"a\":2}";
    assert(fpe_json_canonical_fingerprint(basic, sizeof(basic)-1u, fingerprint, &error) == FPE_OK);
    assert(strcmp(fingerprint, "015abd7f5cc57a2dd94b7590f04ad8084273905ee33ec5cebeae62276a97f862") == 0);
    assert(fpe_json_canonical_fingerprint(unicode, sizeof(unicode)-1u, fingerprint, &error) == FPE_OK);
    assert(strcmp(fingerprint, "536e4f605f37403dd17a302a6a7227a8e1f50e92df933531f9013e965e861912") == 0);
    assert(fpe_json_canonical_fingerprint(duplicate, sizeof(duplicate)-1u, fingerprint, &error) == FPE_INVALID_PROJECTION);
}

static void test_projection_bridge(void) {
    FPEError error;
    FPEProjection projection;
    FPERuntime *runtime = NULL;
    FPEPlan plan;
    char altered[sizeof(k_projection)];
    char fingerprint[65];
    assert(fpe_json_canonical_fingerprint(k_projection, sizeof(k_projection)-1u, fingerprint, &error) == FPE_OK);
    assert(strcmp(fingerprint, "3ecf678309a1665f767870f6d26b16f186909841572fc11cfe8e1ea70f4e356a") == 0);
    assert(fpe_projection_from_json(k_projection, sizeof(k_projection)-1u, &projection, &error) == FPE_OK);
    assert(projection.cluster_count == 1u);
    assert(projection.columns == 1u && projection.rows == 1u);
    assert(projection.seed == 7301);
    assert(strcmp(projection.clusters[0].id, "sector_0_0") == 0);
    assert(projection.summary.straight_bud_count == 4u);
    assert(fpe_runtime_create(&projection, 4u, &runtime, &error) == FPE_OK);
    fpe_projection_json_destroy(&projection);
    memset(&plan, 0, sizeof(plan));
    assert(fpe_runtime_get_plan(runtime, &plan, &error) == FPE_OK);
    assert(plan.item_count == 1u && plan.counts.cluster_proxies == 1u);
    fpe_plan_destroy(&plan);
    fpe_runtime_destroy(runtime);

    memcpy(altered, k_projection, sizeof(k_projection));
    {
        char *metric = strstr(altered, "\"stability\":0.62");
        assert(metric != NULL);
        metric[strlen("\"stability\":0.")] = '6';
        metric[strlen("\"stability\":0.") + 1u] = '3';
    }
    assert(fpe_projection_from_json(altered, sizeof(altered)-1u, &projection, &error) == FPE_INVALID_PROJECTION);
}

int main(void) {
    test_canonical_sha256();
    test_projection_bridge();
    puts("FPE C JSON bridge: PASS (SHA-256, UTF-8, canonical keys, projection validation, runtime ownership)");
    return 0;
}
