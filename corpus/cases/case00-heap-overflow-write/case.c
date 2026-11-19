#include "harness.h"

/* Case 0: Write a[24] past a 24-byte allocation; control writes a[23].
 * Pool alignment slack hides the overflow unless annotated. */
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
