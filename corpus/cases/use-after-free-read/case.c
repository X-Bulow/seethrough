#include "harness.h"

/* Case 9 -- use after free, read, with no allocation in between. Case 8's
 * twin. A stale read is the quietest memory-safety defect there is: it
 * corrupts nothing, so no later crash will ever point at it, and under an
 * allocator whose free is a no-op it returns the object's own old contents --
 * the program cannot tell, and neither can a tool that only knows malloc
 * lifetimes.
 *
 * NEGATIVE CONTROL: the read happens before the free. */
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
