#include "fpe/fpe.h"
#include "fpe_internal.h"

#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FPE_GLYPH_COUNT 12u
#define FPE_MAX_JSON_DEPTH 32u

static const char *const k_glyphs[FPE_GLYPH_COUNT] = {
    "#", "%", "&", "8", "@", "+", "=", "-", ":", ".", "/", "\\"
};

typedef struct FPEEntry {
    size_t cluster_index;
    int64_t next_tick;
    int64_t last_tick;
    bool has_last;
    FPEPlanKind detail;
} FPEEntry;

struct FPERuntime {
    FPEProjection projection; /* Deep-owned strings and arrays. */
    size_t budget;
    FPEViewState view;
    FPEEntry *entries;
    size_t entry_count;
    int64_t last_tick;           /* Monotonic host/runtime clock. */
    int64_t scheduler_last_tick; /* Reset on projection handoff. */
};

struct FPECheckpoint {
    FPEProjection projection;
    size_t budget;
    FPEViewState view;
    FPEEntry *entries;
    size_t entry_count;
    int64_t last_tick;
    int64_t scheduler_last_tick;
};

static void set_error(FPEError *error, FPEErrorCode code, const char *message) {
    if (error == NULL) return;
    error->code = code;
    if (message == NULL) message = "";
    (void)snprintf(error->message, sizeof(error->message), "%s", message);
}

void fpe_error_clear(FPEError *error) {
    if (error != NULL) {
        error->code = FPE_OK;
        error->message[0] = '\0';
    }
}

const char *fpe_version(void) { return FPE_C_VERSION; }

const char *fpe_glyph(uint32_t index) {
    return index < FPE_GLYPH_COUNT ? k_glyphs[index] : "?";
}

const char *fpe_error_name(FPEErrorCode code) {
    switch (code) {
        case FPE_OK: return "OK";
        case FPE_INVALID_OPTIONS: return "INVALID_OPTIONS";
        case FPE_INVALID_PROJECTION: return "INVALID_PROJECTION";
        case FPE_FOREIGN_WORLD: return "FOREIGN_WORLD";
        case FPE_STALE_REVISION: return "STALE_REVISION";
        case FPE_REVISION_CONFLICT: return "REVISION_CONFLICT";
        case FPE_INVALID_VIEW: return "INVALID_VIEW";
        case FPE_UNKNOWN_ID: return "UNKNOWN_ID";
        case FPE_PARENT_COLLAPSED: return "PARENT_COLLAPSED";
        case FPE_INVALID_TICK: return "INVALID_TICK";
        case FPE_INVALID_REQUEST: return "INVALID_REQUEST";
        case FPE_INVALID_SNAPSHOT: return "INVALID_SNAPSHOT";
        default: return "UNKNOWN_ERROR";
    }
}

static bool safe_integer(int64_t value) {
    return value >= -FPE_MAX_SAFE_INTEGER && value <= FPE_MAX_SAFE_INTEGER;
}

static bool safe_clock(uint64_t value) {
    return value <= (uint64_t)FPE_MAX_SAFE_INTEGER;
}

static size_t bounded_length(const char *value, size_t limit) {
    size_t n=0;
    if(value==NULL) return limit+1u;
    while(n<=limit && value[n]!='\0') ++n;
    return n;
}

static bool text_ok(const char *value, size_t max_bytes) {
    return value != NULL && value[0] != '\0' && bounded_length(value,max_bytes) <= max_bytes;
}

static bool hex64_ok(const char *value) {
    size_t i;
    if (value == NULL || strlen(value) != 64u) return false;
    for (i = 0; i < 64u; ++i) {
        if (!((value[i] >= '0' && value[i] <= '9') ||
              (value[i] >= 'a' && value[i] <= 'f'))) return false;
    }
    return true;
}

static char *copy_string(const char *value) {
    size_t n;
    char *copy;
    if (value == NULL) return NULL;
    n = strlen(value);
    copy = (char *)malloc(n + 1u);
    if (copy != NULL) memcpy(copy, value, n + 1u);
    return copy;
}

static bool finite_range(double value, double low, double high) {
    return isfinite(value) && value >= low && value <= high;
}

static bool expected_bud_offset(uint32_t index, int32_t *x, int32_t *z) {
    static const int32_t offsets[4][2] = {{-1,-1},{1,-1},{-1,1},{1,1}};
    if (index >= 4u) return false;
    *x = offsets[index][0];
    *z = offsets[index][1];
    return true;
}

static bool validate_projection_inner(const FPEProjection *p, char *message, size_t cap) {
    size_t i, j, expected_count;
    uint64_t territories = 0, fronts = 0, straight = 0, curved = 0;
    unsigned char *seen_sectors = NULL;
#define INVALID_PROJECTION(msg) do { \
        (void)snprintf(message, cap, "%s", (msg)); \
        free(seen_sectors); \
        return false; \
    } while (0)
    if (p == NULL) INVALID_PROJECTION("projection is null");
    if (p->schema == NULL || strcmp(p->schema, FPE_PROJECTION_SCHEMA) != 0 ||
        p->mode == NULL || strcmp(p->mode, "read_only_hierarchical_projection") != 0)
        INVALID_PROJECTION("unsupported projection schema or mode");
    if (!hex64_ok(p->projection_fingerprint) || !hex64_ok(p->pixelgen_world_fingerprint))
        INVALID_PROJECTION("invalid projection/world fingerprint");
    if (!safe_integer(p->seed) || !safe_clock(p->state_revision) || !safe_clock(p->state_tick))
        INVALID_PROJECTION("invalid seed or source clock");
    if (p->columns == 0u || p->rows == 0u ||
        (size_t)p->columns > SIZE_MAX / (size_t)p->rows)
        INVALID_PROJECTION("invalid source dimensions");
    expected_count = (size_t)p->columns * (size_t)p->rows;
    if (p->cluster_count != expected_count || p->clusters == NULL)
        INVALID_PROJECTION("cluster count does not match dimensions");
    if (!finite_range(p->sector_spacing, 0.001, 1000000.0) ||
        !finite_range(p->local_bud_offset, 0.001, 1000000.0))
        INVALID_PROJECTION("invalid layout spacing");
    seen_sectors = (unsigned char *)calloc(expected_count, sizeof(unsigned char));
    if (seen_sectors == NULL) INVALID_PROJECTION("out of memory validating sector uniqueness");

    for (i = 0; i < p->cluster_count; ++i) {
        const FPECluster *c = &p->clusters[i];
        char expected_id[FPE_ID_CAPACITY];
        size_t sector_index;
        if (!text_ok(c->id, FPE_ID_CAPACITY - 1u) ||
            c->sector_x >= p->columns || c->sector_y >= p->rows)
            INVALID_PROJECTION("invalid cluster identity/sector");
        sector_index = (size_t)c->sector_y * (size_t)p->columns + (size_t)c->sector_x;
        if (seen_sectors[sector_index] != 0u)
            INVALID_PROJECTION("duplicate sector coordinate");
        seen_sectors[sector_index] = 1u;
        (void)snprintf(expected_id, sizeof(expected_id), "sector_%u_%u", c->sector_x, c->sector_y);
        if (strcmp(c->id, expected_id) != 0)
            INVALID_PROJECTION("noncanonical cluster id");
        if (!finite_range(c->projection.cohesion, 0, 1) ||
            !finite_range(c->projection.breakup_resistance, 0, 1) ||
            !finite_range(c->projection.agitation, 0, 1) ||
            !finite_range(c->projection.collapse_bias, 0, 1) ||
            !finite_range(c->projection.damage_proxy, 0, 1) ||
            !finite_range(c->projection.update_rate, 0, 1) ||
            !finite_range(c->state.stability, 0, 1) ||
            !finite_range(c->state.alert, 0, 1) ||
            !finite_range(c->state.front_tension, 0, 1) ||
            !finite_range(c->state.front_activity, 0, 1) ||
            !finite_range(c->state.control_strength, 0, 1.75) ||
            c->state.front_status < FPE_FRONT_QUIET || c->state.front_status > FPE_FRONT_VOLATILE)
            INVALID_PROJECTION("invalid cluster state/projection value");
        if (c->territory_id != NULL && !text_ok(c->territory_id, FPE_ID_CAPACITY - 1u))
            INVALID_PROJECTION("invalid territory id");
        if (c->territory_id != NULL) ++territories;
        if (c->front_count != 0u && c->front_ids == NULL)
            INVALID_PROJECTION("missing front id array");
        if (c->front_count != 0u) ++fronts;
        for (j = 0; j < c->front_count; ++j) {
            if (!text_ok(c->front_ids[j], FPE_ID_CAPACITY - 1u))
                INVALID_PROJECTION("invalid front id");
        }
        for (j = 0; j < FPE_BUDS_PER_CLUSTER; ++j) {
            const FPEBud *bud = &c->buds[j];
            char expected_bud_id[FPE_ID_CAPACITY];
            int32_t ox, oz;
            (void)expected_bud_offset((uint32_t)j, &ox, &oz);
            (void)snprintf(expected_bud_id, sizeof(expected_bud_id), "%s_bud_%u", c->id, (unsigned)j);
            if (!text_ok(bud->id, FPE_ID_CAPACITY - 1u) || strcmp(bud->id, expected_bud_id) != 0 ||
                bud->index != (uint32_t)j || bud->offset_x != ox || bud->offset_z != oz ||
                !text_ok(bud->seed_key, FPE_ID_CAPACITY - 1u) ||
                (bud->type != FPE_BUD_STRAIGHT && bud->type != FPE_BUD_CURVED))
                INVALID_PROJECTION("invalid bud identity/type/offset");
            if (bud->type == FPE_BUD_STRAIGHT) ++straight; else ++curved;
        }
    }
    if (p->summary.cluster_count != p->cluster_count ||
        p->summary.bud_count != (uint64_t)p->cluster_count * FPE_BUDS_PER_CLUSTER ||
        p->summary.territory_cluster_count != territories ||
        p->summary.front_cluster_count != fronts ||
        p->summary.straight_bud_count != straight ||
        p->summary.curved_bud_count != curved)
        INVALID_PROJECTION("projection summary does not match source data");
    free(seen_sectors);
#undef INVALID_PROJECTION
    return true;
}

FPEErrorCode fpe_projection_validate(const FPEProjection *projection, FPEError *error) {
    char message[FPE_ERROR_CAPACITY];
    fpe_error_clear(error);
    if (!validate_projection_inner(projection, message, sizeof(message))) {
        set_error(error, FPE_INVALID_PROJECTION, message);
        return FPE_INVALID_PROJECTION;
    }
    return FPE_OK;
}

static void projection_destroy(FPEProjection *p) {
    size_t i, j;
    if (p == NULL) return;
    for (i = 0; p->clusters != NULL && i < p->cluster_count; ++i) {
        FPECluster *c = (FPECluster *)&p->clusters[i];
        free((void *)c->id);
        free((void *)c->territory_id);
        if(c->front_ids!=NULL) {
            for (j = 0; j < c->front_count; ++j) free((void *)c->front_ids[j]);
        }
        free((void *)c->front_ids);
        for (j = 0; j < FPE_BUDS_PER_CLUSTER; ++j) {
            free((void *)c->buds[j].id);
            free((void *)c->buds[j].seed_key);
        }
    }
    free((void *)p->clusters);
    free((void *)p->schema);
    free((void *)p->mode);
    free((void *)p->projection_fingerprint);
    free((void *)p->pixelgen_world_fingerprint);
    free((void *)p->json_document);
    memset(p, 0, sizeof(*p));
}

static bool projection_clone(const FPEProjection *source, FPEProjection *out) {
    size_t i, j;
    FPEProjection copy;
    memset(&copy, 0, sizeof(copy));
    copy = *source;
    copy.schema = copy_string(source->schema);
    copy.mode = copy_string(source->mode);
    copy.projection_fingerprint = copy_string(source->projection_fingerprint);
    copy.pixelgen_world_fingerprint = copy_string(source->pixelgen_world_fingerprint);
    copy.json_document = NULL;
    if (source->json_document != NULL && source->json_document_length != 0u) {
        char *document = (char *)malloc(source->json_document_length + 1u);
        if (document != NULL) {
            memcpy(document, source->json_document, source->json_document_length);
            document[source->json_document_length] = '\\0';
            copy.json_document = document;
        }
    }
    copy.clusters = (FPECluster *)calloc(source->cluster_count, sizeof(FPECluster));
    if (copy.schema == NULL || copy.mode == NULL || copy.projection_fingerprint == NULL ||
        copy.pixelgen_world_fingerprint == NULL || copy.clusters == NULL ||
        (source->json_document != NULL && source->json_document_length != 0u && copy.json_document == NULL)) goto fail;
    for (i = 0; i < source->cluster_count; ++i) {
        const FPECluster *src = &source->clusters[i];
        FPECluster *dst = (FPECluster *)&copy.clusters[i];
        size_t bud_index;
        *dst = *src;
        /* Clear every borrowed pointer before cloning, so partial failure cleanup
           never frees memory owned by the caller. */
        dst->id = NULL;
        dst->territory_id = NULL;
        dst->front_ids = NULL;
        for(bud_index=0;bud_index<FPE_BUDS_PER_CLUSTER;++bud_index) {
            dst->buds[bud_index].id = NULL;
            dst->buds[bud_index].seed_key = NULL;
        }
        dst->id = copy_string(src->id);
        dst->territory_id = copy_string(src->territory_id);
        if (dst->id == NULL || (src->territory_id != NULL && dst->territory_id == NULL)) goto fail;
        if (src->front_count != 0u) {
            const char **fronts = (const char **)calloc(src->front_count, sizeof(char *));
            if (fronts == NULL) goto fail;
            dst->front_ids = fronts;
            for (j = 0; j < src->front_count; ++j) {
                fronts[j] = copy_string(src->front_ids[j]);
                if (fronts[j] == NULL) goto fail;
            }
        }
        for (j = 0; j < FPE_BUDS_PER_CLUSTER; ++j) {
            dst->buds[j].id = copy_string(src->buds[j].id);
            dst->buds[j].seed_key = copy_string(src->buds[j].seed_key);
            if (dst->buds[j].id == NULL || dst->buds[j].seed_key == NULL) goto fail;
        }
    }
    *out = copy;
    return true;
fail:
    projection_destroy(&copy);
    return false;
}

static bool string_equal(const char *a, const char *b) {
    if (a == NULL || b == NULL) return a == b;
    return strcmp(a, b) == 0;
}

static bool projection_equal(const FPEProjection *a, const FPEProjection *b) {
    size_t i, j;
    if (!string_equal(a->schema,b->schema) || !string_equal(a->mode,b->mode) ||
        !string_equal(a->projection_fingerprint,b->projection_fingerprint) ||
        !string_equal(a->pixelgen_world_fingerprint,b->pixelgen_world_fingerprint) ||
        a->seed!=b->seed || a->columns!=b->columns || a->rows!=b->rows ||
        a->state_revision!=b->state_revision || a->state_tick!=b->state_tick ||
        a->sector_spacing!=b->sector_spacing || a->local_bud_offset!=b->local_bud_offset ||
        a->cluster_count!=b->cluster_count ||
        memcmp(&a->summary,&b->summary,sizeof(a->summary))!=0) return false;
    for (i=0;i<a->cluster_count;++i) {
        const FPECluster *x=&a->clusters[i], *y=&b->clusters[i];
        if (!string_equal(x->id,y->id) || x->sector_x!=y->sector_x || x->sector_y!=y->sector_y ||
            x->projection.cohesion!=y->projection.cohesion ||
            x->projection.breakup_resistance!=y->projection.breakup_resistance ||
            x->projection.agitation!=y->projection.agitation ||
            x->projection.collapse_bias!=y->projection.collapse_bias ||
            x->projection.damage_proxy!=y->projection.damage_proxy ||
            x->projection.update_rate!=y->projection.update_rate ||
            x->state.stability!=y->state.stability || x->state.alert!=y->state.alert ||
            x->state.front_tension!=y->state.front_tension || x->state.front_activity!=y->state.front_activity ||
            x->state.control_strength!=y->state.control_strength || x->state.front_status!=y->state.front_status ||
            !string_equal(x->territory_id,y->territory_id) || x->front_count!=y->front_count) return false;
        for(j=0;j<x->front_count;++j) if(!string_equal(x->front_ids[j],y->front_ids[j])) return false;
        for(j=0;j<FPE_BUDS_PER_CLUSTER;++j) {
            const FPEBud *u=&x->buds[j], *v=&y->buds[j];
            if(!string_equal(u->id,v->id)||u->index!=v->index||u->offset_x!=v->offset_x||
               u->offset_z!=v->offset_z||u->type!=v->type||!string_equal(u->seed_key,v->seed_key)) return false;
        }
    }
    return true;
}

void fpe_view_state_destroy(FPEViewState *view) {
    size_t i;
    if (view == NULL) return;
    for (i=0;i<view->expanded_cluster_count;++i) free(view->expanded_clusters[i]);
    for (i=0;i<view->expanded_bud_count;++i) free(view->expanded_buds[i]);
    free(view->expanded_clusters);
    free(view->expanded_buds);
    memset(view,0,sizeof(*view));
}

static bool id_in_list(char *const *list, size_t count, const char *id) {
    size_t i;
    for(i=0;i<count;++i) if(strcmp(list[i],id)==0) return true;
    return false;
}

static bool cluster_exists(const FPEProjection *p, const char *id) {
    size_t i;
    for(i=0;i<p->cluster_count;++i) if(strcmp(p->clusters[i].id,id)==0) return true;
    return false;
}

static const FPECluster *find_cluster(const FPEProjection *p, const char *id) {
    size_t i;
    for(i=0;i<p->cluster_count;++i) if(strcmp(p->clusters[i].id,id)==0) return &p->clusters[i];
    return NULL;
}

static const FPEBud *find_bud(const FPEProjection *p, const char *id, const FPECluster **parent) {
    size_t i,j;
    for(i=0;i<p->cluster_count;++i) for(j=0;j<FPE_BUDS_PER_CLUSTER;++j) {
        if(strcmp(p->clusters[i].buds[j].id,id)==0) {
            if(parent!=NULL) *parent=&p->clusters[i];
            return &p->clusters[i].buds[j];
        }
    }
    return NULL;
}

static int string_ptr_compare(const void *a, const void *b) {
    const char *const *x=(const char *const *)a, *const *y=(const char *const *)b;
    return strcmp(*x,*y);
}

static FPEErrorCode normalize_view(const FPEProjection *p, const FPEViewState *input,
                                   FPEViewState *out, FPEError *error) {
    size_t i;
    FPEViewState result;
    memset(&result,0,sizeof(result));
    if(input!=NULL && ((input->expanded_cluster_count!=0u && input->expanded_clusters==NULL) ||
                       (input->expanded_bud_count!=0u && input->expanded_buds==NULL))) {
        set_error(error,FPE_INVALID_VIEW,"view arrays are missing"); return FPE_INVALID_VIEW;
    }
    if(input!=NULL && input->expanded_cluster_count!=0u) {
        result.expanded_clusters=(char **)calloc(input->expanded_cluster_count,sizeof(char *));
        if(result.expanded_clusters==NULL) goto oom;
        for(i=0;i<input->expanded_cluster_count;++i) {
            const char *id=input->expanded_clusters[i];
            if(id!=NULL && cluster_exists(p,id) && !id_in_list(result.expanded_clusters,result.expanded_cluster_count,id)) {
                result.expanded_clusters[result.expanded_cluster_count]=copy_string(id);
                if(result.expanded_clusters[result.expanded_cluster_count]==NULL) goto oom;
                ++result.expanded_cluster_count;
            }
        }
        qsort(result.expanded_clusters,result.expanded_cluster_count,sizeof(char *),string_ptr_compare);
    }
    if(input!=NULL && input->expanded_bud_count!=0u) {
        result.expanded_buds=(char **)calloc(input->expanded_bud_count,sizeof(char *));
        if(result.expanded_buds==NULL) goto oom;
        for(i=0;i<input->expanded_bud_count;++i) {
            const FPECluster *parent=NULL;
            const char *id=input->expanded_buds[i];
            if(id!=NULL && find_bud(p,id,&parent)!=NULL &&
               id_in_list(result.expanded_clusters,result.expanded_cluster_count,parent->id) &&
               !id_in_list(result.expanded_buds,result.expanded_bud_count,id)) {
                result.expanded_buds[result.expanded_bud_count]=copy_string(id);
                if(result.expanded_buds[result.expanded_bud_count]==NULL) goto oom;
                ++result.expanded_bud_count;
            }
        }
        qsort(result.expanded_buds,result.expanded_bud_count,sizeof(char *),string_ptr_compare);
    }
    *out=result;
    return FPE_OK;
oom:
    fpe_view_state_destroy(&result);
    set_error(error,FPE_INVALID_VIEW,"out of memory normalizing view");
    return FPE_INVALID_VIEW;
}

static bool view_has_cluster(const FPEViewState *view,const char *id) {
    return id_in_list(view->expanded_clusters,view->expanded_cluster_count,id);
}
static bool view_has_bud(const FPEViewState *view,const char *id) {
    return id_in_list(view->expanded_buds,view->expanded_bud_count,id);
}

static uint32_t hash32(const char *text) {
    const unsigned char *p=(const unsigned char *)text;
    uint32_t h=2166136261u;
    while(*p!=0u) { h^=(uint32_t)*p++; h*=16777619u; }
    return h;
}

static double rand01(const char *key) { return (double)(hash32(key)%1000000u)/1000000.0; }

static bool make_key(char *out,size_t cap,const char *base,const char *suffix) {
    int n=snprintf(out,cap,"%s:%s",base,suffix);
    return n>=0 && (size_t)n<cap;
}

static void sector_center(const FPEProjection *p,const FPECluster *c,double *x,double *y,double *z) {
    *x=((double)c->sector_x-((double)p->columns-1.0)/2.0)*p->sector_spacing;
    *y=3.0;
    *z=((double)c->sector_y-((double)p->rows-1.0)/2.0)*p->sector_spacing;
}

static bool geometry_for_bud(const FPEProjection *p,const FPECluster *cluster,const FPEBud *bud,
                             FPEPlanItem *item) {
    const size_t n=bud->type==FPE_BUD_STRAIGHT?8u:14u;
    const double size=3.2, half=size/2.0;
    char key[FPE_ID_CAPACITY+24u];
    double cx,cy,cz;
    size_t i,j;
    sector_center(p,cluster,&cx,&cy,&cz);
    if(!make_key(key,sizeof(key),bud->seed_key,"height")) return false;
    cx+=(double)bud->offset_x*p->local_bud_offset;
    cy=3.0+rand01(key)*1.8;
    cz+=(double)bud->offset_z*p->local_bud_offset;
    item->center_x=cx; item->center_y=cy; item->center_z=cz;
    item->nodes=(FPEGeometryNode *)calloc(n,sizeof(FPEGeometryNode));
    if(item->nodes==NULL) return false;
    item->node_count=n;
    if(bud->type==FPE_BUD_STRAIGHT) {
        size_t index=0;
        for(i=0;i<2u;++i) for(j=0;j<2u;++j) {
            size_t k;
            for(k=0;k<2u;++k) {
                item->nodes[index].x=cx+(i?half:-half);
                item->nodes[index].y=cy+(j?half:-half);
                item->nodes[index].z=cz+(k?half:-half);
                ++index;
            }
        }
        item->edges=(FPEGeometryEdge *)calloc(12u,sizeof(FPEGeometryEdge));
        if(item->edges==NULL) return false;
        for(i=0;i<n;++i) for(j=i+1u;j<n;++j) {
            const FPEGeometryNode *a=&item->nodes[i],*b=&item->nodes[j];
            unsigned diff=(unsigned)(a->x!=b->x)+(unsigned)(a->y!=b->y)+(unsigned)(a->z!=b->z);
            if(diff==1u) {
                FPEGeometryEdge *e=&item->edges[item->edge_count++];
                e->from=(uint32_t)i; e->to=(uint32_t)j; e->weight=0.0;
            }
        }
    } else {
        const double pi=3.14159265358979323846;
        const double golden=pi*(3.0-sqrt(5.0));
        const double radius=size/1.8;
        bool seen[14][14]={{false}};
        double distances[14][14];
        item->edges=(FPEGeometryEdge *)calloc(42u,sizeof(FPEGeometryEdge));
        if(item->edges==NULL) return false;
        for(i=0;i<n;++i) {
            const double y=1.0-((double)i/((double)n-1.0))*2.0;
            const double rr=sqrt(fmax(0.0,1.0-y*y));
            const double t=golden*(double)i;
            item->nodes[i].x=cx+cos(t)*rr*radius;
            item->nodes[i].y=cy+y*radius*0.8+size*0.35;
            item->nodes[i].z=cz+sin(t)*rr*radius;
        }
        for(i=0;i<n;++i) for(j=0;j<n;++j) {
            const FPEGeometryNode *a=&item->nodes[i],*b=&item->nodes[j];
            const double dx=a->x-b->x,dy=a->y-b->y,dz=a->z-b->z;
            distances[i][j]=i==j?HUGE_VAL:sqrt(dx*dx+dy*dy+dz*dz);
        }
        for(i=0;i<n;++i) {
            size_t order[13],count=0,k;
            for(j=0;j<n;++j) if(j!=i) {
                size_t pos=count;
                while(pos>0u && distances[i][j]<distances[i][order[pos-1u]]) {
                    order[pos]=order[pos-1u]; --pos;
                }
                order[pos]=j; ++count;
            }
            for(k=0;k<3u;++k) {
                const size_t other=order[k],lo=i<other?i:other,hi=i<other?other:i;
                if(!seen[lo][hi]) {
                    char edge_key[64];
                    double weight;
                    (void)snprintf(edge_key,sizeof(edge_key),"edge:%u_%u",(unsigned)lo,(unsigned)hi);
                    if(!make_key(key,sizeof(key),bud->seed_key,edge_key)) return false;
                    weight=0.35+rand01(key)*0.25;
                    seen[lo][hi]=true;
                    item->edges[item->edge_count].from=(uint32_t)i;
                    item->edges[item->edge_count].to=(uint32_t)other;
                    item->edges[item->edge_count].weight=weight;
                    ++item->edge_count;
                }
            }
        }
    }
    for(i=0;i<n;++i) {
        char suffix[64];
        item->nodes[i].random_value=0.0;
        item->nodes[i].phase=0.0;
        item->nodes[i].glyph_index=0u;
        (void)snprintf(suffix,sizeof(suffix),"node:%u:rnd",(unsigned)i);
        if(!make_key(key,sizeof(key),bud->seed_key,suffix)) return false;
        item->nodes[i].random_value=rand01(key);
        (void)snprintf(suffix,sizeof(suffix),"node:%u:phase",(unsigned)i);
        if(!make_key(key,sizeof(key),bud->seed_key,suffix)) return false;
        item->nodes[i].phase=rand01(key)*2.0*3.14159265358979323846;
        (void)snprintf(suffix,sizeof(suffix),"node:%u:glyph",(unsigned)i);
        if(!make_key(key,sizeof(key),bud->seed_key,suffix)) return false;
        item->nodes[i].glyph_index=(uint32_t)floor(rand01(key)*(double)FPE_GLYPH_COUNT);
    }
    item->kind=FPE_PLAN_GEOMETRY;
    return true;
}

static void plan_item_destroy(FPEPlanItem *item) {
    free(item->nodes); free(item->edges); memset(item,0,sizeof(*item));
}

void fpe_plan_destroy(FPEPlan *plan) {
    size_t i;
    if(plan==NULL) return;
    for(i=0;i<plan->item_count;++i) plan_item_destroy(&plan->items[i]);
    free(plan->items);
    fpe_view_state_destroy(&plan->state);
    memset(plan,0,sizeof(*plan));
}

static FPEErrorCode build_plan(const FPEProjection *p,const FPEViewState *view,FPEPlan *out,FPEError *error) {
    size_t i,j,capacity=0;
    FPEPlan plan;
    memset(&plan,0,sizeof(plan));
    if(p->cluster_count>SIZE_MAX/FPE_BUDS_PER_CLUSTER) {
        set_error(error,FPE_INVALID_VIEW,"plan size overflow"); return FPE_INVALID_VIEW;
    }
    capacity=p->cluster_count*FPE_BUDS_PER_CLUSTER;
    plan.items=(FPEPlanItem *)calloc(capacity,sizeof(FPEPlanItem));
    if(plan.items==NULL) { set_error(error,FPE_INVALID_VIEW,"out of memory building plan"); return FPE_INVALID_VIEW; }
    if(normalize_view(p,view,&plan.state,error)!=FPE_OK) { free(plan.items); return FPE_INVALID_VIEW; }
    for(i=0;i<p->cluster_count;++i) {
        const FPECluster *c=&p->clusters[i];
        double cx,cy,cz;
        FPEPlanItem *item;
        sector_center(p,c,&cx,&cy,&cz);
        if(!view_has_cluster(&plan.state,c->id)) {
            item=&plan.items[plan.item_count++];
            item->kind=FPE_PLAN_CLUSTER_PROXY;
            (void)snprintf(item->id,sizeof(item->id),"%s",c->id);
            (void)snprintf(item->cluster_id,sizeof(item->cluster_id),"%s",c->id);
            item->center_x=cx; item->center_y=cy; item->center_z=cz;
            ++plan.counts.cluster_proxies;
            continue;
        }
        for(j=0;j<FPE_BUDS_PER_CLUSTER;++j) {
            const FPEBud *b=&c->buds[j];
            double bx=cx+(double)b->offset_x*p->local_bud_offset;
            double by=3.0, bz=cz+(double)b->offset_z*p->local_bud_offset;
            char key[FPE_ID_CAPACITY+24u];
            item=&plan.items[plan.item_count++];
            (void)snprintf(item->id,sizeof(item->id),"%s",b->id);
            (void)snprintf(item->cluster_id,sizeof(item->cluster_id),"%s",c->id);
            if(!make_key(key,sizeof(key),b->seed_key,"height")) goto plan_oom;
            by+=rand01(key)*1.8;
            if(!view_has_bud(&plan.state,b->id)) {
                item->kind=FPE_PLAN_BUD_PROXY;
                item->center_x=bx; item->center_y=by; item->center_z=bz;
                ++plan.counts.bud_proxies;
            } else {
                if(!geometry_for_bud(p,c,b,item)) goto plan_oom;
                ++plan.counts.geometries;
                plan.counts.nodes+=item->node_count;
                plan.counts.edges+=item->edge_count;
            }
        }
    }
    *out=plan;
    return FPE_OK;
plan_oom:
    fpe_plan_destroy(&plan);
    set_error(error,FPE_INVALID_VIEW,"out of memory building geometry plan");
    return FPE_INVALID_VIEW;
}

static bool entries_create(const FPEProjection *p,FPEEntry **out_entries,size_t *out_count) {
    size_t i,j;
    FPEEntry *entries=(FPEEntry *)calloc(p->cluster_count,sizeof(FPEEntry));
    if(entries==NULL) return false;
    for(i=0;i<p->cluster_count;++i) entries[i].cluster_index=i;
    /* Match JavaScript's id sort explicitly, independent of projection order. */
    for(i=1;i<p->cluster_count;++i) {
        FPEEntry value=entries[i];
        j=i;
        while(j>0u && strcmp(p->clusters[value.cluster_index].id,
                             p->clusters[entries[j-1u].cluster_index].id)<0) {
            entries[j]=entries[j-1u]; --j;
        }
        entries[j]=value;
    }
    for(i=0;i<p->cluster_count;++i) {
        entries[i].next_tick=0;
        entries[i].last_tick=0;
        entries[i].has_last=false;
        entries[i].detail=FPE_PLAN_CLUSTER_PROXY;
    }
    *out_entries=entries; *out_count=p->cluster_count;
    return true;
}

FPEErrorCode fpe_runtime_create(const FPEProjection *projection,size_t budget,
                                FPERuntime **out_runtime,FPEError *error) {
    FPERuntime *runtime;
    FPEErrorCode code;
    fpe_error_clear(error);
    if(out_runtime==NULL || budget==0u) {
        set_error(error,FPE_INVALID_OPTIONS,"runtime output and positive scheduler budget are required");
        return FPE_INVALID_OPTIONS;
    }
    *out_runtime=NULL;
    code=fpe_projection_validate(projection,error);
    if(code!=FPE_OK) return code;
    runtime=(FPERuntime *)calloc(1,sizeof(FPERuntime));
    if(runtime==NULL) { set_error(error,FPE_INVALID_OPTIONS,"out of memory creating runtime"); return FPE_INVALID_OPTIONS; }
    if(!projection_clone(projection,&runtime->projection) ||
       !entries_create(&runtime->projection,&runtime->entries,&runtime->entry_count)) {
        projection_destroy(&runtime->projection); free(runtime);
        set_error(error,FPE_INVALID_OPTIONS,"out of memory copying projection/runtime state");
        return FPE_INVALID_OPTIONS;
    }
    runtime->budget=budget;
    runtime->last_tick=-1;
    runtime->scheduler_last_tick=-1;
    *out_runtime=runtime;
    return FPE_OK;
}

void fpe_runtime_destroy(FPERuntime *runtime) {
    if(runtime==NULL) return;
    projection_destroy(&runtime->projection);
    fpe_view_state_destroy(&runtime->view);
    free(runtime->entries);
    free(runtime);
}

const FPEProjection *fpe_runtime_projection(const FPERuntime *runtime) {
    return runtime==NULL?NULL:&runtime->projection;
}

FPEErrorCode fpe_runtime_accept(FPERuntime *runtime,const FPEProjection *incoming,
                                bool *changed,FPEError *error) {
    FPEProjection next_projection;
    FPEViewState next_view;
    FPEEntry *next_entries=NULL;
    size_t next_count=0;
    FPEPlan preflight;
    const FPEProjection *current;
    FPEErrorCode code;
    memset(&next_projection,0,sizeof(next_projection));
    memset(&next_view,0,sizeof(next_view));
    memset(&preflight,0,sizeof(preflight));
    fpe_error_clear(error);
    if(runtime==NULL || changed==NULL) {
        set_error(error,FPE_INVALID_OPTIONS,"runtime and changed output are required"); return FPE_INVALID_OPTIONS;
    }
    *changed=false;
    code=fpe_projection_validate(incoming,error);
    if(code!=FPE_OK) return code;
    current=&runtime->projection;
    if(current->seed!=incoming->seed ||
       current->columns!=incoming->columns || current->rows!=incoming->rows ||
       !string_equal(current->pixelgen_world_fingerprint,incoming->pixelgen_world_fingerprint)) {
        set_error(error,FPE_FOREIGN_WORLD,"projection belongs to another world; create a new runtime");
        return FPE_FOREIGN_WORLD;
    }
    if(incoming->state_revision<current->state_revision || incoming->state_tick<current->state_tick) {
        set_error(error,FPE_STALE_REVISION,"projection revision or source tick moved backward");
        return FPE_STALE_REVISION;
    }
    if(incoming->state_revision==current->state_revision) {
        if(!projection_equal(current,incoming)) {
            set_error(error,FPE_REVISION_CONFLICT,"different projection content at the same revision");
            return FPE_REVISION_CONFLICT;
        }
        return FPE_OK;
    }
    if(!projection_clone(incoming,&next_projection)) {
        set_error(error,FPE_INVALID_PROJECTION,"out of memory copying incoming projection"); return FPE_INVALID_PROJECTION;
    }
    code=normalize_view(&next_projection,&runtime->view,&next_view,error);
    if(code!=FPE_OK) { projection_destroy(&next_projection); return code; }
    code=build_plan(&next_projection,&next_view,&preflight,error);
    if(code!=FPE_OK) {
        projection_destroy(&next_projection); fpe_view_state_destroy(&next_view); return FPE_INVALID_PROJECTION;
    }
    fpe_plan_destroy(&preflight);
    if(!entries_create(&next_projection,&next_entries,&next_count)) {
        projection_destroy(&next_projection); fpe_view_state_destroy(&next_view);
        set_error(error,FPE_INVALID_PROJECTION,"out of memory resetting scheduler for new projection");
        return FPE_INVALID_PROJECTION;
    }
    projection_destroy(&runtime->projection);
    fpe_view_state_destroy(&runtime->view);
    free(runtime->entries);
    runtime->projection=next_projection;
    runtime->view=next_view;
    runtime->entries=next_entries;
    runtime->entry_count=next_count;
    /* Preserve the host clock; only the new revision's scheduler restarts. */
    runtime->scheduler_last_tick=-1;
    *changed=true;
    return FPE_OK;
}

FPEErrorCode fpe_runtime_set_view(FPERuntime *runtime,const FPEViewState *view,
                                  FPEViewState *normalized,FPEError *error) {
    FPEViewState next;
    FPEErrorCode code;
    memset(&next,0,sizeof(next));
    fpe_error_clear(error);
    size_t i;
    if(runtime==NULL || normalized==NULL) { set_error(error,FPE_INVALID_OPTIONS,"runtime and output view are required"); return FPE_INVALID_OPTIONS; }
    if(view==NULL || (view->expanded_cluster_count!=0u && view->expanded_clusters==NULL) ||
       (view->expanded_bud_count!=0u && view->expanded_buds==NULL)) {
        set_error(error,FPE_INVALID_VIEW,"view requires two arrays of string IDs"); return FPE_INVALID_VIEW;
    }
    for(i=0;i<view->expanded_cluster_count;++i) if(!text_ok(view->expanded_clusters[i],FPE_ID_CAPACITY-1u)) {
        set_error(error,FPE_INVALID_VIEW,"expanded cluster IDs must be non-empty strings"); return FPE_INVALID_VIEW;
    }
    for(i=0;i<view->expanded_bud_count;++i) if(!text_ok(view->expanded_buds[i],FPE_ID_CAPACITY-1u)) {
        set_error(error,FPE_INVALID_VIEW,"expanded bud IDs must be non-empty strings"); return FPE_INVALID_VIEW;
    }
    code=normalize_view(&runtime->projection,view,&next,error);
    if(code!=FPE_OK) return code;
    fpe_view_state_destroy(&runtime->view);
    runtime->view=next;
    code=normalize_view(&runtime->projection,&runtime->view,normalized,error);
    return code;
}

static bool remove_view_id(char ***list,size_t *count,const char *id) {
    size_t i;
    for(i=0;i<*count;++i) if(strcmp((*list)[i],id)==0) {
        free((*list)[i]);
        if(i+1u<*count) memmove(&(*list)[i],&(*list)[i+1u],(*count-i-1u)*sizeof(char *));
        --(*count);
        return true;
    }
    return false;
}

static bool append_view_id(char ***list,size_t *count,const char *id) {
    char **next=(char **)realloc(*list,(*count+1u)*sizeof(char *));
    if(next==NULL) return false;
    *list=next;
    next[*count]=copy_string(id);
    if(next[*count]==NULL) return false;
    ++(*count);
    return true;
}

FPEErrorCode fpe_runtime_toggle_cluster(FPERuntime *runtime,const char *cluster_id,
                                        FPEViewState *result,FPEError *error) {
    FPEViewState next;
    const FPECluster *cluster;
    size_t i;
    fpe_error_clear(error);
    if(runtime==NULL || result==NULL) { set_error(error,FPE_INVALID_OPTIONS,"runtime and result view are required"); return FPE_INVALID_OPTIONS; }
    cluster=find_cluster(&runtime->projection,cluster_id==NULL?"":cluster_id);
    if(cluster==NULL) { set_error(error,FPE_UNKNOWN_ID,"unknown cluster id"); return FPE_UNKNOWN_ID; }
    if(normalize_view(&runtime->projection,&runtime->view,&next,error)!=FPE_OK) return FPE_INVALID_VIEW;
    if(!remove_view_id(&next.expanded_clusters,&next.expanded_cluster_count,cluster_id)) {
        if(!append_view_id(&next.expanded_clusters,&next.expanded_cluster_count,cluster_id)) goto oom;
    } else {
        for(i=0;i<FPE_BUDS_PER_CLUSTER;++i)
            (void)remove_view_id(&next.expanded_buds,&next.expanded_bud_count,cluster->buds[i].id);
    }
    qsort(next.expanded_clusters,next.expanded_cluster_count,sizeof(char *),string_ptr_compare);
    qsort(next.expanded_buds,next.expanded_bud_count,sizeof(char *),string_ptr_compare);
    fpe_view_state_destroy(&runtime->view);
    runtime->view=next;
    return fpe_runtime_get_view(runtime,result,error);
oom:
    fpe_view_state_destroy(&next);
    set_error(error,FPE_INVALID_VIEW,"out of memory toggling cluster"); return FPE_INVALID_VIEW;
}

FPEErrorCode fpe_runtime_toggle_bud(FPERuntime *runtime,const char *bud_id,
                                    FPEViewState *result,FPEError *error) {
    const FPECluster *parent=NULL;
    FPEViewState next;
    fpe_error_clear(error);
    if(runtime==NULL || result==NULL) { set_error(error,FPE_INVALID_OPTIONS,"runtime and result view are required"); return FPE_INVALID_OPTIONS; }
    if(find_bud(&runtime->projection,bud_id==NULL?"":bud_id,&parent)==NULL) {
        set_error(error,FPE_UNKNOWN_ID,"unknown bud id"); return FPE_UNKNOWN_ID;
    }
    if(!view_has_cluster(&runtime->view,parent->id)) {
        set_error(error,FPE_PARENT_COLLAPSED,"expand the parent cluster before its bud"); return FPE_PARENT_COLLAPSED;
    }
    if(normalize_view(&runtime->projection,&runtime->view,&next,error)!=FPE_OK) return FPE_INVALID_VIEW;
    if(!remove_view_id(&next.expanded_buds,&next.expanded_bud_count,bud_id)) {
        if(!append_view_id(&next.expanded_buds,&next.expanded_bud_count,bud_id)) {
            fpe_view_state_destroy(&next); set_error(error,FPE_INVALID_VIEW,"out of memory toggling bud"); return FPE_INVALID_VIEW;
        }
    }
    qsort(next.expanded_buds,next.expanded_bud_count,sizeof(char *),string_ptr_compare);
    fpe_view_state_destroy(&runtime->view);
    runtime->view=next;
    return fpe_runtime_get_view(runtime,result,error);
}

FPEErrorCode fpe_runtime_get_view(const FPERuntime *runtime,FPEViewState *out_view,FPEError *error) {
    fpe_error_clear(error);
    if(runtime==NULL || out_view==NULL) { set_error(error,FPE_INVALID_OPTIONS,"runtime and view output are required"); return FPE_INVALID_OPTIONS; }
    memset(out_view,0,sizeof(*out_view));
    if(normalize_view(&runtime->projection,&runtime->view,out_view,error)!=FPE_OK) return FPE_INVALID_VIEW;
    return FPE_OK;
}

FPEErrorCode fpe_runtime_get_plan(const FPERuntime *runtime,FPEPlan *out_plan,FPEError *error) {
    fpe_error_clear(error);
    if(runtime==NULL || out_plan==NULL) { set_error(error,FPE_INVALID_OPTIONS,"runtime and plan output are required"); return FPE_INVALID_OPTIONS; }
    memset(out_plan,0,sizeof(*out_plan));
    return build_plan(&runtime->projection,&runtime->view,out_plan,error);
}

static FPEPlanKind detail_for_cluster(const FPECluster *cluster,const FPEViewState *view) {
    size_t i;
    if(!view_has_cluster(view,cluster->id)) return FPE_PLAN_CLUSTER_PROXY;
    for(i=0;i<FPE_BUDS_PER_CLUSTER;++i) if(view_has_bud(view,cluster->buds[i].id)) return FPE_PLAN_GEOMETRY;
    return FPE_PLAN_BUD_PROXY;
}

static bool entry_before(const FPEProjection *p,const FPEEntry *a,const FPEEntry *b) {
    if(a->next_tick!=b->next_tick) return a->next_tick<b->next_tick;
    return strcmp(p->clusters[a->cluster_index].id,p->clusters[b->cluster_index].id)<0;
}

FPEErrorCode fpe_runtime_step(FPERuntime *runtime,int64_t tick,FPEUpdateBatch *out_batch,FPEError *error) {
    FPEEntry *working=NULL;
    size_t *due=NULL,due_count=0,i,emit_count;
    FPEUpdateBatch batch;
    memset(&batch,0,sizeof(batch));
    fpe_error_clear(error);
    if(runtime==NULL || out_batch==NULL) { set_error(error,FPE_INVALID_OPTIONS,"runtime and update batch are required"); return FPE_INVALID_OPTIONS; }
    memset(out_batch,0,sizeof(*out_batch));
    if(tick<0 || tick>INT64_MAX-16 || tick<runtime->last_tick) {
        set_error(error,FPE_INVALID_TICK,"host runtime tick must be monotonic and within safe range"); return FPE_INVALID_TICK;
    }
    batch.tick=tick;
    if(tick==runtime->scheduler_last_tick) { batch.repeated=true; *out_batch=batch; return FPE_OK; }
    working=(FPEEntry *)malloc(runtime->entry_count*sizeof(FPEEntry));
    due=(size_t *)malloc(runtime->entry_count*sizeof(size_t));
    if((runtime->entry_count!=0u) && (working==NULL || due==NULL)) goto oom;
    if(runtime->entry_count!=0u) memcpy(working,runtime->entries,runtime->entry_count*sizeof(FPEEntry));
    for(i=0;i<runtime->entry_count;++i) {
        FPEEntry *e=&working[i];
        const FPECluster *c=&runtime->projection.clusters[e->cluster_index];
        FPEPlanKind detail=detail_for_cluster(c,&runtime->view);
        if(detail!=e->detail) { if(e->next_tick>tick) e->next_tick=tick; e->detail=detail; }
        if(e->next_tick<=tick) {
            size_t pos=due_count;
            while(pos>0u && entry_before(&runtime->projection,e,&working[due[pos-1u]])) {
                due[pos]=due[pos-1u]; --pos;
            }
            due[pos]=i; ++due_count;
        }
    }
    emit_count=due_count<runtime->budget?due_count:runtime->budget;
    if(emit_count!=0u) {
        batch.updates=(FPEUpdate *)calloc(emit_count,sizeof(FPEUpdate));
        if(batch.updates==NULL) goto oom;
    }
    batch.update_count=emit_count;
    batch.deferred_count=due_count-emit_count;
    for(i=0;i<emit_count;++i) {
        FPEEntry *e=&working[due[i]];
        const FPECluster *c=&runtime->projection.clusters[e->cluster_index];
        const double rate=c->projection.update_rate;
        uint32_t base=rate>=0.66?1u:(rate>=0.33?2u:4u);
        uint32_t multiplier=e->detail==FPE_PLAN_CLUSTER_PROXY?4u:(e->detail==FPE_PLAN_BUD_PROXY?2u:1u);
        uint32_t period=base*multiplier;
        int64_t elapsed=e->has_last?tick-e->last_tick:0;
        (void)snprintf(batch.updates[i].cluster_id,sizeof(batch.updates[i].cluster_id),"%s",c->id);
        batch.updates[i].tick=tick;
        batch.updates[i].elapsed=elapsed;
        batch.updates[i].period=period;
        batch.updates[i].detail=e->detail;
        e->has_last=true; e->last_tick=tick; e->next_tick=tick+(int64_t)period;
    }
    if(runtime->entry_count!=0u) memcpy(runtime->entries,working,runtime->entry_count*sizeof(FPEEntry));
    runtime->last_tick=tick;
    runtime->scheduler_last_tick=tick;
    free(working); free(due);
    *out_batch=batch;
    return FPE_OK;
oom:
    free(working); free(due); free(batch.updates);
    set_error(error,FPE_INVALID_TICK,"out of memory preparing scheduler batch");
    return FPE_INVALID_TICK;
}

/* Minimal strict JSON validator for detached action payload objects. */
typedef struct JSONCursor { const char *p; unsigned depth; } JSONCursor;
static void json_ws(JSONCursor *c) { while(*c->p==' '||*c->p=='\n'||*c->p=='\r'||*c->p=='\t') ++c->p; }
static bool json_string(JSONCursor *c) {
    if(*c->p!='"') return false;
    ++c->p;
    while(*c->p!='\0') {
        unsigned char ch=(unsigned char)*c->p++;
        if(ch=='"') return true;
        if(ch<0x20u) return false;
        if(ch=='\\') {
            char esc;
            unsigned k;
            if(*c->p=='\0') return false;
            esc=*c->p++;
            if(esc=='"'||esc=='\\'||esc=='/'||esc=='b'||esc=='f'||esc=='n'||esc=='r'||esc=='t') continue;
            if(esc=='u') {
                for(k=0;k<4u;++k) {
                    if(*c->p=='\0' || !isxdigit((unsigned char)*c->p)) return false;
                    ++c->p;
                }
                continue;
            }
            return false;
        }
    }
    return false;
}
static bool json_value(JSONCursor *c);
static bool json_array(JSONCursor *c) {
    if(*c->p++!='[') return false;
    json_ws(c); if(*c->p==']') { ++c->p; return true; }
    for(;;) {
        if(!json_value(c)) return false;
        json_ws(c);
        if(*c->p==']') { ++c->p; return true; }
        if(*c->p++!=',') return false;
        json_ws(c);
    }
}
static bool json_object(JSONCursor *c) {
    if(*c->p++!='{') return false;
    json_ws(c); if(*c->p=='}') { ++c->p; return true; }
    for(;;) {
        if(!json_string(c)) return false;
        json_ws(c); if(*c->p++!=':') return false;
        json_ws(c); if(!json_value(c)) return false;
        json_ws(c);
        if(*c->p=='}') { ++c->p; return true; }
        if(*c->p++!=',') return false;
        json_ws(c);
    }
}
static bool json_number(JSONCursor *c) {
    const char *start=c->p; char *end=NULL; double value;
    if(*c->p=='-') ++c->p;
    if(*c->p=='0') ++c->p;
    else { if(*c->p<'1'||*c->p>'9') return false; while(*c->p>='0'&&*c->p<='9') ++c->p; }
    if(*c->p=='.') { ++c->p; if(*c->p<'0'||*c->p>'9') return false; while(*c->p>='0'&&*c->p<='9') ++c->p; }
    if(*c->p=='e'||*c->p=='E') { ++c->p; if(*c->p=='+'||*c->p=='-') ++c->p; if(*c->p<'0'||*c->p>'9') return false; while(*c->p>='0'&&*c->p<='9') ++c->p; }
    value=strtod(start,&end);
    return end==c->p && isfinite(value);
}
static bool json_value(JSONCursor *c) {
    if(c->depth++>FPE_MAX_JSON_DEPTH) return false;
    json_ws(c);
    if(*c->p=='{') { if(!json_object(c)) return false; }
    else if(*c->p=='[') { if(!json_array(c)) return false; }
    else if(*c->p=='"') { if(!json_string(c)) return false; }
    else if(strncmp(c->p,"true",4u)==0) c->p+=4;
    else if(strncmp(c->p,"false",5u)==0) c->p+=5;
    else if(strncmp(c->p,"null",4u)==0) c->p+=4;
    else if(!json_number(c)) return false;
    --c->depth;
    return true;
}
static bool valid_payload_object(const char *json) {
    JSONCursor c;
    if(json==NULL || strlen(json)>FPE_MAX_PAYLOAD_BYTES) return false;
    c.p=json; c.depth=0; json_ws(&c);
    if(*c.p!='{' || !json_object(&c)) return false;
    json_ws(&c);
    return *c.p=='\0';
}

void fpe_action_request_destroy(FPEActionRequest *request) {
    if(request==NULL) return;
    free(request->payload_json);
    memset(request,0,sizeof(*request));
}

FPEErrorCode fpe_runtime_request(const FPERuntime *runtime,const char *action,
                                 const char *target_id,const char *payload_json,
                                 FPEActionRequest *out_request,FPEError *error) {
    size_t n,start=0,end;
    const FPECluster *parent=NULL;
    FPEActionRequest request;
    fpe_error_clear(error);
    if(runtime==NULL || out_request==NULL || action==NULL || target_id==NULL) {
        set_error(error,FPE_INVALID_REQUEST,"runtime, action, target and output are required"); return FPE_INVALID_REQUEST;
    }
    memset(&request,0,sizeof(request));
    n=strlen(action);
    if(n==0u || n>FPE_MAX_ACTION_BYTES) { set_error(error,FPE_INVALID_REQUEST,"action must contain 1..64 bytes"); return FPE_INVALID_REQUEST; }
    while(start<n && isspace((unsigned char)action[start])) ++start;
    end=n;
    while(end>start && isspace((unsigned char)action[end-1u])) --end;
    if(end==start) { set_error(error,FPE_INVALID_REQUEST,"action must not be blank"); return FPE_INVALID_REQUEST; }
    if(end-start>FPE_MAX_ACTION_BYTES) { set_error(error,FPE_INVALID_REQUEST,"trimmed action is too long"); return FPE_INVALID_REQUEST; }
    if(find_cluster(&runtime->projection,target_id)!=NULL) request.target_kind=FPE_TARGET_CLUSTER;
    else if(find_bud(&runtime->projection,target_id,&parent)!=NULL) request.target_kind=FPE_TARGET_BUD;
    else { set_error(error,FPE_UNKNOWN_ID,"unknown semantic request target"); return FPE_UNKNOWN_ID; }
    if(payload_json==NULL) payload_json="{}";
    if(!valid_payload_object(payload_json)) { set_error(error,FPE_INVALID_REQUEST,"payload must be a finite, valid JSON object (max 64 KiB/depth 32)"); return FPE_INVALID_REQUEST; }
    memcpy(request.schema,FPE_ACTION_SCHEMA,strlen(FPE_ACTION_SCHEMA)+1u);
    memcpy(request.action,action+start,end-start); request.action[end-start]='\0';
    if(strlen(target_id)>=sizeof(request.target_id)) { set_error(error,FPE_INVALID_REQUEST,"target id is too long"); return FPE_INVALID_REQUEST; }
    (void)snprintf(request.target_id,sizeof(request.target_id),"%s",target_id);
    request.payload_json=copy_string(payload_json);
    if(request.payload_json==NULL) { set_error(error,FPE_INVALID_REQUEST,"out of memory copying request payload"); return FPE_INVALID_REQUEST; }
    request.seed=runtime->projection.seed;
    (void)snprintf(request.pixelgen_world_fingerprint,sizeof(request.pixelgen_world_fingerprint),"%s",runtime->projection.pixelgen_world_fingerprint);
    request.columns=runtime->projection.columns; request.rows=runtime->projection.rows;
    request.source_revision=runtime->projection.state_revision; request.source_tick=runtime->projection.state_tick;
    *out_request=request;
    return FPE_OK;
}

static bool checkpoint_scheduler_valid(const FPECheckpoint *cp) {
    size_t i;
    if(cp->entry_count!=cp->projection.cluster_count || (cp->entry_count!=0u && cp->entries==NULL) ||
       cp->last_tick < -1 || cp->scheduler_last_tick < -1 ||
       cp->scheduler_last_tick > cp->last_tick ||
       (cp->scheduler_last_tick != -1 && cp->scheduler_last_tick != cp->last_tick)) return false;
    for(i=0;i<cp->entry_count;++i) {
        const FPEEntry *e=&cp->entries[i];
        if(e->cluster_index>=cp->projection.cluster_count || e->next_tick<0 ||
           (e->has_last && (e->last_tick<0 || e->last_tick>cp->scheduler_last_tick || e->next_tick<=e->last_tick)) ||
           (!e->has_last && e->next_tick!=0) ||
           e->detail<FPE_PLAN_CLUSTER_PROXY || e->detail>FPE_PLAN_GEOMETRY) return false;
        if(i>0u && strcmp(cp->projection.clusters[cp->entries[i-1u].cluster_index].id,
                          cp->projection.clusters[e->cluster_index].id)>=0) return false;
    }
    return true;
}

FPEErrorCode fpe_runtime_checkpoint(const FPERuntime *runtime,FPECheckpoint **out_checkpoint,FPEError *error) {
    FPECheckpoint *cp;
    fpe_error_clear(error);
    if(runtime==NULL || out_checkpoint==NULL) { set_error(error,FPE_INVALID_OPTIONS,"runtime and checkpoint output are required"); return FPE_INVALID_OPTIONS; }
    *out_checkpoint=NULL;
    cp=(FPECheckpoint *)calloc(1,sizeof(FPECheckpoint));
    if(cp==NULL) { set_error(error,FPE_INVALID_SNAPSHOT,"out of memory creating checkpoint"); return FPE_INVALID_SNAPSHOT; }
    if(!projection_clone(&runtime->projection,&cp->projection) ||
       normalize_view(&runtime->projection,&runtime->view,&cp->view,error)!=FPE_OK) goto fail;
    cp->entries=(FPEEntry *)malloc(runtime->entry_count*sizeof(FPEEntry));
    if(runtime->entry_count!=0u && cp->entries==NULL) goto fail;
    if(runtime->entry_count!=0u) memcpy(cp->entries,runtime->entries,runtime->entry_count*sizeof(FPEEntry));
    cp->entry_count=runtime->entry_count; cp->budget=runtime->budget;
    cp->last_tick=runtime->last_tick; cp->scheduler_last_tick=runtime->scheduler_last_tick;
    *out_checkpoint=cp;
    return FPE_OK;
fail:
    fpe_checkpoint_destroy(cp);
    set_error(error,FPE_INVALID_SNAPSHOT,"could not deep-copy runtime checkpoint");
    return FPE_INVALID_SNAPSHOT;
}

FPEErrorCode fpe_runtime_restore(const FPECheckpoint *checkpoint,FPERuntime **out_runtime,FPEError *error) {
    FPERuntime *runtime;
    FPEPlan preflight;
    fpe_error_clear(error);
    if(checkpoint==NULL || out_runtime==NULL || checkpoint->budget==0u) {
        set_error(error,FPE_INVALID_SNAPSHOT,"invalid native checkpoint"); return FPE_INVALID_SNAPSHOT;
    }
    *out_runtime=NULL;
    if(fpe_projection_validate(&checkpoint->projection,error)!=FPE_OK || !checkpoint_scheduler_valid(checkpoint)) {
        set_error(error,FPE_INVALID_SNAPSHOT,"checkpoint projection or scheduler state is invalid"); return FPE_INVALID_SNAPSHOT;
    }
    memset(&preflight,0,sizeof(preflight));
    if(build_plan(&checkpoint->projection,&checkpoint->view,&preflight,error)!=FPE_OK) {
        set_error(error,FPE_INVALID_SNAPSHOT,"checkpoint view is invalid"); return FPE_INVALID_SNAPSHOT;
    }
    fpe_plan_destroy(&preflight);
    runtime=(FPERuntime *)calloc(1,sizeof(FPERuntime));
    if(runtime==NULL) { set_error(error,FPE_INVALID_SNAPSHOT,"out of memory restoring checkpoint"); return FPE_INVALID_SNAPSHOT; }
    if(!projection_clone(&checkpoint->projection,&runtime->projection) ||
       normalize_view(&checkpoint->projection,&checkpoint->view,&runtime->view,error)!=FPE_OK) goto fail;
    runtime->entries=(FPEEntry *)malloc(checkpoint->entry_count*sizeof(FPEEntry));
    if(checkpoint->entry_count!=0u && runtime->entries==NULL) goto fail;
    if(checkpoint->entry_count!=0u) memcpy(runtime->entries,checkpoint->entries,checkpoint->entry_count*sizeof(FPEEntry));
    runtime->entry_count=checkpoint->entry_count; runtime->budget=checkpoint->budget;
    runtime->last_tick=checkpoint->last_tick; runtime->scheduler_last_tick=checkpoint->scheduler_last_tick;
    *out_runtime=runtime;
    return FPE_OK;
fail:
    fpe_runtime_destroy(runtime);
    set_error(error,FPE_INVALID_SNAPSHOT,"out of memory restoring checkpoint state");
    return FPE_INVALID_SNAPSHOT;
}

static int snapshot_entry_ptr_compare(const void *a,const void *b) {
    const FPESnapshotSchedulerEntry *const *x=(const FPESnapshotSchedulerEntry *const *)a;
    const FPESnapshotSchedulerEntry *const *y=(const FPESnapshotSchedulerEntry *const *)b;
    return strcmp((*x)->id,(*y)->id);
}

static bool view_state_equal(const FPEViewState *a,const FPEViewState *b) {
    size_t i;
    if(a->expanded_cluster_count!=b->expanded_cluster_count ||
       a->expanded_bud_count!=b->expanded_bud_count) return false;
    for(i=0;i<a->expanded_cluster_count;++i)
        if(strcmp(a->expanded_clusters[i],b->expanded_clusters[i])!=0) return false;
    for(i=0;i<a->expanded_bud_count;++i)
        if(strcmp(a->expanded_buds[i],b->expanded_buds[i])!=0) return false;
    return true;
}

FPEErrorCode fpe_runtime_restore_snapshot_parts(
    const FPEProjection *projection,size_t budget,const FPEViewState *view,
    int64_t runtime_last_tick,int64_t scheduler_last_tick,
    const FPESnapshotSchedulerEntry *entries,size_t entry_count,
    FPERuntime **out_runtime,FPEError *error) {
    FPERuntime *runtime=NULL;
    FPEViewState normalized;
    const FPESnapshotSchedulerEntry **ordered=NULL;
    size_t i;
    memset(&normalized,0,sizeof(normalized));
    fpe_error_clear(error);
    if(out_runtime==NULL) {
        set_error(error,FPE_INVALID_SNAPSHOT,"snapshot runtime output is required");
        return FPE_INVALID_SNAPSHOT;
    }
    *out_runtime=NULL;
    if((uint64_t)budget>(uint64_t)FPE_MAX_SAFE_INTEGER ||
       runtime_last_tick < -1 || runtime_last_tick > FPE_MAX_SAFE_INTEGER-16 ||
       scheduler_last_tick < -1 || scheduler_last_tick > runtime_last_tick ||
       (scheduler_last_tick!=-1 && scheduler_last_tick!=runtime_last_tick) ||
       entry_count!=(projection!=NULL?projection->cluster_count:0u) ||
       (entry_count!=0u && entries==NULL)) {
        set_error(error,FPE_INVALID_SNAPSHOT,"snapshot options, clocks or scheduler entry count are invalid");
        return FPE_INVALID_SNAPSHOT;
    }
    if(fpe_runtime_create(projection,budget,&runtime,error)!=FPE_OK) {
        set_error(error,FPE_INVALID_SNAPSHOT,"snapshot projection or budget is invalid");
        return FPE_INVALID_SNAPSHOT;
    }
    if(normalize_view(&runtime->projection,view,&normalized,error)!=FPE_OK ||
       !view_state_equal(&normalized,view)) {
        fpe_view_state_destroy(&normalized);
        fpe_runtime_destroy(runtime);
        set_error(error,FPE_INVALID_SNAPSHOT,"snapshot view is not canonical for its projection");
        return FPE_INVALID_SNAPSHOT;
    }
    if(entry_count!=0u) {
        ordered=(const FPESnapshotSchedulerEntry **)malloc(entry_count*sizeof(*ordered));
        if(ordered==NULL) {
            fpe_view_state_destroy(&normalized);
            fpe_runtime_destroy(runtime);
            set_error(error,FPE_INVALID_SNAPSHOT,"out of memory validating snapshot scheduler entries");
            return FPE_INVALID_SNAPSHOT;
        }
        for(i=0;i<entry_count;++i) ordered[i]=&entries[i];
        qsort(ordered,entry_count,sizeof(*ordered),snapshot_entry_ptr_compare);
    }
    for(i=0;i<entry_count;++i) {
        const FPESnapshotSchedulerEntry *raw=ordered[i];
        FPEEntry *dst=&runtime->entries[i];
        const FPECluster *cluster=&runtime->projection.clusters[dst->cluster_index];
        if(raw->id==NULL || raw->id[0]=='\0' ||
           (i!=0u && strcmp(ordered[i-1u]->id,raw->id)==0) ||
           strcmp(raw->id,cluster->id)!=0 ||
           !isfinite(raw->rate) || raw->rate!=cluster->projection.update_rate ||
           raw->next_tick<0 || raw->next_tick>FPE_MAX_SAFE_INTEGER ||
           raw->detail<FPE_PLAN_CLUSTER_PROXY || raw->detail>FPE_PLAN_GEOMETRY ||
           (raw->has_last && (raw->last_tick<0 || raw->last_tick>scheduler_last_tick ||
                              raw->next_tick<=raw->last_tick)) ||
           (!raw->has_last && raw->next_tick!=0) ||
           (scheduler_last_tick==-1 &&
             (raw->has_last || raw->next_tick!=0 || raw->detail!=FPE_PLAN_CLUSTER_PROXY))) {
            free(ordered);
            fpe_view_state_destroy(&normalized);
            fpe_runtime_destroy(runtime);
            set_error(error,FPE_INVALID_SNAPSHOT,"snapshot scheduler entry is invalid or does not match projection");
            return FPE_INVALID_SNAPSHOT;
        }
        dst->next_tick=raw->next_tick;
        dst->last_tick=raw->has_last?raw->last_tick:0;
        dst->has_last=raw->has_last;
        dst->detail=raw->detail;
    }
    free(ordered);
    runtime->view=normalized;
    runtime->last_tick=runtime_last_tick;
    runtime->scheduler_last_tick=scheduler_last_tick;
    *out_runtime=runtime;
    return FPE_OK;
}

void fpe_checkpoint_destroy(FPECheckpoint *checkpoint) {
    if(checkpoint==NULL) return;
    projection_destroy(&checkpoint->projection);
    fpe_view_state_destroy(&checkpoint->view);
    free(checkpoint->entries);
    free(checkpoint);
}

typedef struct FPESnapshotBuffer {
    char *data;
    size_t length;
    size_t capacity;
    bool failed;
} FPESnapshotBuffer;

static bool snapshot_buffer_reserve(FPESnapshotBuffer *b,size_t extra) {
    size_t needed,capacity;
    char *next;
    if(b->failed || extra>SIZE_MAX-b->length-1u) { b->failed=true; return false; }
    needed=b->length+extra+1u;
    if(needed<=b->capacity) return true;
    capacity=b->capacity!=0u?b->capacity:512u;
    while(capacity<needed) {
        if(capacity>SIZE_MAX/2u) { capacity=needed; break; }
        capacity*=2u;
    }
    next=(char *)realloc(b->data,capacity);
    if(next==NULL) { b->failed=true; return false; }
    b->data=next; b->capacity=capacity;
    return true;
}
static void snapshot_buffer_bytes(FPESnapshotBuffer *b,const char *data,size_t length) {
    if(!snapshot_buffer_reserve(b,length)) return;
    if(length!=0u) memcpy(b->data+b->length,data,length);
    b->length+=length; b->data[b->length]='\0';
}
static void snapshot_buffer_text(FPESnapshotBuffer *b,const char *text) {
    snapshot_buffer_bytes(b,text,strlen(text));
}
static void snapshot_buffer_string(FPESnapshotBuffer *b,const char *text) {
    const unsigned char *p=(const unsigned char *)text;
    snapshot_buffer_text(b,"\"");
    while(*p!=0u) {
        const unsigned char ch=*p++;
        switch(ch) {
            case '"': snapshot_buffer_text(b,"\\\""); break;
            case '\\': snapshot_buffer_text(b,"\\\\"); break;
            case '\b': snapshot_buffer_text(b,"\\b"); break;
            case '\f': snapshot_buffer_text(b,"\\f"); break;
            case '\n': snapshot_buffer_text(b,"\\n"); break;
            case '\r': snapshot_buffer_text(b,"\\r"); break;
            case '\t': snapshot_buffer_text(b,"\\t"); break;
            default:
                if(ch<0x20u) {
                    char escaped[7];
                    (void)snprintf(escaped,sizeof(escaped),"\\u%04x",(unsigned)ch);
                    snapshot_buffer_bytes(b,escaped,6u);
                } else snapshot_buffer_bytes(b,(const char *)&ch,1u);
                break;
        }
    }
    snapshot_buffer_text(b,"\"");
}
static void snapshot_buffer_i64(FPESnapshotBuffer *b,int64_t value) {
    char text[32];
    int n=snprintf(text,sizeof(text),"%lld",(long long)value);
    if(n<0 || (size_t)n>=sizeof(text)) { b->failed=true; return; }
    snapshot_buffer_bytes(b,text,(size_t)n);
}
static void snapshot_buffer_size(FPESnapshotBuffer *b,size_t value) {
    char text[32];
    int n=snprintf(text,sizeof(text),"%llu",(unsigned long long)value);
    if(n<0 || (size_t)n>=sizeof(text)) { b->failed=true; return; }
    snapshot_buffer_bytes(b,text,(size_t)n);
}
static void snapshot_buffer_double(FPESnapshotBuffer *b,double value) {
    char text[64];
    int precision,n=-1;
    if(!isfinite(value)) { b->failed=true; return; }
    for(precision=1;precision<=17;++precision) {
        char *end=NULL;
        double parsed;
        int candidate=snprintf(text,sizeof(text),"%.*g",precision,value);
        if(candidate<=0 || (size_t)candidate>=sizeof(text)) continue;
        parsed=strtod(text,&end);
        if(end!=NULL && *end=='\0' && parsed==value) { n=candidate; break; }
    }
    if(n<=0 || (size_t)n>=sizeof(text)) { b->failed=true; return; }
    snapshot_buffer_bytes(b,text,(size_t)n);
}
static const char *snapshot_detail_name(FPEPlanKind detail) {
    switch(detail) {
        case FPE_PLAN_CLUSTER_PROXY: return "cluster_proxy";
        case FPE_PLAN_BUD_PROXY: return "bud_proxy";
        case FPE_PLAN_GEOMETRY: return "geometry";
        default: return NULL;
    }
}

void fpe_json_string_destroy(char *json) { free(json); }

FPEErrorCode fpe_runtime_serialize_json(const FPERuntime *runtime,
                                        char **out_json,size_t *out_length,
                                        FPEError *error) {
    FPESnapshotBuffer b;
    FPEViewState view;
    size_t i;
    fpe_error_clear(error);
    memset(&b,0,sizeof(b));
    memset(&view,0,sizeof(view));
    if(runtime==NULL || out_json==NULL || out_length==NULL) {
        set_error(error,FPE_INVALID_OPTIONS,"runtime and JSON output pointers are required");
        return FPE_INVALID_OPTIONS;
    }
    *out_json=NULL; *out_length=0u;
    if(runtime->projection.json_document==NULL || runtime->projection.json_document_length==0u ||
       runtime->budget==0u || (uint64_t)runtime->budget>(uint64_t)FPE_MAX_SAFE_INTEGER) {
        set_error(error,FPE_INVALID_SNAPSHOT,"portable JSON snapshots require a verified JSON-origin projection and safe budget");
        return FPE_INVALID_SNAPSHOT;
    }
    if(normalize_view(&runtime->projection,&runtime->view,&view,error)!=FPE_OK) {
        set_error(error,FPE_INVALID_SNAPSHOT,"runtime view cannot be normalized for snapshot");
        return FPE_INVALID_SNAPSHOT;
    }
    snapshot_buffer_text(&b,"{\"schema\":\"fpe.runtime_snapshot/0.11.0\",\"runtime_version\":\"1.0.0\"");
    snapshot_buffer_text(&b,",\"projection_schema\":");
    snapshot_buffer_string(&b,FPE_PROJECTION_SCHEMA);
    snapshot_buffer_text(&b,",\"action_request_schema\":");
    snapshot_buffer_string(&b,FPE_ACTION_SCHEMA);
    snapshot_buffer_text(&b,",\"options\":{\"budget\":");
    snapshot_buffer_size(&b,runtime->budget);
    snapshot_buffer_text(&b,"},\"projection\":");
    snapshot_buffer_bytes(&b,runtime->projection.json_document,runtime->projection.json_document_length);

    snapshot_buffer_text(&b,",\"view\":{\"expandedClusters\":[");
    for(i=0;i<view.expanded_cluster_count;++i) {
        if(i!=0u) snapshot_buffer_text(&b,",");
        snapshot_buffer_string(&b,view.expanded_clusters[i]);
    }
    snapshot_buffer_text(&b,"],\"expandedBuds\":[");
    for(i=0;i<view.expanded_bud_count;++i) {
        if(i!=0u) snapshot_buffer_text(&b,",");
        snapshot_buffer_string(&b,view.expanded_buds[i]);
    }
    snapshot_buffer_text(&b,"]},\"clock\":{\"last_tick\":");
    snapshot_buffer_i64(&b,runtime->last_tick);
    snapshot_buffer_text(&b,"},\"scheduler\":{\"schema\":\"fpe.scheduler_state/0.11.0\",\"budget\":");
    snapshot_buffer_size(&b,runtime->budget);
    snapshot_buffer_text(&b,",\"projection_fingerprint\":");
    snapshot_buffer_string(&b,runtime->projection.projection_fingerprint);
    snapshot_buffer_text(&b,",\"source_revision\":");
    snapshot_buffer_i64(&b,(int64_t)runtime->projection.state_revision);
    snapshot_buffer_text(&b,",\"source_tick\":");
    snapshot_buffer_i64(&b,(int64_t)runtime->projection.state_tick);
    snapshot_buffer_text(&b,",\"last_tick\":");
    snapshot_buffer_i64(&b,runtime->scheduler_last_tick);
    snapshot_buffer_text(&b,",\"entries\":[");
    for(i=0;i<runtime->entry_count;++i) {
        const FPEEntry *entry=&runtime->entries[i];
        const FPECluster *cluster;
        const char *detail;
        if(entry->cluster_index>=runtime->projection.cluster_count) { b.failed=true; break; }
        cluster=&runtime->projection.clusters[entry->cluster_index];
        detail=snapshot_detail_name(entry->detail);
        if(detail==NULL) { b.failed=true; break; }
        if(i!=0u) snapshot_buffer_text(&b,",");
        snapshot_buffer_text(&b,"{\"id\":");
        snapshot_buffer_string(&b,cluster->id);
        snapshot_buffer_text(&b,",\"rate\":");
        snapshot_buffer_double(&b,cluster->projection.update_rate);
        snapshot_buffer_text(&b,",\"next\":");
        snapshot_buffer_i64(&b,entry->next_tick);
        snapshot_buffer_text(&b,",\"last\":");
        if(entry->has_last) snapshot_buffer_i64(&b,entry->last_tick);
        else snapshot_buffer_text(&b,"null");
        snapshot_buffer_text(&b,",\"detail\":");
        snapshot_buffer_string(&b,detail);
        snapshot_buffer_text(&b,"}");
    }
    snapshot_buffer_text(&b,"]},\"request_context\":{\"action_request_schema\":");
    snapshot_buffer_string(&b,FPE_ACTION_SCHEMA);
    snapshot_buffer_text(&b,",\"source\":{\"seed\":");
    snapshot_buffer_i64(&b,runtime->projection.seed);
    snapshot_buffer_text(&b,",\"pixelgen_world_fingerprint\":");
    snapshot_buffer_string(&b,runtime->projection.pixelgen_world_fingerprint);
    snapshot_buffer_text(&b,",\"dimensions\":[");
    snapshot_buffer_size(&b,runtime->projection.columns);
    snapshot_buffer_text(&b,",");
    snapshot_buffer_size(&b,runtime->projection.rows);
    snapshot_buffer_text(&b,"],\"state_revision\":");
    snapshot_buffer_i64(&b,(int64_t)runtime->projection.state_revision);
    snapshot_buffer_text(&b,",\"state_tick\":");
    snapshot_buffer_i64(&b,(int64_t)runtime->projection.state_tick);
    snapshot_buffer_text(&b,"}}}");
    fpe_view_state_destroy(&view);
    if(b.failed || b.data==NULL) {
        free(b.data);
        set_error(error,FPE_INVALID_SNAPSHOT,"out of memory or invalid data serializing portable snapshot");
        return FPE_INVALID_SNAPSHOT;
    }
    *out_json=b.data; *out_length=b.length;
    return FPE_OK;
}

void fpe_update_batch_destroy(FPEUpdateBatch *batch) {
    if(batch==NULL) return;
    free(batch->updates);
    memset(batch,0,sizeof(*batch));
}
