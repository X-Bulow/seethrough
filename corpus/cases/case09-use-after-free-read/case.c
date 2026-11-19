#include "harness.h"

/* Case 9: Read after free without reuse; control reads before free.
 * Pool storage remains addressable unless the freed object is annotated. */
ST_CASE(9) {
    unsigned char *a = st_alloc(24);
    memset(a, ST_FILL, 24);
#ifdef ST_NEGATIVE_CONTROL
    ST_READY();
    st_sink(a[0]);             /* while still live */
    st_free(a);
#else
    st_free(a);
    ST_READY();
    st_sink(a[0]);             /* the defect: after the free */
#endif
}
