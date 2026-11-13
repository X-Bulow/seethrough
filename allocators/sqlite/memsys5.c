/* SQLite's built-in memsys5 allocator, reached through the public API. */
#include <stdint.h>
#include <stdlib.h>
#include "alloc.h"
#include "sqlite3.h"
#include "st_annot.h"

#define ST_SQLITE_HEAP (1u << 20)
static void *heap;
static size_t heap_bytes;
static int initialized;
typedef struct {
    void *ptr;
    size_t requested;
    size_t rounded;
    int live;
} st_sqlite_object;
static st_sqlite_object *objects;
static size_t object_count, object_capacity;

static st_sqlite_object *find_object(void *p) {
    for (size_t i = object_count; i > 0; --i) {
        if (objects[i - 1].ptr == p) return &objects[i - 1];
    }
    return NULL;
}
static int reserve_object(void) {
    if (object_count < object_capacity) return 1;
    size_t next = object_capacity ? object_capacity * 2 : 64;
    if (next < object_capacity || next > SIZE_MAX / sizeof(*objects)) return 0;
    st_sqlite_object *grown = realloc(objects, next * sizeof(*objects));
    if (!grown) return 0;
    objects = grown;
    object_capacity = next;
    return 1;
}

void st_alloc_init(size_t bytes) {
    if (heap) st_alloc_fini();
    if (!bytes) bytes = ST_SQLITE_HEAP;
    if (bytes > INT32_MAX) return;
    heap = malloc(bytes);
    if (!heap) return;
    if (sqlite3_config(SQLITE_CONFIG_HEAP, heap, (int)bytes, 16) != SQLITE_OK ||
        sqlite3_initialize() != SQLITE_OK) {
        sqlite3_shutdown();
        free(heap);
        heap = NULL;
        return;
    }
    heap_bytes = bytes;
    initialized = 1;
}

void *st_alloc(size_t n) {
    if (!initialized || !n || !reserve_object()) return NULL;
    void *p = sqlite3_malloc64(n);
    if (!p) return NULL;
    size_t rounded = (size_t)sqlite3_msize(p);
    objects[object_count++] = (st_sqlite_object){p, n, rounded, 1};
    if (rounded > n) {
        ST_POISON((unsigned char *)p + n, rounded - n);
        ST_NOACCESS((unsigned char *)p + n, rounded - n);
    }
    return p;
}
void st_free(void *p) {
    if (!initialized) return;
    st_sqlite_object *obj = find_object(p);
    if (obj && obj->live) {
        if (obj->rounded > obj->requested) {
            ST_UNPOISON((unsigned char *)p + obj->requested,
                        obj->rounded - obj->requested);
            ST_DEFINED((unsigned char *)p + obj->requested,
                       obj->rounded - obj->requested);
        }
        obj->live = 0;
    }
    sqlite3_free(p);
}
void *st_realloc(void *p, size_t n) {
    if (!initialized) return NULL;
    if (!p) return st_alloc(n);
    if (!n) { st_free(p); return NULL; }
    if (!reserve_object()) return NULL;
    st_sqlite_object *old = find_object(p);
    if (!old || !old->live) return NULL;
    size_t old_requested = old->requested;
    size_t old_rounded = old->rounded;
    if (old_rounded > old_requested) {
        ST_UNPOISON((unsigned char *)p + old_requested,
                    old_rounded - old_requested);
        ST_DEFINED((unsigned char *)p + old_requested,
                   old_rounded - old_requested);
    }
    void *next = sqlite3_realloc64(p, n);
    if (!next) {
        if (old_rounded > old_requested) {
            ST_POISON((unsigned char *)p + old_requested, old_rounded - old_requested);
            ST_NOACCESS((unsigned char *)p + old_requested, old_rounded - old_requested);
        }
        return NULL;
    }
    old->live = 0;
    size_t rounded = (size_t)sqlite3_msize(next);
    ST_UNPOISON(next, rounded);
    objects[object_count++] = (st_sqlite_object){next, n, rounded, 1};
    if (rounded > n) {
        ST_POISON((unsigned char *)next + n, rounded - n);
        ST_NOACCESS((unsigned char *)next + n, rounded - n);
    }
    return next;
}
void st_alloc_fini(void) {
    if (!heap) return;
    sqlite3_shutdown();
    free(heap);
    free(objects);
    heap = NULL;
    heap_bytes = 0;
    initialized = 0;
    objects = NULL;
    object_count = object_capacity = 0;
}
const char *st_alloc_name(void) { return "memsys5"; }
size_t st_alloc_pool_bytes(void) { return heap_bytes; }
