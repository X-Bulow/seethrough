/* Arena: one block from malloc, bump-pointer allocation, free is a no-op.
 * TODO(B1.2): implement. Keep the layout facts in README.md true. */
#include <stdlib.h>
#include <stdint.h>
#include "alloc.h"
#include "st_annot.h"

#define ST_ARENA_DEFAULT (1u << 20)
#define ST_ALIGN 16

static unsigned char *base, *cur, *end;

void st_alloc_init(size_t bytes) {
    if (bytes == 0) bytes = ST_ARENA_DEFAULT;
    base = cur = malloc(bytes);
    end = base + bytes;
    ST_POISON(base, bytes);                      /* nothing is live yet */
    ST_POOL_CREATE(base, 0, 0);
}
void *st_alloc(size_t n) {
    size_t rounded = (n + ST_ALIGN - 1) & ~(size_t)(ST_ALIGN - 1);
    if ((size_t)(end - cur) < rounded) return NULL;
    void *p = cur;
    cur += rounded;
    ST_UNPOISON(p, n);                           /* exactly n, not rounded: the slack stays poisoned */
    ST_POOL_ALLOC(base, p, n);
    return p;
}
void st_free(void *p) {
    (void)p;                                     /* an arena does not free; TODO(B2): size is unknown here --
                                                    either keep a header or a side table so the annotated
                                                    arm can re-poison exactly the object */
}
void *st_realloc(void *p, size_t n) { (void)p; (void)n; return NULL; /* TODO(B1.2) */ }
void st_alloc_fini(void) {
    if (!base) return;                           /* idempotent: case 12 calls it, then main does */
    ST_POOL_DESTROY(base);
    ST_UNPOISON(base, (size_t)(end - base));     /* hand the block back clean */
    free(base);
    base = cur = end = NULL;
}
const char *st_alloc_name(void) { return "arena"; }
size_t      st_alloc_pool_bytes(void) { return (size_t)(end - base); }
