#include "harness.h"

/* Case 7: Overwrite the eight bytes before the object; control writes inside it.
 * These bytes hold malloc metadata or the preceding pool object's slack. */
ST_CASE(7) {
    unsigned char *first = st_alloc(24);
    unsigned char *a = st_alloc(24);
    memset(first, ST_FILL, 24);
    memset(a, ST_FILL, 24);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    memset(a, 0xcc, 8);        /* the object's own first 8 bytes */
#else
    memset(a - 8, 0xcc, 8);    /* the defect: the 8 bytes an allocator keeps a size in */
#endif
    st_sink(first[0]);
    st_free(a);
    st_free(first);
}
