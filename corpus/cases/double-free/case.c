#include "harness.h"

/* Case 13 -- double free.
 *
 * Two objects, two frees in both images: the control frees a then b, the defect
 * frees a then a again and leaves b to the pool teardown. Keeping the free
 * COUNT equal matters, because a tool that reports on free-call number three
 * and not number two would otherwise look like a detector.
 *
 * What makes this interesting under a custom allocator is that the defect may
 * not be a defect at all down there. A bump-pointer arena reclaims nothing on
 * st_free; ours only clears a liveness flag in its side table (B1.2), so the
 * second free finds the object dead, corrupts nothing and is invisible to any
 * tool that watches accesses -- the program still violates the allocator's
 * contract, but the allocator has no state to corrupt. Only an ownership
 * interface sees it: the annotated arena hands every st_free to
 * VALGRIND_MEMPOOL_FREE. A free list, by contrast, pushes the same block twice and
 * is now committed to handing one address out to two callers, which is case 15.
 *
 * NEGATIVE CONTROL: frees b instead of a the second time. */
ST_CASE(13) {
    unsigned char *a = st_alloc(24);
    unsigned char *b = st_alloc(24);
    memset(a, ST_FILL, 24);
    memset(b, ST_FILL, 24);
    st_free(a);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    st_free(b);                /* the other live object */
#else
    st_free(a);                /* the defect: a again. b is left to st_alloc_fini */
#endif
}
