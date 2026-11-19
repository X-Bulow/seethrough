#include "harness.h"

/* Case 2: Write a[28] into alignment slack beyond a 24-byte request.
 * Exact-size poisoning detects it; 16-byte tagging cannot. Control writes a[23]. */
ST_CASE(2) {
    unsigned char *a = st_alloc(24);
    unsigned char *b = st_alloc(24);
    memset(a, ST_FILL, 24);
    memset(b, ST_FILL, 24);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    a[23] = 1;                 /* last byte of the request */
#else
    a[28] = 1;                 /* the defect: 4 bytes into the 16-byte alignment slack */
#endif
    st_sink(b[0]);
    st_free(b);
    st_free(a);
}
