#include "harness.h"

/* Case 1 -- heap overflow, read, 1 byte past the end.
 *
 * Case 0's twin. Two 24-byte objects back to back; the defect reads a[24],
 * which under malloc is the padding or ASan's redzone and under an arena is
 * b[0] -- a byte of a live object, so the read even returns a plausible value.
 * Read and write are separate cases because a tool can check one and not the
 * other: ASan instruments both, Valgrind reports an invalid read only when the
 * byte is unaddressable, and a read never corrupts anything, so nothing
 * downstream will ever crash and reveal it.
 *
 * NEGATIVE CONTROL: reads a[23], the last valid byte. */
ST_CASE(1) {
    unsigned char *a = st_alloc(24);
    unsigned char *b = st_alloc(24);
    memset(a, ST_FILL, 24);
    memset(b, ST_FILL, 24);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    st_sink(a[23]);            /* last valid byte */
#else
    st_sink(a[24]);            /* the defect: one past the end */
#endif
    st_free(b);
    st_free(a);
}
