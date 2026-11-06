#include "harness.h"

/* Case 3 -- heap overflow, write, 40 bytes past the end: over the neighbour.
 *
 * Three 24-byte objects. Under a 16-byte-aligned arena they occupy [0,32),
 * [32,64) and [64,96), so a[64] is c[0]: the write skips b entirely and lands
 * in the object after it.
 *
 * Why it is a separate case. A detector's reach is finite. ASan's redzone is
 * at least 16 bytes but a far enough write jumps it and lands in another live
 * malloc object, where ASan's shadow says "addressable" -- so on malloc this
 * case can be MISSED while case 0 is DETECTED. On an arena nothing changes: a
 * poisoned-gap annotation catches it only if the gap is between a and c, which
 * it is not. The pair (case 0, case 3) measures how much of the detection comes
 * from the redzone being in the right place rather than from the tool knowing
 * the object's size.
 *
 * NEGATIVE CONTROL: writes a[23]. */
ST_CASE(3) {
    unsigned char *a = st_alloc(24);
    unsigned char *b = st_alloc(24);
    unsigned char *c = st_alloc(24);
    memset(a, ST_FILL, 24);
    memset(b, ST_FILL, 24);
    memset(c, ST_FILL, 24);
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    a[23] = 1;                 /* last valid byte */
#else
    a[64] = 1;                 /* the defect: 40 past the end, over b, into c */
#endif
    st_sink(b[0]);
    st_sink(c[0]);
    st_free(c);
    st_free(b);
    st_free(a);
}
