#include "harness.h"

/* Case 1: Read a[24] past a 24-byte allocation; control reads a[23].
 * Pool alignment slack hides the read unless annotated. */
ST_CASE(1) {
    unsigned char *a = st_alloc(24);
    unsigned char *b = st_alloc(24);
    memset(a, ST_FILL, 24);
    memset(b, ST_FILL, 24);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    st_sink(a[23]);            /* last valid byte */
#else
    st_sink(a[24]);            /* the defect: one past the end */
#endif
    st_free(b);
    st_free(a);
}
