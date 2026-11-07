/* Bump arena: objects live in one backing block; bookkeeping stays outside it. */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "alloc.h"
#include "st_annot.h"

#define ST_ARENA_DEFAULT (1u << 20)
#define ST_ALIGN 16u

typedef struct {
    void *ptr;
    size_t size;
    int live;
} st_object;

static unsigned char *base, *cur, *end;
static size_t pool_bytes;
static st_object *objects;
static size_t object_count, object_capacity;

static st_object *find_object(void *p) {
    for (size_t i = object_count; i > 0; --i) {
        if (objects[i - 1].ptr == p) return &objects[i - 1];
    }
    return NULL;
}

static int reserve_object(void) {
    if (object_count < object_capacity) return 1;
    size_t next = object_capacity ? object_capacity * 2 : 64;
    if (next < object_capacity || next > SIZE_MAX / sizeof(*objects)) return 0;
    st_object *grown = realloc(objects, next * sizeof(*objects));
    if (!grown) return 0;
    objects = grown;
    object_capacity = next;
    return 1;
}

void st_alloc_init(size_t bytes) {
    if (base) st_alloc_fini();
    if (bytes == 0) bytes = ST_ARENA_DEFAULT;
    base = malloc(bytes);
    if (!base) return;
    cur = base;
    end = base + bytes;
    pool_bytes = bytes;
    ST_POISON(base, bytes);
    ST_POOL_CREATE(base, 0, 0);
    ST_NOACCESS(base, bytes);
}
void *st_alloc(size_t n) {
    if (!base || n == 0 || n > SIZE_MAX - (ST_ALIGN - 1)) return NULL;
    size_t rounded = (n + ST_ALIGN - 1) & ~(size_t)(ST_ALIGN - 1);
    if ((size_t)(end - cur) < rounded || !reserve_object()) return NULL;
    void *p = cur;
    cur += rounded;
    objects[object_count++] = (st_object){p, n, 1};
    ST_UNPOISON(p, n);
    ST_POOL_ALLOC(base, p, n);
    return p;
}
void st_free(void *p) {
    if (!p || !base) return;
    st_object *obj = find_object(p);
    if (obj && obj->live) {
        ST_POISON(p, obj->size);
        obj->live = 0;
    }
    /* Also pass invalid and repeated frees to Memcheck's ownership model. */
    ST_POOL_FREE(base, p);
}
void *st_realloc(void *p, size_t n) {
    if (!p) return st_alloc(n);
    if (n == 0) {
        st_free(p);
        return NULL;
    }
    st_object *old = find_object(p);
    if (!old || !old->live) return NULL;
    size_t old_size = old->size;
    void *next = st_alloc(n);
    if (!next) return NULL;
    memcpy(next, p, old_size < n ? old_size : n);
    st_free(p);
    return next;
}
void st_alloc_fini(void) {
    if (!base) return;
    ST_POOL_DESTROY(base);
    ST_UNPOISON(base, pool_bytes);
    free(base);
    free(objects);
    base = cur = end = NULL;
    pool_bytes = 0;
    objects = NULL;
    object_count = object_capacity = 0;
}
const char *st_alloc_name(void) { return "arena"; }
size_t st_alloc_pool_bytes(void) { return pool_bytes; }
