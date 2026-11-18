#ifndef FPE_INTERNAL_H
#define FPE_INTERNAL_H

#include "fpe/fpe.h"

typedef struct FPESnapshotSchedulerEntry {
    const char *id;
    double rate;
    int64_t next_tick;
    bool has_last;
    int64_t last_tick;
    FPEPlanKind detail;
} FPESnapshotSchedulerEntry;

FPEErrorCode fpe_runtime_restore_snapshot_parts(
    const FPEProjection *projection,
    size_t budget,
    const FPEViewState *view,
    int64_t runtime_last_tick,
    int64_t scheduler_last_tick,
    const FPESnapshotSchedulerEntry *entries,
    size_t entry_count,
    FPERuntime **out_runtime,
    FPEError *error);

#endif
