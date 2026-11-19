#include "harness.h"

/* Case 10: Write through a stale pointer after immediate slot reuse; control uses the live pointer.
 * Requires reuse=1. Poisoning permits the live slot; fresh tags can reject the stale pointer. */
ST_CASE(10) {
    unsigned char *a = st_alloc(24);
    memset(a, ST_FILL, 24);
    st_free(a);
    unsigned char *b = st_alloc(24);
    memset(b, 0x11, 24);
    printf("ST NOTE reuse=%d\n", (int)st_same_address(b, a));
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    b[0] = 0x22;               /* through the live pointer */
#else
    a[0] = 0x22;               /* the defect: through the stale one, into b's data */
#endif
    st_sink(b[0]);
    st_free(b);
}
