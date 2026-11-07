#include "harness.h"

/* Case 15 -- double free after the storage was reissued: two owners, one block.
 *
 * The free-list layer's worst case, and the reason double free is split into
 * two cases. Free a; allocate b, which a free list satisfies from a's storage;
 * then free a again. The second free is of an address the allocator currently
 * considers LIVE and owned by b, so afterwards the free list holds b's storage
 * while b's owner still uses it. The next allocation aliases b.
 *
 * On malloc with a quarantine the two pointers differ, so the second free is a
 * genuine double free and ASan says so. On a free list that reissues
 * immediately, a == b and the second free is indistinguishable from a correct
 * free of b: no tool can object to it, and the defect only becomes visible when
 * b is used afterwards -- which is the read this case ends with. Expect the
 * detection to come from the stale read rather than from the free, and say so
 * in the results.
 *
 * "ST NOTE reuse=1" is the precondition; without it (an arena) the row is
 * UNSUPPORTED via case.json's `requires`.
 *
 * NEGATIVE CONTROL: frees b, which is the correct second free. */
ST_CASE(15) {
    unsigned char *a = st_alloc(24);
    memset(a, ST_FILL, 24);
    st_free(a);
    unsigned char *b = st_alloc(24);
    memset(b, 0x11, 24);
    printf("ST NOTE reuse=%d\n", (int)(b == a));
    ST_READY();
#ifdef ST_NEGATIVE_CONTROL
    st_free(b);                /* the live object's own pointer */
#else
    st_free(a);                /* the defect: frees b's storage while b is live */
    st_sink(b[0]);             /* b is now a freed block */
#endif
}
