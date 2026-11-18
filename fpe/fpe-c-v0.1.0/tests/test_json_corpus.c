#include "fpe/fpe.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CORPUS_LINE_MAX (8u * 1024u * 1024u + 2u)
#define EXPECTED_VECTORS 256u

static int verify_line(const char *line, size_t length, size_t index) {
    FPEProjection projection;
    FPEError error;
    FPEErrorCode result;
    memset(&projection, 0, sizeof(projection));
    result = fpe_projection_from_json(line, length, &projection, &error);
    if (result != FPE_OK) {
        (void)fprintf(stderr, "vector %lu rejected: %s\n",
                      (unsigned long)index, error.message);
        return 0;
    }
    if (projection.cluster_count != 30u ||
        projection.summary.bud_count != 120u ||
        projection.columns != 6u || projection.rows != 5u) {
        (void)fprintf(stderr, "vector %lu decoded unexpected dimensions/counts\n",
                      (unsigned long)index);
        fpe_projection_json_destroy(&projection);
        return 0;
    }
    fpe_projection_json_destroy(&projection);
    return 1;
}

int main(int argc, char **argv) {
    FILE *file;
    char *line;
    size_t length = 0u, count = 0u;
    int ch;
    if (argc != 2) {
        (void)fprintf(stderr, "usage: fpe_c_json_corpus_tests VECTORS.jsonl\n");
        return 2;
    }
    file = fopen(argv[1], "rb");
    if (file == NULL) {
        (void)fprintf(stderr, "cannot open vector corpus: %s\n", argv[1]);
        return 2;
    }
    line = (char *)malloc(CORPUS_LINE_MAX);
    if (line == NULL) {
        fclose(file);
        (void)fprintf(stderr, "out of memory allocating corpus input buffer\n");
        return 2;
    }
    while ((ch = fgetc(file)) != EOF) {
        if (ch == '\n') {
            if (length != 0u && line[length - 1u] == '\r') --length;
            if (length == 0u || !verify_line(line, length, count)) {
                free(line);
                fclose(file);
                return 1;
            }
            ++count;
            length = 0u;
            continue;
        }
        if (length >= CORPUS_LINE_MAX - 1u) {
            (void)fprintf(stderr, "vector line exceeds 8 MiB limit\n");
            free(line);
            fclose(file);
            return 1;
        }
        line[length++] = (char)(unsigned char)ch;
    }
    if (ferror(file)) {
        (void)fprintf(stderr, "error reading vector corpus\n");
        free(line);
        fclose(file);
        return 1;
    }
    if (length != 0u) {
        if (!verify_line(line, length, count)) {
            free(line);
            fclose(file);
            return 1;
        }
        ++count;
    }
    free(line);
    fclose(file);
    if (count != EXPECTED_VECTORS) {
        (void)fprintf(stderr, "expected %u vectors, got %lu\n",
                      EXPECTED_VECTORS, (unsigned long)count);
        return 1;
    }
    (void)printf("Python↔C projection fingerprint corpus: PASS (%lu vectors)\n",
                 (unsigned long)count);
    return 0;
}
