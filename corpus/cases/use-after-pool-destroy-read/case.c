#include "harness.h"

/* Case 12 -- use after free, read, after the whole pool's lifetime ended.
 *
 * The temporal defect that only exists because of the custom allocator. The
 * object is never freed individually; the pool it lives in is released in one
 * go, and a pointer into it survives. This is PostgreSQL's
 * MemoryContextReset, Apache's apr_pool_destroy and every arena's "free
 * everything at the end of the request": the idiom that makes arenas attractive
 * is exactly the one that creates this bug, and no amount of per-object
 * bookkeeping in the allocator is involved, because there was none.
 *
 * For an arena the entire backing block goes back to malloc, so the stale read
 * is an ordinary use-after-free OF THE POOL and malloc-granular tools report
 * it. That asymmetry is the point: an arena hides accesses inside its pool and
 * exposes accesses after its pool.
 *
 * There is no pool to destroy under malloc, where st_alloc_fini is a no-op and
 * the object simply stays live -- the read is then legitimate and the case has
 * tested nothing. "ST NOTE pool=1" says a pool existed, and case.json's
 * `requires` makes the malloc column UNSUPPORTED rather than a miss. The malloc
 * equivalent of ending this object's lifetime is st_free, which is case 9.
 *
 * st_alloc_fini is called here and again by harness/main.c, so every allocator
 * must make it idempotent (alloc.h).
 *
 * NEGATIVE CONTROL: the read happens before the pool is destroyed. */
ST_CASE(12) {
    unsigned char *a = st_alloc(24);
    memset(a, ST_FILL, 24);
    printf("ST NOTE pool=%d\n", (int)(st_alloc_pool_bytes() > 0));
#ifdef ST_NEGATIVE_CONTROL
    ST_READY();
    st_sink(a[0]);             /* while the pool is alive */
    st_alloc_fini();
#else
    st_alloc_fini();           /* the pool's lifetime ends; a was never freed */
    ST_READY();
    st_sink(a[0]);             /* the defect */
#endif
}
