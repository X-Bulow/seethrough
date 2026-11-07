#include "harness.h"

/* Case 7 -- heap underflow, write, over the 8 bytes where a header would live.
 *
 * The ground-truth version of what capstone's memsys5 demonstrator shows in
 * corpus/real: an allocator that keeps bookkeeping IN BAND, in the bytes next
 * to the object it hands out, turns an ordinary off-by-a-few write into
 * corruption of the allocator itself. glibc keeps the chunk size at p - 8;
 * memsys5 keeps its free-list links in the body of freed blocks.
 *
 * So the same source line means something different per allocator, and that is
 * the measurement: on malloc the write hits the chunk header (ASan's left
 * redzone catches it first, and without a tool free() may abort); on a
 * bump-pointer arena there is no header at all, so it is just the previous
 * object's tail, which nothing notices unless an annotated build has poisoned
 * that slack. Our free list (B1.3) keeps no header either: its bookkeeping is
 * in a side table outside the pool.
 *
 * NEGATIVE CONTROL: writes the first 8 bytes of the object instead. */
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
