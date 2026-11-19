#include "harness.h"

/* Case 4: Read beyond the backing pool; control reads within the object.
 * Detection depends on the target mapping, not logical object tracking. */
ST_CASE(4) {
    size_t pool = st_alloc_pool_bytes();
    size_t off = pool ? pool + 8192 : 24;
    unsigned char *a = st_alloc(24);
    memset(a, ST_FILL, 24);
    printf("ST NOTE pool_bytes=%zu offset=%zu\n", pool, off);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    st_sink(a[23]);            /* last valid byte */
#else
    st_sink(a[off]);           /* the defect: outside the container, not just the object */
#endif
    st_free(a);
}
