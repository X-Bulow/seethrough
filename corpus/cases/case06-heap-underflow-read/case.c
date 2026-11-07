#include "harness.h"

/* Case 6 -- heap underflow, read, 1 byte before the start. Case 5's twin;
 * see that file for why the two sides of an object are not symmetric.
 *
 * NEGATIVE CONTROL: reads a[0]. */
ST_CASE(6) {
    unsigned char *first = st_alloc(24);
    unsigned char *a = st_alloc(24);
    memset(first, ST_FILL, 24);
    memset(a, ST_FILL, 24);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    st_sink(a[0]);             /* first valid byte */
#else
    st_sink(*(a - 1));         /* the defect: one before the start */
#endif
    st_sink(first[0]);
    st_free(a);
    st_free(first);
}
