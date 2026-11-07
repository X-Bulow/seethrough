#include "harness.h"

/* Case 2 -- heap overflow, write, inside the allocator's own alignment slack.
 *
 * Why this is not case 0. A 24-byte request is rounded up to 32 by any
 * 16-byte-aligned allocator, so bytes 24..31 belong to no object at all: they
 * are the allocator's slack, not the neighbour's data. a[28] is therefore past
 * what the program asked for but inside what the allocator handed out.
 *
 * That is the dividing line between tools that remember the REQUEST and tools
 * that only know the BLOCK. ASan records the request and poisons the slack, so
 * it reports. LowFat's bounds are the size class, so 28 is in bounds for it.
 * An annotated arena reports only if it poisons the slack as well as the gap
 * to the neighbour, which is why allocators/arena/arena.c unpoisons exactly n
 * and not the rounded size.
 *
 * NEGATIVE CONTROL: writes a[23], the last byte of the request. */
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
