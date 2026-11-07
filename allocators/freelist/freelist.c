/* Fixed size-class free lists carved from one backing block. */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "alloc.h"
#include "st_annot.h"

#define ST_FREELIST_DEFAULT (1u << 20)
#define ST_ALIGN 16u
#define ST_CLASSES 4

static const size_t class_sizes[ST_CLASSES] = {32, 64, 128, 256};

typedef struct {
    void *ptr;
    size_t requested;
    size_t slot_size;
    int class_index;              /* -1 for a large, non-recycled slot */
    int live;
} st_slot;

static unsigned char *base, *cur, *end;
static size_t pool_bytes;
static void *heads[ST_CLASSES];
static st_slot *slots;
static size_t slot_count, slot_capacity;

static int class_for(size_t n) {
    for (int i = 0; i < ST_CLASSES; ++i) {
        if (n <= class_sizes[i]) return i;
    }
    return -1;
}

static st_slot *find_exact(void *p) {
    for (size_t i = slot_count; i > 0; --i) {
        if (slots[i - 1].ptr == p) return &slots[i - 1];
    }
    return NULL;
}

static st_slot *find_containing(void *p) {
    uintptr_t q = (uintptr_t)p;
    for (size_t i = slot_count; i > 0; --i) {
        uintptr_t start = (uintptr_t)slots[i - 1].ptr;
        if (q >= start && q - start < slots[i - 1].slot_size) return &slots[i - 1];
    }
    return NULL;
}

static int reserve_slot(void) {
    if (slot_count < slot_capacity) return 1;
    size_t next = slot_capacity ? slot_capacity * 2 : 64;
    if (next < slot_capacity || next > SIZE_MAX / sizeof(*slots)) return 0;
    st_slot *grown = realloc(slots, next * sizeof(*slots));
    if (!grown) return 0;
    slots = grown;
    slot_capacity = next;
    return 1;
}

void st_alloc_init(size_t bytes) {
    if (base) st_alloc_fini();
    if (bytes == 0) bytes = ST_FREELIST_DEFAULT;
    base = malloc(bytes);
    if (!base) return;
    cur = base;
    end = base + bytes;
    pool_bytes = bytes;
    memset(heads, 0, sizeof(heads));
    ST_POISON(base, bytes);
    ST_POOL_CREATE(base, 0, 0);
    ST_NOACCESS(base, bytes);
}

void *st_alloc(size_t n) {
    if (!base || n == 0) return NULL;
    int klass = class_for(n);
    if (n > SIZE_MAX - (ST_ALIGN - 1)) return NULL;
    size_t slot_size = klass >= 0 ? class_sizes[klass]
                                  : (n + ST_ALIGN - 1) & ~(size_t)(ST_ALIGN - 1);
    void *p;
    st_slot *slot;
    if (klass >= 0 && heads[klass]) {
        p = heads[klass];
        /* The next link is stored inside the freed slot. Open only that word. */
        ST_UNPOISON(p, sizeof(void *));
        ST_DEFINED(p, sizeof(void *));
        heads[klass] = *(void **)p;
        ST_POISON(p, slot_size);
        ST_NOACCESS(p, slot_size);
        slot = find_exact(p);
        if (!slot) {
            if (!reserve_slot()) return NULL;
            slot = &slots[slot_count++];
            *slot = (st_slot){p, n, slot_size, klass, 0};
        }
    } else {
        if ((size_t)(end - cur) < slot_size || !reserve_slot()) return NULL;
        p = cur;
        cur += slot_size;
        slot = &slots[slot_count++];
        *slot = (st_slot){p, n, slot_size, klass, 0};
    }
    slot->requested = n;
    slot->live = 1;
    ST_POOL_ALLOC(base, p, n);
    ST_UNPOISON(p, n);
    return p;
}

void st_free(void *p) {
    if (!p || !base) return;
    st_slot *slot = find_exact(p);
    if (!slot) slot = find_containing(p); /* an interior free corrupts the list */
    if (!slot) {
        ST_POOL_FREE(base, p);            /* Memcheck can still report invalid ownership */
        return;
    }
    if (slot->class_index >= 0) {
        /* A short request may leave the link word inside poisoned slack. */
        ST_UNPOISON(p, sizeof(void *));
        ST_DEFINED(p, sizeof(void *));
        *(void **)p = heads[slot->class_index];
        heads[slot->class_index] = p;
    }
    if (slot->ptr == p) slot->live = 0;
    ST_POOL_FREE(base, p);
    if (slot->ptr == p) ST_POISON(p, slot->slot_size);
    else ST_NOACCESS(p, sizeof(void *));
}

void *st_realloc(void *p, size_t n) {
    if (!p) return st_alloc(n);
    if (n == 0) {
        st_free(p);
        return NULL;
    }
    st_slot *old = find_exact(p);
    if (!old || !old->live) return NULL;
    size_t old_size = old->requested;
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
    free(slots);
    base = cur = end = NULL;
    pool_bytes = 0;
    slots = NULL;
    slot_count = slot_capacity = 0;
    memset(heads, 0, sizeof(heads));
}

const char *st_alloc_name(void) { return "freelist"; }
size_t st_alloc_pool_bytes(void) { return pool_bytes; }
