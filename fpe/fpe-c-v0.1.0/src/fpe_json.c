#include "fpe/fpe.h"

#include <ctype.h>
#include <errno.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FPE_JSON_MAX_BYTES (8u * 1024u * 1024u)
#define FPE_JSON_MAX_NODES 300000u
#define FPE_JSON_MAX_DEPTH 64u
#define FPE_JSON_MAX_CLUSTERS 100000u
#define FPE_JSON_MAX_SAFE 9007199254740991.0

typedef enum JType { J_NULL, J_BOOL, J_NUMBER, J_STRING, J_ARRAY, J_OBJECT } JType;
typedef struct JNode JNode;
typedef struct JMember { char *key; JNode *value; } JMember;
struct JNode {
    JType type;
    char *string;
    double number;
    bool integer_token;
    bool boolean_value;
    int64_t integer;
    JNode **items;
    size_t count;
    JMember *members;
};

typedef struct JParser {
    const unsigned char *input;
    size_t length;
    size_t pos;
    size_t nodes;
    char error[ FPE_ERROR_CAPACITY ];
} JParser;

typedef struct JBuffer {
    char *data;
    size_t length;
    size_t capacity;
    bool failed;
} JBuffer;

typedef struct SHA256 {
    uint32_t h[8];
    uint64_t total;
    unsigned char block[64];
    size_t used;
} SHA256;

typedef enum CanonContext {
    C_ROOT, C_LAYOUT, C_CLUSTERS, C_CLUSTER, C_CLUSTER_STATE,
    C_CLUSTER_PROJECTION, C_OTHER
} CanonContext;

static void json_error(FPEError *error, FPEErrorCode code, const char *message) {
    if (error == NULL) return;
    error->code = code;
    (void)snprintf(error->message, sizeof(error->message), "%s", message != NULL ? message : "");
}

static char *json_copy_string(const char *s) {
    size_t n;
    char *copy;
    if (s == NULL) return NULL;
    n = strlen(s);
    if (n == SIZE_MAX) return NULL;
    copy = (char *)malloc(n + 1u);
    if (copy != NULL) memcpy(copy, s, n + 1u);
    return copy;
}

static JNode *node_new(JParser *p, JType type) {
    JNode *node;
    if (++p->nodes > FPE_JSON_MAX_NODES) {
        (void)snprintf(p->error, sizeof(p->error), "JSON node limit exceeded");
        return NULL;
    }
    node = (JNode *)calloc(1u, sizeof(*node));
    if (node == NULL) {
        (void)snprintf(p->error, sizeof(p->error), "out of memory parsing JSON");
        return NULL;
    }
    node->type = type;
    return node;
}

static void node_destroy(JNode *node) {
    size_t i;
    if (node == NULL) return;
    free(node->string);
    for (i = 0; i < node->count; ++i) {
        if (node->type == J_OBJECT) {
            free(node->members[i].key);
            node_destroy(node->members[i].value);
        } else if (node->type == J_ARRAY) {
            node_destroy(node->items[i]);
        }
    }
    free(node->items);
    free(node->members);
    free(node);
}

static void skip_ws(JParser *p) {
    while (p->pos < p->length) {
        unsigned char c = p->input[p->pos];
        if (c == ' ' || c == '\t' || c == '\r' || c == '\n') ++p->pos;
        else break;
    }
}

static bool utf8_sequence(const unsigned char *s, size_t left, size_t *width) {
    unsigned char a;
    if (left == 0u) return false;
    a = s[0];
    if (a < 0x80u) { *width = 1u; return true; }
    if (a >= 0xc2u && a <= 0xdfu) {
        if (left < 2u || (s[1] & 0xc0u) != 0x80u) return false;
        *width = 2u; return true;
    }
    if (a >= 0xe0u && a <= 0xefu) {
        if (left < 3u || (s[1] & 0xc0u) != 0x80u || (s[2] & 0xc0u) != 0x80u) return false;
        if (a == 0xe0u && s[1] < 0xa0u) return false;
        if (a == 0xedu && s[1] >= 0xa0u) return false;
        *width = 3u; return true;
    }
    if (a >= 0xf0u && a <= 0xf4u) {
        if (left < 4u || (s[1] & 0xc0u) != 0x80u ||
            (s[2] & 0xc0u) != 0x80u || (s[3] & 0xc0u) != 0x80u) return false;
        if (a == 0xf0u && s[1] < 0x90u) return false;
        if (a == 0xf4u && s[1] > 0x8fu) return false;
        *width = 4u; return true;
    }
    return false;
}

static bool append_utf8(char *out, size_t cap, size_t *used, uint32_t cp) {
    unsigned char bytes[4];
    size_t n, i;
    if (cp <= 0x7fu) { bytes[0] = (unsigned char)cp; n = 1u; }
    else if (cp <= 0x7ffu) {
        bytes[0] = (unsigned char)(0xc0u | (cp >> 6));
        bytes[1] = (unsigned char)(0x80u | (cp & 0x3fu)); n = 2u;
    } else if (cp <= 0xffffu && !(cp >= 0xd800u && cp <= 0xdfffu)) {
        bytes[0] = (unsigned char)(0xe0u | (cp >> 12));
        bytes[1] = (unsigned char)(0x80u | ((cp >> 6) & 0x3fu));
        bytes[2] = (unsigned char)(0x80u | (cp & 0x3fu)); n = 3u;
    } else if (cp >= 0x10000u && cp <= 0x10ffffu) {
        bytes[0] = (unsigned char)(0xf0u | (cp >> 18));
        bytes[1] = (unsigned char)(0x80u | ((cp >> 12) & 0x3fu));
        bytes[2] = (unsigned char)(0x80u | ((cp >> 6) & 0x3fu));
        bytes[3] = (unsigned char)(0x80u | (cp & 0x3fu)); n = 4u;
    } else return false;
    if (*used > cap || n > cap - *used) return false;
    for (i = 0; i < n; ++i) out[(*used)++] = (char)bytes[i];
    return true;
}

static bool hex4(JParser *p, uint32_t *value) {
    size_t i;
    uint32_t v = 0u;
    if (p->length - p->pos < 4u) return false;
    for (i = 0; i < 4u; ++i) {
        unsigned char c = p->input[p->pos++];
        uint32_t d;
        if (c >= '0' && c <= '9') d = (uint32_t)(c - '0');
        else if (c >= 'a' && c <= 'f') d = (uint32_t)(c - 'a') + 10u;
        else if (c >= 'A' && c <= 'F') d = (uint32_t)(c - 'A') + 10u;
        else return false;
        v = (v << 4) | d;
    }
    *value = v;
    return true;
}

static char *parse_string(JParser *p) {
    char *out;
    size_t used = 0u;
    if (p->pos >= p->length || p->input[p->pos] != '"') return NULL;
    ++p->pos;
    out = (char *)malloc(p->length - p->pos + 1u);
    if (out == NULL) {
        (void)snprintf(p->error, sizeof(p->error), "out of memory parsing string");
        return NULL;
    }
    while (p->pos < p->length) {
        unsigned char c = p->input[p->pos++];
        if (c == '"') {
            out[used] = '\0';
            return out;
        }
        if (c < 0x20u) break;
        if (c == '\\') {
            uint32_t cp;
            if (p->pos >= p->length) break;
            c = p->input[p->pos++];
            switch (c) {
                case '"': out[used++] = '"'; break;
                case '\\': out[used++] = '\\'; break;
                case '/': out[used++] = '/'; break;
                case 'b': out[used++] = '\b'; break;
                case 'f': out[used++] = '\f'; break;
                case 'n': out[used++] = '\n'; break;
                case 'r': out[used++] = '\r'; break;
                case 't': out[used++] = '\t'; break;
                case 'u':
                    if (!hex4(p, &cp)) goto bad;
                    if (cp >= 0xd800u && cp <= 0xdbffu) {
                        uint32_t low;
                        if (p->length - p->pos < 6u || p->input[p->pos] != '\\' ||
                            p->input[p->pos + 1u] != 'u') goto bad;
                        p->pos += 2u;
                        if (!hex4(p, &low) || low < 0xdc00u || low > 0xdfffu) goto bad;
                        cp = 0x10000u + ((cp - 0xd800u) << 10) + (low - 0xdc00u);
                    } else if (cp >= 0xdc00u && cp <= 0xdfffu) goto bad;
                    if (cp == 0u || !append_utf8(out, p->length, &used, cp)) goto bad;
                    break;
                default: goto bad;
            }
        } else if (c < 0x80u) {
            out[used++] = (char)c;
        } else {
            size_t width, start = p->pos - 1u, i;
            if (!utf8_sequence(p->input + start, p->length - start, &width)) goto bad;
            for (i = 0; i < width; ++i) out[used++] = (char)p->input[start + i];
            p->pos = start + width;
        }
    }
bad:
    free(out);
    (void)snprintf(p->error, sizeof(p->error), "invalid JSON string or UTF-8 sequence");
    return NULL;
}

static bool node_push_array(JParser *p, JNode *array, JNode *value) {
    JNode **next;
    if (array->count >= FPE_JSON_MAX_NODES) return false;
    next = (JNode **)realloc(array->items, (array->count + 1u) * sizeof(JNode *));
    if (next == NULL) {
        (void)snprintf(p->error, sizeof(p->error), "out of memory growing JSON array");
        return false;
    }
    array->items = next;
    array->items[array->count++] = value;
    return true;
}

static bool node_push_member(JParser *p, JNode *object, char *key, JNode *value) {
    JMember *next;
    size_t i;
    for (i = 0; i < object->count; ++i) {
        if (strcmp(object->members[i].key, key) == 0) {
            (void)snprintf(p->error, sizeof(p->error), "duplicate JSON object key");
            return false;
        }
    }
    if (object->count >= FPE_JSON_MAX_NODES) return false;
    next = (JMember *)realloc(object->members, (object->count + 1u) * sizeof(JMember));
    if (next == NULL) {
        (void)snprintf(p->error, sizeof(p->error), "out of memory growing JSON object");
        return false;
    }
    object->members = next;
    object->members[object->count].key = key;
    object->members[object->count].value = value;
    ++object->count;
    return true;
}

static JNode *parse_value(JParser *p, size_t depth);

static JNode *parse_array(JParser *p, size_t depth) {
    JNode *array = node_new(p, J_ARRAY);
    if (array == NULL) return NULL;
    ++p->pos;
    skip_ws(p);
    if (p->pos < p->length && p->input[p->pos] == ']') { ++p->pos; return array; }
    for (;;) {
        JNode *value = parse_value(p, depth + 1u);
        if (value == NULL || !node_push_array(p, array, value)) {
            node_destroy(value); node_destroy(array); return NULL;
        }
        skip_ws(p);
        if (p->pos >= p->length) break;
        if (p->input[p->pos] == ']') { ++p->pos; return array; }
        if (p->input[p->pos] != ',') break;
        ++p->pos; skip_ws(p);
    }
    node_destroy(array);
    (void)snprintf(p->error, sizeof(p->error), "malformed JSON array");
    return NULL;
}

static JNode *parse_object(JParser *p, size_t depth) {
    JNode *object = node_new(p, J_OBJECT);
    if (object == NULL) return NULL;
    ++p->pos;
    skip_ws(p);
    if (p->pos < p->length && p->input[p->pos] == '}') { ++p->pos; return object; }
    for (;;) {
        char *key;
        JNode *value;
        if (p->pos >= p->length || p->input[p->pos] != '"') break;
        key = parse_string(p);
        if (key == NULL) break;
        skip_ws(p);
        if (p->pos >= p->length || p->input[p->pos] != ':') {
            free(key); break;
        }
        ++p->pos; skip_ws(p);
        value = parse_value(p, depth + 1u);
        if (value == NULL || !node_push_member(p, object, key, value)) {
            free(key); node_destroy(value); node_destroy(object); return NULL;
        }
        skip_ws(p);
        if (p->pos >= p->length) break;
        if (p->input[p->pos] == '}') { ++p->pos; return object; }
        if (p->input[p->pos] != ',') break;
        ++p->pos; skip_ws(p);
    }
    node_destroy(object);
    if (p->error[0] == '\0') (void)snprintf(p->error, sizeof(p->error), "malformed JSON object");
    return NULL;
}

static JNode *parse_number(JParser *p) {
    size_t start = p->pos, length;
    char *token, *end;
    double value;
    JNode *node;
    if (p->input[p->pos] == '-') ++p->pos;
    if (p->pos >= p->length) return NULL;
    if (p->input[p->pos] == '0') ++p->pos;
    else if (p->input[p->pos] >= '1' && p->input[p->pos] <= '9') {
        while (p->pos < p->length && isdigit((int)p->input[p->pos])) ++p->pos;
    } else return NULL;
    if (p->pos < p->length && p->input[p->pos] == '.') {
        ++p->pos;
        if (p->pos >= p->length || !isdigit((int)p->input[p->pos])) return NULL;
        while (p->pos < p->length && isdigit((int)p->input[p->pos])) ++p->pos;
    }
    if (p->pos < p->length && (p->input[p->pos] == 'e' || p->input[p->pos] == 'E')) {
        ++p->pos;
        if (p->pos < p->length && (p->input[p->pos] == '+' || p->input[p->pos] == '-')) ++p->pos;
        if (p->pos >= p->length || !isdigit((int)p->input[p->pos])) return NULL;
        while (p->pos < p->length && isdigit((int)p->input[p->pos])) ++p->pos;
    }
    length = p->pos - start;
    token = (char *)malloc(length + 1u);
    if (token == NULL) return NULL;
    memcpy(token, p->input + start, length); token[length] = '\0';
    errno = 0; value = strtod(token, &end);
    if (end != token + length || errno == ERANGE || !isfinite(value)) {
        free(token);
        (void)snprintf(p->error, sizeof(p->error), "JSON number is outside finite range");
        return NULL;
    }
    node = node_new(p, J_NUMBER);
    if (node == NULL) { free(token); return NULL; }
    node->number = value;
    node->integer_token = strpbrk(token, ".eE") == NULL;
    if (node->integer_token) {
        char *iend;
        long long iv;
        errno = 0; iv = strtoll(token, &iend, 10);
        if (errno == 0 && iend == token + length) node->integer = (int64_t)iv;
        else node->integer_token = false;
    }
    free(token);
    return node;
}

static JNode *parse_value(JParser *p, size_t depth) {
    JNode *node;
    if (depth > FPE_JSON_MAX_DEPTH) {
        (void)snprintf(p->error, sizeof(p->error), "JSON nesting depth exceeded");
        return NULL;
    }
    skip_ws(p);
    if (p->pos >= p->length) return NULL;
    switch (p->input[p->pos]) {
        case '{': return parse_object(p, depth);
        case '[': return parse_array(p, depth);
        case '"':
            node = node_new(p, J_STRING);
            if (node == NULL) return NULL;
            node->string = parse_string(p);
            if (node->string == NULL) { node_destroy(node); return NULL; }
            return node;
        case 't':
            if (p->length - p->pos >= 4u && memcmp(p->input + p->pos, "true", 4u) == 0) {
                p->pos += 4u; node = node_new(p, J_BOOL);
                if (node != NULL) node->boolean_value = true;
                return node;
            }
            break;
        case 'f':
            if (p->length - p->pos >= 5u && memcmp(p->input + p->pos, "false", 5u) == 0) {
                p->pos += 5u; node = node_new(p, J_BOOL);
                if (node != NULL) node->boolean_value = false;
                return node;
            }
            break;
        case 'n':
            if (p->length - p->pos >= 4u && memcmp(p->input + p->pos, "null", 4u) == 0) {
                p->pos += 4u; return node_new(p, J_NULL);
            }
            break;
        default:
            if (p->input[p->pos] == '-' || isdigit((int)p->input[p->pos])) return parse_number(p);
            break;
    }
    if (p->error[0] == '\0') (void)snprintf(p->error, sizeof(p->error), "invalid JSON token");
    return NULL;
}

static JNode *json_parse(const char *input, size_t length, char *error, size_t error_size) {
    JParser parser;
    JNode *root;
    memset(&parser, 0, sizeof(parser));
    if (input == NULL || length == 0u || length > FPE_JSON_MAX_BYTES) {
        (void)snprintf(error, error_size, "JSON input is empty or exceeds 8 MiB");
        return NULL;
    }
    parser.input = (const unsigned char *)input;
    parser.length = length;
    root = parse_value(&parser, 0u);
    skip_ws(&parser);
    if (root == NULL || parser.pos != parser.length) {
        node_destroy(root);
        (void)snprintf(error, error_size, "%s", parser.error[0] != '\0' ? parser.error : "trailing data or malformed JSON");
        return NULL;
    }
    return root;
}

static JNode *object_get(const JNode *object, const char *key) {
    size_t i;
    if (object == NULL || object->type != J_OBJECT) return NULL;
    for (i = 0; i < object->count; ++i)
        if (strcmp(object->members[i].key, key) == 0) return object->members[i].value;
    return NULL;
}

static bool buffer_reserve(JBuffer *b, size_t extra) {
    size_t needed, cap;
    char *next;
    if (b->failed || extra > SIZE_MAX - b->length - 1u) { b->failed = true; return false; }
    needed = b->length + extra + 1u;
    if (needed <= b->capacity) return true;
    cap = b->capacity != 0u ? b->capacity : 256u;
    while (cap < needed) {
        if (cap > SIZE_MAX / 2u) { cap = needed; break; }
        cap *= 2u;
    }
    next = (char *)realloc(b->data, cap);
    if (next == NULL) { b->failed = true; return false; }
    b->data = next; b->capacity = cap;
    return true;
}

static void buffer_bytes(JBuffer *b, const char *s, size_t n) {
    if (!buffer_reserve(b, n)) return;
    memcpy(b->data + b->length, s, n); b->length += n; b->data[b->length] = '\0';
}
static void buffer_char(JBuffer *b, char c) { buffer_bytes(b, &c, 1u); }

static void canonical_string(JBuffer *b, const char *s) {
    const unsigned char *p = (const unsigned char *)s;
    buffer_char(b, '"');
    while (*p != 0u) {
        unsigned char c = *p++;
        switch (c) {
            case '"': buffer_bytes(b, "\\\"", 2u); break;
            case '\\': buffer_bytes(b, "\\\\", 2u); break;
            case '\b': buffer_bytes(b, "\\b", 2u); break;
            case '\f': buffer_bytes(b, "\\f", 2u); break;
            case '\n': buffer_bytes(b, "\\n", 2u); break;
            case '\r': buffer_bytes(b, "\\r", 2u); break;
            case '\t': buffer_bytes(b, "\\t", 2u); break;
            default:
                if (c < 0x20u) {
                    char escaped[7];
                    (void)snprintf(escaped, sizeof(escaped), "\\u%04x", (unsigned)c);
                    buffer_bytes(b, escaped, 6u);
                } else buffer_char(b, (char)c);
                break;
        }
    }
    buffer_char(b, '"');
}

static int member_pointer_compare(const void *a, const void *b) {
    const JMember *const *x = (const JMember *const *)a;
    const JMember *const *y = (const JMember *const *)b;
    return strcmp((*x)->key, (*y)->key);
}

static bool float_path(CanonContext context, const char *key) {
    if (context == C_LAYOUT)
        return strcmp(key, "sector_spacing") == 0 || strcmp(key, "local_bud_offset") == 0;
    if (context == C_CLUSTER_STATE)
        return strcmp(key, "control_strength") == 0 || strcmp(key, "stability") == 0 ||
               strcmp(key, "alert") == 0 || strcmp(key, "front_tension") == 0 ||
               strcmp(key, "front_activity") == 0;
    if (context == C_CLUSTER_PROJECTION)
        return strcmp(key, "cohesion") == 0 || strcmp(key, "breakup_resistance") == 0 ||
               strcmp(key, "agitation") == 0 || strcmp(key, "collapse_bias") == 0 ||
               strcmp(key, "damage_proxy") == 0 || strcmp(key, "update_rate") == 0;
    return false;
}

static void canonical_node(JBuffer *b, const JNode *node, CanonContext context, bool as_float);

static void canonical_number(JBuffer *b, double value, bool as_float) {
    char text[64];
    int n;
    if (as_float) {
        if (value == 0.0 && signbit(value)) {
            buffer_bytes(b, "-0.0", 4u); return;
        }
        if (floor(value) == value && fabs(value) <= FPE_JSON_MAX_SAFE) {
            n = snprintf(text, sizeof(text), "%.0f.0", value);
        } else {
            /* Shortest round-tripping decimal: try increasing precision until
               strtod recreates the exact parsed IEEE-754 value. */
            int precision;
            n = -1;
            for (precision = 1; precision <= 17; ++precision) {
                char *end;
                double back;
                int candidate = snprintf(text, sizeof(text), "%.*g", precision, value);
                if (candidate <= 0 || (size_t)candidate >= sizeof(text)) continue;
                back = strtod(text, &end);
                if (*end == '\0' && back == value) { n = candidate; break; }
            }
        }
    } else if (floor(value) == value && fabs(value) <= FPE_JSON_MAX_SAFE) {
        n = snprintf(text, sizeof(text), "%.0f", value);
    } else {
        int precision;
        n = -1;
        for (precision = 1; precision <= 17; ++precision) {
            char *end;
            double back;
            int candidate = snprintf(text, sizeof(text), "%.*g", precision, value);
            if (candidate <= 0 || (size_t)candidate >= sizeof(text)) continue;
            back = strtod(text, &end);
            if (*end == '\0' && back == value) { n = candidate; break; }
        }
    }
    if (n <= 0 || (size_t)n >= sizeof(text)) { b->failed = true; return; }
    buffer_bytes(b, text, (size_t)n);
}

static void canonical_node(JBuffer *b, const JNode *node, CanonContext context, bool as_float) {
    size_t i;
    switch (node->type) {
        case J_NULL: buffer_bytes(b, "null", 4u); break;
        case J_BOOL:
            if (node->boolean_value) buffer_bytes(b, "true", 4u);
            else buffer_bytes(b, "false", 5u);
            break;
        case J_NUMBER: canonical_number(b, node->number, as_float); break;
        case J_STRING: canonical_string(b, node->string); break;
        case J_ARRAY:
            buffer_char(b, '[');
            for (i = 0; i < node->count; ++i) {
                if (i != 0u) buffer_char(b, ',');
                canonical_node(b, node->items[i], context == C_CLUSTERS ? C_CLUSTER : C_OTHER, false);
            }
            buffer_char(b, ']');
            break;
        case J_OBJECT: {
            JMember **order = NULL;
            size_t written = 0u;
            if (node->count != 0u) {
                order = (JMember **)malloc(node->count * sizeof(JMember *));
                if (order == NULL) { b->failed = true; return; }
                for (i = 0; i < node->count; ++i) order[i] = &node->members[i];
                qsort(order, node->count, sizeof(JMember *), member_pointer_compare);
            }
            buffer_char(b, '{');
            for (i = 0; i < node->count; ++i) {
                JMember *member = order[i];
                CanonContext child = C_OTHER;
                if (context == C_ROOT) {
                    if (strcmp(member->key, "layout") == 0) child = C_LAYOUT;
                    else if (strcmp(member->key, "clusters") == 0) child = C_CLUSTERS;
                } else if (context == C_CLUSTER) {
                    if (strcmp(member->key, "state") == 0) child = C_CLUSTER_STATE;
                    else if (strcmp(member->key, "projection") == 0) child = C_CLUSTER_PROJECTION;
                }
                if (context == C_ROOT && strcmp(member->key, "projection_fingerprint") == 0) continue;
                if (written++ != 0u) buffer_char(b, ',');
                canonical_string(b, member->key);
                buffer_char(b, ':');
                canonical_node(b, member->value, child, float_path(context, member->key));
            }
            buffer_char(b, '}');
            free(order);
            break;
        }
    }
}

static uint32_t rotr32(uint32_t x, unsigned n) { return (x >> n) | (x << (32u - n)); }

static void sha_transform(SHA256 *ctx, const unsigned char block[64]) {
    static const uint32_t k[64] = {
        0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,0x3956c25bu,0x59f111f1u,0x923f82a4u,0xab1c5ed5u,
        0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,
        0xe49b69c1u,0xefbe4786u,0x0fc19dc6u,0x240ca1ccu,0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
        0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,0xc6e00bf3u,0xd5a79147u,0x06ca6351u,0x14292967u,
        0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,
        0xa2bfe8a1u,0xa81a664bu,0xc24b8b70u,0xc76c51a3u,0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
        0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,0x391c0cb3u,0x4ed8aa4au,0x5b9cca4fu,0x682e6ff3u,
        0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u
    };
    uint32_t w[64];
    uint32_t v[8];
    size_t i;
    for (i=0;i<16u;++i) {
        size_t j=i*4u;
        w[i]=((uint32_t)block[j]<<24)|((uint32_t)block[j+1u]<<16)|
             ((uint32_t)block[j+2u]<<8)|(uint32_t)block[j+3u];
    }
    for (i=16u;i<64u;++i) {
        uint32_t s0=rotr32(w[i-15u],7u)^rotr32(w[i-15u],18u)^(w[i-15u]>>3);
        uint32_t s1=rotr32(w[i-2u],17u)^rotr32(w[i-2u],19u)^(w[i-2u]>>10);
        w[i]=w[i-16u]+s0+w[i-7u]+s1;
    }
    memcpy(v,ctx->h,sizeof(v));
    for (i=0;i<64u;++i) {
        uint32_t e1=rotr32(v[4],6u)^rotr32(v[4],11u)^rotr32(v[4],25u);
        uint32_t choose=(v[4]&v[5])^((~v[4])&v[6]);
        uint32_t t1=v[7]+e1+choose+k[i]+w[i];
        uint32_t a0=rotr32(v[0],2u)^rotr32(v[0],13u)^rotr32(v[0],22u);
        uint32_t majority=(v[0]&v[1])^(v[0]&v[2])^(v[1]&v[2]);
        uint32_t t2=a0+majority;
        v[7]=v[6]; v[6]=v[5]; v[5]=v[4]; v[4]=v[3]+t1;
        v[3]=v[2]; v[2]=v[1]; v[1]=v[0]; v[0]=t1+t2;
    }
    for (i=0;i<8u;++i) ctx->h[i]+=v[i];
}

static void sha_init(SHA256 *ctx) {
    static const uint32_t initial[8] = {
        0x6a09e667u,0xbb67ae85u,0x3c6ef372u,0xa54ff53au,
        0x510e527fu,0x9b05688cu,0x1f83d9abu,0x5be0cd19u
    };
    memcpy(ctx->h, initial, sizeof(initial)); ctx->total=0u; ctx->used=0u;
}
static void sha_hex(const char *data, size_t length, char output[65]) {
    static const char hex[] = "0123456789abcdef";
    SHA256 ctx;
    unsigned char digest[32];
    unsigned char *padded;
    uint64_t bits = (uint64_t)length * 8u;
    size_t total = ((length + 9u + 63u) / 64u) * 64u;
    size_t offset, i;
    padded = (unsigned char *)calloc(total, 1u);
    if (padded == NULL) {
        output[0] = '\0';
        return;
    }
    if (length != 0u) memcpy(padded, data, length);
    padded[length] = 0x80u;
    for (i = 0; i < 8u; ++i) padded[total - 1u - i] = (unsigned char)(bits >> (i * 8u));
    sha_init(&ctx);
    for (offset = 0u; offset < total; offset += 64u) sha_transform(&ctx, padded + offset);
    free(padded);
    for (i = 0; i < 8u; ++i) {
        digest[i * 4u] = (unsigned char)(ctx.h[i] >> 24);
        digest[i * 4u + 1u] = (unsigned char)(ctx.h[i] >> 16);
        digest[i * 4u + 2u] = (unsigned char)(ctx.h[i] >> 8);
        digest[i * 4u + 3u] = (unsigned char)ctx.h[i];
    }
    for (i = 0; i < 32u; ++i) {
        output[i * 2u] = hex[digest[i] >> 4];
        output[i * 2u + 1u] = hex[digest[i] & 15u];
    }
    output[64] = '\0';
}

static bool canonical_hash(const JNode *root, char output[65], char *error, size_t error_size) {
    JBuffer buffer;
    memset(&buffer,0,sizeof(buffer));
    if (root == NULL || root->type != J_OBJECT) {
        (void)snprintf(error,error_size,"canonical fingerprint input must be a JSON object");
        return false;
    }
    canonical_node(&buffer,root,C_ROOT,false);
    if (buffer.failed) {
        free(buffer.data);
        (void)snprintf(error,error_size,"out of memory or unsupported number during canonicalization");
        return false;
    }
    sha_hex(buffer.data != NULL ? buffer.data : "",buffer.length,output);
    free(buffer.data);
    return true;
}

FPEErrorCode fpe_json_canonical_fingerprint(const char *json, size_t length,
                                             char out_fingerprint[65], FPEError *error) {
    JNode *root;
    char message[FPE_ERROR_CAPACITY];
    fpe_error_clear(error);
    if (out_fingerprint == NULL) {
        json_error(error,FPE_INVALID_PROJECTION,"fingerprint output buffer is required");
        return FPE_INVALID_PROJECTION;
    }
    root=json_parse(json,length,message,sizeof(message));
    if(root==NULL) {
        json_error(error,FPE_INVALID_PROJECTION,message);
        return FPE_INVALID_PROJECTION;
    }
    if(!canonical_hash(root,out_fingerprint,message,sizeof(message))) {
        node_destroy(root); json_error(error,FPE_INVALID_PROJECTION,message); return FPE_INVALID_PROJECTION;
    }
    node_destroy(root);
    return FPE_OK;
}

static bool is_object(const JNode *n) { return n != NULL && n->type == J_OBJECT; }
static bool is_array(const JNode *n) { return n != NULL && n->type == J_ARRAY; }
static bool get_string(const JNode *object,const char *key,const char **out) {
    JNode *n=object_get(object,key);
    if(n==NULL||n->type!=J_STRING) return false;
    *out=n->string; return true;
}
static bool get_number(const JNode *object,const char *key,double *out) {
    JNode *n=object_get(object,key);
    if(n==NULL||n->type!=J_NUMBER||!isfinite(n->number)) return false;
    *out=n->number; return true;
}
static bool get_integer(const JNode *object,const char *key,int64_t *out) {
    JNode *n=object_get(object,key);
    if(n==NULL||n->type!=J_NUMBER||floor(n->number)!=n->number||fabs(n->number)>FPE_JSON_MAX_SAFE) return false;
    *out=(int64_t)n->number; return true;
}
static bool get_required_string(const JNode *object,const char *key,const char **out) {
    return get_string(object,key,out) && (*out)[0] != '\0';
}
static bool expect_text(const JNode *object,const char *key,const char *expected) {
    const char *value;
    return get_string(object,key,&value) && strcmp(value,expected)==0;
}
static bool parse_front_status(const char *s,FPEFrontStatus *out) {
    if(strcmp(s,"quiet")==0) *out=FPE_FRONT_QUIET;
    else if(strcmp(s,"active")==0) *out=FPE_FRONT_ACTIVE;
    else if(strcmp(s,"tense")==0) *out=FPE_FRONT_TENSE;
    else if(strcmp(s,"volatile")==0) *out=FPE_FRONT_VOLATILE;
    else return false;
    return true;
}

void fpe_projection_json_destroy(FPEProjection *projection) {
    size_t i,j;
    if(projection==NULL) return;
    for(i=0;projection->clusters!=NULL&&i<projection->cluster_count;++i) {
        FPECluster *c=(FPECluster *)&projection->clusters[i];
        free((void *)c->id); free((void *)c->territory_id);
        if(c->front_ids!=NULL) {
            for(j=0;j<c->front_count;++j) free((void *)c->front_ids[j]);
        }
        free((void *)c->front_ids);
        for(j=0;j<FPE_BUDS_PER_CLUSTER;++j) {
            free((void *)c->buds[j].id); free((void *)c->buds[j].seed_key);
        }
    }
    free((void *)projection->clusters);
    free((void *)projection->schema); free((void *)projection->mode);
    free((void *)projection->projection_fingerprint);
    free((void *)projection->pixelgen_world_fingerprint);
    free((void *)projection->json_document);
    memset(projection,0,sizeof(*projection));
}

static bool parse_safe_int(const JNode *n,int64_t *out) {
    if(n==NULL||n->type!=J_NUMBER||floor(n->number)!=n->number||fabs(n->number)>FPE_JSON_MAX_SAFE) return false;
    *out=(int64_t)n->number; return true;
}
static bool parse_range(const JNode *o,const char *key,double lo,double hi,double *out) {
    return get_number(o,key,out) && *out>=lo && *out<=hi;
}
static bool parse_summary(const JNode *summary,FPEProjection *p) {
    int64_t values[6];
    static const char *keys[6]={"cluster_count","bud_count","territory_cluster_count","front_cluster_count","straight_bud_count","curved_bud_count"};
    size_t i;
    for(i=0;i<6u;++i) if(!get_integer(summary,keys[i],&values[i])||values[i]<0) return false;
    p->summary.cluster_count=(uint64_t)values[0];
    p->summary.bud_count=(uint64_t)values[1];
    p->summary.territory_cluster_count=(uint64_t)values[2];
    p->summary.front_cluster_count=(uint64_t)values[3];
    p->summary.straight_bud_count=(uint64_t)values[4];
    p->summary.curved_bud_count=(uint64_t)values[5];
    return true;
}

static bool parse_projection_tree(const JNode *root,FPEProjection *out,char *message,size_t message_size) {
    const JNode *source=object_get(root,"source"),*layout=object_get(root,"layout");
    const JNode *authority=object_get(root,"authority"),*hierarchy=object_get(root,"hierarchy");
    const JNode *dims,*clusters,*summary,*levels;
    const char *text;
    int64_t seed,revision,tick,cols,rows,buds_per_sector;
    double spacing,offset;
    size_t i,j;
    FPEProjection p;
    memset(&p,0,sizeof(p));
#define BAD(msg) do { (void)snprintf(message,message_size,"%s",(msg)); goto fail; } while(0)
    if(root==NULL||root->type!=J_OBJECT||!is_object(source)||!is_object(layout)||
       !is_object(authority)||!is_object(hierarchy)) BAD("missing projection contract objects");
    if(!expect_text(root,"schema",FPE_PROJECTION_SCHEMA)||!expect_text(root,"fpe_version","0.6.0")||
       !expect_text(root,"bridge_version","0.6.0")||
       !expect_text(root,"mode","read_only_hierarchical_projection")) BAD("unsupported projection schema or mode");
    if(!expect_text(authority,"objective_state_owner","PixelGen")||
       !expect_text(authority,"geometry_owner","FPE")||
       !expect_text(authority,"writeback","disabled_in_v0.6")) BAD("invalid projection authority");
    if(!expect_text(hierarchy,"schema",FPE_VIEW_SCHEMA)||
       !expect_text(hierarchy,"initial_detail","cluster_proxy")||
       !expect_text(hierarchy,"expansion_state_owner","viewer")||
       !expect_text(hierarchy,"semantic_effect","none")) BAD("invalid hierarchy contract");
    levels=object_get(hierarchy,"levels");
    if(!is_array(levels)||levels->count!=4u||
       levels->items[0]->type!=J_STRING||strcmp(levels->items[0]->string,"world")!=0||
       levels->items[1]->type!=J_STRING||strcmp(levels->items[1]->string,"cluster")!=0||
       levels->items[2]->type!=J_STRING||strcmp(levels->items[2]->string,"bud")!=0||
       levels->items[3]->type!=J_STRING||strcmp(levels->items[3]->string,"geometry")!=0) BAD("invalid hierarchy levels");
    if(!get_integer(source,"seed",&seed)||!get_integer(source,"state_revision",&revision)||
       !get_integer(source,"state_tick",&tick)||revision<0||tick<0) BAD("invalid source seed or clock");
    dims=object_get(source,"dimensions");
    if(!is_array(dims)||dims->count!=2u||!parse_safe_int(dims->items[0],&cols)||
       !parse_safe_int(dims->items[1],&rows)||cols<1||rows<1||
       cols>(int64_t)UINT32_MAX||rows>(int64_t)UINT32_MAX) BAD("invalid source dimensions");
    if((uint64_t)cols*(uint64_t)rows>FPE_JSON_MAX_CLUSTERS) BAD("projection exceeds C cluster capacity");
    if(!get_number(layout,"sector_spacing",&spacing)||spacing<0.001||spacing>1000000.0||
       !get_number(layout,"local_bud_offset",&offset)||offset<0.001||offset>1000000.0||
       !get_integer(layout,"buds_per_sector",&buds_per_sector)||buds_per_sector!=(int64_t)FPE_BUDS_PER_CLUSTER||
       !expect_text(layout,"cluster_kind","pixelgen_sector")) BAD("invalid projection layout");
    if(!get_required_string(source,"pixelgen_world_fingerprint",&text)||strlen(text)!=64u) BAD("invalid PixelGen world fingerprint");
    for(i=0;i<64u;++i) if(!((text[i]>='0'&&text[i]<='9')||(text[i]>='a'&&text[i]<='f'))) BAD("invalid PixelGen world fingerprint");
    if(!get_required_string(root,"projection_fingerprint",&text)||strlen(text)!=64u) BAD("invalid projection fingerprint");
    for(i=0;i<64u;++i) if(!((text[i]>='0'&&text[i]<='9')||(text[i]>='a'&&text[i]<='f'))) BAD("invalid projection fingerprint");

    p.schema=json_copy_string(FPE_PROJECTION_SCHEMA);
    p.mode=json_copy_string("read_only_hierarchical_projection");
    p.projection_fingerprint=json_copy_string(text);
    text=NULL;
    (void)get_string(source,"pixelgen_world_fingerprint",&text);
    p.pixelgen_world_fingerprint=json_copy_string(text);
    p.seed=seed; p.columns=(uint32_t)cols; p.rows=(uint32_t)rows;
    p.state_revision=(uint64_t)revision; p.state_tick=(uint64_t)tick;
    p.sector_spacing=spacing; p.local_bud_offset=offset;
    if(p.schema==NULL||p.mode==NULL||p.projection_fingerprint==NULL||p.pixelgen_world_fingerprint==NULL)
        BAD("out of memory copying projection identity");
    clusters=object_get(root,"clusters");
    if(!is_array(clusters)||(uint64_t)clusters->count!=(uint64_t)cols*(uint64_t)rows) BAD("cluster count does not match source dimensions");
    p.cluster_count=clusters->count;
    p.clusters=(FPECluster *)calloc(p.cluster_count,sizeof(FPECluster));
    if(p.clusters==NULL) BAD("out of memory allocating projection clusters");
    for(i=0;i<p.cluster_count;++i) {
        const JNode *c=clusters->items[i],*sector,*state,*metrics,*source_meta,*fronts,*buds;
        FPECluster *dst=(FPECluster *)&p.clusters[i];
        int64_t sx,sy;
        const char *status;
        if(!is_object(c)||!is_object(object_get(c,"state"))||!is_object(object_get(c,"projection"))||
           !is_object(object_get(c,"source"))) BAD("invalid cluster object structure");
        sector=object_get(c,"sector");
        if(!is_array(sector)||sector->count!=2u||!parse_safe_int(sector->items[0],&sx)||
           !parse_safe_int(sector->items[1],&sy)||sx<0||sy<0||sx>=cols||sy>=rows) BAD("invalid cluster sector coordinates");
        if(!get_required_string(c,"id",&text)) BAD("invalid cluster id");
        dst->id=json_copy_string(text);
        dst->sector_x=(uint32_t)sx; dst->sector_y=(uint32_t)sy;
        state=object_get(c,"state"); metrics=object_get(c,"projection"); source_meta=object_get(c,"source");
        if(dst->id==NULL) BAD("out of memory copying cluster id");
        if(!parse_range(state,"control_strength",0.0,1.75,&dst->state.control_strength)||
           !parse_range(state,"stability",0.0,1.0,&dst->state.stability)||
           !parse_range(state,"alert",0.0,1.0,&dst->state.alert)||
           !parse_range(state,"front_tension",0.0,1.0,&dst->state.front_tension)||
           !parse_range(state,"front_activity",0.0,1.0,&dst->state.front_activity)||
           !get_required_string(state,"front_status",&status)||!parse_front_status(status,&dst->state.front_status)) BAD("invalid cluster state");
        if(!parse_range(metrics,"cohesion",0.0,1.0,&dst->projection.cohesion)||
           !parse_range(metrics,"breakup_resistance",0.0,1.0,&dst->projection.breakup_resistance)||
           !parse_range(metrics,"agitation",0.0,1.0,&dst->projection.agitation)||
           !parse_range(metrics,"collapse_bias",0.0,1.0,&dst->projection.collapse_bias)||
           !parse_range(metrics,"damage_proxy",0.0,1.0,&dst->projection.damage_proxy)||
           !parse_range(metrics,"update_rate",0.0,1.0,&dst->projection.update_rate)) BAD("invalid cluster projection metrics");
        fronts=object_get(source_meta,"front_ids");
        if(!is_array(fronts)) BAD("invalid source.front_ids");
        dst->front_count=fronts->count;
        if(dst->front_count!=0u) {
            const char **front_list=(const char **)calloc(dst->front_count,sizeof(char *));
            if(front_list==NULL) BAD("out of memory allocating front ids");
            dst->front_ids=front_list;
            for(j=0;j<dst->front_count;++j) {
                if(fronts->items[j]->type!=J_STRING||fronts->items[j]->string[0]=='\0') BAD("invalid front id");
                front_list[j]=json_copy_string(fronts->items[j]->string);
                if(front_list[j]==NULL) BAD("out of memory copying front id");
            }
        }
        {
            JNode *territory=(JNode *)object_get(source_meta,"territory_id");
            if(territory==NULL||(territory->type!=J_NULL&&territory->type!=J_STRING)) BAD("invalid territory id");
            if(territory->type==J_STRING) {
                if(territory->string[0]=='\0') BAD("empty territory id");
                dst->territory_id=json_copy_string(territory->string);
                if(dst->territory_id==NULL) BAD("out of memory copying territory id");
            }
        }
        buds=object_get(c,"buds");
        if(!is_array(buds)||buds->count!=FPE_BUDS_PER_CLUSTER) BAD("each cluster must contain four buds");
        for(j=0;j<FPE_BUDS_PER_CLUSTER;++j) {
            const JNode *b=buds->items[j],*bud_offset;
            FPEBud *bd=&dst->buds[j];
            int64_t index,ox,oz;
            const char *type;
            if(!is_object(b)||!get_required_string(b,"id",&text)) BAD("invalid bud object or id");
            bd->id=json_copy_string(text);
            if(bd->id==NULL) BAD("out of memory copying bud id");
            if(!get_integer(b,"index",&index)||index!=(int64_t)j||
               !get_required_string(b,"seed_key",&text)) BAD("invalid bud index or seed key");
            bd->index=(uint32_t)index; bd->seed_key=json_copy_string(text);
            if(bd->seed_key==NULL) BAD("out of memory copying bud seed key");
            if(!get_required_string(b,"type",&type)) BAD("invalid bud type");
            if(strcmp(type,"STRAIGHT")==0) bd->type=FPE_BUD_STRAIGHT;
            else if(strcmp(type,"CURVED")==0) bd->type=FPE_BUD_CURVED;
            else BAD("unknown bud type");
            bud_offset=object_get(b,"offset");
            if(!is_array(bud_offset)||bud_offset->count!=2u||
               !parse_safe_int(bud_offset->items[0],&ox)||!parse_safe_int(bud_offset->items[1],&oz)) BAD("invalid bud offset");
            {
                static const int32_t expected[4][2]={{-1,-1},{1,-1},{-1,1},{1,1}};
                if(ox!=expected[j][0]||oz!=expected[j][1]) BAD("noncanonical bud offset");
                bd->offset_x=(int32_t)ox; bd->offset_z=(int32_t)oz;
            }
        }
    }
    summary=object_get(root,"summary");
    if(!parse_summary(summary,&p)) BAD("invalid projection summary");
    {
        FPEError validation_error;
        if(fpe_projection_validate(&p,&validation_error)!=FPE_OK) {
            (void)snprintf(message,message_size,"%s",validation_error.message);
            goto fail;
        }
    }
    *out=p;
#undef BAD
    return true;
fail:
    fpe_projection_json_destroy(&p);
#undef BAD
    return false;
}

FPEErrorCode fpe_projection_from_json(const char *json,size_t length,
                                      FPEProjection *out_projection,FPEError *error) {
    JNode *root;
    char message[FPE_ERROR_CAPACITY],fingerprint[65];
    const char *expected;
    FPEProjection projection;
    fpe_error_clear(error);
    if(out_projection==NULL) {
        json_error(error,FPE_INVALID_PROJECTION,"projection output pointer is required");
        return FPE_INVALID_PROJECTION;
    }
    memset(out_projection,0,sizeof(*out_projection));
    memset(&projection,0,sizeof(projection));
    root=json_parse(json,length,message,sizeof(message));
    if(root==NULL) {
        json_error(error,FPE_INVALID_PROJECTION,message);
        return FPE_INVALID_PROJECTION;
    }
    if(!canonical_hash(root,fingerprint,message,sizeof(message))) {
        node_destroy(root); json_error(error,FPE_INVALID_PROJECTION,message); return FPE_INVALID_PROJECTION;
    }
    if(!get_required_string(root,"projection_fingerprint",&expected)||strcmp(expected,fingerprint)!=0) {
        node_destroy(root); json_error(error,FPE_INVALID_PROJECTION,"projection_fingerprint mismatch");
        return FPE_INVALID_PROJECTION;
    }
    if(!parse_projection_tree(root,&projection,message,sizeof(message))) {
        node_destroy(root); json_error(error,FPE_INVALID_PROJECTION,message); return FPE_INVALID_PROJECTION;
    }
    projection.json_document=(const char *)malloc(length+1u);
    if(projection.json_document==NULL) {
        node_destroy(root); fpe_projection_json_destroy(&projection);
        json_error(error,FPE_INVALID_PROJECTION,"out of memory retaining verified projection JSON");
        return FPE_INVALID_PROJECTION;
    }
    memcpy((char *)projection.json_document,json,length);
    ((char *)projection.json_document)[length]='\\0';
    projection.json_document_length=length;
    node_destroy(root);
    *out_projection=projection;
    return FPE_OK;
}
