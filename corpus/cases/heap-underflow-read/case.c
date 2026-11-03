#include "harness.h"

/* Case 3 -- heap-underflow-read. TODO(A): write the sequence. Rules in corpus/README.md:
 * same st_alloc/st_free traffic in both images, ST_READY() right before the
 * defect, st_sink() on anything read, the control replaces only the access. */
ST_CASE(3) {
    unsigned char *a = st_alloc(24);
    memset(a, ST_FILL, 24);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    st_sink(a[0]);
#else
    st_sink(a[0]);             /* TODO: the defect */
#endif
    st_free(a);
}
