#include "harness.h"

/* Case 11 -- use after free, read, through a pointer realloc invalidated.
 *
 * st_realloc(p, bigger) may move the object, and when it does the old block is
 * freed. A pointer that was taken before the call is stale afterwards, which is
 * the single most common way real programs get a use-after-free: SQLite's
 * agginfo defect (capstone case 01) and PostgreSQL's repalloc rows are both
 * this shape, and the bug is invisible in the source because no free() appears.
 *
 * It is a separate case from 8 and 9 because what ends the lifetime is inside
 * the allocator, so an allocator can get it right or wrong independently of its
 * free: an arena that grows in place never moves and has no defect to find,
 * while one that copies must poison the old block.
 *
 * "ST NOTE realloc=1 moved=1" is the precondition: the call succeeded and the
 * object actually moved. An allocator whose st_realloc returns NULL or grows in
 * place prints otherwise and case.json's `requires` makes the row UNSUPPORTED.
 *
 * NEGATIVE CONTROL: reads through the new pointer. */
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
