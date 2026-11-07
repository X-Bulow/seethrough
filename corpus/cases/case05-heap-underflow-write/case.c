#include "harness.h"

/* Case 5 -- heap underflow, write, 1 byte before the start.
 *
 * Two 24-byte objects; the defect writes *(a - 1). Under malloc that byte is
 * the last byte of the chunk header, which libc will read back in free(), so
 * the program can crash later even with no tool. Under an arena it is the last
 * slack byte of the object allocated before a -- addressable, owned by nobody,
 * and silent.
 *
 * Underflow is a separate class from overflow because the two sides of an
 * object are not symmetric for any of these tools: a bump-pointer arena's
 * leftward neighbour is an older object, a free-list's is often the free-list
 * link, and ASan's left redzone is checked by different instrumentation from
 * its right one.
 *
 * NEGATIVE CONTROL: writes a[0], the first valid byte. */
ST_CASE(5) {
    unsigned char *first = st_alloc(24);
    unsigned char *a = st_alloc(24);
    memset(first, ST_FILL, 24);
    memset(a, ST_FILL, 24);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    a[0] = 1;                  /* first valid byte */
#else
    *(a - 1) = 1;              /* the defect: one before the start */
#endif
    st_sink(first[0]);
    st_free(a);
    st_free(first);
}
