#include "harness.h"

/* Case 11: Read the old pointer after realloc moves the object; control uses the new pointer.
 * A missing move marker makes the configuration UNSUPPORTED. */
ST_CASE(11) {
    unsigned char *a = st_alloc(24);
    memset(a, ST_FILL, 24);
    unsigned char *big = st_realloc(a, 4096);
    printf("ST NOTE realloc=%d moved=%d\n", (int)(big != NULL), (int)(big != NULL && !st_same_address(big, a)));
    if (!big) return;          /* the allocator has no realloc; requires makes this UNSUPPORTED */
    memset(big, ST_FILL, 4096);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    st_sink(big[0]);           /* the pointer realloc returned */
#else
    st_sink(a[0]);             /* the defect: the pointer realloc invalidated */
#endif
    st_free(big);
}
