#include "harness.h"

/* Case 15: Free a stale pointer after reuse, then read the live object; control frees through its live pointer.
 * Requires reuse=1. The bad free closes the live slot, exposing the subsequent read. */
ST_CASE(15) {
    unsigned char *a = st_alloc(24);
    memset(a, ST_FILL, 24);
    st_free(a);
    unsigned char *b = st_alloc(24);
    memset(b, 0x11, 24);
    printf("ST NOTE reuse=%d\n", (int)st_same_address(b, a));
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    st_free(b);                /* the live object's own pointer */
#else
    st_free(a);                /* the defect: frees b's storage while b is live */
    st_sink(b[0]);             /* b is now a freed block */
#endif
}
