#include "harness.h"

/* Case 12: Read after pool destruction; control reads before destruction.
 * Requires pool=1; malloc has no pool. Finalization must tolerate the harness calling it again. */
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
