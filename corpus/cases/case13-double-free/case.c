#include "harness.h"

/* Case 13: Free the same pointer twice; control frees separate objects.
 * Memcheck models ownership; poisoning alone cannot diagnose an invalid free call. */
ST_CASE(13) {
    unsigned char *a = st_alloc(24);
    unsigned char *b = st_alloc(24);
    memset(a, ST_FILL, 24);
    memset(b, ST_FILL, 24);
    st_free(a);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    st_free(b);                /* the other live object */
#else
    st_free(a);                /* the defect: a again. b is left to st_alloc_fini */
#endif
}
