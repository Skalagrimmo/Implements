#include "fpe/fpe.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char k_projection[] =
    "{\"schema\":\"fpe.pixelgen_hierarchy/0.6.0\",\"fpe_version\":\"0.6.0\",\"bridge_version\":\"0.6.0\",\"mode\":\"read_only_hierarchical_projection\",\"authority\":{\"objective_state_owner\":\"PixelGen\",\"geometry_owner\":\"FPE\",\"writeback\":\"disabled_in_v0.6\"},\"source\":{\"pixelgen_world_fingerprint\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\",\"pixelgen_generator_version\":\"1.0.0\",\"pixelgen_state_version\":\"0.8.0\",\"seed\":7301,\"dimensions\":[1,1],\"state_revision\":0,\"state_tick\":0},\"layout\":{\"cluster_kind\":\"pixelgen_sector\",\"buds_per_sector\":4,\"sector_spacing\":10.0,\"local_bud_offset\":2.15},\"hierarchy\":{\"schema\":\"fpe.view_hierarchy/0.6.0\",\"levels\":[\"world\",\"cluster\",\"bud\",\"geometry\"],\"initial_detail\":\"cluster_proxy\",\"expansion_state_owner\":\"viewer\",\"semantic_effect\":\"none\"},\"clusters\":[{\"id\":\"sector_0_0\",\"sector\":[0,0],\"source\":{\"region_id\":0,\"biome\":\"dark_forest\",\"subbiome\":\"wet_pine\",\"geography_zone\":\"mid\",\"territory_id\":null,\"territory_alignment\":null,\"territory_status\":\"neutral\",\"topology_status\":\"neutral\",\"front_ids\":[],\"corridors\":[]},\"state\":{\"control_strength\":0.52,\"stability\":0.62,\"alert\":0.12,\"front_tension\":0.0,\"front_activity\":0.0,\"front_status\":\"quiet\"},\"projection\":{\"cohesion\":0.6,\"breakup_resistance\":0.6,\"agitation\":0.1,\"collapse_bias\":0.2,\"damage_proxy\":0.3,\"update_rate\":0.18},\"buds\":[{\"id\":\"sector_0_0_bud_0\",\"index\":0,\"type\":\"STRAIGHT\",\"offset\":[-1,-1],\"seed_key\":\"7301:0:0:bud:0\"},{\"id\":\"sector_0_0_bud_1\",\"index\":1,\"type\":\"STRAIGHT\",\"offset\":[1,-1],\"seed_key\":\"7301:0:0:bud:1\"},{\"id\":\"sector_0_0_bud_2\",\"index\":2,\"type\":\"STRAIGHT\",\"offset\":[-1,1],\"seed_key\":\"7301:0:0:bud:2\"},{\"id\":\"sector_0_0_bud_3\",\"index\":3,\"type\":\"STRAIGHT\",\"offset\":[1,1],\"seed_key\":\"7301:0:0:bud:3\"}]}],\"summary\":{\"cluster_count\":1,\"bud_count\":4,\"territory_cluster_count\":0,\"front_cluster_count\":0,\"straight_bud_count\":4,\"curved_bud_count\":0},\"projection_fingerprint\":\"3ecf678309a1665f767870f6d26b16f186909841572fc11cfe8e1ea70f4e356a\"}";

static void test_canonical_sha256(void) {
    FPEError error;
    char fingerprint[65];
    const char basic[] = "{\"projection_fingerprint\":\"ignored\",\"a\":1}";
    const char unicode[] = "{\"projection_fingerprint\":\"x\",\"z\":\"ліс 🌲\",\"a\":false}";
    const char duplicate[] = "{\"a\":1,\"a\":2}";
    const char trailing[] = "{\"a\":1} trailing";
    const char nul_escape[] = "{\"a\":\"\\u0000\"}";
    assert(fpe_json_canonical_fingerprint(basic, sizeof(basic)-1u, fingerprint, &error) == FPE_OK);
    assert(strcmp(fingerprint, "015abd7f5cc57a2dd94b7590f04ad8084273905ee33ec5cebeae62276a97f862") == 0);
    assert(fpe_json_canonical_fingerprint(unicode, sizeof(unicode)-1u, fingerprint, &error) == FPE_OK);
    assert(strcmp(fingerprint, "536e4f605f37403dd17a302a6a7227a8e1f50e92df933531f9013e965e861912") == 0);
    assert(fpe_json_canonical_fingerprint(duplicate, sizeof(duplicate)-1u, fingerprint, &error) == FPE_INVALID_PROJECTION);
    assert(fpe_json_canonical_fingerprint(trailing, sizeof(trailing)-1u, fingerprint, &error) == FPE_INVALID_PROJECTION);
    assert(fpe_json_canonical_fingerprint(nul_escape, sizeof(nul_escape)-1u, fingerprint, &error) == FPE_INVALID_PROJECTION);
}

static char *read_text_file(const char *path, size_t *out_length) {
    FILE *file = fopen(path, "rb");
    long size;
    char *data;
    if (file == NULL) return NULL;
    if (fseek(file, 0, SEEK_END) != 0) { fclose(file); return NULL; }
    size = ftell(file);
    if (size < 0 || (unsigned long)size > 8u * 1024u * 1024u) { fclose(file); return NULL; }
    if (fseek(file, 0, SEEK_SET) != 0) { fclose(file); return NULL; }
    data = (char *)malloc((size_t)size + 1u);
    if (data == NULL) { fclose(file); return NULL; }
    if (fread(data, 1u, (size_t)size, file) != (size_t)size) {
        free(data); fclose(file); return NULL;
    }
    data[(size_t)size] = '\0';
    fclose(file);
    *out_length = (size_t)size;
    return data;
}

static void test_golden_projection(const char *path, const char *expected_fp) {
    FPEError error;
    FPEProjection projection;
    FPERuntime *runtime = NULL;
    FPEPlan plan;
    char fingerprint[65];
    char *json;
    size_t length = 0u;
    json = read_text_file(path, &length);
    assert(json != NULL);
    assert(fpe_json_canonical_fingerprint(json, length, fingerprint, &error) == FPE_OK);
    assert(strcmp(fingerprint, expected_fp) == 0);
    assert(fpe_projection_from_json(json, length, &projection, &error) == FPE_OK);
    assert(projection.cluster_count == 30u);
    assert(projection.summary.bud_count == 120u);
    assert(projection.columns == 6u && projection.rows == 5u);
    assert(fpe_runtime_create(&projection, 8u, &runtime, &error) == FPE_OK);
    fpe_projection_json_destroy(&projection);
    memset(&plan, 0, sizeof(plan));
    assert(fpe_runtime_get_plan(runtime, &plan, &error) == FPE_OK);
    assert(plan.item_count == 30u && plan.counts.cluster_proxies == 30u);
    fpe_plan_destroy(&plan);
    fpe_runtime_destroy(runtime);
    free(json);
}

static void assert_batches_equal(const FPEUpdateBatch *a,const FPEUpdateBatch *b) {
    size_t i;
    assert(a->tick==b->tick);
    assert(a->update_count==b->update_count);
    assert(a->deferred_count==b->deferred_count);
    assert(a->repeated==b->repeated);
    for(i=0;i<a->update_count;++i) {
        assert(strcmp(a->updates[i].cluster_id,b->updates[i].cluster_id)==0);
        assert(a->updates[i].tick==b->updates[i].tick);
        assert(a->updates[i].elapsed==b->updates[i].elapsed);
        assert(a->updates[i].period==b->updates[i].period);
        assert(a->updates[i].detail==b->updates[i].detail);
    }
}

static void test_snapshot_fixture(const char *path,bool fresh_scheduler) {
    FPEError error;
    FPERuntime *runtime=NULL,*roundtrip=NULL,*bad_runtime=NULL;
    FPEUpdateBatch first,second;
    char *json,*serialized=NULL,*corrupt=NULL,*budget_field;
    size_t length=0u,serialized_length=0u;
    json=read_text_file(path,&length);
    assert(json!=NULL);
    assert(fpe_runtime_restore_json(json,length,&runtime,&error)==FPE_OK);
    assert(runtime!=NULL);
    assert(fpe_runtime_serialize_json(runtime,&serialized,&serialized_length,&error)==FPE_OK);
    assert(serialized!=NULL && serialized_length!=0u);
    assert(strstr(serialized,"\"runtime_version\":\"1.0.0\"")!=NULL);
    assert(fpe_runtime_restore_json(serialized,serialized_length,&roundtrip,&error)==FPE_OK);
    assert(roundtrip!=NULL);

    memset(&first,0,sizeof(first));
    memset(&second,0,sizeof(second));
    if(fresh_scheduler) {
        /* Historical 0.11: host clock 13, new-revision scheduler clock -1. */
        assert(fpe_runtime_step(runtime,12,&first,&error)==FPE_INVALID_TICK);
        assert(fpe_runtime_step(roundtrip,12,&second,&error)==FPE_INVALID_TICK);
        assert(fpe_runtime_step(runtime,13,&first,&error)==FPE_OK);
        assert(fpe_runtime_step(roundtrip,13,&second,&error)==FPE_OK);
        assert(!first.repeated && !second.repeated);
        assert_batches_equal(&first,&second);
        fpe_update_batch_destroy(&first);
        fpe_update_batch_destroy(&second);
        assert(fpe_runtime_step(runtime,13,&first,&error)==FPE_OK);
        assert(fpe_runtime_step(roundtrip,13,&second,&error)==FPE_OK);
        assert(first.repeated && second.repeated);
        assert_batches_equal(&first,&second);
    } else {
        /* Historical 0.12: both clocks are already at tick 19. */
        assert(fpe_runtime_step(runtime,18,&first,&error)==FPE_INVALID_TICK);
        assert(fpe_runtime_step(roundtrip,18,&second,&error)==FPE_INVALID_TICK);
        assert(fpe_runtime_step(runtime,19,&first,&error)==FPE_OK);
        assert(fpe_runtime_step(roundtrip,19,&second,&error)==FPE_OK);
        assert(first.repeated && second.repeated);
        assert_batches_equal(&first,&second);
        fpe_update_batch_destroy(&first);
        fpe_update_batch_destroy(&second);
        assert(fpe_runtime_step(runtime,20,&first,&error)==FPE_OK);
        assert(fpe_runtime_step(roundtrip,20,&second,&error)==FPE_OK);
        assert_batches_equal(&first,&second);
    }
    fpe_update_batch_destroy(&first);
    fpe_update_batch_destroy(&second);

    /* A modified budget in the snapshot must be rejected, not normalized. */
    corrupt=(char *)malloc(serialized_length+1u);
    assert(corrupt!=NULL);
    memcpy(corrupt,serialized,serialized_length+1u);
    budget_field=strstr(corrupt,"\"budget\":3");
    assert(budget_field!=NULL);
    budget_field[strlen("\"budget\":")]='4';
    {
        FPEErrorCode corrupt_result=fpe_runtime_restore_json(corrupt,serialized_length,&bad_runtime,&error);
        if(corrupt_result!=FPE_INVALID_SNAPSHOT) {
            (void)fprintf(stderr,"corrupt budget was accepted: result=%d error=%s context=%.48s\\n",
                          (int)corrupt_result,error.message,budget_field-10);
        }
        assert(corrupt_result==FPE_INVALID_SNAPSHOT);
    }
    assert(bad_runtime==NULL);

    free(corrupt);
    free(json);
    fpe_json_string_destroy(serialized);
    fpe_runtime_destroy(runtime);
    fpe_runtime_destroy(roundtrip);
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

int main(int argc, char **argv) {
    assert(argc == 5);
    test_canonical_sha256();
    test_projection_bridge();
    test_golden_projection(argv[1], "e62718146d9393f265317e3a2351fecc0ba0757862748be2d322ec4043e699c8");
    test_golden_projection(argv[2], "678c6027a279ceeade30c7f0284554bdc47dfe94507a6aa1d4276dc4f69750c1");
    test_snapshot_fixture(argv[3], true);
    test_snapshot_fixture(argv[4], false);
    puts("FPE C JSON bridge: PASS (projection fingerprints, 0.11/0.12 snapshot restore, round-trip, split clocks)");
    return 0;
}
