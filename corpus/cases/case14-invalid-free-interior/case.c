#include "harness.h"

/* Case 14: Free an interior pointer; control frees the allocation base.
 * Memcheck pool ownership can reject it even without an invalid memory access. */
ST_CASE(14) {
    unsigned char *a = st_alloc(24);
    memset(a, ST_FILL, 24);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    st_free(a);                /* the pointer st_alloc returned */
#else
    st_free(a + 8);            /* the defect: an interior pointer */
#endif
}
