#ifndef FPE_FPE_H
#define FPE_FPE_H

/*
 * FPE C 0.1.0 — portable C11 manifestation/view runtime.
 * This is a typed native ABI. It does not yet parse or emit the stable
 * JavaScript JSON snapshot/projection schemas byte-for-byte.
 */
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define FPE_C_VERSION "0.1.0"
#define FPE_PROJECTION_SCHEMA "fpe.pixelgen_hierarchy/0.6.0"
#define FPE_VIEW_SCHEMA "fpe.view_hierarchy/0.6.0"
#define FPE_ACTION_SCHEMA "fpe.action_request/0.10.0"
#define FPE_SNAPSHOT_SCHEMA "fpe.runtime_snapshot/0.11.0"
#define FPE_SCHEDULER_SCHEMA "fpe.scheduler_state/0.11.0"
#define FPE_BUDS_PER_CLUSTER 4u
#define FPE_ID_CAPACITY 128u
#define FPE_ERROR_CAPACITY 192u
#define FPE_MAX_ACTION_BYTES 64u
#define FPE_MAX_PAYLOAD_BYTES 65536u
#define FPE_MAX_SAFE_INTEGER INT64_C(9007199254740991)

typedef enum FPEErrorCode {
    FPE_OK = 0,
    FPE_INVALID_OPTIONS,
    FPE_INVALID_PROJECTION,
    FPE_FOREIGN_WORLD,
    FPE_STALE_REVISION,
    FPE_REVISION_CONFLICT,
    FPE_INVALID_VIEW,
    FPE_UNKNOWN_ID,
    FPE_PARENT_COLLAPSED,
    FPE_INVALID_TICK,
    FPE_INVALID_REQUEST,
    FPE_INVALID_SNAPSHOT
} FPEErrorCode;

typedef struct FPEError {
    FPEErrorCode code;
    char message[FPE_ERROR_CAPACITY];
} FPEError;

typedef enum FPEBudType {
    FPE_BUD_STRAIGHT = 0,
    FPE_BUD_CURVED = 1
} FPEBudType;

typedef enum FPEFrontStatus {
    FPE_FRONT_QUIET = 0,
    FPE_FRONT_ACTIVE,
    FPE_FRONT_TENSE,
    FPE_FRONT_VOLATILE
} FPEFrontStatus;

typedef enum FPEPlanKind {
    FPE_PLAN_CLUSTER_PROXY = 0,
    FPE_PLAN_BUD_PROXY,
    FPE_PLAN_GEOMETRY
} FPEPlanKind;

typedef enum FPETargetKind {
    FPE_TARGET_CLUSTER = 0,
    FPE_TARGET_BUD
} FPETargetKind;

typedef struct FPEBud {
    const char *id;
    uint32_t index;
    int32_t offset_x;
    int32_t offset_z;
    FPEBudType type;
    const char *seed_key;
} FPEBud;

typedef struct FPEClusterMetrics {
    double cohesion;
    double breakup_resistance;
    double agitation;
    double collapse_bias;
    double damage_proxy;
    double update_rate;
} FPEClusterMetrics;

typedef struct FPEClusterState {
    double stability;
    double alert;
    double front_tension;
    double front_activity;
    double control_strength;
    FPEFrontStatus front_status;
} FPEClusterState;

typedef struct FPECluster {
    const char *id;
    uint32_t sector_x;
    uint32_t sector_y;
    FPEClusterMetrics projection;
    FPEClusterState state;
    const char *territory_id; /* NULL means no territory. */
    const char *const *front_ids;
    size_t front_count;
    FPEBud buds[FPE_BUDS_PER_CLUSTER];
} FPECluster;

typedef struct FPEProjectionSummary {
    uint64_t cluster_count;
    uint64_t bud_count;
    uint64_t territory_cluster_count;
    uint64_t front_cluster_count;
    uint64_t straight_bud_count;
    uint64_t curved_bud_count;
} FPEProjectionSummary;

/*
 * Borrowed input projection. All strings/arrays remain owned by the caller;
 * fpe_runtime_create/accept validate and deep-copy them before returning.
 */
typedef struct FPEProjection {
    const char *schema; /* Must be FPE_PROJECTION_SCHEMA. */
    const char *mode;   /* read_only_hierarchical_projection */
    const char *projection_fingerprint;     /* 64 lowercase hex chars. */
    const char *pixelgen_world_fingerprint; /* 64 lowercase hex chars. */
    int64_t seed;
    uint32_t columns;
    uint32_t rows;
    uint64_t state_revision;
    uint64_t state_tick;
    double sector_spacing;
    double local_bud_offset;
    const FPECluster *clusters;
    size_t cluster_count;
    FPEProjectionSummary summary;
} FPEProjection;

typedef struct FPEViewState {
    char **expanded_clusters;
    size_t expanded_cluster_count;
    char **expanded_buds;
    size_t expanded_bud_count;
} FPEViewState;

typedef struct FPEGeometryNode {
    double x, y, z;
    double random_value;
    double phase;
    uint32_t glyph_index;
} FPEGeometryNode;

typedef struct FPEGeometryEdge {
    uint32_t from;
    uint32_t to;
    double weight;
} FPEGeometryEdge;

typedef struct FPEPlanItem {
    FPEPlanKind kind;
    char id[FPE_ID_CAPACITY];
    char cluster_id[FPE_ID_CAPACITY];
    double center_x, center_y, center_z;
    FPEGeometryNode *nodes;
    size_t node_count;
    FPEGeometryEdge *edges;
    size_t edge_count;
} FPEPlanItem;

typedef struct FPEPlanCounts {
    size_t cluster_proxies;
    size_t bud_proxies;
    size_t geometries;
    size_t nodes;
    size_t edges;
} FPEPlanCounts;

typedef struct FPEPlan {
    FPEPlanItem *items;
    size_t item_count;
    FPEPlanCounts counts;
    FPEViewState state;
} FPEPlan;

typedef struct FPEUpdate {
    char cluster_id[FPE_ID_CAPACITY];
    int64_t tick;
    int64_t elapsed;
    uint32_t period;
    FPEPlanKind detail;
} FPEUpdate;

typedef struct FPEUpdateBatch {
    int64_t tick;
    FPEUpdate *updates;
    size_t update_count;
    size_t deferred_count;
    bool repeated;
} FPEUpdateBatch;

typedef struct FPEActionRequest {
    char schema[48];
    char action[FPE_MAX_ACTION_BYTES + 1u];
    FPETargetKind target_kind;
    char target_id[FPE_ID_CAPACITY];
    char *payload_json;
    int64_t seed;
    char pixelgen_world_fingerprint[65];
    uint32_t columns, rows;
    uint64_t source_revision, source_tick;
} FPEActionRequest;

typedef struct FPERuntime FPERuntime;
typedef struct FPECheckpoint FPECheckpoint;

const char *fpe_version(void);
const char *fpe_error_name(FPEErrorCode code);
const char *fpe_glyph(uint32_t index);

FPEErrorCode fpe_projection_validate(const FPEProjection *projection, FPEError *error);
FPEErrorCode fpe_runtime_create(const FPEProjection *projection, size_t budget,
                                FPERuntime **out_runtime, FPEError *error);
void fpe_runtime_destroy(FPERuntime *runtime);

/* Returns a borrowed, immutable-by-contract pointer valid until accept/destroy. */
const FPEProjection *fpe_runtime_projection(const FPERuntime *runtime);
FPEErrorCode fpe_runtime_accept(FPERuntime *runtime, const FPEProjection *incoming,
                                bool *changed, FPEError *error);
FPEErrorCode fpe_runtime_set_view(FPERuntime *runtime, const FPEViewState *view,
                                  FPEViewState *normalized, FPEError *error);
FPEErrorCode fpe_runtime_toggle_cluster(FPERuntime *runtime, const char *cluster_id,
                                        FPEViewState *result, FPEError *error);
FPEErrorCode fpe_runtime_toggle_bud(FPERuntime *runtime, const char *bud_id,
                                    FPEViewState *result, FPEError *error);
FPEErrorCode fpe_runtime_get_view(const FPERuntime *runtime, FPEViewState *out_view,
                                  FPEError *error);
FPEErrorCode fpe_runtime_get_plan(const FPERuntime *runtime, FPEPlan *out_plan,
                                  FPEError *error);
FPEErrorCode fpe_runtime_step(FPERuntime *runtime, int64_t tick,
                              FPEUpdateBatch *out_batch, FPEError *error);
FPEErrorCode fpe_runtime_request(const FPERuntime *runtime, const char *action,
                                 const char *target_id, const char *payload_json,
                                 FPEActionRequest *out_request, FPEError *error);

/* Native typed checkpoints; JSON snapshot interoperability is a later milestone. */
FPEErrorCode fpe_runtime_checkpoint(const FPERuntime *runtime,
                                    FPECheckpoint **out_checkpoint, FPEError *error);
FPEErrorCode fpe_runtime_restore(const FPECheckpoint *checkpoint,
                                 FPERuntime **out_runtime, FPEError *error);
void fpe_checkpoint_destroy(FPECheckpoint *checkpoint);

void fpe_view_state_destroy(FPEViewState *view);
void fpe_plan_destroy(FPEPlan *plan);
void fpe_update_batch_destroy(FPEUpdateBatch *batch);
void fpe_action_request_destroy(FPEActionRequest *request);
void fpe_error_clear(FPEError *error);

#ifdef __cplusplus
}
#endif
#endif /* FPE_FPE_H */
