#include "harness.h"

/* Case 8: Write after free without reuse; control writes before free.
 * Re-poisoning requires object sizes, supplied by the arena side table. */
ST_CASE(8) {
    unsigned char *a = st_alloc(24);
    memset(a, ST_FILL, 24);
#ifdef ST_NEGATIVE_CONTROL
    ST_READY();
    a[0] = 1;                  /* while still live */
    st_free(a);
#else
    st_free(a);
    ST_READY();
    a[0] = 1;                  /* the defect: after the free */
#endif
}
