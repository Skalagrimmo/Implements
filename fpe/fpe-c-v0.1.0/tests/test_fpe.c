#include "fpe/fpe.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static FPECluster clusters[4];
static FPEBud buds[4][4];
static char cluster_ids[4][FPE_ID_CAPACITY];
static char bud_ids[4][4][FPE_ID_CAPACITY];
static char seed_keys[4][4][FPE_ID_CAPACITY];
static const char *front_ids[2][2] = {{"front_north",NULL},{"front_south",NULL}};
static const char fp_a[65] = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
static const char fp_world[65] = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789";

static FPEProjection fixture(void) {
    static FPEProjection projection;
    size_t i,j;
    memset(&projection,0,sizeof(projection));
    memset(clusters,0,sizeof(clusters));
    for(i=0;i<4;++i) {
        const unsigned x=(unsigned)(i%2u), y=(unsigned)(i/2u);
        (void)snprintf(cluster_ids[i],sizeof(cluster_ids[i]),"sector_%u_%u",x,y);
        clusters[i].id=cluster_ids[i];
        clusters[i].sector_x=x; clusters[i].sector_y=y;
        clusters[i].projection.cohesion=0.7;
        clusters[i].projection.breakup_resistance=0.65;
        clusters[i].projection.agitation=0.2;
        clusters[i].projection.collapse_bias=0.1;
        clusters[i].projection.damage_proxy=0.05;
        clusters[i].projection.update_rate=(i==0u?0.8:(i==1u?0.5:0.2));
        clusters[i].state.stability=0.8;
        clusters[i].state.alert=0.1;
        clusters[i].state.front_tension=0.2;
        clusters[i].state.front_activity=0.15;
        clusters[i].state.control_strength=1.0;
        clusters[i].state.front_status=FPE_FRONT_QUIET;
        clusters[i].territory_id=(i%2u==0u?"territory_alpha":NULL);
        if(i==0u) { clusters[i].front_ids=front_ids[0]; clusters[i].front_count=1; }
        if(i==3u) { clusters[i].front_ids=front_ids[1]; clusters[i].front_count=1; }
        for(j=0;j<4;++j) {
            static const int offsets[4][2]={{-1,-1},{1,-1},{-1,1},{1,1}};
            (void)snprintf(bud_ids[i][j],sizeof(bud_ids[i][j]),"sector_%u_%u_bud_%u",x,y,(unsigned)j);
            (void)snprintf(seed_keys[i][j],sizeof(seed_keys[i][j]),"sg_%u_%u_b%u",x,y,(unsigned)j);
            buds[i][j].id=bud_ids[i][j];
            buds[i][j].index=(uint32_t)j;
            buds[i][j].offset_x=offsets[j][0];
            buds[i][j].offset_z=offsets[j][1];
            buds[i][j].type=((i+j)%2u==0u?FPE_BUD_STRAIGHT:FPE_BUD_CURVED);
            buds[i][j].seed_key=seed_keys[i][j];
        }
        memcpy(clusters[i].buds,buds[i],sizeof(buds[i]));
    }
    projection.schema=FPE_PROJECTION_SCHEMA;
    projection.mode="read_only_hierarchical_projection";
    projection.projection_fingerprint=fp_a;
    projection.pixelgen_world_fingerprint=fp_world;
    projection.seed=7301;
    projection.columns=2; projection.rows=2;
    projection.state_revision=1; projection.state_tick=10;
    projection.sector_spacing=12.0; projection.local_bud_offset=2.2;
    projection.clusters=clusters; projection.cluster_count=4;
    projection.summary.cluster_count=4;
    projection.summary.bud_count=16;
    projection.summary.territory_cluster_count=2;
    projection.summary.front_cluster_count=2;
    projection.summary.straight_bud_count=8;
    projection.summary.curved_bud_count=8;
    return projection;
}

static void require_ok(FPEErrorCode code,const FPEError *error) {
    if(code!=FPE_OK) {
        fprintf(stderr,"unexpected FPE error %s: %s\n",fpe_error_name(code),error?error->message:"(no details)");
        abort();
    }
}

static void test_projection_and_plan(void) {
    FPEProjection p=fixture();
    FPEError e;
    FPERuntime *rt=NULL;
    FPEPlan plan;
    FPEViewState view;
    require_ok(fpe_projection_validate(&p,&e),&e);
    require_ok(fpe_runtime_create(&p,8,&rt,&e),&e);
    memset(&plan,0,sizeof(plan));
    require_ok(fpe_runtime_get_plan(rt,&plan,&e),&e);
    assert(plan.item_count==4 && plan.counts.cluster_proxies==4);
    assert(plan.counts.bud_proxies==0 && plan.counts.geometries==0);
    fpe_plan_destroy(&plan);

    memset(&view,0,sizeof(view));
    require_ok(fpe_runtime_toggle_cluster(rt,"sector_0_0",&view,&e),&e);
    assert(view.expanded_cluster_count==1 && view.expanded_bud_count==0);
    fpe_view_state_destroy(&view);
    memset(&plan,0,sizeof(plan));
    require_ok(fpe_runtime_get_plan(rt,&plan,&e),&e);
    assert(plan.item_count==7);
    assert(plan.counts.cluster_proxies==3 && plan.counts.bud_proxies==4 && plan.counts.geometries==0);
    fpe_plan_destroy(&plan);

    memset(&view,0,sizeof(view));
    require_ok(fpe_runtime_toggle_bud(rt,"sector_0_0_bud_0",&view,&e),&e);
    assert(view.expanded_cluster_count==1 && view.expanded_bud_count==1);
    fpe_view_state_destroy(&view);
    memset(&plan,0,sizeof(plan));
    require_ok(fpe_runtime_get_plan(rt,&plan,&e),&e);
    assert(plan.item_count==7 && plan.counts.geometries==1 && plan.counts.bud_proxies==3);
    assert(plan.counts.nodes==8 && plan.counts.edges==12);
    assert(plan.items[0].kind==FPE_PLAN_CLUSTER_PROXY || plan.items[0].kind==FPE_PLAN_GEOMETRY);
    fpe_plan_destroy(&plan);

    /* Curved bud geometry is independently deterministic and has 14 nodes. */
    memset(&view,0,sizeof(view));
    require_ok(fpe_runtime_toggle_bud(rt,"sector_0_0_bud_1",&view,&e),&e);
    fpe_view_state_destroy(&view);
    memset(&plan,0,sizeof(plan));
    require_ok(fpe_runtime_get_plan(rt,&plan,&e),&e);
    assert(plan.counts.geometries==2 && plan.counts.nodes==22);
    {
        FPEPlan repeat;
        size_t k;
        memset(&repeat,0,sizeof(repeat));
        require_ok(fpe_runtime_get_plan(rt,&repeat,&e),&e);
        assert(repeat.item_count==plan.item_count);
        for(k=0;k<plan.item_count;++k) {
            const FPEPlanItem *left=&plan.items[k], *right=&repeat.items[k];
            size_t n;
            assert(left->kind==right->kind && left->node_count==right->node_count && left->edge_count==right->edge_count);
            for(n=0;n<left->node_count;++n) {
                assert(left->nodes[n].x==right->nodes[n].x);
                assert(left->nodes[n].y==right->nodes[n].y);
                assert(left->nodes[n].z==right->nodes[n].z);
                assert(left->nodes[n].phase==right->nodes[n].phase);
                assert(left->nodes[n].glyph_index==right->nodes[n].glyph_index);
            }
        }
        fpe_plan_destroy(&repeat);
    }
    fpe_plan_destroy(&plan);

    /* Collapse removes descendant expansion; a bud cannot expand under a closed parent. */
    memset(&view,0,sizeof(view));
    require_ok(fpe_runtime_toggle_cluster(rt,"sector_0_0",&view,&e),&e);
    fpe_view_state_destroy(&view);
    assert(fpe_runtime_toggle_bud(rt,"sector_0_0_bud_0",&view,&e)==FPE_PARENT_COLLAPSED);
    fpe_runtime_destroy(rt);
}

static void test_view_normalization(void) {
    FPEProjection p=fixture();
    FPEError e;
    FPERuntime *rt=NULL;
    FPEViewState proposed,normalized;
    char *clusters_in[3]={"sector_1_1","sector_1_1","not-a-cluster"};
    char *buds_in[3]={"sector_1_1_bud_0","sector_0_0_bud_0","not-a-bud"};
    memset(&proposed,0,sizeof(proposed));
    memset(&normalized,0,sizeof(normalized));
    proposed.expanded_clusters=clusters_in; proposed.expanded_cluster_count=3;
    proposed.expanded_buds=buds_in; proposed.expanded_bud_count=3;
    require_ok(fpe_runtime_create(&p,8,&rt,&e),&e);
    require_ok(fpe_runtime_set_view(rt,&proposed,&normalized,&e),&e);
    assert(normalized.expanded_cluster_count==1);
    assert(strcmp(normalized.expanded_clusters[0],"sector_1_1")==0);
    assert(normalized.expanded_bud_count==1);
    assert(strcmp(normalized.expanded_buds[0],"sector_1_1_bud_0")==0);
    fpe_view_state_destroy(&normalized);
    assert(fpe_runtime_set_view(rt,NULL,&normalized,&e)==FPE_INVALID_VIEW);
    fpe_runtime_destroy(rt);
}

static void test_scheduler_and_checkpoint(void) {
    FPEProjection p=fixture();
    FPEError e;
    FPERuntime *rt=NULL,*restored=NULL;
    FPEUpdateBatch batch;
    FPECheckpoint *checkpoint=NULL;
    FPEViewState view;
    require_ok(fpe_runtime_create(&p,2,&rt,&e),&e);
    memset(&batch,0,sizeof(batch));
    require_ok(fpe_runtime_step(rt,0,&batch,&e),&e);
    assert(batch.tick==0 && batch.update_count==2 && batch.deferred_count==2 && !batch.repeated);
    assert(strcmp(batch.updates[0].cluster_id,"sector_0_0")==0);
    assert(strcmp(batch.updates[1].cluster_id,"sector_0_1")==0);
    fpe_update_batch_destroy(&batch);
    require_ok(fpe_runtime_step(rt,0,&batch,&e),&e);
    assert(batch.repeated && batch.update_count==0);
    fpe_update_batch_destroy(&batch);

    require_ok(fpe_runtime_step(rt,1,&batch,&e),&e);
    assert(batch.update_count==2 && batch.deferred_count==0);
    fpe_update_batch_destroy(&batch);
    assert(fpe_runtime_step(rt,0,&batch,&e)==FPE_INVALID_TICK);

    memset(&view,0,sizeof(view));
    require_ok(fpe_runtime_toggle_cluster(rt,"sector_0_0",&view,&e),&e);
    fpe_view_state_destroy(&view);
    memset(&view,0,sizeof(view));
    require_ok(fpe_runtime_toggle_bud(rt,"sector_0_0_bud_0",&view,&e),&e);
    fpe_view_state_destroy(&view);
    require_ok(fpe_runtime_step(rt,4,&batch,&e),&e);
    {
        size_t i; bool found=false;
        for(i=0;i<batch.update_count;++i) if(strcmp(batch.updates[i].cluster_id,"sector_0_0")==0) {
            found=true; assert(batch.updates[i].detail==FPE_PLAN_GEOMETRY);
            assert(batch.updates[i].period==1u);
        }
        assert(found);
    }
    fpe_update_batch_destroy(&batch);

    require_ok(fpe_runtime_checkpoint(rt,&checkpoint,&e),&e);
    require_ok(fpe_runtime_restore(checkpoint,&restored,&e),&e);
    require_ok(fpe_runtime_step(restored,4,&batch,&e),&e);
    assert(batch.repeated && batch.update_count==0);
    fpe_update_batch_destroy(&batch);
    memset(&view,0,sizeof(view));
    require_ok(fpe_runtime_get_view(restored,&view,&e),&e);
    assert(view.expanded_cluster_count==1 && view.expanded_bud_count==1);
    fpe_view_state_destroy(&view);

    fpe_checkpoint_destroy(checkpoint);
    fpe_runtime_destroy(restored);
    fpe_runtime_destroy(rt);
}

static void test_request_and_revision_handoff(void) {
    FPEProjection p=fixture(), next;
    FPEError e;
    FPERuntime *rt=NULL;
    FPEActionRequest request;
    FPEUpdateBatch batch;
    FPECheckpoint *checkpoint=NULL;
    FPERuntime *restored=NULL;
    bool changed=false;
    require_ok(fpe_runtime_create(&p,8,&rt,&e),&e);
    memset(&request,0,sizeof(request));
    require_ok(fpe_runtime_request(rt,"  inspect  ","sector_0_0_bud_1","{\"mode\":\"deep\",\"enabled\":true}",&request,&e),&e);
    assert(strcmp(request.action,"inspect")==0);
    assert(request.target_kind==FPE_TARGET_BUD);
    assert(request.source_revision==1 && request.source_tick==10);
    assert(strcmp(request.payload_json,"{\"mode\":\"deep\",\"enabled\":true}")==0);
    fpe_action_request_destroy(&request);
    assert(fpe_runtime_request(rt,"explode","not-a-target","{}",&request,&e)==FPE_UNKNOWN_ID);
    assert(fpe_runtime_request(rt,"explode","sector_0_0","{bad}",&request,&e)==FPE_INVALID_REQUEST);

    /* Host time must survive a revision handoff even though scheduler entries restart. */
    memset(&batch,0,sizeof(batch));
    require_ok(fpe_runtime_step(rt,20,&batch,&e),&e);
    assert(!batch.repeated);
    fpe_update_batch_destroy(&batch);

    next=p;
    next.state_revision=2; next.state_tick=11;
    next.projection_fingerprint="1123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
    require_ok(fpe_runtime_accept(rt,&next,&changed,&e),&e);
    assert(changed);
    assert(fpe_runtime_step(rt,19,&batch,&e)==FPE_INVALID_TICK);
    require_ok(fpe_runtime_step(rt,20,&batch,&e),&e);
    assert(!batch.repeated && batch.update_count==4u);
    fpe_update_batch_destroy(&batch);
    require_ok(fpe_runtime_step(rt,20,&batch,&e),&e);
    assert(batch.repeated && batch.update_count==0u);
    fpe_update_batch_destroy(&batch);
    require_ok(fpe_runtime_checkpoint(rt,&checkpoint,&e),&e);
    require_ok(fpe_runtime_restore(checkpoint,&restored,&e),&e);
    assert(fpe_runtime_step(restored,19,&batch,&e)==FPE_INVALID_TICK);
    require_ok(fpe_runtime_step(restored,20,&batch,&e),&e);
    assert(batch.repeated);
    fpe_update_batch_destroy(&batch);
    fpe_checkpoint_destroy(checkpoint);
    fpe_runtime_destroy(restored);
    restored=NULL; checkpoint=NULL;

    require_ok(fpe_runtime_accept(rt,&next,&changed,&e),&e);
    assert(!changed); /* Identical same-revision delivery is a no-op. */

    {
        FPEProjection conflict=next;
        FPECluster changed_cluster=clusters[0];
        FPECluster local_clusters[4];
        memcpy(local_clusters,clusters,sizeof(clusters));
        changed_cluster.state.alert=0.7;
        local_clusters[0]=changed_cluster;
        conflict.clusters=local_clusters;
        assert(fpe_runtime_accept(rt,&conflict,&changed,&e)==FPE_REVISION_CONFLICT);
    }
    {
        FPEProjection stale=next;
        stale.state_revision=1;
        assert(fpe_runtime_accept(rt,&stale,&changed,&e)==FPE_STALE_REVISION);
    }
    {
        FPEProjection foreign=next;
        foreign.pixelgen_world_fingerprint="bbbbbb0123456789abcdef0123456789abcdef0123456789abcdef0123456789";
        assert(fpe_runtime_accept(rt,&foreign,&changed,&e)==FPE_FOREIGN_WORLD);
    }
    fpe_runtime_destroy(rt);
}

static void test_validation_and_input_ownership(void) {
    FPEProjection p=fixture(),bad;
    FPEError e;
    FPERuntime *rt=NULL;
    const FPEProjection *owned;
    char original_id[FPE_ID_CAPACITY];
    require_ok(fpe_runtime_create(&p,4,&rt,&e),&e);
    (void)snprintf(original_id,sizeof(original_id),"%s",clusters[0].id);
    memset(cluster_ids[0],0,sizeof(cluster_ids[0]));
    owned=fpe_runtime_projection(rt);
    assert(strcmp(owned->clusters[0].id,original_id)==0); /* Runtime owns a deep copy. */
    fpe_runtime_destroy(rt);

    bad=fixture();
    bad.summary.bud_count=15;
    assert(fpe_projection_validate(&bad,&e)==FPE_INVALID_PROJECTION);
    {
        FPECluster duplicate[4];
        bad=fixture();
        memcpy(duplicate,clusters,sizeof(duplicate));
        duplicate[1].sector_x=0; duplicate[1].sector_y=0;
        bad.clusters=duplicate;
        assert(fpe_projection_validate(&bad,&e)==FPE_INVALID_PROJECTION);
    }
}

static void test_large_world(void) {
    const uint32_t side=100u;
    const size_t count=(size_t)side*(size_t)side;
    FPECluster *large=(FPECluster *)calloc(count,sizeof(FPECluster));
    char (*cluster_names)[32]=(char (*)[32])calloc(count,sizeof(*cluster_names));
    char (*bud_names)[4][48]=(char (*)[4][48])calloc(count,sizeof(*bud_names));
    char (*seed_names)[4][48]=(char (*)[4][48])calloc(count,sizeof(*seed_names));
    FPEProjection p;
    FPERuntime *runtime=NULL;
    FPEPlan plan;
    FPEUpdateBatch batch;
    FPEError error;
    size_t i,j;
    assert(large!=NULL && cluster_names!=NULL && bud_names!=NULL && seed_names!=NULL);
    memset(&p,0,sizeof(p));
    for(i=0;i<count;++i) {
        const uint32_t x=(uint32_t)(i%side),y=(uint32_t)(i/side);
        (void)snprintf(cluster_names[i],sizeof(cluster_names[i]),"sector_%u_%u",x,y);
        large[i].id=cluster_names[i]; large[i].sector_x=x; large[i].sector_y=y;
        large[i].projection.cohesion=0.5; large[i].projection.breakup_resistance=0.5;
        large[i].projection.agitation=0.2; large[i].projection.collapse_bias=0.2;
        large[i].projection.damage_proxy=0.1; large[i].projection.update_rate=0.5;
        large[i].state.stability=0.8; large[i].state.alert=0.1;
        large[i].state.front_tension=0.1; large[i].state.front_activity=0.1;
        large[i].state.control_strength=1.0; large[i].state.front_status=FPE_FRONT_QUIET;
        for(j=0;j<4u;++j) {
            static const int offsets[4][2]={{-1,-1},{1,-1},{-1,1},{1,1}};
            (void)snprintf(bud_names[i][j],sizeof(bud_names[i][j]),"sector_%u_%u_bud_%u",x,y,(unsigned)j);
            (void)snprintf(seed_names[i][j],sizeof(seed_names[i][j]),"s_%u_%u_%u",x,y,(unsigned)j);
            large[i].buds[j].id=bud_names[i][j]; large[i].buds[j].index=(uint32_t)j;
            large[i].buds[j].offset_x=offsets[j][0]; large[i].buds[j].offset_z=offsets[j][1];
            large[i].buds[j].type=((i+j)%2u==0u?FPE_BUD_STRAIGHT:FPE_BUD_CURVED);
            large[i].buds[j].seed_key=seed_names[i][j];
        }
    }
    p.schema=FPE_PROJECTION_SCHEMA; p.mode="read_only_hierarchical_projection";
    p.projection_fingerprint=fp_a; p.pixelgen_world_fingerprint=fp_world;
    p.seed=7301; p.columns=side; p.rows=side; p.state_revision=1; p.state_tick=0;
    p.sector_spacing=12.0; p.local_bud_offset=2.2; p.clusters=large; p.cluster_count=count;
    p.summary.cluster_count=count; p.summary.bud_count=count*4u;
    p.summary.straight_bud_count=count*2u; p.summary.curved_bud_count=count*2u;
    require_ok(fpe_runtime_create(&p,8,&runtime,&error),&error);
    /* Input storage can be released immediately: the runtime owns its copy. */
    free(large); free(cluster_names); free(bud_names); free(seed_names);
    memset(&plan,0,sizeof(plan));
    require_ok(fpe_runtime_get_plan(runtime,&plan,&error),&error);
    assert(plan.item_count==count && plan.counts.cluster_proxies==count);
    fpe_plan_destroy(&plan);
    memset(&batch,0,sizeof(batch));
    require_ok(fpe_runtime_step(runtime,0,&batch,&error),&error);
    assert(batch.update_count==8u && batch.deferred_count==count-8u);
    fpe_update_batch_destroy(&batch);
    fpe_runtime_destroy(runtime);
}

int main(void) {
    test_projection_and_plan();
    test_view_normalization();
    test_scheduler_and_checkpoint();
    test_request_and_revision_handoff();
    test_validation_and_input_ownership();
    test_large_world();
    puts("FPE C 0.1.0: all tests passed");
    return 0;
}
