#include "harness.h"

/* Case 3: Write a[64] into another live pool object; control writes within a.
 * Addressability cannot distinguish this overflow from valid destination access. */
ST_CASE(3) {
    unsigned char *a = st_alloc(24);
    unsigned char *b = st_alloc(24);
    unsigned char *c = st_alloc(24);
    memset(a, ST_FILL, 24);
    memset(b, ST_FILL, 24);
    memset(c, ST_FILL, 24);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    a[23] = 1;                 /* last valid byte */
#else
    a[64] = 1;                 /* the defect: 40 past the end, over b, into c */
#endif
    st_sink(b[0]);
    st_sink(c[0]);
    st_free(c);
    st_free(b);
    st_free(a);
}
