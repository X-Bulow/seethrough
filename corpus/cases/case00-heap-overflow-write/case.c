#include "harness.h"

/* Case 0 -- heap overflow, write, 1 byte past the end.
 *
 * Two 24-byte objects allocated back to back. The defect writes a[24], which
 * under malloc lands in the allocator's padding / ASan redzone, and under an
 * arena lands in b[0] (or in b's header, if the arena has one).
 *
 * NEGATIVE CONTROL (-DST_NEGATIVE_CONTROL): the same two allocations, the same
 * memset, and the write goes to a[23] -- the last valid byte -- instead. */
ST_CASE(0) {
    unsigned char *a = st_alloc(24);
    unsigned char *b = st_alloc(24);
    memset(a, ST_FILL, 24);
    memset(b, ST_FILL, 24);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    a[23] = 1;                 /* last valid byte */
#else
    a[24] = 1;                 /* the defect: one past the end */
#endif
    st_sink(b[0]);             /* b stays live and observed */
    st_free(b);
    st_free(a);
}
